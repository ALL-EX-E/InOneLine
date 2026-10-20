"""P20-J: rename one temporary original Max Amount lot after 00:00."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QMessageBox
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, Game
from streaming_manager.views.auction import AuctionTab


class LateTemporaryRenameTests(unittest.TestCase):
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
        self.now = "2026-10-20T17:00:00+00:00"

    def source(self, *, tie=False):
        with self.db.connect() as conn:
            sid = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,remaining_ms,remaining_seconds,deadline_at"
                ") VALUES(?,?,?,?,?,?,?,?)",
                ("P20-J", "max_amount", "local", self.now, "running", 0, 0, self.now),
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
            entries = [dict(row) for row in conn.execute(
                "SELECT * FROM auction_entries WHERE auction_id=? ORDER BY id",
                (sid,),
            )]
            contributions = [dict(row) for row in conn.execute(
                "SELECT * FROM contributions ORDER BY id"
            )]
            games = [dict(row) for row in conn.execute(
                "SELECT id,title,sm_points,auction_only,archived FROM games ORDER BY id"
            )]
        return session, entries, contributions, games

    def test_rename_winning_temporary_lot_keeps_points_history_and_zero_clock(self):
        sid = self.source()
        tmp = self.db.add_post_expiry_manual_lot(sid, "Temp One", 115)["game_id"]
        before = self.snapshot(sid)
        self.assertEqual(before[0]["winner_game_id"], tmp)
        result = self.db.rename_post_expiry_temporary_lot(sid, tmp, "Renamed One")
        after = self.snapshot(sid)
        self.assertEqual(result["old_title"], "Temp One")
        self.assertEqual(result["title"], "Renamed One")
        self.assertEqual(after[0], before[0])
        self.assertEqual(after[2], before[2])
        self.assertEqual(len(after[1]), len(before[1]))
        self.assertEqual(self.db.get_game(tmp).sm_points, 115)
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT snapshot_title,bid_sm_points,starting_sm_points "
                "FROM auction_entries WHERE auction_id=? AND game_id=?",
                (sid, tmp),
            ).fetchone()
            log = conn.execute(
                "SELECT action,before_json,after_json FROM change_log "
                "WHERE entity_type='auction_lot' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        self.assertEqual(row["snapshot_title"], "Renamed One")
        self.assertEqual(row["bid_sm_points"], 115)
        self.assertEqual(row["starting_sm_points"], 0)
        self.assertEqual(self.db.get_game(tmp).title, "Renamed One")
        self.assertEqual(log["action"], "post_expiry_temporary_rename")
        self.assertEqual(json.loads(log["before_json"])["old_title"], "Temp One")
        self.assertTrue(json.loads(log["after_json"])["no_timer_restart"])

    def test_inactive_nonleader_in_tie_renames_without_changing_tie(self):
        sid = self.source(tie=True)
        tmp = self.db.add_post_expiry_manual_lot(sid, "Low Temp", 20)["game_id"]
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT active FROM auction_entries WHERE auction_id=? AND game_id=?",
                (sid, tmp),
            ).fetchone()
        self.assertEqual(row["active"], 0)
        before = self.snapshot(sid)
        self.db.rename_post_expiry_temporary_lot(sid, tmp, "Low Changed")
        after = self.snapshot(sid)
        self.assertEqual(after[0], before[0])
        self.assertEqual(after[0]["status"], "tie_break_required")
        self.assertIsNone(after[0]["winner_game_id"])
        self.assertEqual(after[2], before[2])
        self.assertEqual({
            row["title"] for row in self.db.list_provisional_max_amount_entries(sid)
            if row["game_id"] == tmp
        }, {"Low Changed"})

    def test_duplicate_main_archived_temporary_and_deleted_titles_are_rejected(self):
        sid = self.source()
        tmp = self.db.add_post_expiry_manual_lot(sid, "Temporary", 30)["game_id"]
        other = self.db.add_post_expiry_manual_lot(sid, "Other Temp", 5)["game_id"]
        archived = self.db.add_game(
            Game(None, "Archived Name", None, 0, 0, "not_played", "")
        )
        with self.db.connect() as conn:
            conn.execute("UPDATE games SET archived=1 WHERE id=?", (archived,))
        before = self.snapshot(sid)
        for title in ("Alpha", "Other Temp", "Archived Name", "Temporary"):
            with self.subTest(title=title):
                with self.assertRaises(ValueError):
                    self.db.rename_post_expiry_temporary_lot(sid, tmp, title)
                self.assertEqual(self.snapshot(sid), before)
        # Already excluded permanent title stays unavailable even though
        # its game and historical entry remain in the source auction.
        self.db.exclude_post_expiry_permanent_auction_lot(sid, self.beta)
        before = self.snapshot(sid)
        with self.assertRaises(ValueError):
            self.db.rename_post_expiry_temporary_lot(sid, tmp, "Beta")
        self.assertEqual(self.snapshot(sid), before)
        self.assertIsNotNone(self.db.get_game(other))

    def test_permanent_foreign_removed_and_confirmed_or_wheel_are_immutable(self):
        sid = self.source()
        tmp = self.db.add_post_expiry_manual_lot(sid, "Temporary", 30)["game_id"]
        foreign = self.db.add_game(
            Game(None, "Foreign", None, 8, 0, "not_played", "")
        )
        before = self.snapshot(sid)
        for game_id in (self.alpha, foreign, -1):
            with self.subTest(game_id=game_id):
                with self.assertRaises((RuntimeError, ValueError)):
                    self.db.rename_post_expiry_temporary_lot(sid, game_id, "New")
                self.assertEqual(self.snapshot(sid), before)
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_entries SET result='removed',active=0 "
                "WHERE auction_id=? AND game_id=?", (sid, tmp),
            )
        before = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.rename_post_expiry_temporary_lot(sid, tmp, "New")
        self.assertEqual(self.snapshot(sid), before)
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET status='awaiting_wheel' WHERE id=?", (sid,),
            )
        before = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.rename_post_expiry_temporary_lot(sid, tmp, "New")
        self.assertEqual(self.snapshot(sid), before)
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET status='confirmed' WHERE id=?", (sid,),
            )
        before = self.snapshot(sid)
        with self.assertRaises(RuntimeError):
            self.db.rename_post_expiry_temporary_lot(sid, tmp, "New")
        self.assertEqual(self.snapshot(sid), before)

    def test_other_session_external_contributions_and_pending_are_guarded(self):
        sid = self.source()
        tmp = self.db.add_post_expiry_manual_lot(sid, "Temporary", 30)["game_id"]
        with patch.object(
            self.db, "_require_auction_conversions_resolved_conn",
            side_effect=RuntimeError("Ожидающие поступления"),
        ):
            before = self.snapshot(sid)
            with self.assertRaisesRegex(RuntimeError, "Ожидающие"):
                self.db.rename_post_expiry_temporary_lot(sid, tmp, "New")
            self.assertEqual(before, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO contributions(game_id,source,points,unit,note,created_at,"
                "credited_sm_points) VALUES(?,?,?,?,?,?,?)",
                (tmp, "twitch", 1, "SM", "external", self.now, 1),
            )
        before = self.snapshot(sid)
        with self.assertRaisesRegex(RuntimeError, "внешние"):
            self.db.rename_post_expiry_temporary_lot(sid, tmp, "New")
        self.assertEqual(before, self.snapshot(sid))
        with self.db.connect() as conn:
            conn.execute(
                "DELETE FROM contributions WHERE game_id=? AND source='twitch'", (tmp,),
            )
            other = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,remaining_ms,remaining_seconds"
                ") VALUES(?,?,?,?,?,?,?)",
                ("Other", "max_amount", "local", self.now, "running", 0, 0),
            ).lastrowid)
            conn.execute(
                "INSERT INTO auction_entries("
                "auction_id,game_id,weight,active,starting_sm_points,bid_sm_points,"
                "snapshot_title,snapshot_status) "
                "SELECT ?,?,?,1,?,0,title,status FROM games WHERE id=?",
                (other, tmp, 30, 30, tmp),
            )
        before = self.snapshot(sid)
        with self.assertRaisesRegex(RuntimeError, "другим аукционом"):
            self.db.rename_post_expiry_temporary_lot(sid, tmp, "New")
        self.assertEqual(before, self.snapshot(sid))

    def test_qt_modal_edit_selected_temporary_then_freeze(self):
        sid = self.source()
        tmp = self.db.add_post_expiry_manual_lot(sid, "Temp Qt", 110)["game_id"]
        tab = AuctionTab(self.db)
        try:
            tab.show()
            tab._active_auction_id = sid
            tab.refresh()
            tab.select_conduct_game_id(tmp)
            self.app.processEvents()
            self.assertTrue(tab.rename_lot_btn.isEnabled())
            self.assertTrue(tab.rename_lot_btn.isVisible())
            self.assertFalse(hasattr(tab, "rename_lot_widget"))
            self.assertFalse(hasattr(tab, "rename_lot_title"))
            self.assertIs(
                tab.rename_lot_btn.parentWidget(), tab.bid_widget
            )

            def fill_dialog(dialog):
                current = dialog.findChild(
                    QLineEdit, "auction_rename_current_title"
                )
                editor = dialog.findChild(
                    QLineEdit, "auction_rename_new_title"
                )
                self.assertIsNotNone(current)
                self.assertTrue(current.isReadOnly())
                self.assertEqual(current.text(), "Temp Qt")
                self.assertEqual(editor.text(), "Temp Qt")
                editor.setText("Edited Qt")
                return QDialog.DialogCode.Accepted

            with patch.object(QDialog, "exec", new=fill_dialog):
                with patch.object(
                    QMessageBox, "question", return_value=QMessageBox.Yes
                ) as question:
                    tab.rename_temporary_lot()
            self.assertEqual(question.call_count, 1)
            self.assertEqual(
                question.call_args.args[-1], QMessageBox.No
            )
            self.assertEqual(self.db.get_game(tmp).title, "Edited Qt")
            self.assertEqual(self.db.get_auction_session(sid)["remaining_ms"], 0)
            tab.select_conduct_game_id(self.alpha)
            self.app.processEvents()
            self.assertFalse(tab.rename_lot_btn.isVisible())
            with self.db.connect() as conn:
                conn.execute(
                    "UPDATE auction_sessions SET status='confirmed' WHERE id=?",
                    (sid,),
                )
            tab.refresh()
            tab.select_conduct_game_id(tmp)
            self.app.processEvents()
            self.assertFalse(tab.rename_lot_btn.isEnabled())
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()

    def test_qt_modal_cancel_or_no_confirmation_never_writes(self):
        sid = self.source()
        tmp = self.db.add_post_expiry_manual_lot(sid, "Keep Name", 111)["game_id"]
        tab = AuctionTab(self.db)
        try:
            tab.show()
            tab._active_auction_id = sid
            tab.refresh()
            tab.select_conduct_game_id(tmp)
            self.app.processEvents()
            before = self.snapshot(sid)
            with patch.object(
                QDialog, "exec", return_value=QDialog.DialogCode.Rejected
            ):
                with patch.object(QMessageBox, "question") as question:
                    tab.rename_temporary_lot()
            question.assert_not_called()
            self.assertEqual(self.snapshot(sid), before)

            def changed(dialog):
                dialog.findChild(
                    QLineEdit, "auction_rename_new_title"
                ).setText("Do Not Apply")
                return QDialog.DialogCode.Accepted

            with patch.object(QDialog, "exec", new=changed):
                with patch.object(
                    QMessageBox, "question", return_value=QMessageBox.No
                ) as question:
                    tab.rename_temporary_lot()
            question.assert_called_once()
            self.assertEqual(self.snapshot(sid), before)
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
