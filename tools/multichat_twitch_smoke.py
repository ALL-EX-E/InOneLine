"""D41-02 isolated Twitch EventSub/chat regression; no real Twitch credentials."""
from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from streaming_manager.multichat import ChatMessage, MultichatState
from streaming_manager.twitch import (
    TWITCH_CHAT_EVENT_TYPES, TWITCH_CHAT_READ_SCOPE, TWITCH_MANAGE_SCOPE,
    TWITCH_REQUIRED_SCOPE, TwitchAdapter, TwitchApiClient, TwitchCredential,
)
from streaming_manager.twitch_b4 import TwitchEventSubRuntime


class FakeSocket:
    def __init__(self, events):
        self.events = iter(events)
        self.closed = False

    def recv(self):
        return json.dumps(next(self.events))

    def close(self):
        self.closed = True


class FakeService:
    def __init__(self, *, scopes=(TWITCH_CHAT_READ_SCOPE,), rewards=()):
        self.db = SimpleNamespace(get_integration_connection=lambda service: {
            "enabled": True, "status": "connected",
            "provider_config": {"twitch_user_id": "channel1", "granted_scopes": list(scopes)},
        })
        self.calls = []
        self.rewards = tuple(rewards)
        self.redemptions = []
        self.integration_manager = SimpleNamespace(call_adapter=self.call)

    def call(self, service, method, *args):
        self.calls.append((service, method, *args))
        return {}

    def connection_ready(self):
        return True

    def managed_reward_ids(self):
        return self.rewards

    def desired_rewards_enabled(self):
        return False

    def sync_reward_enabled_state(self, *args):
        return True

    def catch_up_unfulfilled(self):
        return 0

    def process_redemption(self, event):
        self.redemptions.append(event)


def welcome():
    return {"metadata": {"message_type": "session_welcome"},
            "payload": {"session": {"id": "session1"}}}


def notification(kind, event):
    return {
        "metadata": {"message_type": "notification",
                     "message_timestamp": "2026-10-24T16:40:00Z",
                     "message_id": "evt-id"},
        "payload": {"subscription": {"type": kind}, "event": event},
    }


def reconnect():
    return {"metadata": {"message_type": "session_reconnect"},
            "payload": {"session": {"reconnect_url": "wss://eventsub.wss.twitch.tv/ws?reconnect=1"}}}


def message(mid, author="u1", source="channel1"):
    return {"broadcaster_user_id": source, "message_id": mid,
            "chatter_user_id": author, "chatter_user_name": author,
            "message": {"text": "Hello <b>chat</b>"}}


class TwitchChatSmoke(unittest.TestCase):
    def test_chat_subscriptions_without_rewards(self):
        service = FakeService(rewards=())
        state = MultichatState()
        events = [welcome(), notification("channel.chat.message", message("m1")),
                  notification("channel.chat.message", message("m1")),
                  notification("channel.chat.message", message("foreign", source="elsewhere")),
                  reconnect()]
        sock = FakeSocket(events)
        runtime = TwitchEventSubRuntime(service, chat_state=state, socket_factory=lambda _: sock)
        runtime._chat_source_id = "channel1"
        self.assertIn("reconnect=1", runtime._run_connection("wss://example/ws", subscriptions_required=True))
        self.assertTrue(sock.closed)
        self.assertEqual([m["external_id"] for m in state.snapshot()["messages"]], ["m1"])
        self.assertEqual(state.snapshot()["messages"][0]["author_id"], "u1")
        self.assertEqual(len(service.calls), len(TWITCH_CHAT_EVENT_TYPES))
        self.assertEqual({x[3] for x in service.calls}, set(TWITCH_CHAT_EVENT_TYPES))
        self.assertEqual(service.redemptions, [])

    def test_silent_socket_expires_after_provider_keepalive_window(self):
        now = [100.0]
        provider_welcome = welcome()
        provider_welcome["payload"]["session"]["keepalive_timeout_seconds"] = 10

        class SilentSocket(FakeSocket):
            def recv(self):
                value = next(self.events)
                if value == "timeout":
                    now[0] += 5.1
                    raise TimeoutError("No WebSocket data")
                return json.dumps(value)

        service = FakeService(rewards=("reward1",))
        socket = SilentSocket([provider_welcome, "timeout", "timeout", reconnect()])
        runtime = TwitchEventSubRuntime(
            service, chat_state=MultichatState(), socket_factory=lambda _: socket,
        )
        runtime._chat_source_id = "channel1"
        with (
            patch("streaming_manager.twitch_b4.monotonic", side_effect=lambda: now[0]),
            patch.object(runtime, "_schedule_media_warmup"),
            patch.object(runtime, "_schedule_third_party_catalog"),
        ):
            with self.assertRaisesRegex(RuntimeError, "keepalive"):
                runtime._run_connection("wss://example/ws", subscriptions_required=True)
        self.assertTrue(socket.closed)
        self.assertFalse(runtime.connected)
        self.assertFalse(runtime.chat_connected)

    def test_notifications_and_keepalive_extend_socket_deadline(self):
        now = [100.0]
        provider_welcome = welcome()
        provider_welcome["payload"]["session"]["keepalive_timeout_seconds"] = 10

        class TimedSocket(FakeSocket):
            def recv(self):
                elapsed, value = next(self.events)
                now[0] += elapsed
                if value == "timeout":
                    raise TimeoutError("No WebSocket data")
                return json.dumps(value)

        service = FakeService(rewards=("reward1",))
        state = MultichatState()
        socket = TimedSocket([
            (0, provider_welcome),
            (8, {"metadata": {"message_type": "session_keepalive"}, "payload": {}}),
            (8, notification("channel.chat.message", message("after-keepalive"))),
            (8, "timeout"),
            (1, reconnect()),
        ])
        runtime = TwitchEventSubRuntime(service, chat_state=state, socket_factory=lambda _: socket)
        runtime._chat_source_id = "channel1"
        with (
            patch("streaming_manager.twitch_b4.monotonic", side_effect=lambda: now[0]),
            patch.object(runtime, "_schedule_media_warmup"),
            patch.object(runtime, "_schedule_third_party_catalog"),
        ):
            result = runtime._run_connection("wss://example/ws", subscriptions_required=True)
        self.assertIn("reconnect=1", result)
        self.assertEqual([m["external_id"] for m in state.snapshot()["messages"]], ["after-keepalive"])
        self.assertTrue(socket.closed)

    def test_silent_connection_is_replaced_and_subscriptions_are_recreated(self):
        now = [100.0]
        provider_welcome = welcome()
        provider_welcome["payload"]["session"]["keepalive_timeout_seconds"] = 10

        class SilentSocket(FakeSocket):
            def recv(self):
                value = next(self.events)
                if value == "timeout":
                    now[0] += 11
                    raise TimeoutError("No WebSocket data")
                return json.dumps(value)

        class RecoveredSocket(FakeSocket):
            def recv(self):
                value = next(self.events)
                if value["metadata"]["message_type"] == "session_keepalive":
                    runtime._stop.set()
                return json.dumps(value)

        service = FakeService(rewards=("reward1",))
        old = SilentSocket([provider_welcome, "timeout", reconnect()])
        new = RecoveredSocket([
            provider_welcome,
            {"metadata": {"message_type": "session_keepalive"}, "payload": {}},
        ])
        sockets = Mock(side_effect=[old, new])
        runtime = TwitchEventSubRuntime(service, chat_state=MultichatState(), socket_factory=sockets)
        with (
            patch("streaming_manager.twitch_b4.monotonic", side_effect=lambda: now[0]),
            patch.object(runtime, "_wait"),
            patch.object(runtime, "_schedule_media_warmup"),
            patch.object(runtime, "_schedule_third_party_catalog"),
        ):
            runtime._run()
        self.assertEqual(sockets.call_count, 2)
        self.assertEqual(sockets.call_args_list[0], sockets.call_args_list[1])
        expected_subscriptions = 1 + len(TWITCH_CHAT_EVENT_TYPES)
        self.assertEqual(len(service.calls), expected_subscriptions * 2)
        self.assertTrue(old.closed and new.closed)

    def test_channel_point_event_stays_on_original_service(self):
        service = FakeService(scopes=(TWITCH_CHAT_READ_SCOPE, TWITCH_MANAGE_SCOPE), rewards=("reward1",))
        state = MultichatState()
        sock = FakeSocket([welcome(), notification(
            "channel.channel_points_custom_reward_redemption.add",
            {"id": "redemption-1", "reward": {"id": "reward1"}},
        ), reconnect()])
        runtime = TwitchEventSubRuntime(service, chat_state=state, socket_factory=lambda _: sock)
        runtime._chat_source_id = "channel1"
        runtime._run_connection("wss://example/ws", subscriptions_required=True)
        self.assertEqual(len(service.redemptions), 1)
        self.assertEqual(service.redemptions[0]["_eventsub_metadata"]["message_id"], "evt-id")
        self.assertEqual(len(service.calls), 1 + len(TWITCH_CHAT_EVENT_TYPES))
        self.assertEqual(state.snapshot()["messages"], [])

    def test_failed_chat_subscription_does_not_stop_rewards(self):
        service = FakeService(scopes=(TWITCH_MANAGE_SCOPE, TWITCH_CHAT_READ_SCOPE),
                              rewards=("reward1",))
        original_call = service.call
        def fail_chat(*args):
            if args[1] == "create_chat_eventsub_subscription":
                raise RuntimeError("Provider denied chat")
            return original_call(*args)
        service.integration_manager.call_adapter = fail_chat
        state = MultichatState()
        sock = FakeSocket([welcome(), notification(
            "channel.channel_points_custom_reward_redemption.add",
            {"id": "redemption-2", "reward": {"id": "reward1"}},
        ), reconnect()])
        runtime = TwitchEventSubRuntime(service, chat_state=state, socket_factory=lambda _: sock)
        runtime._chat_source_id = "channel1"
        runtime._run_connection("wss://example/ws", subscriptions_required=True)
        self.assertEqual(len(service.redemptions), 1)
        self.assertFalse(runtime.chat_connected)
        self.assertTrue(runtime.chat_error)
        self.assertEqual(state.snapshot()["messages"], [])

    def test_deletions_and_clear_user_affect_both_feeds(self):
        service = FakeService()
        state = MultichatState()
        sock = FakeSocket([
            welcome(),
            notification("channel.chat.message", message("a", "u1")),
            notification("channel.chat.message", message("b", "u2")),
            notification("channel.chat.message_delete", {"broadcaster_user_id": "channel1", "message_id": "a"}),
            notification("channel.chat.message", message("c", "u2")),
            notification("channel.chat.clear_user_messages", {"broadcaster_user_id": "channel1", "target_user_id": "u2"}),
            notification("channel.chat.message", message("d", "u3")),
            reconnect(),
        ])
        runtime = TwitchEventSubRuntime(service, chat_state=state, socket_factory=lambda _: sock)
        runtime._chat_source_id = "channel1"
        runtime._run_connection("wss://example/ws", subscriptions_required=True)
        self.assertEqual([x["external_id"] for x in state.snapshot()["messages"]], ["d"])
        self.assertEqual([x["external_id"] for x in state.snapshot(for_obs=True)["messages"]], ["d"])
        state.clear_chat("twitch", "channel1")
        self.assertEqual(state.snapshot()["messages"], [])

    def test_offline_pending_is_discarded_without_clearing_old_messages(self):
        state = MultichatState(delay=20)
        state.ingest(ChatMessage("twitch", "channel1", "m1", "u", "hello"))
        state.disconnect("twitch")
        state.configure(delay=0)
        self.assertEqual(state.snapshot()["messages"], [])
        state.ingest(ChatMessage("youtube", "youtube1", "y1", "y", "test"))
        state.ingest(ChatMessage("twitch", "channel1", "m2", "t", "test"))
        state.change_source("twitch")
        self.assertEqual([x["platform"] for x in state.snapshot()["messages"]], ["youtube"])

    def test_reconnect_scopes_preserve_rewards(self):
        adapter = TwitchAdapter()
        context = SimpleNamespace(provider_config={
            "granted_scopes": [TWITCH_MANAGE_SCOPE, TWITCH_REQUIRED_SCOPE],
        })
        scopes = adapter._desired_scopes(context)
        self.assertEqual(set(scopes), {TWITCH_MANAGE_SCOPE, TWITCH_REQUIRED_SCOPE, TWITCH_CHAT_READ_SCOPE})
        self.assertEqual(set(adapter._desired_scopes(SimpleNamespace(provider_config={}), manage=True)),
                         {TWITCH_MANAGE_SCOPE, TWITCH_REQUIRED_SCOPE, TWITCH_CHAT_READ_SCOPE})

    def test_eventsub_request_uses_verified_channel_and_user(self):
        client = TwitchApiClient()
        with patch.object(client, "_request_json", return_value={}) as request:
            client.create_chat_subscription("client", "access", session_id="s1",
                                            broadcaster_id="b1", chatter_id="u1",
                                            event_type="channel.chat.message")
        body = request.call_args.kwargs["json_body"]
        self.assertEqual(body["condition"], {"broadcaster_user_id": "b1", "user_id": "u1"})
        self.assertEqual(body["transport"], {"method": "websocket", "session_id": "s1"})
        with self.assertRaises(ValueError):
            client.create_chat_subscription("c", "a", session_id="s", broadcaster_id="b",
                                            chatter_id="u", event_type="not_chat")

    def test_old_reward_only_token_requires_reauthorization_for_chat(self):
        service = FakeService(scopes=(TWITCH_MANAGE_SCOPE,), rewards=("reward1",))
        state = MultichatState()
        runtime = TwitchEventSubRuntime(service, chat_state=state)
        self.assertIn("повторная авторизация", runtime.chat_status())
        self.assertEqual(runtime._chat_profile(), ("channel1", False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
