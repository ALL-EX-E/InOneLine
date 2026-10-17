"""P16-A: cancelled spins cannot seed the next spin with elapsed remainder."""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
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


class CancelDurationTests(unittest.TestCase):
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
        QTest.qWait(650)
        self.tab = self.window.auction_tab

    def tearDown(self):
        self.window.thread_pool.waitForDone(5000)
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        self.temp.cleanup()

    def begin_partial_spin(self, wheel_format):
        self.tab.mode_combo.setCurrentIndex(self.tab.mode_combo.findData("weighted_wheel"))
        self.tab.wheel_format_combo.setCurrentIndex(self.tab.wheel_format_combo.findData(wheel_format))
        self.tab._set_wheel_timer_ms(13000)
        self.tab._prestart_wheel_duration_ms = 13000
        auction_id = self.db.create_auction_session(
            "weighted_wheel", 0, wheel_duration_ms=13000,
            start_in_wheel_mode=True, wheel_format=wheel_format,
        )
        self.db.run_weighted_wheel(auction_id, pick=0)
        self.db.prepare_wheel_animation(auction_id)
        with self.db.connect() as conn:
            conn.execute("UPDATE auction_sessions SET wheel_started_at=? WHERE id=?", (
                (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat(), auction_id,
            ))
        self.tab._active_auction_id = auction_id
        self.tab.refresh()
        self.tab._tick_timer_display()
        self.assertLess(self.tab._parse_timer_text(self.tab.timer_edit.text()), 10000)
        self.assertGreater(self.tab._parse_timer_text(self.tab.timer_edit.text()), 5000)
        return auction_id

    def assert_cancel_restart(self, wheel_format):
        old_id = self.begin_partial_spin(wheel_format)
        old_session = self.db.get_auction_session(old_id)
        with patch.object(QMessageBox, "warning", return_value=QMessageBox.Yes):
            self.tab.cancel_auction()
        QTest.qWait(40)
        self.assertIsNone(self.tab._current_session())
        self.assertEqual(self.tab._parse_timer_text(self.tab.timer_edit.text()), 13000, "Cancelled spin left remainder in next-start editor")
        self.assertEqual(self.tab._prestart_wheel_duration_ms, 13000)
        self.assertEqual(self.db.get_setting("auction_wheel_default_duration_ms", "8000"), "8000", "Cancel rewrote Settings default")
        cancelled = self.db.get_auction_session(old_id)
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(cancelled["wheel_spin_id"], old_session["wheel_spin_id"])
        self.assertEqual(cancelled["winner_game_id"], old_session["winner_game_id"])
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            self.tab.start_auction()
            QTest.qWait(70)
        new_session = self.tab._current_session()
        self.assertIsNotNone(new_session)
        self.assertNotEqual(new_session["id"], old_id)
        self.assertEqual(new_session["wheel_duration_ms"], 13000)

    def test_standard_cancel_restores_full_duration_for_new_spin(self):
        self.assert_cancel_restart("standard")

    def test_elimination_cancel_restores_full_duration_for_new_spin(self):
        self.assert_cancel_restart("elimination")

    def test_declined_cancel_preserves_active_spin_and_countdown(self):
        old_id = self.begin_partial_spin("standard")
        with patch.object(QMessageBox, "warning", return_value=QMessageBox.No):
            self.tab.cancel_auction()
        self.assertEqual(self.tab._current_session()["id"], old_id)
        self.assertEqual(self.db.get_auction_session(old_id)["status"], "winner_selected")
        self.assertLess(self.tab._parse_timer_text(self.tab.timer_edit.text()), 10000)

    def test_max_amount_tie_wheel_cancel_preserves_auction_default(self):
        self.tab.mode_combo.setCurrentIndex(self.tab.mode_combo.findData("max_amount"))
        max_default_ms = self.tab._saved_max_amount_default_duration_ms()
        old_id = self.db.create_auction_session("max_amount", 60, wheel_duration_ms=13000)
        self.db.finish_auction(old_id)
        self.assertEqual(self.db.get_auction_session(old_id)["status"], "tie_break_required")
        self.db.start_auction_tie_wheel(old_id)
        self.db.run_weighted_wheel(old_id, pick=0)
        self.db.prepare_wheel_animation(old_id)
        self.tab._active_auction_id = old_id
        self.tab.refresh()
        with patch.object(QMessageBox, "warning", return_value=QMessageBox.Yes):
            self.tab.cancel_auction()
        QTest.qWait(40)
        self.assertIsNone(self.tab._current_session())
        self.assertEqual(self.tab._timer_context, "auction")
        self.assertEqual(self.tab._parse_timer_text(self.tab.timer_edit.text()), max_default_ms)
        self.assertEqual(self.tab._prestart_wheel_duration_ms, 13000)
        self.assertEqual(self.db.get_auction_session(old_id)["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
