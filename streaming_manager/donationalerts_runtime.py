from __future__ import annotations

"""DonationAlerts persistent intake service and resilient Centrifugo runtime."""

import json
import threading
import time
from decimal import Decimal, InvalidOperation
from typing import Callable

from .donationalerts import (
    DONATIONALERTS_CENTRIFUGO_URL,
    DONATIONALERTS_DONATION_EVENT_TYPE,
    DONATIONALERTS_SERVICE_KEY,
)
from .integrations import IntegrationError, IntegrationManager, NormalizedIntegrationEvent

# 0.3.64 used an explicit auction-only intake toggle and target-auction binding.
# Keep the legacy keys exported so old databases/tests/tools can still be read,
# but I1 no longer consults them.  A connected DonationAlerts integration is a
# permanent contribution source both inside and outside auctions.
DONATIONALERTS_TRACKING_ENABLED_KEY = "donationalerts_tracking_enabled"
DONATIONALERTS_TARGET_AUCTION_ID_KEY = "donationalerts_target_auction_id"
DONATIONALERTS_LAST_SEEN_ID_KEY = "donationalerts_last_seen_id"
DONATIONALERTS_CURSOR_INITIALIZED_KEY = "donationalerts_cursor_initialized"


class DonationAlertsDonationService:
    """Maps DonationAlerts donations into the common B3 contribution contract.

    Product rule: connection is the permission.  While DonationAlerts is enabled
    and connected, new donations are accepted continuously.  Source timestamps
    decide whether an event belongs to a running auction or to the persistent
    game list outside auctions, so delayed delivery can never leak into a newer
    auction.

    The first run after a brand-new/intentional connection snapshots the newest
    remote donation ID.  That prevents importing the user's historic DonationAlerts
    archive.  Temporary runtime failures keep the cursor and are recovered by REST
    catch-up on reconnect.
    """

    def __init__(
        self,
        db,
        integration_manager: IntegrationManager,
        *,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        self.db = db
        self.integration_manager = integration_manager
        self.sleeper = sleeper
        self._state_lock = threading.RLock()

    def connection_ready(self) -> bool:
        row = self.db.get_integration_connection(DONATIONALERTS_SERVICE_KEY)
        return bool(
            row is not None
            and bool(row.get("enabled"))
            and str(row.get("status") or "") == "connected"
        )

    def last_seen_id(self) -> int:
        raw = self.db.get_setting(DONATIONALERTS_LAST_SEEN_ID_KEY, "0")
        try:
            return max(0, int(raw or 0))
        except (TypeError, ValueError):
            return 0

    def cursor_initialized(self) -> bool:
        explicit = self.db.get_setting(DONATIONALERTS_CURSOR_INITIALIZED_KEY, "")
        if str(explicit).strip() == "1":
            return True
        # Seamless 0.3.64 upgrade: if the old tracking flow already established
        # a high-water cursor, preserve it instead of skipping newer donations.
        return self.last_seen_id() > 0

    @staticmethod
    def _rows(payload: dict) -> list[dict]:
        rows = payload.get("data") or []
        return [dict(row) for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []

    @staticmethod
    def _donation_id(row: dict) -> int:
        try:
            return max(0, int(row.get("id") or 0))
        except (TypeError, ValueError):
            return 0

    def _latest_remote_id(self) -> int:
        payload = self.integration_manager.call_adapter(
            DONATIONALERTS_SERVICE_KEY,
            "list_donations_page",
            1,
        )
        return max((self._donation_id(row) for row in self._rows(payload)), default=0)

    def ensure_cursor_initialized(self) -> int:
        """Establish a one-time history baseline without importing old donations."""
        if not self.connection_ready():
            raise IntegrationError(
                "DonationAlerts должен быть включён и находиться в состоянии «Подключено»."
            )
        with self._state_lock:
            if self.cursor_initialized():
                # Materialize the explicit marker for upgraded 0.3.64 databases.
                if self.db.get_setting(DONATIONALERTS_CURSOR_INITIALIZED_KEY, "") != "1":
                    self.db.set_setting(DONATIONALERTS_CURSOR_INITIALIZED_KEY, "1")
                return self.last_seen_id()
            baseline = self._latest_remote_id()
            self.db.set_settings_bulk(
                {
                    DONATIONALERTS_LAST_SEEN_ID_KEY: str(baseline),
                    DONATIONALERTS_CURSOR_INITIALIZED_KEY: "1",
                    # Retire 0.3.64 auction-only state explicitly.
                    DONATIONALERTS_TRACKING_ENABLED_KEY: "",
                    DONATIONALERTS_TARGET_AUCTION_ID_KEY: "",
                }
            )
            return baseline

    def on_connection_removed(self) -> None:
        """An intentional local removal starts with a fresh baseline next time."""
        self.db.set_settings_bulk(
            {
                DONATIONALERTS_LAST_SEEN_ID_KEY: "0",
                DONATIONALERTS_CURSOR_INITIALIZED_KEY: "0",
                DONATIONALERTS_TRACKING_ENABLED_KEY: "",
                DONATIONALERTS_TARGET_AUCTION_ID_KEY: "",
            }
        )

    def mark_seen(self, donation_id: int) -> None:
        donation_id = max(0, int(donation_id))
        with self._state_lock:
            current = self.last_seen_id()
            if donation_id > current:
                self.db.set_setting(DONATIONALERTS_LAST_SEEN_ID_KEY, str(donation_id))
            if self.db.get_setting(DONATIONALERTS_CURSOR_INITIALIZED_KEY, "") != "1":
                self.db.set_setting(DONATIONALERTS_CURSOR_INITIALIZED_KEY, "1")

    def _normalize_donation(self, raw: dict) -> dict:
        row = dict(raw or {})
        donation_id = self._donation_id(row)
        if donation_id <= 0:
            raise ValueError("DonationAlerts donation не содержит корректный уникальный ID.")
        amount_raw = row.get("amount")
        try:
            amount = Decimal(str(amount_raw))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("DonationAlerts donation содержит некорректную сумму.") from exc
        if not amount.is_finite() or amount < 0:
            raise ValueError("DonationAlerts donation содержит некорректную сумму.")
        currency = str(row.get("currency") or "").strip().upper()
        if len(currency) != 3 or not currency.isalpha() or not currency.isascii():
            raise ValueError("DonationAlerts donation содержит некорректную валюту.")
        username = str(row.get("username") or row.get("name") or "").strip()
        message = str(row.get("message") or "").strip()
        return {
            "id": donation_id,
            "amount": str(amount),
            "currency": currency,
            "username": username,
            "message": message,
            "message_type": str(row.get("message_type") or ""),
            "created_at": str(row.get("created_at") or ""),
            "shown_at": str(row.get("shown_at") or ""),
            "is_shown": row.get("is_shown"),
            "raw": row,
        }

    def process_donation(self, raw: dict) -> dict:
        donation = self._normalize_donation(raw)
        donation_id = int(donation["id"])
        if donation_id <= self.last_seen_id():
            return {"status": "duplicate_cursor", "donation_id": donation_id}
        if not self.connection_ready():
            raise IntegrationError(
                "DonationAlerts должен быть включён и находиться в состоянии «Подключено»."
            )

        # Provider creation time, not desktop delivery time, selects auction
        # context. Missing/invalid provider time fails safely to an outside-
        # auction persistent top-up rather than contaminating a newer session.
        source_auction_id = self.db.find_running_auction_at(donation["created_at"])
        event = NormalizedIntegrationEvent(
            service_key=DONATIONALERTS_SERVICE_KEY,
            external_event_id=str(donation_id),
            event_type=DONATIONALERTS_DONATION_EVENT_TYPE,
            source_amount=donation["amount"],
            source_unit=donation["currency"],
            source_unit_label=donation["currency"],
            unit_kind="currency",
            contributor=donation["username"],
            # DonationAlerts' message is the viewer-provided game/lot target.
            # B3 performs the existing exact normalized title reuse/new-game rule.
            lot_title=donation["message"],
            note="DonationAlerts donation",
            provider_metadata={
                "donation_id": donation_id,
                "message": donation["message"],
                "message_type": donation["message_type"],
                "created_at": donation["created_at"],
                "shown_at": donation["shown_at"],
                "is_shown": donation["is_shown"],
                "username": donation["username"],
            },
            auction_id_hint=source_auction_id,
            force_outside_auction=source_auction_id is None,
        )
        result = self.integration_manager.accept_normalized_event(event)
        self.mark_seen(donation_id)
        return result

    def catch_up(self, *, max_pages: int = 50) -> int:
        """Recover unseen donations while preserving API rate-limit headroom."""
        if not self.connection_ready():
            return 0
        self.ensure_cursor_initialized()
        after_id = self.last_seen_id()
        unseen: dict[int, dict] = {}
        for page in range(1, max(1, int(max_pages)) + 1):
            payload = self.integration_manager.call_adapter(
                DONATIONALERTS_SERVICE_KEY,
                "list_donations_page",
                page,
            )
            rows = self._rows(payload)
            if not rows:
                break
            ids = [self._donation_id(row) for row in rows if self._donation_id(row) > 0]
            for row in rows:
                row_id = self._donation_id(row)
                if row_id > after_id:
                    unseen[row_id] = row
            # API examples are newest-first. As soon as one page reaches the
            # persisted cursor, older pages cannot contain unseen IDs.
            if ids and min(ids) <= after_id:
                break
            meta = payload.get("meta") or {}
            last_page = int(meta.get("last_page") or page) if isinstance(meta, dict) else page
            if page >= last_page:
                break
            # DonationAlerts documents a 60 requests/minute application limit.
            self.sleeper(1.05)

        processed = 0
        for donation_id in sorted(unseen):
            self.process_donation(unseen[donation_id])
            processed += 1
        return processed


class DonationAlertsRuntime:
    """One reconnecting Centrifugo WebSocket loop for DonationAlerts."""

    def __init__(
        self,
        service: DonationAlertsDonationService,
        *,
        socket_factory: Callable[[str], object] | None = None,
        retry_seconds: float = 5.0,
        handshake_timeout_seconds: float = 6.0,
    ):
        self.service = service
        self.socket_factory = socket_factory or self._default_socket_factory
        self.retry_seconds = max(0.2, float(retry_seconds))
        self.handshake_timeout_seconds = max(0.2, float(handshake_timeout_seconds))
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._socket = None
        # Donation pushes can legally race with command replies on the same
        # WebSocket. Keep them across reconnect attempts until REST catch-up has
        # established the contiguous high-water cursor and they can be applied
        # safely in source-ID order.
        self._pending_donations: dict[int, dict] = {}
        self.last_error = ""
        self.connected = False

    @staticmethod
    def _default_socket_factory(url: str):
        import websocket

        return websocket.create_connection(url, timeout=2.0, enable_multithread=True)

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="DonationAlertsCentrifugo",
            daemon=True,
        )
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
        try:
            payload = json.loads(str(raw))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise IntegrationError(
                "DonationAlerts Centrifugo прислал некорректный JSON frame."
            ) from exc
        if not isinstance(payload, dict):
            raise IntegrationError(
                "DonationAlerts Centrifugo прислал некорректный JSON frame."
            )
        return payload

    @staticmethod
    def _send_json(sock, payload: dict) -> None:
        sock.send(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))

    @staticmethod
    def _is_timeout_exception(exc: Exception) -> bool:
        return exc.__class__.__name__ in {
            "WebSocketTimeoutException",
            "TimeoutError",
            "socket.timeout",
        }

    @staticmethod
    def _centrifugo_error_text(message: dict) -> str:
        error = message.get("error")
        if not error:
            result = message.get("result")
            if isinstance(result, dict):
                error = result.get("error")
        if not error:
            return ""
        if isinstance(error, dict):
            code = error.get("code")
            detail = str(error.get("message") or error.get("reason") or "").strip()
            parts = []
            if code not in (None, ""):
                parts.append(f"код {code}")
            if detail:
                parts.append(detail)
            return ": ".join(parts) if parts else json.dumps(error, ensure_ascii=False)
        return str(error).strip()

    def _queue_handshake_donation(self, message: dict) -> bool:
        donation = self._extract_donation(message)
        if donation is None:
            return False
        donation_id = self.service._donation_id(donation)
        if donation_id > 0:
            self._pending_donations[donation_id] = dict(donation)
        return True

    def _wait_for_handshake_reply(
        self,
        sock,
        *,
        phase: str,
        expected_id: int,
        matcher: Callable[[dict], bool],
    ) -> dict:
        """Wait for the intended command reply without consuming async pushes.

        DonationAlerts currently documents Centrifugo 2.x-shaped JSON where the
        private-channel ACK may omit ``id`` entirely. Therefore matching cannot
        rely on a single next ``recv()`` nor solely on command correlation IDs.
        We accept the documented structural ACK, ignore service frames/pings,
        preserve donation pushes, and fail with provider error details when the
        server explicitly rejects the command.
        """
        deadline = time.monotonic() + self.handshake_timeout_seconds
        while not self._stop.is_set():
            if time.monotonic() >= deadline:
                raise IntegrationError(
                    f"DonationAlerts Centrifugo: превышено время ожидания {phase}."
                )
            try:
                message = self._recv_json(sock)
            except Exception as exc:
                if self._is_timeout_exception(exc):
                    continue
                raise

            # Empty JSON objects are Centrifugo application-level service frames
            # (including ping in newer protocol generations). They are not ACKs.
            if not message:
                continue

            if self._queue_handshake_donation(message):
                continue

            error_text = self._centrifugo_error_text(message)
            if error_text:
                message_id = message.get("id")
                if message_id in (None, expected_id, str(expected_id)):
                    raise IntegrationError(
                        f"DonationAlerts Centrifugo ({phase}): {error_text}."
                    )

            if matcher(message):
                return message

            message_id = message.get("id")
            if message_id in (expected_id, str(expected_id)):
                raise IntegrationError(
                    f"DonationAlerts Centrifugo прислал некорректный ответ для {phase}."
                )
            # Unsolicited pushes and replies to unrelated command IDs are valid on
            # a multiplexed WebSocket and must not abort the current handshake.

        raise IntegrationError("DonationAlerts Centrifugo: подключение остановлено.")

    def _flush_pending_donations(self) -> None:
        for donation_id in sorted(tuple(self._pending_donations)):
            donation = self._pending_donations.get(donation_id)
            if donation is None:
                continue
            if donation_id <= self.service.last_seen_id():
                self._pending_donations.pop(donation_id, None)
                continue
            self.service.process_donation(donation)
            self._pending_donations.pop(donation_id, None)

    @staticmethod
    def _extract_donation(message: dict) -> dict | None:
        result = message.get("result") or {}
        if not isinstance(result, dict):
            return None
        outer = result.get("data") or {}
        if not isinstance(outer, dict):
            return None
        candidate = outer.get("data") if isinstance(outer.get("data"), dict) else outer
        if not isinstance(candidate, dict):
            return None
        if candidate.get("id") is None or candidate.get("amount") is None:
            return None
        return dict(candidate)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                if not self.service.connection_ready():
                    self.connected = False
                    self._wait(1.0)
                    continue
                self.service.ensure_cursor_initialized()
                self._run_connection()
            except Exception as exc:
                self.last_error = str(exc)
                self.connected = False
                if not self._stop.is_set():
                    self._wait(self.retry_seconds)

    def _run_connection(self) -> None:
        snapshot = self.service.integration_manager.call_adapter(
            DONATIONALERTS_SERVICE_KEY,
            "runtime_snapshot",
        )
        access = str(snapshot.get("access") or "")
        user_id = str(snapshot.get("user_id") or "")
        socket_token = str(snapshot.get("socket_connection_token") or "")
        if not access or not user_id or not socket_token:
            raise IntegrationError("DonationAlerts runtime snapshot неполон.")
        channel = f"$alerts:donation_{user_id}"

        sock = self.socket_factory(DONATIONALERTS_CENTRIFUGO_URL)
        self._socket = sock
        try:
            self._send_json(sock, {"params": {"token": socket_token}, "id": 1})
            welcome = self._wait_for_handshake_reply(
                sock,
                phase="подтверждения подключения",
                expected_id=1,
                matcher=lambda message: bool(
                    message.get("id") in (1, "1")
                    and isinstance(message.get("result"), dict)
                    and str((message.get("result") or {}).get("client") or "")
                ),
            )
            result = welcome.get("result") or {}
            centrifugo_client_id = str(result.get("client") or "") if isinstance(result, dict) else ""
            if not centrifugo_client_id:
                raise IntegrationError("DonationAlerts Centrifugo не вернул client ID.")

            channel_token = self.service.integration_manager.call_adapter(
                DONATIONALERTS_SERVICE_KEY,
                "subscribe_centrifugo",
                centrifugo_client_id,
                channel,
            )
            self._send_json(
                sock,
                {
                    "params": {"channel": channel, "token": str(channel_token)},
                    "method": 1,
                    "id": 2,
                },
            )
            def donation_channel_ack(message: dict) -> bool:
                result = message.get("result")
                if not isinstance(result, dict):
                    return False
                reply_channel = str(result.get("channel") or "")
                # DonationAlerts documents a Centrifugo 2.x-shaped structural
                # ACK that repeats the private channel and may omit command id.
                if reply_channel:
                    return reply_channel == channel
                # Live DonationAlerts can also return a modern correlated
                # command ACK such as {"id": 2, "result": {}}.  Correlation
                # plus a result object and no provider error is sufficient; the
                # channel was already fixed in the command and token request.
                return message.get("id") in (2, "2")

            self._wait_for_handshake_reply(
                sock,
                phase="подтверждения donation-канала",
                expected_id=2,
                matcher=donation_channel_ack,
            )

            self.connected = True
            self.last_error = ""
            # Socket is subscribed before REST catch-up, closing the gap between
            # baseline and realtime intake. Catch-up must run before queued pushes
            # so the monotonic cursor cannot leap over lower unseen donation IDs.
            # B3/source-ID dedup makes overlap with queued realtime events safe.
            self.service.catch_up()
            self._flush_pending_donations()

            while not self._stop.is_set():
                if not self.service.connection_ready():
                    return
                try:
                    message = self._recv_json(sock)
                except Exception as exc:
                    if self._is_timeout_exception(exc):
                        continue
                    raise
                if not message:
                    continue
                donation = self._extract_donation(message)
                if donation is None:
                    continue
                donation_id = self.service._donation_id(donation)
                if donation_id <= self.service.last_seen_id():
                    continue
                self._pending_donations[donation_id] = dict(donation)
                self._flush_pending_donations()
        finally:
            self.connected = False
            self._socket = None
            try:
                sock.close()
            except Exception:
                pass


__all__ = [
    "DONATIONALERTS_TRACKING_ENABLED_KEY",
    "DONATIONALERTS_LAST_SEEN_ID_KEY",
    "DONATIONALERTS_TARGET_AUCTION_ID_KEY",
    "DONATIONALERTS_CURSOR_INITIALIZED_KEY",
    "DonationAlertsDonationService",
    "DonationAlertsRuntime",
]
