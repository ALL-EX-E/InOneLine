"""D41-03 read-only local capture; isolated deterministic regression.

No Twitch/Google account, no stream or external network is required.
"""
import os
import unittest
from unittest.mock import Mock

from streaming_manager.browser_chat import (
    BrowserChatRuntime, BrowserChatSource, _BROWSER_OBSERVER,
    normalize_browser_chat_source,
)
from streaming_manager.multichat import MultichatState


class Urls(unittest.TestCase):
    def test_youtube_studio_popout_from_user_screenshot(self):
        source = normalize_browser_chat_source(
            'youtube', 'https://studio.youtube.com/live_chat?is_popout=1&v=4cC65h_Tecc',
        )
        self.assertEqual(source.source_id, '4cC65h_Tecc')
        self.assertEqual(source.channel, '4cC65h_Tecc')
        self.assertTrue(source.url.startswith('https://www.youtube.com/live_chat?'))

    def test_youtube_regular_popout(self):
        source = normalize_browser_chat_source(
            'youtube', 'https://www.youtube.com/live_chat?v=AaBbCcDd123&is_popout=1',
        )
        self.assertEqual(source.source_id, 'AaBbCcDd123')
        self.assertNotIn('token', source.url)

    def test_twitch_dashboard_popout_from_user_screenshot(self):
        source = normalize_browser_chat_source(
            'twitch', 'https://dashboard.twitch.tv/popout/u/alex_say62/stream-manager/chat',
        )
        self.assertEqual(source.source_id, 'alex_say62')
        self.assertEqual(source.channel, 'alex_say62')
        self.assertEqual(source.url, 'https://www.twitch.tv/popout/alex_say62/chat?popout=')

    def test_twitch_public_popout(self):
        source = normalize_browser_chat_source('twitch', 'https://www.twitch.tv/popout/alex_say62/chat?popout=')
        self.assertEqual(source.source_id, 'alex_say62')

    def test_no_arbitrary_or_insecure_urls(self):
        invalid = [
            ('youtube','http://studio.youtube.com/live_chat?v=AaBbCcDd123'),
            ('youtube','https://studio.youtube.com.evil.test/live_chat?v=AaBbCcDd123'),
            ('youtube','https://studio.youtube.com/live_chat?v=bad'),
            ('youtube','https://studio.youtube.com/live_chat?is_popout=1&v=AaBbCcDd123#x'),
            ('youtube','https://www.youtube.com/watch?v=AaBbCcDd123'),
            ('twitch','https://www.twitch.tv/alex_say62'),
            ('twitch','https://dashboard.twitch.tv/popout/u/alex_say62/stream-manager/chat?token=x#x'),
            ('twitch','https://dashboard.twitch.tv@evil.test/popout/u/alex_say62/stream-manager/chat'),
            ('twitch','https://www.twitch.tv/popout/a/chat?popout='),
        ]
        for platform,url in invalid:
            with self.subTest(platform=platform,url=url):
                with self.assertRaises(ValueError):
                    normalize_browser_chat_source(platform,url)

    def test_known_query_is_whitelisted(self):
        source = normalize_browser_chat_source('youtube',
                    'https://www.youtube.com/live_chat?v=AaBbCcDd123&track=secret')
        self.assertNotIn('track', source.url)

    def test_observer_is_read_only_bounded_and_skips_history(self):
        self.assertIn('MutationObserver', _BROWSER_OBSERVER)
        self.assertIn('document.querySelectorAll(selectors).forEach(n => observed.add(n))', _BROWSER_OBSERVER)
        self.assertIn('baseline = true', _BROWSER_OBSERVER)
        self.assertIn('events.length >= 512', _BROWSER_OBSERVER)
        self.assertIn('events.splice(0, 100)', _BROWSER_OBSERVER)
        self.assertNotIn('fetch(', _BROWSER_OBSERVER)
        self.assertNotIn('click()', _BROWSER_OBSERVER)
        self.assertNotIn('localStorage', _BROWSER_OBSERVER)

    def test_offline_webengine_dom_observer_reads_new_only(self):
        """Native Qt WebEngine: a local synthetic chat, no platform network."""
        from PySide6.QtCore import QEventLoop, QTimer, QUrl
        from PySide6.QtWidgets import QApplication
        from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript

        app = QApplication.instance() or QApplication([])
        page = QWebEnginePage()
        page.setVisible(True)
        page.setAudioMuted(True)
        script = QWebEngineScript()
        script.setName("D41-03-test-observer")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
        script.setSourceCode(_BROWSER_OBSERVER)
        page.scripts().insert(script)

        def await_ms(ms):
            loop = QEventLoop()
            QTimer.singleShot(ms, loop.quit)
            loop.exec()

        def wait_reader_ready(label):
            """Allow Qt Chromium's isolated script world and 3s baseline to settle."""
            import json
            last = None
            for _ in range(80):
                replies = []
                page.runJavaScript(
                    "JSON.stringify(window.__iolBrowserChat ? window.__iolBrowserChat.drain() : null)",
                    QWebEngineScript.ScriptWorldId.ApplicationWorld,
                    lambda value: replies.append(value),
                )
                for _ in range(20):
                    if replies:
                        break
                    await_ms(50)
                last = replies[0] if replies else None
                try:
                    data = json.loads(last) if isinstance(last, str) else None
                except ValueError:
                    data = None
                if isinstance(data, dict) and data.get("ready"):
                    return
                await_ms(150)
            self.fail(f"{label} Qt WebEngine observer was not ready: {last!r}")

        loaded = []
        page.loadFinished.connect(lambda ok: loaded.append(bool(ok)))
        page.setHtml(
            '<!doctype html><html><body><div class="chat-line__message">'
            '<span class="chat-author__display-name">Old</span>'
            '<span data-a-target="chat-message-text">history</span></div></body></html>',
            QUrl("https://www.twitch.tv"),
        )
        for _ in range(40):
            if loaded:
                break
            await_ms(250)
        self.assertEqual(loaded, [True], "local Qt WebEngine synthetic page could not load")
        # The initial page and late first-rendered history are baseline only.
        wait_reader_ready("Twitch")
        page.runJavaScript(
            'document.body.insertAdjacentHTML("beforeend", '
            '\'<div class="chat-line__message">'
            '<span class="chat-author__display-name">New</span>'
            '<span data-a-target="chat-message-text">live text</span></div>\');',
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(450)
        received = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat ? window.__iolBrowserChat.drain() : null)",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: received.append(value),
        )
        for _ in range(20):
            if received:
                break
            await_ms(100)
        import json
        result = json.loads(received[0]) if received and isinstance(received[0], str) else None
        self.assertTrue(result and result["ready"])
        self.assertEqual(
            [(e["author"], e["text"]) for e in result["events"]],
            [("New", "live text")],
        )
        # Twitch changes a displayed message into a deletion placeholder.
        # A normal DOM removal, e.g. because of chat virtualization, must
        # never be treated as a moderation event.
        page.runJavaScript(
            'document.querySelectorAll(".chat-line__message")[1]'
            '.querySelector("[data-a-target=chat-message-text]")'
            '.textContent = "<сообщение удалено>";',
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(300)
        deleted = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: deleted.append(value),
        )
        for _ in range(20):
            if deleted:
                break
            await_ms(100)
        event = json.loads(deleted[0])["events"]
        self.assertEqual(event, [{"kind": "delete", "id": "dom-1"}])
        page.runJavaScript(
            'document.querySelectorAll(".chat-line__message")[1].remove();',
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(300)
        unchanged = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: unchanged.append(value),
        )
        for _ in range(20):
            if unchanged:
                break
            await_ms(100)
        self.assertEqual(json.loads(unchanged[0])["events"], [])

        # Real Twitch DOM report (25 Oct 2026): original line is removed,
        # an identical new line appears without any stable data-id, and only
        # later that NEW row becomes a deletion tombstone without a message
        # text region. A normal remount must not create a duplicate.
        page.runJavaScript(
            """document.body.insertAdjacentHTML("beforeend",
               '<div class="chat-line__message">' +
               '<span class="chat-author__display-name">Again</span>' +
               '<span data-a-target="chat-message-text">second message</span></div>');""",
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(400)
        before_remount = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: before_remount.append(value),
        )
        for _ in range(20):
            if before_remount:
                break
            await_ms(100)
        self.assertEqual(
            [(x["kind"], x["id"], x.get("text"))
             for x in json.loads(before_remount[0])["events"]],
            [("message", "dom-2", "second message")],
        )
        page.runJavaScript(
            """(() => {
                const items = document.querySelectorAll('.chat-line__message');
                const row = items[items.length - 1];
                row.replaceWith(row.cloneNode(true));
              })();""",
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(350)
        after_remount = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: after_remount.append(value),
        )
        for _ in range(20):
            if after_remount:
                break
            await_ms(100)
        self.assertEqual(json.loads(after_remount[0])["events"], [],
                         "Ordinary Twitch remount must preserve one message ID")
        page.runJavaScript(
            """(() => {
                const items = document.querySelectorAll('.chat-line__message');
                const row = items[items.length - 1];
                row.innerHTML =
                  '<span class="chat-author__display-name">Again</span>: ' +
                  '<span>&lt;сообщение удалено&gt;</span>';
              })();""",
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(350)
        after_tombstone = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: after_tombstone.append(value),
        )
        for _ in range(20):
            if after_tombstone:
                break
            await_ms(100)
        self.assertEqual(json.loads(after_tombstone[0])["events"],
                         [{"kind": "delete", "id": "dom-2"}])

        # No delete event from a message that merely scrolls/virtualizes out.
        page.runJavaScript(
            """document.body.insertAdjacentHTML("beforeend",
               '<div class="chat-line__message">' +
               '<span class="chat-author__display-name">Safe</span>' +
               '<span data-a-target="chat-message-text">normal text</span></div>');""",
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(300)
        safe = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: safe.append(value),
        )
        for _ in range(20):
            if safe:
                break
            await_ms(100)
        self.assertEqual([x.get("kind") for x in json.loads(safe[0])["events"]], ["message"])
        page.runJavaScript(
            """(() => {
               const rows = document.querySelectorAll('.chat-line__message');
               rows[rows.length - 1].remove();
              })();""",
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(300)
        no_false_delete = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: no_false_delete.append(value),
        )
        for _ in range(20):
            if no_false_delete:
                break
            await_ms(100)
        self.assertEqual(json.loads(no_false_delete[0])["events"], [],
                         "Removal without confirmed moderation must not delete")

        # Two separate childList mutations (remove now, insert later) are
        # permitted by Twitch's asynchronous React reconciliation. The
        # replacement initially has no author element, but the same message.
        page.runJavaScript(
            """document.body.insertAdjacentHTML("beforeend",
               '<div class="chat-line__message">' +
               '<span class="chat-author__display-name">Late</span>' +
               '<span data-a-target="chat-message-text">pending body</span></div>');""",
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(300)
        late_added = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: late_added.append(value),
        )
        for _ in range(20):
            if late_added:
                break
            await_ms(100)
        self.assertEqual(
            [(x["kind"], x["id"]) for x in json.loads(late_added[0])["events"]],
            [("message", "dom-4")],
        )
        # Two acknowledged MainWorld DOM mutations. A Chromium timer can be
        # throttled in a hidden page; never assume a JS setTimeout has fired.
        removed_sync = []
        page.runJavaScript(
            """(() => {
              const nodes = document.querySelectorAll('.chat-line__message');
              nodes[nodes.length - 1].remove();
              return 'removed';
            })();""",
            QWebEngineScript.ScriptWorldId.MainWorld,
            lambda value: removed_sync.append(value),
        )
        for _ in range(20):
            if removed_sync:
                break
            await_ms(100)
        self.assertEqual(removed_sync, ["removed"])
        await_ms(150)
        inserted_sync = []
        page.runJavaScript(
            """(() => {
              document.body.insertAdjacentHTML('beforeend',
                '<div class="chat-line__message">' +
                '<span data-a-target="chat-message-text">pending body</span></div>');
              return 'inserted';
            })();""",
            QWebEngineScript.ScriptWorldId.MainWorld,
            lambda value: inserted_sync.append(value),
        )
        for _ in range(20):
            if inserted_sync:
                break
            await_ms(100)
        self.assertEqual(inserted_sync, ["inserted"])
        await_ms(250)
        hydrated = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: hydrated.append(value),
        )
        for _ in range(20):
            if hydrated:
                break
            await_ms(100)
        self.assertEqual(json.loads(hydrated[0])["events"], [],
                         "Separate remount mutations must not cause duplicate delivery")
        mutation_result = []
        page.runJavaScript(
            """JSON.stringify((function() {
              try {
                const nodes = document.querySelectorAll('.chat-line__message');
                let row = null;
                for (const item of nodes) {
                  const region = item.querySelector('[data-a-target="chat-message-text"]');
                  if (region && region.textContent.trim() === 'pending body') row = item;
                }
                if (!row) return {ok:false,count:nodes.length,note:'target row not found'};
                row.innerHTML = '<span>&lt;сообщение удалено&gt;</span>';
                return {ok:true,count:nodes.length,
                        hasMessageRegion:!!row.querySelector('[data-a-target="chat-message-text"]'),
                        deletedText:row.textContent.trim() === '<сообщение удалено>'};
              } catch (error) {
                return {ok:false,reason:String(error && error.name || 'javascript-error')};
              }
            })())""",
            QWebEngineScript.ScriptWorldId.MainWorld,
            lambda value: mutation_result.append(value),
        )
        for _ in range(30):
            if mutation_result:
                break
            await_ms(100)
        self.assertTrue(
            mutation_result and isinstance(mutation_result[0], str)
            and mutation_result[0] != ""
            and json.loads(mutation_result[0]).get("ok")
            and json.loads(mutation_result[0]).get("deletedText"),
            f"Qt MainWorld tombstone mutation did not execute: {mutation_result!r}",
        )
        await_ms(300)
        late_deleted = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: late_deleted.append(value),
        )
        for _ in range(20):
            if late_deleted:
                break
            await_ms(100)
        diag = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.diagnose())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: diag.append(value),
        )
        for _ in range(20):
            if diag:
                break
            await_ms(100)
        self.assertEqual(
            json.loads(late_deleted[0])["events"],
            [{"kind": "delete", "id": "dom-4"}],
            f"Async Twitch remount diagnostic (structural only): {diag[0] if diag else 'callback missing'}",
        )

        # A literal user-authored string that resembles a tombstone must not
        # be interpreted as moderation when it is an actual message fragment.
        page.runJavaScript(
            """document.body.insertAdjacentHTML("beforeend",
               '<div class="chat-line__message">' +
               '<span class="chat-author__display-name">User</span>' +
               '<span data-a-target="chat-message-text">&lt;сообщение удалено&gt;</span></div>');""",
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(300)
        literal = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: literal.append(value),
        )
        for _ in range(20):
            if literal:
                break
            await_ms(100)
        self.assertEqual(
            [(x["kind"], x.get("text")) for x in json.loads(literal[0])["events"]],
            [("message", "<сообщение удалено>")],
        )

        # A separate page avoids stale ApplicationWorld or pending page
        # callbacks after switching between two unrelated provider origins.
        page.setUrl(QUrl("about:blank"))
        page.deleteLater()
        app.processEvents()
        page = QWebEnginePage()
        page.setVisible(True)
        page.setAudioMuted(True)
        page.scripts().insert(script)
        loaded = []
        page.loadFinished.connect(lambda ok: loaded.append(bool(ok)))
        page.setHtml(
            '<!doctype html><html><body><yt-live-chat-text-message-renderer id="old">'
            '<span id="author-name">Past</span><span id="message">earlier</span>'
            '</yt-live-chat-text-message-renderer></body></html>',
            QUrl("https://www.youtube.com/live_chat?v=AaBbCcDd123"),
        )
        for _ in range(40):
            if loaded:
                break
            await_ms(250)
        self.assertEqual(loaded, [True])
        wait_reader_ready("YouTube")
        page.runJavaScript(
            'document.body.insertAdjacentHTML("beforeend",'
            ' \'<yt-live-chat-text-message-renderer id="yt-new">'
            '<span id="author-name">Viewer</span><span id="message">live</span>'
            '<span id="deleted-state" hidden>Message deleted</span>'
            '</yt-live-chat-text-message-renderer>\');',
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(300)
        added = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: added.append(value),
        )
        for _ in range(20):
            if added:
                break
            await_ms(100)
        self.assertEqual(
            [(event["id"], event["text"]) for event in json.loads(added[0])["events"]],
            [("yt-new", "live")],
        )
        # Real Chrome recording: YouTube creates a normal row containing the
        # *hidden* #deleted-state placeholder; later it can adjust the ID,
        # and only on moderation sets is-deleted on the actual renderer.
        # Initial delivery must precede deletion, even with that placeholder.
        page.runJavaScript(
            'document.getElementById("yt-new").id = "yt-final";',
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(200)
        same = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: same.append(value),
        )
        for _ in range(20):
            if same:
                break
            await_ms(100)
        self.assertEqual(json.loads(same[0])["events"], [],
                         "Stable renderer re-ID is not a new message")

        page.runJavaScript(
            'document.getElementById("yt-final").setAttribute("is-deleted", "");',
            QWebEngineScript.ScriptWorldId.MainWorld,
        )
        await_ms(300)
        removed = []
        page.runJavaScript(
            "JSON.stringify(window.__iolBrowserChat.drain())",
            QWebEngineScript.ScriptWorldId.ApplicationWorld,
            lambda value: removed.append(value),
        )
        for _ in range(20):
            if removed:
                break
            await_ms(100)
        self.assertEqual(json.loads(removed[0])["events"], [{"kind": "delete", "id": "yt-new"}])

        page.setUrl(QUrl("about:blank"))
        page.deleteLater()
        app.processEvents()

    def test_browser_deleted_event_removes_ram_and_obs(self):
        from types import SimpleNamespace
        from streaming_manager.browser_chat import _BrowserChatPage
        from streaming_manager.multichat import ChatMessage

        state = MultichatState(delay=0)
        state.ingest(ChatMessage("youtube", "video", "yt-123", "Viewer", "hello"))
        state.ingest(ChatMessage("twitch", "other", "tw-456", "Other", "keep"))
        dummy = SimpleNamespace(
            source=SimpleNamespace(source_id="video"),
            _generation=5, _busy=True, _last_reply=0,
            platform="youtube", owner=SimpleNamespace(state=state), status="",
        )
        _BrowserChatPage._received(
            dummy,
            {"alive": True, "events": [{"kind": "delete", "id": "yt-123"}]},
            "video", 5,
        )
        for obs in (False, True):
            actual = state.snapshot(for_obs=obs)["messages"]
            self.assertEqual([(m["platform"], m["external_id"]) for m in actual],
                             [("twitch", "tw-456")])

    def test_two_browser_pages_remain_independent_when_one_url_changes(self):
        """Real Qt WebEngine: both sources run concurrently; URL switching is isolated."""
        from unittest.mock import patch
        from PySide6.QtCore import QEventLoop, QTimer, QUrl
        from PySide6.QtWidgets import QApplication
        from PySide6.QtWebEngineCore import QWebEngineScript
        from streaming_manager.browser_chat import _BrowserChatPage
        from streaming_manager.multichat import ChatMessage

        app = QApplication.instance() or QApplication([])

        class MemorySettings:
            def __init__(self):
                self.values = {
                    "multichat_youtube_browser_url":
                        "https://www.youtube.com/live_chat?v=AaBbCcDd123",
                    "multichat_twitch_reader": "browser",
                    "multichat_twitch_browser_url":
                        "https://www.twitch.tv/popout/testuser/chat?popout=",
                }

            def get_setting(self, name, default=""):
                return self.values.get(name, default)

        db = MemorySettings()
        state = MultichatState(limit=100, delay=0)
        runtime = BrowserChatRuntime(db, state)

        def await_ms(ms):
            loop = QEventLoop()
            QTimer.singleShot(ms, loop.quit)
            loop.exec()

        def until(condition, label, rounds=110):
            for _ in range(rounds):
                runtime.wake()
                if condition():
                    return
                await_ms(100)
            self.fail(label)

        def offline_load(reader):
            # Reuse the real per-provider Qt profiles, document scripts, tick,
            # and state. Only the external HTTP navigation is synthetic.
            reader._generation += 1
            reader._busy = False
            if reader.platform == "youtube":
                body = ('<yt-live-chat-text-message-renderer id="old">'
                        '<span id="author-name">History</span><span id="message">past</span>'
                        '</yt-live-chat-text-message-renderer>')
            else:
                body = ('<div class="chat-line__message" data-message-id="old">'
                        '<span class="chat-author__display-name">History</span>'
                        '<span data-a-target="chat-message-text">past</span></div>')
            reader.page.setHtml('<html><body>' + body + '</body></html>',
                                QUrl(reader.source.url))

        def send(reader, msg_id, text):
            if reader.platform == "youtube":
                row = ('<yt-live-chat-text-message-renderer id="' + msg_id + '">'
                       '<span id="author-name">ViewerYT</span><span id="message">'
                       + text + '</span></yt-live-chat-text-message-renderer>')
            else:
                row = ('<div class="chat-line__message" data-message-id="' + msg_id + '">'
                       '<span class="chat-author__display-name">ViewerTW</span>'
                       '<span data-a-target="chat-message-text">' + text + '</span></div>')
            import json
            reader.page.runJavaScript(
                "document.body.insertAdjacentHTML('beforeend', " + json.dumps(row) + ");",
                QWebEngineScript.ScriptWorldId.MainWorld,
            )

        with patch.object(_BrowserChatPage, "_load", offline_load):
            try:
                runtime.start()
                youtube = runtime._readers["youtube"]
                twitch = runtime._readers["twitch"]
                self.assertIsNotNone(youtube)
                self.assertIsNotNone(twitch)
                self.assertIsNot(youtube.profile, twitch.profile)
                self.assertIsNot(youtube.page, twitch.page)

                def ready(reader):
                    replies = []
                    reader.page.runJavaScript(
                        "window.__iolBrowserChat && window.__iolBrowserChat.drain().ready",
                        QWebEngineScript.ScriptWorldId.ApplicationWorld,
                        lambda reply: replies.append(reply),
                    )
                    for _ in range(6):
                        if replies:
                            break
                        await_ms(30)
                    return replies and replies[0] is True

                until(lambda: ready(youtube) and ready(twitch),
                      "Both chat DOM observers must be ready at once", rounds=120)
                send(youtube, "yt-1", "first-yt")
                send(twitch, "tw-1", "first-tw")
                until(lambda: len(state.snapshot()["messages"]) == 2,
                      "Both platforms must deliver new messages together")
                # Embedded diagnostics must not drain the live queue or expose text.
                diagnostics = []
                before_diag = [(m["platform"], m["external_id"])
                               for m in state.snapshot()["messages"]]
                runtime.collect_diagnostics(lambda report: diagnostics.append(report))
                until(lambda: len(diagnostics) == 1,
                      "Embedded Qt diagnostics must complete for both live pages")
                self.assertEqual(set(diagnostics[0]["sources"]), {"youtube", "twitch"})
                self.assertTrue(diagnostics[0]["sources"]["youtube"]["dom"]["observerPresent"])
                self.assertTrue(diagnostics[0]["sources"]["twitch"]["dom"]["observerPresent"])
                self.assertEqual(
                    before_diag,
                    [(m["platform"], m["external_id"])
                     for m in state.snapshot()["messages"]],
                )
                self.assertNotIn("first-yt", str(diagnostics[0]))
                self.assertNotIn("first-tw", str(diagnostics[0]))

                before = {m["platform"] for m in state.snapshot()["messages"]}
                self.assertEqual(before, {"youtube", "twitch"})

                old_yt_page = youtube.page
                old_tw_page = twitch.page
                db.values["multichat_youtube_browser_url"] = (
                    "https://www.youtube.com/live_chat?v=BbCcDdEe456")
                runtime.wake()
                self.assertIs(runtime._readers["youtube"], youtube)
                self.assertIs(runtime._readers["twitch"], twitch)
                self.assertIsNot(youtube.page, old_yt_page)
                self.assertIs(twitch.page, old_tw_page)
                until(lambda: ready(youtube) and ready(twitch),
                      "Replaced YouTube source and unchanged Twitch must both remain alive",
                      rounds=120)
                send(youtube, "yt-2", "second-yt")
                send(twitch, "tw-2", "second-tw")
                until(lambda: any(m["external_id"] == "yt-2" for m in state.snapshot()["messages"])
                      and any(m["external_id"] == "tw-2" for m in state.snapshot()["messages"]),
                      "Both chats must receive new posts after replacing one URL")
                messages = state.snapshot()["messages"]
                self.assertTrue(any(m["external_id"] == "tw-1" for m in messages))
                self.assertFalse(any(m["external_id"] == "yt-1" for m in messages))
                self.assertEqual({m["platform"] for m in messages}, {"youtube", "twitch"})

                # Replacing Twitch must likewise preserve and continue YouTube.
                old_yt_page = youtube.page
                db.values["multichat_twitch_browser_url"] = (
                    "https://www.twitch.tv/popout/another/chat?popout=")
                runtime.wake()
                self.assertIs(youtube.page, old_yt_page)
                until(lambda: ready(youtube) and ready(twitch),
                      "Both observers must survive Twitch source change", rounds=120)
                send(youtube, "yt-3", "third-yt")
                send(twitch, "tw-3", "third-tw")
                until(lambda: any(m["external_id"] == "yt-3" for m in state.snapshot()["messages"])
                      and any(m["external_id"] == "tw-3" for m in state.snapshot()["messages"]),
                      "Both chats must receive after switching Twitch URL")
            finally:
                runtime.stop()
                app.processEvents()

    def test_multiple_copies_dedupe_at_shared_state(self):
        from streaming_manager.multichat import ChatMessage
        state=MultichatState()
        item=ChatMessage('twitch','chan','one','Viewer','text')
        self.assertTrue(state.ingest(item))
        self.assertFalse(state.ingest(item))
        self.assertEqual(len(state.snapshot()['messages']),1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
