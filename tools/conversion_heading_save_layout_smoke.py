"""P19-A / UI-085: conversion heading and Save-button placement only."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.views.settings import SettingsTab


class ConversionHeadingSaveLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.tab = SettingsTab(self.db, self.paths, LocalApiServer(self.db))

    def tearDown(self):
        self.tab.thread_pool.waitForDone(5000)
        self.tab.deleteLater()
        self.app.processEvents()
        self.tmp.cleanup()

    def _save_button(self):
        buttons = [
            b for b in self.tab.conversion_page.findChildren(QPushButton)
            if b.text() == "Сохранить курсы"
        ]
        self.assertEqual(len(buttons), 1)
        return buttons[0]

    def test_heading_names_rates_not_only_currencies(self):
        labels = [label.text() for label in self.tab.conversion_page.findChildren(QLabel)]
        self.assertIn("Конвертация в баллы", labels)
        self.assertIn("Курсы конвертации", labels)
        self.assertNotIn("Валюты", labels)
        self.assertIn("Ожидают применения", labels)

    def test_save_is_between_rate_editors_and_pending_section(self):
        layout = self.tab.conversion_page.layout()
        save = self._save_button()
        rate_idx = layout.indexOf(self.tab.conversion_rates_widget)
        save_idx = layout.indexOf(save)
        pending_idx = layout.indexOf(self.tab.pending_conversion_table)
        self.assertGreaterEqual(rate_idx, 0)
        self.assertEqual(save_idx, rate_idx + 1)
        self.assertGreater(pending_idx, save_idx)
        # Only the visual sequence changes, not the native row/editor widgets.
        self.assertIn("RUB", self.tab.conversion_rate_edits)

    def test_save_callback_remains_functional_after_relocation(self):
        edit = self.tab.conversion_rate_edits["RUB"]
        edit.setText("2")
        self._save_button().click()
        self.assertEqual(self.db.get_conversion_rate("RUB"), "2")
        self.assertEqual(self.tab.conversion_rate_edits["RUB"].text(), "2")

    def test_refresh_and_navigation_keep_single_button(self):
        page = self.tab.conversion_page
        self.tab.settings_tabs.setCurrentWidget(page)
        self.tab.settings_tabs.setCurrentWidget(self.tab.integration_page)
        self.tab.settings_tabs.setCurrentWidget(page)
        self.tab._refresh_conversion_rate_rows(force=True)
        self.assertEqual(
            sum(button.text() == "Сохранить курсы" for button in page.findChildren(QPushButton)),
            1,
        )
        layout = page.layout()
        self.assertEqual(
            layout.indexOf(self._save_button()),
            layout.indexOf(self.tab.conversion_rates_widget) + 1,
        )


if __name__ == "__main__":
    unittest.main()
