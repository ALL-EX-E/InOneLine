"""R06 ZERO: real Chromium static List+Twitch-chat geometry and commands.

All previous movement animation tests are preserved in Git history. This new
baseline deliberately checks there is NO List/chat transition, wipe or fade.
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
from streaming_manager.database import Database, Game
from streaming_manager.constants import STATUS_NOT_PLAYED
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
        return json.loads(value)
    return value


METRICS = """JSON.stringify((() => {
  const root=document.getElementById('list-composition'),
        layer=document.getElementById('list-layer'),
        panel=document.getElementById('list-panel'),
        chat=document.getElementById('list-chat'),
        frame=chat?.querySelector('iframe'),
        doc=frame?.contentDocument,
        cards=doc?.getElementById('messages'),
        pc=panel&&getComputedStyle(panel),
        cc=chat&&getComputedStyle(chat);
  if (!root || !layer || !panel || !chat) return {ready:false};
  const r=root.getBoundingClientRect(),
        l=layer.getBoundingClientRect(),
        c=chat.getBoundingClientRect();
  return {
    ready:true, shown:root.classList.contains('r06-shown'),
    replace:root.classList.contains('r06-replace'),
    listHeight:l.height, chatHeight:c.height, rootHeight:r.height,
    chatBottomGap: +(r.bottom-c.bottom).toFixed(2),
    count:cards?.children.length ?? -1,
    panelOpacity:+pc.opacity, panelTransform:pc.transform,
    panelTransition:pc.transitionDuration, panelAnimation:pc.animationName,
    chatTransition:cc.transitionDuration, chatAnimation:cc.animationName,
    oldMovementClasses:['r06-flow-exit','r06-split-exit','r06-flow-enter',
       'r06-top-enter','r06-always-resize'].filter(x=>root.classList.contains(x)),
    childURL:doc?.location?.href || null,
  };
})())"""


def until(page, predicate, label, timeout=32):
    end = time.monotonic() + timeout
    recent = None
    while time.monotonic() < end:
        recent = evaluate(page, METRICS)
        if recent.get("ready") and predicate(recent):
            print("R06_ZERO_PASS:", label, recent, flush=True)
            return recent
        QTest.qWait(140)
    raise AssertionError(f"{label} timeout: {recent!r}")


def static_check(state, label):
    assert state["panelOpacity"] >= 0.99, (label, state)
    assert state["panelTransform"] == "none", (label, state)
    assert float(state["panelTransition"].split(",")[0].rstrip("s")) == 0, (label, state)
    assert float(state["chatTransition"].split(",")[0].rstrip("s")) == 0, (label, state)
    assert state["panelAnimation"] == "none", (label, state)
    assert state["chatAnimation"] == "none", (label, state)
    assert not state["oldMovementClasses"], (label, state)
    assert abs(state["chatBottomGap"]) <= 3, (label, state)


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
        db = Database(Path(temporary) / "r06_zero_browser.db")
        for index in range(8):
            db.add_game(Game(None, "QA List Entry " + str(index),
                             "2026-01-01", 100 + index, 0, STATUS_NOT_PLAYED, ""))
        db.set_settings_bulk({
            "list_overlay_show_mode":"always",
            "list_slide_direction":"right",
            "list_slide_duration":"20",
            "list_animation_seconds":"1.5",
            "list_slide_command":"!list",
            "list_chat_layout":"split",
            "list_with_chat":"1",
        })
        state = MultichatState()
        api = LocalApiServer(db, port=free_port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.configure_list_show("always", "!list", 20)
        api.start()
        views = []
        try:
            screen = app.primaryScreen().availableGeometry()
            for i, (route, width) in enumerate((("/overlay", 1000),
                                                ("/list-overlay", 380))):
                view = QWebEngineView()
                view.resize(width, 620)
                view.move(screen.x() + 5 + i * 110, screen.y() + 5 + i * 35)
                view.show()
                view.load(QUrl(api.base_url + route))
                views.append(view)
                app.processEvents()
                QTest.qWait(300)
            pages = [view.page() for view in views]

            for page in pages:
                m = until(page, lambda a: a["shown"] and a["chatHeight"] == 0,
                          "initial always List, empty hide-empty chat")
                static_check(m, "initial")

            # Empty chat in Always reserves half the area when List is visible.
            db.set_setting("multichat_appearance_common",
                           json.dumps({"visibility":"always"}))
            for page in pages:
                m = until(page, lambda a: a["shown"] and
                          0 < a["chatHeight"] < a["rootHeight"],
                          "fixed-height always-chat / split")
                static_check(m, "always-chat split")

            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 20)
            for page in pages:
                m = until(page, lambda a: not a["shown"] and
                          a["listHeight"] <= 2 and
                          abs(a["chatHeight"]-a["rootHeight"]) <= 3,
                          "hidden List, full-height always-chat")
                static_check(m, "hidden")

            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 20)
            for page in pages:
                m = until(page, lambda a: a["shown"] and
                          a["listHeight"] > 10 and
                          a["chatHeight"] > 10,
                          "instant Always reappearance")
                static_check(m, "restore always")

            # Hide-empty mode only reserves room when a message exists.
            db.set_setting("multichat_appearance_common",
                           json.dumps({"visibility":"hide_empty"}))
            for page in pages:
                m = until(page, lambda a: a["shown"] and a["chatHeight"] == 0,
                          "hide-empty chat releases its area")
                static_check(m, "empty chat")

            assert state.ingest(ChatMessage("twitch", "chan", "zero-message",
                                            "alice", "R06 ZERO visible chat"))
            for page in pages:
                m = until(page, lambda a: a["shown"] and a["count"] == 1 and
                          a["chatHeight"] > 15,
                          "dynamic Twitch chat gets message and intrinsic height")
                static_check(m, "dynamic chat")

            # Directional settings are retained but MUST NOT move the panel.
            for direction in ("left","right","top","bottom"):
                db.set_settings_bulk({
                    "list_overlay_show_mode":"slide",
                    "list_chat_layout":"split",
                    "list_slide_direction":direction,
                })
                api.configure_list_show("slide", "!list", 20)
                for page in pages:
                    m=until(page, lambda a: not a["shown"] and a["listHeight"] <= 2,
                            "hidden command List before "+direction)
                    static_check(m, "before "+direction)
                result=state.ingest(ChatMessage("twitch", "chan",
                    "zero-command-"+direction, "alice", "!list"))
                assert result, ("List command was rejected", direction)
                with urlopen(api.base_url + "/api/data", timeout=5) as response:
                    server = json.loads(response.read().decode("utf-8"))
                assert server["list_show"]["remaining_ms"] > 0, (
                    "R06 ZERO command did not activate server timer",
                    direction, server["list_show"])
                for page in pages:
                    m=until(page, lambda a: a["shown"] and not a["replace"] and
                            a["listHeight"] > 10,
                            "instant command List from "+direction)
                    static_check(m, "command "+direction)
                for page in pages:
                    m=until(page, lambda a: not a["shown"] and
                            a["listHeight"] <= 2,
                            "command expiration from "+direction, timeout=27)
                    static_check(m, "expired "+direction)

            # Replacement covers chat while shown, then uncovers it at once.
            db.set_setting("list_chat_layout","replace")
            api.configure_list_show("slide", "!list", 20)
            assert state.ingest(ChatMessage("twitch", "chan",
                                            "zero-replace", "alice", "!list"))
            for page in pages:
                m=until(page, lambda a: a["shown"] and a["replace"] and
                        a["listHeight"] >= a["rootHeight"]-3,
                        "static replacement")
                static_check(m, "replacement")
            for page in pages:
                m=until(page, lambda a: not a["shown"] and not a["replace"] and
                        a["listHeight"] <= 2,
                        "replacement timeout", timeout=27)
                static_check(m, "replacement timeout")

            # The OBS switch must remove the chat without reserving empty space.
            state.set_obs_enabled("twitch", False)
            db.set_setting("list_overlay_show_mode","always")
            api.configure_list_show("always", "!list", 20)
            for page in pages:
                m=until(page, lambda a: a["shown"] and a["chatHeight"] == 0 and
                        a["listHeight"] > 10,
                        "OBS Twitch disabled / full List")
                static_check(m, "OBS chat disabled")
            print("R06_ZERO_BROWSER_ALL_PASS", flush=True)
        finally:
            for view in views:
                view.close()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
