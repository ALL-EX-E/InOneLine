"""Auction verification visibility and refresh query regression."""
from __future__ import annotations

from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from streaming_manager.app_paths import AppPaths
from streaming_manager.credentials import MemoryCredentialStore
from streaming_manager.database import Database, Game
from streaming_manager.views.auction import AuctionTab


class AuctionContextRefreshTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(temp.cleanup)
        paths = AppPaths.from_root(temp.name)
        paths.ensure_runtime_dirs()
        self.db = Database(paths.database_path, credential_store=MemoryCredentialStore())
        for title in ("Alpha", "Beta"):
            self.db.add_game(Game(None, title, None, 100, 0, "not_played", ""))
        self.tab = self.open_tab()

    def open_tab(self):
        tab = AuctionTab(self.db)

        def close_tab():
            tab.set_main_tab_visible(False)
            tab.auction_timer.stop()
            tab.shutdown_audio()
            tab.shutdown_shared_xlsx()
            tab.close()

        self.addCleanup(close_tab)
        return tab

    def set_mode(self, mode):
        self.tab.mode_combo.setCurrentIndex(self.tab.mode_combo.findData(mode))

    def test_verification_hidden_until_preview_available(self):
        self.assertIs(self.tab.verification_data_btn.parent(), self.tab.wheel_panel)
        self.assertTrue(self.tab.verification_data_btn.isHidden())
        self.set_mode("weighted_wheel")
        self.assertFalse(self.tab.verification_data_btn.isHidden())
        self.set_mode("max_amount")
        self.assertTrue(self.tab.verification_data_btn.isHidden())

        session_id = self.db.create_auction_session("max_amount", 60, "random_org")
        self.tab.refresh()
        self.assertTrue(self.tab.verification_data_btn.isHidden())
        self.assertEqual(self.db.finish_auction(session_id)["status"], "tie_break_required")
        self.tab.refresh()
        self.assertTrue(self.tab.verification_data_btn.isHidden())

        self.db.start_auction_tie_wheel(session_id)
        self.tab.refresh()
        self.assertFalse(self.tab.verification_data_btn.isHidden())
        self.assertTrue(self.tab.setup_widget.isHidden())
        self.tab = self.open_tab()
        self.assertFalse(self.tab.verification_data_btn.isHidden())
        self.assertTrue(self.tab.setup_widget.isHidden())
        before = self.db.get_auction_session(session_id)
        with patch("streaming_manager.views.auction_parts.rng.show_readonly_text_dialog") as dialog:
            self.tab.verification_data_btn.click()
        dialog.assert_called_once()
        self.assertEqual(self.db.get_auction_session(session_id), before)
        self.assertEqual(before["rng_method"], "random_org")

    def test_weighted_wheel_loads_one_snapshot_on_mode_format_and_clean_return(self):
        with patch.object(self.db, "current_wheel_payload", wraps=self.db.current_wheel_payload) as load:
            self.set_mode("weighted_wheel")
            self.assertEqual(load.call_count, 1)
            self.assertFalse(self.tab.verification_data_btn.isHidden())
            load.reset_mock()
            self.tab.wheel_format_combo.setCurrentIndex(
                self.tab.wheel_format_combo.findData("elimination")
            )
            self.assertEqual(load.call_count, 1)
            load.reset_mock()
            self.tab.set_main_tab_visible(False)
            self.tab.set_main_tab_visible(True)
            self.assertEqual(load.call_count, 1)
        chance_column = self.tab._conduct_chance_column
        self.assertEqual(self.tab.conduct_table.item(0, chance_column).text(), "50,00 %")

        self.db.create_auction_session("weighted_wheel", 0, start_in_wheel_mode=True)
        self.tab.refresh()
        with patch.object(self.db, "wheel_payload", wraps=self.db.wheel_payload) as load:
            self.tab.set_main_tab_visible(False)
            self.tab.set_main_tab_visible(True)
            self.assertEqual(load.call_count, 1)
        self.assertEqual(self.tab.conduct_table.item(0, chance_column).text(), "50,00 %")

    def test_refresh_reuses_prestart_lots_and_current_session(self):
        with patch.object(self.db, "auction_eligible_games", wraps=self.db.auction_eligible_games) as eligible:
            initial_tab = self.open_tab()
            self.assertEqual(eligible.call_count, 1)
        self.assertEqual(initial_tab.timer_edit.text(), "00:10:00.000")

        with patch.object(self.db, "auction_eligible_games", wraps=self.db.auction_eligible_games) as eligible:
            self.tab.refresh()
            self.assertEqual(eligible.call_count, 1)
        self.assertIn("200", self.tab.auction_total_label.text())

        self.db.create_auction_session("max_amount", 60)
        self.tab.refresh()
        with patch.object(self.tab, "_current_session", wraps=self.tab._current_session) as read:
            self.tab.refresh()
            self.assertEqual(read.call_count, 1)


    def test_explicit_data_refresh_leaves_soundtrack_catalogs_alone(self):
        self.tab.set_main_tab_visible(False)
        self.db.add_game(Game(None, "Gamma", None, 50, 0, "not_played", ""))
        with (
            patch.object(self.tab, "_refresh_wheel_soundtrack_library") as wheel,
            patch.object(self.tab, "_refresh_auction_soundtrack_library") as auction,
        ):
            self.tab.refresh_force(refresh_soundtracks=False)
            self.assertEqual(self.tab.conduct_table.rowCount(), 3)
            wheel.assert_not_called()
            auction.assert_not_called()
            self.tab.refresh_force()
            wheel.assert_called_once()
            auction.assert_called_once()


if __name__ == "__main__":
    main()
