"""P20-E: manually correct surviving Max Amount lot after 00:00, before freeze."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, Game
from streaming_manager.views.auction import AuctionTab


class ProvisionalLateManualBidTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        paths = AppPaths.from_root(self.tmp.name)
        paths.ensure_runtime_dirs()
        self.db = Database(paths.database_path)
        self.alpha = self.db.add_game(Game(None, "Alpha", None, 100, 0, "not_played", ""))
        self.beta = self.db.add_game(Game(None, "Beta", None, 90, 0, "not_played", ""))
        self.gamma = self.db.add_game(Game(None, "Gamma", None, 80, 0, "not_played", ""))
        self.now = "2026-10-19T09:00:00+00:00"

    def source(self, *, tie=False):
        with self.db.connect() as conn:
            sid = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,remaining_ms,remaining_seconds,deadline_at"
                ") VALUES(?,?,?,?,?,?,?,?)",
                ("P20-E", "max_amount", "local", self.now, "running", 0, 0, self.now),
            ).lastrowid)
            for gid, score in (
                (self.alpha, 100),
                (self.beta, 100 if tie else 90),
                (self.gamma, 80),
            ):
                conn.execute(
                    "INSERT INTO auction_entries("
                    "auction_id,game_id,weight,active,starting_sm_points,bid_sm_points,"
                    "snapshot_title,snapshot_status) "
                    "SELECT ?,?,?,1,?,0,title,status FROM games WHERE id=?",
                    (sid, gid, score, score, gid),
                )
        result = self.db.finish_auction(sid)
        self.assertEqual(
            result["status"], "tie_break_required" if tie else "winner_selected"
        )
        return sid

    def snapshot(self, sid):
        with self.db.connect() as conn:
            session = dict(conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?", (sid,)
            ).fetchone())
            entries = [dict(x) for x in conn.execute(
                "SELECT * FROM auction_entries WHERE auction_id=? ORDER BY id", (sid,)
            ).fetchall()]
            contribution_count = int(conn.execute(
                "SELECT COUNT(*) FROM contributions"
            ).fetchone()[0])
            return session, entries, contribution_count

    def test_late_bid_changes_winner_but_never_restores_expired_timer(self):
        sid = self.source()
        before = self.snapshot(sid)
        self.db.add_post_expiry_manual_bid(sid, self.beta, 15)
        after = self.snapshot(sid)
        self.assertEqual(after[0]["status"], "winner_selected")
        self.assertEqual(after[0]["winner_game_id"], self.beta)
        self.assertEqual(self.db.get_game(self.beta).sm_points, 105)
        self.assertEqual(after[2], before[2] + 1)
        for field in ("finished_at", "remaining_ms", "remaining_seconds", "deadline_at"):
            self.assertEqual(before[0][field], after[0][field])
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT action,after_json FROM change_log "
                "WHERE entity_type='auction_bid' ORDER BY id DESC LIMIT 1"
            ).fetchone()
            self.assertEqual(row["action"], "post_expiry_add")
            self.assertIn('"no_timer_restart": true', row["after_json"])

    def test_tie_and_inactive_nonleader_can_be_recalculated_without_new_lot(self):
        sid = self.source(tie=True)
        self.assertEqual(len(self.db.list_auction_entries(sid)), 2)
        visible = self.db.list_provisional_max_amount_entries(sid)
        self.assertEqual({x["game_id"] for x in visible},
                         {self.alpha, self.beta, self.gamma})
        self.db.add_post_expiry_manual_bid(sid, self.gamma, 25)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "winner_selected")
        self.assertEqual(self.db.get_auction_session(sid)["winner_game_id"], self.gamma)
        self.assertEqual(len(self.db.list_auction_entries(sid)), 3)
        self.db.add_post_expiry_manual_bid(sid, self.alpha, 5)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "tie_break_required")
        self.assertEqual(
            {x["game_id"] for x in self.db.list_auction_entries(sid)},
            {self.alpha, self.gamma},
        )
        self.assertEqual(len(self.db.list_provisional_max_amount_entries(sid)), 3)

    def test_confirmed_or_wheel_frozen_auction_cannot_be_changed(self):
        sid = self.source()
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET status='confirmed' WHERE id=?", (sid,)
            )
        before = self.snapshot(sid)
        with self.assertRaisesRegex(RuntimeError, "корректировка"):
            self.db.add_post_expiry_manual_bid(sid, self.beta, 15)
        self.assertEqual(before, self.snapshot(sid))

        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET status='awaiting_wheel' WHERE id=?", (sid,)
            )
        after = self.snapshot(sid)
        with self.assertRaisesRegex(RuntimeError, "корректировка"):
            self.db.add_post_expiry_manual_bid(sid, self.beta, 15)
        self.assertEqual(after, self.snapshot(sid))

    def test_archived_removed_foreign_and_zero_bid_blocked_atomically(self):
        sid = self.source()
        foreign = self.db.add_game(Game(None, "Foreign", None, 20, 0, "not_played", ""))
        before = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.add_post_expiry_manual_bid(sid, foreign, 10)
        with self.assertRaisesRegex(ValueError, "больше нуля"):
            self.db.add_post_expiry_manual_bid(sid, self.beta, 0)
        self.assertEqual(before, self.snapshot(sid))

        with self.db.connect() as conn:
            conn.execute("UPDATE games SET archived=1 WHERE id=?", (self.beta,))
        after_archive = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.add_post_expiry_manual_bid(sid, self.beta, 10)
        self.assertEqual(after_archive, self.snapshot(sid))

        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_entries SET result='removed',active=0 "
                "WHERE auction_id=? AND game_id=?", (sid, self.gamma),
            )
        after_removed = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.add_post_expiry_manual_bid(sid, self.gamma, 10)
        self.assertEqual(after_removed, self.snapshot(sid))
        self.assertNotIn(self.gamma, {
            x["game_id"] for x in self.db.list_provisional_max_amount_entries(sid)
        })

    def test_conduct_late_add_only_and_manual_action_use_existing_lot(self):
        sid = self.source(tie=True)
        tab = AuctionTab(self.db)
        try:
            tab.show()
            tab._active_auction_id = sid
            tab.refresh()
            self.assertTrue(tab.bid_widget.isVisible())
            self.assertTrue(tab.add_bid_btn.isEnabled())
            self.assertFalse(tab.decrease_bid_btn.isEnabled())
            self.assertFalse(tab.new_lot_btn.isEnabled())
            self.assertEqual(tab.conduct_table.rowCount(), 3)
            tab.select_conduct_game_id(self.gamma)
            self.assertEqual(tab.selected_conduct_game_id(), self.gamma)
            tab.bid_amount.setValue(25)
            tab.add_manual_bid()
            self.assertEqual(self.db.get_auction_session(sid)["winner_game_id"], self.gamma)
            self.assertEqual(self.db.get_auction_session(sid)["remaining_ms"], 0)
            self.assertEqual(self.db.get_game(self.gamma).sm_points, 105)
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
