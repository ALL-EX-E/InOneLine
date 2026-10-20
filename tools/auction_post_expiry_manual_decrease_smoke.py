"""P20-F: bounded 00:00 manual subtraction before Max Amount confirmation."""
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


class PostExpiryManualDecreaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        paths = AppPaths.from_root(self.temp.name)
        paths.ensure_runtime_dirs()
        self.db = Database(paths.database_path)
        self.alpha = self.db.add_game(
            Game(None, "Alpha", None, 100, 0, "not_played", "")
        )
        self.beta = self.db.add_game(
            Game(None, "Beta", None, 90, 0, "not_played", "")
        )
        self.gamma = self.db.add_game(
            Game(None, "Gamma", None, 80, 0, "not_played", "")
        )
        self.now = "2026-10-19T11:00:00+00:00"

    def source(self, *, tie=False):
        with self.db.connect() as conn:
            sid = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,remaining_ms,remaining_seconds,deadline_at"
                ") VALUES(?,?,?,?,?,?,?,?)",
                ("P20-F", "max_amount", "local", self.now, "running", 0, 0, self.now),
            ).lastrowid)
            for gid, points in (
                (self.alpha, 100),
                (self.beta, 100 if tie else 90),
                (self.gamma, 80),
            ):
                conn.execute(
                    "INSERT INTO auction_entries("
                    "auction_id,game_id,weight,active,starting_sm_points,bid_sm_points,"
                    "snapshot_title,snapshot_status) "
                    "SELECT ?,?,?,1,?,0,title,status FROM games WHERE id=?",
                    (sid, gid, points, points, gid),
                )
        self.db.finish_auction(sid)
        self.assertEqual(self.db.get_auction_session(sid)["remaining_ms"], 0)
        return sid

    def snapshot(self, auction_id):
        with self.db.connect() as conn:
            session = dict(conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?", (auction_id,),
            ).fetchone())
            entries = [dict(x) for x in conn.execute(
                "SELECT * FROM auction_entries WHERE auction_id=? ORDER BY id",
                (auction_id,),
            )]
            contributions = int(conn.execute(
                "SELECT COUNT(*) FROM contributions"
            ).fetchone()[0])
        return session, entries, contributions

    def test_decrease_recalculates_provisional_leader_and_preserves_zero_clock(self):
        sid = self.source()
        self.db.add_post_expiry_manual_bid(sid, self.beta, 15)
        before = self.snapshot(sid)
        self.assertEqual(before[0]["winner_game_id"], self.beta)
        self.db.decrease_post_expiry_manual_bid(sid, self.beta, 10)
        after = self.snapshot(sid)
        self.assertEqual(after[0]["winner_game_id"], self.alpha)
        self.assertEqual(after[0]["status"], "winner_selected")
        self.assertEqual(self.db.get_game(self.beta).sm_points, 95)
        self.assertEqual(after[2], before[2])  # no negative contribution
        for k in ("finished_at", "remaining_ms", "remaining_seconds", "deadline_at"):
            self.assertEqual(before[0][k], after[0][k])
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT action,after_json FROM change_log "
                "WHERE entity_type='auction_bid' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        self.assertEqual(row["action"], "post_expiry_decrease")
        audit = json.loads(row["after_json"])
        self.assertTrue(audit["no_timer_restart"])
        self.assertEqual(audit["decreased_sm_points"], 10)
        self.assertEqual(audit["bid_sm_points"], 5)

    def test_tie_and_surviving_inactive_lot_recalculate_after_decrease(self):
        sid = self.source(tie=True)
        self.db.add_post_expiry_manual_bid(sid, self.gamma, 25)
        self.assertEqual(self.db.get_auction_session(sid)["winner_game_id"], self.gamma)
        self.db.decrease_post_expiry_manual_bid(sid, self.gamma, 5)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "tie_break_required")
        self.assertEqual(
            {x["game_id"] for x in self.db.list_auction_entries(sid)},
            {self.alpha, self.beta, self.gamma},
        )
        self.db.decrease_post_expiry_manual_bid(sid, self.gamma, 5)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "tie_break_required")
        self.assertEqual(
            {x["game_id"] for x in self.db.list_auction_entries(sid)},
            {self.alpha, self.beta},
        )
        self.assertEqual(
            {x["game_id"] for x in self.db.list_provisional_max_amount_entries(sid)},
            {self.alpha, self.beta, self.gamma},
        )

    def test_lower_bound_and_nonpositive_input_roll_back_atomically(self):
        sid = self.source()
        self.db.add_post_expiry_manual_bid(sid, self.beta, 5)
        before = self.snapshot(sid)
        before_game = self.db.get_game(self.beta).sm_points
        with self.assertRaisesRegex(ValueError, "максимум"):
            self.db.decrease_post_expiry_manual_bid(sid, self.beta, 6)
        with self.assertRaisesRegex(ValueError, "больше нуля"):
            self.db.decrease_post_expiry_manual_bid(sid, self.beta, 0)
        self.assertEqual(before, self.snapshot(sid))
        self.assertEqual(before_game, self.db.get_game(self.beta).sm_points)
        self.db.decrease_post_expiry_manual_bid(sid, self.beta, 5)
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT starting_sm_points,bid_sm_points FROM auction_entries "
                "WHERE auction_id=? AND game_id=?", (sid, self.beta),
            ).fetchone()
        self.assertEqual(row["bid_sm_points"], 0)
        self.assertEqual(self.db.get_game(self.beta).sm_points, before_game - 5)

    def test_foreign_removed_archived_and_frozen_are_immutable(self):
        sid = self.source()
        self.db.add_post_expiry_manual_bid(sid, self.beta, 10)
        foreign = self.db.add_game(
            Game(None, "Foreign", None, 20, 0, "not_played", "")
        )
        old = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.decrease_post_expiry_manual_bid(sid, foreign, 1)
        self.assertEqual(old, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute("UPDATE games SET archived=1 WHERE id=?", (self.beta,))
        old = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.decrease_post_expiry_manual_bid(sid, self.beta, 1)
        self.assertEqual(old, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute("UPDATE games SET archived=0 WHERE id=?", (self.beta,))
            conn.execute(
                "UPDATE auction_entries SET result='removed',active=0 "
                "WHERE auction_id=? AND game_id=?", (sid, self.beta),
            )
        old = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.decrease_post_expiry_manual_bid(sid, self.beta, 1)
        self.assertEqual(old, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET status='awaiting_wheel' WHERE id=?",
                (sid,),
            )
        old = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.decrease_post_expiry_manual_bid(sid, self.beta, 1)
        self.assertEqual(old, self.snapshot(sid))

    def test_real_qt_decrease_button_and_result_gate(self):
        sid = self.source()
        self.db.add_post_expiry_manual_bid(sid, self.beta, 15)
        tab = AuctionTab(self.db)
        try:
            tab.show()
            tab._active_auction_id = sid
            tab.refresh()
            self.assertTrue(tab.add_bid_btn.isEnabled())
            self.assertTrue(tab.decrease_bid_btn.isEnabled())
            # P20-G extends the provisional editor with guarded new-title reuse.
            self.assertTrue(tab.new_lot_btn.isEnabled())
            tab.select_conduct_game_id(self.beta)
            tab.bid_amount.setValue(10)
            tab.decrease_manual_bid()
            self.assertEqual(self.db.get_auction_session(sid)["winner_game_id"], self.alpha)
            self.assertEqual(self.db.get_auction_session(sid)["remaining_ms"], 0)
            with self.db.connect() as conn:
                conn.execute(
                    "UPDATE auction_sessions SET status='confirmed' WHERE id=?",
                    (sid,),
                )
            tab.refresh()
            self.assertFalse(tab.decrease_bid_btn.isEnabled())
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
