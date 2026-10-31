"""PERF-04: native frozen Windows graceful-exit gate (never count forced kill as PASS).

Usage: python tools/graceful_frozen_exit_smoke.py dist\\InOneLine\\InOneLine.exe
"""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request


def top_level_window_for_pid(pid: int):
    user32 = ctypes.windll.user32
    windows = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @callback_type
    def visitor(hwnd, _data):
        window_pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
        if window_pid.value == pid and user32.IsWindowVisible(hwnd):
            windows.append(hwnd)
        return True

    user32.EnumWindows(visitor, 0)
    return windows[0] if windows else None


def api_is_responding():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/api/health", timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


def port_is_closed():
    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", 8765)) != 0


def main():
    if os.name != "nt" or len(sys.argv) != 2:
        return 2
    executable = Path(sys.argv[1]).resolve()
    if not executable.is_file():
        raise FileNotFoundError(executable)

    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "windows"
    process = subprocess.Popen(
        [str(executable)], cwd=str(executable.parent), env=env,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        ready_by = time.monotonic() + 50
        hwnd = None
        while time.monotonic() < ready_by:
            if process.poll() is not None:
                raise AssertionError(f"Frozen app exited during startup: {process.returncode}")
            if api_is_responding():
                hwnd = top_level_window_for_pid(process.pid)
                if hwnd is not None:
                    break
            time.sleep(0.25)
        if hwnd is None:
            raise AssertionError("Visible native main window or API health not ready")
        if not ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0):
            raise AssertionError("Unable to post WM_CLOSE")

        # Only normal Qt closeEvent is allowed to produce PASS.
        started = time.monotonic()
        try:
            code = process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            raise AssertionError("Frozen PID still exists 15s after WM_CLOSE")
        elapsed = time.monotonic() - started
        if code != 0:
            raise AssertionError(f"Frozen app exited with status {code}")
        if not port_is_closed():
            raise AssertionError("HTTP port still occupied after frozen exit")
        print(f"PERF_GRACEFUL_FROZEN_EXIT=PASS elapsed={elapsed:.3f}s pid={process.pid}")
        return 0
    finally:
        # Only cleanup AFTER a failed gate; forced termination is NEVER success.
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
