"""UI-086 / P20-G: manual original-session lot creation or reuse after 00:00."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, Game
from streaming_manager.views.auction import AuctionTab


class LateNewLotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        paths = AppPaths.from_root(self.temp.name)
        paths.ensure_runtime_dirs()
        self.db = Database(paths.database_path)
        self.alpha = self.db.add_game(Game(None, "Alpha", None, 100, 0, "not_played", ""))
        self.beta = self.db.add_game(Game(None, "Beta", None, 90, 0, "not_played", ""))
        self.gamma = self.db.add_game(Game(None, "Gamma", None, 80, 0, "not_played", ""))
        self.now = "2026-10-20T02:00:00+00:00"

    def source(self, *, tie=False):
        with self.db.connect() as conn:
            sid = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,remaining_ms,remaining_seconds,deadline_at"
                ") VALUES(?,?,?,?,?,?,?,?)",
                ("P20-G", "max_amount", "local", self.now, "running", 0, 0, self.now),
            ).lastrowid)
            for gid, points in ((self.alpha, 100), (self.beta, 100 if tie else 90)):
                conn.execute(
                    "INSERT INTO auction_entries("
                    "auction_id,game_id,weight,active,starting_sm_points,bid_sm_points,"
                    "snapshot_title,snapshot_status) "
                    "SELECT ?,?,?,1,?,0,title,status FROM games WHERE id=?",
                    (sid, gid, points, points, gid),
                )
        self.db.finish_auction(sid)
        return sid

    def snapshot(self, sid):
        with self.db.connect() as conn:
            session = dict(conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?", (sid,),
            ).fetchone())
            entries = [dict(r) for r in conn.execute(
                "SELECT * FROM auction_entries WHERE auction_id=? ORDER BY id",
                (sid,),
            )]
            games = [dict(r) for r in conn.execute(
                "SELECT id,title,sm_points,auction_only,archived FROM games ORDER BY id",
            )]
            contributions = int(conn.execute(
                "SELECT COUNT(*) FROM contributions",
            ).fetchone()[0])
        return session, entries, games, contributions

    def test_new_temporary_lot_changes_leader_and_preserves_expired_timer(self):
        sid = self.source()
        before = self.snapshot(sid)
        result = self.db.add_post_expiry_manual_lot(sid, "Brand New", 115)
        self.assertTrue(result["created"])
        self.assertTrue(result["temporary"])
        self.assertFalse(result["merged"])
        after = self.snapshot(sid)
        self.assertEqual(after[0]["winner_game_id"], result["game_id"])
        self.assertEqual(after[0]["status"], "winner_selected")
        for key in ("remaining_ms", "remaining_seconds", "deadline_at", "finished_at"):
            self.assertEqual(before[0][key], after[0][key])
        self.assertEqual(after[3], before[3] + 1)
        with self.db.connect() as conn:
            g = conn.execute(
                "SELECT auction_only,sm_points FROM games WHERE id=?",
                (result["game_id"],),
            ).fetchone()
            entry = conn.execute(
                "SELECT starting_sm_points,bid_sm_points,weight FROM auction_entries "
                "WHERE auction_id=? AND game_id=?", (sid, result["game_id"]),
            ).fetchone()
            log = conn.execute(
                "SELECT action,after_json FROM change_log "
                "WHERE entity_type='auction_lot' ORDER BY id DESC LIMIT 1",
            ).fetchone()
        self.assertEqual(int(g["auction_only"]), 1)
        self.assertEqual(int(g["sm_points"]), 115)
        self.assertEqual(entry["starting_sm_points"], 0)
        self.assertEqual(entry["bid_sm_points"], 115)
        self.assertEqual(entry["weight"], 115)
        self.assertEqual(log["action"], "post_expiry_create")
        self.assertTrue(json.loads(log["after_json"])["no_timer_restart"])

    def test_existing_surviving_title_merges_without_duplicate_or_clock_reset(self):
        sid = self.source()
        before = self.snapshot(sid)
        result = self.db.add_post_expiry_manual_lot(sid, "  bEtA  ", 20)
        self.assertFalse(result["created"])
        self.assertTrue(result["merged"])
        self.assertEqual(result["game_id"], self.beta)
        after = self.snapshot(sid)
        self.assertEqual(len(after[1]), len(before[1]))
        self.assertEqual(len(after[2]), len(before[2]))
        self.assertEqual(after[0]["winner_game_id"], self.beta)
        self.assertEqual(after[3], before[3] + 1)
        self.assertEqual(before[0]["finished_at"], after[0]["finished_at"])
        self.assertEqual(after[0]["remaining_ms"], 0)
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT action FROM change_log "
                "WHERE entity_type='auction_lot' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        self.assertEqual(row["action"], "post_expiry_merge")

    def test_attaches_existing_regular_game_from_outside_snapshot_without_duplicate(self):
        sid = self.source(tie=True)
        before = self.snapshot(sid)
        result = self.db.add_post_expiry_manual_lot(sid, "Gamma", 30)
        self.assertEqual(result["game_id"], self.gamma)
        self.assertTrue(result["created"])  # new SESSION lot, existing regular game
        self.assertFalse(result["temporary"])
        after = self.snapshot(sid)
        self.assertEqual(len(after[2]), len(before[2]))
        self.assertEqual(after[0]["winner_game_id"], self.gamma)
        self.assertEqual(after[0]["status"], "winner_selected")
        self.assertEqual(after[3], before[3] + 1)
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT starting_sm_points,bid_sm_points FROM auction_entries "
                "WHERE auction_id=? AND game_id=?", (sid, self.gamma),
            ).fetchone()
        self.assertEqual(int(row["starting_sm_points"]), 80)
        self.assertEqual(int(row["bid_sm_points"]), 30)

    def test_zero_points_new_lot_allowed_without_creating_false_contribution(self):
        sid = self.source()
        before = self.snapshot(sid)
        result = self.db.add_post_expiry_manual_lot(sid, "Zero Lot", 0)
        after = self.snapshot(sid)
        self.assertTrue(result["temporary"])
        self.assertEqual(after[3], before[3])
        self.assertEqual(after[0]["winner_game_id"], self.alpha)
        self.assertEqual(after[0]["remaining_ms"], 0)
        self.assertEqual(len(after[1]), len(before[1]) + 1)

    def test_removed_archived_and_invalid_title_never_resurrect(self):
        sid = self.source()
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_entries SET result='removed',active=0 "
                "WHERE auction_id=? AND game_id=?", (sid, self.beta),
            )
            conn.execute(
                "UPDATE games SET archived=1 WHERE id=?", (self.gamma,),
            )
        before = self.snapshot(sid)
        with self.assertRaisesRegex(RuntimeError, "Удалённый"):
            self.db.add_post_expiry_manual_lot(sid, "Beta", 20)
        with self.assertRaises(RuntimeError):
            self.db.add_post_expiry_manual_lot(sid, "Gamma", 10)
        with self.assertRaises(ValueError):
            self.db.add_post_expiry_manual_lot(sid, "  ", 10)
        with self.assertRaises(ValueError):
            self.db.add_post_expiry_manual_lot(sid, "New", -1)
        self.assertEqual(before, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_entries SET game_id=NULL "
                "WHERE auction_id=? AND snapshot_title='Beta'", (sid,),
            )
        before_null = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.add_post_expiry_manual_lot(sid, "Beta", 20)
        self.assertEqual(before_null, self.snapshot(sid))

    def test_closed_wheel_or_unrelated_auction_cannot_be_touched(self):
        sid = self.source()
        other = self.source()
        old_other = self.snapshot(other)
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET status='awaiting_wheel' WHERE id=?",
                (sid,),
            )
        before = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.add_post_expiry_manual_lot(sid, "Late", 10)
        self.assertEqual(before, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET status='confirmed' WHERE id=?",
                (sid,),
            )
        before = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.add_post_expiry_manual_lot(sid, "Late", 10)
        self.assertEqual(before, self.snapshot(sid))
        self.assertEqual(old_other, self.snapshot(other))

    def test_qt_post_expiry_new_lot_and_close_gate(self):
        sid = self.source()
        tab = AuctionTab(self.db)
        try:
            tab.show()
            tab._active_auction_id = sid
            tab.refresh()
            self.assertTrue(tab.new_lot_widget.isVisible())
            self.assertTrue(tab.new_lot_btn.isEnabled())
            self.assertTrue(tab.add_bid_btn.isEnabled())
            self.assertTrue(tab.decrease_bid_btn.isEnabled())
            tab.new_lot_title.setText("Qt Late")
            tab.new_lot_points.setValue(115)
            tab.add_new_auction_lot()
            session = self.db.get_auction_session(sid)
            self.assertEqual(session["status"], "winner_selected")
            self.assertEqual(session["remaining_ms"], 0)
            with self.db.connect() as conn:
                row = conn.execute(
                    "SELECT g.id,ae.bid_sm_points FROM auction_entries ae "
                    "JOIN games g ON g.id=ae.game_id "
                    "WHERE ae.auction_id=? AND g.title='Qt Late'", (sid,),
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row["bid_sm_points"], 115)
                conn.execute(
                    "UPDATE auction_sessions SET status='confirmed' WHERE id=?",
                    (sid,),
                )
            tab.refresh()
            self.assertFalse(tab.new_lot_btn.isEnabled())
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
