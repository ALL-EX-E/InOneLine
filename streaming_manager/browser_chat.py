from __future__ import annotations

"""D41-03: operator-selected, read-only local browser chat sources.

This is not a supported Twitch/YouTube API. Web-site markup may change and
platform terms may restrict automated extraction. No credentials are collected
by InOneLine, no scraping bypass is implemented, and no chat history is stored.
All Qt WebEngine objects live on the Qt GUI thread. OBS reads existing D41 RAM.
"""

from dataclasses import dataclass
import json
import re
import time
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript

from .multichat import ChatMessage, MultichatState

_YOUTUBE_VIDEO = re.compile(r"^[a-zA-Z0-9_-]{11}$")
_TWITCH_LOGIN = re.compile(r"^[a-zA-Z0-9_]{2,25}$")


@dataclass(frozen=True)
class BrowserChatSource:
    platform: str
    url: str
    channel: str
    source_id: str


def normalize_browser_chat_source(platform: str, url: str) -> BrowserChatSource:
    """Accept only supported popout chats; reject arbitrary browser URLs."""
    value = str(url or "").strip()
    if not value or len(value) > 1800 or any(ord(c) < 32 for c in value):
        raise ValueError("Введите адрес отдельного окна чата.")
    try:
        p = urlsplit(value)
        hostname = (p.hostname or "").lower().rstrip(".")
        if p.scheme != "https" or p.username or p.password or p.port not in (None, 443) or p.fragment:
            raise ValueError("Нужна HTTPS-ссылка на чат без логина и фрагмента.")
    except (ValueError, TypeError) as exc:
        raise ValueError("Некорректная HTTPS-ссылка на чат.") from exc
    params = parse_qs(p.query, keep_blank_values=False)
    if platform == "youtube":
        if hostname not in ("www.youtube.com", "youtube.com", "studio.youtube.com") or p.path != "/live_chat":
            raise ValueError("YouTube: вставьте ссылку отдельного окна Live Chat.")
        video = (params.get("v") or [""])[0]
        if not _YOUTUBE_VIDEO.fullmatch(video):
            raise ValueError("YouTube: в адресе чата отсутствует корректный ID трансляции.")
        safe_query = urlencode({"is_popout": "1", "v": video})
        # A Studio popout belongs to the operator's signed-in browser. Read
        # the equivalent public chat of exactly the same video instead: this
        # does not require copying Chrome cookies or adding Google OAuth.
        return BrowserChatSource(platform, urlunsplit(("https", "www.youtube.com", "/live_chat", safe_query, "")), video, video)
    if platform == "twitch":
        if hostname in ("www.twitch.tv", "twitch.tv"):
            match = re.fullmatch(r"/popout/([a-zA-Z0-9_]{2,25})/chat/?", p.path, re.I)
            if not match:
                raise ValueError("Twitch: нужна ссылка отдельного окна чата канала.")
            login = match.group(1).lower()
            return BrowserChatSource(platform, f"https://www.twitch.tv/popout/{login}/chat?popout=", login, login)
        if hostname == "dashboard.twitch.tv":
            match = re.fullmatch(r"/popout/u/([a-zA-Z0-9_]{2,25})/stream-manager/chat/?", p.path, re.I)
            if not match:
                raise ValueError("Twitch: нужна ссылка отдельного окна чата панели автора.")
            login = match.group(1).lower()
            # Dashboard chat normally depends on the owner's signed-in
            # browser. Use the equivalent public popout of that channel so
            # the invisible Qt reader needs no credentials or Chrome cookie.
            return BrowserChatSource(platform, f"https://www.twitch.tv/popout/{login}/chat?popout=", login, login)
        raise ValueError("Twitch: ссылка должна вести на twitch.tv или dashboard.twitch.tv.")
    raise ValueError("Неизвестная платформа браузерного чата.")


# Our own DOM read-only observer, bounded to prevent unbounded memory growth.
# The script is installed before the page populates its chat messages, but it
# intentionally skips all messages present in an initial 3-second baseline.
# It never clicks page controls, submits messages or obtains cookies.
_BROWSER_OBSERVER = r"""
(() => {
  if (window.__iolBrowserChat) return;
  const yt = location.hostname.endsWith('youtube.com');
  const selectors = yt
    ? 'yt-live-chat-text-message-renderer,yt-live-chat-paid-message-renderer,yt-live-chat-membership-item-renderer'
    : '.chat-line__message,[data-test-selector="chat-line-message"]';
  const observed = new WeakSet();
  const events = [];
  let serial = 0;
  let dropped = 0;
  let baseline = false;
  function nodesUnder(root) {
    const found = [];
    if (root.nodeType === 1 && root.matches && root.matches(selectors)) found.push(root);
    if (root.querySelectorAll) root.querySelectorAll(selectors).forEach(n => found.push(n));
    return found;
  }
  function pickText(root, selector) {
    const node = root.querySelector(selector);
    return node ? (node.innerText || node.textContent || '').trim() : '';
  }
  function collect(el) {
    if (observed.has(el)) return;
    if (!baseline) { observed.add(el); return; }
    const author = yt
      ? pickText(el, '#author-name')
      : pickText(el, '.chat-author__display-name,[data-a-target="chat-message-username"]');
    const text = yt
      ? pickText(el, '#message')
      : pickText(el, '[data-a-target="chat-message-text"],.text-fragment');
    if (!author || !text) return;
    observed.add(el);
    const nativeId = yt ? (el.getAttribute('id') || '')
      : (el.getAttribute('data-id') || el.getAttribute('data-message-id') || '');
    const id = nativeId || ('dom-' + (++serial));
    if (events.length >= 512) { events.shift(); dropped++; }
    events.push({id, author: author.slice(0, 200), text: text.slice(0, 10000)});
  }
  // Baseline existing items, and give the site a short loading grace period.
  document.querySelectorAll(selectors).forEach(n => observed.add(n));
  setTimeout(() => {
    document.querySelectorAll(selectors).forEach(n => observed.add(n));
    baseline = true;
  }, 3000);
  const watcher = new MutationObserver(changes => {
    if (!baseline) return;
    for (const change of changes) {
      for (const node of change.addedNodes) nodesUnder(node).forEach(collect);
      if (change.target && change.target.nodeType === 1) {
        const target = change.target.closest && change.target.closest(selectors);
        if (target) collect(target);
      }
    }
  });
  if (document.documentElement) watcher.observe(document.documentElement,
    {childList:true,subtree:true,characterData:true});
  window.__iolBrowserChat = {
    drain() {
      const batch = events.splice(0, 100);
      const lost = dropped;
      dropped = 0;
      return {ready: baseline, alive: true, events: batch, dropped: lost};
    }
  };
})();
"""


class _BrowserChatPage(QObject):
    """One QWebEnginePage; no window or local user interaction needed."""

    def __init__(self, owner: "BrowserChatRuntime", platform: str):
        super().__init__(owner)
        self.owner = owner
        self.platform = platform
        self.page = QWebEnginePage(self)
        # There is intentionally no visible window. Tell Chromium that its
        # document itself is in a visible/active state, so the live chat isn't
        # voluntarily throttled like a background tab (Qt Page Visibility API).
        self.page.setVisible(True)
        self.page.setAudioMuted(True)
        self.source: BrowserChatSource | None = None
        self.status = "Не настроена ссылка."
        self._generation = 0
        self._last_reply = time.monotonic()
        self._next_retry = 0.0
        self._backoff = 5.0
        self._busy = False
        self.page.loadFinished.connect(self._loaded)
        self.page.renderProcessTerminated.connect(self._crashed)
        script = QWebEngineScript()
        script.setName("InOneLine-readonly-chat-observer")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        # Keep capture helpers isolated from page scripts and extensions.
        script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
        script.setRunsOnSubFrames(False)
        script.setSourceCode(_BROWSER_OBSERVER)
        self.page.scripts().insert(script)

    def set_source(self, source: BrowserChatSource | None) -> None:
        if self.source == source:
            return
        old = self.source
        self.source = source
        self._generation += 1
        self._busy = False
        self._backoff = 5.0
        self._next_retry = 0.0
        if old is not None and source is not None and old.source_id != source.source_id:
            self.owner.state.change_source(self.platform)
        elif source is None:
            self.owner.state.disconnect(self.platform)
        if source is None:
            self.page.setUrl(QUrl("about:blank"))
            self.status = "Отключён."
        else:
            self._load()

    def _load(self):
        if self.source is None:
            return
        self._generation += 1
        self._busy = False
        self._last_reply = time.monotonic()
        self.status = "Загрузка страницы чата..."
        self.page.setUrl(QUrl(self.source.url))
        try:
            self.page.setLifecycleState(QWebEnginePage.LifecycleState.Active)
        except (AttributeError, RuntimeError):
            pass

    def _loaded(self, ok: bool):
        if self.source is None:
            return
        if not ok:
            self._fail("Страница не загрузилась.")
            return
        self._backoff = 5.0
        self._last_reply = time.monotonic()
        self.status = "Страница открыта, ожидание новых сообщений."

    def _crashed(self, *_args):
        if self.source is not None:
            self._fail("Процесс браузера завершился, восстановление...")

    def _fail(self, reason: str):
        self._generation += 1
        self._busy = False
        self.status = reason
        self._next_retry = time.monotonic() + self._backoff
        self._backoff = min(120.0, self._backoff * 2)

    def poll(self):
        if self.source is None:
            return
        now = time.monotonic()
        if self._next_retry and now < self._next_retry:
            return
        if self._next_retry:
            self._next_retry = 0
            self._load()
            return
        if self._busy:
            if now - self._last_reply > 25.0:
                self._fail("Браузер не отвечает, переподключение...")
            return
        source_id, generation = self.source.source_id, self._generation
        self._busy = True
        self.page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat ? window.__iolBrowserChat.drain() : null)",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value, key=source_id, g=generation: self._received(value, key, g),
        )

    def _received(self, value, source_id: str, generation: int):
        if (self.source is None or generation != self._generation
                or source_id != self.source.source_id):
            return
        self._busy = False
        self._last_reply = time.monotonic()
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (ValueError, TypeError):
                value = None
        if not isinstance(value, dict) or not value.get("alive"):
            # Wait for a legitimate page and script to load; not a reason to
            # claim that an idle chat has disconnected.
            self.status = "Ожидание загрузки элементов чата."
            return
        self.status = "Чтение чата активно."
        dropped = value.get("dropped")
        if isinstance(dropped, int) and dropped > 0:
            self.status = f"Чат активен, очередь перегружена: потеряно {dropped} сообщений."
        for item in (value.get("events") or [])[:100]:
            if not isinstance(item, dict):
                continue
            uid = str(item.get("id") or "")[:160]
            if uid.startswith("dom-"):
                # DOM-local sequence restarts at 1 after a page reload.
                # Namespace it by page generation so new messages do not
                # collide with the bounded RAM dedupe keys of an old page.
                uid = f"page-{generation}-{uid}"
            author = str(item.get("author") or "")[:200]
            text = str(item.get("text") or "")[:10000]
            if not uid or not author or not text:
                continue
            self.owner.state.ingest(ChatMessage(
                platform=self.platform, source_id=source_id,
                external_id=uid, author=author, text=text,
            ))

    def shutdown(self):
        self._generation += 1
        self.source = None
        self.page.loadFinished.disconnect(self._loaded)
        self.page.renderProcessTerminated.disconnect(self._crashed)
        self.page.setUrl(QUrl("about:blank"))
        self.page.deleteLater()


class BrowserChatRuntime(QObject):
    """Read the selected popout locally; never connect OBS to the provider."""

    def __init__(self, db, state: MultichatState, parent: QObject | None = None):
        super().__init__(parent)
        self.db = db
        self.state = state
        # Pages are expensive Chromium processes: create only for configured
        # sources. InOneLine with no browser chat URLs retains its previous
        # lightweight startup, and native GUI regressions use no WebEngine.
        self._readers: dict[str, _BrowserChatPage | None] = {
            "youtube": None, "twitch": None,
        }
        self._source_errors: dict[str, str] = {}
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._tick)

    def start(self):
        self._timer.start()
        self._tick()

    def stop(self):
        self._timer.stop()
        for platform, reader in self._readers.items():
            if reader is not None:
                reader.shutdown()
            self._readers[platform] = None

    def status(self, platform: str) -> str:
        name = "YouTube" if platform == "youtube" else "Twitch"
        reader = self._readers[platform]
        return name + " (браузер): " + (
            reader.status if reader is not None
            else self._source_errors.get(platform, "Не настроена ссылка.")
        )

    def active(self, platform: str) -> bool:
        reader = self._readers[platform]
        return reader is not None and reader.source is not None

    def wake(self):
        self._tick()

    def _tick(self):
        twitch_mode = self.db.get_setting("multichat_twitch_reader", "eventsub")
        desired = {
            "youtube": self.db.get_setting("multichat_youtube_browser_url", ""),
            "twitch": (self.db.get_setting("multichat_twitch_browser_url", "")
                       if twitch_mode == "browser" else ""),
        }
        for platform, raw in desired.items():
            try:
                source = normalize_browser_chat_source(platform, raw) if raw else None
                self._source_errors.pop(platform, None)
            except ValueError as exc:
                source = None
                self._source_errors[platform] = str(exc)
            reader = self._readers[platform]
            if source is None:
                if reader is not None:
                    reader.set_source(None)
                    reader.shutdown()
                    self._readers[platform] = None
                continue
            if reader is None:
                reader = _BrowserChatPage(self, platform)
                self._readers[platform] = reader
            reader.set_source(source)
            reader.poll()
