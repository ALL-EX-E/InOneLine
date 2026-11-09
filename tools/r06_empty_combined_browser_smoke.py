"""R06: main OBS must park the combined container when both widgets are hidden.

An idle command-only List is not visible.  The Twitch message, command timer,
timer expiry, independent Always modes, and camera/info geometry are checked
in real Qt WebEngine Chromium rather than inferred from CSS string matching.
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
  const root=document.getElementById("list-composition"),
        layer=document.getElementById("list-layer"),
        chat=document.getElementById("list-chat"),
        panel=document.getElementById("list-panel"),
        camera=document.getElementById("webcam-frame"),
        info=document.getElementById("info-panel"),
        game=document.getElementById("game-frame"),
        gameCutout=document.getElementById("game-cutout"),
        cameraCutout=document.getElementById("webcam-cutout"),
        frame=chat?.querySelector("iframe");
  if (!root || !layer || !chat || !panel || !camera || !info || !game) {
    return {ready:false};
  }
  const box=(element)=>element.getBoundingClientRect();
  const s=getComputedStyle(panel), c=getComputedStyle(chat);
  const doc=frame?.contentDocument, messages=doc?.getElementById("messages");
  return {
    ready:true,
    parent:root.parentElement?.id,
    listShown:root.classList.contains("r06-shown"),
    listHeight:box(layer).height, chatHeight:box(chat).height,
    rootHeight:box(root).height,
    chatCount:messages?.children.length ?? -1,
    childURL:doc?.location?.href ?? null,
    childReady:doc?.readyState ?? null,
    childRenderType:typeof frame?.contentWindow?.IOLRenderEmbeddedChatState,
    childRefreshType:typeof frame?.contentWindow?.IOLRefreshEmbeddedChat,
    childShellHidden:doc?.getElementById("shell")?.classList.contains("hidden"),
    cameraParent:camera.parentElement?.id,
    infoParent:info.parentElement?.id,
    rightVisible:getComputedStyle(document.getElementById("right-column")).display !== "none",
    gameWidth:box(game).width,
    gameCutoutWidth:Number(gameCutout?.getAttribute("width")||0),
    cameraCutoutWidth:Number(cameraCutout?.getAttribute("width")||0),
    panelOpacity:s.opacity, panelTransform:s.transform, panelTransition:s.transitionDuration,
    chatTransition:c.transitionDuration
  };
})())"""


class ManualClock:
    """Control only the command deadline; Chromium still uses real elapsed time."""

    def __init__(self) -> None:
        self.now = time.monotonic()

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def inspect(page):
    values = []
    page.runJavaScript(JS, values.append)
    end = time.monotonic() + 8
    while not values and time.monotonic() < end:
        QTest.qWait(25)
    if not values:
        raise AssertionError("R06 empty-container Chromium JS callback timed out")
    return json.loads(values[0]) if isinstance(values[0], str) else values[0]


def until(page, predicate, label: str, timeout: float = 25, *, api=None, dynamic_chat=False):
    end = time.monotonic() + timeout
    latest = None
    while time.monotonic() < end:
        latest = inspect(page)
        if (latest and latest.get("ready") and predicate(latest) and
                latest["cameraParent"] == "right-top" and
                latest["infoParent"] == "right-bottom" and
                latest["rightVisible"]):
            # Do not accept the initial HTML state before the first /api/data
            # layout pass has attached the independent camera/info widgets.
            assert latest["gameWidth"] > 0, (label, latest)
            assert latest["gameCutoutWidth"] > 0, (label, latest)
            assert latest["cameraCutoutWidth"] > 0, (label, latest)
            assert float(latest["panelOpacity"]) >= 0.99, (label, latest)
            assert latest["panelTransform"] == "none", (label, latest)
            assert latest["panelTransition"] == "0s", (label, latest)
            if not dynamic_chat:
                assert latest["chatTransition"] == "0s", (label, latest)
            print("R06_EMPTY_CONTAINER_PASS", label, latest, flush=True)
            return latest
        QTest.qWait(130)
    if api is not None:
        # Do not heal the browser under test; report actual server snapshots.
        try:
            with urlopen(api.base_url + "/api/multichat", timeout=5) as response:
                server_chat = json.load(response)
            with urlopen(api.base_url + "/api/data", timeout=5) as response:
                server_data = json.load(response)
            print("R06_EMPTY_DIAGNOSTIC", json.dumps({
                "label": label,
                "server_message_ids": [m.get("external_id") for m in server_chat.get("messages", [])],
                "server_obs_enabled": server_chat.get("obs_enabled"),
                "server_list_show": server_data.get("list_show"),
                "server_multichat": server_data.get("multichat"),
                "chromium": latest,
            }, ensure_ascii=True), flush=True)
        except Exception as exc:
            print("R06_EMPTY_DIAGNOSTIC_API_ERROR", repr(exc), flush=True)
    raise AssertionError(f"R06 empty-container {label} timeout: {latest!r}")


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
        db = Database(Path(temporary) / "r06_empty_main.db")
        db.add_game(Game(None, "QA Empty Main", "2026-01-01",
                         50, 0, STATUS_NOT_PLAYED, ""))
        db.set_settings_bulk({
            "list_overlay_show_mode": "slide",
            "list_slide_command": "!list",
            "list_slide_duration": "3",
            "combined_list_chat_layout": "split",
            "multichat_appearance_common": json.dumps({"visibility": "hide_empty"}),
            "overlay_webcam_enabled": "1",
            "overlay_webcam_position": "top_right",
            "overlay_info_position": "bottom_right",
        })
        clock = ManualClock()
        state = MultichatState(clock=clock)
        api = LocalApiServer(db, port=free_port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.configure_list_show("slide", "!list", 3)
        api.start()
        view = QWebEngineView()
        try:
            view.resize(1150, 680)
            view.show()
            view.load(QUrl(api.base_url + "/overlay"))
            page = view.page()
            idle = until(
                page,
                lambda m: m["parent"] == "movable-elements" and not m["listShown"],
                "slide idle with empty hide-empty chat is parked",
                dynamic_chat=True,
            )
            assert idle["listHeight"] <= 1, idle

            # A new Twitch message revives only the chat, in the original
            # working column, without changing the independent list mode.
            assert state.ingest(ChatMessage(
                "twitch", "channel", "msg-1", "tester", "QA visible chat",
            ))
            with urlopen(api.base_url + "/api/multichat", timeout=5) as response:
                state_snapshot = json.load(response)
            assert any(
                row.get("external_id") == "msg-1"
                for row in state_snapshot.get("messages", [])
            ), ("Twitch test message missing from server OBS snapshot", state_snapshot)
            message = until(
                page,
                lambda m: m["parent"] == "right-list" and
                not m["listShown"] and m["chatHeight"] > 10 and
                m["listHeight"] <= 2 and m["chatCount"] >= 1,
                "new message restores chat only", api=api, dynamic_chat=True,
            )
            assert abs(message["gameWidth"] - idle["gameWidth"]) <= 1.0

            state.delete_message("twitch", "channel", "msg-1")
            until(
                page,
                lambda m: m["parent"] == "movable-elements" and
                not m["listShown"],
                "deleted final message releases combined container", dynamic_chat=True,
            )

            assert state.ingest(ChatMessage(
                "twitch", "channel", "cmd-1", "tester", "!list",
            ))
            with urlopen(api.base_url + "/api/data", timeout=5) as response:
                snapshot = json.load(response)
            assert snapshot["list_show"]["remaining_ms"] >= 2500, snapshot["list_show"]
            # Removing the command message makes the chat genuinely empty
            # while the application-owned List timer keeps running.
            state.delete_message("twitch", "channel", "cmd-1")
            shown = until(
                page,
                lambda m: m["parent"] == "right-list" and m["listShown"] and
                m["listHeight"] > 20 and m["chatHeight"] < 2,
                "command shows only list", api=api, dynamic_chat=True,
            )
            assert abs(shown["gameWidth"] - idle["gameWidth"]) <= 1.0
            # Server time expires deterministically, while the accepted local
            # Browser Source phase clock finishes its independent 3-second hold.
            clock.advance(4)
            with urlopen(api.base_url + "/api/data", timeout=5) as response:
                expired = json.load(response)
            assert expired["list_show"]["remaining_ms"] == 0, expired["list_show"]
            until(
                page,
                lambda m: m["parent"] == "movable-elements" and
                not m["listShown"],
                "command expiry parks empty combined container",
                timeout=25, api=api, dynamic_chat=True,
            )

            # Independent Always visibility means a real visible widget exists.
            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 90)
            until(
                page,
                lambda m: m["parent"] == "right-list" and m["listShown"] and
                m["listHeight"] > 20,
                "always list keeps combined container",
            )

            db.set_settings_bulk({
                "list_overlay_show_mode": "hidden",
                "multichat_appearance_common": json.dumps({"visibility": "always"}),
            })
            api.configure_list_show("hidden", "!list", 90)
            until(
                page,
                lambda m: m["parent"] == "right-list" and not m["listShown"] and
                m["chatHeight"] > 20 and m["listHeight"] <= 2,
                "always chat keeps combined container",
            )

            db.set_setting(
                "multichat_appearance_common", json.dumps({"visibility": "hidden"})
            )
            until(
                page,
                lambda m: m["parent"] == "movable-elements" and
                not m["listShown"],
                "hidden list and hidden chat park container",
            )
            print("R06_EMPTY_COMBINED_BROWSER_ALL_PASS", flush=True)
        finally:
            view.close()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
