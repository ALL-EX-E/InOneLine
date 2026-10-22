"""Issue #4/C: real Windows Qt multi-file soundtrack imports in Auction/Wheel."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from streaming_manager.constants import (
    AUCTION_SOUNDTRACK_MEDIA_ID_KEY, WHEEL_SOUNDTRACK_MEDIA_ID_KEY,
)
from streaming_manager.database import Database
from streaming_manager.media import (
    MEDIA_CATEGORY_SOUNDTRACK, MEDIA_STORAGE_MANAGED, MEDIA_STORAGE_EXTERNAL,
)
from streaming_manager.views.auction import AuctionTab


class SoundtrackBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(self.tmp.name)
        self.db = Database(root / "data" / "app.db")
        self.auction = AuctionTab(self.db)
        self.auction.show()
        self.warnings = []
        self.warnings_patch = patch.object(
            QMessageBox, "warning",
            side_effect=lambda *args: self.warnings.append(args),
        )
        self.notice_patch = patch.object(
            QMessageBox, "information", return_value=QMessageBox.Ok,
        )
        self.warnings_patch.start()
        self.notice_patch.start()
        self.root = root

    def tearDown(self):
        self.warnings_patch.stop()
        self.notice_patch.stop()
        self.auction.thread_pool.waitForDone(5000)
        self.auction.close()
        self.auction.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        self.tmp.cleanup()

    def source(self, name: str) -> Path:
        path = self.root / name
        path.write_bytes(b"fixture-audio-bytes-for-issue4c-" + name.encode())
        return path

    def assets(self):
        return self.db.sync_managed_media_category(MEDIA_CATEGORY_SOUNDTRACK)

    def find(self, file: Path):
        return self.db.media_assets_by_filename(MEDIA_CATEGORY_SOUNDTRACK, file.name)

    def wait_batch(self):
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            self.app.processEvents()
            if (self.auction._soundtrack_import_batch is None
                    and self.auction._wheel_soundtrack_copy_worker is None
                    and self.auction._auction_soundtrack_copy_worker is None):
                return
            QTest.qWait(10)
        self.fail("Batch worker timed out")

    def add(self, kind, paths, mode):
        with (
            patch.object(QFileDialog, "getOpenFileNames",
                         return_value=([str(p) for p in paths], "")) as chooser,
            patch.object(
                self.auction,
                "_choose_wheel_soundtrack_storage_mode"
                if kind == "wheel" else "_choose_auction_soundtrack_storage_mode",
                return_value=mode,
            ) as storage,
        ):
            getattr(self.auction, f"_import_{kind}_soundtrack")()
        self.assertEqual(chooser.call_count, 1)
        if paths:
            self.assertEqual(storage.call_count, 1)
            self.assertIsInstance(storage.call_args.args[0],
                                  Path if len(paths) == 1 else list)
        return storage

    def test_wheel_multiple_external_shared_catalog_one_selection(self):
        files = [self.source("w-a.mp3"), self.source("w-b.ogg"),
                 self.source("w-c.wav")]
        wheel_calls = []
        original = self.auction._wheel_soundtrack_selection_changed
        with patch.object(self.auction, "_wheel_soundtrack_selection_changed",
                          side_effect=lambda: (wheel_calls.append(1), original())):
            self.add("wheel", files, MEDIA_STORAGE_EXTERNAL)
            self.wait_batch()
        self.assertEqual(len(self.assets()), 3)
        self.assertEqual(wheel_calls, [1], "Intermediate live wheel soundtrack switch")
        chosen = self.find(files[-1])[0].id
        self.assertEqual(self.auction.wheel_soundtrack_combo.currentData(), chosen)
        self.assertEqual(self.db.get_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, ""),
                         str(chosen))
        self.assertEqual(self.db.get_setting(AUCTION_SOUNDTRACK_MEDIA_ID_KEY, ""), "")
        self.assertEqual(self.warnings, [])
        for source in files:
            self.assertEqual(self.find(source)[0].storage_mode, MEDIA_STORAGE_EXTERNAL)

    def test_auction_managed_two_audio_copies_one_selection(self):
        first = self.source("auction-one.mp3")
        second = self.source("auction-two.ogg")
        selected = []
        original = self.auction._auction_soundtrack_selection_changed
        with patch.object(self.auction, "_auction_soundtrack_selection_changed",
                          side_effect=lambda: (selected.append(1), original())):
            self.add("auction", [first, second], MEDIA_STORAGE_MANAGED)
            self.wait_batch()
        self.assertEqual(selected, [1])
        self.assertEqual(len(self.assets()), 2)
        self.assertEqual(self.auction.auction_soundtrack_combo.currentData(),
                         self.find(second)[0].id)
        self.assertEqual(self.db.get_setting(AUCTION_SOUNDTRACK_MEDIA_ID_KEY, ""),
                         str(self.find(second)[0].id))
        self.assertEqual(self.db.get_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, ""), "")
        for file in (first, second):
            self.assertEqual(self.find(file)[0].storage_mode, MEDIA_STORAGE_MANAGED)
            self.assertTrue((self.auction.soundtrack_dir / file.name).is_file())
        self.assertEqual(self.warnings, [])

    def test_repeated_wheel_external_batch_reuses_rows(self):
        files = [self.source("dedup-a.wav"), self.source("dedup-b.mp3")]
        self.add("wheel", files, MEDIA_STORAGE_EXTERNAL)
        self.add("wheel", files, MEDIA_STORAGE_EXTERNAL)
        self.assertEqual(len(self.assets()), 2)
        self.assertEqual(len(self.find(files[0])), 1)
        self.assertEqual(len(self.find(files[1])), 1)

    def test_partial_invalid_file_and_cancel_preserve_good(self):
        first = self.source("valid.mp3")
        other = self.source("unsupported.txt")
        missing = self.root / "missing.ogg"
        self.add("auction", [other, missing, first], MEDIA_STORAGE_EXTERNAL)
        self.wait_batch()
        self.assertEqual(len(self.assets()), 1)
        self.assertEqual(self.auction.auction_soundtrack_combo.currentData(),
                         self.find(first)[0].id)
        self.assertEqual(len(self.warnings), 1)
        self.assertIn("unsupported.txt", self.warnings[0][2])
        self.assertIn("missing.ogg", self.warnings[0][2])
        before = self.db.get_setting(AUCTION_SOUNDTRACK_MEDIA_ID_KEY, "")
        with patch.object(QFileDialog, "getOpenFileNames", return_value=([], "")):
            self.auction._import_auction_soundtrack()
        self.assertEqual(self.db.get_setting(AUCTION_SOUNDTRACK_MEDIA_ID_KEY, ""), before)

    def test_failed_wheel_copy_continues_and_preserves_selected_success(self):
        fail = self.source("fail.mp3")
        good = self.source("good.wav")
        original = AuctionTab._copy_wheel_soundtrack

        def broken_copy(src, dst):
            if src.name == fail.name:
                raise OSError("deliberate copy failure")
            return original(src, dst)

        with patch.object(
            AuctionTab, "_copy_wheel_soundtrack", staticmethod(broken_copy),
        ):
            self.add("wheel", [fail, good], MEDIA_STORAGE_MANAGED)
            self.wait_batch()
        self.assertFalse(self.find(fail))
        self.assertEqual(len(self.find(good)), 1)
        self.assertEqual(self.auction.wheel_soundtrack_combo.currentData(),
                         self.find(good)[0].id)
        self.assertEqual(len(self.warnings), 1)
        self.assertIn("fail.mp3", self.warnings[0][2])

    def test_single_file_import_preserved_and_shared_between_contexts(self):
        first = self.source("single.ogg")
        self.add("wheel", [first], MEDIA_STORAGE_EXTERNAL)
        self.assertEqual(len(self.assets()), 1)
        wheel_id = self.auction.wheel_soundtrack_combo.currentData()
        self.add("auction", [first], MEDIA_STORAGE_EXTERNAL)
        self.assertEqual(len(self.assets()), 1)
        self.assertEqual(wheel_id, self.auction.auction_soundtrack_combo.currentData())
        self.assertEqual(wheel_id, self.auction.wheel_soundtrack_combo.currentData())

    def test_rejected_batch_does_not_replace_active_soundtrack(self):
        first = self.source("single.wav")
        invalid = self.source("not-audio.png")
        self.add("wheel", [first], MEDIA_STORAGE_EXTERNAL)
        old_id = self.auction.wheel_soundtrack_combo.currentData()
        with (
            patch.object(QFileDialog, "getOpenFileNames",
                         return_value=([str(invalid), str(self.root / "gone.ogg")], "")),
            patch.object(QMessageBox, "warning") as warning,
        ):
            self.auction._import_wheel_soundtrack()
            self.assertEqual(warning.call_count, 1)
        self.assertEqual(old_id, self.auction.wheel_soundtrack_combo.currentData())
        self.assertEqual(len(self.assets()), 1)


if __name__ == "__main__":
    unittest.main()
