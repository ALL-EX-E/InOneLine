"""P16-D: tie overtime uses Max Amount default; timer, wheel and audio use one spin boundary."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, Game
from streaming_manager.ui import MainWindow


class AuctionTimerBoundaryTests(unittest.TestCase):
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
        self.db.set_setting("auction_max_amount_default_duration_ms", "90000")
        self.db.set_setting("auction_wheel_default_duration_ms", "14000")
        self.window = MainWindow(self.db, self.paths)
        self.window.show()
        self.window._set_current_main_page(self.window.auction_tab)
        QTest.qWait(350)
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

    def test_tie_overtime_uses_max_amount_default_not_wheel(self):
        sid = self.db.create_auction_session(
            "max_amount", 60, wheel_duration_ms=14000,
        )
        self.db.finish_auction(sid)
        self.assertEqual(
            self.db.get_auction_session(sid)["status"], "tie_break_required"
        )
        self.tab._active_auction_id = sid
        self.tab.refresh()
        self.tab.start_tie_overtime()
        self.assertTrue(self.tab._pending_tie_overtime)
        self.assertEqual(self.tab._parse_timer_text(self.tab.timer_edit.text()), 90000)
        self.tab.timer_edit.setText("00:00:25.000")
        self.tab.reset_auction_timer()
        self.assertEqual(self.tab._parse_timer_text(self.tab.timer_edit.text()), 90000)
        self.assertEqual(self.db.get_setting("auction_wheel_default_duration_ms"), "14000")
        self.tab.timer_edit.setText("00:00:33.000")
        self.tab._start_pending_tie_overtime()
        session = self.db.get_auction_session(sid)
        self.assertEqual(session["status"], "running")
        self.assertEqual(int(session["duration_ms"]), 33000)

        self.assertIn("«Настроек»", self.tab.timer_reset_btn.toolTip())
        self.assertIn("Максимальная сумма", self.tab.timer_reset_btn.toolTip())
        self.assertIn("колесо", self.tab.timer_reset_btn.toolTip())
        self.assertNotIn("колесо — 8 секунд", self.tab.timer_reset_btn.toolTip())

    def test_short_wheel_prep_local_obs_and_audio_one_boundary(self):
        sid = self.db.create_auction_session(
            "weighted_wheel", 0, start_in_wheel_mode=True,
            wheel_duration_ms=1000,
        )
        self.db.run_weighted_wheel(sid, pick=0)
        prepared = self.db.prepare_wheel_animation(sid, lead_in_ms=1200)
        animation = prepared["animation"]
        started_at = str(animation["started_at"])
        self.assertEqual(int(animation["duration_ms"]), 1000)

        self.tab._active_auction_id = sid
        self.tab.refresh()
        session = self.db.get_auction_session(sid)
        self.assertEqual(str(session["wheel_started_at"]), started_at)
        self.assertEqual(
            str(self.tab._timer_display_wheel_start.isoformat(timespec="milliseconds")),
            started_at,
        )
        local_wheel = self.tab.wheel_widget._payload["animation"]
        obs_wheel = self.db.current_wheel_payload("weighted_wheel")["animation"]
        self.assertEqual(str(local_wheel["started_at"]), started_at)
        self.assertEqual(str(obs_wheel["started_at"]), started_at)
        self.assertEqual(local_wheel["spin_id"], obs_wheel["spin_id"])
        obs_timer = self.db.current_timer_payload({"mode": "weighted_wheel"})
        self.assertEqual(obs_timer["timer_kind"], "wheel")
        self.assertEqual(obs_timer["remaining_ms"], 1000)
        self.assertFalse(obs_timer["running"])
        self.assertEqual(self.tab._timer_display_remaining_ms(), 1000)

        # Verify the schedule receives the EXACT committed wheel clock,
        # instead of another independently calculated now + lead-in.
        with (
            patch.object(
                self.tab, "_configured_soundtrack_asset",
                return_value=SimpleNamespace(id=99),
            ),
            patch(
                "streaming_manager.views.auction_parts.audio.resolve_media_asset_path",
                return_value=Path(self.temp.name) / "mock.mp3",
            ),
            patch.object(self.tab.wheel_audio, "schedule_loop") as schedule,
            patch.object(self.tab, "_acquire_auction_audio_owner"),
            patch.object(self.tab, "_sync_audio_owner_with_session"),
            patch.object(self.tab, "_refresh_browser_audio_snapshot"),
        ):
            self.tab._schedule_wheel_soundtrack(prepared)
        self.assertEqual(schedule.call_count, 1)
        kwargs = schedule.call_args.kwargs
        self.assertEqual(kwargs["started_at"], started_at)
        self.assertEqual(kwargs["duration_ms"], 1000)

    def test_pending_overtime_reset_preserves_manual_wheel_duration(self):
        sid = self.db.create_auction_session(
            "max_amount", 60, wheel_duration_ms=14000,
        )
        self.db.finish_auction(sid)
        self.tab._active_auction_id = sid
        self.tab.refresh()
        self.tab.start_tie_overtime()
        self.tab.timer_edit.setText("00:00:45.000")
        self.tab.reset_auction_timer()
        self.assertEqual(self.tab._parse_timer_text(self.tab.timer_edit.text()), 90000)
        self.assertEqual(
            self.db.get_auction_session(sid)["wheel_duration_ms"], 14000
        )


if __name__ == "__main__":
    unittest.main()
