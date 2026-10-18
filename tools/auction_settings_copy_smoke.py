"""P17-A/UI-083: native Auction Settings wording and accepted behavior lock."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QLabel, QMessageBox

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.constants import AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_KEY
from streaming_manager.database import Database
from streaming_manager.views.settings import SettingsTab


class AuctionSettingsCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.temp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.tab = SettingsTab(self.db, self.paths, LocalApiServer(self.db))

    def tearDown(self):
        self.tab.thread_pool.waitForDone(5000)
        self.tab.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def test_center_asset_help_is_accurate_and_fallback_named(self):
        combo = self.tab.wheel_center_image_combo
        self.assertEqual(combo.itemText(0), "— логотип InOneLine —")
        self.assertEqual(combo.itemData(0), "")
        self.assertIn(
            "встроенный логотип InOneLine",
            self.tab.wheel_center_image_status.text(),
        )
        notes = [
            label.text()
            for label in self.tab.auction_page.findChildren(QLabel)
        ]
        text = "\n".join(notes)
        self.assertIn("локальная копия в поддерживаемом формате", text)
        self.assertIn("GIF/WebP сохраняют анимацию", text)
        self.assertNotIn("локальная PNG-копия", text)
        self.assertNotIn("— стандартный центр —", text)

    def test_external_label_does_not_rename_persisted_reason(self):
        control = self.tab.auto_extend_external_enabled
        self.assertEqual(control.text(), "Внешнее поступление")
        original = self.db.get_setting(AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_KEY, "")
        control.setChecked(not bool(int(original or "0")))
        self.tab.auction_wheel_duration.setText("00:00:01.000")
        self.tab.auction_max_amount_duration.setText("00:00:10.000")
        with patch.object(QMessageBox, "information"):
            self.tab.save_auction_settings()
        self.assertEqual(
            self.db.get_setting(AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_KEY),
            "1" if control.isChecked() else "0",
        )
        self.assertEqual(self.db.get_setting("auction_wheel_default_duration_ms"), "1000")
        self.assertEqual(
            self.db.get_setting("auction_max_amount_default_duration_ms"), "10000",
        )
        self.assertEqual(self.db.get_setting("wheel_center_image_media_id", ""), "")


if __name__ == "__main__":
    unittest.main()
