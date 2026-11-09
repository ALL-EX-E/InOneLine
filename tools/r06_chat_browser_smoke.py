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
        cc=chat&&getComputedStyle(chat),
        rc=root&&getComputedStyle(root);
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
    mainUnifiedShell:root.classList.contains('r06-main-split-always-shell'),
    rootRadius:rc.borderRadius,
    rootBorderWidth:rc.borderTopWidth,
    rootBorderColor:rc.borderTopColor,
    rootBoxShadow:rc.boxShadow,
    panelBorderWidth:pc.borderTopWidth,
    panelRadius:pc.borderRadius,
    panelBoxShadow:pc.boxShadow,
    chatBorderWidth:cc.borderTopWidth,
    chatRadius:cc.borderRadius,
    chatBoxShadow:cc.boxShadow,
    panelBackground:pc.backgroundColor,
    iframeStable:!window.__r06MainQaFrame || frame === window.__r06MainQaFrame,
    documentStable:!window.__r06MainQaDocument || doc === window.__r06MainQaDocument,
    hasSentinel:[...(cards?.children || [])].some(x=>x.textContent.includes('R06 ZERO visible chat')),
    scrollTransform:document.getElementById('game-list')?.style.transform || '',
    scrollRows:document.querySelectorAll('#game-list .game-row').length,
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


def assert_main_shared_shell(state, label):
    assert state['mainUnifiedShell'], (label, state)
    assert state['rootRadius'] == '8px', (label, state)
    assert state['rootBorderWidth'] == '3px', (label, state)
    assert state['rootBoxShadow'] != 'none', (label, state)
    # This removes competing outlines and rounded corners at the moving
    # List/chat divider without changing separately customized contents.
    assert state['panelBorderWidth'] == '0px', (label, state)
    assert state['chatBorderWidth'] == '0px', (label, state)
    assert state['panelRadius'] == state['chatRadius'] == '0px', (label, state)
    assert state['panelBoxShadow'] == state['chatBoxShadow'] == 'none', (label, state)
    assert state['panelOpacity'] >= 0.99, (label, state)


def static_check(state, label, dynamic_chat=False):
    assert state["panelOpacity"] >= 0.99, (label, state)
    assert state["panelTransform"] == "none", (label, state)
    assert float(state["panelTransition"].split(",")[0].rstrip("s")) == 0, (label, state)
    assert state["panelAnimation"] == "none", (label, state)
    assert state["chatAnimation"] == "none", (label, state)
    if not dynamic_chat:
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
                static_check(m, "initial", dynamic_chat=True)

            # Empty chat in Always reserves half the area when List is visible.
            db.set_setting("multichat_appearance_common",
                           json.dumps({"visibility":"always"}))
            for page in pages:
                m = until(page, lambda a: a["shown"] and
                          0 < a["chatHeight"] < a["rootHeight"] and
                          a["chatTransition"] == "0s" and a["mainUnifiedShell"],
                          "fixed-height always-chat / split settled")
                static_check(m, "always-chat split")
                assert_main_shared_shell(m, "main static 50/50")

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
                assert_main_shared_shell(m, "main static 100% chat")

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
                assert_main_shared_shell(m, "main static restored split")

            # Hide-empty mode only reserves room when a message exists.
            db.set_setting("multichat_appearance_common",
                           json.dumps({"visibility":"hide_empty"}))
            for page in pages:
                m = until(page, lambda a: a["shown"] and a["chatHeight"] == 0,
                          "hide-empty chat releases its area")
                static_check(m, "empty chat", dynamic_chat=True)
                assert not m['mainUnifiedShell'], m
                assert m['panelBorderWidth'] == '3px', m

            assert state.ingest(ChatMessage("twitch", "chan", "zero-message",
                                            "alice", "R06 ZERO visible chat"))
            for page in pages:
                m = until(page, lambda a: a["shown"] and a["count"] == 1 and
                          a["chatHeight"] > 15 and not a["mainUnifiedShell"] and
                          a["chatTransition"].startswith("1.5s"),
                          "dynamic Twitch chat settles to hide-empty intrinsic height")
                static_check(m, "dynamic chat", dynamic_chat=True)
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
                assert_main_shared_shell(idle, "main command before entrance")
                evaluate(page,
                    "(window.__r06MainQaFrame=document.querySelector("
                    "'#list-chat iframe'),window.__r06MainQaDocument="
                    "window.__r06MainQaFrame.contentDocument,true)")
            for direction in ("left", "right", "top", "bottom"):
                db.set_setting("list_slide_direction", direction)
                # /overlay and /combined-overlay apply saved settings via
                # their existing 1-second /api/data poll. Wait for the next
                # full poll before issuing a Twitch command, otherwise this
                # test races a newly saved direction against the old one.
                QTest.qWait(1600)
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
                            assert_main_shared_shell(point, "main command moving seam")
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
                    assert_main_shared_shell(held, "main command stable 50/50")
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
                            assert_main_shared_shell(point, "main command moving seam")
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
                    assert_main_shared_shell(after, "main command restored 100% chat")

            # New 0-second mode: server state stays ON until the next unique
            # Twitch command; the same main compositor uses the accepted
            # full chat mask and reversible 2-second entrance/exit.
            db.set_settings_bulk({
                "list_slide_duration":"0",
                "list_slide_direction":"left",
            })
            api.configure_list_show("slide", "!list", 0)
            QTest.qWait(1600)
            for page in pages:
                idle = until(page, lambda a: not a["shown"] and
                             a["combinedSync"] == "idle",
                             "main zero toggle initially hidden")
                prior_exit = idle["exitCount"]
            QTest.qWait(1900)  # Offscreen clock must not reset on show.
            assert state.ingest(ChatMessage(
                "twitch", "chan", "main-zero-on", "qa_viewer", "!list"
            ))
            for page in pages:
                opening = until(page, lambda a: a["motionKind"] == "enter" and
                                a["lastEntrance"] == "left",
                                "main zero command entrance")
                assert_main_shared_shell(opening, "zero command entrance shell")
                held_zero = until(page, lambda a: a["shown"] and
                                  a["phase"] == "hold" and
                                  a["combinedSync"] == "idle" and
                                  a["scrollRows"] > 4,
                                  "main zero command held indefinitely")
                assert held_zero["iframeStable"] and held_zero["hasSentinel"], held_zero
                assert held_zero["scrollTransform"] not in ("", "translateY(0px)"), (
                    "Main hidden List restarted its scroll on command", held_zero
                )
                assert_main_shared_shell(held_zero, "zero held 50/50")
            QTest.qWait(1800)
            for page in pages:
                still = evaluate(page, METRICS)
                assert still["shown"] and still["exitCount"] == prior_exit, (
                    "0-second command expired without second Twitch event", still
                )
            assert not state.ingest(ChatMessage(
                "twitch", "chan", "main-zero-on", "qa_viewer", "!list"
            ))
            assert state.ingest(ChatMessage(
                "twitch", "chan", "main-zero-off", "qa_viewer", "!list"
            ))
            for page in pages:
                closing = until(page, lambda a: a["motionKind"] == "exit" and
                                a["lastExit"] == "left" and
                                a["exitCount"] == prior_exit+1,
                                "main zero command reverse exit")
                assert_main_shared_shell(closing, "zero command exit shell")
                hidden_zero = until(page, lambda a: not a["shown"] and
                                    a["phase"] == "idle" and
                                    a["combinedSync"] == "idle" and
                                    abs(a["chatHeight"]-a["rootHeight"]) <= 3,
                                    "main zero command restored full Twitch chat")
                assert hidden_zero["hasSentinel"] and hidden_zero["iframeStable"], hidden_zero
                assert_main_shared_shell(hidden_zero, "zero hidden 100% chat")

            # Hide-empty is now a first-class partner of the accepted shared
            # List motion. It grows up from zero, with List using the rest.
            db.set_settings_bulk({
                "multichat_appearance_common":json.dumps({"visibility":"hide_empty"}),
                "list_slide_duration":"0",
                "list_slide_animation_seconds":"1.00",
                "list_animation_seconds":"0.60",
                "combined_list_chat_layout":"split",
            })
            api.configure_list_show("slide", "!list", 0)
            state.clear_chat("twitch", "chan")
            for page in pages:
                empty = until(page, lambda a: not a["shown"] and
                              a["chatHeight"] <= 2 and a["listHeight"] <= 2,
                              "hide-empty starts with no chat region")
            assert state.ingest(ChatMessage(
                "twitch", "chan", "dynamic-first", "alice", "R06 ZERO visible chat"))
            for page in pages:
                first = until(page, lambda a:
                    not a["shown"] and a["count"] == 1 and a["hasSentinel"] and
                    8 < a["chatHeight"] < a["rootHeight"] / 2,
                    "first message grows compact chat from bottom")
                assert first["chatTransition"].startswith("0.6s"), first
                assert first["iframeStable"], first
                # A parked main OBS composition is permitted to navigate its
                # child ONCE on reattachment. The accepted iframe/document
                # identity invariant begins after that first rendered message
                # and must hold throughout every subsequent List motion.
                page.runJavaScript("""(() => {
                  window.__r06MainQaFrame = document.querySelector('#list-chat iframe');
                  window.__r06MainQaDocument = window.__r06MainQaFrame?.contentDocument;
                })()""")
                fresh = until(page, lambda a:
                    a["hasSentinel"] and a["iframeStable"] and a["documentStable"],
                    "hide-empty first live iframe established")

            for direction in ("left","right","top","bottom"):
                db.set_setting("list_slide_direction", direction)
                QTest.qWait(2200)  # Allow browser API poll to apply saved direction
                for page in pages:
                    prior = until(page, lambda a: not a["shown"] and
                                  a["motionKind"] == "idle",
                                  "hide-empty idle before "+direction)
                assert state.ingest(ChatMessage(
                    "twitch", "chan", "dynamic-on-"+direction, "alice", "!list"))
                for page in pages:
                    entry = until(page, lambda a: a["combinedSync"] == "command-enter"
                                  and a["motionKind"] == "enter"
                                  and a["lastEntrance"] == direction,
                                  "hide-empty shared entrance "+direction)
                    assert entry["motionDuration"] == 1000, entry
                    assert entry["iframeStable"] and entry["documentStable"], entry
                    held = until(page, lambda a: a["shown"] and not a["replace"]
                                 and a["phase"] == "hold"
                                 and a["combinedSync"] == "idle"
                                 and a["chatHeight"] <= a["rootHeight"] / 2 + 3
                                 and a["listHeight"] >= a["rootHeight"] / 2 - 12
                                 and a["chatBottomGap"] <= 3,
                                 "hide-empty list fills to live chat edge "+direction)
                    assert held["hasSentinel"] and held["iframeStable"], held
                if direction == "left":
                    # Extra messages while List is shown grow the chat upward,
                    # cap it at half, and keep older rows in the existing iframe.
                    for index in range(8):
                        assert state.ingest(ChatMessage(
                            "twitch","chan","dynamic-grow-"+str(index),
                            "alice","R06 growing chat "+str(index)))
                    for page in pages:
                        grown = until(page, lambda a:
                            a["shown"] and a["count"] >= 9 and
                            a["chatHeight"] > first["chatHeight"] + 35 and
                            a["chatHeight"] <= a["rootHeight"] / 2 + 4 and
                            a["listHeight"] + a["chatHeight"] <= a["rootHeight"] + 4,
                            "chat grows upward under live List")
                        assert grown["hasSentinel"] and grown["iframeStable"], grown
                assert state.ingest(ChatMessage(
                    "twitch","chan","dynamic-off-"+direction,"alice","!list"))
                for page in pages:
                    leave = until(page, lambda a: a["combinedSync"] == "command-exit"
                                  and a["motionKind"] == "exit" and
                                  a["lastExit"] == direction,
                                  "hide-empty reverse List exit "+direction)
                    assert leave["motionDuration"] == 1000, leave
                    restored = until(page, lambda a: not a["shown"] and
                                     a["motionKind"] == "idle" and
                                     a["chatHeight"] <= a["rootHeight"] + 3 and
                                     a["chatHeight"] > 10,
                                     "hide-empty chat returns to natural height "+direction)
                    assert restored["iframeStable"] and restored["documentStable"], restored

            db.set_setting("combined_list_chat_layout","replace")
            QTest.qWait(1300)
            for direction in ("left","right","top","bottom"):
                db.set_setting("list_slide_direction",direction)
                QTest.qWait(2200)  # Allow browser API poll to apply saved direction
                assert state.ingest(ChatMessage(
                    "twitch","chan","dynamic-replace-on-"+direction,"alice","!list"))
                for page in pages:
                    entry = until(page, lambda a:
                        a["combinedSync"] == "replace-command-enter" and
                        a["motionKind"] == "enter" and a["lastEntrance"] == direction,
                        "hide-empty replacement enters "+direction)
                    assert entry["iframeStable"] and entry["documentStable"], entry
                    full = until(page, lambda a:
                        a["shown"] and a["replace"] and a["phase"] == "hold" and
                        a["listHeight"] >= a["rootHeight"]-3,
                        "hide-empty replacement fills entire region "+direction)
                    assert full["hasSentinel"],full
                assert state.ingest(ChatMessage(
                    "twitch","chan","dynamic-replace-off-"+direction,"alice","!list"))
                for page in pages:
                    leave = until(page, lambda a:
                        a["combinedSync"] == "replace-command-exit" and
                        a["motionKind"] == "exit",
                        "hide-empty replacement reverses "+direction)
                    restored = until(page, lambda a:
                        not a["shown"] and not a["replace"] and
                        a["motionKind"] == "idle" and
                        a["chatHeight"] > 10 and a["hasSentinel"],
                        "hide-empty replacement restores messages "+direction)
                    assert restored["iframeStable"] and restored["documentStable"], restored
            print("R06_MAIN_HIDE_EMPTY_SPLIT_REPLACE_MOTION_PASS", flush=True)

            # The OBS switch must remove the chat without reserving empty space.
            state.set_obs_enabled("twitch", False)
            db.set_setting("list_overlay_show_mode","always")
            api.configure_list_show("always", "!list", 20)
            for page in pages:
                m=until(page, lambda a: a["shown"] and a["chatHeight"] == 0 and
                        a["listHeight"] > 10,
                        "OBS Twitch disabled / full List")
                static_check(m, "OBS chat disabled", dynamic_chat=True)
            print("R06_ZERO_BROWSER_ALL_PASS", flush=True)
        finally:
            for view in views:
                view.close()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
