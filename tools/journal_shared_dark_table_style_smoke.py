"""UI-081 step 1: shared dark table style works for Journal QTableView.

All former QTableWidget colors and alternate row behavior are preserved.
No database, Journal worker, search or event formatting changes.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QApplication, QTableView, QTableWidget, QWidget

from streaming_manager.views.common import APP_STYLE
from streaming_manager.views.log import LogTableModel


class SharedDarkTableStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_one_shared_dark_style_has_both_table_selectors(self):
        matches = re.findall(
            r"QTableWidget\s*,\s*QTableView\s*\{([^}]*)\}",
            APP_STYLE, re.MULTILINE,
        )
        self.assertEqual(len(matches), 1)
        rules = matches[0]
        for setting in (
            "background: #202326",
            "alternate-background-color: #24282b",
            "color: #ededed",
            "border: 1px solid #393e43",
            "selection-background-color: #295e83",
            "selection-color: white",
            "gridline-color: #32373b",
        ):
            with self.subTest(setting=setting):
                self.assertIn(setting, rules)

    def test_dark_alternation_is_actually_rendered_in_qtableview(self):
        owner = QWidget()
        owner.setStyleSheet(APP_STYLE)
        owner.resize(450, 210)
        view = QTableView(owner)
        view.setGeometry(4, 4, 420, 176)
        view.setAlternatingRowColors(True)
        view.setShowGrid(False)
        view.verticalHeader().setVisible(False)
        view.horizontalHeader().setVisible(False)
        view.verticalHeader().setDefaultSectionSize(32)
        model = QStandardItemModel(2, 1, view)
        model.setData(model.index(0, 0), "")
        model.setData(model.index(1, 0), "")
        view.setModel(model)
        view.setColumnWidth(0, 340)
        owner.show()
        try:
            self.app.processEvents()
            viewport = view.viewport()
            picture = viewport.grab().toImage()
            x = 140
            first = picture.pixelColor(x, 16)
            second = picture.pixelColor(x, 48)
            rgb_first = (first.red(), first.green(), first.blue())
            rgb_second = (second.red(), second.green(), second.blue())
            self.assertEqual(rgb_first, (0x20, 0x23, 0x26))
            self.assertEqual(rgb_second, (0x24, 0x28, 0x2b))
            self.assertTrue(view.alternatingRowColors())
        finally:
            owner.close()
            owner.deleteLater()
            self.app.processEvents()

    def test_original_qtablewidget_and_journal_model_unchanged(self):
        view = QTableView()
        widget = QTableWidget()
        model = LogTableModel()
        try:
            self.assertEqual(model.HEADERS, (
                "ВРЕМЯ", "ОБЪЕКТ", "ID", "ДЕЙСТВИЕ", "ПОДРОБНОСТИ",
            ))
            model.replace_rows([(
                "21.10.2026 17:00:00", "Игра", "12", "ИЗМЕНЕНИЕ", "Изменены баллы",
            )])
            view.setModel(model)
            self.assertEqual(model.rowCount(), 1)
            self.assertEqual(model.columnCount(), 5)
            self.assertEqual(
                model.data(model.index(0, 4), Qt.ToolTipRole),
                "Изменены баллы",
            )
            self.assertIsInstance(widget, QTableWidget)
        finally:
            view.close()
            widget.close()
            view.deleteLater()
            widget.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
