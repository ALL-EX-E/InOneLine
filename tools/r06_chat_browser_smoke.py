"""R06 combined main-overlay and dedicated OBS URL: static List/chat geometry.

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
        shell=doc?.getElementById('shell'),
        firstCard=cards?.firstElementChild,
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
    rootTop:r.top, rootLeft:r.left, rootWidth:r.width,
    listTop:l.top, listBottom:l.bottom, chatTop:c.top,
    chatBottomGap: +(r.bottom-c.bottom).toFixed(2),
    combinedSync:root.dataset.r06CombinedSync || 'idle',
    motionKind:root.dataset.r06StandaloneMotionKind || 'idle',
    motionDuration:Number(root.dataset.r06StandaloneLastMotionDurationMs || 0),
    phase:root.dataset.r06StandalonePhase || 'idle',
    lastEntrance:root.dataset.r06StandaloneLastEntrance || '',
    lastExit:root.dataset.r06StandaloneLastExit || '',
    entranceCount:Number(root.dataset.r06StandaloneEntranceCount || 0),
    exitCount:Number(root.dataset.r06StandaloneExitCount || 0),
    chatClipPath:cc.clipPath,
    listClipPath:getComputedStyle(layer).clipPath,
    iframeStable:!window.__r06MainQaFrame || frame === window.__r06MainQaFrame,
    documentStable:!window.__r06MainQaDocument || doc === window.__r06MainQaDocument,
    hasSentinel:[...(cards?.children || [])].some(x=>x.textContent.includes('R06 ZERO visible chat')),
    count:cards?.children.length ?? -1,
    shellRadius:shell ? doc.defaultView.getComputedStyle(shell).borderRadius : null,
    cardRadius:firstCard ? doc.defaultView.getComputedStyle(firstCard).borderRadius : null,
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
    assert state["panelAnimation"] == "none", (label, state)
    assert state["chatAnimation"] == "none", (label, state)
    assert state["chatTransition"] == "0s", (label, state)
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
            "list_slide_animation_seconds":"2.00",
            "list_animation_seconds":"1.5",
            "list_slide_command":"!list",
            "combined_list_chat_layout":"split",
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
            for i, (route, width) in enumerate((("/overlay", 1000),)):
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

            # Main /overlay already embeds the shared List/chat component.
            # The accepted Save transitions must use that same engine here.
            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 20)
            for page in pages:
                first = until(
                    page, lambda a: a["combinedSync"] == "split-exit"
                    and a["motionKind"] == "exit",
                    "shared main Save exit begins")
                assert first["motionDuration"] == 2000, first
                midframes = []
                for _ in range(10):
                    frame = evaluate(page, METRICS)
                    if frame["combinedSync"] == "split-exit":
                        midframes.append(frame)
                        assert abs(frame["chatBottomGap"]) < 3, frame
                    QTest.qWait(135)
                assert len(midframes) >= 2, midframes
                m = until(
                    page, lambda a: not a["shown"] and
                    a["combinedSync"] == "idle" and
                    a["motionKind"] == "idle" and a["listHeight"] <= 2 and
                    abs(a["chatHeight"]-a["rootHeight"]) <= 3,
                    "shared main Save exit leaves full chat")
                static_check(m, "hidden")

            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 20)
            for page in pages:
                first = until(
                    page, lambda a: a["combinedSync"] == "split-enter"
                    and a["motionKind"] == "enter",
                    "shared main Save entrance begins")
                assert first["motionDuration"] == 2000, first
                m = until(
                    page, lambda a: a["shown"] and
                    a["combinedSync"] == "idle" and
                    a["motionKind"] == "idle" and
                    a["listHeight"] > 10 and a["chatHeight"] > 10,
                    "shared main Save entrance settles")
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
                assert float(m["chatTransition"].split(",")[0].rstrip("s")) == 0
                assert m["shellRadius"] == m["cardRadius"] == "8px", (
                    "Original Twitch cards must match shell radius in the main OBS source", m)

            # The CSS default must not override the saved custom card radius.
            for radius in (0, 20):
                db.set_setting(
                    "multichat_appearance_twitch",
                    json.dumps({"mode": "custom", "card_radius": radius}),
                )
                for page in pages:
                    m = until(page, lambda a: a["count"] == 1 and
                              a["cardRadius"] == f"{radius}px",
                              f"custom Twitch card radius {radius}px")
                    assert m["shellRadius"] == "8px", m
            db.set_setting("multichat_appearance_twitch",
                           json.dumps({"mode": "original"}))
            for page in pages:
                m = until(page, lambda a: a["count"] == 1 and
                          a["cardRadius"] == a["shellRadius"] == "8px",
                          "original Twitch corners restored after custom mode")

            # New main-OBS parity: use the existing Twitch iframe and the
            # same four-direction 2s entry -> 5s hold -> 2s reverse exit.
            db.set_settings_bulk({
                "multichat_appearance_common":json.dumps({"visibility":"always"}),
                "combined_list_chat_layout":"split",
                "list_overlay_show_mode":"slide",
                "list_slide_duration":"5",
                "list_slide_animation_seconds":"2.00",
            })
            api.configure_list_show("slide", "!list", 5)
            for page in pages:
                idle = until(page, lambda a: not a["shown"] and
                             a["combinedSync"] == "idle" and
                             abs(a["chatHeight"]-a["rootHeight"]) <= 3,
                             "main combined command idle")
                assert idle["hasSentinel"], idle
                evaluate(page,
                    "(window.__r06MainQaFrame=document.querySelector("
                    "'#list-chat iframe'),window.__r06MainQaDocument="
                    "window.__r06MainQaFrame.contentDocument,true)")
            for direction in ("left", "right", "top", "bottom"):
                db.set_setting("list_slide_direction", direction)
                for page in pages:
                    idle = until(page, lambda a: not a["shown"] and
                                 a["combinedSync"] == "idle" and
                                 a["motionKind"] == "idle",
                                 "main before command "+direction)
                    previous_exit = idle["exitCount"]
                assert state.ingest(ChatMessage(
                    "twitch", "chan", "main-parity-"+direction, "qa_viewer", "!list"
                )), direction
                for page in pages:
                    started = until(
                        page, lambda a: a["combinedSync"] == "command-enter"
                        and a["motionKind"] == "enter"
                        and a["lastEntrance"] == direction,
                        "main shared command entrance "+direction)
                    assert started["motionDuration"] == 2000, started
                    assert started["iframeStable"] and started["documentStable"], started
                    entry = []
                    for _ in range(10):
                        point = evaluate(page, METRICS)
                        if point["combinedSync"] == "command-enter":
                            entry.append(point)
                            assert point["chatClipPath"] != "none", point
                            assert point["hasSentinel"], point
                            assert point["iframeStable"] and point["documentStable"], point
                            assert abs(point["chatBottomGap"]) <= 3, point
                        QTest.qWait(125)
                    assert len(entry) >= 2, (direction, entry)
                    assert len({p["chatClipPath"] for p in entry}) >= 2, entry
                    held = until(
                        page, lambda a: a["shown"]
                        and a["combinedSync"] == "idle" and a["phase"] == "hold",
                        "main shared full hold "+direction)
                    assert held["hasSentinel"], held
                    assert held["chatClipPath"] == "none", held
                    assert held["iframeStable"] and held["documentStable"], held
                    assert held["chatHeight"] > 10 and held["listHeight"] > 10, held
                    reverse = until(
                        page, lambda a: a["combinedSync"] == "command-exit"
                        and a["motionKind"] == "exit" and
                        a["lastExit"] == direction and
                        a["exitCount"] == previous_exit+1,
                        "main shared reverse exit "+direction)
                    assert reverse["motionDuration"] == 2000, reverse
                    retreat = []
                    for _ in range(10):
                        point = evaluate(page, METRICS)
                        if point["combinedSync"] == "command-exit":
                            retreat.append(point)
                            assert point["chatClipPath"] != "none", point
                            assert point["hasSentinel"], point
                            assert point["iframeStable"] and point["documentStable"], point
                            assert abs(point["chatBottomGap"]) <= 3, point
                        QTest.qWait(125)
                    assert len(retreat) >= 2, retreat
                    assert len({p["chatClipPath"] for p in retreat}) >= 2, retreat
                    after = until(
                        page, lambda a: not a["shown"] and
                        a["combinedSync"] == "idle" and
                        a["motionKind"] == "idle" and
                        a["phase"] == "idle" and
                        abs(a["chatHeight"]-a["rootHeight"]) <= 3,
                        "main shared reverse restores chat "+direction)
                    assert after["hasSentinel"], after
                    assert after["iframeStable"] and after["documentStable"], after
                    assert after["exitCount"] == previous_exit+1, after

            # Restore unchanged hide-empty mode for its original static
            # command tests; it is NOT part of the accepted combined motion.
            db.set_settings_bulk({
                "multichat_appearance_common":json.dumps({"visibility":"hide_empty"}),
                "list_slide_duration":"20",
            })
            api.configure_list_show("slide", "!list", 20)
            state.clear_chat("twitch", "chan")
            assert state.ingest(ChatMessage(
                "twitch", "chan", "zero-message-restored",
                "alice", "R06 ZERO visible chat"))
            for page in pages:
                restored = until(
                    page, lambda a: a["count"] == 1 and
                    a["combinedSync"] == "idle" and a["hasSentinel"],
                    "existing hide-empty behavior restored")

            # Directional settings in hide-empty remain instant and do not move.

            for direction in ("left","right","top","bottom"):
                db.set_settings_bulk({
                    "list_overlay_show_mode":"slide",
                    "combined_list_chat_layout":"split",
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
            db.set_setting("combined_list_chat_layout","replace")
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
