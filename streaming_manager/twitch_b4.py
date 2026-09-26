from __future__ import annotations

"""B4 Twitch Channel Points / Custom Rewards / EventSub orchestration.

Provider transport remains in ``twitch.py``.  I1 simplifies the product rule:
a connected Twitch integration with app-managed rewards is a permanent event
source. Reward availability is controlled manually in Settings and is no longer
linked to auction start/stop. Source-time context, B3 normalization and Twitch
redemption fulfillment/refund semantics remain unchanged.
"""

import json
import re
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from .conversion import parse_positive_rate
from .integrations import IntegrationError, IntegrationManager, NormalizedIntegrationEvent
from .twitch import (
    TWITCH_CHANNEL_POINTS_EVENT_TYPE,
    TWITCH_CHANNEL_POINTS_LABEL,
    TWITCH_CHANNEL_POINTS_UNIT,
    TWITCH_SERVICE_KEY,
)

# Legacy 0.3.64 settings retained only for backward-readable databases. I1 no longer
# uses either flag as an intake gate.
TWITCH_CP_ENABLED_KEY = "twitch_channel_points_enabled"
TWITCH_REWARDS_LINK_AUCTION_KEY = "twitch_rewards_link_to_auction"
TWITCH_REWARDS_MANUAL_ENABLED_KEY = "twitch_rewards_manual_enabled"
TWITCH_REWARD_COMMON_TITLE_KEY = "twitch_reward_common_title"
TWITCH_REWARD_DEFINITIONS_KEY = "twitch_reward_definitions_json"
TWITCH_RETIRED_REWARD_IDS_KEY = "twitch_retired_reward_ids_json"
TWITCH_DEFAULT_COMMON_TITLE = "Ставка"
TWITCH_DEFAULT_REWARD_COLOR = "#9146FF"
TWITCH_REWARD_PROMPT = "Введите название игры/лота"
TWITCH_EVENTSUB_URL = "wss://eventsub.wss.twitch.tv/ws?keepalive_timeout_seconds=30"
_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


@dataclass(frozen=True)
class TwitchRewardDefinition:
    cost: int
    color: str = TWITCH_DEFAULT_REWARD_COLOR
    reward_id: str = ""

    def normalized(self) -> "TwitchRewardDefinition":
        cost = int(self.cost)
        if cost < 1:
            raise ValueError("Стоимость Twitch-награды должна быть не меньше 1 Channel Point.")
        color = str(self.color or TWITCH_DEFAULT_REWARD_COLOR).strip().upper()
        if not _COLOR_RE.fullmatch(color):
            raise ValueError("Цвет Twitch-награды должен быть в формате #RRGGBB.")
        return TwitchRewardDefinition(cost=cost, color=color, reward_id=str(self.reward_id or "").strip())


class TwitchChannelPointsService:
    def __init__(self, db, integration_manager: IntegrationManager):
        self.db = db
        self.integration_manager = integration_manager

    @staticmethod
    def _bool(raw: object, default: bool = False) -> bool:
        if raw is None or str(raw).strip() == "":
            return bool(default)
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}

    def channel_points_enabled(self) -> bool:
        """Compatibility reader: connection itself is now the intake permission."""
        return self.connection_ready()

    def link_rewards_to_auction(self) -> bool:
        """Compatibility reader for the retired 0.3.64 auction-link flag."""
        return False

    def manual_rewards_enabled(self) -> bool:
        return self._bool(self.db.get_setting(TWITCH_REWARDS_MANUAL_ENABLED_KEY, "0"), False)

    def common_title(self) -> str:
        return str(self.db.get_setting(TWITCH_REWARD_COMMON_TITLE_KEY, TWITCH_DEFAULT_COMMON_TITLE) or TWITCH_DEFAULT_COMMON_TITLE).strip()

    def reward_definitions(self) -> list[TwitchRewardDefinition]:
        raw = self.db.get_setting(TWITCH_REWARD_DEFINITIONS_KEY, "[]")
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = []
        result: list[TwitchRewardDefinition] = []
        if isinstance(payload, list):
            for item in payload:
                if not isinstance(item, dict):
                    continue
                try:
                    result.append(
                        TwitchRewardDefinition(
                            cost=int(item.get("cost") or 0),
                            color=str(item.get("color") or TWITCH_DEFAULT_REWARD_COLOR),
                            reward_id=str(item.get("reward_id") or ""),
                        ).normalized()
                    )
                except (TypeError, ValueError):
                    continue
        return result

    def retired_reward_ids(self) -> list[str]:
        raw = self.db.get_setting(TWITCH_RETIRED_REWARD_IDS_KEY, "[]")
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = []
        if not isinstance(payload, list):
            return []
        return sorted({str(item).strip() for item in payload if str(item).strip()})

    def configuration(self) -> dict:
        return {
            "manual_rewards_enabled": self.manual_rewards_enabled(),
            "common_title": self.common_title(),
            "rewards": self.reward_definitions(),
        }

    @staticmethod
    def reward_title(common_title: str, cost: int) -> str:
        return f"{str(common_title).strip()} - {int(cost)}"

    def _validate_configuration(
        self,
        common_title: str,
        rewards: list[TwitchRewardDefinition],
    ) -> tuple[str, list[TwitchRewardDefinition]]:
        title = str(common_title or "").strip()
        if not title:
            raise ValueError("Общее название Twitch-наград не может быть пустым.")
        normalized = [item.normalized() for item in rewards]
        if len(normalized) > 50:
            raise ValueError("Twitch допускает не более 50 Custom Rewards на канале.")
        costs = [item.cost for item in normalized]
        if len(costs) != len(set(costs)):
            raise ValueError("Стоимость каждой Twitch-награды должна быть уникальной.")
        for item in normalized:
            full_title = self.reward_title(title, item.cost)
            if len(full_title) > 45:
                raise ValueError(
                    f"Название «{full_title}» длиннее лимита Twitch в 45 символов."
                )
        return title, normalized

    def save_configuration(
        self,
        *,
        common_title: str,
        rewards: list[TwitchRewardDefinition],
    ) -> dict:
        title, normalized = self._validate_configuration(common_title, rewards)
        before = self.reward_definitions()
        kept_ids = {item.reward_id for item in normalized if item.reward_id}
        retired = set(self.retired_reward_ids())
        retired.update(item.reward_id for item in before if item.reward_id and item.reward_id not in kept_ids)
        retired.difference_update(kept_ids)
        payload = [
            {"cost": item.cost, "color": item.color, "reward_id": item.reward_id}
            for item in normalized
        ]
        self.db.set_settings_bulk(
            {
                TWITCH_REWARD_COMMON_TITLE_KEY: title,
                TWITCH_REWARD_DEFINITIONS_KEY: json.dumps(payload, ensure_ascii=False, sort_keys=True),
                # Clear retired 0.3.64 gates so database inspection reflects I1.
                TWITCH_CP_ENABLED_KEY: "",
                TWITCH_REWARDS_LINK_AUCTION_KEY: "",
                TWITCH_RETIRED_REWARD_IDS_KEY: json.dumps(sorted(retired), ensure_ascii=False),
            }
        )
        return self.configuration()

    def connection_ready(self) -> bool:
        row = self.db.get_integration_connection(TWITCH_SERVICE_KEY)
        return bool(
            row is not None
            and bool(row.get("enabled"))
            and str(row.get("status")) == "connected"
        )

    def _connection(self) -> dict:
        row = self.db.get_integration_connection(TWITCH_SERVICE_KEY)
        if row is None or not bool(row.get("enabled")) or str(row.get("status")) != "connected":
            raise IntegrationError("Twitch должен быть включён и находиться в состоянии «Подключено».")
        return row

    def _require_positive_rate(self) -> str:
        raw = self.db.get_conversion_rate(TWITCH_CHANNEL_POINTS_UNIT)
        if not raw:
            raise ValueError(
                "Сначала задайте курс Twitch Channel Points на вкладке «Конвертация»."
            )
        parse_positive_rate(raw)
        return raw

    def ensure_manage_scope(self) -> dict:
        self._connection()
        row = self.integration_manager.call_adapter(TWITCH_SERVICE_KEY, "ensure_manage_scope")
        if not isinstance(row, dict):
            row = self.db.get_integration_connection(TWITCH_SERVICE_KEY) or {}
        config = dict(row.get("provider_config") or {})
        if not bool(config.get("channel_points_custom_rewards_available", False)):
            reason = str(config.get("channel_points_custom_rewards_reason") or "Custom Rewards недоступны")
            raise IntegrationError(reason)
        return row

    def set_channel_points_enabled(self, enabled: bool) -> bool:
        """Deprecated compatibility shim. I1 removed the local intake toggle."""
        if not enabled:
            raise ValueError(
                "Отдельное отключение учёта Channel Points больше не используется. "
                "Отключите Twitch или сами Twitch-награды."
            )
        self._require_positive_rate()
        self.ensure_manage_scope()
        return True

    def set_manual_rewards_enabled(self, enabled: bool) -> bool:
        enabled = bool(enabled)
        if enabled:
            self._require_positive_rate()
            self.ensure_manage_scope()
        self.db.set_setting(TWITCH_REWARDS_MANUAL_ENABLED_KEY, "1" if enabled else "0")
        self.sync_reward_enabled_state()
        return enabled

    def set_link_to_auction(self, enabled: bool) -> bool:
        """Deprecated compatibility shim for the removed auction-link behavior."""
        if enabled:
            raise ValueError(
                "Привязка Twitch-наград к старту аукциона больше не используется."
            )
        self.db.set_setting(TWITCH_REWARDS_LINK_AUCTION_KEY, "")
        return False

    def prepare_disconnect(self) -> None:
        """Disable registered remote rewards before stopping Twitch intake."""
        if self.connection_ready() and self.managed_reward_ids():
            self.sync_reward_enabled_state(False)

    def on_connection_removed(self) -> None:
        """Fail closed after local Twitch credentials/config are removed."""
        self.db.set_settings_bulk(
            {
                TWITCH_CP_ENABLED_KEY: "",
                TWITCH_REWARDS_LINK_AUCTION_KEY: "",
                TWITCH_REWARDS_MANUAL_ENABLED_KEY: "0",
            }
        )

    def desired_rewards_enabled(self) -> bool:
        # Availability is independent of auction state. The explicit remote
        # reward on/off control in Settings is the only availability switch.
        return self.manual_rewards_enabled()

    @staticmethod
    def _reward_body(
        *,
        title: str,
        cost: int,
        color: str,
        enabled: bool,
        create: bool,
    ) -> dict:
        body = {
            "title": str(title),
            "cost": int(cost),
            "prompt": TWITCH_REWARD_PROMPT,
            "background_color": str(color),
            "is_enabled": bool(enabled),
            "is_user_input_required": True,
            "should_redemptions_skip_request_queue": False,
        }
        if not create:
            # Twitch's update endpoint supports these fields too; keeping them
            # explicit repairs manual remote edits back to the app contract.
            return body
        return body

    def sync_rewards(self) -> list[TwitchRewardDefinition]:
        self.ensure_manage_scope()
        definitions = self.reward_definitions()
        common_title = self.common_title()
        self._validate_configuration(common_title, definitions)
        desired_enabled = self.desired_rewards_enabled()
        remote = self.integration_manager.call_adapter(TWITCH_SERVICE_KEY, "list_manageable_rewards")
        remote_by_id = {str(row.get("id") or ""): row for row in remote if str(row.get("id") or "")}
        remote_by_title = {str(row.get("title") or ""): row for row in remote if str(row.get("title") or "")}

        updated: list[TwitchRewardDefinition] = []
        for definition in definitions:
            title = self.reward_title(common_title, definition.cost)
            body = self._reward_body(
                title=title,
                cost=definition.cost,
                color=definition.color,
                enabled=desired_enabled,
                create=not bool(definition.reward_id),
            )
            reward_id = definition.reward_id
            remote_row = remote_by_id.get(reward_id) if reward_id else None
            if remote_row is None:
                remote_row = remote_by_title.get(title)
                if remote_row is not None:
                    reward_id = str(remote_row.get("id") or "")
            if remote_row is not None and reward_id:
                self.integration_manager.call_adapter(
                    TWITCH_SERVICE_KEY,
                    "update_managed_reward",
                    reward_id,
                    body,
                )
            else:
                created = self.integration_manager.call_adapter(
                    TWITCH_SERVICE_KEY,
                    "create_managed_reward",
                    body,
                )
                reward_id = str(created.get("id") or "")
                if not reward_id:
                    raise IntegrationError("Twitch не вернул ID созданной награды.")
            updated.append(
                TwitchRewardDefinition(
                    cost=definition.cost,
                    color=definition.color,
                    reward_id=reward_id,
                )
            )

        active_ids = {item.reward_id for item in updated if item.reward_id}
        # Removing a local reward row is intentionally non-destructive: the
        # remote reward is disabled immediately so viewers cannot spend points
        # into an unsubscribed reward, but it is only deleted by the separately
        # confirmed «Удалить награды» action.
        for retired_id in self.retired_reward_ids():
            if retired_id in active_ids or retired_id not in remote_by_id:
                continue
            self.integration_manager.call_adapter(
                TWITCH_SERVICE_KEY,
                "update_managed_reward",
                retired_id,
                {"is_enabled": False},
            )

        self.save_configuration(
            common_title=common_title,
            rewards=updated,
        )
        return updated

    def sync_reward_enabled_state(self, forced: bool | None = None) -> bool:
        definitions = [item for item in self.reward_definitions() if item.reward_id]
        desired = self.desired_rewards_enabled() if forced is None else bool(forced)
        if not definitions:
            return desired
        self.ensure_manage_scope()
        for definition in definitions:
            self.integration_manager.call_adapter(
                TWITCH_SERVICE_KEY,
                "update_managed_reward",
                definition.reward_id,
                {"is_enabled": desired},
            )
        return desired

    def delete_managed_rewards(self) -> int:
        self.ensure_manage_scope()
        definitions = self.reward_definitions()
        ids = {item.reward_id for item in definitions if item.reward_id}
        ids.update(self.retired_reward_ids())
        deleted = 0
        for reward_id in sorted(ids):
            self.integration_manager.call_adapter(
                TWITCH_SERVICE_KEY,
                "delete_managed_reward",
                reward_id,
            )
            deleted += 1
        cleared = [
            TwitchRewardDefinition(cost=item.cost, color=item.color, reward_id="")
            for item in definitions
        ]
        self.db.set_settings_bulk(
            {
                TWITCH_REWARD_DEFINITIONS_KEY: json.dumps(
                    [
                        {"cost": item.cost, "color": item.color, "reward_id": ""}
                        for item in cleared
                    ],
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                TWITCH_RETIRED_REWARD_IDS_KEY: "[]",
                TWITCH_REWARDS_MANUAL_ENABLED_KEY: "0",
            }
        )
        return deleted

    def managed_reward_ids(self) -> tuple[str, ...]:
        return tuple(item.reward_id for item in self.reward_definitions() if item.reward_id)

    def _set_redemption_status(self, reward_id: str, redemption_id: str, status: str) -> None:
        self.integration_manager.call_adapter(
            TWITCH_SERVICE_KEY,
            "update_redemption_status",
            reward_id,
            redemption_id,
            status,
        )

    @staticmethod
    def _normalize_redemption(raw: dict) -> dict:
        event = dict(raw or {})
        reward = event.get("reward") or {}
        if not isinstance(reward, dict):
            reward = {}
        return {
            "id": str(event.get("id") or ""),
            "user_id": str(event.get("user_id") or event.get("user_id") or ""),
            "user_login": str(event.get("user_login") or ""),
            "user_name": str(event.get("user_name") or ""),
            "user_input": str(event.get("user_input") or "").strip(),
            "redeemed_at": str(event.get("redeemed_at") or ""),
            "reward_id": str(reward.get("id") or ""),
            "reward_title": str(reward.get("title") or ""),
            "reward_cost": int(reward.get("cost") or 0),
            "eventsub_metadata": dict(event.get("_eventsub_metadata") or {})
            if isinstance(event.get("_eventsub_metadata"), dict) else {},
            "raw": event,
        }

    def process_redemption(self, raw_event: dict) -> dict:
        redemption = self._normalize_redemption(raw_event)
        redemption_id = redemption["id"]
        reward_id = redemption["reward_id"]
        if not redemption_id or not reward_id:
            raise ValueError("Twitch redemption не содержит обязательные ID.")

        managed = set(self.managed_reward_ids())
        if reward_id not in managed:
            return {"status": "ignored_unmanaged", "redemption_id": redemption_id}

        redeemed_at = str(redemption["redeemed_at"] or "").strip()
        try:
            parsed_redeemed_at = datetime.fromisoformat(redeemed_at.replace("Z", "+00:00"))
        except ValueError:
            parsed_redeemed_at = None
        if parsed_redeemed_at is None or parsed_redeemed_at.tzinfo is None:
            self._set_redemption_status(reward_id, redemption_id, "CANCELED")
            return {"status": "canceled_invalid_redeemed_at", "redemption_id": redemption_id}
        if int(redemption["reward_cost"]) < 1:
            self._set_redemption_status(reward_id, redemption_id, "CANCELED")
            return {"status": "canceled_invalid_reward_cost", "redemption_id": redemption_id}

        try:
            self._require_positive_rate()
        except Exception:
            self._set_redemption_status(reward_id, redemption_id, "CANCELED")
            return {"status": "canceled_missing_rate", "redemption_id": redemption_id}

        source_auction_id = self.db.find_running_auction_at(redemption["redeemed_at"])

        contributor = redemption["user_name"] or redemption["user_login"] or redemption["user_id"]
        event = NormalizedIntegrationEvent(
            service_key=TWITCH_SERVICE_KEY,
            external_event_id=redemption_id,
            event_type=TWITCH_CHANNEL_POINTS_EVENT_TYPE,
            source_amount=redemption["reward_cost"],
            source_unit=TWITCH_CHANNEL_POINTS_UNIT,
            source_unit_label=TWITCH_CHANNEL_POINTS_LABEL,
            unit_kind="service",
            contributor=contributor,
            lot_title=redemption["user_input"],
            note=f"Twitch reward: {redemption['reward_title']}",
            provider_metadata={
                "reward_id": reward_id,
                "reward_title": redemption["reward_title"],
                "reward_cost": redemption["reward_cost"],
                "redeemed_at": redemption["redeemed_at"],
                "twitch_user_id": redemption["user_id"],
                "twitch_user_login": redemption["user_login"],
                "twitch_user_name": redemption["user_name"],
                "eventsub_message_id": str(redemption["eventsub_metadata"].get("message_id") or ""),
                "eventsub_message_timestamp": str(redemption["eventsub_metadata"].get("message_timestamp") or ""),
                "eventsub_subscription_id": str(redemption["eventsub_metadata"].get("subscription_id") or ""),
            },
            auction_id_hint=source_auction_id,
            force_outside_auction=source_auction_id is None,
        )
        result = self.integration_manager.accept_normalized_event(event)
        status = str(result.get("status") or "")
        if status == "processed":
            self._set_redemption_status(reward_id, redemption_id, "FULFILLED")
        elif status == "inapplicable":
            self._set_redemption_status(reward_id, redemption_id, "CANCELED")
        elif status == "awaiting_rate":
            # This path is guarded above.  Never leave a Twitch redemption in
            # Pending where a later manual apply could double-conflict with a
            # refund decision.
            self._set_redemption_status(reward_id, redemption_id, "CANCELED")
        return result

    def catch_up_unfulfilled(self) -> int:
        processed = 0
        for reward_id in self.managed_reward_ids():
            rows = self.integration_manager.call_adapter(
                TWITCH_SERVICE_KEY,
                "list_unfulfilled_redemptions",
                reward_id,
            )
            for row in rows:
                self.process_redemption(dict(row))
                processed += 1
        return processed


class TwitchEventSubRuntime:
    """One resilient desktop EventSub WebSocket loop.

    The loop is intentionally independent of Qt so tests can use a fake socket
    factory.  It creates subscriptions only for registered app-managed reward
    IDs, filters again before processing, catches up UNFULFILLED redemptions on
    reconnect, and delegates all business mutation to TwitchChannelPointsService.
    """

    def __init__(
        self,
        service: TwitchChannelPointsService,
        *,
        socket_factory: Callable[[str], object] | None = None,
        retry_seconds: float = 5.0,
    ):
        self.service = service
        self.socket_factory = socket_factory or self._default_socket_factory
        self.retry_seconds = max(0.2, float(retry_seconds))
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._socket = None
        self.last_error = ""
        self.connected = False

    @staticmethod
    def _default_socket_factory(url: str):
        import websocket  # websocket-client, installed by requirements.txt

        return websocket.create_connection(url, timeout=2.0, enable_multithread=True)

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="TwitchEventSub", daemon=True)
        self._thread.start()

    def wake(self) -> None:
        self._wake.set()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        sock = self._socket
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=3.0)
        self._thread = None
        self.connected = False

    def _wait(self, seconds: float) -> None:
        self._wake.wait(timeout=max(0.0, float(seconds)))
        self._wake.clear()

    @staticmethod
    def _recv_json(sock) -> dict:
        raw = sock.recv()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        payload = json.loads(str(raw))
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _message_type(message: dict) -> str:
        metadata = message.get("metadata") or {}
        return str(metadata.get("message_type") or "") if isinstance(metadata, dict) else ""

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                if (
                    not self.service.connection_ready()
                    or not self.service.managed_reward_ids()
                ):
                    self.connected = False
                    self._wait(1.0)
                    continue
                url = TWITCH_EVENTSUB_URL
                subscriptions_required = True
                while not self._stop.is_set():
                    reconnect_url = self._run_connection(
                        url,
                        subscriptions_required=subscriptions_required,
                    )
                    if not reconnect_url:
                        break
                    # Twitch migrates existing subscriptions to reconnect_url.
                    # Keep the handoff iterative so repeated provider reconnects
                    # cannot grow the Python call stack over a long desktop run.
                    url = reconnect_url
                    subscriptions_required = False
            except Exception as exc:  # keep runtime isolated from the GUI process
                self.last_error = str(exc)
                self.connected = False
                if not self._stop.is_set():
                    self._wait(self.retry_seconds)

    def _run_connection(self, url: str, *, subscriptions_required: bool) -> str:
        sock = self.socket_factory(url)
        self._socket = sock
        try:
            welcome = self._recv_json(sock)
            if self._message_type(welcome) != "session_welcome":
                raise RuntimeError("Twitch EventSub не прислал session_welcome.")
            session = ((welcome.get("payload") or {}).get("session") or {})
            session_id = str(session.get("id") or "") if isinstance(session, dict) else ""
            if not session_id:
                raise RuntimeError("Twitch EventSub не прислал session_id.")

            reward_ids = self.service.managed_reward_ids()
            if subscriptions_required:
                # First subscription is created immediately after welcome to
                # satisfy Twitch's default 10-second unused-connection limit.
                for reward_id in reward_ids:
                    self.service.integration_manager.call_adapter(
                        TWITCH_SERVICE_KEY,
                        "create_eventsub_subscription",
                        session_id,
                        reward_id,
                    )
            self.connected = True
            self.last_error = ""
            try:
                self.service.sync_reward_enabled_state()
            except Exception:
                pass
            # Recover events that happened while the app or socket was offline,
            # and retry remote FULFILLED/CANCELED after a prior network failure.
            self.service.catch_up_unfulfilled()
            last_desired = self.service.desired_rewards_enabled()

            while not self._stop.is_set():
                if not self.service.connection_ready():
                    return ""
                current_ids = self.service.managed_reward_ids()
                if current_ids != reward_ids:
                    # Reconnect so the subscription set exactly follows the
                    # registered app-managed reward IDs.
                    return
                desired = self.service.desired_rewards_enabled()
                if desired != last_desired:
                    self.service.sync_reward_enabled_state(desired)
                    last_desired = desired
                try:
                    message = self._recv_json(sock)
                except Exception as exc:
                    # websocket-client timeout is expected and is used to poll
                    # local auction state without a second timer thread.
                    if exc.__class__.__name__ in {"WebSocketTimeoutException", "TimeoutError"}:
                        continue
                    raise
                message_type = self._message_type(message)
                if message_type == "session_keepalive":
                    continue
                if message_type == "notification":
                    payload = message.get("payload") or {}
                    event = payload.get("event") or {} if isinstance(payload, dict) else {}
                    if isinstance(event, dict):
                        metadata = message.get("metadata") or {}
                        subscription = payload.get("subscription") or {} if isinstance(payload, dict) else {}
                        enriched = dict(event)
                        enriched["_eventsub_metadata"] = {
                            "message_id": str(metadata.get("message_id") or "")
                            if isinstance(metadata, dict) else "",
                            "message_timestamp": str(metadata.get("message_timestamp") or "")
                            if isinstance(metadata, dict) else "",
                            "subscription_id": str(subscription.get("id") or "")
                            if isinstance(subscription, dict) else "",
                        }
                        self.service.process_redemption(enriched)
                    continue
                if message_type == "session_reconnect":
                    payload = message.get("payload") or {}
                    session_data = payload.get("session") or {} if isinstance(payload, dict) else {}
                    reconnect_url = str(session_data.get("reconnect_url") or "") if isinstance(session_data, dict) else ""
                    if reconnect_url:
                        # Twitch carries existing subscriptions to the reconnect
                        # URL; return it to the iterative handoff loop so no
                        # duplicate subscriptions are created.
                        return reconnect_url
                if message_type == "revocation":
                    return ""
            return ""
        finally:
            self.connected = False
            self._socket = None
            try:
                sock.close()
            except Exception:
                pass


__all__ = [
    "TWITCH_CP_ENABLED_KEY",
    "TWITCH_REWARDS_LINK_AUCTION_KEY",
    "TWITCH_REWARDS_MANUAL_ENABLED_KEY",
    "TWITCH_REWARD_COMMON_TITLE_KEY",
    "TWITCH_REWARD_DEFINITIONS_KEY",
    "TWITCH_RETIRED_REWARD_IDS_KEY",
    "TWITCH_DEFAULT_COMMON_TITLE",
    "TWITCH_DEFAULT_REWARD_COLOR",
    "TWITCH_REWARD_PROMPT",
    "TWITCH_EVENTSUB_URL",
    "TwitchRewardDefinition",
    "TwitchChannelPointsService",
    "TwitchEventSubRuntime",
]
