from __future__ import annotations

"""D41 chat delivery state; shared by Qt and local OBS HTTP readers.

Provider adapters own their connections.  This module neither connects to
platforms nor persists chat text: one thread-safe, bounded RAM state is the
only source of published messages for both consumers.
"""

from collections import deque
from dataclasses import asdict, dataclass, replace
from math import isfinite
from threading import RLock
from time import monotonic, time
from typing import Callable


@dataclass(frozen=True)
class ChatMessage:
    platform: str
    source_id: str
    external_id: str
    author: str
    text: str
    sent_at: float | None = None
    received_at: float | None = None
    author_id: str = ""
    # D41-04: provider-verified presentation data only; never an HTML payload.
    fragments: tuple[dict, ...] = ()
    badges: tuple[dict, ...] = ()
    color: str = ""
    avatar_url: str = ""

    def __post_init__(self) -> None:
        if not self.platform or not self.source_id or not self.external_id:
            raise ValueError("Chat message requires platform, source and event IDs")
        if self.sent_at is not None and not isfinite(self.sent_at):
            raise ValueError("Invalid source timestamp")
        if self.received_at is not None and not isfinite(self.received_at):
            raise ValueError("Invalid reception timestamp")


class MultichatState:
    """Bounded current-session chat and a bounded optional delivery buffer.

    All public functions may be called by provider workers or Qt/HTTP readers.
    Delayed messages are admitted to OBS only when they become ready, using
    the *current* platform OBS permission.  Existing OBS messages are never
    removed just because that permission was switched off.
    """

    def __init__(
        self,
        *,
        limit: int = 100,
        delay: float = 0.0,
        clock: Callable[[], float] = monotonic,
        wall_clock: Callable[[], float] = time,
    ) -> None:
        self._lock = RLock()
        self._clock = clock
        self._wall_clock = wall_clock
        self._limit = self._valid_limit(limit)
        self._delay = self._valid_delay(delay)
        self._sequence = 0
        self._pending: list[tuple[float, int, ChatMessage]] = []
        self._operator: deque[ChatMessage] = deque(maxlen=self._limit)
        self._obs: deque[ChatMessage] = deque(maxlen=self._limit)
        self._obs_enabled: dict[str, bool] = {}
        self._seen: set[tuple[str, str, str]] = set()
        self._seen_order: deque[tuple[str, str, str]] = deque()
        self._seen_capacity = max(4096, self._limit * 4)
        self._overflow_count = 0
        self._show_time = True
        self._show_platform_icons = True

    @staticmethod
    def _valid_limit(value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or not 10 <= value <= 1000:
            raise ValueError("Chat limit must be an integer from 10 to 1000")
        return value

    @staticmethod
    def _valid_delay(value: float) -> float:
        try:
            delay = float(value)
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError("Invalid chat delay") from exc
        if not isfinite(delay) or delay < 0:
            raise ValueError("Chat delay must be a finite nonnegative number")
        return delay

    def configure(
        self,
        *,
        limit: int | None = None,
        delay: float | None = None,
        show_time: bool | None = None,
        show_platform_icons: bool | None = None,
    ) -> None:
        # Validate the entire change before mutating any field: an invalid
        # delay must never leave a partly-applied message limit behind.
        new_limit = self._valid_limit(limit) if limit is not None else None
        new_delay = self._valid_delay(delay) if delay is not None else None
        with self._lock:
            if new_limit is not None and new_limit != self._limit:
                self._operator = deque(self._operator, maxlen=new_limit)
                self._obs = deque(self._obs, maxlen=new_limit)
                self._limit = new_limit
                self._seen_capacity = max(4096, new_limit * 4)
                self._trim_seen()
            if new_delay is not None:
                self._delay = new_delay
            if show_time is not None:
                self._show_time = bool(show_time)
            if show_platform_icons is not None:
                self._show_platform_icons = bool(show_platform_icons)
            self._flush_ready(self._clock())
            self._shed_pending()

    def set_obs_enabled(self, platform: str, enabled: bool) -> None:
        with self._lock:
            self._obs_enabled[platform] = bool(enabled)

    def ingest(self, message: ChatMessage) -> bool:
        """Return False for a repeated event, True for a new received event."""
        if not isinstance(message, ChatMessage):
            raise TypeError("Expected ChatMessage")
        key = (message.platform, message.source_id, message.external_id)
        with self._lock:
            if key in self._seen:
                return False
            self._seen.add(key)
            self._seen_order.append(key)
            self._trim_seen()
            now = self._clock()
            received = self._wall_clock() if message.received_at is None else message.received_at
            item = replace(message, received_at=received)
            self._sequence += 1
            self._pending.append((now, self._sequence, item))
            self._flush_ready(now)
            self._shed_pending()
            return True

    def tick(self) -> None:
        with self._lock:
            self._flush_ready(self._clock())

    def delete_message(self, platform: str, source_id: str, external_id: str) -> None:
        """Provider-authenticated deletion, never a manual UI action."""
        with self._lock:
            def keep(m: ChatMessage) -> bool:
                return (m.platform, m.source_id, m.external_id) != (platform, source_id, external_id)
            self._pending = [p for p in self._pending if keep(p[2])]
            self._operator = deque((m for m in self._operator if keep(m)), maxlen=self._limit)
            self._obs = deque((m for m in self._obs if keep(m)), maxlen=self._limit)

    def clear_chat(self, platform: str, source_id: str, *, author_id: str | None = None) -> None:
        """Apply only an authenticated provider clear/ban to its own channel."""
        if not platform or not source_id or author_id == "":
            return
        with self._lock:
            def keep(m: ChatMessage) -> bool:
                return not (
                    m.platform == platform and m.source_id == source_id
                    and (author_id is None or m.author_id == author_id)
                )
            self._pending = [item for item in self._pending if keep(item[2])]
            self._operator = deque((m for m in self._operator if keep(m)), maxlen=self._limit)
            self._obs = deque((m for m in self._obs if keep(m)), maxlen=self._limit)

    def enrich_twitch_media(
        self, source_id: str, *, avatar_by_user: dict[str, str] | None = None,
        badge_urls: dict[tuple[str, str], str] | None = None,
    ) -> None:
        """Update media on messages still present, without recreating deleted rows.

        Only matching broadcaster records are touched. One RAM/OBS source of
        truth remains in place; delayed messages receive the same enrichment.
        """
        avatars = avatar_by_user or {}
        badge_map = badge_urls or {}
        if not avatars and not badge_map:
            return

        def enhanced(item: ChatMessage) -> ChatMessage:
            if item.platform != "twitch" or item.source_id != source_id:
                return item
            changes = {}
            avatar = avatars.get(item.author_id, "")
            if avatar and not item.avatar_url:
                changes["avatar_url"] = avatar
            if item.badges and badge_map:
                new_badges = tuple(
                    {**badge, "url": badge_map.get(
                        (str(badge.get("set_id") or ""), str(badge.get("id") or "")),
                        str(badge.get("url") or ""),
                    )} for badge in item.badges
                )
                if new_badges != item.badges:
                    changes["badges"] = new_badges
            return replace(item, **changes) if changes else item

        with self._lock:
            self._pending = [(t, seq, enhanced(item)) for t, seq, item in self._pending]
            self._operator = deque((enhanced(item) for item in self._operator), maxlen=self._limit)
            self._obs = deque((enhanced(item) for item in self._obs), maxlen=self._limit)

    def disconnect(self, platform: str) -> None:
        """Ordinary disconnect discards unpublished items, not shown history."""
        with self._lock:
            self._pending = [p for p in self._pending if p[2].platform != platform]

    def change_source(self, platform: str) -> None:
        """Only call after a confirmed change of account or chosen broadcast."""
        with self._lock:
            self.disconnect(platform)
            self._operator = deque((m for m in self._operator if m.platform != platform), maxlen=self._limit)
            self._obs = deque((m for m in self._obs if m.platform != platform), maxlen=self._limit)
            self._seen_order = deque(k for k in self._seen_order if k[0] != platform)
            self._seen = set(self._seen_order)

    def snapshot(self, *, for_obs: bool = False) -> dict:
        with self._lock:
            self._flush_ready(self._clock())
            messages = self._obs if for_obs else self._operator
            return {
                "messages": [asdict(m) for m in messages],
                "show_time": self._show_time,
                "show_platform_icons": self._show_platform_icons,
                "limit": self._limit,
                "delay": self._delay,
                "overflow_count": self._overflow_count,
            }

    def _trim_seen(self) -> None:
        while len(self._seen_order) > self._seen_capacity:
            self._seen.discard(self._seen_order.popleft())

    def _publish(self, items: list[tuple[float, int, ChatMessage]]) -> None:
        items.sort(key=lambda p: (
            p[2].sent_at if p[2].sent_at is not None else p[2].received_at,
            p[1],
        ))
        for _, _, message in items:
            self._operator.append(message)
            if self._obs_enabled.get(message.platform, True):
                self._obs.append(message)

    def _flush_ready(self, now: float) -> None:
        ready: list[tuple[float, int, ChatMessage]] = []
        pending: list[tuple[float, int, ChatMessage]] = []
        for item in self._pending:
            (ready if now - item[0] >= self._delay else pending).append(item)
        self._pending = pending
        if ready:
            self._publish(ready)

    def _shed_pending(self) -> None:
        # Large requested delays must never allow unbounded RAM growth.
        ceiling = max(20, 2 * self._limit)
        if len(self._pending) > ceiling:
            self._pending.sort(key=lambda item: item[1])
            excess = len(self._pending) - ceiling
            self._overflow_count += excess
            self._publish(self._pending[:excess])
            del self._pending[:excess]
