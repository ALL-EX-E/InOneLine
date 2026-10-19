"""P19-F/UI-085: preserve unsaved rate editor text across capability rebuilds."""
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


SERVICE_UNIT = ConversionUnit("TEST_POINTS", "Баллы канала", "twitch", "service")
NEW_CURRENCY = ConversionUnit("PLN", "PLN", kind="currency")


class ConversionDraftPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.db.set_conversion_rate("TEST_POINTS", "2", kind="service", service="twitch")
        self.connected = [SERVICE_UNIT]

    def tearDown(self):
        self.tmp.cleanup()

    def view(self):
        return SettingsTab(
            self.db, self.paths, LocalApiServer(self.db),
            conversion_units_provider=lambda: list(self.connected),
        )

    def close_view(self, tab):
        tab.thread_pool.waitForDone(5000)
        tab.deleteLater()
        self.app.processEvents()

    def test_unsaved_visible_and_hidden_drafts_survive_disconnect_reconnect(self):
        tab = self.view()
        try:
            tab.conversion_rate_edits["RUB"].setText("7,25")
            tab.conversion_rate_edits["TEST_POINTS"].setText("9,75")
            self.connected = []
            tab._refresh_conversion_rate_rows()
            self.assertEqual(tab.conversion_rate_edits["RUB"].text(), "7,25")
            self.assertNotIn("TEST_POINTS", tab.conversion_rate_edits)
            self.assertEqual(tab._conversion_rate_drafts["TEST_POINTS"], "9,75")
            self.assertEqual(self.db.get_conversion_rate("RUB"), "1")
            self.assertEqual(self.db.get_conversion_rate("TEST_POINTS"), "2")
            self.connected = [SERVICE_UNIT]
            tab._refresh_conversion_rate_rows()
            self.assertEqual(tab.conversion_rate_edits["RUB"].text(), "7,25")
            self.assertEqual(tab.conversion_rate_edits["TEST_POINTS"].text(), "9,75")
            tab._refresh_conversion_rate_rows(force=True)
            self.assertEqual(tab.conversion_rate_edits["TEST_POINTS"].text(), "9,75")
            self.assertEqual(self.db.get_conversion_rate("TEST_POINTS"), "2")
        finally:
            self.close_view(tab)

    def test_hidden_unsaved_unit_remains_draft_after_visible_rates_saved(self):
        tab = self.view()
        try:
            tab.conversion_rate_edits["TEST_POINTS"].setText("10")
            tab.conversion_rate_edits["RUB"].setText("3,5")
            self.connected = []
            tab._refresh_conversion_rate_rows()
            with patch.object(QMessageBox, "information"):
                tab.save_conversion_settings()
            self.assertEqual(self.db.get_conversion_rate("RUB"), "3.5")
            self.assertEqual(self.db.get_conversion_rate("TEST_POINTS"), "2")
            self.assertEqual(tab._conversion_rate_drafts["TEST_POINTS"], "10")
            self.assertNotIn("RUB", tab._conversion_rate_drafts)
            self.connected = [SERVICE_UNIT]
            tab._refresh_conversion_rate_rows()
            self.assertEqual(tab.conversion_rate_edits["TEST_POINTS"].text(), "10")
            with patch.object(QMessageBox, "information"):
                tab.save_conversion_settings()
            self.assertEqual(self.db.get_conversion_rate("TEST_POINTS"), "10")
            self.assertEqual(tab._conversion_rate_drafts, {})
        finally:
            self.close_view(tab)

    def test_new_currency_capability_preserves_existing_editor(self):
        tab = self.view()
        try:
            tab.conversion_rate_edits["RUB"].setText("11,5")
            self.connected = [SERVICE_UNIT, NEW_CURRENCY]
            tab._refresh_conversion_rate_rows()
            self.assertIn("PLN", tab.conversion_rate_edits)
            self.assertEqual(tab.conversion_rate_edits["RUB"].text(), "11,5")
            tab.conversion_rate_edits["PLN"].setText("1,25")
            tab._handle_settings_page_changed(0)
            self.assertEqual(tab.conversion_rate_edits["PLN"].text(), "1,25")
            self.assertEqual(self.db.get_conversion_rate("RUB"), "1")
            self.assertEqual(self.db.get_conversion_rate("PLN"), "")
            with patch.object(QMessageBox, "information"):
                tab.save_conversion_settings()
            self.assertEqual(self.db.get_conversion_rate("RUB"), "11.5")
            self.assertEqual(self.db.get_conversion_rate("PLN"), "1.25")
        finally:
            self.close_view(tab)

    def test_validation_failure_preserves_all_drafts_through_rebuild(self):
        tab = self.view()
        try:
            tab.conversion_rate_edits["RUB"].setText("4")
            tab.conversion_rate_edits["TEST_POINTS"].setText("incorrect")
            with patch.object(QMessageBox, "warning") as warning:
                tab.save_conversion_settings()
            warning.assert_called_once()
            self.assertEqual(self.db.get_conversion_rate("RUB"), "1")
            self.connected = []
            tab._refresh_conversion_rate_rows()
            self.connected = [SERVICE_UNIT]
            tab._refresh_conversion_rate_rows()
            self.assertEqual(tab.conversion_rate_edits["RUB"].text(), "4")
            self.assertEqual(tab.conversion_rate_edits["TEST_POINTS"].text(), "incorrect")
            self.assertEqual(self.db.get_conversion_rate("TEST_POINTS"), "2")
        finally:
            self.close_view(tab)

    def test_reverting_to_saved_value_discards_draft_on_rebuild(self):
        tab = self.view()
        try:
            edit = tab.conversion_rate_edits["TEST_POINTS"]
            edit.setText("17")
            self.assertEqual(tab._conversion_rate_drafts["TEST_POINTS"], "17")
            edit.setText("2")
            self.assertNotIn("TEST_POINTS", tab._conversion_rate_drafts)
            self.connected = []
            tab._refresh_conversion_rate_rows()
            self.connected = [SERVICE_UNIT]
            tab._refresh_conversion_rate_rows()
            self.assertEqual(tab.conversion_rate_edits["TEST_POINTS"].text(), "2")
            self.assertEqual(tab._conversion_rate_drafts, {})
        finally:
            self.close_view(tab)


if __name__ == "__main__":
    unittest.main()
