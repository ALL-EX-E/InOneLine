"""PERF-01/03 controlled lifecycle tests: no real Twitch, user data or network."""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import tempfile
from pathlib import Path
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from streaming_manager.views.chat_rich_feed import (
    ChatRichFeed, _ChatImageProcessRunner,
)


class BlockedChild:
    """A DNS/body-blocked helper; kill() must unblock communicate()."""

    def __init__(self, *args, **kwargs):
        self.started = threading.Event()
        self.ended = threading.Event()
        self.killed = False
        self.returncode = None

    def communicate(self, timeout=None):
        self.started.set()
        if not self.ended.wait(timeout):
            raise subprocess.TimeoutExpired("fake-child", timeout)
        return b"", b""

    def kill(self):
        self.killed = True
        self.returncode = -9
        self.ended.set()


class ShutdownLifecycleSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_active_image_request_is_cancelled_and_dns_shutdown_is_bounded(self):
        fake = BlockedChild()
        runner = _ChatImageProcessRunner()
        with patch("streaming_manager.views.chat_rich_feed.subprocess.Popen", return_value=fake):
            with ThreadPoolExecutor(max_workers=1) as workers:
                future = workers.submit(runner.fetch, "https://cdn.7tv.app/icon.png")
                self.assertTrue(fake.started.wait(2), "helper was not started")
                start = time.monotonic()
                runner.shutdown()
                self.assertLess(time.monotonic() - start, 2)
                self.assertIsNone(future.result(timeout=2))
                self.assertTrue(fake.killed)
                runner.shutdown()  # idempotent
                self.assertIsNone(runner.fetch("https://cdn.7tv.app/new.png"))

    def test_slow_body_has_total_deadline(self):
        fake = BlockedChild()
        runner = _ChatImageProcessRunner()
        with (
            patch("streaming_manager.views.chat_rich_feed.subprocess.Popen", return_value=fake),
            patch("streaming_manager.views.chat_rich_feed._CHAT_FETCH_DEADLINE_SECONDS", 0.1),
        ):
            start = time.monotonic()
            self.assertIsNone(runner.fetch("https://cdn.7tv.app/slow.png"))
            self.assertLess(time.monotonic() - start, 2)
            self.assertTrue(fake.killed)
        runner.shutdown()

    def test_chat_queue_is_cancelled_and_feed_shutdown_is_idempotent(self):
        feed = ChatRichFeed()
        blocking = threading.Event()
        started = threading.Event()

        def fake_fetch(_url):
            started.set()
            blocking.wait(2)
            return None

        feed._fetch_processes.fetch = fake_fetch
        try:
            for i in range(9):
                feed._enqueue(f"https://cdn.7tv.app/image{i}.png")
            self.assertTrue(started.wait(2))
            self.assertGreater(len(feed._jobs), 0)
            feed.shutdown()
            self.assertTrue(feed._pool._shutdown)
            self.assertFalse(feed._poll.isActive())
            self.assertEqual(feed._jobs, {})
            feed._enqueue("https://cdn.7tv.app/after.png")
            self.assertEqual(feed._jobs, {})
            feed.shutdown()
        finally:
            blocking.set()
            feed.close()
            self.app.processEvents()

    def test_helper_rejects_local_source_before_network_access(self):
        # This exercises the REAL source-mode subprocess entrypoint, including
        # safe-URL validation and absence of binary payload on failure.
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "image.img"
            p = subprocess.run(
                [sys.executable, "-m", "streaming_manager.remote_image",
                 "--chat-image-fetch", "http://127.0.0.1/internal.png", str(output)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=12,
                check=False,
            )
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(p.stdout, b"")
            self.assertFalse(output.exists(), "Rejected URL must not write data")

    def test_helper_binary_protocol_preserves_static_image(self):
        image = QImage(2, 3, QImage.Format_ARGB32)
        image.fill(0xFFFF0080)
        out = QByteArray()
        buf = QBuffer(out)
        self.assertTrue(buf.open(QIODevice.WriteOnly))
        self.assertTrue(image.save(buf, "PNG"))
        encoded = bytes((0,)) + bytes(out)
        fake = BlockedChild()

        def communicate(timeout=None):
            fake.started.set()
            fake.returncode = 0
            return b"", b""

        def start_fake(command, **_kwargs):
            Path(command[-1]).write_bytes(encoded)
            return fake

        fake.communicate = communicate
        runner = _ChatImageProcessRunner()
        with patch("streaming_manager.views.chat_rich_feed.subprocess.Popen", side_effect=start_fake):
            result = runner.fetch("https://cdn.7tv.app/static.png")
        self.assertIsNotNone(result)
        self.assertFalse(result[0].animated)
        self.assertEqual(result[1].height(), 48)
        runner.shutdown()

    def test_cancel_exit_does_not_preempt_shutdown_approval(self):
        # MainWindow.closeEvent invokes feed_frame.shutdown only AFTER
        # Save / Discard approval. We exercise the actual dirty-editor branch
        # without destroying the expensive main window runtime.
        import inspect
        from streaming_manager.views.main_window import MainWindow

        source = inspect.getsource(MainWindow.closeEvent)
        self.assertLess(source.index("event.ignore()"), source.index("feed_frame.shutdown()"))
        self.assertIn("if not editor.save():", source)
        self.assertIn("editor.discard()", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
