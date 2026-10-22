"""Issue #4/B: native Ctrl/Shift batch backgrounds, preserving shared D26 media."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QWidget

from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database
from streaming_manager.media import (
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, MEDIA_STORAGE_EXTERNAL,
    MEDIA_STORAGE_MANAGED,
)
from streaming_manager.views.stream import StreamTab


class BackgroundMultiFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(self.temp.name)
        self.db = Database(root / "data" / "app.db")
        self.api = LocalApiServer(self.db, port=0)
        self.stream = StreamTab(self.db, self.api)
        self.stream.show()
        self.messages = []
        self.warning = patch.object(
            QMessageBox, "warning",
            side_effect=lambda *args: self.messages.append(args),
        )
        self.notice = patch.object(QMessageBox, "information", return_value=QMessageBox.Ok)
        self.warning.start()
        self.notice.start()

    def tearDown(self):
        self.warning.stop()
        self.notice.stop()
        self.stream.thread_pool.waitForDone(5000)
        self.stream.close()
        self.stream.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        self.api.stop()
        self.temp.cleanup()

    def image(self, name, color="#1248AB"):
        source = Path(self.temp.name) / name
        image = QImage(20, 20, QImage.Format.Format_ARGB32)
        image.fill(QColor(color))
        self.assertTrue(image.save(str(source)))
        return source

    def video(self, name):
        source = Path(self.temp.name) / name
        source.write_bytes(b"issue4-native-regression-video-copy")
        return source

    def get_assets(self):
        return self.db.sync_managed_media_category(MEDIA_CATEGORY_OVERLAY_BACKGROUNDS)

    def by_filename(self, path):
        return self.db.media_assets_by_filename(
            MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, path.name,
        )

    def import_paths(self, target, paths, storage):
        with (
            patch.object(
                QFileDialog, "getOpenFileNames",
                return_value=([str(p) for p in paths], ""),
            ) as chooser,
            patch.object(
                self.stream, "_choose_background_storage_mode",
                return_value=storage,
            ) as choice,
        ):
            self.stream._import_background_media_for(target)
        self.assertEqual(chooser.call_count, 1)
        if paths:
            self.assertEqual(choice.call_count, 1)
            self.assertIsInstance(
                choice.call_args.args[0],
                Path if len(paths) == 1 else list,
            )
        return choice

    def await_batch(self):
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            self.app.processEvents()
            if (
                self.stream._background_import_batch is None
                and self.stream._background_copy_worker is None
            ):
                return
            QTest.qWait(15)
        self.fail("Batch/video worker did not complete")

    def test_main_managed_all_files_registered_once_and_last_selected(self):
        first = self.image("background-a.png", "#AA0011")
        second = self.image("background-b.png", "#00AB22")
        third = self.image("background-c.webp", "#3322AA")
        self.import_paths("main", [first, second, third], MEDIA_STORAGE_MANAGED)
        self.await_batch()
        self.assertEqual(len(self.get_assets()), 3)
        for source in (first, second, third):
            rows = self.by_filename(source)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].storage_mode, MEDIA_STORAGE_MANAGED)
            self.assertTrue(
                (self.stream.background_dir / rows[0].managed_name).is_file()
            )
            self.assertGreaterEqual(
                self.stream.timer_background_combo.findData(rows[0].id), 0,
            )
        self.assertEqual(
            self.stream.background_combo.currentData(),
            self.by_filename(third)[0].id,
        )
        self.assertEqual(self.messages, [])

    def test_auction_lots_external_dedup_does_not_move_main_choice(self):
        main = self.image("main-first.png")
        first = self.image("lot-a.png", "#11AA22")
        second = self.image("lot-b.png", "#2211AA")
        self.import_paths("main", [main], MEDIA_STORAGE_MANAGED)
        main_id = self.stream.background_combo.currentData()
        self.import_paths(
            "auction_lots", [first, second], MEDIA_STORAGE_EXTERNAL,
        )
        self.await_batch()
        selected = self.stream.auction_lots_background_combo.currentData()
        self.assertEqual(selected, self.by_filename(second)[0].id)
        self.assertEqual(self.stream.background_combo.currentData(), main_id)
        self.import_paths(
            "auction_lots", [first, second], MEDIA_STORAGE_EXTERNAL,
        )
        self.await_batch()
        self.assertEqual(len(self.get_assets()), 3)
        self.assertEqual(
            self.stream.auction_lots_background_combo.currentData(), selected,
        )
        self.assertEqual(self.by_filename(first)[0].storage_mode, MEDIA_STORAGE_EXTERNAL)
        self.assertEqual(self.messages, [])

    def test_timer_two_async_videos_save_only_final_selected(self):
        first = self.video("timer-one.mp4")
        second = self.video("timer-two.webm")
        self.stream.timer_background_media_mode.setChecked(True)
        self.import_paths("timer", [first, second], MEDIA_STORAGE_MANAGED)
        self.assertIsNotNone(self.stream._background_copy_worker)
        self.stream._save_timer_overlay_settings()
        self.assertTrue(self.stream._timer_save_waiting_for_video_copy)
        self.await_batch()
        self.assertEqual(len(self.by_filename(first)), 1)
        self.assertEqual(len(self.by_filename(second)), 1)
        selected_id = self.by_filename(second)[0].id
        self.assertEqual(self.stream.timer_background_combo.currentData(), selected_id)
        self.assertEqual(
            self.db.get_setting("timer_overlay_background_media_id", ""),
            str(selected_id),
        )
        self.assertEqual(self.messages, [])

    def test_rules_images_call_editor_selection_once_and_reject_gif(self):
        first = self.image("rules-a.png", "#CC4422")
        gif = self.video("rules-forbidden.gif")
        second = self.image("rules-b.png", "#0088AA")
        owner = QWidget()
        owner.show()
        selected = []
        try:
            with (
                patch.object(
                    QFileDialog, "getOpenFileNames",
                    return_value=([str(first), str(gif), str(second)], ""),
                ),
                patch.object(
                    self.stream, "_choose_background_storage_mode",
                    return_value=MEDIA_STORAGE_MANAGED,
                ),
            ):
                self.stream.import_rules_background_media(selected.append, owner)
            self.await_batch()
            self.assertEqual(len(self.get_assets()), 2)
            self.assertEqual(selected, [self.by_filename(second)[0].id])
            self.assertFalse(self.by_filename(gif))
            self.assertEqual(self.stream.background_combo.currentData(), "")
            self.assertEqual(self.messages.__len__(), 1)
            self.assertIn(gif.name, self.messages[0][2])
        finally:
            owner.close()
            owner.deleteLater()
            self.app.processEvents()

    def test_cancel_preserves_current_and_one_file_still_works(self):
        source = self.image("single.png")
        self.import_paths("main", [source], MEDIA_STORAGE_EXTERNAL)
        before = self.stream.background_combo.currentData()
        with patch.object(QFileDialog, "getOpenFileNames", return_value=([], "")):
            self.stream._import_background_media_for("main")
        self.assertEqual(self.stream.background_combo.currentData(), before)
        self.assertEqual(len(self.get_assets()), 1)
        self.assertEqual(self.messages, [])

    def test_video_copy_failure_continues_to_next_video(self):
        first = self.video("copy-fail.mp4")
        second = self.video("copy-ok.webm")
        original_copy = StreamTab._copy_background_video

        def fail_one(source, target):
            if source.name == first.name:
                raise OSError("Simulated video copy failure")
            return original_copy(source, target)

        with patch.object(
            StreamTab, "_copy_background_video", staticmethod(fail_one),
        ):
            self.import_paths("main", [first, second], MEDIA_STORAGE_MANAGED)
            self.await_batch()
        self.assertFalse(self.by_filename(first))
        self.assertEqual(len(self.by_filename(second)), 1)
        self.assertEqual(
            self.stream.background_combo.currentData(),
            self.by_filename(second)[0].id,
        )
        self.assertEqual(len(self.messages), 1)
        self.assertIn(first.name, self.messages[0][2])


if __name__ == "__main__":
    unittest.main()
