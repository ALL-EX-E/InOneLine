"""Issue #4/A: native Qt Ctrl/Shift batch import for shared wheel-center media."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from streaming_manager.app_paths import AppPaths
from streaming_manager.constants import WHEEL_CENTER_IMAGE_MEDIA_ID_KEY
from streaming_manager.database import Database
from streaming_manager.media import MEDIA_CATEGORY_WHEEL_CENTER_ICONS
from streaming_manager.ui import MainWindow


class WheelCenterMultiFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.temp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.window = MainWindow(self.db, self.paths)
        self.window.show()
        self.settings = self.window.settings_tab
        self.auction = self.window.auction_tab
        self.warnings = []
        self.warning_patch = patch.object(
            QMessageBox, "warning",
            side_effect=lambda *args, **kwargs: self.warnings.append(args),
        )
        self.warning_patch.start()

    def tearDown(self):
        self.warning_patch.stop()
        self.window.thread_pool.waitForDone(5000)
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        self.temp.cleanup()

    def image(self, name: str, color: str) -> str:
        path = Path(self.temp.name) / name
        image = QImage(18, 18, QImage.Format.Format_ARGB32)
        image.fill(QColor(color))
        self.assertTrue(image.save(str(path)), f"Failed to save fixture {name}")
        return str(path)

    def await_batch(self, target: str):
        if target == "settings":
            done = lambda: (
                self.settings._wheel_center_image_worker is None
                and self.settings._wheel_center_file_batch is None
            )
        else:
            done = lambda: (
                self.auction._wheel_center_import_worker is None
                and self.auction._wheel_center_picker_file_batch is None
            )
        for _ in range(600):
            self.app.processEvents()
            if done():
                return
            QTest.qWait(10)
        self.fail(f"Wheel-center batch worker did not finish for {target}")

    def catalog(self):
        return self.db.sync_managed_media_category(MEDIA_CATEGORY_WHEEL_CENTER_ICONS)

    def test_settings_batch_reuses_existing_hash_dedupe_and_selects_last(self):
        first = self.image("a.png", "#FF0000")
        second = self.image("b.png", "#0000FF")
        duplicate = self.image("same-b.png", "#0000FF")
        signals = []
        self.settings.wheelCenterChanged.connect(signals.append)
        with patch.object(
            QFileDialog, "getOpenFileNames",
            return_value=([first, second, duplicate], ""),
        ) as dialog:
            self.settings._import_wheel_center_image_file()
            self.await_batch("settings")
        self.assertEqual(dialog.call_count, 1)
        self.assertEqual(len(self.catalog()), 2, "Duplicate bytes created a second asset")
        selected = self.db.get_setting(WHEEL_CENTER_IMAGE_MEDIA_ID_KEY, "")
        self.assertTrue(selected)
        self.assertEqual(int(selected), signals[-1])
        self.assertEqual(len(signals), 1, "Batch should persist the selection once")
        self.assertEqual(int(self.settings.wheel_center_image_combo.currentData()), int(selected))
        self.assertEqual(len(self.warnings), 0)

    def test_settings_partial_failure_keeps_good_import_and_cancel_is_noop(self):
        good = self.image("valid.png", "#12AD34")
        bad = str(Path(self.temp.name) / "missing.png")
        with patch.object(
            QFileDialog, "getOpenFileNames",
            return_value=([bad, good], ""),
        ):
            self.settings._import_wheel_center_image_file()
            self.await_batch("settings")
        self.assertEqual(len(self.catalog()), 1)
        self.assertTrue(self.db.get_setting(WHEEL_CENTER_IMAGE_MEDIA_ID_KEY, ""))
        self.assertEqual(len(self.warnings), 1)
        self.assertIn("missing.png", self.warnings[0][2])
        previous = self.db.get_setting(WHEEL_CENTER_IMAGE_MEDIA_ID_KEY, "")
        with patch.object(
            QFileDialog, "getOpenFileNames",
            return_value=([], ""),
        ):
            self.settings._import_wheel_center_image_file()
        self.assertEqual(self.db.get_setting(WHEEL_CENTER_IMAGE_MEDIA_ID_KEY, ""), previous)

    def test_auction_center_picker_imports_multiple_and_closes_only_once(self):
        first = self.image("wheel-a.png", "#00FF00")
        second = self.image("wheel-b.png", "#123456")
        signals = []
        self.auction.centerImageChanged.connect(signals.append)

        class Picker:
            def __init__(self):
                self.closed = 0
                self.busy = []
            def set_busy(self, value):
                self.busy.append(bool(value))
            def close(self):
                self.closed += 1

        picker = Picker()
        self.auction._wheel_center_picker = picker
        try:
            with patch.object(
                QFileDialog, "getOpenFileNames",
                return_value=([first, second], ""),
            ) as dialog:
                self.auction._wheel_center_picker_upload()
                self.await_batch("auction")
            self.assertEqual(dialog.call_count, 1)
            self.assertEqual(len(self.catalog()), 2)
            self.assertEqual(picker.closed, 1, "Picker closed before all files imported")
            self.assertEqual(picker.busy, [True, True])
            self.assertEqual(len(signals), 1)
            self.assertEqual(
                self.db.get_setting(WHEEL_CENTER_IMAGE_MEDIA_ID_KEY, ""),
                str(signals[0]),
            )
            self.assertEqual(len(self.warnings), 0)
        finally:
            self.auction._wheel_center_picker = None

    def test_auction_all_invalid_does_not_replace_current_wheel_center(self):
        first = self.image("existing.png", "#AADDEE")
        with patch.object(
            QFileDialog, "getOpenFileNames", return_value=([first], ""),
        ):
            self.settings._import_wheel_center_image_file()
            self.await_batch("settings")
        before = self.db.get_setting(WHEEL_CENTER_IMAGE_MEDIA_ID_KEY, "")
        bad = str(Path(self.temp.name) / "absent.gif")
        signals = []
        self.auction.centerImageChanged.connect(signals.append)
        with patch.object(
            QFileDialog, "getOpenFileNames", return_value=([bad], ""),
        ):
            self.auction._wheel_center_picker_upload()
            self.await_batch("auction")
        self.assertEqual(self.db.get_setting(WHEEL_CENTER_IMAGE_MEDIA_ID_KEY, ""), before)
        self.assertEqual(signals, [])
        self.assertEqual(len(self.catalog()), 1)
        self.assertEqual(len(self.warnings), 1)


if __name__ == "__main__":
    unittest.main()
