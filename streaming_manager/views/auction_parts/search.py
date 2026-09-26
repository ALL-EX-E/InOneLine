from __future__ import annotations
import hashlib
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QDialogButtonBox, QLabel, QTabWidget, QTextEdit, QVBoxLayout, QWidget

from ...database import format_points
from ...exporters import export_pointauc_csv, pointauc_text
from ...random_sources import RandomDraw, RandomOrgClient
from ...workers import FunctionWorker


class AuctionSearchMixin:
    def _search_text_changed(self, source: str, text: str):
        """Route synchronized search through MainWindow; standalone fallback stays eager."""
        window = self.window()
        if hasattr(window, "sync_search_text"):
            window.sync_search_text(source, text)
        else:
            self.refresh()

    def selected_game_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def selected_conduct_game_id(self) -> int | None:
        row = self.conduct_table.currentRow()
        if row < 0:
            return None
        item = self.conduct_table.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def select_conduct_game_id(self, game_id: int) -> bool:
        for row in range(self.conduct_table.rowCount()):
            item = self.conduct_table.item(row, 0)
            if item is None:
                continue
            try:
                row_id = int(item.data(Qt.UserRole))
            except (TypeError, ValueError):
                continue
            if row_id != game_id:
                continue

            self.conduct_table.selectRow(row)
            self.conduct_table.scrollToItem(item)
            return True
        return False

    def activate_conduct_search(self):
        query = self.conduct_search.text().strip()
        self.refresh()

        if self.conduct_table.rowCount() == 0:
            if query:
                QMessageBox.information(
                    self,
                    "Поиск лота",
                    f"По запросу «{query}» ничего не найдено.",
                )
            return

        self.conduct_table.selectRow(0)
        target = self.conduct_table.item(0, 0)
        if target is not None:
            self.conduct_table.scrollToItem(target)
        self.conduct_table.setFocus()

        game_id = self.selected_conduct_game_id()
        window = self.window()
        if game_id is not None and hasattr(window, "sync_search_result"):
            window.sync_search_result(
                game_id,
                source="auction_conduct",
            )

    def _sync_lot_scroll_buttons(self):
        text = (
            "Автопрокрутка: ВКЛ"
            if self._desktop_lot_auto_scroll_enabled
            else "Автопрокрутка: ВЫКЛ"
        )
        for button_name in ("lots_scroll_btn", "conduct_scroll_btn"):
            button = getattr(self, button_name, None)
            if button is not None:
                button.setText(text)

    def _set_desktop_lot_auto_scroll(self, enabled: bool):
        self._desktop_lot_auto_scroll_enabled = bool(enabled)
        if self._desktop_lot_auto_scroll_enabled:
            self._lots_scroll_direction = 1
            self._conduct_scroll_direction = 1
        timer = getattr(self, "conduct_scroll_timer", None)
        if timer is not None:
            should_run = bool(
                self._desktop_lot_auto_scroll_enabled
                and getattr(self, "_main_tab_visible", True)
            )
            if should_run and not timer.isActive():
                timer.start()
            elif not should_run and timer.isActive():
                timer.stop()
        self._sync_lot_scroll_buttons()

    def _toggle_desktop_lot_auto_scroll(self):
        self._set_desktop_lot_auto_scroll(
            not bool(self._desktop_lot_auto_scroll_enabled)
        )

    def _reset_conduct_auto_scroll(self):
        # Historical callers use this name when opening/restarting an auction.
        # Reset both local lists only while their shared switch is enabled.
        if not self._desktop_lot_auto_scroll_enabled:
            return
        self._lots_scroll_direction = 1
        self._conduct_scroll_direction = 1
        for table in (self.table, self.conduct_table):
            bar = table.verticalScrollBar()
            bar.setValue(bar.minimum())

    @staticmethod
    def _advance_auto_scroll_table(table, direction: int) -> int:
        bar = table.verticalScrollBar()
        minimum = bar.minimum()
        maximum = bar.maximum()
        if maximum <= minimum:
            return direction

        value = bar.value()
        if direction > 0:
            next_value = value + 1
            if next_value >= maximum:
                next_value = maximum
                direction = -1
        else:
            next_value = value - 1
            if next_value <= minimum:
                next_value = minimum
                direction = 1
        bar.setValue(next_value)
        return direction

    def _auto_scroll_conduct_lots(self):
        # One shared operator switch controls both local auction tables. It is
        # intentionally independent from every OBS/list-overlay autoscroll.
        if not self._desktop_lot_auto_scroll_enabled:
            return

        # During wheel animation keep both tables still to preserve smooth GUI
        # rendering in the single Qt thread.
        if self.wheel_widget.is_spinning():
            return

        # Explicit operator work takes priority. Per the approved desktop
        # contract, search/manual focus turns the shared switch OFF instead of
        # silently resuming later. A7 history hover is only a temporary pause.
        operator_interaction = bool(
            self.search.text().strip()
            or self.table.hasFocus()
            or self.conduct_search.text().strip()
            or self.conduct_table.hasFocus()
            or self.bid_amount.hasFocus()
            or self.add_bid_btn.hasFocus()
            or self.decrease_bid_btn.hasFocus()
            or self.new_lot_title.hasFocus()
            or self.new_lot_points.hasFocus()
            or self.new_lot_btn.hasFocus()
        )
        if operator_interaction:
            self._set_desktop_lot_auto_scroll(False)
            return

        self._lots_scroll_direction = self._advance_auto_scroll_table(
            self.table, self._lots_scroll_direction
        )
        if not getattr(self, "_history_hover_pauses_auto_scroll", False):
            self._conduct_scroll_direction = self._advance_auto_scroll_table(
                self.conduct_table, self._conduct_scroll_direction
            )

    def select_synced_search_result(self, game_id: int) -> bool:
        found = False
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                continue
            try:
                row_id = int(item.data(Qt.UserRole))
            except (TypeError, ValueError):
                continue
            if row_id != game_id:
                continue

            self.table.selectRow(row)
            self.table.scrollToItem(item)
            found = True
            break

        conduct_found = self.select_conduct_game_id(game_id)
        return found or conduct_found

    def activate_search(self):
        query = self.search.text().strip()
        self.refresh()

        if self.table.rowCount() == 0:
            if query:
                QMessageBox.information(
                    self,
                    "Поиск",
                    f"По запросу «{query}» ничего не найдено.",
                )
            return

        self.table.selectRow(0)
        target = self.table.item(0, 0)
        if target is not None:
            self.table.scrollToItem(target)
        self.table.setFocus()

        game_id = self.selected_game_id()
        window = self.window()
        if game_id is not None and hasattr(window, "sync_search_result"):
            window.sync_search_result(game_id, source="auction")
