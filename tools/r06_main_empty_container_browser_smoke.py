"""R06: empty combined List/Twitch source must unmount from main OBS.

Real Chromium regression for the accepted hide-empty/slide/idle rules.
Independent list/chat URLs and command timer behavior are unchanged.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

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
from streaming_manager.constants import STATUS_NOT_PLAYED
from streaming_manager.database import Database, Game
from streaming_manager.multichat import ChatMessage, MultichatState


JS = """JSON.stringify((() => {
  const root=document.getElementById('list-composition'),
        list=document.getElementById('list-layer'),
        chat=document.getElementById('list-chat'),
        cam=document.getElementById('webcam-frame'),
        info=document.getElementById('info-panel'),
        game=document.getElementById('game-frame'),
        mask=document.getElementById('overlay-cutout-mask');
  if (!root || !list || !chat || !cam || !info || !game || !mask) {
    return {ready:false};
  }
  const lr=list.getBoundingClientRect(), cr=chat.getBoundingClientRect(),
        rr=root.getBoundingClientRect(), gr=game.getBoundingClientRect();
  return {
    ready: document.documentElement.dataset.obsPolicyReady === 'true',
    parent:root.parentElement?.id,
    shown:root.classList.contains('r06-shown'),
    replacing:root.classList.contains('r06-replace'),
    listHeight:lr.height, chatHeight:cr.height, rootHeight:rr.height,
    panelOpacity:getComputedStyle(document.getElementById('list-panel')).opacity,
    panelTransform:getComputedStyle(document.getElementById('list-panel')).transform,
    chatTransition:getComputedStyle(chat).transitionDuration,
    webcamParent:cam.parentElement?.id, infoParent:info.parentElement?.id,
    webcamVisible:getComputedStyle(cam).display !== 'none',
    infoVisible:getComputedStyle(info).display !== 'none',
    maskExists:!!mask,
    gameWidth:gr.width, gameHeight:gr.height
  };
})())"""


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def inspect(page):
    result = []
    page.runJavaScript(JS, result.append)
    deadline = time.monotonic() + 8
    while not result and time.monotonic() < deadline:
        QTest.qWait(25)
    if not result:
        raise AssertionError("R06 main empty-container Chromium callback timed out")
    return json.loads(result[0]) if isinstance(result[0], str) else result[0]


def until(page, predicate, name, timeout=30):
    deadline = time.monotonic() + timeout
    latest = None
    while time.monotonic() < deadline:
        latest = inspect(page)
        if latest and latest.get("ready") and predicate(latest):
            assert latest["maskExists"], (name, latest)
            assert latest["webcamVisible"] and latest["infoVisible"], (name, latest)
            assert latest["webcamParent"] != "movable-elements", (name, latest)
            assert latest["infoParent"] != "movable-elements", (name, latest)
            assert latest["gameWidth"] > 100 and latest["gameHeight"] > 100, (name, latest)
            assert float(latest["panelOpacity"]) >= .99, (name, latest)
            assert latest["panelTransform"] == "none", (name, latest)
            assert latest["chatTransition"] == "0s", (name, latest)
            print("R06_MAIN_EMPTY_PASS", name, latest, flush=True)
            return latest
        QTest.qWait(125)
    raise AssertionError(f"R06 main empty-container {name} timed out: {latest!r}")


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
        db = Database(Path(temporary) / "main_empty.db")
        db.add_game(Game(None, "QA Empty Source", "2026-01-01",
                         25, 0, STATUS_NOT_PLAYED, ""))
        db.set_settings_bulk({
            "list_overlay_show_mode": "slide",
            "list_slide_command": "!list",
            "list_slide_duration": "5",
            "combined_list_chat_layout": "split",
            "overlay_webcam_enabled": "1",
            "multichat_appearance_common": json.dumps({"visibility": "hide_empty"}),
        })
        clock = Clock()
        state = MultichatState(clock=clock)
        api = LocalApiServer(db, port=free_port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.configure_list_show("slide", "!list", 5)
        api.start()
        view = QWebEngineView()
        try:
            view.resize(1100, 750)
            view.show()
            view.load(QUrl(api.base_url + "/overlay"))
            page = view.page()

            # The previous code retained a dormant "slide" list in its
            # working slot. The accepted rule requires parking both-hidden.
            idle = until(page, lambda x: x["parent"] == "movable-elements"
                         and not x["shown"], "idle slide + empty hide-empty chat")
            neighbors = (idle["webcamParent"], idle["infoParent"])

            # A genuine first Twitch message reintroduces the shared source.
            # Hide-empty chat keeps its content-sized height (possibly <50px);
            # list remains inactive without a reserved panel.
            assert state.ingest(ChatMessage(
                "twitch", "channel", "hello-1", "alice", "A message"
            ))
            until(page, lambda x: x["parent"] in {"left-list", "right-list"}
                  and not x["shown"] and 10 < x["chatHeight"] <= x["rootHeight"]
                  and x["listHeight"] <= 2
                  and (x["webcamParent"], x["infoParent"]) == neighbors,
                  "first Twitch message, chat-only shared area")

            state.delete_message("twitch", "channel", "hello-1")
            until(page, lambda x: x["parent"] == "movable-elements"
                  and not x["shown"], "last message removed, both hidden")

            # A Twitch command counts as a message, but deleting that card
            # must not cancel the running command timer.
            assert state.ingest(ChatMessage(
                "twitch", "channel", "command-1", "alice", "!list"
            ))
            state.delete_message("twitch", "channel", "command-1")
            with urlopen(api.base_url + "/api/data", timeout=8) as response:
                data = json.load(response)
            assert data["list_show"]["remaining_ms"] > 3000, data["list_show"]
            until(page, lambda x: x["parent"] in {"left-list", "right-list"}
                  and x["shown"] and x["listHeight"] > 50
                  and x["chatHeight"] <= 2,
                  "Twitch command shows list while chat is empty")

            clock.advance(9)
            until(page, lambda x: x["parent"] == "movable-elements"
                  and not x["shown"], "command expired and chat empty")

            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 5)
            until(page, lambda x: x["parent"] in {"left-list", "right-list"}
                  and x["shown"] and x["listHeight"] > 50,
                  "always-list holds main container")

            db.set_setting("multichat_appearance_common",
                           json.dumps({"visibility": "always"}))
            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 5)
            until(page, lambda x: x["parent"] in {"left-list", "right-list"}
                  and not x["shown"] and x["chatHeight"] > 50,
                  "always-chat holds main container")

            print("R06_MAIN_EMPTY_BROWSER_ALL_PASS", flush=True)
        finally:
            view.close()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
