"""D41-01 isolated tests; no Twitch/YouTube credentials, Qt or OBS needed."""
import unittest
from streaming_manager.multichat import ChatMessage, MultichatState


class FakeTime:
    def __init__(self):
        self.now = 100.0
    def __call__(self):
        return self.now
    def advance(self, seconds):
        self.now += seconds


def msg(platform="twitch", identifier="1", sent=100.0, source="channel"):
    return ChatMessage(platform, source, identifier, "Test", "hello", sent)


class MultichatCoreTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeTime()
        self.state = MultichatState(clock=self.clock, wall_clock=self.clock)

    def ids(self, obs=False):
        return [m["external_id"] for m in self.state.snapshot(for_obs=obs)["messages"]]

    def test_zero_delay_follows_receipt_order(self):
        self.state.ingest(msg(identifier="later", sent=200))
        self.state.ingest(msg(identifier="earlier", sent=100))
        self.assertEqual(self.ids(), ["later", "earlier"])

    def test_delayed_window_sorts_by_source_time(self):
        self.state.configure(delay=2.0)
        self.state.ingest(msg(identifier="later", sent=110))
        self.state.ingest(msg(identifier="earlier", sent=100))
        self.assertEqual(self.ids(), [])
        self.clock.advance(2)
        self.assertEqual(self.ids(), ["earlier", "later"])

    def test_delay_change_recalculates_pending(self):
        self.state.configure(delay=10.0)
        self.state.ingest(msg())
        self.clock.advance(3)
        self.state.configure(delay=2.0)
        self.assertEqual(self.ids(), ["1"])

    def test_no_backdating_after_published(self):
        self.state.ingest(msg(identifier="published", sent=999))
        self.state.configure(delay=3)
        self.state.ingest(msg(identifier="pending", sent=1))
        self.clock.advance(3)
        self.assertEqual(self.ids(), ["published", "pending"])

    def test_duplicate_ignored(self):
        self.assertTrue(self.state.ingest(msg()))
        self.assertFalse(self.state.ingest(msg()))
        self.assertEqual(self.ids(), ["1"])

    def test_dedupe_scoped_to_platform_and_source(self):
        self.state.ingest(msg())
        self.state.ingest(msg(platform="youtube"))
        self.state.ingest(msg(source="another"))
        self.assertEqual(len(self.ids()), 3)

    def test_obs_filters_at_delivery_not_receipt(self):
        self.state.configure(delay=1)
        self.state.ingest(msg())
        self.state.set_obs_enabled("twitch", False)
        self.clock.advance(1)
        self.assertEqual(self.ids(), ["1"])
        self.assertEqual(self.ids(obs=True), [])
        self.state.set_obs_enabled("twitch", True)
        self.assertEqual(self.ids(obs=True), [])
        self.state.ingest(msg(identifier="2"))
        self.clock.advance(1)
        self.assertEqual(self.ids(obs=True), ["2"])

    def test_operator_feed_serializes_only_changes_after_delayed_delivery(self):
        from unittest.mock import patch

        self.state.configure(delay=2)
        initial = self.state.operator_feed_snapshot()
        self.state.ingest(msg(identifier="local"))
        self.state.ingest(msg(platform="youtube", identifier="other"))
        self.assertIsNone(self.state.operator_feed_snapshot(initial["key"]))

        self.clock.advance(2)
        ready = self.state.operator_feed_snapshot(initial["key"])
        self.assertEqual([m["external_id"] for m in ready["messages"]], ["local", "other"])
        self.assertEqual(self.ids(obs=True), ["local", "other"])
        with patch("streaming_manager.multichat.asdict", side_effect=AssertionError("idle copy")):
            self.assertIsNone(self.state.operator_feed_snapshot(ready["key"]))

    def test_operator_feed_detects_media_and_visibility_changes(self):
        self.state.ingest(msg(identifier="1"))
        before = self.state.operator_feed_snapshot()
        self.state.set_obs_enabled("twitch", False)
        self.assertIsNone(self.state.operator_feed_snapshot(before["key"]))
        self.state.configure(show_time=False, show_platform_icons=False)
        url = "https://static-cdn.jtvnw.net/avatar.png"
        self.state.set_media_preload("twitch", (url,))
        changed = self.state.operator_feed_snapshot(before["key"])
        self.assertFalse(changed["show_time"])
        self.assertFalse(changed["show_platform_icons"])
        self.assertEqual(changed["media_preload"], (url,))
        self.state.delete_message("twitch", "channel", "1")
        after = self.state.operator_feed_snapshot(changed["key"])
        self.assertEqual(after["messages"], [])

    def test_obs_overlay_summary_preserves_chat_delay_and_list_hold(self):
        self.state.configure(delay=3)
        self.state.configure_list_show("slide", "hello", 0)
        self.state.ingest(msg(platform="youtube", identifier="youtube"))
        self.state.ingest(msg(identifier="twitch"))
        initial = self.state.obs_overlay_summary()
        self.assertFalse(initial["twitch_has_messages"])
        self.assertEqual(initial["list_show"], {"remaining_ms": 0, "sequence": 1, "held": True})
        self.clock.advance(3)
        ready = self.state.obs_overlay_summary()
        self.assertTrue(ready["twitch_has_messages"])
        self.assertEqual(self.state.snapshot(for_obs=True)["list_show"], ready["list_show"])
        self.state.set_obs_enabled("twitch", False)
        hidden = self.state.obs_overlay_summary()
        self.assertTrue(hidden["twitch_has_messages"])
        self.assertFalse(hidden["obs_enabled"]["twitch"])
        self.assertTrue(hidden["list_show"]["held"])

    def test_list_command_exact_match_shared_timer_and_repeats(self):
        self.state.configure_list_show("slide", "!список", 30)
        self.assertEqual(self.state.snapshot()["list_show"]["remaining_ms"], 0)
        self.state.ingest(ChatMessage("twitch", "ch", "c1", "A", " !список"))
        self.state.ingest(ChatMessage("twitch", "ch", "c2", "A", "!СПИСОК"))
        self.state.ingest(ChatMessage("twitch", "ch", "c3", "A", "!список текст"))
        self.assertEqual(self.state.snapshot()["list_show"]["sequence"], 0)
        self.state.ingest(ChatMessage("twitch", "ch", "c4", "A", "!список"))
        self.assertEqual(self.state.snapshot()["list_show"]["remaining_ms"], 30000)
        self.clock.advance(12)
        self.state.ingest(ChatMessage("twitch", "ch", "c5", "B", "!список"))
        self.assertEqual(self.state.snapshot()["list_show"]["sequence"], 2)
        self.assertEqual(self.state.snapshot()["list_show"]["remaining_ms"], 30000)
        self.clock.advance(30)
        self.assertEqual(self.state.snapshot()["list_show"]["remaining_ms"], 0)

    def test_music_command_uses_exact_twitch_arrival_independently_of_list(self):
        self.state.configure(delay=20)
        self.state.set_obs_enabled("twitch", False)
        self.state.configure_list_show("slide", "!список", 30)
        self.state.configure_music_command("!музыка")
        for index, (platform, text) in enumerate([
            ("twitch", " !музыка"), ("twitch", "!музыка трек"),
            ("twitch", "!МУЗЫКА"), ("youtube", "!музыка"),
            ("twitch", "!список"),
        ]):
            self.state.ingest(ChatMessage(platform, "ch", str(index), "viewer", text))
        self.assertIsNone(self.state.music_command_event())
        self.assertEqual(self.state.snapshot()["list_show"]["remaining_ms"], 30000)
        command = ChatMessage("twitch", "ch", "music-1", "viewer", "!музыка")
        self.assertTrue(self.state.ingest(command))
        first = self.state.music_command_event()
        self.assertEqual(first["received_at_ms"], 100000)
        self.assertEqual(self.ids(obs=True), [])
        self.clock.advance(1)
        self.assertFalse(self.state.ingest(command))
        self.assertEqual(self.state.music_command_event(), first)
        self.state.ingest(ChatMessage("twitch", "ch", "music-2", "viewer", "!музыка"))
        second = self.state.music_command_event()
        self.assertGreater(second["sequence"], first["sequence"])
        self.assertEqual(second["received_at_ms"], 101000)
        self.assertEqual(self.state.snapshot()["list_show"]["remaining_ms"], 29000)
        self.state.configure_music_command("!трек")
        self.assertIsNone(self.state.music_command_event())
        self.state.ingest(ChatMessage("twitch", "ch", "music-3", "viewer", "!трек"))
        self.assertIsNotNone(self.state.music_command_event())
        self.state.change_source("twitch")
        self.assertIsNone(self.state.music_command_event())
        self.state.configure_music_command("")
        self.state.ingest(ChatMessage("twitch", "ch", "music-4", "viewer", "!трек"))
        self.assertIsNone(self.state.music_command_event())

    def test_list_command_works_when_obs_chat_off(self):
        self.state.configure_list_show("slide", "show", 20)
        self.state.set_obs_enabled("twitch", False)
        self.state.ingest(ChatMessage("twitch", "ch", "cmd", "viewer", "show"))
        self.assertEqual(self.state.snapshot()["list_show"]["sequence"], 1)
        self.assertEqual(self.ids(obs=True), [])
        self.assertEqual(self.ids(), ["cmd"])

    def test_list_command_change_only_applies_to_new_arrivals(self):
        self.state.configure_list_show("slide", "old", 30)
        self.state.configure(delay=8)
        self.state.ingest(ChatMessage("twitch", "ch", "c1", "viewer", "old"))
        self.clock.advance(3)
        self.state.configure_list_show("slide", "new", 40)
        self.state.ingest(ChatMessage("twitch", "ch", "c2", "viewer", "old"))
        self.assertEqual(self.state.snapshot()["list_show"]["sequence"], 1)
        self.clock.advance(8)
        self.assertEqual(self.state.snapshot()["list_show"]["sequence"], 1)
        self.state.ingest(ChatMessage("twitch", "ch", "c3", "viewer", "new"))
        self.assertEqual(self.state.snapshot()["list_show"]["sequence"], 2)

    def test_obs_disable_preserves_previous_and_filters_at_ready_time(self):
        self.state.configure(delay=4)
        self.state.ingest(msg(identifier="old"))
        self.clock.advance(4)
        self.assertEqual(self.ids(obs=True), ["old"])
        self.state.ingest(msg(identifier="pending"))
        self.state.set_obs_enabled("twitch", False)
        self.assertEqual(self.ids(obs=True), ["old"])
        self.clock.advance(4)
        self.assertEqual(self.ids(obs=True), ["old"])
        self.state.ingest(msg(identifier="ready_after_enable"))
        self.state.set_obs_enabled("twitch", True)
        self.clock.advance(4)
        self.assertEqual(self.ids(obs=True), ["old", "ready_after_enable"])
        self.state.ingest(msg(identifier="fresh"))
        self.clock.advance(4)
        self.assertEqual(self.ids(obs=True), ["old", "ready_after_enable", "fresh"])
        self.assertEqual(self.ids(), ["old", "pending", "ready_after_enable", "fresh"])

    def test_list_empty_command_never_matches_and_timer_survives_duration_change(self):
        self.state.configure_list_show("slide", "", 30)
        self.state.ingest(ChatMessage("twitch", "ch", "empty", "viewer", ""))
        self.assertEqual(self.state.snapshot()["list_show"]["sequence"], 0)
        self.state.configure_list_show("slide", "go", 30)
        self.state.ingest(ChatMessage("twitch", "ch", "go", "viewer", "go"))
        self.clock.advance(10)
        self.state.configure_list_show("slide", "next", 120)
        self.assertEqual(self.state.snapshot()["list_show"]["remaining_ms"], 20000)
        self.state.configure_list_show("hidden", "next", 120)
        self.assertEqual(self.state.snapshot()["list_show"]["remaining_ms"], 0)

    def test_disconnect_keeps_published_drops_pending(self):
        self.state.ingest(msg())
        self.state.configure(delay=5)
        self.state.ingest(msg(identifier="2"))
        self.state.disconnect("twitch")
        self.clock.advance(5)
        self.assertEqual(self.ids(), ["1"])

    def test_source_change_clears_only_that_platform(self):
        self.state.ingest(msg())
        self.state.ingest(msg(platform="youtube", identifier="1"))
        before = self.state.operator_feed_snapshot()
        self.state.change_source("twitch")
        self.assertEqual([m['platform'] for m in self.state.operator_feed_snapshot(before['key'])['messages']], ['youtube'])
        self.assertEqual(len(self.ids()), 1)
        self.assertEqual(self.ids(), ["1"])
        self.assertEqual(self.state.snapshot()["messages"][0]["platform"], "youtube")
        self.assertTrue(self.state.ingest(msg()))

    def test_deletion_updates_both_and_pending(self):
        self.state.ingest(msg())
        self.state.delete_message("twitch", "channel", "1")
        self.assertEqual(self.ids(), [])
        self.assertEqual(self.ids(obs=True), [])
        self.state.configure(delay=3)
        self.state.ingest(msg(identifier="2"))
        self.state.delete_message("twitch", "channel", "2")
        self.clock.advance(3)
        self.assertEqual(self.ids(), [])

    def test_limit_reduces_both_views_without_backfill(self):
        for i in range(15):
            self.state.ingest(msg(identifier=str(i)))
        before = self.state.operator_feed_snapshot()
        self.state.configure(limit=10)
        self.assertEqual(self.ids(), [str(i) for i in range(5, 15)])
        after = self.state.operator_feed_snapshot(before["key"])
        self.assertEqual([m["external_id"] for m in after["messages"]], self.ids())
        self.assertEqual(self.ids(obs=True), self.ids())
        self.state.configure(limit=100)
        self.assertEqual(len(self.ids()), 10)

    def test_validation(self):
        for x in (-1, float("nan"), float("inf"), "bad"):
            with self.assertRaises(ValueError):
                MultichatState(delay=x)
        for x in (0, 1001, 1.2, True):
            with self.assertRaises(ValueError):
                MultichatState(limit=x)

    def test_invalid_multi_setting_change_is_atomic(self):
        before = self.state.snapshot()
        with self.assertRaises(ValueError):
            self.state.configure(limit=10, delay=float("nan"))
        after = self.state.snapshot()
        self.assertEqual(before["limit"], after["limit"])
        self.assertEqual(before["delay"], after["delay"])

    def test_existing_message_not_repeated_on_time_toggle(self):
        self.state.ingest(msg())
        self.state.configure(show_time=False)
        self.state.configure(show_time=True)
        self.assertEqual(self.ids(), ["1"])
        self.assertEqual(self.ids(obs=True), ["1"])

    def test_extension_of_delay_keeps_existing_pending(self):
        self.state.configure(delay=2)
        self.state.ingest(msg())
        self.clock.advance(1)
        self.state.configure(delay=5)
        self.clock.advance(2)
        self.assertEqual(self.ids(), [])
        self.clock.advance(2)
        self.assertEqual(self.ids(), ["1"])

    def test_delay_buffer_uses_receipt_fallback(self):
        self.state.configure(delay=2)
        self.state.ingest(msg(identifier="first", sent=None))
        self.clock.advance(0.1)
        self.state.ingest(msg(identifier="second", sent=None))
        self.clock.advance(2)
        self.assertEqual(self.ids(), ["first", "second"])

    def test_late_delivery_is_not_inserted_backwards(self):
        self.state.configure(delay=2)
        self.state.ingest(msg(identifier="first", sent=100))
        self.clock.advance(2)
        self.assertEqual(self.ids(), ["first"])
        self.state.ingest(msg(identifier="late", sent=10))
        self.clock.advance(2)
        self.assertEqual(self.ids(), ["first", "late"])

    def test_empty_state_both_views(self):
        self.assertEqual(self.ids(), [])
        self.assertEqual(self.ids(obs=True), [])
        self.assertEqual(self.state.snapshot()["overflow_count"], 0)

    def test_source_change_does_not_affect_other_platform(self):
        self.state.configure(delay=4)
        self.state.ingest(msg(platform="youtube", identifier="y"))
        self.state.ingest(msg(platform="twitch", identifier="t"))
        self.state.change_source("twitch")
        self.clock.advance(4)
        self.assertEqual(self.ids(), ["y"])

    def test_pending_is_bounded_when_delay_is_huge(self):
        self.state.configure(limit=10, delay=1000000)
        for i in range(25):
            self.state.ingest(msg(identifier=str(i)))
        snapshot = self.state.snapshot()
        self.assertEqual(snapshot["overflow_count"], 5)
        self.assertEqual(snapshot["messages"], [dict(**m) for m in snapshot["messages"]])
        self.assertEqual(self.ids(), [str(i) for i in range(5)])


if __name__ == "__main__":
    unittest.main()
