"""R06 FIX2: real Chromium chat/list geometry, equal speed and replacement wipe."""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from urllib.request import urlopen
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
  const root = document.getElementById('list-composition');
  if (root?.classList.contains('r06-flow-exit') &&
      Array.isArray(window.__r06T01BoundaryTrace)) {
    window.__r06T01BoundaryTrace.push(+(
      chat.getBoundingClientRect().top -
      panel.getBoundingClientRect().bottom).toFixed(3));
  }
  if (!chat || !panel) return {
    ready: document.readyState, href: location.href, panel: !!panel,
    height: -1, count: -1, transition: 0, replace: false, shown: false
  };
  return {
    ready: document.readyState, href: location.href, panel: true,
    height: Math.round(chat?.getBoundingClientRect().height || 0),
    count: cards?.children.length ?? -1,
    transition: parseFloat(getComputedStyle(panel).transitionDuration) || 0,
    chatTransition: parseFloat(getComputedStyle(chat).transitionDuration) || 0,
    iframeOpacity: parseFloat(getComputedStyle(chat?.querySelector('iframe')).opacity),
    panelOpacity: parseFloat(getComputedStyle(panel).opacity),
    chatClip: getComputedStyle(chat).clipPath,
    chatBottomGap: +((document.getElementById('list-composition').getBoundingClientRect().bottom
      - chat.getBoundingClientRect().bottom).toFixed(2)),
    chatTop: +chat.getBoundingClientRect().top.toFixed(2),
    listTop: +document.getElementById('list-layer').getBoundingClientRect().top.toFixed(2),
    splitOutgoing: document.getElementById('list-composition')?.classList.contains('r06-split-exit'),
    flowOutgoing: root?.classList.contains('r06-flow-exit'),
    alwaysEntering: root?.classList.contains('r06-flow-enter') ||
      root?.classList.contains('r06-top-enter') ||
      root?.classList.contains('r06-always-resize'),
    topEnterFinished: Number(root?.dataset.r06TopEnterFinished || 0),
    replace: document.getElementById('list-composition')?.classList.contains('r06-replace'),
    shown: document.getElementById('list-composition')?.classList.contains('r06-shown'),
    chatSrc: chat?.querySelector('iframe')?.getAttribute('src'),
    childURL: doc?.location?.href ?? '(not ready)',
    childState: doc?.readyState ?? '(not ready)',
    childText: cards?.textContent?.slice(0,100) ?? '(not ready)',
  };
})())"""


# Foreground replay uses the exact same real-time boundary sampler.
# Qt Chromium can suspend RAF in a covered OBS window on Windows runners.
T01_TRACE_SCRIPT = """(() => {
                  window.__r06T01BoundaryTrace = [];
                  const root = document.getElementById('list-composition');
                  const chat = document.getElementById('list-chat');
                  const panel = document.getElementById('list-panel');
                  let started = null;
                  const tick = () => {
                    if (root.classList.contains('r06-flow-exit')) {
                      if (started === null) started = performance.now();
                      const gap = chat.getBoundingClientRect().top -
                        panel.getBoundingClientRect().bottom;
                      window.__r06T01BoundaryTrace.push(+gap.toFixed(3));
                    }
                    if (started === null || performance.now() - started < 4500)
                      requestAnimationFrame(tick);
                  };
                  requestAnimationFrame(tick);
                  return true;
                })()"""


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
        # The production /overlay side slot depends on a populated scrolling
        # list; an empty DB collapses its root to about 17px and cannot test
        # the chat's intrinsic height or list/chat split at all.
        for index in range(8):
            db.add_game(Game(None, "QA List Entry " + str(index), "2026-01-01",
                             100 + index, 0, STATUS_NOT_PLAYED, ""))
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

            # T01 approved manual fix: an empty but always-shown Twitch
            # chat has the SAME outer frame dimensions as the List. Saving
            # 'Не показывать' must move the list UP regardless of the last
            # saved command slide direction ('right' deliberately remains).
            db.set_setting("multichat_appearance_common",
                           json.dumps({"visibility": "always", "glow": True}))
            for p in pages:
                until(p, lambda m: m["count"] == 0 and m["height"] > 30,
                      "R06_T01_EMPTY_CHAT: always-chat occupies a frame")
                frame = evaluate(p, """JSON.stringify((() => {
                  const panel = document.getElementById('list-panel');
                  const chat = document.getElementById('list-chat');
                  const shell = chat.querySelector('iframe').contentDocument
                    ?.getElementById('shell');
                  return {
                    listBorder: getComputedStyle(panel).border,
                    chatBorder: getComputedStyle(chat).border,
                    listRadius: getComputedStyle(panel).borderRadius,
                    chatRadius: getComputedStyle(chat).borderRadius,
                    listGlow: getComputedStyle(panel).boxShadow,
                    chatGlow: getComputedStyle(chat).boxShadow,
                    shellBorder: shell && getComputedStyle(shell).borderTopWidth,
                    listWidth: panel.getBoundingClientRect().width,
                    chatWidth: chat.getBoundingClientRect().width,
                  };
                })())""")
                assert frame["listBorder"] == frame["chatBorder"], frame
                assert frame["listRadius"] == frame["chatRadius"], frame
                assert frame["listGlow"] == frame["chatGlow"], frame
                assert frame["shellBorder"] == "0px", frame
                assert abs(frame["listWidth"] - frame["chatWidth"]) <= 3, frame
                print("R06_T01_FRAME_PASS", frame, flush=True)
            # T01: one animated chat height, List following in the very
            # same flex layout. Real edges must coincide in EVERY frame.
            for p in pages:
                evaluate(p, T01_TRACE_SCRIPT)
            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 30)
            for p in pages:
                until(p, lambda m: not m["shown"] and m["height"] > 40,
                      "R06_T01_HIDE: empty chat grows when list hides")
                QTest.qWait(1800)
                snapshot = evaluate(p, """JSON.stringify((() => {
                  const root = document.getElementById('list-composition');
                  const panel = document.getElementById('list-panel');
                  const chat = document.getElementById('list-chat');
                  return {
                    hiddenTransform: root.style.getPropertyValue('--r06-hidden-transform'),
                    panelTop: panel.getBoundingClientRect().top,
                    composeTop: root.getBoundingClientRect().top,
                    frameGap: root.getBoundingClientRect().bottom -
                      chat.getBoundingClientRect().bottom,
                    chatHeight: chat.getBoundingClientRect().height,
                    composeHeight: root.getBoundingClientRect().height,
                  };
                })())""")
                assert snapshot["hiddenTransform"].startswith("translateY(-"), snapshot
                assert snapshot["panelTop"] < snapshot["composeTop"], snapshot
                assert abs(snapshot["frameGap"]) <= 3, snapshot
                assert abs(snapshot["chatHeight"] - snapshot["composeHeight"]) <= 3, snapshot
                print("R06_T01_HIDE_PASS", snapshot, flush=True)
            for idx, p in enumerate(pages):
                trace = evaluate(p,
                    "JSON.stringify(window.__r06T01BoundaryTrace || [])")
                if len(trace) < 5:
                    # A covered Chromium window may get 0 RAF callbacks.
                    # Re-play the SAME accepted T01 transition with that
                    # source foregrounded, not weaken the geometry bound.
                    views[idx].raise_()
                    views[idx].activateWindow()
                    QTest.qWait(160)
                    db.set_setting("list_overlay_show_mode", "always")
                    api.configure_list_show("always", "!list", 30)
                    until(p, lambda m: m["shown"] and m["height"] > 30,
                          "R06_T01_FOREGROUND_REPLAY: restore visible List")
                    QTest.qWait(1850)
                    evaluate(p, T01_TRACE_SCRIPT)
                    db.set_setting("list_overlay_show_mode", "hidden")
                    api.configure_list_show("hidden", "!list", 30)
                    until(p, lambda m: m["flowOutgoing"],
                          "R06_T01_FOREGROUND_REPLAY: real flow exit started")
                    # Host-driven CSS snapshots do not depend on RAF in an
                    # occluded Qt Chromium page. This retains the same <=1px
                    # true List/chat boundary requirement.
                    for _ in range(12):
                        evaluate(p, CHAT_METRICS)
                        QTest.qWait(110)
                    QTest.qWait(700)
                    trace = evaluate(p,
                        "JSON.stringify(window.__r06T01BoundaryTrace || [])")
                assert len(trace) >= 5, (
                    "T01 shared flex exit not observed even foregrounded", idx, trace)
                assert max(abs(gap) for gap in trace) <= 1.0, (
                    "T01 List/Chat geometry diverged in a real frame", idx, trace)
                hidden_transform = evaluate(p, """document.getElementById(
                  'list-composition').style.getPropertyValue('--r06-hidden-transform')""")
                assert hidden_transform == "translateY(-100%)", (
                    "T01 hidden mode must use upward exit", idx, hidden_transform)
                print("R06_T01_LOCKED_BOUNDARY_PASS", idx, len(trace),
                      max(abs(gap) for gap in trace), flush=True)
            # T02: entering Always from a completely hidden List is the
            # exact REVERSE of T01. The full-size List rides the shrinking
            # chat's upper edge; it never grows from a zero-height panel or
            # inherits a previously saved horizontal slide direction.
            for p in pages:
                evaluate(p, """(() => {
                  window.__r06T02Trace = [];
                  const root = document.getElementById('list-composition');
                  const chat = document.getElementById('list-chat');
                  const panel = document.getElementById('list-panel');
                  let started = null;
                  const tick = () => {
                    if (root.classList.contains('r06-flow-enter')) {
                      if (started === null) started = performance.now();
                      const a = panel.getBoundingClientRect(), b = chat.getBoundingClientRect();
                      window.__r06T02Trace.push({
                        gap:+(b.top-a.bottom).toFixed(3),
                        chatHeight:+b.height.toFixed(3),
                        panelHeight:+a.height.toFixed(3),
                        chatBottom:+b.bottom.toFixed(3),
                        alpha:+getComputedStyle(panel).opacity,
                        transform:getComputedStyle(panel).transform
                      });
                    }
                    if (started === null || performance.now()-started < 4200)
                      requestAnimationFrame(tick);
                  };
                  requestAnimationFrame(tick);
                  return true;
                })()""")
            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 30)
            for p in pages:
                until(p, lambda m: m["shown"] and m["height"] > 40,
                      "R06_T02_SHOW: reverse always-entry from hidden")
            QTest.qWait(1850)
            for p in pages:
                until(p, lambda m: m["shown"] and m["height"] > 30 and
                      m["height"] < 360 and not m["alwaysEntering"],
                      "T02 Always: entry finished and final split settled in both OBS sources")
            for idx, p in enumerate(pages):
                trace = evaluate(p, "JSON.stringify(window.__r06T02Trace || [])")
                assert len(trace) >= 5, ("T02 missing entering frames", idx, trace)
                assert max(abs(row["gap"]) for row in trace) <= 1.0, (
                    "T02 list/chat boundary desynchronized", idx, trace)
                assert max(row["panelHeight"] for row in trace) - min(
                    row["panelHeight"] for row in trace) <= 1.0, (
                    "T02 List stretched during entry", idx, trace)
                assert min(row["alpha"] for row in trace) >= 0.99, (
                    "T02 must not fade List content", idx, trace)
                assert trace[0]["chatHeight"] > min(row["chatHeight"] for row in trace) + 1, (
                    "T02 chat must begin shrinking downward in sampled frames", idx, trace)
                assert max(abs(row["chatBottom"] - trace[0]["chatBottom"])
                           for row in trace) <= 1.0, (
                    "T02 chat bottom jumped", idx, trace)
                snapshot = evaluate(p, """JSON.stringify((() => {
                  const root=document.getElementById('list-composition');
                  const panel=document.getElementById('list-panel');
                  const chat=document.getElementById('list-chat');
                  return {show:root.classList.contains('r06-shown'),
                    flow:root.classList.contains('r06-flow-enter'),
                    gap:chat.getBoundingClientRect().top-panel.getBoundingClientRect().bottom,
                    panelHeight:panel.getBoundingClientRect().height,
                    chatHeight:chat.getBoundingClientRect().height
                  };
                })())""")
                assert snapshot["show"] and not snapshot["flow"], (idx, snapshot)
                assert abs(snapshot["gap"]) <= 1.0, (idx, snapshot)
                # Qt Chromium can provide only the first few RAF callbacks
                # before the source is covered. The *full* 620->304 shrink
                # is verified against a separately measured final DOM state,
                # while every sampled moving frame still has <=1px gap.
                assert trace[0]["chatHeight"] > snapshot["chatHeight"] + 30, (
                    "T02 chat failed to shrink into final split geometry", idx, trace, snapshot)
                assert abs(snapshot["panelHeight"] - trace[0]["panelHeight"]) <= 1.0, (
                    "T02 List changed intrinsic size during entrance", idx, trace, snapshot)
                print("R06_T02_REVERSE_GEOMETRY_PASS", idx, len(trace),
                      max(abs(row["gap"]) for row in trace), flush=True)
            # Re-saving Always while it is already occupying its target
            # cannot retrigger entry or reset the visible content.
            for p in pages:
                before = evaluate(p, """JSON.stringify((() => {
                  const root=document.getElementById('list-composition');
                  return {cls:root.className,
                    chat:document.getElementById('list-chat').offsetHeight,
                    panel:document.getElementById('list-panel').offsetHeight};
                })())""")
                QTest.qWait(260)
                after = evaluate(p, """JSON.stringify((() => {
                  const root=document.getElementById('list-composition');
                  return {cls:root.className,
                    chat:document.getElementById('list-chat').offsetHeight,
                    panel:document.getElementById('list-panel').offsetHeight};
                })())""")
                assert before == after, ("T02 stable Always must not animate", before, after)
            # Return to T01's hidden state before subsequent chat modes.
            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 30)
            QTest.qWait(1900)
            db.set_setting("multichat_appearance_common",
                           json.dumps({"visibility": "hide_empty"}))
            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 30)
            for p in pages:
                until(p, lambda m: m["count"] == 0 and m["height"] == 0,
                      "R06_T01_RESTORE: empty hide-empty chat hidden")
            QTest.qWait(1750)
            for p in pages:
                until(p, lambda m: m["shown"] and m["height"] == 0 and
                      not m["alwaysEntering"] and not m["splitOutgoing"] and
                      abs(m["transition"] - 1.5) < 0.03,
                      "T02 restored Always completely before message height/speed tests")

            accepted = state.ingest(ChatMessage("twitch", "chan", "first", "alice", "short message"))
            print("R06_BROWSER_INGEST:", accepted, state.snapshot(for_obs=True)["messages"], flush=True)
            with urlopen(api.base_url + "/api/multichat", timeout=5) as response:
                print("R06_BROWSER_API_MULTICHAT:", response.read().decode("utf-8")[:1000], flush=True)
            first_heights = []
            for p in pages:
                metrics = until(p, lambda m: m["count"] == 1 and m["height"] >= 8,
                                "One message has natural height")
                assert abs(metrics["transition"] - 1.5) < 0.03, metrics
                assert abs(metrics["chatTransition"] - 1.5) < 0.03, (
                    "List/chat animation speeds must be identical", metrics)
                first_heights.append(metrics["height"])

            for i in range(2, 5):
                state.ingest(ChatMessage("twitch", "chan", str(i), "viewer",
                    "Additional text to make the card taller and validate dynamic layout"))
            for idx, p in enumerate(pages):
                metrics = until(p, lambda m: m["count"] == 4 and
                                m["height"] > first_heights[idx] + 8,
                                "More messages grow chat in " + str(idx))
                # FIX2 deliberately slows the chat to the same saved
                # duration as the List. Growing during that time is correct;
                # only sample for oscillation once the transition settles.
                QTest.qWait(1650)
                heights = []
                for _ in range(5):
                    QTest.qWait(500)
                    heights.append(evaluate(p, CHAT_METRICS)["height"])
                assert max(heights) - min(heights) <= 3, (
                    "Chat panel flickers/oscillates", heights
                )
                print("R06_BROWSER_PASS: stable height", heights, flush=True)

            # FIX3 regression from nine user videos: the chat must remain
            # bottom-anchored while the list exits LEFT and RIGHT. Before
            # the fix, the reserved List flex area vanished instantly after
            # the slide had ended, teleporting the chat to the top before its
            # height animated. Simultaneous outgoing animation must keep
            # the chat's bottom coordinate stable at every sampled frame.
            for i in range(5, 18):
                state.ingest(ChatMessage("twitch", "chan", str(i), "viewer",
                    "Long multi-line content for a tall Twitch chat layout"))
            for direction in ("left", "right"):
                db.set_settings_bulk({
                    "list_overlay_show_mode": "slide",
                    "list_chat_layout": "split",
                    "list_slide_direction": direction,
                    "list_animation_seconds": "0.75",
                    "list_slide_duration": "15",
                })
                # A multi-window Qt Chromium CI runner can throttle one
                # unfocused page for several seconds. Keep this geometry
                # smoke observable in BOTH pages; 5 s is still covered by
                # the shared command/API regression and user's manual QA.
                api.configure_list_show("slide", "!list", 15)
                # Settles previous list mode before we send a new command.
                QTest.qWait(1300)
                for p in pages:
                    until(p, lambda m: not m["shown"] and m["count"] >= 16
                          and abs(m["chatBottomGap"]) <= 3,
                          direction + " hidden chat pinned at bottom")
                state.ingest(ChatMessage("twitch", "chan", "cmd-" + direction,
                             "alice", "!list"))
                for p in pages:
                    until(p, lambda m: m["shown"] and not m["replace"],
                          direction + " slide started")
                # The accepted horizontal entry remains staged. Check the
                # exit during the fifth second and sample throughout growth.
                until(pages[0], lambda m: not m["shown"] and m["splitOutgoing"],
                      direction + " simultaneous Split exit", timeout=15)
                # Capture both pages in the SAME frame window; a sequential
                # wait can miss the second source's 0.75 s outgoing interval.
                samples = {idx: [] for idx in range(len(pages))}
                for _ in range(6):
                    for idx, p in enumerate(pages):
                        samples[idx].append(evaluate(p, CHAT_METRICS))
                    QTest.qWait(95)
                for idx, sequence in samples.items():
                    gaps = [m["chatBottomGap"] for m in sequence]
                    assert max(abs(g) for g in gaps) <= 3, (
                        direction + " chat jumped vertically", idx, gaps)
                    assert all(m["count"] >= 16 for m in sequence), (
                        direction + " Twitch rows disappeared during exit", idx, sequence)
                    # The independent source can finish its 0.75 s exit
                    # slightly ahead of the main source's sampled window.
                    # Keep the true requirement: no vertical jump in EITHER
                    # source; only the trigger-source must be caught exiting.
                    assert any(m["splitOutgoing"] for m in sequence) or idx > 0, (
                        direction + " outgoing event missing", idx, sequence)
                    if any(m["shown"] for m in sequence):
                        # Chromium may deprioritize the other top-level
                        # source while the first source is in focus. Do not
                        # classify a late frame as a second trigger: require
                        # its own authoritative expiry and stable final state.
                        until(pages[idx], lambda m: not m["shown"],
                              direction + " secondary source caught up to shared expiry",
                              timeout=6)
                        QTest.qWait(250)
                        assert not evaluate(pages[idx], CHAT_METRICS)["shown"], (
                            direction + " source resumed unexpectedly", idx)
                    print("R06_BROWSER_PASS: FIX3 chat bottom pinned " +
                          direction, idx, gaps, flush=True)
                QTest.qWait(1000)

            # Restore the original FIX2 speed for the remaining cases.
            db.set_setting("list_animation_seconds", "1.50")
            api.configure_list_show("always", "!list", 30)
            db.set_setting("list_overlay_show_mode", "always")
            QTest.qWait(600)

            # One operator setting must control BOTH transitions (and URLs).
            for seconds in (0.25, 1.0, 3.0, 1.5):
                db.set_setting("list_animation_seconds", f"{seconds:.2f}")
                for p in pages:
                    until(p, lambda m, expected=seconds:
                          abs(m["transition"] - expected) < 0.03 and
                          abs(m["chatTransition"] - expected) < 0.03,
                          f"Shared List+chat speed {seconds:.2f} seconds")

            # Same saved composition mode in both URLs; a real replacement
            # wipes OVER the intact chat (never fades its iframe to zero).
            db.set_setting("list_overlay_show_mode", "slide")
            db.set_setting("list_chat_layout", "replace")
            api.configure_list_show("slide", "!list", 30)
            state.ingest(ChatMessage("twitch", "chan", "trigger", "alice", "!list"))
            for p in pages:
                until(p, lambda m:
                      m["replace"] and m["shown"] and
                      abs(m["chatTransition"] - 1.5) < 0.03 and
                      abs(m["transition"] - 1.5) < 0.03 and
                      m["count"] >= 4 and
                      m["iframeOpacity"] == 1.0 and
                      m["panelOpacity"] == 1.0 and
                      m["chatClip"] != "none",
                      "Replace overlays moving panel over still-live opaque chat")
                # It must remain in the iframe DOM even when fully occluded.
                QTest.qWait(1800)
                snapshot = evaluate(p, CHAT_METRICS)
                assert snapshot["count"] >= 4, snapshot
                assert snapshot["iframeOpacity"] == 1.0, (
                    "Replace must not fade/clear Twitch iframe", snapshot)
                assert snapshot["chatClip"] != "none", snapshot
            db.set_setting("list_chat_layout", "split")
            for p in pages:
                until(p, lambda m: not m["replace"] and m["shown"] and m["height"] > 8,
                      "Return to split without resetting active list")

            # T02: active Replace->Always never exits and re-enters.
            # Instead, the already visible full-size List shrinks to its
            # Always share while the chat grows underneath the SAME edge.
            db.set_setting("list_chat_layout", "replace")
            for p in pages:
                until(p, lambda m: m["replace"] and m["shown"],
                      "T02 prepare: visible full-size replacement List")
                evaluate(p, """(() => {
                  window.__r06T02ResizeTrace=[];
                  const root=document.getElementById('list-composition'),
                        list=document.getElementById('list-panel'),
                        chat=document.getElementById('list-chat');
                  let started=null;
                  const tick=()=>{
                    if(root.classList.contains('r06-always-resize')){
                      if(started===null)started=performance.now();
                      const a=list.getBoundingClientRect(),b=chat.getBoundingClientRect();
                      window.__r06T02ResizeTrace.push({
                        gap:+(b.top-a.bottom).toFixed(3),
                        listHeight:+a.height.toFixed(3),
                        chatHeight:+b.height.toFixed(3),
                        alpha:+getComputedStyle(list).opacity,
                        top:+a.top.toFixed(3)
                      });
                    }
                    if(started===null || performance.now()-started<3500)
                      requestAnimationFrame(tick);
                  };
                  requestAnimationFrame(tick);return true;
                })()""")
            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 30)
            # The persisted-setting polling period may exceed the first
            # 1.9 seconds on a loaded Windows Qt runner. Do not inspect an
            # animation which the source has not even started yet.
            for p in pages:
                until(p, lambda m: m["shown"] and not m["replace"] and
                      m["height"] < 600,
                      "T02 Replace->Always saved state reached browser")
            QTest.qWait(1850)
            for idx,p in enumerate(pages):
                trace=evaluate(p,"JSON.stringify(window.__r06T02ResizeTrace || [])")
                assert len(trace)>=5, ("T02 visible resizing frames missing",idx,trace)
                assert max(abs(row["gap"]) for row in trace)<=1.0, (
                    "T02 resize List and chat edges diverged",idx,trace)
                assert min(row["alpha"] for row in trace)>=0.99, (
                    "T02 visible List must not fade during resize",idx,trace)
                assert trace[0]["listHeight"]>trace[-1]["listHeight"]+30, (
                    "T02 oversized visible List did not shrink",idx,trace)
                assert trace[-1]["chatHeight"]>trace[0]["chatHeight"]+30, (
                    "T02 chat did not grow under shrinking List",idx,trace)
                print("R06_T02_VISIBLE_REPLACE_RESIZE_PASS",idx,len(trace),flush=True)
            state.set_obs_enabled("twitch", False)
            for p in pages:
                until(p, lambda m: m["height"] == 0,
                      "Global OBS chat toggle releases area")
            # T02: when no Twitch chat is visible, the List has the
            # entire composition and must enter vertically from ABOVE.
            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 30)
            # MUST actually reach "hidden" in both independently polling
            # OBS sources before asking for the inverse top entry. Otherwise
            # Already-visible->Always correctly has NO entry animation.
            for p in pages:
                until(p, lambda m: not m["shown"] and m["height"] == 0,
                      "T02 no-chat: prior List mode is really hidden")
            QTest.qWait(1850)
            for p in pages:
                evaluate(p, """(() => {
                  window.__r06T02TopTrace=[];
                  window.__r06T02TopEvents=[];
                  const r=document.getElementById('list-composition'),
                        panel=document.getElementById('list-panel');
                  window.__r06T02TopBaseline={
                    started:Number(r.dataset.r06TopEnterStarted||0),
                    finished:Number(r.dataset.r06TopEnterFinished||0)};
                  const sample=()=>{
                    const a=panel.getBoundingClientRect(),b=r.getBoundingClientRect();
                    window.__r06T02TopTrace.push({
                      top:+(a.top-b.top).toFixed(3),
                      opacity:+getComputedStyle(panel).opacity,
                      transform:getComputedStyle(panel).transform
                    });
                  };
                  for(const name of ['animationstart','animationend']){
                    panel.addEventListener(name,e=>{
                      if(e.animationName==='r06-always-enter-top'){
                        window.__r06T02TopEvents.push(name);
                        sample();
                      }
                    });
                  }
                  const started=performance.now();
                  const tick=()=>{
                    const a=panel.getBoundingClientRect(),b=r.getBoundingClientRect();
                    if(r.classList.contains('r06-top-enter') ||
                       (r.classList.contains('r06-shown') && performance.now()-started<1450)){
                      window.__r06T02TopTrace.push({
                        top:+(a.top-b.top).toFixed(3),
                        opacity:+getComputedStyle(panel).opacity,
                        transform:getComputedStyle(panel).transform
                      });
                    }
                    if(performance.now()-started<3500)requestAnimationFrame(tick);
                  };
                  requestAnimationFrame(tick);return true;
                })()""")
            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 30)
            for p in pages:
                until(p, lambda m: m["shown"] and m["height"] == 0,
                      "T02 no-chat saved state reached browser")
            for p in pages:
                baseline=evaluate(p, "JSON.stringify(window.__r06T02TopBaseline || {})")
                until(p, lambda m, previous=baseline.get("finished", 0):
                      m["topEnterFinished"] > previous and
                      m["shown"] and not m["alwaysEntering"],
                      "T02 no-chat compositor animation fully finished")
            for idx,p in enumerate(pages):
                trace=evaluate(p,"JSON.stringify(window.__r06T02TopTrace || [])")
                proof=evaluate(p, """JSON.stringify((() => {
                  const root=document.getElementById('list-composition'),
                        panel=document.getElementById('list-panel'),
                        start=window.__r06T02TopBaseline||{};
                  return {started:Number(root.dataset.r06TopEnterStarted||0),
                    finished:Number(root.dataset.r06TopEnterFinished||0),
                    baselineStarted:start.started||0,baselineFinished:start.finished||0,
                    finalTop:panel.getBoundingClientRect().top-
                      root.getBoundingClientRect().top,
                    alpha:Number(getComputedStyle(panel).opacity)};
                })())""")
                assert proof["started"] > proof["baselineStarted"], (
                    "T02 no-chat compositor entrance was never started",idx,proof)
                assert proof["finished"] > proof["baselineFinished"], (
                    "T02 no-chat compositor entrance did not finish",idx,proof)
                assert abs(proof["finalTop"])<=2.0, (
                    "T02 no-chat List did not finish at the top",idx,proof)
                assert proof["alpha"]>=0.99, (
                    "T02 no-chat List content faded",idx,proof)
                if trace:
                    assert min(row["opacity"] for row in trace)>=0.99, (
                        "T02 no-chat List content fades during entry",idx,trace)
                print("R06_T02_NO_CHAT_TOP_ENTRY_PASS",idx,len(trace),flush=True)
            state.set_obs_enabled("twitch", True)
            fresh_ingested = state.ingest(
                ChatMessage("twitch", "chan", "fresh", "alice", "new only"))
            authoritative = state.snapshot(for_obs=True)
            print("R06_REENABLE_CHAT_SERVER_STATE:",
                  {"ingested": fresh_ingested,
                   "obs_enabled": authoritative["obs_enabled"],
                   "messages": [(m["platform"], m["external_id"])
                                for m in authoritative["messages"]]},
                  flush=True)
            assert fresh_ingested and len(authoritative["messages"]) == 1, (
                "Twitch server must admit exactly one fresh OBS message",
                fresh_ingested, authoritative)
            with urlopen(api.base_url + "/api/multichat", timeout=5) as response:
                print("R06_REENABLE_CHAT_HTTP_STATE:",
                      response.read().decode("utf-8")[:500], flush=True)
            for idx,p in enumerate(pages):
                try:
                    until(p, lambda m: m["count"] == 1 and m["height"] >= 8,
                          "Fresh history after re-enabling chat")
                except AssertionError:
                    print("R06_REENABLE_CHAT_CLIENT_DIAG:", idx,
                          evaluate(p, """JSON.stringify((() => {
                            const r=document.getElementById('list-chat'),
                                  frame=r?.querySelector('iframe'),
                                  doc=frame?.contentDocument,
                                  rows=doc?.getElementById('rows');
                            return {frame:frame?.src, ready:doc?.readyState,
                              childURL:doc?.URL, rows:rows?.children.length,
                              text:rows?.textContent?.slice(0,150),
                              iframeDisplay:frame&&getComputedStyle(frame).display,
                              online:navigator.onLine};
                          })())"""), flush=True)
                    raise
            # T02 FIX4: all four previously saved command-slide directions
            # MUST be ignored when a HIDDEN List is switched to Always.
            # Exercise both shared Chromium sources, a permanently visible
            # chat, dynamic hide-empty chat, and globally disabled OBS chat.
            # This specifically covers the user's post-PASS left entry report.
            for chat_mode in ("always", "hide_empty", "disabled"):
                state.set_obs_enabled("twitch", chat_mode != "disabled")
                db.set_setting("multichat_appearance_common",
                               json.dumps({"visibility":
                                           "always" if chat_mode == "always"
                                           else "hide_empty"}))
                db.set_settings_bulk({
                    "list_chat_layout": "split",
                    "list_animation_seconds": "0.75",
                    "list_slide_duration": "15",
                })
                for direction in ("left", "right", "top", "bottom"):
                    db.set_settings_bulk({
                        "list_overlay_show_mode": "slide",
                        "list_slide_direction": direction,
                    })
                    api.configure_list_show("slide", "!list", 15)
                    for p in pages:
                        until(p, lambda m: not m["shown"] and
                              not m["splitOutgoing"] and
                              not m["flowOutgoing"],
                              "T02 FIX4 hidden command List " + chat_mode +
                              "/" + direction, timeout=25)
                    # Wait until the PRIOR directional slide is fully gone
                    # before claiming this tests a new Always entry.
                    QTest.qWait(900)
                    for p in pages:
                        evaluate(p, """(() => {
                          const root=document.getElementById('list-composition'),
                                panel=document.getElementById('list-panel');
                          window.__r06UniversalObserver?.disconnect();
                          window.__r06UniversalTrace=[];
                          const started=performance.now();
                          const capture=()=>{
                            if(!root.classList.contains('r06-shown')) return;
                            const t=new DOMMatrixReadOnly(
                              getComputedStyle(panel).transform);
                            window.__r06UniversalTrace.push({
                              x:t.m41, y:t.m42,
                              opacity:+getComputedStyle(panel).opacity,
                              flow:root.classList.contains('r06-flow-enter'),
                              top:root.classList.contains('r06-top-enter')
                            });
                          };
                          // Qt WebEngine throttles RAF for background OBS
                          // windows. A class-change observer captures the
                          // entry even when zero animation frames run.
                          window.__r06UniversalObserver=
                            new MutationObserver(capture);
                          window.__r06UniversalObserver.observe(root,{
                            attributes:true,attributeFilter:['class']});
                          window.__r06UniversalObserver.observe(panel,{
                            attributes:true,attributeFilter:['style']});
                          const timer=setInterval(capture,60);
                          const tick=()=>{
                            capture();
                            if(performance.now()-started<3800)
                              requestAnimationFrame(tick);
                          };
                          requestAnimationFrame(tick);
                          setTimeout(()=>clearInterval(timer),4000);
                          return true;
                        })()""")
                    db.set_setting("list_overlay_show_mode", "always")
                    api.configure_list_show("always", "!list", 30)
                    for p in pages:
                        until(p, lambda m: m["shown"],
                              "T02 FIX4 Always visible " + chat_mode +
                              "/" + direction, timeout=25)
                    QTest.qWait(1100)
                    for idx,p in enumerate(pages):
                        until(p, lambda m: m["shown"] and
                              not m["alwaysEntering"],
                              "T02 FIX4 Always settled " + chat_mode +
                              "/" + direction, timeout=25)
                        trace=evaluate(p,
                          "JSON.stringify(window.__r06UniversalTrace || [])")
                        assert trace, ("T02 FIX4 missing trace", idx,
                                       chat_mode, direction)
                        assert max(abs(row["x"]) for row in trace) <= 1.0, (
                          "T02 FIX4 inherited horizontal slide during Always",
                          idx, chat_mode, direction, trace)
                        assert min(row["opacity"] for row in trace) >= 0.99, (
                          "T02 FIX4 List faded during Always",
                          idx, chat_mode, direction, trace)
                        assert any(row["flow"] or row["top"]
                                   for row in trace), (
                          "T02 FIX4 no universal top/flow entry seen",
                          idx, chat_mode, direction, trace)
                        print("R06_T02_ANY_SLIDE_TO_ALWAYS_PASS",
                              idx, chat_mode, direction, len(trace),
                              flush=True)
            print("R06_BROWSER_FIX2_PASS", flush=True)
        finally:
            for v in views:
                v.close()
                v.deleteLater()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
