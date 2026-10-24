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
        self.state.change_source("twitch")
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
        self.state.configure(limit=10)
        self.assertEqual(self.ids(), [str(i) for i in range(5, 15)])
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
