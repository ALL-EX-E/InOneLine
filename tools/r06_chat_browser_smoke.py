"""R06 FIX1: actual Chromium chat/list geometry across both existing OBS URLs."""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "windows")
if sys.platform != "win32":
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")

from PySide6.QtCore import QUrl
from PySide6.QtTest import QTest
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database
from streaming_manager.multichat import ChatMessage, MultichatState


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def evaluate(page, expression):
    values = []
    page.runJavaScript(expression, values.append)
    end = time.monotonic() + 8
    while not values and time.monotonic() < end:
        QTest.qWait(25)
    if not values:
        raise AssertionError("Chromium JS callback timed out: " + expression)
    value = values[0]
    if expression.startswith("JSON.stringify") and isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    return value


CHAT_METRICS = """JSON.stringify((() => {
  const chat = document.getElementById('list-chat');
  const doc = chat?.querySelector('iframe')?.contentDocument;
  const cards = doc?.getElementById('messages');
  const panel = document.getElementById('list-panel');
  if (!chat || !panel) return {
    ready: document.readyState, href: location.href, panel: !!panel,
    height: -1, count: -1, transition: 0, replace: false, shown: false
  };
  return {
    ready: document.readyState, href: location.href, panel: true,
    height: Math.round(chat?.getBoundingClientRect().height || 0),
    count: cards?.children.length ?? -1,
    transition: parseFloat(getComputedStyle(panel).transitionDuration) || 0,
    replace: document.getElementById('list-composition')?.classList.contains('r06-replace'),
    shown: document.getElementById('list-composition')?.classList.contains('r06-shown'),
  };
})())"""


def until(page, predicate, label, timeout=50):
    end = time.monotonic() + timeout
    latest = None
    last_log = 0
    while time.monotonic() < end:
        latest = evaluate(page, CHAT_METRICS)
        if isinstance(latest, str) and latest.startswith("{"):
            latest = json.loads(latest)
        if latest and isinstance(latest, dict) and predicate(latest):
            print("R06_BROWSER_PASS:", label, latest, flush=True)
            return latest
        if time.monotonic() - last_log > 6:
            print("R06_BROWSER_WAIT:", label, "url=", page.url().toString(),
                  "state=", latest, flush=True)
            last_log = time.monotonic()
        QTest.qWait(120)
    raise AssertionError(f"{label}: timed out, last result {latest!r}")


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
        db = Database(Path(temporary) / "r06_browser.db")
        db.set_settings_bulk({
            "list_overlay_show_mode": "always",
            "list_slide_direction": "right",
            "list_slide_duration": "30",
            "list_animation_seconds": "1.50",
            "list_slide_command": "!list",
            "list_chat_layout": "split",
            "list_with_chat": "1",
        })
        state = MultichatState()
        api = LocalApiServer(db, port=free_port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.configure_list_show("always", "!list", 30)
        api.start()
        views = []
        try:
            screen = app.primaryScreen().availableGeometry()
            for i, (route, width) in enumerate((("/overlay", 1000), ("/list-overlay", 380))):
                view = QWebEngineView()
                view.resize(width, 620)
                view.move(screen.x() + 5 + i * 100, screen.y() + 5 + i * 35)
                view.loadFinished.connect(
                    lambda ok, source=route: print("R06_BROWSER_LOAD:", source, ok, flush=True)
                )
                view.renderProcessTerminated.connect(
                    lambda status, code, source=route: print(
                        "R06_BROWSER_RENDER_EXIT:", source, status, code, flush=True)
                )
                view.show()
                view.load(QUrl(api.base_url + route))
                views.append(view)
                app.processEvents()
                QTest.qWait(400)
                print("R06_BROWSER_DIAGNOSTIC:", route, "url", view.page().url().toString(),
                      "math", evaluate(view.page(), "2+2"),
                      "ready", evaluate(view.page(), "document.readyState"),
                      "panel", evaluate(view.page(),
                                        "!!document.getElementById('list-panel')"),
                      flush=True)
                until(view.page(), lambda m: m["panel"] and m["count"] == 0 and m["height"] == 0,
                      "Empty chat releases entire area in " + route)
            pages = [view.page() for view in views]

            state.ingest(ChatMessage("twitch", "chan", "first", "alice", "short message"))
            first_heights = []
            for p in pages:
                metrics = until(p, lambda m: m["count"] == 1 and m["height"] >= 40,
                                "One message has natural height")
                assert abs(metrics["transition"] - 1.5) < 0.03, metrics
                first_heights.append(metrics["height"])

            for i in range(2, 5):
                state.ingest(ChatMessage("twitch", "chan", str(i), "viewer",
                    "Additional text to make the card taller and validate dynamic layout"))
            for idx, p in enumerate(pages):
                metrics = until(p, lambda m: m["count"] == 4 and
                                m["height"] > first_heights[idx] + 18,
                                "More messages grow chat in " + str(idx))
                heights = []
                for _ in range(5):
                    QTest.qWait(500)
                    heights.append(evaluate(p, CHAT_METRICS)["height"])
                assert max(heights) - min(heights) <= 3, (
                    "Chat panel flickers/oscillates", heights
                )
                print("R06_BROWSER_PASS: stable height", heights, flush=True)

            # Same saved composition mode in both URLs; an active slide
            # replaces chat, returning to split restores intrinsic sizing.
            db.set_setting("list_overlay_show_mode", "slide")
            db.set_setting("list_chat_layout", "replace")
            api.configure_list_show("slide", "!list", 30)
            state.ingest(ChatMessage("twitch", "chan", "trigger", "alice", "!list"))
            for p in pages:
                until(p, lambda m: m["replace"] and m["shown"],
                      "Slide replaces chat in both layouts")
            db.set_setting("list_chat_layout", "split")
            for p in pages:
                until(p, lambda m: not m["replace"] and m["shown"] and m["height"] > 40,
                      "Return to split without resetting active list")

            state.set_obs_enabled("twitch", False)
            for p in pages:
                until(p, lambda m: m["height"] == 0,
                      "Global OBS chat toggle releases area")
            state.set_obs_enabled("twitch", True)
            state.ingest(ChatMessage("twitch", "chan", "fresh", "alice", "new only"))
            for p in pages:
                until(p, lambda m: m["count"] == 1 and m["height"] >= 40,
                      "Fresh history after re-enabling chat")
            print("R06_BROWSER_FIX1_PASS", flush=True)
        finally:
            for v in views:
                v.close()
                v.deleteLater()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
