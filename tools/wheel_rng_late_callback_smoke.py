"""P16-E: late remote RNG callbacks never affect a later wheel/audio session.

This regression does not connect to RANDOM.ORG: it delivers late callback
signals deterministically after cancelling one auction and starting another.
"""
from __future__ import annotations

import sys
import unittest
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


class WheelLateRngCallbacksTests(unittest.TestCase):
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
        QTest.qWait(300)
        self.tab = self.window.auction_tab

    def tearDown(self):
        self.window.thread_pool.waitForDone(5000)
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        self.temp.cleanup()

    def new_awaiting(self):
        sid = self.db.create_auction_session(
            "weighted_wheel", 0, start_in_wheel_mode=True,
            wheel_duration_ms=12000,
        )
        self.tab._active_auction_id = sid
        self.tab.refresh()
        self.assertEqual(self.db.get_auction_session(sid)["status"], "awaiting_wheel")
        return sid

    def replace_with_new_auction(self, *, spinning=True):
        old = self.new_awaiting()
        self.db.cancel_auction(old)
        new = self.new_awaiting()
        if spinning:
            self.db.run_weighted_wheel(new, pick=0)
            self.db.prepare_wheel_animation(new, lead_in_ms=1200)
            self.tab.refresh()
            self.assertTrue(self.tab.stop_wheel_btn.isVisible())
        return old, new

    def test_late_rng_result_cannot_release_new_spin_owner(self):
        old, new = self.replace_with_new_auction()
        before = self.db.get_auction_session(new)
        self.assertTrue(before["wheel_spin_id"])
        with (
            patch.object(self.tab, "_release_auction_audio_owner") as release,
            patch.object(self.db, "run_weighted_wheel", side_effect=AssertionError("stale RNG draw")),
            patch.object(QMessageBox, "critical") as error,
        ):
            self.tab._apply_wheel_draw(old, None)
        release.assert_not_called()
        error.assert_not_called()
        after = self.db.get_auction_session(new)
        self.assertEqual(after["wheel_spin_id"], before["wheel_spin_id"])
        self.assertEqual(after["winner_game_id"], before["winner_game_id"])
        self.assertEqual(after["rng_value"], before["rng_value"])

    def test_late_rng_error_cannot_interrupt_new_session(self):
        old, new = self.replace_with_new_auction(spinning=False)
        with (
            patch.object(self.tab, "_release_auction_audio_owner") as release,
            patch.object(QMessageBox, "critical") as error,
        ):
            self.tab._wheel_rng_failed(RuntimeError("old remote error"), old)
        release.assert_not_called()
        error.assert_not_called()
        self.assertEqual(self.db.get_auction_session(new)["status"], "awaiting_wheel")

    def test_live_rng_error_still_shows_one_error_and_releases_owner(self):
        current = self.new_awaiting()
        with (
            patch.object(self.tab, "_release_auction_audio_owner") as release,
            patch.object(QMessageBox, "critical") as error,
        ):
            self.tab._wheel_rng_failed(RuntimeError("current RNG offline"), current)
        release.assert_called_once_with()
        error.assert_called_once()
        self.assertEqual(self.db.get_auction_session(current)["status"], "awaiting_wheel")

    def test_double_click_during_lead_in_cannot_reroll(self):
        current = self.new_awaiting()
        self.db.run_weighted_wheel(current, pick=0)
        payload = self.db.prepare_wheel_animation(current, lead_in_ms=1200)
        before = self.db.get_auction_session(current)
        self.tab.refresh()
        self.assertIsNotNone(before["wheel_spin_id"])
        self.assertEqual(payload["animation"]["duration_ms"], 12000)
        with (
            patch.object(self.db, "run_weighted_wheel", side_effect=AssertionError("second RNG call")),
            patch.object(self.tab, "_schedule_wheel_soundtrack") as schedule,
        ):
            self.tab.run_wheel(confirm=False)
            self.tab.run_wheel(confirm=False)
        schedule.assert_not_called()
        after = self.db.get_auction_session(current)
        self.assertEqual(after["wheel_spin_id"], before["wheel_spin_id"])
        self.assertEqual(after["winner_game_id"], before["winner_game_id"])
        self.assertEqual(after["rng_value"], before["rng_value"])

    def test_in_flight_rng_worker_blocks_reentry(self):
        current = self.new_awaiting()
        self.tab._wheel_rng_worker = object()
        try:
            with (
                patch.object(self.db, "run_weighted_wheel", side_effect=AssertionError("duplicate RNG")),
                patch.object(QMessageBox, "question") as question,
            ):
                self.tab.run_wheel(confirm=True)
                self.tab.run_wheel(confirm=False)
            question.assert_not_called()
        finally:
            self.tab._wheel_rng_worker = None
        self.assertEqual(self.db.get_auction_session(current)["status"], "awaiting_wheel")


if __name__ == "__main__":
    unittest.main()
