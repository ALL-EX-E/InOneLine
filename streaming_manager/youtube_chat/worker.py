"""Cancellable connection state machine, independent of any window toolkit."""

from dataclasses import dataclass
import threading
import time

from .feed import Feed
from .transport import Transport, FetchError
from .multichat import to_multichat_events


MAX_POLL_INTERVAL = 2.0
RATE_LIMIT_BASE = 60.0
RATE_LIMIT_MAX = 900.0


@dataclass(frozen=True)
class Status:
    code: str
    text: str


@dataclass(frozen=True)
class Snapshot:
    video_id: str
    title: str
    messages: tuple
    counters: dict
    responses: int
    reconnects: int
    last_response: float
    server_delay: float
    poll_interval: float = 0.0


class Worker:
    def __init__(self, video_id, sink, *, show_history=False, transport=None,
                 clock=time.monotonic, wall_clock=time.time):
        self.video_id = video_id
        self.sink = sink
        self.transport = transport or Transport()
        self.clock = clock
        self.wall_clock = wall_clock
        self.feed = Feed(started_at=wall_clock(), show_history=show_history, clock=wall_clock)
        self.status = Status("connecting", "Подключаемся к YouTube…")
        self.stage = "bootstrap"
        self.active = True
        self.context = None
        self.token = None
        self.title = ""
        self.next_due = 0.0
        self.provider_cooldown = 0.0
        self.pause_until = 0.0
        self.failures = 0
        self.rate_limit_failures = 0
        self.responses = 0
        self.reconnects = 0
        self.event_sequence = 0
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self._reconnect = threading.Event()

    def _status(self, code, text):
        self.status = Status(code, text)
        if not self.stop_event.is_set():
            self.sink("status", self.status)

    def stop(self):
        self.stop_event.set()
        self.wake.set()

    def reconnect(self):
        self._reconnect.set()
        self.wake.set()

    def pause(self, seconds=20):
        self.pause_until = self.clock() + max(0, seconds)
        self.wake.set()

    def tick(self):
        if self.stop_event.is_set() or not self.active:
            return 0
        now = self.clock()
        if self._reconnect.is_set():
            self._reconnect.clear()
            self.pause_until = 0
            self.stage = "bootstrap"
            self.next_due = self.provider_cooldown
            self.failures = 0
            self.reconnects += 1
            self._status("connecting", "Обновляем подключение, сохраняя ленту…")
            if self.provider_cooldown > now:
                self._status("retrying", "YouTube ограничил частоту запросов. Ждём ещё "
                             + str(round(self.provider_cooldown - now)) + " с.")
        if self.pause_until > now:
            self._status("paused", "Проверочная пауза приёма. Чтение продолжится автоматически.")
            return self.pause_until - now
        if self.next_due > now:
            return self.next_due - now
        try:
            if self.stage == "bootstrap":
                self._status("connecting", "Открываем выбранный чат…")
                initial = self.transport.bootstrap(self.video_id)
                if self.stop_event.is_set():
                    return 0
                self.context, self.token, self.title = initial.context, initial.token, initial.title
                self.stage = "initial"
                self.next_due = self.clock()
                return 0
            result = self.transport.poll(self.context, self.token)
            if self.stop_event.is_set():
                return 0
            received_at = self.wall_clock()
            multichat_events = to_multichat_events(result.events, received_at, self.event_sequence)
            self.event_sequence += len(result.events)
            initializing = self.stage in {"initial", "selecting"}
            self.feed.apply(result.events, initializing=initializing)
            if initializing:
                visible_ids = {message.id for message in self.feed.messages}
                multichat_events = tuple(event for event in multichat_events
                    if event['kind'] not in {'add', 'replace'} or event['id'] in visible_ids)
            self.responses += 1
            self.token = result.token
            poll_interval = min(result.delay, MAX_POLL_INTERVAL)
            self.next_due = self.clock() + poll_interval
            if initializing:
                if result.all_selected:
                    self.stage = "reading"
                elif self.stage == "initial" and result.all_token:
                    self.stage, self.token = "selecting", result.all_token
                    self._status("connecting", "Включаем режим «Все сообщения»…")
                    return poll_interval
                else:
                    raise FetchError("YouTube не подтвердил режим «Все сообщения».", reset=True)
            self.failures = 0
            self.rate_limit_failures = 0
            self._status("connected", "Подключено · Все сообщения")
            if multichat_events:
                self.sink("multichat", multichat_events)
            self.sink("update", Snapshot(self.video_id, self.title, self.feed.messages, self.feed.counters(),
                                         self.responses, self.reconnects, self.wall_clock(),
                                         result.delay, poll_interval))
            return poll_interval
        except FetchError as exc:
            if self.stop_event.is_set():
                return 0
            self.failures += 1
            if not exc.retryable:
                self.active = False
                self._status("error", str(exc))
                return 0
            if exc.rate_limited:
                self.rate_limit_failures += 1
                rate_delay = min(RATE_LIMIT_BASE * (2 ** min(self.rate_limit_failures - 1, 4)),
                                 RATE_LIMIT_MAX)
                delay = max(rate_delay, exc.retry_after)
            else:
                delay = max(min(2 ** min(self.failures, 6), 60), exc.retry_after)
            if exc.retry_after:
                self.provider_cooldown = max(self.provider_cooldown, self.clock() + delay)
            elif exc.rate_limited:
                self.provider_cooldown = max(self.provider_cooldown, self.clock() + delay)
            self.next_due = self.clock() + delay
            if exc.reset:
                self.stage = "bootstrap"
                self.reconnects += 1
            self._status("retrying", str(exc) + " Следующая попытка через " + str(round(delay)) + " с.")
            return delay

    def run(self):
        try:
            while self.active and not self.stop_event.is_set():
                delay = self.tick()
                if delay > 0:
                    self.wake.wait(delay)
                    self.wake.clear()
        except Exception:
            # Unexpected provider changes must not leak a traceback or tokens into the UI.
            self.active = False
            self._status("error", "Не удалось обработать ответ YouTube. Попробуйте переподключиться.")
        finally:
            if self.stop_event.is_set():
                self.status = Status("stopped", "Отключено")
