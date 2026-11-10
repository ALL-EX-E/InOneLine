"""R06 combined main-overlay and dedicated OBS URL: static List/chat geometry.

All previous movement animation tests are preserved in Git history. This new
baseline deliberately checks there is NO List/chat transition, wipe or fade.
"""
from __future__ import annotations

import json
import os
import socket
import threading
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
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from tools.qt_browser_test_wait import wait_with_http_workers
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
        wait_with_http_workers(25)
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
  const coveredTop = Math.max(l.top, c.top);
  const coveredBottom = Math.min(l.bottom, c.bottom);
  const chatCenterX = (c.left + c.right) / 2;
  let coveredChatClipped = false, exposedChatVisible = false;
  if (coveredBottom - coveredTop > 2) {
    // Main OBS disables pointer events on its outer container. Enable hit
    // testing only for this measurement, with no change to its painted mask.
    const pointerEvents = chat.style.pointerEvents;
    chat.style.pointerEvents = "auto";
    coveredChatClipped =
      !document.elementsFromPoint(chatCenterX, (coveredTop + coveredBottom) / 2).includes(chat);
    exposedChatVisible = c.bottom - l.bottom > 4 &&
      document.elementsFromPoint(chatCenterX, (c.bottom + l.bottom) / 2).includes(chat);
    chat.style.pointerEvents = pointerEvents;
  }
  return {
    ready:true, shown:root.classList.contains('r06-shown'),
    replace:root.classList.contains('r06-replace'),
    listHeight:l.height, chatHeight:c.height, rootHeight:r.height,
    listPanelHeight:panel.getBoundingClientRect().height,
    coveredChatClipped, exposedChatVisible,
    rootTop:r.top, rootLeft:r.left, rootWidth:r.width,
    listTop:l.top, listBottom:l.bottom, chatTop:c.top,
    chatBottomGap: +(r.bottom-c.bottom).toFixed(2),
    combinedSync:root.dataset.r06CombinedSync || 'idle',
    motionKind:root.dataset.r06StandaloneMotionKind || 'idle',
    motionDuration:Number(root.dataset.r06StandaloneLastMotionDurationMs || 0),
    phase:root.dataset.r06StandalonePhase || 'idle',
    lastEntrance:root.dataset.r06StandaloneLastEntrance || '',
    lastExit:root.dataset.r06StandaloneLastExit || '',
    appliedDirection:root.dataset.r06AppliedListDirection || '',
    appliedComposeMode:root.dataset.r06AppliedComposeMode || '',
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
        wait_with_http_workers(140)
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
                wait_with_http_workers(300)
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
                # A Windows Chromium callback may arrive only after the
                # 2-second WAAPI finishes under runner load. The first
                # measured exit frame is already proof of a real transition;
                # check its geometry and any additionally sampled frames,
                # then independently verify the settled end state below.
                assert abs(first["chatBottomGap"]) < 3, first
                midframes = [first]
                for _ in range(10):
                    frame = evaluate(page, METRICS)
                    if frame["combinedSync"] == "split-exit":
                        midframes.append(frame)
                        assert abs(frame["chatBottomGap"]) < 3, frame
                    else:
                        break
                    wait_with_http_workers(135)
                assert midframes[0]["motionKind"] == "exit", midframes
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
            # Keep a passive browser-side observer: the sequential poll fix
            # must not stall saved settings or mask a failed /api/data response.
            for page in pages:
                assert evaluate(page, """(() => {
                  const previousFetch = window.fetch.bind(window);
                  const p = {started:0, completed:0, errors:0,
                             lastDirection:null, lastStatus:null};
                  window.__r06SavedDirectionPoll = p;
                  window.fetch = (...args) => {
                    const url=String(args[0]?.url || args[0] || '');
                    if (!url.includes('/api/data')) return previousFetch(...args);
                    p.started++;
                    return previousFetch(...args).then(response => {
                      p.completed++;
                      p.lastStatus=response.status;
                      response.clone().json().then(data => {
                        p.lastDirection=data.overlay?.list_slide_direction;
                      }).catch(() => {p.errors++;});
                      return response;
                    }, error => {p.errors++;throw error;});
                  };
                  return true;
                })()""") is True
            for direction in ("left", "right", "top", "bottom"):
                db.set_setting("list_slide_direction", direction)
                assert db.get_setting("list_slide_direction") == direction
                with urlopen(api.base_url + "/api/data", timeout=8) as response:
                    immediate = json.load(response)
                assert immediate["overlay"]["list_slide_direction"] == direction, (
                    "Database/API direction mismatch", direction, immediate["overlay"]["list_slide_direction"])
                # /overlay and /combined-overlay apply saved settings via
                # their existing 1-second /api/data poll. Wait for the next
                # full poll before issuing a Twitch command, otherwise this
                # test races a newly saved direction against the old one.
                wait_with_http_workers(1600)
                for page in pages:
                    try:
                        idle = until(page, lambda a: not a["shown"] and
                                     a["combinedSync"] == "idle" and
                                     a["motionKind"] == "idle" and
                                     a["appliedDirection"] == direction and
                                     a["appliedComposeMode"] == "split",
                                     "main saved direction applied before command "+direction)
                    except AssertionError:
                        probe = evaluate(page, """JSON.stringify({
                          ...window.__r06SavedDirectionPoll,
                          pageReady:document.readyState,
                          current:document.getElementById('list-composition')?.dataset.r06AppliedListDirection
                        })""")
                        with urlopen(api.base_url + "/api/data", timeout=8) as response:
                            latest = json.load(response)
                        print("R06_SAVED_DIRECTION_DIAGNOSTIC", {
                            "expected":direction, "database":db.get_setting("list_slide_direction"),
                            "api":latest["overlay"]["list_slide_direction"],
                            "browser":probe}, flush=True)
                        raise
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
                        wait_with_http_workers(125)
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
                        wait_with_http_workers(125)
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
            wait_with_http_workers(1600)
            for page in pages:
                idle = until(page, lambda a: not a["shown"] and
                             a["combinedSync"] == "idle" and
                             a["motionKind"] == "idle" and
                             a["appliedDirection"] == "left" and
                             a["appliedComposeMode"] == "split",
                             "main zero toggle initially hidden after saved direction")
                prior_exit = idle["exitCount"]
            wait_with_http_workers(1900)  # Offscreen clock must not reset on show.
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
            wait_with_http_workers(1800)
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

                for page in pages:
                    until(page, lambda a: a["appliedDirection"] == direction and
                          a["appliedComposeMode"] == "split",
                          "Chromium applied hide-empty split "+direction)

                for page in pages:
                    prior = until(page, lambda a: not a["shown"] and
                                  a["motionKind"] == "idle",
                                  "hide-empty idle before "+direction)
                assert state.ingest(ChatMessage(
                    "twitch", "chan", "dynamic-on-"+direction, "alice", "!list"))
                for page in pages:
                    # A 1-second entrance can finish before a loaded Windows
                    # Chromium callback is delivered. An observed entrance OR
                    # its correctly counted, fully visible hold is valid here;
                    # longer motion tests below still inspect intermediate
                    # frames and the live Twitch mask.
                    entry = until(page, lambda a:
                        a["lastEntrance"] == direction and
                        a["entranceCount"] == prior["entranceCount"] + 1 and
                        a["motionDuration"] == 1000 and a["shown"] and
                        ((a["combinedSync"] == "command-enter" and
                          a["motionKind"] == "enter") or
                         (a["phase"] == "hold" and a["motionKind"] == "idle" and
                          a["listHeight"] >= a["rootHeight"] / 2 - 12)),
                        "hide-empty shared entrance/hold "+direction)
                    assert entry["motionDuration"] == 1000, entry
                    assert entry["iframeStable"] and entry["documentStable"], entry
                    held = until(page, lambda a: a["shown"] and not a["replace"]
                                 and a["phase"] == "hold"
                                 and a["combinedSync"] == "idle"
                                 and a["chatHeight"] <= a["rootHeight"] + 3
                                 and a["listHeight"] >= a["rootHeight"] / 2 - 12
                                 and (a["chatTop"] >= a["listBottom"] - 2 or
                                      a["coveredChatClipped"])
                                 and a["chatBottomGap"] <= 3,
                                 "hide-empty list fills to live chat edge "+direction)
                    assert held["hasSentinel"] and held["iframeStable"], held
                if direction == "left":
                    # Extra messages while List is shown grow the chat upward,
                    # cap its exposed area, and retain rows in the existing iframe.
                    for index in range(8):
                        assert state.ingest(ChatMessage(
                            "twitch","chan","dynamic-grow-"+str(index),
                            "alice","R06 growing chat "+str(index)))
                    obs_ids = [row["external_id"] for row in
                               state.snapshot(for_obs=True)["messages"]]
                    with urlopen(api.base_url + "/api/multichat", timeout=5) as response:
                        api_ids = [row["external_id"] for row in
                                   json.load(response)["messages"]]
                    assert len(obs_ids) >= 9 and obs_ids == api_ids, (
                        "Twitch growth not published in authoritative state/API",
                        obs_ids, api_ids)
                    for page in pages:
                        try:
                            grown = until(page, lambda a:
                                a["shown"] and a["count"] >= 9 and
                                a["chatHeight"] > first["chatHeight"] + 35 and
                                a["chatHeight"] <= a["rootHeight"] + 3 and
                                (a["chatTop"] >= a["listBottom"] - 2 or
                                 a["coveredChatClipped"]),
                                "chat grows upward under live List")
                        except AssertionError as original:
                            # Non-mutating, failure-only browser-network probe.
                            # Do not monkeypatch fetch or force DOM rendering.
                            page.runJavaScript("""(() => {
                              const probe=window.__r06TransportProbe={
                                parentData:{status:'pending'},
                                parentChat:{status:'pending'},
                                childChat:{status:'pending'},
                                parentXhr:{status:'pending'}
                              };
                              function check(context, url, key) {
                                context.fetch(url, {cache:'no-store'})
                                  .then(r=>r.ok?r.json():Promise.reject(Error('HTTP '+r.status)))
                                  .then(value=>probe[key]={
                                    status:'ok', count:value.messages?.length ?? null,
                                    hasMessages:value.multichat?.has_messages ?? null
                                  }).catch(e=>probe[key]={status:'error',error:String(e)});
                              }
                              check(window, '/api/data', 'parentData');
                              check(window, '/api/multichat', 'parentChat');
                              const frame=document.querySelector('#list-chat iframe');
                              if(frame?.contentWindow)
                                check(frame.contentWindow, '/api/multichat', 'childChat');
                              else probe.childChat={status:'no-frame'};
                              const xhr=new XMLHttpRequest();
                              xhr.open('GET','/api/multichat',true);
                              xhr.onload=()=>{probe.parentXhr={
                                status:'ok', httpStatus:xhr.status,
                                count:JSON.parse(xhr.responseText)?.messages?.length ?? null};};
                              xhr.onerror=()=>{probe.parentXhr={status:'error'};};
                              xhr.send();
                            })()""")
                            wait_with_http_workers(2200)
                            probe = evaluate(page, """JSON.stringify((() => {
                              const iframe=document.querySelector('#list-chat iframe');
                              return {requests:window.__r06TransportProbe,
                                      childReady:iframe?.contentDocument?.readyState,
                                      childRender:typeof iframe?.contentWindow?.IOLRenderEmbeddedChatState,
                                      cards:iframe?.contentDocument?.getElementById('messages')?.children.length};
                            })())""")
                            raise AssertionError("Live Twitch transport diagnostic: " +
                                repr({"obs_count":len(obs_ids), "http_count":len(api_ids),
                                      "probe":probe, "original":str(original)})) from original
                        assert grown["hasSentinel"] and grown["iframeStable"], grown
                assert state.ingest(ChatMessage(
                    "twitch","chan","dynamic-off-"+direction,"alice","!list"))
                for page in pages:
                    leave = until(page, lambda a:
                        a["lastExit"] == direction and
                        a["exitCount"] == prior["exitCount"] + 1 and
                        a["motionDuration"] == 1000 and
                        ((a["combinedSync"] == "command-exit" and
                          a["motionKind"] == "exit") or
                         (a["motionKind"] == "idle" and not a["shown"] and
                          a["listHeight"] <= 2)),
                        "hide-empty reverse List exit/idle "+direction)
                    assert leave["motionDuration"] == 1000, leave
                    restored = until(page, lambda a: not a["shown"] and
                                     a["motionKind"] == "idle" and
                                     a["chatHeight"] <= a["rootHeight"] + 3 and
                                     a["chatHeight"] > 10,
                                     "hide-empty chat returns to natural height "+direction)
                    assert restored["iframeStable"] and restored["documentStable"], restored

            db.set_setting("combined_list_chat_layout","replace")
            wait_with_http_workers(1300)
            for direction in ("left","right","top","bottom"):
                db.set_setting("list_slide_direction",direction)

                for page in pages:
                    prior_replace = until(page, lambda a:
                        not a["shown"] and a["motionKind"] == "idle" and
                        a["appliedDirection"] == direction and
                        a["appliedComposeMode"] == "replace",
                        "Chromium applied hide-empty replace "+direction)

                assert state.ingest(ChatMessage(
                    "twitch","chan","dynamic-replace-on-"+direction,"alice","!list"))
                for page in pages:
                    entry = until(page, lambda a:
                        a["lastEntrance"] == direction and
                        a["entranceCount"] == prior_replace["entranceCount"] + 1 and
                        a["motionDuration"] == 1000 and a["shown"] and
                        ((a["combinedSync"] == "replace-command-enter" and
                          a["motionKind"] == "enter") or
                         (a["motionKind"] == "idle" and a["phase"] == "hold" and
                          a["replace"] and a["listHeight"] >= a["rootHeight"] - 3)),
                        "hide-empty replacement enters/holds "+direction)
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
                        a["lastExit"] == direction and
                        a["exitCount"] == prior_replace["exitCount"] + 1 and
                        a["motionDuration"] == 1000 and
                        ((a["combinedSync"] == "replace-command-exit" and
                          a["motionKind"] == "exit") or
                         (a["motionKind"] == "idle" and not a["shown"] and
                          a["listHeight"] <= 2)),
                        "hide-empty replacement reverses/settles "+direction)
                    restored = until(page, lambda a:
                        not a["shown"] and not a["replace"] and
                        a["motionKind"] == "idle" and
                        a["chatHeight"] > 10 and a["hasSentinel"],
                        "hide-empty replacement restores messages "+direction)
                    assert restored["iframeStable"] and restored["documentStable"], restored
            # Messages arriving in the MIDDLE of a long entrance or
            # reverse exit must change the actual Twitch geometry, rather than
            # jump on the List's WAAPI finish. Test both real /overlay views.
            for composition in ("split", "replace"):
                db.set_settings_bulk({
                    "combined_list_chat_layout": composition,
                    "list_slide_animation_seconds": "6.00",
                    "list_slide_direction": "left",
                })
                state.clear_chat("twitch", "chan")
                assert state.ingest(ChatMessage(
                    "twitch", "chan", "video-start-" + composition,
                    "alice", "R06 movie first message"))
                expected_id = "video-start-" + composition
                server_ids = [row["external_id"] for row in
                              state.snapshot(for_obs=True)["messages"]]
                with urlopen(api.base_url + "/api/multichat", timeout=5) as response:
                    http_ids = [row["external_id"] for row in
                                json.load(response)["messages"]]
                assert server_ids == http_ids == [expected_id], (
                    "Clear/new message did not propagate to server API",
                    composition, server_ids, http_ids)
                for page in pages:
                    try:
                        before = until(page, lambda a:
                            not a["shown"] and a["count"] == 1 and
                            a["appliedComposeMode"] == composition and
                            a["appliedDirection"] == "left" and
                            15 < a["chatHeight"] < a["rootHeight"] / 2,
                            "one-message dynamic chat before movie " + composition)
                    except AssertionError as original:
                        # Passive failure-only diagnostic. Do NOT replace
                        # fetch or force the embedded renderer to update.
                        page.runJavaScript("""(() => {
                          window.__r06ChatNetworkProbe = {status:"pending"};
                          fetch('/api/multichat', {cache:'no-store'})
                            .then(response => response.ok ? response.json() :
                                  Promise.reject(Error('HTTP '+response.status)))
                            .then(snapshot => {window.__r06ChatNetworkProbe = {
                              status:"ok", count:snapshot.messages?.length ?? -1,
                              ids:(snapshot.messages || []).map(x=>x.external_id)
                            };})
                            .catch(error => {window.__r06ChatNetworkProbe = {
                              status:"error", error:String(error)
                            };});
                        })()""")
                        wait_with_http_workers(1600)
                        probe = evaluate(page, """JSON.stringify((() => {
                          const iframe=document.querySelector('#list-chat iframe');
                          return {network:window.__r06ChatNetworkProbe,
                                  childRender:typeof iframe?.contentWindow?.IOLRenderEmbeddedChatState,
                                  childReady:iframe?.contentDocument?.readyState,
                                  count:iframe?.contentDocument?.getElementById('messages')?.children.length};
                        })())""")
                        raise AssertionError(
                            "Chromium stale Twitch diagnostic: " +
                            repr({"scenario":composition, "server_ids":server_ids,
                                  "http_ids":http_ids, "probe":probe,
                                  "original":str(original)})) from original
                assert state.ingest(ChatMessage(
                    "twitch", "chan", "video-enter-" + composition,
                    "alice", "!list"))
                for page in pages:
                    entering = until(page, lambda a:
                        a["motionKind"] == "enter" and
                        a["motionDuration"] == 6000 and
                        a["lastEntrance"] == "left" and
                        (a["combinedSync"] == "command-enter" if composition == "split"
                         else a["combinedSync"] == "replace-command-enter"),
                        "movie List entry starts " + composition)
                    assert abs(entering["chatBottomGap"]) < 4, entering
                    # A content-sized Twitch frame must NEVER temporarily
                    # become 100% high just because Replace uses a full List.
                    assert entering["chatHeight"] < entering["rootHeight"] / 2, entering
                for index in range(9):
                    assert state.ingest(ChatMessage(
                        "twitch", "chan", "video-enter-grow-" + composition + str(index),
                        "alice", "Message while List enters " + str(index)))
                for page in pages:
                    growing = until(page, lambda a:
                        a["motionKind"] == "enter" and
                        a["count"] >= 10 and
                        a["chatHeight"] > entering["chatHeight"] + 25 and
                        abs(a["chatBottomGap"]) < 4,
                        "chat grows while List enters " + composition)
                    assert growing["iframeStable"] and growing["documentStable"], growing
                    assert growing["panelOpacity"] >= .99, growing
                    held = until(page, lambda a:
                        a["motionKind"] == "idle" and a["phase"] == "hold" and
                        a["shown"], "movie List entry settles " + composition)
                assert state.ingest(ChatMessage(
                    "twitch", "chan", "video-exit-" + composition,
                    "alice", "!list"))
                for page in pages:
                    exiting = until(page, lambda a:
                        a["motionKind"] == "exit" and a["motionDuration"] == 6000 and
                        a["lastExit"] == "left", "movie List exit starts " + composition)
                    assert abs(exiting["chatBottomGap"]) < 4, exiting
                assert state.ingest(ChatMessage(
                    "twitch", "chan", "video-exit-grow-" + composition,
                    "alice", "Message DURING reverse List exit"))
                for page in pages:
                    latest = until(page, lambda a:
                        a["motionKind"] == "exit" and a["count"] >= 11 and
                        abs(a["chatBottomGap"]) < 4,
                        "chat receives messages during reverse exit " + composition)
                    assert latest["iframeStable"] and latest["documentStable"], latest
                    settled = until(page, lambda a:
                        not a["shown"] and a["motionKind"] == "idle" and
                        a["count"] >= 11 and 0 < a["chatHeight"] <= a["rootHeight"] + 3 and
                        abs(a["chatBottomGap"]) < 4,
                        "natural Twitch height survives reverse exit " + composition)
                    assert settled["iframeStable"] and settled["documentStable"], settled
            # FIX-092: the previous browser test only entered with a SHORT
            # one-message Twitch frame, which could not detect the user's
            # regression: a fully populated chat SHRANK before the moving
            # List finished entering. Exercise all directions in combined
            # modes on the real main OBS page, with chat at full height.
            db.set_setting("list_slide_animation_seconds", "2.00")
            state.clear_chat("twitch", "chan")
            for index in range(24):
                assert state.ingest(ChatMessage(
                    "twitch", "chan", "full-chat-fix092-" + str(index),
                    "alice", "FULL Twitch message " + str(index)))
            for composition in ("split", "replace"):
                for direction in ("left", "right", "top", "bottom"):
                    db.set_settings_bulk({
                        "combined_list_chat_layout": composition,
                        "list_slide_direction": direction,
                    })
                    for page in pages:
                        before = until(page, lambda a:
                            not a["shown"] and a["motionKind"] == "idle" and
                            a["appliedComposeMode"] == composition and
                            a["appliedDirection"] == direction and
                            a["count"] >= 24 and
                            a["chatHeight"] >= a["rootHeight"] - 2,
                            "full Twitch frame before List entry " +
                            composition + " " + direction)
                    # At zero seconds, a command must toggle the shared
                    # server-held bit ON exactly once. This is independent
                    # from the List animation and catches a real unexpected
                    # OFF rather than silently tolerating a missing phase.
                    server_before = state.snapshot()["list_show"]
                    assert server_before.get("held") is False, (
                        "Unexpected zero-toggle server ON before command",
                        composition, direction, server_before)
                    assert state.ingest(ChatMessage(
                        "twitch", "chan",
                        "fix092-show-" + composition + "-" + direction,
                        "alice", "!list"))
                    server_on = state.snapshot()["list_show"]
                    assert server_on.get("held") is True and (
                        server_on["sequence"] == server_before["sequence"] + 1), (
                        "Server failed to latch ONE zero-toggle command",
                        composition, direction, server_before, server_on)
                    for page in pages:
                        entering = until(page, lambda a:
                              a["motionKind"] == "enter" and
                              a["motionDuration"] == 2000 and
                              a["lastEntrance"] == direction,
                              "FIX-092 List begins over FULL chat " +
                              composition + " " + direction)
                        assert state.snapshot()["list_show"].get("held") is True, (
                            "Server unexpectedly toggled OFF during List entry",
                            composition, direction, entering,
                            state.snapshot()["list_show"])
                    # Sample an actual intermediate frame, not just endpoints.
                    wait_with_http_workers(350)
                    for page in pages:
                        m = evaluate(page, METRICS)
                        server_mid = state.snapshot()["list_show"]
                        assert server_mid.get("held") is True, (
                            "Server toggled OFF without a second explicit command",
                            composition, direction, server_on, server_mid, m)
                        assert m["motionKind"] == "enter", (
                            "Browser List left its entrance before 2 seconds",
                            composition, direction, server_on, server_mid, m)
                        assert m["chatHeight"] >= m["rootHeight"] * .90, (
                            "Premature Twitch shrink", composition, direction, m)
                        assert abs(m["chatBottomGap"]) < 4, m
                        assert m["chatClipPath"] == "none" or (
                            m["chatClipPath"].startswith('path(evenodd, ')), (
                            "Twitch clip must subtract real painted List rectangle",
                            composition, direction, m)
                        assert m["iframeStable"] and m["documentStable"], m
                    for page in pages:
                        hold = until(page, lambda a:
                            a["motionKind"] == "idle" and a["phase"] == "hold" and
                            a["listHeight"] >= a["rootHeight"] *
                                (.47 if composition == "split" else .97),
                            "List remains painted after full-chat entrance " +
                            composition + " " + direction)
                        assert hold["panelOpacity"] > .99, hold
                    # The previous candidate shrank the chat AFTER WAAPI ended.
                    # Check the actual settled hold before issuing the exit.
                    wait_with_http_workers(1100)
                    for page in pages:
                        held = evaluate(page, METRICS)
                        assert abs(held["chatHeight"] - before["chatHeight"]) <= 3, held
                        assert abs(held["listTop"] - held["rootTop"]) <= 3, held
                        assert abs(held["listPanelHeight"] - held["listHeight"]) <= 3, held
                        assert held["coveredChatClipped"], held
                        if composition == "split":
                            assert .47 <= held["listHeight"] / held["rootHeight"] <= .53, held
                            assert held["exposedChatVisible"], held
                        else:
                            assert abs(held["listHeight"] - held["rootHeight"]) <= 3, held
                    assert state.ingest(ChatMessage(
                        "twitch", "chan",
                        "fix092-hide-" + composition + "-" + direction,
                        "alice", "!list"))
                    server_off = state.snapshot()["list_show"]
                    assert server_off.get("held") is False and (
                        server_off["sequence"] == server_on["sequence"] + 1), (
                        "Server zero-toggle OFF must follow exactly one command",
                        composition, direction, server_on, server_off)
                    for page in pages:
                        exiting = until(page, lambda a: a["motionKind"] == "exit" and
                              a["lastExit"] == direction,
                              "FIX-092 reverse exit " + composition + " " + direction)
                        assert abs(exiting["chatHeight"] - before["chatHeight"]) <= 3, exiting
                        end = until(page, lambda a:
                            a["motionKind"] == "idle" and not a["shown"] and
                            a["chatHeight"] > a["rootHeight"] * .90,
                            "full Twitch chat restored " +
                            composition + " " + direction)
                        assert end["iframeStable"] and end["documentStable"], end
            print("R06_FIX092_FULL_CHAT_ALL_DIRECTIONS_PASS", flush=True)

            print("R06_MAIN_LIVE_MOTION_RESIZE_VIDEO_PASS", flush=True)
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
            # R06/ORDERED-POLL-098: force REAL HTTP responses out of order.
            # The threaded test API snapshots the first old state, holds its
            # response, then serves a newer Save on a different request.
            # No JS fetch replacement: this exercises the actual page poll.
            db.set_setting("list_slide_direction", "left")
            for page in pages:
                until(page, lambda a: a["appliedDirection"] == "left" and
                      a["motionKind"] == "idle",
                      "main ordered-poll baseline left saved direction")
            original_stream_payload = db.current_stream_payload
            first_ready = threading.Event()
            first_release = threading.Event()
            first_returned = threading.Event()
            counter_lock = threading.Lock()
            request_state = {"started": 0, "completed": 0, "old_direction": None}

            def delayed_stream_payload():
                with counter_lock:
                    request_state["started"] += 1
                    first = request_state["started"] == 1
                payload = original_stream_payload()
                if first:
                    request_state["old_direction"] = payload["overlay"]["list_slide_direction"]
                    first_ready.set()
                    if not first_release.wait(45):
                        raise AssertionError("R06 main old HTTP reply was never released")
                    first_returned.set()
                with counter_lock:
                    request_state["completed"] += 1
                return payload

            db.current_stream_payload = delayed_stream_payload
            try:
                deadline = time.monotonic() + 12
                while not first_ready.is_set() and time.monotonic() < deadline:
                    wait_with_http_workers(100)
                assert first_ready.is_set(), request_state
                assert request_state["old_direction"] == "left", request_state
                db.set_setting("list_slide_direction", "right")
                for page in pages:
                    until(page, lambda a:
                          a["appliedDirection"] == "right" and
                          a["motionKind"] == "idle",
                          "main real HTTP new Save with older reply blocked")
                assert request_state["started"] >= 2, request_state
                assert request_state["completed"] >= 1, request_state
                first_release.set()
                deadline = time.monotonic() + 8
                while not first_returned.is_set() and time.monotonic() < deadline:
                    wait_with_http_workers(50)
                assert first_returned.is_set(), request_state
                # A stale response must not flip the saved direction even
                # for a single observed frame before the next poll repairs it.
                for _ in range(28):
                    for page in pages:
                        stable = evaluate(page, METRICS)
                        assert stable["appliedDirection"] == "right", (
                            "Old main HTTP reply reverted newer Save", stable)
                    wait_with_http_workers(60)
            finally:
                first_release.set()
                db.current_stream_payload = original_stream_payload
            print("R06_MAIN_ORDERED_POLL_GATE_PASS", flush=True)
            print("R06_ZERO_BROWSER_ALL_PASS", flush=True)
        finally:
            for view in views:
                view.close()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
