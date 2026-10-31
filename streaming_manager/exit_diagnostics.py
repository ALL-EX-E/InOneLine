"""Opt-in PERF-01 exit instrumentation for the unresponsive Windows PID.

Never captures local variables, chat messages, credentials, thread arguments,
or complete paths. No changes to shutdown behavior or task scheduling.
Enabled only by INONELINE_EXIT_TRACE=1 on the parent GUI process.
"""
from __future__ import annotations

import atexit
import json
import os
import sys
import threading
import time
import traceback
from pathlib import Path


_CHECKPOINTS = (1.0, 3.0, 8.0, 15.0, 30.0, 60.0, 90.0)


def _thread_snapshot() -> list[dict]:
    frames = sys._current_frames()
    result = []
    for thread in threading.enumerate():
        frame = frames.get(thread.ident)
        # Only source basename / function / line: never serialize raw data.
        stack = traceback.extract_stack(frame, limit=14) if frame is not None else ()
        result.append({
            "name": thread.name[:80],
            "daemon": bool(thread.daemon),
            "alive": bool(thread.is_alive()),
            "stack": [
                {
                    "file": Path(item.filename).name[:80],
                    "function": item.name[:80],
                    "line": int(item.lineno),
                }
                for item in stack[-12:]
            ],
        })
    return result[:80]


class ExitTrace:
    def __init__(self, logs_dir: Path):
        self.path = logs_dir / "exit_trace.jsonl"
        self._lock = threading.Lock()
        self._start = time.monotonic()
        self._close_start = None
        self._stop = threading.Event()
        self._worker = None
        self.mark("trace_enabled")
        atexit.register(self._at_exit)

    def mark(self, event: str):
        elapsed = round(time.monotonic() - self._start, 3)
        with self._lock:
            if event == "close_accepted" and self._close_start is None:
                self._close_start = time.monotonic()
            row = {"event": event, "elapsed_s": elapsed, "pid": os.getpid()}
            self._write(row)
        if event == "close_accepted" and self._worker is None:
            self._worker = threading.Thread(
                target=self._monitor, name="IOL-ExitTrace",
                daemon=True,
            )
            self._worker.start()

    def _write(self, row: dict):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as out:
                out.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        except OSError:
            pass

    def _monitor(self):
        for deadline in _CHECKPOINTS:
            start = self._close_start
            if start is None:
                return
            remaining = max(0.0, deadline - (time.monotonic() - start))
            if self._stop.wait(remaining):
                return
            try:
                snapshots = _thread_snapshot()
                row = {
                    "event": "still_running",
                    "after_close_s": round(time.monotonic() - start, 3),
                    "pid": os.getpid(),
                    "python_threads": snapshots,
                }
                with self._lock:
                    self._write(row)
            except Exception:
                # Diagnostics must never interfere with normal application exit.
                continue

    def _at_exit(self):
        self.mark("atexit")
        self._stop.set()
