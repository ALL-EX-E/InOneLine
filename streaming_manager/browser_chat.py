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
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript, QWebEngineProfile

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
  const delivered = new WeakMap();
  const deliveredById = new Map();
  const removedIds = new Set();
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
  function push(event) {
    if (events.length >= 512) { events.shift(); dropped++; }
    events.push(event);
  }
  function nativeId(el) {
    return (yt ? el.getAttribute('id')
      : (el.getAttribute('data-id') || el.getAttribute('data-message-id'))) || '';
  }
  function authorOf(el) {
    return yt ? pickText(el, '#author-name')
      : pickText(el, '.chat-author__display-name,[data-a-target="chat-message-username"]');
  }
  function messageOf(el) {
    return yt ? pickText(el, '#message')
      : pickText(el, '[data-a-target="chat-message-text"],.text-fragment');
  }
  const deletedText = /^(?:[<\[]\s*)?(?:сообщение удалено(?: отправителем| модератором)?|сообщение было удалено(?: отправителем| модератором)?|message deleted(?: by (?:sender|author|moderator))?|message removed|this message was deleted|deleted by moderator|message retracted|сообщение отозвано)(?:\s*[>\]])?$/i;
  function deletionMarker(el, info) {
    // Verified against real YouTube Studio DOM (D41 QA 25 Oct 2026):
    // ordinary yt-live-chat-text-message-renderer rows have a nested
    // #deleted-state placeholder *before* deletion. Never treat its mere
    // presence as moderation. Actual deletion sets is-deleted on the
    // message renderer itself; the observer already watches this attribute.
    if (yt) {
      if (el.hasAttribute('is-deleted')) return true;
    } else if (
      el.matches('.chat-line__message--deleted,[data-a-target="chat-deleted-message"],[data-test-selector="chat-deleted-message"]') ||
      el.querySelector('[data-a-target="chat-deleted-message"],[data-test-selector="chat-deleted-message"],.chat-line__message--deleted')
    ) return true;
    const value = messageOf(el);
    const text = (value || el.innerText || el.textContent || '').trim();
    if (info && text === info.text) return false;
    // A normal message containing "deleted" is NOT a moderation command.
    // Only an exact platform tombstone can invalidate an existing item.
    return deletedText.test(text);
  }
  function markDeleted(info) {
    if (!info || removedIds.has(info.id)) return false;
    removedIds.add(info.id);
    deliveredById.delete(info.id);
    push({kind: 'delete', id: info.id});
    return true;
  }
  function removeKnown(el) {
    const native = nativeId(el);
    const info = delivered.get(el) || (native ? deliveredById.get(native) : null);
    if (!info || !deletionMarker(el, info)) return false;
    delivered.delete(el);
    markDeleted(info);
    return true;
  }
  function collect(el) {
    if (removeKnown(el)) return;
    if (observed.has(el)) return;
    if (!baseline) { observed.add(el); return; }
    // Never publish tombstones inserted after capture starts.
    if (deletionMarker(el, null)) { observed.add(el); return; }
    const author = authorOf(el);
    const text = messageOf(el);
    if (!author || !text) return;
    observed.add(el);
    const id = nativeId(el) || ('dom-' + (++serial));
    const info = {id, author, text};
    delivered.set(el, info);
    // A framework may replace the old renderer with a deletion tombstone
    // carrying the same stable platform ID. Retain a bounded recent index.
    if (nativeId(el)) {
      deliveredById.set(id, info);
      if (deliveredById.size > 1000) deliveredById.delete(deliveredById.keys().next().value);
    }
    push({kind: 'message', id, author: author.slice(0, 200), text: text.slice(0, 10000)});
  }
  function inspect(target) {
    if (!target) return;
    const el = target.nodeType === 1 ? target : target.parentElement;
    const row = el && el.closest && el.closest(selectors);
    if (row) collect(row);
  }
  function replacement(change) {
    // Some Twitch builds replace a row rather than changing its text.
    // A normal React rerender or scrolling away is NEVER a deletion.
    if (change.type !== 'childList' || !change.removedNodes.length || !change.addedNodes.length) return;
    const removed = [];
    const added = [];
    change.removedNodes.forEach(node => nodesUnder(node).forEach(el => {
      const item = delivered.get(el);
      if (item) removed.push(item);
    }));
    change.addedNodes.forEach(node => nodesUnder(node).forEach(el => {
      if (deletionMarker(el, {text: ''})) added.push(el);
    }));
    if (removed.length !== 1 || added.length !== 1) return;
    const old = removed[0], fresh = added[0], nextId = nativeId(fresh);
    const nextAuthor = authorOf(fresh);
    if ((nextId && nextId !== old.id) || (nextAuthor && nextAuthor !== old.author)) return;
    markDeleted(old);
  }
  // Baseline existing items and late first-rendered history.
  document.querySelectorAll(selectors).forEach(n => observed.add(n));
  setTimeout(() => {
    document.querySelectorAll(selectors).forEach(n => observed.add(n));
    baseline = true;
  }, 3000);
  const watcher = new MutationObserver(changes => {
    if (!baseline) return;
    for (const change of changes) {
      replacement(change);
      if (change.type === 'childList')
        for (const node of change.addedNodes) nodesUnder(node).forEach(collect);
      inspect(change.target);
    }
  });
  if (document.documentElement) watcher.observe(document.documentElement,
    {childList:true,subtree:true,characterData:true,attributes:true,
     attributeFilter:['is-deleted','class','data-a-target','data-test-selector']});
  window.__iolBrowserChat = {
    drain() {
      // Reconcile only the newest 200 rows, never remove messages merely
      // because a chat UI virtualizes or scrolls its older DOM nodes.
      if (baseline) {
        const latest = document.querySelectorAll(selectors);
        const begin = Math.max(0, latest.length - 200);
        for (let i = begin; i < latest.length; i++) collect(latest[i]);
      }
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
        # Each platform owns a distinct off-the-record Chromium profile.  Do
        # not share transient page state/cookies between concurrent providers.
        self.profile = QWebEngineProfile(self)
        self.page: QWebEnginePage | None = None
        self.source: BrowserChatSource | None = None
        self.status = "Не настроена ссылка."
        self._generation = 0
        self._last_reply = time.monotonic()
        self._next_retry = 0.0
        self._backoff = 5.0
        self._busy = False

    def _create_page(self):
        # A navigation can leave pending asynchronous callbacks or an obsolete
        # isolated JavaScript world. Replacing the QWebEnginePage per selected
        # source avoids carrying it to the next broadcast, while the profile
        # remains independent and alive for this platform.
        previous = self.page
        if previous is not None:
            previous.loadFinished.disconnect(self._loaded)
            previous.renderProcessTerminated.disconnect(self._crashed)
            previous.setUrl(QUrl("about:blank"))
            previous.deleteLater()
        page = QWebEnginePage(self.profile, self)
        page.setVisible(True)
        page.setAudioMuted(True)
        page.loadFinished.connect(self._loaded)
        page.renderProcessTerminated.connect(self._crashed)
        script = QWebEngineScript()
        script.setName("InOneLine-readonly-chat-observer")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
        script.setRunsOnSubFrames(False)
        script.setSourceCode(_BROWSER_OBSERVER)
        page.scripts().insert(script)
        self.page = page

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
            self._create_page()
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
            self._create_page()
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
            kind = str(item.get("kind") or "message")
            if kind == "delete":
                if uid:
                    self.owner.state.delete_message(self.platform, source_id, uid)
                continue
            if kind != "message":
                continue
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
        if self.page is not None:
            self.page.loadFinished.disconnect(self._loaded)
            self.page.renderProcessTerminated.disconnect(self._crashed)
            self.page.setUrl(QUrl("about:blank"))
            self.page.deleteLater()
            self.page = None
        self.profile.deleteLater()


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


    def collect_diagnostics(self, callback):
        """Read-only embedded page snapshots: no text, cookies, URLs with tokens or chat drain."""
        report = {
            "format": "InOneLine-D41-Qt-diagnostic-v1",
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sources": {},
        }
        outstanding = set()
        completed = False
        script = r"""(() => {
          const selectors = ['yt-live-chat-renderer','yt-live-chat-item-list-renderer',
            'yt-live-chat-text-message-renderer','yt-live-chat-deleted-message-renderer',
            '.chat-line__message','[data-test-selector="chat-line-message"]',
            '[data-a-target="chat-deleted-message"]'];
          const counts = {};
          for (const q of selectors) counts[q] = document.querySelectorAll(q).length;
          const body = document.body ? (document.body.innerText || '') : '';
          const frames = [...document.querySelectorAll('iframe')].slice(0, 12).map(e => {
            try {
              const host = new URL(e.src || 'about:blank', location.href).hostname;
              return /(^|\.)(youtube\.com|twitch\.tv)$/.test(host) ? host : 'other';
            } catch (_) { return 'unknown'; }
          });
          return JSON.stringify({
            pageHost:location.hostname,readyState:document.readyState,
            visibility:document.visibilityState,observerPresent:!!window.__iolBrowserChat,
            frameHosts:frames,counts,bodyTextLength:body.length,
            possibleLogin:/sign in to|log in to|войдите в аккаунт/i.test(body),
            possibleChallenge:/captcha|verify you are human|checking your browser/i.test(body)
          });
        })()"""

        def complete():
            nonlocal completed
            if completed:
                return
            completed = True
            for platform in outstanding:
                report["sources"][platform]["dom"] = {"error": "timeout"}
            callback(report)

        for platform in ("youtube", "twitch"):
            reader = self._readers[platform]
            if reader is None or reader.source is None or reader.page is None:
                report["sources"][platform] = {"connected": False, "status": self.status(platform)}
                continue
            page = reader.page
            report["sources"][platform] = {
                "connected": True, "status": reader.status,
                "pageHost": page.url().host(),
                "wantedHost": urlsplit(reader.source.url).hostname,
                "generation": reader._generation,
                "pollBusy": reader._busy,
                "lastReplyAgeSec": round(max(0.0, time.monotonic() - reader._last_reply), 2),
                "retryScheduled": reader._next_retry > time.monotonic(),
            }
            outstanding.add(platform)

            def ready(value, platform=platform):
                if completed or platform not in outstanding:
                    return
                outstanding.remove(platform)
                try:
                    parsed = json.loads(value) if isinstance(value, str) else None
                except (TypeError, ValueError):
                    parsed = None
                report["sources"][platform]["dom"] = parsed if isinstance(parsed, dict) else {
                    "error": "no_javascript_response",
                }
                if not outstanding:
                    complete()

            page.runJavaScript(script, QWebEngineScript.ScriptWorldId.ApplicationWorld, ready)
        if not outstanding:
            complete()
        else:
            QTimer.singleShot(6000, complete)
