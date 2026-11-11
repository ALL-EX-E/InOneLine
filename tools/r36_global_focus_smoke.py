"""R36: real Qt events, current-page isolation and existing Escape consumers."""
from __future__ import annotations

import socket
import warnings
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QComboBox, QDialog, QLineEdit,
    QMenu, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QWidget,
)

from streaming_manager.app_paths import AppPaths
from streaming_manager.credentials import MemoryCredentialStore
from streaming_manager.database import Database
from streaming_manager.ui_settings import UI_SETTINGS_MIGRATION_KEY, ui_settings_path
from streaming_manager.views.main_window import MainWindow


def main() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(prefix="iol-r36-") as temporary:
        paths = AppPaths.from_root(temporary)
        paths.ensure_runtime_dirs()
        settings = QSettings(str(ui_settings_path(paths.data_dir)), QSettings.IniFormat)
        settings.setValue(UI_SETTINGS_MIGRATION_KEY, True)
        settings.sync()
        db = Database(paths.database_path, credential_store=MemoryCredentialStore())
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            db.set_setting("api_port", str(listener.getsockname()[1]))
        with patch.object(MainWindow, "_startup_backup"), patch.object(MainWindow, "_validate_active_integrations"):
            window = MainWindow(db, paths)
            window.setAttribute(Qt.WA_DontShowOnScreen, True)
            window.resize(1100, 850)
            window.show()

            def settle():
                app.processEvents()
                # Direct widget-event coverage without activating a desktop window.
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", DeprecationWarning)
                    app.setActiveWindow(window)

            def focus(widget):
                settle()
                widget.setFocus(Qt.OtherFocusReason)
                app.processEvents()
                assert app.focusWidget() is widget, type(widget).__name__

            def escape(widget):
                QTest.keyClick(widget, Qt.Key_Escape)
                app.processEvents()

            probes = []
            try:
                for key, page in window._main_tab_pages.items():
                    window._set_current_main_page(page)
                    settle()
                    probe = QWidget(page)
                    probe.setGeometry(20, 20, 450, 330)
                    field = QLineEdit("Сохранить этот текст", probe)
                    field.setGeometry(5, 5, 280, 30)
                    table = QTableWidget(50, 2, probe)
                    table.setGeometry(5, 45, 400, 170)
                    table.setSelectionBehavior(QAbstractItemView.SelectRows)
                    for row in range(50):
                        table.setItem(row, 0, QTableWidgetItem(f"Строка {row}"))
                    probe.show()
                    probes.append((probe, field, table))
                    table.selectRow(0)
                    focus(field)
                    escape(field)
                    assert not table.selectedItems(), f"{key}: Escape left the row selected"
                    assert app.focusWidget() is not field, f"{key}: Escape left text focus"
                    assert field.text() == "Сохранить этот текст", key
                    table.selectRow(1)
                    focus(field)
                    QTest.mouseClick(probe, Qt.LeftButton, pos=QPoint(430, 300))
                    assert not table.selectedItems(), f"{key}: background left selection"
                    assert app.focusWidget() is not field, f"{key}: background left text focus"
                    assert field.text() == "Сохранить этот текст", key
                    table.selectRow(2)
                    focus(table)
                    escape(table)
                    assert not table.selectedItems() and not table.currentIndex().isValid(), key
                    print(f"R36_PAGE_PASS={key}", flush=True)

                # A hidden page keeps its selection and field contents.
                old_probe, old_field, old_table = probes[0]
                old_table.selectRow(4)
                probe, field, table = probes[-1]
                table.selectRow(3)
                focus(field)
                escape(field)
                assert old_table.selectedItems(), "Escape changed another main tab"
                assert old_field.text() == "Сохранить этот текст"

                # Interactive mouse targets keep their usual action/selection.
                button = QPushButton("Действие", probe)
                button.setGeometry(5, 225, 130, 30)
                button.show()
                clicks = []
                button.clicked.connect(lambda: clicks.append(True))
                table.selectRow(1)
                QTest.mouseClick(button, Qt.LeftButton)
                assert clicks == [True] and table.selectedItems(), "button click intercepted"
                QTest.mouseClick(table.viewport(), Qt.LeftButton, pos=table.visualItemRect(table.item(2, 0)).center())
                assert table.currentRow() == 2 and table.selectedItems(), "normal table click intercepted"
                focus(field)
                field.selectAll()
                QTest.keyClick(field, Qt.Key_A, Qt.ControlModifier)
                assert field.selectedText() == field.text(), "text selection intercepted"
                QTest.keyClick(field, Qt.Key_Return)
                assert table.selectedItems(), "Enter cleared table selection"
                QTest.keyClick(field, Qt.Key_Escape, Qt.ControlModifier)
                assert table.selectedItems(), "modified Escape intercepted"
                QTest.keyClick(field, Qt.Key_Tab)
                assert app.focusWidget() is not field, "Tab navigation intercepted"

                # Escape belongs first to an active cell editor, then R36.
                table.selectRow(0)
                table.editItem(table.item(0, 0))
                app.processEvents()
                editor = app.focusWidget()
                assert editor is not table and table.state() == QAbstractItemView.EditingState
                QTest.keyClicks(editor, "changed")
                escape(editor)
                assert table.item(0, 0).text() == "Строка 0" and table.selectedItems(), "cell Escape changed"
                escape(table)
                assert not table.selectedItems(), "second Escape did not clear selection"

                table.selectRow(0)
                dialog = QDialog(window)
                dialog.setAttribute(Qt.WA_DontShowOnScreen, True)
                dialog.setModal(True)
                dialog.show()
                app.processEvents()
                escape(dialog)
                assert not dialog.isVisible() and table.selectedItems(), "dialog Escape intercepted"

                combo = QComboBox(probe)
                combo.setGeometry(145, 225, 150, 30)
                combo.addItems(["Первый", "Второй"])
                combo.show()
                focus(combo)
                combo.showPopup()
                app.processEvents()
                escape(combo.view())
                assert combo.currentIndex() == 0 and table.selectedItems(), "combo popup Escape intercepted"

                menu = QMenu(window)
                menu.addAction("Обычное действие")
                menu.popup(window.mapToGlobal(QPoint(30, 30)))
                app.processEvents()
                escape(menu)
                assert not menu.isVisible() and table.selectedItems(), "menu Escape intercepted"

                # Invalid numeric text must not be silently corrected by blur.
                spin = QSpinBox(probe)
                spin.setRange(10, 99)
                spin.setGeometry(305, 225, 100, 30)
                spin.show()
                focus(spin)
                spin.lineEdit().setText("")
                escape(spin)
                assert spin.lineEdit().text() == "", "invalid spin text corrected"
                assert spin.hasFocus() or spin.lineEdit().hasFocus(), "invalid spin lost focus"
                QTest.mouseClick(probe, Qt.LeftButton, pos=QPoint(430, 300))
                assert spin.value() == 10 and spin.hasAcceptableInput(), "normal focus-out validation changed"

                # An ordinary background click commits a cell edit first.
                table.selectRow(0)
                table.editItem(table.item(0, 0))
                app.processEvents()
                editor = app.focusWidget()
                editor.selectAll()
                QTest.keyClicks(editor, "saved")
                QTest.mouseClick(probe, Qt.LeftButton, pos=QPoint(430, 300))
                assert table.item(0, 0).text() == "saved" and not table.selectedItems()

                # Actual selection-dependent application actions are updated.
                window._set_current_main_page(window.games_tab)
                probes[0][0].hide()
                db.sync_main_games_state([{"title": "R36 тест", "sm_points": 1}])
                window.games_tab.refresh()
                settle()
                real_table = window.games_tab.table
                real_table.selectRow(0)
                assert window.games_tab.selected_game_id() is not None
                focus(real_table)
                escape(real_table)
                assert window.games_tab.selected_game_id() is None
                assert not window.games_tab.edit_btn.isEnabled()
                assert not window.games_tab.delete_btn.isEnabled()
                assert not window.games_tab.archive_btn.isEnabled()
                real_table.selectRow(0)
                focus(window.tabs.tabBar())
                escape(window.tabs.tabBar())
                assert window.games_tab.selected_game_id() is None, "tab-bar focus prevented Escape"
                real_table.selectRow(0)
                focus(window.games_tab.search)
                scroll = window.tabs.currentWidget()
                QTest.mouseClick(scroll.viewport(), Qt.LeftButton, pos=QPoint(1, 1))
                assert window.games_tab.selected_game_id() is None, "workspace background left selection"

                # History's existing selection handler uses currentRow(). It
                # must see an invalid current index when deselection is emitted.
                history = window.completed_history_tab
                window._set_current_main_page(history)
                probes[4][0].hide()
                history.table.setRowCount(1)
                item = QTableWidgetItem("Проверка снятия выбора")
                item.setData(Qt.UserRole, 123)
                history.table.setItem(0, 0, item)
                with patch.object(history, "_load_details"):
                    history.table.selectRow(0)
                    assert history._selected_auction_id == 123
                    focus(history.table)
                    escape(history.table)
                assert history._selected_auction_id is None, "history kept details for cleared row"
                assert all(label.text() == "—" for label in history.general_labels.values())
                print("R36_GLOBAL_FOCUS_ALL_PASS", flush=True)
            finally:
                for probe, _, _ in probes:
                    probe.hide()
                window.close()
                app.processEvents()
                window.thread_pool.waitForDone(5000)


if __name__ == "__main__":
    main()
