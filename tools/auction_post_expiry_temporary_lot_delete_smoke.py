"""P20-H: after-00:00 deletion of original auction's temporary lots only."""
from __future__ import annotations

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


class LateTemporaryDeleteTests(unittest.TestCase):
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
        self.time = "2026-10-20T03:00:00+00:00"

    def source(self, *, tie=False):
        with self.db.connect() as conn:
            sid = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,remaining_ms,remaining_seconds,deadline_at"
                ") VALUES(?,?,?,?,?,?,?,?)",
                ("P20-H", "max_amount", "local", self.time, "running", 0, 0, self.time),
            ).lastrowid)
            for gid, score in ((self.alpha, 100), (self.beta, 100 if tie else 90)):
                conn.execute(
                    "INSERT INTO auction_entries("
                    "auction_id,game_id,weight,active,starting_sm_points,bid_sm_points,"
                    "snapshot_title,snapshot_status) "
                    "SELECT ?,?,?,1,?,0,title,status FROM games WHERE id=?",
                    (sid, gid, score, score, gid),
                )
        self.db.finish_auction(sid)
        return sid

    def snapshot(self, sid):
        with self.db.connect() as conn:
            session = dict(conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?", (sid,)
            ).fetchone())
            entries = [dict(r) for r in conn.execute(
                "SELECT * FROM auction_entries WHERE auction_id=? ORDER BY id",
                (sid,),
            )]
            contrib_count = int(conn.execute(
                "SELECT COUNT(*) FROM contributions"
            ).fetchone()[0])
        return session, entries, contrib_count

    def test_delete_late_temp_recomputes_leader_and_never_restarts_timer(self):
        sid = self.source()
        lot = self.db.add_post_expiry_manual_lot(sid, "Tmp New", 115)
        game_id = lot["game_id"]
        before = self.snapshot(sid)
        self.assertEqual(before[0]["winner_game_id"], game_id)
        result = self.db.delete_temporary_auction_lot(sid, game_id)
        after = self.snapshot(sid)
        self.assertEqual(result["game_id"], game_id)
        self.assertEqual(result["removed_contributions"], 1)
        self.assertEqual(after[0]["winner_game_id"], self.alpha)
        self.assertEqual(after[0]["status"], "winner_selected")
        for key in ("remaining_ms", "remaining_seconds", "deadline_at", "finished_at"):
            self.assertEqual(before[0][key], after[0][key])
        self.assertEqual(after[2], before[2] - 1)
        with self.db.connect() as conn:
            tomb = conn.execute(
                "SELECT game_id,result,active,snapshot_title "
                "FROM auction_entries WHERE id=?", (result["entry_id"],),
            ).fetchone()
            game = conn.execute(
                "SELECT id FROM games WHERE id=?", (game_id,)
            ).fetchone()
            changelog = conn.execute(
                "SELECT action,after_json FROM change_log "
                "WHERE entity_type='auction_session' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        self.assertIsNone(tomb["game_id"])
        self.assertEqual(tomb["result"], "removed")
        self.assertEqual(int(tomb["active"]), 0)
        self.assertEqual(tomb["snapshot_title"], "Tmp New")
        self.assertIsNone(game)
        self.assertEqual(changelog["action"], "post_expiry_temporary_lot_delete")
        with self.assertRaises(RuntimeError):
            self.db.add_post_expiry_manual_lot(sid, "Tmp New", 10)

    def test_inactive_temp_from_tie_can_be_deleted_and_tie_preserved(self):
        sid = self.source(tie=True)
        lot = self.db.add_post_expiry_manual_lot(sid, "Tmp Low", 20)
        game_id = lot["game_id"]
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT active FROM auction_entries WHERE auction_id=? AND game_id=?",
                (sid, game_id),
            ).fetchone()
        self.assertEqual(int(row["active"]), 0)
        self.assertIn(game_id, {
            x["game_id"] for x in self.db.list_provisional_max_amount_entries(sid)
        })
        self.db.delete_temporary_auction_lot(sid, game_id)
        session = self.db.get_auction_session(sid)
        self.assertEqual(session["status"], "tie_break_required")
        self.assertIsNone(session["winner_game_id"])
        self.assertEqual({x["game_id"] for x in self.db.list_auction_entries(sid)},
                         {self.alpha, self.beta})

    def test_regular_removed_lots_and_confirmed_or_frozen_sessions_blocked(self):
        sid = self.source()
        tmp = self.db.add_post_expiry_manual_lot(sid, "Tmp", 1)["game_id"]
        before = self.snapshot(sid)
        with self.assertRaises(ValueError):
            self.db.delete_temporary_auction_lot(sid, self.alpha)
        self.assertEqual(before, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_entries SET result='removed',active=0 "
                "WHERE auction_id=? AND game_id=?", (sid, tmp),
            )
        before = self.snapshot(sid)
        with self.assertRaises(ValueError):
            self.db.delete_temporary_auction_lot(sid, tmp)
        self.assertEqual(before, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET status='awaiting_wheel' WHERE id=?", (sid,),
            )
        before = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.delete_temporary_auction_lot(sid, tmp)
        self.assertEqual(before, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET status='confirmed' WHERE id=?", (sid,),
            )
        before = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.delete_temporary_auction_lot(sid, tmp)
        self.assertEqual(before, self.snapshot(sid))

    def test_external_credit_and_other_session_reference_blocked_atomically(self):
        sid = self.source()
        tmp = self.db.add_post_expiry_manual_lot(sid, "Tmp", 10)["game_id"]
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO contributions(game_id,source,points,unit,note,created_at,"
                "credited_sm_points) VALUES(?,?,?,?,?,?,?)",
                (tmp, "twitch", 1, "SM", "paid", self.time, 1),
            )
        before = self.snapshot(sid)
        with self.assertRaisesRegex(RuntimeError, "внешние"):
            self.db.delete_temporary_auction_lot(sid, tmp)
        self.assertEqual(before, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute(
                "DELETE FROM contributions WHERE game_id=? AND source='twitch'", (tmp,),
            )
            foreign = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,remaining_ms,remaining_seconds"
                ") VALUES(?,?,?,?,?,?,?)",
                ("Other", "max_amount", "local", self.time, "running", 0, 0),
            ).lastrowid)
            conn.execute(
                "INSERT INTO auction_entries("
                "auction_id,game_id,weight,active,starting_sm_points,bid_sm_points,"
                "snapshot_title,snapshot_status) "
                "SELECT ?,?,?,1,?,0,title,status FROM games WHERE id=?",
                (foreign, tmp, 10, 10, tmp),
            )
        before = self.snapshot(sid)
        with self.assertRaisesRegex(RuntimeError, "другим аукционом"):
            self.db.delete_temporary_auction_lot(sid, tmp)
        self.assertEqual(before, self.snapshot(sid))

    def test_last_temporary_lot_not_removed_to_unrecoverable_empty_result(self):
        sid = self.source()
        tmp = self.db.add_post_expiry_manual_lot(sid, "Last Tmp", 120)["game_id"]
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_entries SET active=0,result='removed' "
                "WHERE auction_id=? AND game_id IN (?,?)",
                (sid, self.alpha, self.beta),
            )
        before = self.snapshot(sid)
        with self.assertRaisesRegex(RuntimeError, "последний"):
            self.db.delete_temporary_auction_lot(sid, tmp)
        self.assertEqual(before, self.snapshot(sid))

    def test_qt_delete_after_expiry_confirmed_and_protected_after_freeze(self):
        sid = self.source()
        tmp = self.db.add_post_expiry_manual_lot(sid, "Qt Temporary", 115)["game_id"]
        tab = AuctionTab(self.db)
        try:
            tab.show()
            tab._active_auction_id = sid
            tab.refresh()
            tab.select_conduct_game_id(tmp)
            self.app.processEvents()
            tab._update_delete_lot_action_state()
            self.assertTrue(tab.delete_lot_btn.isEnabled())
            with patch.object(QMessageBox, "warning", return_value=QMessageBox.Yes):
                tab.delete_temporary_lot()
            self.assertEqual(self.db.get_auction_session(sid)["winner_game_id"], self.alpha)
            self.assertEqual(self.db.get_auction_session(sid)["remaining_ms"], 0)
            self.assertIsNone(self.db.get_game(tmp))
            again = self.db.add_post_expiry_manual_lot(sid, "Other Qt", 105)["game_id"]
            tab.refresh()
            tab.select_conduct_game_id(again)
            self.app.processEvents()
            self.assertTrue(tab.delete_lot_btn.isEnabled())
            with self.db.connect() as conn:
                conn.execute(
                    "UPDATE auction_sessions SET status='confirmed' WHERE id=?", (sid,),
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
