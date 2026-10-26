"""D41-04 offline verification of native Twitch graphics and global icon flag."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from streaming_manager.chat_graphics import (
    parse_twitch_badges, parse_twitch_fragments, safe_image_url, twitch_name_color,
)
from streaming_manager.multichat import ChatMessage, MultichatState
from streaming_manager.twitch_b4 import TwitchEventSubRuntime


class GraphicsSmoke(unittest.TestCase):
    def test_eventsub_fragment_order_and_url_protection(self):
        parts = parse_twitch_fragments({"fragments": [
            {"type": "text", "text": "<script>hello</script> "},
            {"type": "emote", "text": "Kappa",
             "emote": {"id": "25", "format": ["static","animated"]}},
            {"type": "gif", "text": "[GIF]",
             "gif": {"url": "https://media.tenor.com/example.gif"}},
            {"type": "gif", "text": "blocked",
             "gif": {"url": "http://127.0.0.1/admin"}},
            {"type": "mention", "text": "@friend"},
        ]})
        self.assertEqual([p["kind"] for p in parts],
                         ["text","image","image","text","text"])
        self.assertEqual(parts[0]["text"], "<script>hello</script> ")
        self.assertIn("/animated/dark/2.0", parts[1]["url"])
        self.assertEqual(parts[2]["url"], "https://media.tenor.com/example.gif")
        self.assertEqual(parts[3]["text"], "blocked")
        self.assertEqual(parts[4]["text"], "@friend")
        for bad in ["file:///etc/passwd", "https://127.0.0.1/test.gif",
                    "https://static-cdn.jtvnw.net.evil.com/foo",
                    "https://user:password@media.tenor.com/x",
                    "javascript:alert(1)"]:
            self.assertEqual(safe_image_url(bad), "")
        self.assertEqual(twitch_name_color("#6b38fd"), "#6b38fd")
        self.assertEqual(twitch_name_color("red;display:none"), "")

    def test_badge_order_and_global_icon_persistence(self):
        badges = parse_twitch_badges({"badges": [
            {"set_id": "moderator", "id": "1"},
            {"set_id": "subscriber", "id": "6"},
        ]})
        self.assertEqual([(b["set_id"],b["id"]) for b in badges],
                         [("moderator","1"),("subscriber","6")])
        state = MultichatState(delay=10.0)
        state.configure(show_platform_icons=False)
        sample = ChatMessage("twitch","channel","msg1","Streamer","Hello",author_id="7",
                             badges=badges, color="#123456",
                             fragments=({"kind":"text","text":"Hello"},))
        state.ingest(sample)
        state.enrich_twitch_media("channel",avatar_by_user={"7":"https://static-cdn.jtvnw.net/a.png"},
                                  badge_urls={("moderator","1"):"https://static-cdn.jtvnw.net/m.png"})
        state.configure(delay=0.0)
        for for_obs in [False,True]:
            snap = state.snapshot(for_obs=for_obs)
            self.assertFalse(snap["show_platform_icons"])
            msg = snap["messages"][0]
            self.assertEqual(msg["fragments"][0]["text"],"Hello")
            self.assertEqual(msg["badges"][0]["url"],"https://static-cdn.jtvnw.net/m.png")
            self.assertEqual(msg["badges"][1]["url"],"")
            self.assertEqual(msg["avatar_url"],"https://static-cdn.jtvnw.net/a.png")
        state.delete_message("twitch","channel","msg1")
        state.enrich_twitch_media("channel",avatar_by_user={"7":"https://static-cdn.jtvnw.net/b.png"})
        self.assertEqual(state.snapshot()["messages"],[])
        self.assertEqual(state.snapshot(for_obs=True)["messages"],[])
        state.configure(show_platform_icons=True)
        self.assertTrue(state.snapshot()["show_platform_icons"])

    def test_runtime_preserves_graphics_without_network_or_rewards_change(self):
        state = MultichatState()
        service = SimpleNamespace(connection_ready=lambda:True,
                                  db=SimpleNamespace(get_integration_connection=lambda _:{}))
        runtime = TwitchEventSubRuntime(service,chat_state=state)
        runtime._chat_source_id="12345"
        event={"broadcaster_user_id":"12345","message_id":"m1",
               "chatter_user_name":"Streamer","chatter_user_id":"7",
               "color":"#99CC00","badges":[{"set_id":"moderator","id":"1"}],
               "message":{"text":"Hi Kappa","fragments":[
                   {"type":"text","text":"Hi "},
                   {"type":"emote","text":"Kappa","emote":{"id":"25","format":["static"]}}
               ]}}
        runtime._process_chat_notification("channel.chat.message",event,{})
        msg=state.snapshot()["messages"][0]
        self.assertEqual(msg["color"], "#99CC00")
        self.assertEqual(len(msg["fragments"]),2)
        self.assertEqual(msg["badges"][0]["set_id"],"moderator")
        runtime._process_chat_notification("channel.chat.message_delete",
                                           {"broadcaster_user_id":"12345","message_id":"m1"}, {})
        self.assertEqual(state.snapshot()["messages"],[])

    def test_qt_animated_emote_uses_movie_not_one_static_frame(self):
        import base64
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QMovie
        from streaming_manager.views.chat_rich_feed import ChatRichFeed
        app = QApplication.instance() or QApplication([])
        feed = ChatRichFeed()
        source = "https://static-cdn.jtvnw.net/emoticons/v2/25/animated/dark/2.0"
        gif_bytes = base64.b64decode(
            "R0lGODlhBAAEAIEAAP8AAAAAAAAAAAAAACH/C05FVFNDQVBFMi4wAwEAAAAh"
            "+QQACgAAACwAAAAABAAEAAAICQABCBxIsCCAgAAh+QQBCgABACwAAAAABAAE"
            "AIEAAP8AAAAAAAAAAAAICQABCBxIsCCAgAA7"
        )
        try:
            feed._cache[source] = (gif_bytes, None, None, None, True)
            feed._cache_bytes += len(gif_bytes)
            feed.display([{
                "author":"Viewer","text":"Kappa","avatar_url":"","badges":[],
                "platform":"twitch","fragments":[
                    {"kind":"image","text":"Kappa","url":source},
                ],
            }],show_time=False,show_icons=False)
            movie = feed._cache[source][2]
            self.assertIsNotNone(movie)
            self.assertEqual(movie.state(), QMovie.Running)
            self.assertGreaterEqual(movie.frameCount(), 2)
        finally:
            feed.close()
            app.processEvents()

    def test_qt_native_renderer_does_not_parse_untrusted_html(self):
        from PySide6.QtWidgets import QApplication
        from streaming_manager.views.chat_rich_feed import ChatRichFeed
        app = QApplication.instance() or QApplication([])
        feed = ChatRichFeed()
        try:
            feed.display([{"author":"<b>Bob</b>","text":"<script>wrong</script>",
                           "fragments":[],"badges":[],"avatar_url":"",
                           "platform":"twitch","sent_at":None,"received_at":0}],
                         show_time=False,show_icons=False)
            self.assertIn("<b>Bob</b>",feed.toPlainText())
            self.assertIn("<script>wrong</script>",feed.toPlainText())
            self.assertNotIn("<script>wrong</script>",feed.document().toHtml())
            self.assertNotIn("iol-chat-twitch-logo",feed.document().toHtml())
            feed.display([{"author":"Bob","text":"hi","platform":"twitch",
                           "badges":[],"avatar_url":"","fragments":[]}],
                         show_time=False,show_icons=True)
            self.assertIn("iol-chat-twitch-logo",feed.document().toHtml())
        finally:
            feed.close()
            app.processEvents()


if __name__=="__main__":
    unittest.main(verbosity=2)
