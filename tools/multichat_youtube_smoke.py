"""D41-03 isolated YouTube behavior tests. No Google credentials or network."""
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from urllib import parse

from streaming_manager.multichat import ChatMessage, MultichatState
from streaming_manager.youtube import (
    YouTubeAdapter, YouTubeCredential, YouTubeOAuthRequest,
    _GoogleLoopback, YOUTUBE_SCOPE, YouTubeApi,
)
from streaming_manager.youtube_chat import (
    YouTubeChatRuntime, _broadcast_choices, _consume_message,
)


def broadcast(identifier: str, channel="channel1", chat=None, title=None):
    return {
        "id": identifier,
        "snippet": {"channelId": channel, "title": title or identifier,
                    "liveChatId": chat if chat is not None else "chat-" + identifier},
    }


def event(identifier, content, kind="textMessageEvent", author="author1"):
    return {
        "id": identifier,
        "snippet": {"type": kind, "displayMessage": content,
                    "publishedAt": "2026-10-25T05:30:00Z"},
        "authorDetails": {"displayName": "Tester", "channelId": author},
    }


class Db:
    def __init__(self):
        self.row = {"enabled": True, "status": "connected",
                    "provider_config": {"youtube_channel_id": "channel1",
                                        "youtube_channel_name": "My channel"}}

    def get_integration_connection(self, key):
        assert key == "youtube"
        return self.row


class Manager:
    def call_adapter(self, service, operation):
        assert (service, operation) == ("youtube", "account_access")
        return "mock-access"


class Api:
    def __init__(self, active=None, pages=None):
        self.active = active if active is not None else [broadcast("stream1")]
        self.pages = iter(pages or [])
        self.calls = []

    def broadcasts(self, access):
        assert access == "mock-access"
        return self.active

    def chat_page(self, access, chat_id, token=""):
        self.calls.append((chat_id, token))
        return next(self.pages)


class YouTubeChatSmoke(unittest.TestCase):
    def runtime(self, api=None, callback=None):
        s = MultichatState()
        return YouTubeChatRuntime(Db(), Manager(), s, api=api or Api(),
                                  selection_required=callback), s

    def test_official_broadcast_filter_must_prove_channel(self):
        rows = [broadcast("mine"), broadcast("other", "someone-else"),
                {"id": "unknown", "snippet": {"title": "no channel"}},
                broadcast("mine")]
        self.assertEqual([x["id"] for x in _broadcast_choices(rows, "channel1")], ["mine"])

    def test_first_page_skips_history_followup_delivers_new(self):
        a = Api(pages=[
            {"items": [event("old", "old")], "nextPageToken": "token1", "pollingIntervalMillis": 1000},
            {"items": [event("new", "<b>hello</b>")], "nextPageToken": "token2", "pollingIntervalMillis": 1000},
        ])
        r, s = self.runtime(a)
        r._cycle()
        self.assertEqual(s.snapshot()["messages"], [])
        r._next_message_poll = 0
        r._cycle()
        self.assertEqual([x["external_id"] for x in s.snapshot()["messages"]], ["new"])
        self.assertEqual(s.snapshot(for_obs=True)["messages"][0]["text"], "<b>hello</b>")
        self.assertEqual(a.calls, [("chat-stream1", ""), ("chat-stream1", "token1")])

    def test_missing_next_token_never_accepts_initial_history(self):
        a = Api(pages=[
            {"items": [event("old1", "old")], "pollingIntervalMillis": 1000},
            {"items": [event("old2", "old")], "nextPageToken": "next", "pollingIntervalMillis": 1000},
        ])
        r, s = self.runtime(a)
        r._cycle()
        r._next_message_poll = 0
        r._cycle()
        self.assertEqual(s.snapshot()["messages"], [])
        self.assertEqual(a.calls, [("chat-stream1", ""), ("chat-stream1", "")])

    def test_delete_and_ban_within_selected_chat_only(self):
        s = MultichatState()
        s.ingest(ChatMessage("youtube", "chat-stream1", "first", "Tester", "one", author_id="u1"))
        s.ingest(ChatMessage("youtube", "chat-stream1", "second", "Tester", "two", author_id="u2"))
        s.ingest(ChatMessage("youtube", "another", "other", "Tester", "three", author_id="u1"))
        s.ingest(ChatMessage("twitch", "twitch1", "twitch", "Tester", "four", author_id="u1"))
        _consume_message(s, "chat-stream1", {
            "snippet": {"type": "messageDeletedEvent",
                        "messageDeletedDetails": {"deletedMessageId": "first"}}
        })
        self.assertEqual(len(s.snapshot()["messages"]), 3)
        _consume_message(s, "chat-stream1", {
            "snippet": {"type": "userBannedEvent",
                        "userBannedDetails": {"banType": "permanent",
                                              "bannedUserDetails": {"channelId": "u2"}}}
        })
        self.assertEqual({m["external_id"] for m in s.snapshot()["messages"]}, {"other", "twitch"})
        self.assertEqual(len(s.snapshot(for_obs=True)["messages"]), 2)

    def test_multiple_requires_selection_and_cancel_persists(self):
        shown = []
        r, state = self.runtime(callback=lambda x: shown.append(x))
        r._update_broadcasts([broadcast("a"), broadcast("b")])
        self.assertTrue(r.choice_required())
        self.assertEqual(len(shown), 1)
        r.choose_broadcast(None)
        r._update_broadcasts([broadcast("a")])
        self.assertEqual(r._selected, "")
        r.request_selection()
        r._update_broadcasts([broadcast("a")])
        self.assertEqual(len(shown), 2)
        r.choose_broadcast("a")
        self.assertEqual(r._selected, "a")

    def test_second_simultaneous_stream_does_not_switch(self):
        r, s = self.runtime()
        r._update_broadcasts([broadcast("a")])
        self.assertEqual(r._selected, "a")
        r._update_broadcasts([broadcast("a"), broadcast("b")])
        self.assertEqual(r._selected, "a")
        self.assertFalse(r.choice_required())

    def test_new_stream_after_gap_autoselect_and_clear_youtube_only(self):
        r, s = self.runtime()
        r._update_broadcasts([broadcast("a")])
        s.ingest(ChatMessage("youtube", "chat-a", "old", "User", "old"))
        s.ingest(ChatMessage("twitch", "chan", "keep", "User", "keep"))
        r._update_broadcasts([])
        self.assertEqual(len(s.snapshot()["messages"]), 2)
        r._update_broadcasts([broadcast("b")])
        self.assertEqual(r._selected, "b")
        self.assertEqual([m["platform"] for m in s.snapshot()["messages"]], ["twitch"])

    def test_other_already_live_when_selected_ends_requires_confirmation(self):
        r, _ = self.runtime()
        r._update_broadcasts([broadcast("a")])
        r._update_broadcasts([broadcast("b")])
        self.assertEqual(r._selected, "a")
        self.assertTrue(r.choice_required())
        r.choose_broadcast("b")
        self.assertEqual(r._selected, "b")

    def test_chat_becomes_available_without_switch(self):
        r, _ = self.runtime()
        r._update_broadcasts([broadcast("a", chat="")])
        self.assertEqual(r._live_chat_id, "")
        r._update_broadcasts([broadcast("a", chat="good-chat")])
        self.assertEqual(r._live_chat_id, "good-chat")

    def test_confirmed_change_of_authorized_channel_preserves_twitch(self):
        r, s = self.runtime()
        r._update_broadcasts([broadcast("a")])
        s.ingest(ChatMessage("youtube", "chat-a", "old", "User", "old"))
        s.ingest(ChatMessage("twitch", "chan", "keep", "User", "keep"))
        r.db.row["provider_config"]["youtube_channel_id"] = "channel2"
        r.db.row["provider_config"]["youtube_channel_name"] = "Second"
        r.api.active = []
        r._next_discovery = 0
        r._cycle()
        self.assertEqual([m["platform"] for m in s.snapshot()["messages"]], ["twitch"])

    def test_disconnect_preserves_shown_messages(self):
        r, s = self.runtime()
        s.ingest(ChatMessage("youtube", "chat-a", "shown", "User", "hello"))
        r.db.row["enabled"] = False
        r._cycle()
        self.assertEqual(len(s.snapshot()["messages"]), 1)

    def test_google_oauth_pkce_loopback_state(self):
        import urllib.request
        import urllib.error
        with _GoogleLoopback() as callback:
            self.assertTrue(callback.redirect_uri.startswith("http://127.0.0.1:"))
            wrong = callback.redirect_uri + "?state=wrong&code=evil"
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(wrong, timeout=3)
            correct = callback.redirect_uri + "?" + parse.urlencode({
                "state": callback.state, "code": "test-code",
            })
            urllib.request.urlopen(correct, timeout=3).close()
            self.assertEqual(callback.await_code(__import__("threading").Event(), timeout=2), "test-code")

    def test_credential_redacts_and_validates(self):
        raw = YouTubeCredential("secret-access", "secret-refresh",
                                "public.apps.googleusercontent.com", time.time()+3600).serialize()
        self.assertEqual(YouTubeCredential.parse(raw).refresh, "secret-refresh")
        self.assertNotIn("secret", repr(YouTubeAdapter().view_details({})))
        with self.assertRaises(ValueError):
            YouTubeAdapter.normalize_client_id("madeup-id")

    def test_provider_http_query_official_routes(self):
        api = YouTubeApi()
        def spy(url, *, params, access):
            self.assertTrue(url.endswith("/liveBroadcasts"))
            self.assertEqual(params["broadcastStatus"], "active")
            self.assertEqual(params["mine"], "true")
            self.assertEqual(params["broadcastType"], "all")
            return {"items": [broadcast("mine")]}
        api._json = spy
        self.assertEqual(len(api.broadcasts("token")), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
