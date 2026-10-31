"""PERF-02A: shutdown admission + in-flight file write integrity.

No real Twitch credentials, cloud files or user database are touched.
"""
from __future__ import annotations

import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication

from streaming_manager.views.main_window import MainWindow
from streaming_manager.views.public import PublicTab
from streaming_manager.views.auction import AuctionTab
from streaming_manager.workers import FunctionWorker


class StubTimer:
    def __init__(self):
        self.starts = []
        self.stops = 0

    def start(self, value=None):
        self.starts.append(value)

    def stop(self):
        self.stops += 1


class StubPool:
    def __init__(self):
        self.jobs = []

    def start(self, worker):
        self.jobs.append(worker)


class WorkerLifecycleSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_accepted_exit_blocks_deferred_backup_and_health(self):
        pool = StubPool()
        db = SimpleNamespace(
            get_integration_connection=lambda name: {"enabled": True, "status": "connected"},
            backup_isolated=lambda folder: "existing.db",
            prune_backups=lambda *args: None,
        )
        obj = SimpleNamespace(
            _exit_accepted=True,
            _startup_backup_worker=None,
            _integration_health_worker=None,
            thread_pool=pool,
            db=db,
            paths=SimpleNamespace(backups_dir=Path(tempfile.gettempdir())),
            integration_registry=SimpleNamespace(adapters=lambda: [SimpleNamespace(service_key="twitch")]),
            integration_manager=SimpleNamespace(check_connection=lambda _key: True),
        )
        MainWindow._startup_backup(obj)
        MainWindow._validate_active_integrations(obj)
        self.assertEqual(pool.jobs, [])
        self.assertIsNone(obj._startup_backup_worker)
        self.assertIsNone(obj._integration_health_worker)

    def test_open_lifecycle_allows_existing_backup(self):
        pool = StubPool()
        operations = []
        db = SimpleNamespace(
            backup_isolated=lambda folder: operations.append("backup") or "snapshot.db",
            prune_backups=lambda *args: operations.append("prune"),
        )
        obj = SimpleNamespace(
            _exit_accepted=False, _startup_backup_worker=None,
            db=db, paths=SimpleNamespace(backups_dir=Path(tempfile.gettempdir())),
            thread_pool=pool, _startup_backup_finished=lambda: None,
        )
        MainWindow._startup_backup(obj)
        self.assertEqual(len(pool.jobs), 1)
        pool.jobs[0].run()
        self.assertEqual(operations, ["backup", "prune"])

    def test_closed_health_callback_does_not_update_ui(self):
        obj = SimpleNamespace(
            _exit_accepted=True,
            settings_tab=SimpleNamespace(_refresh_integrations=lambda: self.fail("settings refreshed")),
            auction_tab=SimpleNamespace(refresh_integration_status=lambda: self.fail("auction refreshed")),
            twitch_eventsub_runtime=SimpleNamespace(wake=lambda: self.fail("Twitch woken")),
        )
        MainWindow._integration_health_done(obj)

    def test_public_finished_after_shutdown_never_reschedules(self):
        timer, poll = StubTimer(), StubTimer()
        obj = SimpleNamespace(
            _public_xlsx_shutdown=False,
            _public_xlsx_worker=object(),
            _public_xlsx_write_timer=timer, _public_xlsx_missing_timer=poll,
            _public_xlsx_write_pending=True,
            _public_xlsx_path=Path("test.xlsx"),
        )
        PublicTab.shutdown_public_xlsx(obj)
        self.assertEqual(timer.stops, 1)
        self.assertEqual(poll.stops, 1)
        PublicTab._public_xlsx_worker_finished(obj)
        self.assertIsNone(obj._public_xlsx_worker)
        self.assertEqual(timer.starts, [])

    def test_shared_finished_after_shutdown_never_reschedules(self):
        timer, poll = StubTimer(), StubTimer()
        obj = SimpleNamespace(
            _shared_xlsx_shutdown=False,
            _shared_xlsx_worker=object(), _shared_xlsx_worker_kind="import",
            _shared_xlsx_write_timer=timer, _shared_xlsx_poll_timer=poll,
            _shared_xlsx_write_pending=True,
            _shared_xlsx_path=Path("test.xlsx"),
        )
        AuctionTab.shutdown_shared_xlsx(obj)
        AuctionTab._shared_xlsx_worker_finished(obj)
        self.assertIsNone(obj._shared_xlsx_worker)
        self.assertEqual(obj._shared_xlsx_worker_kind, "")
        self.assertEqual(timer.starts, [])
        # Already deferred QTimer.singleShot() import must also be blocked.
        AuctionTab._shared_xlsx_force_import(obj)
        AuctionTab._shared_xlsx_start_import(obj, (10, 20))
        self.assertEqual(timer.starts, [])

    def test_active_file_write_finishes_without_queue_clear(self):
        """A running, confirmed write must reach os.replace after shutdown."""
        pool = QThreadPool()
        pool.setMaxThreadCount(1)
        started, release, completed = threading.Event(), threading.Event(), threading.Event()
        try:
            with tempfile.TemporaryDirectory() as folder:
                target = Path(folder) / "state.xlsx"
                target.write_bytes(b"before")

                def atomic_write():
                    temp = target.with_suffix(".pending")
                    temp.write_bytes(b"after-complete")
                    started.set()
                    if not release.wait(5):
                        raise TimeoutError("test release was not delivered")
                    os.replace(temp, target)
                    completed.set()
                    return str(target)

                worker = FunctionWorker(atomic_write)
                pool.start(worker)
                self.assertTrue(started.wait(3), "write did not start")
                # Equivalent to the actual PublicTab close sequence; it only
                # stops the scheduling timers, never the active QThreadPool.
                obj = SimpleNamespace(
                    _public_xlsx_shutdown=False,
                    _public_xlsx_worker=worker,
                    _public_xlsx_write_timer=StubTimer(),
                    _public_xlsx_missing_timer=StubTimer(),
                )
                PublicTab.shutdown_public_xlsx(obj)
                self.assertTrue(target.exists())
                release.set()
                self.assertTrue(pool.waitForDone(5000), "active write was interrupted")
                self.assertTrue(completed.is_set())
                self.assertEqual(target.read_bytes(), b"after-complete")
        finally:
            release.set()
            pool.waitForDone(5000)

    def test_cancel_and_failed_save_do_not_close_admission(self):
        import inspect

        text = inspect.getsource(MainWindow.closeEvent)
        self.assertLess(text.index("event.ignore()"), text.index("self._exit_accepted = True"))
        self.assertLess(text.index("if not editor.save():"), text.index("self._exit_accepted = True"))
        self.assertLess(text.index("editor.discard()"), text.index("self._exit_accepted = True"))
        self.assertNotIn("thread_pool.clear()", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
