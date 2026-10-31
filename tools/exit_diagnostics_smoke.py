"""PERF-01 diagnostic logging regression: opt-in, no sensitive values."""
from __future__ import annotations

import atexit
import json
import tempfile
import time
import unittest
from pathlib import Path

from streaming_manager.exit_diagnostics import ExitTrace, _thread_snapshot


class ExitDiagnosticsSmoke(unittest.TestCase):
    def test_events_and_redacted_stacks(self):
        with tempfile.TemporaryDirectory() as temp:
            trace = ExitTrace(Path(temp))
            trace.mark("close_accepted")
            trace.mark("chat_stopped")
            trace.mark("qt_exec_returned")
            # Ensure the 1-second watchdog checkpoint is emitted.
            time.sleep(1.1)
            trace._at_exit()
            atexit.unregister(trace._at_exit)
            rows = [json.loads(line) for line in trace.path.read_text(
                encoding="utf-8"
            ).splitlines()]
            names = [row["event"] for row in rows]
            self.assertIn("trace_enabled", names)
            self.assertIn("close_accepted", names)
            self.assertIn("qt_exec_returned", names)
            self.assertIn("atexit", names)
            self.assertIn("still_running", names)
            self.assertLess(names.index("close_accepted"), names.index("qt_exec_returned"))
            self.assertTrue(rows[0]["pid"] > 0)
            snapshot = next(row for row in rows if row["event"] == "still_running")
            self.assertGreaterEqual(snapshot["after_close_s"], 1)
            for thread in snapshot["python_threads"]:
                self.assertIn("name", thread)
                self.assertIn("daemon", thread)
                for frame in thread["stack"]:
                    self.assertFalse("/" in frame["file"])
                    self.assertFalse("\\" in frame["file"])
                    self.assertEqual(set(frame), {"file", "function", "line"})

    def test_no_shutdown_when_disabled(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.get("INONELINE_EXIT_TRACE") == "1"', source)
        self.assertIn("return app.exec()", source)
        self.assertNotIn("sys.exit(0)", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
