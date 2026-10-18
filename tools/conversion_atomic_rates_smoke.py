"""P19-B / UI-085: all-or-nothing conversion rates and pending states."""
from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QMessageBox

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.conversion import ConversionUnit
from streaming_manager.database import Database
from streaming_manager.db.services import ServicesMixin
from streaming_manager.views.settings import SettingsTab


class AtomicConversionRateTests(unittest.TestCase):
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

    def unit(self, key):
        return ConversionUnit(key, key, kind="currency")

    def add_pending(self, unit, status):
        with self.db.connect() as conn:
            c = conn.execute(
                "INSERT INTO external_events("
                "source,external_event_id,event_type,payload_json,processing_status,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("test", f"{unit}-{status}", "donation", "{}", status,
                 "2026-10-18T10:00:00+00:00"),
            )
            conn.execute(
                "INSERT INTO pending_conversions("
                "external_event_row_id,source_amount_text,source_unit,"
                "source_unit_label,unit_kind,status,created_at"
                ") VALUES(?,?,?,?,?,?,?)",
                (c.lastrowid, "5", unit, unit, "currency", status,
                 "2026-10-18T10:00:00+00:00"),
            )

    def pending_statuses(self):
        with self.db.connect() as conn:
            return (
                [tuple(r) for r in conn.execute(
                    "SELECT source_unit,status FROM pending_conversions ORDER BY id"
                )],
                [tuple(r) for r in conn.execute(
                    "SELECT external_event_id,processing_status FROM external_events ORDER BY id"
                )],
            )

    def audit_rows(self):
        with self.db.connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM change_log").fetchone()[0]

    def test_all_fields_validated_before_any_mutation(self):
        self.db.set_conversion_rate("RUB", "2")
        self.add_pending("PLN", "awaiting_rate")
        before = self.pending_statuses(), self.audit_rows()
        with self.assertRaises(ValueError):
            self.db.set_conversion_rates_atomic([
                (self.unit("RUB"), "9"), (self.unit("PLN"), "not-a-rate")
            ])
        self.assertEqual(self.db.get_conversion_rate("RUB"), "2")
        self.assertEqual(self.db.get_conversion_rate("PLN"), "")
        self.assertEqual((self.pending_statuses(), self.audit_rows()), before)

    def test_atomic_success_updates_both_pending_directions_without_credit(self):
        self.db.set_conversion_rate("EUR", "3")
        self.add_pending("PLN", "awaiting_rate")
        self.add_pending("EUR", "awaiting_manual_apply")
        result = self.db.set_conversion_rates_atomic([
            (self.unit("RUB"), ""),
            (self.unit("PLN"), "0,25"),
            (self.unit("EUR"), ""),
        ])
        self.assertEqual(result, {"RUB": "1", "PLN": "0.25", "EUR": ""})
        self.assertEqual(self.db.get_conversion_rate("RUB"), "1")
        self.assertEqual(self.db.get_conversion_rate("PLN"), "0.25")
        self.assertEqual(self.db.get_conversion_rate("EUR"), "")
        pending, events = self.pending_statuses()
        self.assertEqual(pending, [
            ("PLN", "awaiting_manual_apply"), ("EUR", "awaiting_rate")
        ])
        self.assertEqual(events, [
            ("PLN-awaiting_rate", "awaiting_manual_apply"),
            ("EUR-awaiting_manual_apply", "awaiting_rate"),
        ])
        with self.db.connect() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM contributions").fetchone()[0], 0)

    def test_late_sql_error_rolls_back_rates_units_pending_and_audit(self):
        self.db.set_conversion_rate("RUB", "2")
        self.add_pending("PLN", "awaiting_rate")
        previous = self.pending_statuses(), self.audit_rows()
        real = ServicesMixin._register_conversion_unit_conn

        def fail_second(conn, descriptor):
            if descriptor.normalized_unit() == "PLN":
                raise sqlite3.OperationalError("Injected second-row DB failure")
            return real(conn, descriptor)

        with patch.object(ServicesMixin, "_register_conversion_unit_conn", side_effect=fail_second):
            with self.assertRaises(sqlite3.OperationalError):
                self.db.set_conversion_rates_atomic([
                    (self.unit("RUB"), "5"), (self.unit("PLN"), "2")
                ])
        self.assertEqual(self.db.get_conversion_rate("RUB"), "2")
        self.assertEqual(self.db.get_conversion_rate("PLN"), "")
        self.assertEqual((self.pending_statuses(), self.audit_rows()), previous)

    def test_validation_blocks_duplicates_and_nonpositive_values(self):
        for rows in (
            [(self.unit("RUB"), "4"), (self.unit("rub"), "5")],
            [(self.unit("RUB"), "4"), (self.unit("PLN"), "0")],
            [(self.unit("RUB"), "4"), (self.unit("PLN"), "-1")],
            [(self.unit("RUB"), "4"), (self.unit("PLN"), 0)],
        ):
            with self.assertRaises(ValueError):
                self.db.set_conversion_rates_atomic(rows)
        self.assertEqual(self.db.get_conversion_rate("RUB"), "1")
        self.assertEqual(self.db.get_conversion_rate("PLN"), "")

    def test_user_interface_preserves_all_text_on_error_and_recovers(self):
        self.db.register_conversion_unit("PLN", label="PLN", kind="currency")
        tab = SettingsTab(self.db, self.paths, LocalApiServer(self.db))
        try:
            tab.conversion_rate_edits["RUB"].setText("7")
            tab.conversion_rate_edits["PLN"].setText("invalid")
            with patch.object(QMessageBox, "warning", return_value=QMessageBox.Ok) as warning:
                tab.save_conversion_settings()
            warning.assert_called_once()
            self.assertEqual(tab.conversion_rate_edits["RUB"].text(), "7")
            self.assertEqual(tab.conversion_rate_edits["PLN"].text(), "invalid")
            self.assertEqual(self.db.get_conversion_rate("RUB"), "1")
            self.assertEqual(self.db.get_conversion_rate("PLN"), "")
            tab.conversion_rate_edits["PLN"].setText("2,5")
            with patch.object(QMessageBox, "information", return_value=QMessageBox.Ok):
                tab.save_conversion_settings()
            self.assertEqual(self.db.get_conversion_rate("RUB"), "7")
            self.assertEqual(self.db.get_conversion_rate("PLN"), "2.5")
        finally:
            tab.thread_pool.waitForDone(5000)
            tab.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
