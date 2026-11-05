"""Standalone List: zero Twitch iframes, no List animations, saved-mode changes.

The legacy main-overlay composition has a separate regression until the new
third-container behavior is fully agreed and implemented.
"""
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
from streaming_manager.database import Database, Game
from streaming_manager.constants import STATUS_NOT_PLAYED
from streaming_manager.multichat import ChatMessage, MultichatState


JS = """JSON.stringify((() => {
  const root=document.getElementById("list-composition"),
        layer=document.getElementById("list-layer"),
        panel=document.getElementById("list-panel"),
        chat=document.getElementById("list-chat");
  if (!root || !layer || !panel || !chat) return {ready:false};
  const css=getComputedStyle(panel);
  return {
    ready: true,
    shown:root.classList.contains("r06-shown"),
    listHeight:layer.getBoundingClientRect().height,
    chatHeight:chat.getBoundingClientRect().height,
    iframes:document.querySelectorAll("iframe").length,
    opacity:css.opacity,
    transform:css.transform,
    transition:css.transitionDuration,
    animation:css.animationName,
    hasTopThree:document.querySelectorAll(".top-three-row").length > 0
  };
})())"""


def port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def metrics(page):
    replies = []
    page.runJavaScript(JS, replies.append)
    timeout = time.monotonic() + 8
    while not replies and time.monotonic() < timeout:
        QTest.qWait(25)
    if not replies:
        raise AssertionError("Standalone List Chromium callback timed out")
    value = replies[0]
    return json.loads(value) if isinstance(value, str) else value


def until(page, condition, label):
    timeout = time.monotonic() + 12
    last = None
    while time.monotonic() < timeout:
        last = metrics(page)
        if last and last.get("ready") and condition(last):
            assert last["iframes"] == 0, (label, last)
            assert last["chatHeight"] <= 2, (label, last)
            assert float(last["opacity"]) >= .99, (label, last)
            assert last["transform"] == "none", (label, last)
            assert all(float(x.rstrip("s")) == 0
                       for x in last["transition"].split(", ")), (label, last)
            assert last["animation"] == "none", (label, last)
            print("R06_INDEPENDENT_LIST_PASS", label, last, flush=True)
            return
        QTest.qWait(100)
    raise AssertionError(f"{label} timed out: {last!r}")


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "list_only.db")
        db.add_game(Game(None, "QA standalone list", "2026-01-01",
                         10, 0, STATUS_NOT_PLAYED, ""))
        db.set_settings_bulk({
            "list_overlay_show_mode": "always",
            "list_slide_duration": "2",
            "list_slide_command": "!list",
            # Retained legacy settings must not affect the standalone List.
            "list_animation_seconds": "2.75",
            "list_chat_layout": "replace",
            "list_with_chat": "1",
        })
        old = db.get_settings(["list_animation_seconds",
                               "list_chat_layout", "list_with_chat"])
        state = MultichatState()
        api = LocalApiServer(db, port=port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.configure_list_show("always", "!list", 2)
        api.start()
        view = QWebEngineView()
        try:
            view.resize(390, 630)
            view.show()
            view.load(QUrl(api.base_url + "/list-overlay"))
            until(view.page(), lambda v: v["shown"] and
                  v["listHeight"] > 100 and v["hasTopThree"], "always")
            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 2)
            until(view.page(), lambda v: not v["shown"] and
                  v["listHeight"] <= 2, "hidden immediate")
            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 2)
            until(view.page(), lambda v: v["shown"] and
                  v["listHeight"] > 100, "always restored")
            db.set_setting("list_overlay_show_mode", "slide")
            api.configure_list_show("slide", "!list", 2)
            until(view.page(), lambda v: not v["shown"] and
                  v["listHeight"] <= 2, "command idle")
            assert state.ingest(ChatMessage(
                "twitch", "ch", "standalone-show", "viewer", "!list"
            ))
            until(view.page(), lambda v: v["shown"] and
                  v["listHeight"] > 100, "command visible")
            until(view.page(), lambda v: not v["shown"] and
                  v["listHeight"] <= 2, "command expiration")
            assert db.get_settings(old.keys()) == old, "Legacy values modified"
            print("R06_INDEPENDENT_LIST_BROWSER_ALL_PASS", flush=True)
        finally:
            view.close()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
