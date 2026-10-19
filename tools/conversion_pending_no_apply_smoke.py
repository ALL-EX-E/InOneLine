"""P19-E / UI-085: explicit no-credit rejection with durable provenance."""
from __future__ import annotations

import json
import sqlite3
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.views.settings import SettingsTab


class NoApplyPendingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)

    def tearDown(self):
        self.tmp.cleanup()

    def add_pending(self, event_id="manual-no-apply", *, status="awaiting_rate",
                    auction_id=None, game_id=None):
        now = "2026-10-19T08:00:00+00:00"
        payload = json.dumps({"normalized": {"lot_title": "Новая игра"}},
                             ensure_ascii=False)
        with self.db.connect() as conn:
            external_id = int(conn.execute(
                "INSERT INTO external_events("
                "source,external_event_id,event_type,payload_json,processing_status,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("test", event_id, "donation", payload, status, now),
            ).lastrowid)
            pending_id = int(conn.execute(
                "INSERT INTO pending_conversions("
                "external_event_row_id,game_id,auction_id,source_amount_text,"
                "source_unit,source_unit_label,unit_kind,contributor,note,status,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (external_id, game_id, auction_id, "4", "PLN", "PLN", "currency",
                 "Проверочный донор", "Примечание", status, now),
            ).lastrowid)
        return pending_id, external_id

    def state(self):
        with self.db.connect() as conn:
            counts = {
                table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in ("games", "contributions", "auction_entries",
                              "external_events", "pending_conversions")
            }
            raw = conn.execute(
                "SELECT processing_status,processed_at,payload_json "
                "FROM external_events ORDER BY id LIMIT 1"
            ).fetchone()
            pending = conn.execute(
                "SELECT status,applied_at,credited_sm_points "
                "FROM pending_conversions ORDER BY id LIMIT 1"
            ).fetchone()
            audits = conn.execute(
                "SELECT action,before_json,after_json FROM change_log "
                "WHERE action='reject_pending' ORDER BY id"
            ).fetchall()
        return counts, raw, pending, audits

    def test_no_rate_needed_and_durable_no_credit_with_audit(self):
        pending_id, ext_id = self.add_pending()
        self.assertFalse(self.db.get_pending_conversion_event(pending_id)["can_apply"])
        result = self.db.reject_pending_conversion_event(pending_id)
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(result["external_event_id"], "manual-no-apply")
        self.assertEqual(result["reason"], "operator_no_apply")
        self.assertEqual(self.db.list_pending_conversion_events(), [])
        counts, raw, pending, audits = self.state()
        self.assertEqual(counts["games"], 0)
        self.assertEqual(counts["contributions"], 0)
        self.assertEqual(counts["external_events"], 1)
        self.assertEqual(counts["pending_conversions"], 1)
        self.assertEqual(raw["processing_status"], "cancelled")
        self.assertIsNotNone(raw["processed_at"])
        self.assertIn("Новая игра", raw["payload_json"])
        self.assertEqual(pending["status"], "cancelled")
        self.assertIsNone(pending["applied_at"])
        self.assertIsNone(pending["credited_sm_points"])
        self.assertEqual(len(audits), 1)
        self.assertEqual(audits[0]["action"], "reject_pending")
        before = json.loads(audits[0]["before_json"])
        after = json.loads(audits[0]["after_json"])
        for field in ("pending_id", "source", "external_event_id", "game_id", "auction_id"):
            self.assertIn(field, after)
        self.assertEqual(before["status"], "awaiting_rate")
        self.assertEqual(after["status"], "cancelled")
        self.assertEqual(after["reason"], "operator_no_apply")
        self.assertEqual(after["external_event_id"], "manual-no-apply")
        self.assertEqual(after["source"], "test")

    def test_later_rate_save_and_replayed_provider_id_never_resurrect(self):
        pending_id, _ = self.add_pending()
        self.db.reject_pending_conversion_event(pending_id)
        self.db.set_conversion_rate("PLN", "3")
        row = self.db.get_pending_conversion_event(pending_id)
        self.assertEqual(row["status"], "cancelled")
        with self.assertRaises(RuntimeError):
            self.db.apply_pending_conversion_event(pending_id)
        with self.assertRaises(RuntimeError):
            self.db.reject_pending_conversion_event(pending_id)
        # Real incoming events require an enabled connected provider.
        # Reproduce that lifecycle before simulating a provider replay.
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO integration_connections("
                "service_key,enabled,status,created_at,updated_at"
                ") VALUES(?,?,?,?,?)",
                ("test", 1, "connected", "2026-10-19T08:00:00+00:00",
                 "2026-10-19T08:00:00+00:00"),
            )
        duplicate = self.db.process_normalized_integration_event(
            service_key="test", external_event_id="manual-no-apply",
            event_type="donation", source_amount="4", source_unit="PLN",
            contributor="Проверочный донор", lot_title="Новая игра",
        )
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(duplicate["status"], "cancelled")
        self.assertEqual(self.state()[0]["contributions"], 0)
        self.assertEqual(len(self.state()[3]), 1)

    def test_atomic_rejection_rolls_back_on_external_event_update_fault(self):
        pending_id, _ = self.add_pending()
        with self.db.connect() as conn:
            conn.execute(
                "CREATE TRIGGER reject_fault BEFORE UPDATE OF processing_status "
                "ON external_events BEGIN SELECT RAISE(ABORT,'reject fault'); END"
            )
        with self.assertRaises(sqlite3.DatabaseError):
            self.db.reject_pending_conversion_event(pending_id)
        counts, raw, pending, audits = self.state()
        self.assertEqual(pending["status"], "awaiting_rate")
        self.assertEqual(raw["processing_status"], "awaiting_rate")
        self.assertEqual(len(audits), 0)
        self.assertEqual(counts["games"], 0)
        self.assertEqual(counts["contributions"], 0)

    def test_ui_cancel_does_nothing_and_yes_clears_queue(self):
        pid, _ = self.add_pending()
        tab = SettingsTab(self.db, self.paths, LocalApiServer(self.db))
        try:
            table = tab.pending_conversion_table
            self.assertEqual(table.columnCount(), 8)
            self.assertEqual(table.rowCount(), 1)
            self.assertIsInstance(table.cellWidget(0, 6), QPushButton)
            self.assertFalse(table.cellWidget(0, 6).isEnabled())
            reject = table.cellWidget(0, 7)
            self.assertIsInstance(reject, QPushButton)
            self.assertEqual(reject.text(), "Не применять")
            self.assertTrue(reject.isEnabled())
            with patch.object(QMessageBox, "question", return_value=QMessageBox.No) as dialog:
                reject.click()
            self.assertIn("manual-no-apply", dialog.call_args.args[2])
            self.assertEqual(self.db.get_pending_conversion_event(pid)["status"], "awaiting_rate")
            self.assertEqual(tab.pending_conversion_table.rowCount(), 1)
            with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes), \
                 patch.object(QMessageBox, "information"):
                tab.pending_conversion_table.cellWidget(0, 7).click()
            self.assertEqual(tab.pending_conversion_table.rowCount(), 0)
            self.assertEqual(self.db.get_pending_conversion_event(pid)["status"], "cancelled")
            self.assertEqual(self.state()[0]["contributions"], 0)
        finally:
            tab.thread_pool.waitForDone(5000)
            tab.deleteLater()
            self.app.processEvents()

    def test_no_apply_preserves_source_auction_data(self):
        now = "2026-10-19T08:00:00+00:00"
        with self.db.connect() as conn:
            auction_id = int(conn.execute(
                "INSERT INTO auction_sessions(name,mode,provider,created_at,status) "
                "VALUES(?,?,?,?,?)",
                ("Session", "max_amount", "local", now, "running"),
            ).lastrowid)
        pid, _ = self.add_pending(event_id="auction-no-apply", auction_id=auction_id)
        with self.db.connect() as conn:
            before = dict(conn.execute("SELECT * FROM auction_sessions WHERE id=?",
                                       (auction_id,)).fetchone())
        self.db.reject_pending_conversion_event(pid)
        with self.db.connect() as conn:
            after = dict(conn.execute("SELECT * FROM auction_sessions WHERE id=?",
                                      (auction_id,)).fetchone())
        self.assertEqual(before, after)
        self.assertEqual(self.state()[0]["auction_entries"], 0)
        self.assertEqual(self.db.get_pending_conversion_event(pid)["auction_id"], auction_id)


if __name__ == "__main__":
    unittest.main()
