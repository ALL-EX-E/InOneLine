"""P19-G / UI-085 #7.1: dynamic unknown source units and pending queue."""
from __future__ import annotations

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
from streaming_manager.views.settings import SettingsTab


class UnknownUnitPendingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.now = "2026-10-19T08:45:00+00:00"
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO integration_connections("
                "service_key,enabled,status,created_at,updated_at"
                ") VALUES(?,?,?,?,?)",
                ("test", 1, "connected", self.now, self.now),
            )

    def tearDown(self):
        self.tmp.cleanup()

    def incoming(self, event_id, unit, *, kind="currency", amount="2.5"):
        return self.db.process_normalized_integration_event(
            service_key="test",
            external_event_id=event_id,
            event_type="donation",
            source_amount=amount,
            source_unit=unit,
            source_unit_label=unit,
            unit_kind=kind,
            contributor="Тестовый донор",
            lot_title="Новый лот",
            force_outside_auction=True,
        )

    def view(self):
        # Deliberately don't announce new provider units via capabilities;
        # a real accepted event must still register its own service unit.
        return SettingsTab(
            self.db, self.paths, LocalApiServer(self.db),
            conversion_units_provider=lambda: [],
        )

    def close_view(self, tab):
        tab.thread_pool.waitForDone(5000)
        tab.deleteLater()
        self.app.processEvents()

    def counts(self):
        with self.db.connect() as conn:
            return tuple(int(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])
                         for name in ("external_events", "pending_conversions",
                                      "games", "contributions"))

    def test_unknown_currency_atomically_registers_and_queues_without_credit(self):
        original = self.incoming("new-currency-event", "XYZ")
        self.assertEqual(original["status"], "awaiting_rate")
        self.assertIsNotNone(original["pending_id"])
        self.assertEqual(self.counts(), (1, 1, 0, 0))
        registered = {u.unit: u for u in self.db.list_registered_conversion_units()}
        self.assertIn("XYZ", registered)
        self.assertEqual(registered["XYZ"].normalized_kind(), "currency")
        self.assertIn("XYZ", [u.unit for u in self.db.visible_conversion_units([])])
        pending = self.db.list_pending_conversion_events()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["source_unit"], "XYZ")
        self.assertEqual(pending[0]["game_title"], "Новый лот")
        self.assertFalse(pending[0]["can_apply"])
        tab = self.view()
        try:
            self.assertIn("XYZ", tab.conversion_rate_edits)
            self.assertEqual(tab.conversion_rate_edits["XYZ"].text(), "")
            self.assertEqual(tab.pending_conversion_table.item(0, 5).text(), "Курс не задан")
            self.assertFalse(tab.pending_conversion_table.cellWidget(0, 6).isEnabled())
        finally:
            self.close_view(tab)
        self.assertEqual(self.counts(), (1, 1, 0, 0))

    def test_unannounced_service_unit_appears_while_provider_connected(self):
        original = self.incoming("new-service-unit", "BONUS_STAR", kind="service")
        registered = {u.unit: u for u in self.db.list_registered_conversion_units()}
        self.assertEqual(registered["BONUS_STAR"].service, "test")
        self.assertEqual(registered["BONUS_STAR"].normalized_kind(), "service")
        self.assertIn("BONUS_STAR", [u.unit for u in self.db.visible_conversion_units([])])
        tab = self.view()
        try:
            self.assertIn("BONUS_STAR", tab.conversion_rate_edits)
            self.assertEqual(tab.conversion_rate_edits["BONUS_STAR"].text(), "")
            self.assertEqual(tab.pending_conversion_table.rowCount(), 1)
            self.assertEqual(tab.pending_conversion_table.item(0, 4).text(), "2.5 BONUS_STAR")
            tab.conversion_rate_edits["BONUS_STAR"].setText("1,5")
            with patch.object(QMessageBox, "information"):
                tab.save_conversion_settings()
            self.assertEqual(self.db.get_conversion_rate("BONUS_STAR"), "1.5")
            self.assertEqual(tab.pending_conversion_table.item(0, 5).text(), "4 баллов (× 1,5)")
            self.assertTrue(tab.pending_conversion_table.cellWidget(0, 6).isEnabled())
            self.assertEqual(self.db.get_pending_conversion_event(original["pending_id"])["status"],
                             "awaiting_manual_apply")
            self.assertEqual(self.counts(), (1, 1, 0, 0))
        finally:
            self.close_view(tab)

    def test_service_unit_hidden_on_disconnect_but_pending_and_saved_rate_remain(self):
        self.incoming("disconnected-unit", "BONUS_STAR", kind="service")
        self.db.set_conversion_rate("BONUS_STAR", "2", kind="service", service="test")
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE integration_connections SET enabled=0 WHERE service_key='test'"
            )
        self.assertNotIn("BONUS_STAR", [u.unit for u in self.db.visible_conversion_units([])])
        self.assertEqual(self.db.get_conversion_rate("BONUS_STAR"), "2")
        self.assertEqual(len(self.db.list_pending_conversion_events()), 1)
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE integration_connections SET enabled=1,status='connected' "
                "WHERE service_key='test'"
            )
        self.assertIn("BONUS_STAR", [u.unit for u in self.db.visible_conversion_units([])])
        self.assertEqual(self.counts(), (1, 1, 0, 0))

    def test_duplicate_unknown_unit_event_does_not_requeue_or_credit(self):
        original = self.incoming("duplicate-currency-event", "XYZ")
        duplicate = self.incoming("duplicate-currency-event", "XYZ")
        self.assertFalse(original["duplicate"])
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(original["pending_id"], duplicate["pending_id"])
        self.assertEqual(self.counts(), (1, 1, 0, 0))
        self.db.set_conversion_rate("XYZ", "2")
        duplicate2 = self.incoming("duplicate-currency-event", "XYZ")
        self.assertTrue(duplicate2["duplicate"])
        self.assertEqual(self.counts(), (1, 1, 0, 0))
        self.assertEqual(self.db.get_pending_conversion_event(original["pending_id"])["status"],
                         "awaiting_manual_apply")

    def test_new_pending_queue_refresh_rebuilds_rates_without_losing_draft(self):
        tab = self.view()
        try:
            tab.conversion_rate_edits["RUB"].setText("7,25")
            self.incoming("appearing-currency", "XYZ")
            # Called also when Settings/Conversion is revisited or F5 refreshes.
            tab._refresh_pending_conversion_rows()
            self.assertEqual(tab.conversion_rate_edits["RUB"].text(), "7,25")
            self.assertIn("XYZ", tab.conversion_rate_edits)
            self.assertEqual(tab.pending_conversion_table.rowCount(), 1)
            self.assertEqual(tab.pending_conversion_table.item(0, 2).text(),
                             "appearing-currency")
            self.assertEqual(tab.pending_conversion_table.item(0, 5).text(),
                             "Курс не задан")
            self.assertEqual(self.db.get_conversion_rate("RUB"), "1")
            self.assertEqual(self.counts(), (1, 1, 0, 0))
        finally:
            self.close_view(tab)


if __name__ == "__main__":
    unittest.main()
