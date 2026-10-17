from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from ...constants import AUCTION_LOTS_OBS_AUTO_SCROLL_KEY



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
        # UI-074: local operator table is manual-only, while the persisted
        # control affects the dedicated OBS overlay regardless of tab focus.
        button = getattr(self, "conduct_scroll_btn", None)
        if button is not None:
            button.setText(
                "Автопрокрутка оверлея: ВКЛ"
                if self._obs_lot_auto_scroll_enabled
                else "Автопрокрутка оверлея: ВЫКЛ"
            )

    def _set_lot_overlay_auto_scroll(self, enabled: bool):
        self._obs_lot_auto_scroll_enabled = bool(enabled)
        self.db.set_setting(
            AUCTION_LOTS_OBS_AUTO_SCROLL_KEY,
            "1" if enabled else "0",
        )
        self._sync_lot_scroll_buttons()

    def _toggle_overlay_lot_auto_scroll(self):
        self._set_lot_overlay_auto_scroll(
            not bool(self._obs_lot_auto_scroll_enabled)
        )

    def select_synced_search_result(self, game_id: int) -> bool:
        """Select in the one visible Auction table (prestart sync only)."""
        return self.select_conduct_game_id(game_id)

    def activate_search(self):
        """Compatibility entry point for existing List/Public sync callers."""
        self.activate_conduct_search()
