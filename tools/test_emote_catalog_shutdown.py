import threading
import time
import unittest

from streaming_manager.emote_catalog import _run_parallel_daemon


class EmoteCatalogShutdownTests(unittest.TestCase):
    def test_parallel_workers_are_daemon_threads(self):
        started = threading.Event()
        release = threading.Event()

        def blocked_worker():
            started.set()
            release.wait(2)
            return "done"

        result = _run_parallel_daemon([blocked_worker], wait_timeout=0.02)

        self.assertTrue(started.wait(0.2))
        self.assertEqual(result, [None])
        workers = [
            thread
            for thread in threading.enumerate()
            if thread.name.startswith("InOneLineEmote")
        ]
        self.assertTrue(workers)
        self.assertTrue(all(thread.daemon for thread in workers))
        release.set()
        time.sleep(0.02)


if __name__ == "__main__":
    unittest.main()
