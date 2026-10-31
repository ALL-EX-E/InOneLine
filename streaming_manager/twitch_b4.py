from __future__ import annotations

"""B4 Twitch Channel Points / Custom Rewards / EventSub orchestration.

Provider transport remains in ``twitch.py``.  I1 simplifies the product rule:
a connected Twitch integration with app-managed rewards is a permanent event
source. Reward availability is controlled manually in Settings and is no longer
linked to auction start/stop. Source-time context, B3 normalization and Twitch
redemption fulfillment/refund semantics remain unchanged.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from time import monotonic
from collections import OrderedDict
from queue import Empty, Full, PriorityQueue
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .conversion import parse_positive_rate
from .multichat import ChatMessage, MultichatState
from .chat_third_party import make_catalog, resolve_fragments
from .chat_graphics import (
    parse_twitch_badges, parse_twitch_fragments, safe_image_url, twitch_name_color,
)
from .integrations import IntegrationError, IntegrationManager, NormalizedIntegrationEvent
from .twitch import (
    TWITCH_CHAT_READ_SCOPE,
    TWITCH_CHAT_EVENT_TYPES,
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
        chat_state: MultichatState | None = None,
    ):
        self.service = service
        self.chat_state = chat_state
        self.chat_connected = False
        self.chat_error = ""
        self._chat_subscription_active = False
        self._chat_source_id = ""
        self.socket_factory = socket_factory or self._default_socket_factory
        self.retry_seconds = max(0.2, float(retry_seconds))
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._socket = None
        self.last_error = ""
        self.connected = False
        # Media is resolved on one separate daemon worker, NEVER in EventSub's
        # receive loop. Queue and caches are bounded; failed lookups do not
        # compromise the chat or channel-points connection.
        self._media_lock = threading.RLock()
        self._media_tasks: PriorityQueue = PriorityQueue(maxsize=128)
        self._media_sequence = 0
        self._media_thread: threading.Thread | None = None
        self._avatar_cache: OrderedDict[tuple[str, str], str] = OrderedDict()
        self._avatar_scheduled: OrderedDict[tuple[str, str], None] = OrderedDict()
        self._badge_cache: dict[str, dict[tuple[str, str], str]] = {}
        self._badge_scheduled: set[str] = set()
        self._emotes_scheduled: set[str] = set()
        # External catalogs never share EventSub/Channel Points or the OAuth
        # media queue; their independent slow endpoints cannot delay avatars.
        self._third_party_catalog = {}
        self._third_party_source = ""
        self._third_party_thread: threading.Thread | None = None
        self._third_party_next_refresh = 0.0
        self._third_party_process: subprocess.Popen | None = None

    def _queue_media(self, task: tuple) -> bool:
        if self._media_thread is None or not self._media_thread.is_alive():
            return False
        try:
            # Avatar of a new chatter must not wait behind full catalog scans;
            # all adapter network calls still share the original OAuth lock.
            priorities = {"avatar": 0, "badges": 1, "emotes": 2}
            with self._media_lock:
                self._media_sequence += 1
                item = (priorities.get(task[0], 3), self._media_sequence, task)
                self._media_tasks.put_nowait(item)
            return True
        except Full:
            return False  # no GUI stalls or EventSub backpressure

    def _schedule_third_party_catalog(self, source_id: str) -> None:
        """Asynchronous channel+global catalog; updates affect *future* events."""
        if not self.chat_connected or not source_id or self._stop.is_set():
            return
        with self._media_lock:
            if source_id != self._third_party_source:
                self._third_party_catalog = {}
                self._third_party_source = source_id
                self._third_party_next_refresh = 0.0
            if monotonic() < self._third_party_next_refresh:
                return
            if self._third_party_thread and self._third_party_thread.is_alive():
                return
            self._third_party_next_refresh = monotonic() + 1800.0
            worker = threading.Thread(
                target=self._load_third_party_catalog,
                args=(source_id,),
                name="TwitchThirdPartyEmotes",
                daemon=True,
            )
            self._third_party_thread = worker
            worker.start()

    def _load_third_party_catalog(self, source_id: str) -> None:
        """Load the *existing* provider catalog in one killable helper process.

        Nested ThreadPoolExecutor tasks in the GUI process previously blocked
        Python's _python_exit while waiting for network DNS/connect. Keeping
        that code in a child preserves the providers/parsers, but makes their
        timeout/cancellation independent of Python thread shutdown.
        """
        from .emote_catalog import CHAT_CATALOG_MAX_BYTES, EmoteCatalogItem

        try:
            fd, output_path = tempfile.mkstemp(prefix="iol-catalog-", suffix=".json")
            os.close(fd)
        except OSError:
            return

        process = None
        try:
            if getattr(sys, "frozen", False):
                command = [sys.executable, "--fetch-chat-catalog", source_id, output_path]
            else:
                command = [
                    sys.executable, "-m", "streaming_manager.emote_catalog",
                    "--fetch-chat-catalog", source_id, output_path,
                ]
            with self._media_lock:
                if self._stop.is_set():
                    return
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                self._third_party_process = process

            # Whole helper deadline, including DNS and provider fallbacks.
            process.communicate(timeout=45.0)
            if process.returncode != 0 or self._stop.is_set():
                return
            with open(output_path, "rb") as stream:
                raw = stream.read(CHAT_CATALOG_MAX_BYTES + 1)
            if len(raw) > CHAT_CATALOG_MAX_BYTES:
                return
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, list):
                return
            items = []
            for row in payload[:3000]:
                if not isinstance(row, dict):
                    continue
                if not all(isinstance(row.get(k), str) for k in (
                    "source", "emote_id", "name", "image_url", "preview_url"
                )):
                    continue
                items.append(EmoteCatalogItem(
                    source=row["source"],
                    emote_id=row["emote_id"],
                    name=row["name"],
                    image_url=row["image_url"],
                    preview_url=row["preview_url"],
                    animated=bool(row.get("animated", False)),
                ))
            catalog = make_catalog(items)
            with self._media_lock:
                if (self._stop.is_set()
                        or self._chat_source_id != source_id
                        or self._third_party_source != source_id):
                    return
                self._third_party_catalog = catalog
        except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
            return
        finally:
            if process is not None:
                if process.poll() is None:
                    try:
                        process.kill()
                    except OSError:
                        pass
                    try:
                        process.communicate(timeout=2)
                    except (OSError, subprocess.TimeoutExpired):
                        pass
                with self._media_lock:
                    if self._third_party_process is process:
                        self._third_party_process = None
            try:
                os.unlink(output_path)
            except OSError:
                pass

    def _schedule_media_warmup(self, source_id: str) -> None:
        """Queue provider metadata before the first chat message, off EventSub."""
        if not self.chat_connected or not source_id:
            return
        row = self.service.db.get_integration_connection(TWITCH_SERVICE_KEY) or {}
        config = row.get("provider_config") or {}
        if isinstance(config, dict) and str(config.get("twitch_user_id") or "") == source_id:
            profile = safe_image_url(config.get("profile_image_url"))
            if profile:
                with self._media_lock:
                    self._avatar_cache[(source_id, source_id)] = profile
                if self.chat_state is not None:
                    self.chat_state.set_media_preload("twitch", (profile,))
        with self._media_lock:
            if source_id not in self._badge_scheduled:
                if self._queue_media(("badges", source_id, "", "")):
                    self._badge_scheduled.add(source_id)
            if source_id not in self._emotes_scheduled:
                if self._queue_media(("emotes", source_id, "", "")):
                    self._emotes_scheduled.add(source_id)

    def _media_worker(self) -> None:
        while not self._stop.is_set():
            try:
                task = self._media_tasks.get(timeout=0.4)
            except Empty:
                continue
            _priority, _number, (kind, source_id, user_id, login) = task
            if not self.service.connection_ready():
                continue
            try:
                if kind == "badges":
                    rows = self.service.integration_manager.call_adapter(
                        TWITCH_SERVICE_KEY, "list_chat_badges", source_id,
                    )
                    if isinstance(rows, dict):
                        cleaned = {
                            key: safe_image_url(url) for key, url in rows.items()
                            if isinstance(key, tuple) and len(key) == 2
                        }
                        cleaned = {key: url for key, url in cleaned.items() if url}
                        with self._media_lock:
                            self._badge_cache[source_id] = cleaned
                        if self.chat_state is not None:
                            self.chat_state.enrich_twitch_media(source_id, badge_urls=cleaned)
                            # Warm the most common badge variants before a
                            # moderator/subscriber first appears on screen.
                            important = {"broadcaster", "moderator", "vip", "subscriber"}
                            badge_images = [
                                url for (set_id, _variant), url in cleaned.items()
                                if set_id in important
                            ][:12]
                            self.chat_state.set_media_preload("twitch", badge_images)
                elif kind == "emotes":
                    catalog = self.service.integration_manager.call_adapter(
                        TWITCH_SERVICE_KEY, "list_center_emotes",
                    )
                    rows = catalog.get("items") if isinstance(catalog, dict) else []
                    if not isinstance(rows, list):
                        rows = []
                    preload = []
                    # Use the same official EventSub image URL and rendition
                    # as a real message, not the wheel picker's 3x thumbnails.
                    # A channel with 10+ custom emotes should not prevent
                    # common *global* native emotes from being warmed.
                    common = {
                        "kappa", "lul", "pogchamp", "biblethump",
                        "heyguys", "residentsleeper", "kreygasm", "vohiyo",
                    }
                    preferred = rows[:4] + [
                        row for row in rows
                        if isinstance(row, dict)
                        and str(row.get("name") or "").casefold() in common
                    ]
                    preferred += rows[:256]
                    for row in preferred:
                        if not isinstance(row, dict):
                            continue
                        parts = parse_twitch_fragments({"fragments": [{
                            "type": "emote",
                            "text": str(row.get("name") or ""),
                            "emote": {
                                "id": str(row.get("emote_id") or ""),
                                "format": ["animated" if row.get("animated") else "static"],
                            },
                        }]})
                        if (parts and parts[0].get("kind") == "image"
                                and parts[0]["url"] not in preload):
                            preload.append(parts[0]["url"])
                        if len(preload) >= 10:
                            break
                    if self.chat_state is not None:
                        self.chat_state.set_media_preload("twitch", preload)
                elif kind == "avatar":
                    url = safe_image_url(
                        self.service.integration_manager.call_adapter(
                            TWITCH_SERVICE_KEY, "resolve_profile_image", login,
                        )
                    )
                    if url:
                        with self._media_lock:
                            key = (source_id, user_id)
                            self._avatar_cache[key] = url
                            self._avatar_cache.move_to_end(key)
                            while len(self._avatar_cache) > 512:
                                self._avatar_cache.popitem(last=False)
                        if self.chat_state is not None:
                            self.chat_state.enrich_twitch_media(
                                source_id, avatar_by_user={user_id: url},
                            )
            except Exception:
                # Media failures must not affect Twitch EventSub or rewards.
                pass

    def _media_for_message(
        self, source_id: str, user_id: str, login: str, badges: tuple[dict, ...],
    ) -> tuple[str, tuple[dict, ...]]:
        with self._media_lock:
            if source_id not in self._badge_scheduled:
                if self._queue_media(("badges", source_id, "", "")):
                    self._badge_scheduled.add(source_id)
            if user_id and login and (source_id, user_id) not in self._avatar_scheduled:
                key = (source_id, user_id)
                self._avatar_scheduled[key] = None
                self._queue_media(("avatar", source_id, user_id, login))
                while len(self._avatar_scheduled) > 512:
                    self._avatar_scheduled.popitem(last=False)
            elif (source_id, user_id) in self._avatar_scheduled:
                self._avatar_scheduled.move_to_end((source_id, user_id))
            urls = self._badge_cache.get(source_id, {})
            avatar_url = self._avatar_cache.get((source_id, user_id), "")
            mapped = tuple(
                {**badge, "url": urls.get((badge["set_id"], badge["id"]), "")}
                for badge in badges
            )
            return avatar_url, mapped

    @staticmethod
    def _default_socket_factory(url: str):
        import websocket  # websocket-client, installed by requirements.txt

        return websocket.create_connection(url, timeout=2.0, enable_multithread=True)

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._media_thread = threading.Thread(
            target=self._media_worker, name="TwitchChatMedia", daemon=True,
        )
        self._media_thread.start()
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
        media_thread = self._media_thread
        if media_thread is not None and media_thread.is_alive():
            media_thread.join(timeout=1.0)
        self._media_thread = None
        # A blocked resolver in the catalog child must not block Python exit.
        with self._media_lock:
            catalog_process = self._third_party_process
            self._third_party_catalog = {}
            self._third_party_source = ""
        if catalog_process is not None and catalog_process.poll() is None:
            try:
                catalog_process.kill()
            except OSError:
                pass
        catalog_thread = self._third_party_thread
        if catalog_thread is not None and catalog_thread.is_alive():
            catalog_thread.join(timeout=1.0)
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

    def _chat_profile(self) -> tuple[str, bool]:
        row = self.service.db.get_integration_connection(TWITCH_SERVICE_KEY) or {}
        config = row.get("provider_config") or {}
        if not isinstance(config, dict):
            return "", False
        user_id = str(config.get("twitch_user_id") or "")
        scopes = config.get("granted_scopes") or []
        return user_id, bool(
            user_id and isinstance(scopes, (list, tuple))
            and TWITCH_CHAT_READ_SCOPE in scopes
        )

    def chat_status(self) -> str:
        if not self.service.connection_ready():
            return "Twitch: отключён. Подключение находится в разделе «Интеграции»."
        source_id, ready = self._chat_profile()
        if not source_id:
            return "Twitch: не удалось определить авторизованный канал."
        if not ready:
            return ("Twitch: для чтения чата требуется повторная авторизация "
                    "через «Интеграции» (user:read:chat). Награды не затрагиваются.")
        if self.chat_error:
            if self.chat_connected:
                return "Twitch: чат подключён, но некоторые события модерации недоступны."
            return "Twitch: ошибка подписки на чат; проверьте Twitch и права в «Интеграциях»."
        if self.chat_connected:
            return "Twitch: чат подключён."
        if self.last_error:
            return "Twitch: временная ошибка подключения EventSub. Проверьте интеграцию."
        return "Twitch: подключение к чату..."

    @staticmethod
    def _event_timestamp(metadata: dict) -> float | None:
        raw = str(metadata.get("message_timestamp") or "").strip()
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
        except (TypeError, ValueError, OverflowError):
            return None

    def _process_chat_notification(self, event_type: str, event: dict, metadata: dict) -> None:
        state = self.chat_state
        if state is None:
            return
        source_id = str(event.get("broadcaster_user_id") or "")
        if not source_id or source_id != self._chat_source_id:
            return
        if event_type == "channel.chat.message":
            msg_id = str(event.get("message_id") or "")
            body = event.get("message") or {}
            value = str(body.get("text") or "") if isinstance(body, dict) else ""
            fragments = parse_twitch_fragments(body)
            with self._media_lock:
                active_catalog = (
                    self._third_party_catalog
                    if self._third_party_source == source_id else {}
                )
            if active_catalog:
                fragments = resolve_fragments(fragments, value, active_catalog)
            if not msg_id or (not value and not fragments):
                return
            author_id = str(event.get("chatter_user_id") or "")
            badges = parse_twitch_badges(event)
            avatar, badges = self._media_for_message(
                source_id, author_id,
                str(event.get("chatter_user_login") or ""),
                badges,
            )
            state.ingest(ChatMessage(
                platform="twitch", source_id=source_id, external_id=msg_id,
                author=str(event.get("chatter_user_name") or event.get("chatter_user_login") or ""),
                text=value, sent_at=self._event_timestamp(metadata),
                author_id=author_id, fragments=fragments, badges=badges,
                color=twitch_name_color(event.get("color")),
                avatar_url=avatar,
            ))
        elif event_type == "channel.chat.message_delete":
            message_id = str(event.get("message_id") or "")
            if message_id:
                state.delete_message("twitch", source_id, message_id)
        elif event_type == "channel.chat.clear_user_messages":
            author_id = str(event.get("target_user_id") or "")
            if author_id:
                state.clear_chat("twitch", source_id, author_id=author_id)
        elif event_type == "channel.chat.clear":
            state.clear_chat("twitch", source_id)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:

                if not self.service.connection_ready():
                    self.connected = False
                    self.chat_connected = False
                    if self.chat_state is not None:
                        self.chat_state.disconnect("twitch")
                    self._wait(1.0)
                    continue
                source_id, chat_ready = self._chat_profile()
                if source_id and self._chat_source_id and source_id != self._chat_source_id:
                    if self.chat_state is not None:
                        self.chat_state.change_source("twitch")
                    with self._media_lock:
                        self._third_party_catalog = {}
                        self._third_party_source = ""
                        self._third_party_next_refresh = 0.0
                if source_id:
                    self._chat_source_id = source_id
                if not self.service.managed_reward_ids() and not (
                    self.chat_state is not None and chat_ready
                ):
                    self.connected = False
                    self.chat_connected = False
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
            chat_source, chat_ready = self._chat_profile()
            chat_required = self.chat_state is not None and chat_ready
            if subscriptions_required:
                self._chat_subscription_active = False
                self.chat_error = ""
                # First subscription is created immediately after welcome to
                # satisfy Twitch's default 10-second unused-connection limit.
                for reward_id in reward_ids:
                    self.service.integration_manager.call_adapter(
                        TWITCH_SERVICE_KEY,
                        "create_eventsub_subscription",
                        session_id,
                        reward_id,
                    )

                if chat_required:
                    for event_type in TWITCH_CHAT_EVENT_TYPES:
                        try:
                            self.service.integration_manager.call_adapter(
                                TWITCH_SERVICE_KEY,
                                "create_chat_eventsub_subscription",
                                session_id,
                                event_type,
                            )
                        except Exception:
                            # A chat permission/provider failure must not stop
                            # a working Channel Points EventSub subscription.
                            self.chat_error = "Twitch chat subscription unavailable"
                            if not reward_ids:
                                raise
                            break
                        if event_type == "channel.chat.message":
                            self._chat_subscription_active = True
            self.chat_connected = bool(chat_required and self._chat_subscription_active)
            if self.chat_connected:
                self._schedule_media_warmup(chat_source)
                self._schedule_third_party_catalog(chat_source)
            current_row = self.service.db.get_integration_connection(TWITCH_SERVICE_KEY) or {}
            subscribed_credential_ref = str(current_row.get("credential_ref") or "")
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
                if self.chat_connected:
                    self._schedule_third_party_catalog(chat_source)
                if not self.service.connection_ready():
                    return ""
                current_ids = self.service.managed_reward_ids()
                current_source, current_chat = self._chat_profile()
                current_row = self.service.db.get_integration_connection(TWITCH_SERVICE_KEY) or {}
                credential_ref = str(current_row.get("credential_ref") or "")
                if (current_ids != reward_ids or current_source != chat_source
                        or credential_ref != subscribed_credential_ref
                        or (self.chat_state is not None and current_chat) != chat_required):
                    # The shared socket's subscriptions must match both services.
                    return ""
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
                        event_type = str(subscription.get("type") or "") if isinstance(subscription, dict) else ""
                        if event_type in TWITCH_CHAT_EVENT_TYPES:
                            self._process_chat_notification(
                                event_type, event, metadata if isinstance(metadata, dict) else {},
                            )
                        elif event_type == "channel.channel_points_custom_reward_redemption.add":
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
            self.chat_connected = False
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
