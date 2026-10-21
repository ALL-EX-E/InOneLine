"""UI-081 #2: Journal description reflects actual integrated audit events.

Only the existing user-facing QLabel copy changes; Journal worker, model,
stored change_log, search and table presentation stay untouched.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QTableView

from streaming_manager.views.log import LogTab, LogTableModel


EXPECTED = (
    "Журнал изменений и событий программы, включая аукционы, "
    "настройки и подключённые интеграции."
)


class EmptyJournalDatabase:
    def list_log(self, limit=500):
        return []


class JournalCurrentDescriptionSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tab = LogTab(EmptyJournalDatabase())
        self.app.processEvents()

    def tearDown(self):
        self.tab.thread_pool.waitForDone(5000)
        self.app.processEvents()
        self.tab.close()
        self.tab.deleteLater()
        self.app.processEvents()

    def test_exact_current_description_and_old_copy_absent(self):
        labels = [x.text() for x in self.tab.findChildren(QLabel)]
        self.assertIn(EXPECTED, labels)
        self.assertNotIn(
            "Журнал локальных изменений. "
            "Новые интеграции позже будут писать события сюда же.",
            labels,
        )
        self.assertEqual(labels.count(EXPECTED), 1)
        self.assertTrue(
            any(x.property("muted") for x in self.tab.findChildren(QLabel))
        )

    def test_existing_table_search_and_debounce_unchanged(self):
        self.assertIsInstance(self.tab.table, QTableView)
        self.assertIsInstance(self.tab.model, LogTableModel)
        self.assertEqual(self.tab.model.HEADERS, (
            "ВРЕМЯ", "ОБЪЕКТ", "ID", "ДЕЙСТВИЕ", "ПОДРОБНОСТИ",
        ))
        self.assertTrue(self.tab.table.alternatingRowColors())
        self.assertEqual(self.tab._search_timer.interval(), 250)
        self.assertEqual(self.tab.search.placeholderText(), "Поиск в журнале…")
        self.assertTrue(self.tab.search.isClearButtonEnabled())
        self.assertIsInstance(self.tab.search, QLineEdit)

    def test_existing_readonly_refresh_keeps_description(self):
        self.tab.thread_pool.waitForDone(5000)
        self.app.processEvents()
        self.tab.refresh()
        self.tab.thread_pool.waitForDone(5000)
        self.app.processEvents()
        self.assertEqual(self.tab.model.rowCount(), 0)
        self.assertIn(
            EXPECTED,
            [x.text() for x in self.tab.findChildren(QLabel)],
        )


if __name__ == "__main__":
    unittest.main()
