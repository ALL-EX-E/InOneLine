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
        page.runJavaScript(
            'document.getElementById("yt-new").setAttribute("is-deleted", "");',
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
