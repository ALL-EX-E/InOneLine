"""P20-I: exclude a permanent lot after 00:00 without deleting the game."""
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


class LatePermanentExclusionTests(unittest.TestCase):
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
        self.now = "2026-10-20T04:00:00+00:00"

    def source(self, *, tie=False, gamma=True):
        with self.db.connect() as conn:
            sid = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,remaining_ms,remaining_seconds,deadline_at"
                ") VALUES(?,?,?,?,?,?,?,?)",
                ("P20-I", "max_amount", "local", self.now, "running", 0, 0, self.now),
            ).lastrowid)
            entries = [(self.alpha, 100), (self.beta, 100 if tie else 90)]
            if gamma:
                entries.append((self.gamma, 80))
            for gid, val in entries:
                conn.execute(
                    "INSERT INTO auction_entries("
                    "auction_id,game_id,weight,active,starting_sm_points,bid_sm_points,"
                    "snapshot_title,snapshot_status) "
                    "SELECT ?,?,?,1,?,0,title,status FROM games WHERE id=?",
                    (sid, gid, val, val, gid),
                )
        self.db.finish_auction(sid)
        return sid

    def snapshot(self, sid):
        with self.db.connect() as conn:
            session = dict(conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?", (sid,)
            ).fetchone())
            entries = [dict(row) for row in conn.execute(
                "SELECT * FROM auction_entries WHERE auction_id=? ORDER BY id",
                (sid,),
            )]
            counts = (
                int(conn.execute("SELECT COUNT(*) FROM contributions").fetchone()[0]),
                int(conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]),
            )
        return session, entries, counts

    def test_exclude_permanent_winner_preserves_games_contributions_and_clock(self):
        sid = self.source()
        self.db.add_post_expiry_manual_bid(sid, self.beta, 15)
        self.assertEqual(self.db.get_auction_session(sid)["winner_game_id"], self.beta)
        before = self.snapshot(sid)
        game_before = self.db.get_game(self.beta)
        result = self.db.exclude_post_expiry_permanent_auction_lot(sid, self.beta)
        after = self.snapshot(sid)
        self.assertEqual(result["game_id"], self.beta)
        self.assertEqual(after[0]["winner_game_id"], self.alpha)
        self.assertEqual(after[0]["status"], "winner_selected")
        for key in ("remaining_ms", "remaining_seconds", "deadline_at", "finished_at"):
            self.assertEqual(before[0][key], after[0][key])
        self.assertEqual(after[2], before[2])
        self.assertEqual(self.db.get_game(self.beta).sm_points, game_before.sm_points)
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT active,result,game_id,starting_sm_points,bid_sm_points "
                "FROM auction_entries WHERE id=?", (result["entry_id"],)
            ).fetchone()
            log = conn.execute(
                "SELECT action,after_json FROM change_log "
                "WHERE entity_type='auction_lot' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        self.assertEqual(row["game_id"], self.beta)
        self.assertEqual(row["result"], "removed")
        self.assertEqual(row["active"], 0)
        self.assertEqual(row["bid_sm_points"], 15)
        self.assertEqual(log["action"], "post_expiry_permanent_exclude")
        self.assertTrue(json.loads(log["after_json"])["game_preserved"])
        self.assertTrue(json.loads(log["after_json"])["contributions_preserved"])
        with self.assertRaises(RuntimeError):
            self.db.add_post_expiry_manual_lot(sid, "Beta", 5)

    def test_exclude_inactive_nonleader_then_winner_recomputes_tie(self):
        sid = self.source(tie=True)
        before = self.snapshot(sid)
        self.assertEqual(before[0]["status"], "tie_break_required")
        self.assertIn(self.gamma, {
            x["game_id"] for x in self.db.list_provisional_max_amount_entries(sid)
        })
        self.db.exclude_post_expiry_permanent_auction_lot(sid, self.gamma)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "tie_break_required")
        self.assertEqual({x["game_id"] for x in self.db.list_auction_entries(sid)},
                         {self.alpha, self.beta})
        self.db.exclude_post_expiry_permanent_auction_lot(sid, self.alpha)
        session = self.db.get_auction_session(sid)
        self.assertEqual(session["status"], "winner_selected")
        self.assertEqual(session["winner_game_id"], self.beta)
        self.assertEqual(self.db.get_game(self.gamma).sm_points, 80)
        self.assertNotIn(self.gamma, {
            x["game_id"] for x in self.db.list_provisional_max_amount_entries(sid)
        })

    def test_frozen_confirmed_wrong_session_archived_and_temporary_immutable(self):
        sid = self.source()
        stranger = self.db.add_game(Game(None, "Stranger", None, 70, 0, "not_played", ""))
        before = self.snapshot(sid)
        with self.assertRaises(ValueError):
            self.db.exclude_post_expiry_permanent_auction_lot(sid, stranger)
        with self.assertRaises(ValueError):
            self.db.exclude_post_expiry_permanent_auction_lot(sid, -1)
        self.assertEqual(before, self.snapshot(sid))
        temporary = self.db.add_post_expiry_manual_lot(sid, "Tmp", 5)["game_id"]
        before = self.snapshot(sid)
        with self.assertRaisesRegex(ValueError, "Временный"):
            self.db.exclude_post_expiry_permanent_auction_lot(sid, temporary)
        self.assertEqual(before, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute("UPDATE games SET archived=1 WHERE id=?", (self.alpha,))
        before = self.snapshot(sid)
        with self.assertRaises(ValueError):
            self.db.exclude_post_expiry_permanent_auction_lot(sid, self.alpha)
        self.assertEqual(before, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute("UPDATE auction_sessions SET status='awaiting_wheel' WHERE id=?", (sid,))
        before = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.exclude_post_expiry_permanent_auction_lot(sid, self.beta)
        self.assertEqual(before, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute("UPDATE auction_sessions SET status='confirmed' WHERE id=?", (sid,))
        before = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.exclude_post_expiry_permanent_auction_lot(sid, self.beta)
        self.assertEqual(before, self.snapshot(sid))

    def test_last_lot_not_excluded_and_no_other_session_changes(self):
        sid = self.source()
        other = self.source()
        unrelated_before = self.snapshot(other)
        self.db.exclude_post_expiry_permanent_auction_lot(sid, self.alpha)
        self.db.exclude_post_expiry_permanent_auction_lot(sid, self.gamma)
        before = self.snapshot(sid)
        with self.assertRaisesRegex(RuntimeError, "последний"):
            self.db.exclude_post_expiry_permanent_auction_lot(sid, self.beta)
        self.assertEqual(self.snapshot(sid), before)
        self.assertEqual(self.snapshot(other), unrelated_before)
        self.assertEqual(self.db.get_game(self.beta).sm_points, 90)

    def test_unresolved_source_auction_pending_is_guarded(self):
        sid = self.source()
        before = self.snapshot(sid)
        with patch.object(
            self.db, "_require_auction_conversions_resolved_conn",
            side_effect=RuntimeError("Ожидающие поступления исходного аукциона"),
        ):
            with self.assertRaisesRegex(RuntimeError, "Ожидающие"):
                self.db.exclude_post_expiry_permanent_auction_lot(sid, self.alpha)
        self.assertEqual(before, self.snapshot(sid))

    def test_qt_action_excludes_permanent_after_expiry_with_confirmation(self):
        sid = self.source()
        tab = AuctionTab(self.db)
        try:
            tab.show()
            tab._active_auction_id = sid
            tab.refresh()
            tab.select_conduct_game_id(self.alpha)
            self.app.processEvents()
            tab._update_delete_lot_action_state()
            self.assertTrue(tab.delete_lot_btn.isEnabled())
            self.assertEqual(tab.delete_lot_btn.text(), "Исключить лот")
            with patch.object(QMessageBox, "warning", return_value=QMessageBox.No):
                tab.delete_temporary_lot()
            self.assertEqual(self.db.get_auction_session(sid)["winner_game_id"], self.alpha)
            with patch.object(QMessageBox, "warning", return_value=QMessageBox.Yes):
                tab.delete_temporary_lot()
            self.assertEqual(self.db.get_auction_session(sid)["winner_game_id"], self.beta)
            self.assertEqual(self.db.get_auction_session(sid)["remaining_ms"], 0)
            self.assertIsNotNone(self.db.get_game(self.alpha))
            with self.db.connect() as conn:
                conn.execute(
                    "UPDATE auction_sessions SET status='confirmed' WHERE id=?",
                    (sid,),
                )
            tab.refresh()
            self.assertFalse(tab.delete_lot_btn.isEnabled())
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
