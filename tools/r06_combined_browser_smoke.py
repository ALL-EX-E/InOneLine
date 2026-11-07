"""Separate R06 combined OBS URL: static contracts and first approved motion.

Verifies split/replace/visibility and the user-approved Hidden -> Always
split entry with an empty Always Twitch chat in real native Chromium.
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
        panel=document.getElementById("list-panel"),
        chat=document.getElementById("list-chat"),
        frame=chat?.querySelector("iframe"),
        doc=frame?.contentDocument,
        cards=doc?.getElementById("messages");
  if (!root || !layer || !panel || !chat) return {ready:false};
  const rs=root.getBoundingClientRect(), ls=layer.getBoundingClientRect(),
        cs=chat.getBoundingClientRect(), ps=getComputedStyle(panel),
        csStyle=getComputedStyle(chat);
  return {
    ready:true, shown:root.classList.contains("r06-shown"),
    replace:root.classList.contains("r06-replace"),
    rootHeight:rs.height, rootTop:rs.top,
    listHeight:ls.height, listTop:ls.top, listBottom:ls.bottom,
    chatHeight:cs.height, chatTop:cs.top, chatBottom:cs.bottom,
    combinedSync:root.dataset.r06CombinedSync || "idle",
    motionKind:root.dataset.r06StandaloneMotionKind || "idle",
    motionDuration:Number(root.dataset.r06StandaloneLastMotionDurationMs || 0),
    entranceCount:Number(root.dataset.r06StandaloneEntranceCount || 0),
    iframeCount:document.querySelectorAll("iframe").length,
    childUrl:doc?.location?.href || "",
    messageCount:cards?.children?.length ?? -1,
    chatTransition:csStyle.transitionDuration,
    panelOpacity:ps.opacity, panelTransform:ps.transform,
    obsVisible:document.documentElement.dataset.obsVisible
  };
})())"""


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def inspect(page):
    values = []
    page.runJavaScript(JS, values.append)
    expiry = time.monotonic() + 8
    while not values and time.monotonic() < expiry:
        QTest.qWait(25)
    if not values:
        raise AssertionError("combined Chromium JS callback timed out")
    return json.loads(values[0]) if isinstance(values[0], str) else values[0]


def until(page, expected, label, timeout=35):
    deadline = time.monotonic() + timeout
    latest = None
    while time.monotonic() < deadline:
        latest = inspect(page)
        if latest and latest.get("ready") and expected(latest):
            assert latest["iframeCount"] == 1, (label, latest)
            assert latest["chatTransition"] == "0s", (label, latest)
            assert float(latest["panelOpacity"]) >= .99, (label, latest)
            assert latest["panelTransform"] == "none", (label, latest)
            print("R06_COMBINED_PASS", label, latest, flush=True)
            return latest
        QTest.qWait(130)
    raise AssertionError(f"{label} timed out: {latest!r}")


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        db = Database(Path(temp) / "r06_combined.db")
        db.add_game(Game(None, "QA Combined Entry", "2026-01-01",
                         35, 0, STATUS_NOT_PLAYED, ""))
        db.set_settings_bulk({
            "list_overlay_show_mode": "always",
            "list_slide_command": "!list",
            "list_slide_duration": "15",
            "list_chat_layout": "replace",  # legacy must not control new source
            "combined_list_chat_layout": "split",
            "multichat_appearance_common": json.dumps({"visibility": "always"}),
        })
        state = MultichatState()
        api = LocalApiServer(db, port=free_port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.configure_list_show("always", "!list", 15)
        api.start()
        view = QWebEngineView()
        try:
            view.resize(400, 620)
            view.show()
            view.load(QUrl(api.base_url + "/combined-overlay"))
            m = until(
                view.page(),
                lambda a: a["shown"] and not a["replace"] and
                a["chatHeight"] > 15 and a["listHeight"] > 15 and
                a["childUrl"].endswith("/multichat-overlay?embedded=1"),
                "separate combined route with Twitch iframe",
            )
            assert abs(m["listHeight"] - m["chatHeight"]) < 18, m

            # New "replace" setting must not cover the chat in Always List.
            db.set_setting("combined_list_chat_layout", "replace")
            until(view.page(), lambda a: a["shown"] and not a["replace"],
                  "always mode cannot replace")

            # First command idle, chat owns the whole region.
            db.set_setting("list_overlay_show_mode", "slide")
            api.configure_list_show("slide", "!list", 15)
            until(view.page(), lambda a: not a["shown"] and
                  a["listHeight"] < 2 and
                  abs(a["chatHeight"]-a["rootHeight"]) < 3,
                  "slide idle chat owns full area")

            assert state.ingest(ChatMessage(
                "twitch", "ch", "combined-command", "qa_user", "!list",
            ))
            # Verify the command was accepted by the controller, not only
            # that the chat renderer received the "!list" text.
            with urlopen(api.base_url + "/api/data", timeout=8) as response:
                command_data = json.load(response)
            assert command_data["list_show"]["remaining_ms"] > 12000, (
                "Combined command did not activate server timer",
                command_data["list_show"],
            )
            until(view.page(), lambda a: a["shown"] and a["replace"] and
                  a["listHeight"] >= a["rootHeight"] - 3,
                  "command replacement, instant without opacity animation")
            until(view.page(), lambda a: not a["shown"] and not a["replace"] and
                  a["listHeight"] < 2, "command expiry restores chat")

            db.set_settings_bulk({
                "list_overlay_show_mode": "always",
                "combined_list_chat_layout": "split",
            })
            api.configure_list_show("always", "!list", 15)
            until(view.page(), lambda a: a["shown"] and not a["replace"] and
                  a["chatHeight"] > 15 and a["listHeight"] > 15,
                  "saved split mode restored")

            state.set_obs_enabled("twitch", False)
            until(view.page(), lambda a: a["shown"] and a["chatHeight"] < 2
                  and a["listHeight"] >= a["rootHeight"] - 3,
                  "chat off, list owns full area")

            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 15)
            until(view.page(), lambda a: not a["shown"] and
                  a["chatHeight"] < 2 and a["listHeight"] < 2 and
                  a["obsVisible"] == "false",
                  "both hidden, no visible content")
            # First agreed interaction: share the standalone List's top-down
            # animation, and move the empty Always-chat's upper boundary with
            # the List's lower edge. Neither loses opacity or moves the root.
            state.set_obs_enabled("twitch", True)
            db.set_settings_bulk({
                "combined_list_chat_layout": "split",
                "list_slide_animation_seconds": "2.00",
            })
            until(view.page(), lambda a: not a["shown"] and
                  abs(a["chatHeight"] - a["rootHeight"]) < 3,
                  "hidden List, empty Always-chat takes 100 percent")
            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 15)
            started = until(
                view.page(),
                lambda a: a["combinedSync"] == "split-enter" and
                          a["motionKind"] == "enter",
                "first shared list entry and chat shrink started")
            assert started["motionDuration"] == 2000, started
            assert started["listTop"] < started["rootTop"] + 2, started
            assert abs(started["chatBottom"] -
                       (started["rootTop"] + started["rootHeight"])) < 2, started
            frames = []
            for _ in range(8):
                frame = inspect(view.page())
                if frame["combinedSync"] == "split-enter":
                    frames.append(frame)
                    assert 0 <= frame["chatTop"] - frame["listBottom"] <= 18, frame
                    assert abs(frame["chatBottom"] -
                               (frame["rootTop"] + frame["rootHeight"])) < 2, frame
                    assert float(frame["panelOpacity"]) >= .99, frame
                QTest.qWait(125)
            assert frames, "No intermediate combined animation frames"
            done = until(
                view.page(),
                lambda a: a["shown"] and a["combinedSync"] == "idle" and
                          a["motionKind"] == "idle" and
                          abs(a["listHeight"] - a["chatHeight"]) < 18 and
                          9 <= a["chatTop"] - a["listBottom"] <= 15,
                "split entry finished with aligned edges")
            entrance_count = done["entranceCount"]
            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 15)
            QTest.qWait(1300)
            stable = inspect(view.page())
            assert stable["entranceCount"] == entrance_count, stable
            assert stable["combinedSync"] == "idle", stable
            print("R06_COMBINED_BROWSER_ALL_PASS", flush=True)
        finally:
            view.close()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
