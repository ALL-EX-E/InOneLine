from __future__ import annotations

"""D41-03: one YouTube live-chat reader sharing the D41 RAM/OBS message state.

No API call or polling occurs on the Qt GUI or OBS HTTP threads. YouTube
broadcast selection is ephemeral: cancellations do not survive app restart.
"""
import threading
import time
from datetime import datetime
from typing import Callable

from .integrations import IntegrationAuthRequired, IntegrationTemporaryError
from .multichat import ChatMessage, MultichatState
from .youtube import YouTubeApi, YouTubeHttpError, YOUTUBE_SERVICE_KEY


def _iso_seconds(raw: object) -> float | None:
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError, OverflowError):
        return None


def _broadcast_choices(rows: list[dict], channel_id: str) -> list[dict]:
    choices = []
    seen = set()
    for row in rows:
        data = row.get("snippet") or {}
        identifier = str(row.get("id") or "")
        owner = str(data.get("channelId") or "")
        # Never silently bind another channel when ownership is unprovable.
        if not identifier or not owner or owner != channel_id or identifier in seen:
            continue
        seen.add(identifier)
        choices.append({
            "id": identifier, "title": str(data.get("title") or identifier),
            "live_chat_id": str(data.get("liveChatId") or ""),
        })
    return choices


def _consume_message(state: MultichatState, chat_id: str, row: dict) -> None:
    snippet = row.get("snippet") or {}
    kind = str(snippet.get("type") or "")
    if kind == "messageDeletedEvent":
        deleted = str((snippet.get("messageDeletedDetails") or {}).get("deletedMessageId") or "")
        if deleted:
            state.delete_message("youtube", chat_id, deleted)
        return
    if kind == "userBannedEvent":
        details = snippet.get("userBannedDetails") or {}
        uid = str((details.get("bannedUserDetails") or {}).get("channelId") or "")
        if uid and details.get("banType") == "permanent":
            state.clear_chat("youtube", chat_id, author_id=uid)
        return
    identifier = str(row.get("id") or "")
    if not identifier:
        return
    if kind not in (
        "textMessageEvent", "superChatEvent", "superStickerEvent",
        "newSponsorEvent", "memberMilestoneChatEvent",
        "membershipGiftingEvent", "giftMembershipReceivedEvent",
    ):
        return
    author = row.get("authorDetails") or {}
    display = str(snippet.get("displayMessage") or "")
    if not display:
        display = str((snippet.get("textMessageDetails") or {}).get("messageText") or "")
    if not display:
        return  # No invented fake placeholder or media.
    state.ingest(ChatMessage(
        platform="youtube", source_id=chat_id, external_id=identifier,
        author=str(author.get("displayName") or "YouTube"),
        text=display, author_id=str(author.get("channelId") or ""),
        sent_at=_iso_seconds(snippet.get("publishedAt")),
    ))


class YouTubeChatRuntime:
    """Independent YouTube state machine; accepts official API results only."""

    def __init__(self, db, integration_manager, state: MultichatState, *,
                 api: YouTubeApi | None = None,
                 selection_required: Callable[[list[dict]], None] | None = None):
        self.db = db
        self.manager = integration_manager
        self.state = state
        self.api = api or YouTubeApi()
        self.selection_required = selection_required
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread = None
        self._status = "YouTube: не подключён."
        self._channel_id = ""
        self._channel_name = ""
        self._selected = ""
        self._live_chat_id = ""
        self._page_token: str | None = None
        self._choices: list[dict] = []
        self._cancelled = False
        self._offer_open = False
        self._previous_ended = False
        self._next_discovery = 0.0
        self._next_message_poll = 0.0

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="YouTubeChat", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._wake.set()
        if self._thread:
            self._thread.join(timeout=5)

    def wake(self):
        self._wake.set()

    def status(self) -> str:
        with self._lock:
            return self._status

    def channel_name(self) -> str:
        with self._lock:
            return self._channel_name

    def choices(self) -> list[dict]:
        with self._lock:
            return [dict(x) for x in self._choices]

    def choice_required(self) -> bool:
        with self._lock:
            return bool(self._choices) and (self._cancelled or self._offer_open)

    def choose_broadcast(self, broadcast_id: str | None):
        with self._lock:
            if not broadcast_id:
                self._cancelled = True
                self._offer_open = False
                self._status = "YouTube: выбор трансляции отменён. Откройте список вручную."
            elif any(x["id"] == broadcast_id for x in self._choices):
                self._activate(next(x for x in self._choices if x["id"] == broadcast_id))
                self._cancelled = False
                self._offer_open = False
                self._choices = []
            else:
                return False
        self.wake()
        return True

    def request_selection(self):
        """Operator explicitly reopens the current fresh choice list."""
        with self._lock:
            self._cancelled = False
            self._offer_open = False
            self._next_discovery = 0.0
        self.wake()

    def _status_update(self, text: str):
        with self._lock:
            self._status = text

    def _activate(self, item: dict):
        new_broadcast = item["id"]
        new_chat = item["live_chat_id"]
        # Only a proven new source clears old YouTube messages. Ordinary network
        # failures and broadcaster end never clear them.
        if self._selected and (self._selected != new_broadcast or self._live_chat_id != new_chat):
            self.state.change_source("youtube")
        self._selected = new_broadcast
        self._live_chat_id = new_chat
        self._page_token = None
        self._previous_ended = False
        self._next_message_poll = 0.0
        self._status = (f"YouTube: эфир «{item['title']}», подключение чата."
                        if new_chat else f"YouTube: у эфира «{item['title']}» чат недоступен.")

    def _on_disabled(self):
        with self._lock:
            self.state.disconnect("youtube")
            self._selected = ""
            self._live_chat_id = ""
            self._page_token = None
            self._choices = []
            self._offer_open = False
            self._cancelled = False
            self._previous_ended = False
            self._next_discovery = 0
            self._next_message_poll = 0
            self._status = "YouTube: отключён или требуется авторизация."

    def _run(self):
        while not self._stop.is_set():
            wait = 15.0
            try:
                wait = self._cycle()
            except IntegrationAuthRequired:
                self._status_update("YouTube: требуется авторизация через «Интеграции».")
                wait = 20.0
            except IntegrationTemporaryError:
                self._status_update("YouTube: соединение временно недоступно, повторная попытка.")
                wait = 20.0
            except YouTubeHttpError as exc:
                if exc.status == 401:
                    self._status_update("YouTube: повторно авторизуйте Google в «Интеграциях».")
                elif exc.reason in ("liveChatDisabled", "liveChatEnded", "liveChatNotFound"):
                    self._status_update("YouTube: чат выбранного эфира недоступен.")
                elif exc.reason in ("rateLimitExceeded", "quotaExceeded", "userRateLimitExceeded"):
                    self._status_update("YouTube: превышены квоты API, повторная попытка позднее.")
                    wait = 120.0
                else:
                    self._status_update("YouTube: ошибка API; повторная попытка.")
                wait = max(wait, 30.0)
            except Exception:
                self._status_update("YouTube: не удалось получить сообщения, повторная попытка.")
                wait = 30.0
            self._wake.wait(max(0.25, wait))
            self._wake.clear()

    def _cycle(self) -> float:
        row = self.db.get_integration_connection(YOUTUBE_SERVICE_KEY) or {}
        if not row.get("enabled") or row.get("status") != "connected":
            self._on_disabled()
            return 20.0
        conf = row.get("provider_config") or {}
        channel_id = str(conf.get("youtube_channel_id") or "")
        channel_name = str(conf.get("youtube_channel_name") or "")
        if not channel_id or not channel_name:
            self._status_update("YouTube: авторизованный канал не определён. Переподключите Google.")
            return 20.0
        with self._lock:
            if self._channel_id and self._channel_id != channel_id:
                self.state.change_source("youtube")
                self._selected = ""
                self._live_chat_id = ""
                self._page_token = None
                self._choices = []
                self._cancelled = False
                self._offer_open = False
            self._channel_id = channel_id
            self._channel_name = channel_name
        access = self.manager.call_adapter(YOUTUBE_SERVICE_KEY, "account_access")
        now = time.monotonic()
        if now >= self._next_discovery:
            active = _broadcast_choices(self.api.broadcasts(access), channel_id)
            self._update_broadcasts(active)
            self._next_discovery = time.monotonic() + 45.0

        with self._lock:
            chat_id = self._live_chat_id
            active_selection = self._selected
        if not active_selection or not chat_id:
            return 8.0
        if time.monotonic() < self._next_message_poll:
            return max(0.5, self._next_message_poll - time.monotonic())
        # If a broadcast ended with another already live, keep the chosen
        # source pinned while the operator decides. Existing rows stay visible.
        page = self.api.chat_page(access, chat_id, self._page_token or "")
        next_token = str(page.get("nextPageToken") or "")
        if self._page_token is None:
            # Google's first page can include earlier chat history. It is never
            # delivered to the user, even if it contains deletion events.
            self._page_token = next_token or None
        else:
            for item in page.get("items") or ():
                _consume_message(self.state, chat_id, item)
            self._page_token = next_token or self._page_token
        interval = page.get("pollingIntervalMillis")
        try:
            seconds = max(1.0, min(120.0, float(interval) / 1000))
        except (ValueError, TypeError, OverflowError):
            seconds = 5.0
        self._next_message_poll = time.monotonic() + seconds
        self._status_update(f"YouTube: чат канала «{channel_name}» подключён.")
        return seconds

    def _update_broadcasts(self, active: list[dict]):
        offer = None
        with self._lock:
            by_id = {item["id"]: item for item in active}
            selected = self._selected
            if selected and selected in by_id:
                self._previous_ended = False
                self._choices = []
                self._offer_open = False
                self._status = f"YouTube: выбран эфир «{by_id[selected]['title']}»."
                return
            if selected:
                # Confirmed absence from an authoritative active-broadcast list.
                self._previous_ended = True
            if not active:
                self._choices = []
                self._offer_open = False
                self._status = ("YouTube: выбранный эфир завершён; ожидание нового."
                                if selected else "YouTube: нет активных трансляций.")
                return
            if len(active) == 1 and not self._cancelled and (not selected or not self._previous_ended):
                self._activate(active[0])
                self._choices = []
                self._offer_open = False
                return
            if len(active) == 1 and selected and self._previous_ended and not self._cancelled:
                # A different stream was already running when the old stream
                # ended: the operator must confirm a switch (D41-REQ-56).
                pass
            self._choices = [dict(x) for x in active]
            self._status = ("YouTube: выберите одну трансляцию."
                            if not self._cancelled else "YouTube: ожидание ручного выбора.")
            if not self._cancelled and not self._offer_open:
                self._offer_open = True
                offer = [dict(x) for x in active]
        if offer and self.selection_required:
            self.selection_required(offer)
