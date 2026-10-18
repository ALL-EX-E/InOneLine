"""P16-C / UI-072: 1-second wheel bounds and full-width transparent stop button."""
from __future__ import annotations

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
from streaming_manager.database import Database, Game
from streaming_manager.ui import MainWindow
from streaming_manager.views.common import APP_STYLE


class WheelOneSecondLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.temp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.db.add_game(Game(None, "First", None, 100, 0, "not_played", ""))
        self.db.add_game(Game(None, "Second", None, 100, 0, "not_played", ""))
        self.window = MainWindow(self.db, self.paths)
        self.window.show()
        self.window._set_current_main_page(self.window.auction_tab)
        QTest.qWait(250)
        self.tab = self.window.auction_tab
        self.settings = self.window.settings_tab
        self.critical = patch.object(
            QMessageBox, "critical",
            side_effect=AssertionError("Unexpected modal error in wheel one-second QA"),
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

    def test_settings_accept_1_second_and_reject_below(self):
        self.assertEqual(self.db.WHEEL_MIN_DURATION_MS, 1000)
        self.settings.auction_wheel_duration.setText("00:00:01.000")
        with patch.object(QMessageBox, "information"):
            self.settings.save_auction_settings()
        self.assertEqual(
            self.db.get_setting("auction_wheel_default_duration_ms"), "1000"
        )
        self.assertEqual(self.settings._saved_auction_wheel_duration_ms(), 1000)
        self.assertEqual(self.tab._saved_wheel_default_duration_ms(), 1000)
        self.settings.auction_wheel_duration.setText("00:00:00.999")
        with patch.object(QMessageBox, "warning") as warning:
            self.settings.save_auction_settings()
        self.assertEqual(warning.call_count, 1)
        self.assertEqual(
            self.db.get_setting("auction_wheel_default_duration_ms"), "1000"
        )

    def test_direct_wheel_exact_1000ms_with_separate_preparation(self):
        for invalid in (0, 999, 86400001):
            with self.assertRaises(ValueError):
                self.db.create_auction_session(
                    "weighted_wheel", 0, start_in_wheel_mode=True,
                    wheel_duration_ms=invalid,
                )
        sid = self.db.create_auction_session(
            "weighted_wheel", 0, start_in_wheel_mode=True,
            wheel_duration_ms=1000,
        )
        self.assertEqual(self.db.get_auction_session(sid)["wheel_duration_ms"], 1000)
        with self.assertRaises(ValueError):
            self.db.set_auction_wheel_duration_ms(sid, 999)
        self.assertEqual(self.db.set_auction_wheel_duration_ms(sid, 1000), 1000)
        self.db.run_weighted_wheel(sid, pick=0)
        payload = self.db.prepare_wheel_animation(sid, lead_in_ms=1200)
        self.assertEqual(payload["animation"]["duration_ms"], 1000)
        start = datetime.fromisoformat(str(payload["animation"]["started_at"]))
        lead_in_remaining = (start - datetime.now(timezone.utc)).total_seconds()
        self.assertGreater(lead_in_remaining, 0.1)
        self.assertLessEqual(lead_in_remaining, 1.4)
        timer = self.db._wheel_animation_timer_state(
            self.db.get_auction_session(sid)
        )
        self.assertEqual(timer["remaining_ms"], 1000)
        self.assertFalse(timer["complete"])
        self.tab._active_auction_id = sid
        self.tab.refresh()
        self.assertTrue(self.tab.stop_wheel_btn.isVisible())
        self.assertTrue(self.tab.cancel_btn.isVisible())
        self.assertEqual(
            self.tab.timer_finish_widget.property("cardContent"), True
        )
        self.assertIn('QWidget[cardContent="true"]', APP_STYLE)

        # Each button occupies the identical available width at both sizes,
        # including the responsive stacked layout.
        for width, height in ((1450, 900), (570, 600)):
            self.window.resize(width, height)
            QTest.qWait(80)
            self.app.processEvents()
            self.assertTrue(self.tab.stop_wheel_btn.isVisible())
            self.assertTrue(self.tab.cancel_btn.isVisible())
            self.assertLessEqual(
                abs(self.tab.stop_wheel_btn.width() - self.tab.cancel_btn.width()),
                2,
                f"Wheel Stop width diverged at window width {width}",
            )
            self.assertLess(
                self.tab.stop_wheel_btn.mapToGlobal(
                    self.tab.stop_wheel_btn.rect().topLeft()
                ).y(),
                self.tab.cancel_btn.mapToGlobal(
                    self.tab.cancel_btn.rect().topLeft()
                ).y(),
            )

    def test_one_second_max_amount_tie_and_replay_preserve_rng(self):
        sid = self.db.create_auction_session(
            "max_amount", 60, wheel_duration_ms=1000
        )
        self.db.finish_auction(sid)
        self.assertEqual(
            self.db.get_auction_session(sid)["status"], "tie_break_required"
        )
        with self.assertRaises(ValueError):
            self.db.start_auction_tie_wheel(sid, wheel_duration_ms=999)
        self.db.start_auction_tie_wheel(sid, wheel_duration_ms=1000)
        self.assertEqual(
            self.db.get_auction_session(sid)["status"], "awaiting_wheel"
        )
        self.db.run_weighted_wheel(sid, pick=0)
        original = self.db.prepare_wheel_animation(sid, lead_in_ms=1200)
        before = self.db.get_auction_session(sid)
        proof = self.db.get_wheel_verification_snapshot(sid)
        self.assertEqual(original["animation"]["duration_ms"], 1000)
        self.db.stop_wheel_animation(sid)
        stopped = self.db.get_auction_session(sid)
        self.assertEqual(stopped["status"], "awaiting_wheel")
        self.assertEqual(stopped["wheel_duration_ms"], 1000)
        self.assertEqual(stopped["rng_value"], before["rng_value"])
        replay = self.db.prepare_wheel_animation(sid, replay_stopped=True)
        again = self.db.get_auction_session(sid)
        self.assertEqual(replay["animation"]["duration_ms"], 1000)
        self.assertNotEqual(
            replay["animation"]["spin_id"],
            original["animation"]["spin_id"],
        )
        self.assertEqual(again["winner_game_id"], before["winner_game_id"])
        self.assertEqual(again["rng_value"], before["rng_value"])
        self.assertEqual(self.db.get_wheel_verification_snapshot(sid), proof)

    def test_short_motion_still_finishes_at_persisted_target(self):
        from streaming_manager.wheel_motion import wheel_motion_progress
        self.assertEqual(wheel_motion_progress(0, 1000), 0.0)
        self.assertEqual(wheel_motion_progress(1, 1000), 1.0)
        positions = [
            wheel_motion_progress(i / 50, 1000) for i in range(51)
        ]
        self.assertTrue(
            all(b >= a for a, b in zip(positions, positions[1:]))
        )
        self.assertGreater(positions[1], 0.0)


if __name__ == "__main__":
    unittest.main()
