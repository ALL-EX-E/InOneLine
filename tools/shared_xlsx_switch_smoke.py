"""Serialise a selected shared-XLSX target behind an in-flight operation."""
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic, sleep
from unittest import TestCase, main
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from streaming_manager.app_paths import AppPaths
from streaming_manager.credentials import MemoryCredentialStore
from streaming_manager.database import Database
from streaming_manager.shared_xlsx import SharedXlsxError, SharedXlsxTransientError, read_shared_xlsx, write_shared_xlsx
from streaming_manager.views import auction as ui


class SharedXlsxSwitchTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait_for(self, predicate):
        deadline = monotonic() + 5
        while not predicate():
            self.app.processEvents()
            if monotonic() >= deadline:
                self.fail("Shared XLSX operation did not finish")
            sleep(0.01)

    def run_switch(self, *, create, old_error, old_write=False):
        with TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            root = Path(folder)
            paths = AppPaths.from_root(root / "app")
            paths.ensure_runtime_dirs()
            db = Database(paths.database_path, credential_store=MemoryCredentialStore())
            db.sync_main_games_state([{"title": "Local", "sm_points": 10}])
            fixture = Database(root / "fixture" / "data.db", credential_store=MemoryCredentialStore())
            old, new = root / "old.xlsx", root / "new.xlsx"
            fixture.sync_main_games_state([{"title": "Old external", "sm_points": 20}])
            write_shared_xlsx(fixture, old)
            fixture.sync_main_games_state([{"title": "New external", "sm_points": 30}])
            write_shared_xlsx(fixture, new)
            original_new = new.read_bytes()

            tab = ui.AuctionTab(db)
            tab.set_main_tab_visible(False)
            tab.auction_timer.stop()
            started, finish = Event(), Event()
            reads = []
            original_read = ui.read_shared_xlsx

            def held_read(path):
                reads.append(path)
                if path == old:
                    started.set()
                    if not finish.wait(5):
                        raise RuntimeError("Test did not release old read")
                    if old_error:
                        raise SharedXlsxError("Old workbook is invalid")
                return original_read(path)

            def held_write(db, path):
                if path == old:
                    started.set()
                    if not finish.wait(5):
                        raise RuntimeError("Test did not release old write")
                    if old_error:
                        raise SharedXlsxTransientError("Old workbook is busy")
                return write_shared_xlsx(db, path)

            def choose_target(*_):
                if old_write:
                    tab._shared_xlsx_start_write(old, connect_after=False)
                else:
                    tab._shared_xlsx_start_import(tab._shared_xlsx_signature(old))
                self.wait_for(started.is_set)
                tab.shared_xlsx_local_data_changed()
                return str(new), ""

            try:
                tab._shared_xlsx_activate(old, persist=False, import_now=False)
                with (
                    patch.object(ui, "read_shared_xlsx", side_effect=held_read),
                    patch.object(ui, "write_shared_xlsx", side_effect=held_write),
                    patch.object(QFileDialog, "getOpenFileName", side_effect=choose_target),
                    patch.object(QFileDialog, "getSaveFileName", side_effect=choose_target),
                    patch.object(QMessageBox, "question", return_value=QMessageBox.Yes),
                ):
                    if create:
                        tab._shared_xlsx_create()
                    else:
                        tab._shared_xlsx_connect()
                    finish.set()
                    if not create:
                        self.wait_for(lambda: new in reads)
                    self.wait_for(lambda: tab._shared_xlsx_worker is None)
                    # Drain the existing debounce/force-import callbacks too.
                    self.wait_for(
                        lambda: not tab._shared_xlsx_write_timer.isActive()
                        and tab._shared_xlsx_worker is None
                    )
                    self.assertEqual(tab._shared_xlsx_path, new)
                    self.assertIsNone(tab._shared_xlsx_failed_signature)
                    if create:
                        titles = [row["title"] for row in read_shared_xlsx(new)["rows"]]
                        self.assertEqual(titles, ["Local" if old_error or old_write else "Old external"])
                    else:
                        self.assertEqual(reads, [new] if old_write else [old, new])
                        self.assertEqual([g.title for g in db.list_games()], ["New external"])
                        self.assertEqual(new.read_bytes(), original_new)
            finally:
                finish.set()
                tab.shutdown_shared_xlsx()
                tab.shutdown_audio()
                tab.thread_pool.waitForDone(6000)
                self.app.processEvents()
                tab.close()

    def test_connect_after_old_read_succeeds(self):
        self.run_switch(create=False, old_error=False)

    def test_connect_after_old_read_fails(self):
        self.run_switch(create=False, old_error=True)

    def test_create_after_old_read_succeeds(self):
        self.run_switch(create=True, old_error=False)

    def test_create_after_old_read_fails(self):
        self.run_switch(create=True, old_error=True)

    def test_connect_after_old_write_succeeds(self):
        self.run_switch(create=False, old_error=False, old_write=True)

    def test_connect_after_old_write_needs_retry(self):
        self.run_switch(create=False, old_error=True, old_write=True)

    def test_create_after_old_write_succeeds(self):
        self.run_switch(create=True, old_error=False, old_write=True)

    def test_create_after_old_write_needs_retry(self):
        self.run_switch(create=True, old_error=True, old_write=True)

    def test_local_change_during_create_is_written_to_new_target(self):
        with TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            root = Path(folder)
            paths = AppPaths.from_root(root / "app")
            paths.ensure_runtime_dirs()
            db = Database(paths.database_path, credential_store=MemoryCredentialStore())
            db.sync_main_games_state([{"title": "Before create", "sm_points": 10}])
            old, new = root / "old.xlsx", root / "new.xlsx"
            write_shared_xlsx(db, old)
            tab = ui.AuctionTab(db)
            tab.set_main_tab_visible(False)
            tab.auction_timer.stop()
            saved, finish = Event(), Event()
            writes = []

            def held_create(db, path):
                result = write_shared_xlsx(db, path)
                writes.append(path)
                if path == new and len(writes) == 1:
                    saved.set()
                    if not finish.wait(5):
                        raise RuntimeError("Test did not release create result")
                return result

            try:
                tab._shared_xlsx_activate(old, persist=False, import_now=False)
                with patch.object(ui, "write_shared_xlsx", side_effect=held_create):
                    tab._shared_xlsx_switch_target(new, create=True)
                    self.wait_for(saved.is_set)
                    db.sync_main_games_state([
                        {"title": "Edited during create", "sm_points": 20}
                    ])
                    tab.shared_xlsx_local_data_changed()
                    finish.set()
                    self.wait_for(
                        lambda: writes == [new, new]
                        and tab._shared_xlsx_worker is None
                        and not tab._shared_xlsx_write_timer.isActive()
                    )
                    self.assertEqual(tab._shared_xlsx_path, new)
                    self.assertEqual([g.title for g in db.list_games()], ["Edited during create"])
                    self.assertEqual(
                        [row["title"] for row in read_shared_xlsx(new)["rows"]],
                        ["Edited during create"],
                    )
                    self.assertEqual(
                        [row["title"] for row in read_shared_xlsx(old)["rows"]],
                        ["Before create"],
                    )
            finally:
                finish.set()
                tab.shutdown_shared_xlsx()
                tab.shutdown_audio()
                tab.thread_pool.waitForDone(6000)
                self.app.processEvents()
                tab.close()


if __name__ == "__main__":
    main()
