"""P16-F: real main/overtime timer preparation must not consume set duration."""
from __future__ import annotations

import math
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from streaming_manager.app_paths import AppPaths
from streaming_manager.constants import SCHEMA_VERSION
from streaming_manager.database import Database, Game
from streaming_manager.ui import MainWindow


def milliseconds_between(start, finish):
    return (datetime.fromisoformat(str(finish)) -
            datetime.fromisoformat(str(start))).total_seconds() * 1000.0


class AuctionPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.temp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.db.add_game(Game(None, "Lead A", None, 100, 0, "not_played", ""))
        self.db.add_game(Game(None, "Lead B", None, 100, 0, "not_played", ""))
        self.window = MainWindow(self.db, self.paths)
        self.window.show()
        self.window._set_current_main_page(self.window.auction_tab)
        QTest.qWait(75)
        self.tab = self.window.auction_tab
        self.critical = patch.object(
            QMessageBox, "critical",
            side_effect=AssertionError("Unexpected Qt modal error"),
        )
        self.critical.start()

    def tearDown(self):
        self.critical.stop()
        self.window.thread_pool.waitForDone(5000)
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        self.temp.cleanup()

    def start_main(self, duration_ms=8000):
        sid = self.db.create_auction_session(
            "max_amount", math.ceil(duration_ms / 1000),
            duration_ms=duration_ms, wheel_duration_ms=13000,
        )
        self.tab._active_auction_id = sid
        self.tab.refresh()
        return sid

    def assert_pending_duration(self, sid, expected_ms):
        session = self.db.get_auction_session(sid)
        start = session["timer_phase_starts_at"]
        self.assertIsNotNone(start)
        self.assertGreater(
            (datetime.fromisoformat(start) - datetime.now(timezone.utc)).total_seconds(), 0
        )
        self.assertAlmostEqual(
            milliseconds_between(start, session["deadline_at"]), expected_ms, delta=1
        )
        self.assertEqual(self.db.auction_remaining_milliseconds(sid), expected_ms)
        self.tab.refresh()
        self.assertEqual(self.tab._timer_display_remaining_ms(), expected_ms)
        obs = self.db.current_timer_payload({"mode": "max_amount"})
        self.assertEqual(obs["remaining_ms"], expected_ms)
        self.assertTrue(obs["preparing"])
        self.assertGreater(obs["preparation_remaining_ms"], 0)
        return session

    def test_schema21_and_main_countdown_boundary(self):
        self.assertEqual(SCHEMA_VERSION, 21)
        sid = self.start_main(8000)
        session = self.assert_pending_duration(sid, 8000)
        self.assertAlmostEqual(
            milliseconds_between(session["started_at"], session["timer_phase_starts_at"]),
            1200, delta=2,
        )
        # The scheduled start is a separate field; source-time history still
        # starts at the original session creation timestamp.
        self.assertLess(
            datetime.fromisoformat(session["started_at"]),
            datetime.fromisoformat(session["timer_phase_starts_at"]),
        )
        QTest.qWait(1350)
        remaining = self.db.auction_remaining_milliseconds(sid)
        self.assertLess(remaining, 8000)
        self.assertGreater(remaining, 7600)

    def test_adjust_reset_and_s2_extension_cannot_restart_preparation(self):
        sid = self.start_main(5000)
        start = self.assert_pending_duration(sid, 5000)["timer_phase_starts_at"]
        self.db.adjust_auction_time_ms(sid, 3000)
        session = self.assert_pending_duration(sid, 8000)
        self.assertEqual(session["timer_phase_starts_at"], start)
        self.db.reset_auction_timer_ms(sid)
        session = self.assert_pending_duration(sid, 5000)
        self.assertEqual(session["timer_phase_starts_at"], start)

    def test_pause_during_preparation_resumes_with_new_full_lead_in(self):
        sid = self.start_main(7000)
        old = self.assert_pending_duration(sid, 7000)
        self.db.pause_auction(sid)
        paused = self.db.get_auction_session(sid)
        self.assertEqual(paused["status"], "paused")
        self.assertEqual(paused["remaining_ms"], 7000)
        self.assertIsNone(paused["deadline_at"])
        self.db.resume_auction(sid)
        resumed = self.assert_pending_duration(sid, 7000)
        self.assertNotEqual(old["timer_phase_starts_at"], resumed["timer_phase_starts_at"])

    def test_overtime_freezes_same_qt_and_obs_duration(self):
        sid = self.start_main(10000)
        self.db.finish_auction(sid)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "tie_break_required")
        self.db.start_auction_tie_overtime(sid, 6, duration_ms=6000)
        self.assert_pending_duration(sid, 6000)
        self.assertEqual(self.db.get_auction_session(sid)["wheel_duration_ms"], 13000)

    def test_legacy_null_boundary_retains_immediate_countdown(self):
        sid = self.start_main(8000)
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET timer_phase_starts_at=NULL, "
                "deadline_at=strftime('%Y-%m-%dT%H:%M:%f+00:00','now','+8 seconds') "
                "WHERE id=?",
                (sid,),
            )
        self.tab.refresh()
        payload = self.db.current_timer_payload({"mode": "max_amount"})
        self.assertFalse(payload["preparing"])
        self.assertEqual(payload["preparation_remaining_ms"], 0)
        self.assertLessEqual(self.tab._timer_display_remaining_ms(), 8000)

    def test_soundtrack_is_prepared_paused_until_same_phase_start(self):
        sid = self.start_main(9000)
        session = self.db.get_auction_session(sid)
        with (
            patch.object(
                self.tab, "_resolved_auction_soundtrack_playlist",
                return_value=([Path(self.temp.name) / "mock.mp3"], [777], 0),
            ),
            patch.object(self.tab.auction_audio, "start_playlist") as start,
        ):
            self.tab._start_auction_soundtrack_for_session(session, restart=True)
            self.assertEqual(start.call_count, 1)
            self.assertTrue(start.call_args.kwargs["start_paused"])
            self.assertTrue(self.tab._auction_preparation_audio_timer.isActive())
            self.assertFalse(self.tab.auction_audio.playing)
        self.tab.cancel_auction = lambda: None
        self.db.cancel_auction(sid)
        self.tab._start_soundtrack_at_phase_boundary()
        self.assertFalse(self.db.get_auction_session(sid)["status"] == "running")
        self.tab._auction_preparation_audio_timer.stop()


if __name__ == "__main__":
    unittest.main()
