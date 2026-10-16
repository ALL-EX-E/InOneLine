from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox



class AuctionSearchMixin:
    def _search_text_changed(self, source: str, text: str):
        """Route synchronized search through MainWindow; standalone fallback stays eager."""
        if self._current_session() is not None:
            # The active auction may contain temporary auction_only lots.
            # Its query never overwrites the permanent List/Public searches.
            self.refresh()
            return
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
        if (self._current_session() is None and game_id is not None
                and hasattr(window, "sync_search_result")):
            window.sync_search_result(game_id, source="auction")

    def _sync_lot_scroll_buttons(self):
        text = (
            "Автопрокрутка: ВКЛ"
            if self._desktop_lot_auto_scroll_enabled
            else "Автопрокрутка: ВЫКЛ"
        )
        for button_name in ("conduct_scroll_btn",):
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
        bar = self.conduct_table.verticalScrollBar()
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
        # One shared operator switch controls both local auction tables and the
        # dedicated auction-lots OBS overlay.
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
            self.conduct_search.text().strip()
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

        if not getattr(self, "_history_hover_pauses_auto_scroll", False):
            self._conduct_scroll_direction = self._advance_auto_scroll_table(
                self.conduct_table, self._conduct_scroll_direction
            )

    def select_synced_search_result(self, game_id: int) -> bool:
        """Select in the one visible Auction table (prestart sync only)."""
        return self.select_conduct_game_id(game_id)

    def activate_search(self):
        """Compatibility entry point for existing List/Public sync callers."""
        self.activate_conduct_search()
