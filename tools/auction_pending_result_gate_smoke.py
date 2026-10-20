"""UI-086 P20-A: unresolved source-auction warning and irreversible result guards."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QMessageBox, QTableWidget, QTabWidget, QWidget

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, Game
from streaming_manager.views.auction import AuctionTab
from streaming_manager.views.main_window import MainWindow


class AuctionUnresolvedGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.temp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.db.add_game(Game(None, "Проверочный лот", None, 50, 0, "not_played", ""))
        with self.db.connect() as conn:
            self.game_id = int(conn.execute(
                "SELECT id FROM games WHERE title='Проверочный лот'"
            ).fetchone()["id"])
        self.now = "2026-10-19T09:35:00+00:00"

    def tearDown(self):
        self.temp.cleanup()

    def session(self, status="running"):
        with self.db.connect() as conn:
            sid = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,winner_game_id"
                ") VALUES(?,?,?,?,?,?)",
                ("Проверочный аукцион", "max_amount", "local", self.now,
                 status, self.game_id if status == "winner_selected" else None),
            ).lastrowid)
        return sid

    def live_running_session(self):
        """Use a future deadline; a zero-duration running fixture auto-expires in Qt."""
        sid = self.session("running")
        deadline = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET deadline_at=?, remaining_seconds=?, "
                "remaining_ms=? WHERE id=?",
                (deadline, 300, 300_000, sid),
            )
        return sid

    def pending(self, auction_id, event_id="source-pending", status="awaiting_rate"):
        with self.db.connect() as conn:
            event_row_id = int(conn.execute(
                "INSERT INTO external_events("
                "source,external_event_id,event_type,payload_json,"
                "processing_status,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("test", event_id, "donation",
                 json.dumps({"normalized": {"lot_title": "Проверочный лот"}},
                            ensure_ascii=False), status, self.now),
            ).lastrowid)
            pid = int(conn.execute(
                "INSERT INTO pending_conversions("
                "external_event_row_id,game_id,auction_id,source_amount_text,"
                "source_unit,source_unit_label,unit_kind,status,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,?)",
                (event_row_id, self.game_id, auction_id, "3", "PLN", "PLN",
                 "currency", status, self.now),
            ).lastrowid)
        return pid

    def count_contributions(self):
        with self.db.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM contributions").fetchone()[0])

    def test_count_is_scoped_to_source_session_and_waiting_status(self):
        first = self.session()
        second = self.session()
        self.pending(first, "waiting-first")
        self.pending(first, "ready-first", "awaiting_manual_apply")
        self.pending(second, "waiting-second")
        self.pending(None, "outside-session")
        self.assertEqual(self.db.count_unresolved_auction_conversions(first), 2)
        self.assertEqual(self.db.count_unresolved_auction_conversions(second), 1)
        self.assertEqual(self.db.count_unresolved_auction_conversions(first + second + 99), 0)
        self.assertEqual(self.count_contributions(), 0)

    def test_database_rejects_confirm_without_mutation_and_allows_after_decline(self):
        sid = self.session("winner_selected")
        pid = self.pending(sid)
        with self.assertRaisesRegex(RuntimeError, "необработанные поступления"):
            self.db.confirm_auction_winner(sid)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "winner_selected")
        self.assertEqual(self.db.get_game(self.game_id).status, "not_played")
        self.assertEqual(self.count_contributions(), 0)
        self.db.reject_pending_conversion_event(pid)
        self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 0)
        self.assertEqual(self.db.confirm_auction_winner(sid), self.game_id)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "confirmed")

    def test_tie_wheel_blocked_until_this_source_session_resolved(self):
        sid = self.session("tie_break_required")
        another = self.session("running")
        self.pending(another, "other-session")
        self.db.start_auction_tie_wheel(sid, wheel_duration_ms=1000)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "awaiting_wheel")
        with self.db.connect() as conn:
            conn.execute("UPDATE auction_sessions SET status='tie_break_required' WHERE id=?", (sid,))
        pid = self.pending(sid)
        with self.assertRaisesRegex(RuntimeError, "необработанные поступления"):
            self.db.start_auction_tie_wheel(sid, wheel_duration_ms=1000)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "tie_break_required")
        self.db.reject_pending_conversion_event(pid)
        self.db.start_auction_tie_wheel(sid, wheel_duration_ms=1000)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "awaiting_wheel")
        self.assertEqual(self.db.count_unresolved_auction_conversions(another), 1)

    def test_auction_warning_and_buttons_update_after_no_apply(self):
        sid = self.session("winner_selected")
        pid = self.pending(sid)
        tab = AuctionTab(self.db)
        try:
            tab.show()
            tab._active_auction_id = sid
            tab.refresh()
            self.assertFalse(tab.auction_pending_conversion_warning.isHidden())
            self.assertIn("1", tab.auction_pending_conversion_warning.text())
            self.assertIn("Конвертация", tab.auction_pending_conversion_warning.text())
            self.assertFalse(tab.confirm_btn.isEnabled())
            self.assertIn("ожидающие", tab.confirm_btn.toolTip())
            self.db.reject_pending_conversion_event(pid)
            tab.refresh()
            self.assertTrue(tab.auction_pending_conversion_warning.isHidden())
            self.assertTrue(tab.confirm_btn.isEnabled())
            self.assertEqual(self.count_contributions(), 0)
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()

    def test_timer_finishing_does_not_auto_decline_or_credit(self):
        sid = self.session("running")
        pid = self.pending(sid)
        # P20-A is a result gate, not a rewrite of timer transition.
        result = self.db.finish_auction(sid)
        self.assertEqual(result["status"], "finished_no_winner")
        self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 1)
        self.assertEqual(self.db.get_pending_conversion_event(pid)["status"], "awaiting_rate")
        self.assertEqual(self.count_contributions(), 0)


    # P20-L: only the approved pending-event warning for full-auction stop.
    # The existing cancel_auction operation, session status and point policy
    # must remain exactly as before; nothing auto-applies or auto-declines.
    def test_cancel_auction_with_own_pending_no_keeps_db_and_default_no(self):
        sid = self.session("winner_selected")
        pid = self.pending(sid, "pending-own")
        other = self.session()
        self.pending(other, "pending-other")
        self.pending(None, "pending-outside")
        tab = AuctionTab(self.db)
        try:
            tab._active_auction_id = sid
            with patch.object(
                QMessageBox, "warning", return_value=QMessageBox.No
            ) as confirm:
                tab.cancel_auction()
            confirm.assert_called_once()
            args = confirm.call_args.args
            self.assertIn("Необработанные поступления", args[2])
            self.assertIn("этого аукциона: 1", args[2])
            self.assertIn("НЕ применит и НЕ отклонит", args[2])
            self.assertIn("Настройки → Конвертация", args[2])
            self.assertEqual(args[-1], QMessageBox.No)
            self.assertEqual(self.db.get_auction_session(sid)["status"], "winner_selected")
            self.assertEqual(self.db.get_pending_conversion_event(pid)["status"], "awaiting_rate")
            self.assertEqual(self.count_contributions(), 0)
            self.assertEqual(self.db.count_unresolved_auction_conversions(other), 1)
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()

    def test_cancel_auction_with_own_pending_yes_preserves_pending_without_credit(self):
        sid = self.live_running_session()
        pid = self.pending(sid, "pending-cancel-yes")
        tab = AuctionTab(self.db)
        try:
            tab._active_auction_id = sid
            with patch.object(
                QMessageBox, "warning", return_value=QMessageBox.Yes
            ) as confirm:
                tab.cancel_auction()
            confirm.assert_called_once()
            self.assertIn("Необработанные поступления", confirm.call_args.args[2])
            self.assertEqual(self.db.get_auction_session(sid)["status"], "cancelled")
            self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 1)
            self.assertEqual(self.db.get_pending_conversion_event(pid)["status"], "awaiting_rate")
            self.assertEqual(self.count_contributions(), 0)
            self.assertEqual(self.db.get_game(self.game_id).sm_points, 50)
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()

    def test_cancel_auction_without_own_pending_keeps_original_warning(self):
        sid = self.session()
        other = self.session()
        self.pending(other, "only-other")
        self.pending(None, "only-outside")
        tab = AuctionTab(self.db)
        try:
            tab._active_auction_id = sid
            with patch.object(
                QMessageBox, "warning", return_value=QMessageBox.No
            ) as confirm:
                tab.cancel_auction()
            confirm.assert_called_once()
            message = confirm.call_args.args[2]
            self.assertIn("Остановить текущую сессию", message)
            self.assertNotIn("Необработанные поступления", message)
            self.assertEqual(self.db.get_auction_session(sid)["status"], "running")
            self.assertEqual(self.db.count_unresolved_auction_conversions(other), 1)
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()

    def test_cancel_auction_pending_count_error_aborts_before_confirmation(self):
        sid = self.live_running_session()
        tab = AuctionTab(self.db)
        try:
            tab._active_auction_id = sid
            with patch.object(
                self.db, "count_unresolved_auction_conversions",
                side_effect=RuntimeError("read failed")
            ), patch.object(QMessageBox, "critical") as error_dialog, patch.object(
                QMessageBox, "warning"
            ) as confirm:
                tab.cancel_auction()
            error_dialog.assert_called_once()
            confirm.assert_not_called()
            self.assertEqual(self.db.get_auction_session(sid)["status"], "running")
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()


    # P20-M UI-086: reuse the approved visible warning and Settings conversion
    # page, never create a second pending queue or a background rate save.
    def test_conversion_jump_only_with_source_pending_and_no_data_mutation(self):
        sid = self.session("winner_selected")
        other = self.session("running")
        self.pending(other, "other-jump")
        jump = MagicMock()
        tab = AuctionTab(self.db, open_conversion=jump)
        try:
            tab.show()
            tab._active_auction_id = sid
            tab.refresh()
            self.assertTrue(tab.auction_pending_conversion_warning.isHidden())
            self.assertTrue(tab.auction_pending_conversion_jump_btn.isHidden())
            pending_id = self.pending(sid, "own-jump")
            tab.refresh()
            self.assertFalse(tab.auction_pending_conversion_warning.isHidden())
            self.assertFalse(tab.auction_pending_conversion_jump_btn.isHidden())
            self.assertEqual(
                tab.auction_pending_conversion_jump_btn.text(),
                "Перейти к конвертации",
            )
            tab.auction_pending_conversion_jump_btn.click()
            jump.assert_called_once_with()
            self.assertEqual(self.db.get_pending_conversion_event(pending_id)["status"], "awaiting_rate")
            self.assertEqual(self.count_contributions(), 0)
            self.db.reject_pending_conversion_event(pending_id)
            tab.refresh()
            self.assertTrue(tab.auction_pending_conversion_jump_btn.isHidden())
            self.assertEqual(self.db.count_unresolved_auction_conversions(other), 1)
        finally:
            tab.auction_timer.stop()
            tab.close()
            tab.deleteLater()
            self.app.processEvents()

    def test_conversion_jump_main_window_routes_existing_settings_page(self):
        # The real MainWindow method is exercised without starting a second
        # streaming server, OBS/Chromium instance or a duplicate Settings tab.
        container = QTabWidget()
        old_page = QWidget()
        conversion_page = QWidget()
        container.addTab(old_page, "Интеграции")
        container.addTab(conversion_page, "Конвертация")
        queue = QTableWidget()
        refresh_pending = MagicMock()
        settings = SimpleNamespace(
            settings_tabs=container, conversion_page=conversion_page,
            pending_conversion_table=queue,
            _refresh_pending_conversion_rows=refresh_pending,
        )
        target = SimpleNamespace(
            settings_tab=settings, _set_current_main_page=MagicMock()
        )
        try:
            MainWindow.open_conversion_settings(target)
            target._set_current_main_page.assert_called_once_with(settings)
            self.assertIs(container.currentWidget(), conversion_page)
            refresh_pending.assert_called_once_with()
            self.assertEqual(container.count(), 2)
        finally:
            container.deleteLater()
            queue.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
