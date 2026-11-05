"""R06 FIX1: main OBS layout parks an empty combined list/chat region.

Native Chromium tests the actual /overlay DOM rather than just CSS visibility.
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


METRICS = """JSON.stringify((() => {
  const root = document.getElementById("list-composition"),
        list = document.getElementById("list-layer"),
        chat = document.getElementById("list-chat"),
        panel = document.getElementById("list-panel"),
        frame = document.getElementById("game-frame"),
        camera = document.getElementById("webcam-frame"),
        info = document.getElementById("info-panel"),
        embedded = chat?.querySelector("iframe"),
        cards = embedded?.contentDocument?.getElementById("messages");
  if (!root || !list || !chat || !panel || !frame || !camera || !info)
    return {ready:false};
  return {
    ready:document.documentElement.dataset.obsPolicyReady === "true",
    parent:root.parentElement?.id || "",
    shown:root.classList.contains("r06-shown"),
    listHeight:list.getBoundingClientRect().height,
    chatHeight:chat.getBoundingClientRect().height,
    messageCount:cards?.children?.length ?? 0,
    iframeCount:root.querySelectorAll("iframe").length,
    cameraParent:camera.parentElement?.id || "",
    infoParent:info.parentElement?.id || "",
    gameFrameWidth:frame.getBoundingClientRect().width,
    gameMask:document.getElementById("game-cutout")?.getAttribute("width"),
    opacity:getComputedStyle(panel).opacity,
    transform:getComputedStyle(panel).transform,
    panelTransition:getComputedStyle(panel).transitionDuration,
    chatTransition:getComputedStyle(chat).transitionDuration
  };
})())"""


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def inspect(page):
    result = []
    page.runJavaScript(METRICS, result.append)
    limit = time.monotonic() + 8
    while not result and time.monotonic() < limit:
        QTest.qWait(25)
    if not result:
        raise AssertionError("R06 main layout JavaScript callback timed out")
    return json.loads(result[0]) if isinstance(result[0], str) else result[0]


def until(page, predicate, label, timeout=35):
    end = time.monotonic() + timeout
    recent = None
    while time.monotonic() < end:
        recent = inspect(page)
        if recent.get("ready") and predicate(recent):
            assert recent["iframeCount"] == 1, (label, recent)
            assert recent["cameraParent"] != "movable-elements", (label, recent)
            assert recent["gameFrameWidth"] > 100, (label, recent)
            assert recent["opacity"] == "1", (label, recent)
            assert recent["transform"] == "none", (label, recent)
            assert recent["panelTransition"] == "0s", (label, recent)
            assert recent["chatTransition"] == "0s", (label, recent)
            print("R06_MAIN_EMPTY_LAYOUT_PASS", label, recent, flush=True)
            return recent
        QTest.qWait(130)
    raise AssertionError(f"R06 main empty layout {label} timed out: {recent!r}")


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        db = Database(Path(temp) / "r06_main_parking.db")
        db.add_game(Game(None, "QA Main Layout", "2026-01-01",
                         35, 0, STATUS_NOT_PLAYED, ""))
        db.set_settings_bulk({
            "list_overlay_show_mode": "slide",
            "list_slide_command": "!list",
            "list_slide_duration": "8",
            "combined_list_chat_layout": "split",
            "overlay_webcam_enabled": "1",
            "stream_info_enabled": "1",
            "multichat_appearance_common": json.dumps({"visibility": "hide_empty"}),
        })
        state = MultichatState()
        api = LocalApiServer(db, port=port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.configure_list_show("slide", "!list", 8)
        api.start()
        view = QWebEngineView()
        try:
            view.resize(1000, 620)
            view.show()
            view.load(QUrl(api.base_url + "/overlay"))
            initial = until(view.page(), lambda m:
                m["parent"] == "movable-elements" and not m["shown"],
                "idle slide and empty hide-empty chat park container")
            original_info_parent = initial["infoParent"]
            original_width = initial["gameFrameWidth"]
            original_mask = initial["gameMask"]

            assert state.ingest(ChatMessage(
                "twitch", "r06", "first-message", "qa_user", "Hello from Twitch"
            ))
            msg = until(view.page(), lambda m:
                m["parent"] in {"left-list", "right-list"} and
                not m["shown"] and m["chatHeight"] > 10 and
                m["messageCount"] > 0,
                "first Twitch message brings back chat only")
            assert msg["infoParent"] == original_info_parent
            assert abs(msg["gameFrameWidth"] - original_width) < 2
            assert msg["gameMask"] == original_mask

            state.set_obs_enabled("twitch", False)
            until(view.page(), lambda m:
                  m["parent"] == "movable-elements" and not m["shown"],
                  "chat hidden returns combined container to parking")
            state.set_obs_enabled("twitch", True)

            assert state.ingest(ChatMessage(
                "twitch", "r06", "show-command", "qa_user", "!list"
            ))
            with urlopen(api.base_url + "/api/data", timeout=8) as response:
                payload = json.load(response)
            assert payload["list_show"]["remaining_ms"] > 0, payload["list_show"]
            command = until(view.page(), lambda m:
                m["parent"] in {"left-list", "right-list"} and m["shown"] and
                m["listHeight"] > 20,
                "Twitch command brings back list")
            assert command["infoParent"] == original_info_parent
            state.set_obs_enabled("twitch", False)

            expired = until(view.page(), lambda m:
                m["parent"] == "movable-elements" and not m["shown"],
                "timer expiry with hidden chat returns to parking", timeout=25)
            assert expired["infoParent"] == original_info_parent

            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 8)
            always = until(view.page(), lambda m:
                m["parent"] in {"left-list", "right-list"} and m["shown"] and
                m["listHeight"] > 20 and m["chatHeight"] < 2,
                "always list returns even when chat is hidden")
            assert always["infoParent"] == original_info_parent

            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 8)
            end = until(view.page(), lambda m:
                m["parent"] == "movable-elements" and not m["shown"],
                "both hidden again")
            assert end["infoParent"] == original_info_parent
            print("R06_MAIN_EMPTY_LAYOUT_ALL_PASS", flush=True)
        finally:
            view.close()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
