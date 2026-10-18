"""P16-B: a wheel-only stop preserves the auction and its verified RNG draw."""
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


class WheelStopOnlyTests(unittest.TestCase):
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
        # Unexpected application error dialogs must fail fast instead of
        # hanging an unattended native Windows regression job.
        self.critical_patch = patch.object(
            QMessageBox, "critical",
            side_effect=AssertionError("Unexpected application error dialog"),
        )
        self.critical_patch.start()

    def tearDown(self):
        self.critical_patch.stop()
        self.window.thread_pool.waitForDone(5000)
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        self.temp.cleanup()

    def start_partial_spin(self, mode, wheel_format="standard"):
        ms = 13000
        if mode == "max_amount":
            sid = self.db.create_auction_session(
                "max_amount", 60, wheel_duration_ms=ms
            )
            self.db.finish_auction(sid)
            self.assertEqual(
                self.db.get_auction_session(sid)["status"], "tie_break_required"
            )
            self.db.start_auction_tie_wheel(sid, wheel_duration_ms=ms)
        else:
            self.tab.mode_combo.setCurrentIndex(
                self.tab.mode_combo.findData("weighted_wheel")
            )
            self.tab.wheel_format_combo.setCurrentIndex(
                self.tab.wheel_format_combo.findData(wheel_format)
            )
            sid = self.db.create_auction_session(
                "weighted_wheel", 0, start_in_wheel_mode=True,
                wheel_format=wheel_format, wheel_duration_ms=ms,
            )
        self.db.run_weighted_wheel(sid, pick=0)
        self.db.prepare_wheel_animation(sid, lead_in_ms=1200)
        self.tab._active_auction_id = sid
        self.tab.refresh()
        self.assertTrue(self.tab.stop_wheel_btn.isVisible())
        self.assertTrue(self.tab.cancel_btn.isVisible())
        self.assertLess(
            self.tab.stop_wheel_btn.mapToGlobal(
                self.tab.stop_wheel_btn.rect().topLeft()
            ).y(),
            self.tab.cancel_btn.mapToGlobal(
                self.tab.cancel_btn.rect().topLeft()
            ).y(),
        )
        return sid

    def proof(self, sid):
        with self.db.connect() as conn:
            return [
                tuple(row) for row in conn.execute(
                    "SELECT run_id, spin_index, winner_game_id, rng_value "
                    "FROM wheel_verification_snapshots "
                    "WHERE auction_id=? ORDER BY id",
                    (sid,),
                ).fetchall()
            ]

    def exercise(self, mode, wheel_format="standard"):
        sid = self.start_partial_spin(mode, wheel_format)
        before = self.db.get_auction_session(sid)
        proof_before = self.proof(sid)
        self.assertEqual(len(proof_before), 1)
        with patch.object(QMessageBox, "warning", return_value=QMessageBox.Yes):
            self.tab.stop_wheel()

        stopped = self.db.get_auction_session(sid)
        self.assertEqual(stopped["mode"], mode)
        self.assertEqual(stopped["status"], "awaiting_wheel")
        self.assertIsNone(stopped["wheel_spin_id"])
        self.assertEqual(stopped["winner_game_id"], before["winner_game_id"])
        self.assertEqual(stopped["rng_value"], before["rng_value"])
        self.assertEqual(self.proof(sid), proof_before)
        self.assertEqual(self.tab._parse_timer_text(self.tab.timer_edit.text()), 13000)
        self.assertFalse(self.tab.stop_wheel_btn.isVisible())
        self.assertTrue(self.tab.cancel_btn.isVisible())
        payload = self.db.wheel_payload(sid)
        self.assertIsNone(payload["winner"])
        self.assertIsNone(payload["animation"]["spin_id"])
        self.assertEqual(len(payload["sectors"]), 2)

        # No second RNG draw is permitted, even for Random.org+ in production.
        with patch.object(
            self.db, "run_weighted_wheel",
            side_effect=AssertionError("unexpected reroll"),
        ):
            self.tab.run_wheel(confirm=False)
        after = self.db.get_auction_session(sid)
        self.assertEqual(after["status"], "winner_selected")
        self.assertNotEqual(after["wheel_spin_id"], before["wheel_spin_id"])
        self.assertEqual(after["winner_game_id"], before["winner_game_id"])
        self.assertEqual(after["rng_value"], before["rng_value"])
        self.assertEqual(self.proof(sid), proof_before)
        self.tab.refresh()
        self.assertTrue(self.tab.stop_wheel_btn.isVisible())

        # Universal full-auction cancellation must remain independent.
        with patch.object(QMessageBox, "warning", return_value=QMessageBox.Yes):
            self.tab.cancel_auction()
        self.assertIsNone(self.tab._current_session())
        self.assertEqual(self.db.get_auction_session(sid)["status"], "cancelled")

    def test_tie_wheel_stop_preserves_max_auction_finalists(self):
        self.exercise("max_amount")

    def test_standard_wheel_stop_and_replay(self):
        self.exercise("weighted_wheel")

    def test_elimination_wheel_stop_and_replay(self):
        self.exercise("weighted_wheel", "elimination")

    def test_declined_stop_keeps_the_spin(self):
        sid = self.start_partial_spin("max_amount")
        before = self.db.get_auction_session(sid)
        original_proof = self.proof(sid)
        with patch.object(QMessageBox, "warning", return_value=QMessageBox.No):
            self.tab.stop_wheel()
        after = self.db.get_auction_session(sid)
        self.assertEqual(after["status"], "winner_selected")
        self.assertEqual(after["wheel_spin_id"], before["wheel_spin_id"])
        self.assertEqual(self.proof(sid), original_proof)

    def test_clean_unspun_wheel_cannot_be_replayed(self):
        sid = self.db.create_auction_session(
            "weighted_wheel", 0,
            start_in_wheel_mode=True, wheel_duration_ms=13000,
        )
        with self.assertRaises(RuntimeError):
            self.db.prepare_wheel_animation(sid, replay_stopped=True)
        with self.assertRaises(RuntimeError):
            self.db.stop_wheel_animation(sid)


if __name__ == "__main__":
    unittest.main()
