"""Exercise target changes while a public XLSX write is already in flight."""
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic, sleep
from unittest import TestCase, main
from unittest.mock import patch

from openpyxl import Workbook, load_workbook
from PySide6.QtWidgets import QApplication, QFileDialog

from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database
from streaming_manager.views import public as ui


class PublicXlsxSwitchSmoke(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait_for(self, predicate, failure):
        deadline = monotonic() + 6
        while not predicate():
            self.app.processEvents()
            if monotonic() >= deadline:
                self.fail(failure)
            sleep(0.01)

    def run_switch(self, *, fail_old):
        with TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            root = Path(folder)
            db = Database(root / "test.db")
            tab = ui.PublicTab(db, LocalApiServer(db))
            old = root / "old.xlsx"
            new = root / "new.xlsx"
            workbook = Workbook()
            workbook.active["A1"] = "old target content"
            workbook.save(new)
            workbook.close()

            old_started, finish_old = Event(), Event()
            write = ui.write_public_xlsx
            calls = []
            statuses = []
            set_status = tab._public_xlsx_set_status

            def record_status(text, **kwargs):
                statuses.append(text)
                set_status(text, **kwargs)

            def hold_old_write(db, path):
                calls.append(path)
                if path == old:
                    old_started.set()
                    if not finish_old.wait(6):
                        raise RuntimeError("Test did not release old target")
                    if fail_old:
                        raise ui.PublicXlsxTransientError("Old target busy")
                return write(db, path)

            def select_new_target(*_):
                tab.public_xlsx_local_data_changed()
                self.wait_for(old_started.is_set, "Old write did not start during the dialog")
                return str(new), ""

            try:
                tab._public_xlsx_activate(old, persist=False, force_write=False)
                with (
                    patch.object(tab, "_public_xlsx_set_status", side_effect=record_status),
                    patch.object(ui, "write_public_xlsx", side_effect=hold_old_write),
                    patch.object(QFileDialog, "getOpenFileName", side_effect=select_new_target),
                ):
                    tab.public_xlsx_connect_btn.click()
                    self.wait_for(
                        lambda: tab._public_xlsx_write_pending and not tab._public_xlsx_write_timer.isActive(),
                        "New target was not queued while old target was still writing",
                    )
                    statuses.clear()
                    finish_old.set()
                    self.wait_for(
                        lambda: not tab._public_xlsx_write_pending and tab._public_xlsx_worker is None,
                        "New target did not settle",
                    )
                self.assertEqual(calls, [old, new])
                self.assertEqual(statuses, ["Запись таблицы…", "Синхронизировано"])
                workbook = load_workbook(new, read_only=True)
                try:
                    self.assertEqual(workbook.active["A1"].value, "ПОЗИЦИЯ")
                finally:
                    workbook.close()
            finally:
                finish_old.set()
                tab.shutdown_public_xlsx()
                tab.thread_pool.waitForDone(6000)
                self.app.processEvents()
                tab.close()

    def test_old_success_cannot_skip_replacing_new_target(self):
        self.run_switch(fail_old=False)

    def test_old_failure_does_not_set_status_or_retry_for_new_target(self):
        self.run_switch(fail_old=True)


if __name__ == "__main__":
    main()
