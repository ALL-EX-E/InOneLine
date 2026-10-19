"""UI-086 P20-D: direct weighted wheel freezes only after source pending resolves."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QMessageBox

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, Game
from streaming_manager.views.auction import AuctionTab


class WeightedWheelPendingGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        for title, points in (("Alpha", 100), ("Beta", 90)):
            self.db.add_game(Game(None, title, None, points, 0, "not_played", ""))
        self.sid = self.db.create_auction_session(
            "weighted_wheel", 0, start_in_wheel_mode=True, wheel_duration_ms=8000,
        )
        self.assertEqual(self.db.get_auction_session(self.sid)["status"], "awaiting_wheel")
        self.now = "2026-10-19T09:00:00+00:00"

    def pending(self, auction_id, event_id="unresolved", *, status="awaiting_rate"):
        with self.db.connect() as conn:
            gid = int(conn.execute("SELECT id FROM games WHERE title='Alpha'").fetchone()[0])
            eid = int(conn.execute(
                "INSERT INTO external_events("
                "source,external_event_id,event_type,payload_json,processing_status,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("P20-D", event_id, "donation",
                 json.dumps({"normalized": {"lot_title": "Alpha"}}),
                 status, self.now),
            ).lastrowid)
            pid = int(conn.execute(
                "INSERT INTO pending_conversions("
                "external_event_row_id,game_id,auction_id,source_amount_text,"
                "source_unit,source_unit_label,unit_kind,status,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,?)",
                (eid, gid, auction_id, "5", "PLN", "PLN", "currency", status, self.now),
            ).lastrowid)
        return pid

    def snapshot(self):
        with self.db.connect() as conn:
            s = dict(conn.execute("SELECT * FROM auction_sessions WHERE id=?", (self.sid,)).fetchone())
            entries = [dict(x) for x in conn.execute(
                "SELECT * FROM auction_entries WHERE auction_id=? ORDER BY id", (self.sid,)
            ).fetchall()]
            draws = int(conn.execute("SELECT COUNT(*) FROM wheel_verification_snapshots").fetchone()[0])
        return s, entries, draws

    def test_database_blocks_pending_without_result_or_rng_writes(self):
        self.pending(self.sid)
        before = self.snapshot()
        with self.assertRaisesRegex(RuntimeError, "необработанные поступления"):
            self.db.run_weighted_wheel(self.sid, pick=0)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.db.count_unresolved_auction_conversions(self.sid), 1)

    def test_only_same_source_auction_pending_blocks(self):
        with self.db.connect() as conn:
            other = int(conn.execute(
                "INSERT INTO auction_sessions(name,mode,provider,created_at,status)"
                " VALUES(?,?,?,?,?)",
                ("Previous", "weighted_wheel", "local", self.now, "confirmed"),
            ).lastrowid)
        self.pending(other, event_id="previous")
        self.pending(None, event_id="outside")
        self.assertEqual(self.db.count_unresolved_auction_conversions(self.sid), 0)
        winner = self.db.run_weighted_wheel(self.sid, pick=0)
        self.assertTrue(winner > 0)
        self.assertEqual(self.db.get_auction_session(self.sid)["status"], "winner_selected")
        self.assertEqual(self.db.count_unresolved_auction_conversions(other), 1)

    def test_manual_decline_unlocks_identical_frozen_lot_snapshot(self):
        pid = self.pending(self.sid, status="awaiting_manual_apply")
        before_entries = self.snapshot()[1]
        with self.assertRaisesRegex(RuntimeError, "необработанные поступления"):
            self.db.run_weighted_wheel(self.sid, pick=0)
        self.db.reject_pending_conversion_event(pid)
        winner = self.db.run_weighted_wheel(self.sid, pick=0)
        self.assertTrue(winner > 0)
        session, after_entries, _ = self.snapshot()
        self.assertEqual(session["status"], "winner_selected")
        # Winner result markers may change, but weights must not.
        for before, after in zip(before_entries, after_entries):
            self.assertEqual(before["weight"], after["weight"])
            self.assertEqual(before["bid_sm_points"], after["bid_sm_points"])
        with self.assertRaises(RuntimeError):
            self.db.run_weighted_wheel(self.sid, pick=0)

    def test_interface_disables_fresh_wheel_and_shows_same_source_warning(self):
        pid = self.pending(self.sid)
        tab = AuctionTab(self.db)
        try:
            tab.show()
            tab._active_auction_id = self.sid
            tab.refresh()
            self.assertFalse(tab.start_btn.isEnabled())
            self.assertIn("Конвертация", tab.start_btn.toolTip())
            self.assertIn("1", tab.auction_pending_conversion_warning.text())
            with (
                patch.object(QMessageBox, "warning") as warning,
                patch.object(self.db, "set_auction_wheel_duration_ms",
                             side_effect=AssertionError("duration mutated")),
                patch.object(self.db, "run_weighted_wheel",
                             side_effect=AssertionError("RNG mutated")),
            ):
                tab.run_wheel(confirm=False)
            warning.assert_called_once()
            self.db.reject_pending_conversion_event(pid)
            tab.refresh()
            self.assertTrue(tab.start_btn.isEnabled())
            self.assertEqual(tab.start_btn.toolTip(), "")
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()

    def test_pending_gate_does_not_consume_random_org_ticket(self):
        self.pending(self.sid, status="awaiting_manual_apply")
        tab = AuctionTab(self.db)
        try:
            tab.show()
            tab._active_auction_id = self.sid
            tab.refresh()
            with (
                patch.object(QMessageBox, "warning") as warning,
                patch.object(tab, "_sync_audio_owner_with_session") as audio,
                patch.object(self.db, "get_wheel_draw_info",
                             side_effect=AssertionError("draw accessed")),
            ):
                tab.run_wheel(confirm=False)
            warning.assert_called_once()
            audio.assert_not_called()
            self.assertEqual(self.db.get_auction_session(self.sid)["rng_ticket_id"], None)
            self.assertEqual(self.db.get_auction_session(self.sid)["rng_value"], None)
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
