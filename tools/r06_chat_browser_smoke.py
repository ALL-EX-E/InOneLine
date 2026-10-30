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
    replace: document.getElementById('list-composition')?.classList.contains('r06-replace'),
    shown: document.getElementById('list-composition')?.classList.contains('r06-shown'),
    chatSrc: chat?.querySelector('iframe')?.getAttribute('src'),
    childURL: doc?.location?.href ?? '(not ready)',
    childState: doc?.readyState ?? '(not ready)',
    childText: cards?.textContent?.slice(0,100) ?? '(not ready)',
  };
})())"""


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
            # T01: same CSS duration is NOT enough. Sample the actual
            # moving boundaries frame-by-frame; chat top must track the
            # outgoing List bottom all the way to the top of the viewport.
            evaluate(pages[0], """(() => {
              window.__r06T01BoundaryTrace = [];
              const root = document.getElementById('list-composition');
              const chat = document.getElementById('list-chat');
              const panel = document.getElementById('list-panel');
              const started = performance.now();
              const tick = () => {
                if (root.classList.contains('r06-split-exit')) {
                  const gap = chat.getBoundingClientRect().top -
                    panel.getBoundingClientRect().bottom;
                  window.__r06T01BoundaryTrace.push(+gap.toFixed(3));
                }
                if (performance.now() - started < 4500) requestAnimationFrame(tick);
              };
              requestAnimationFrame(tick);
              return true;
            })()""")
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
            trace = evaluate(pages[0],
                             "JSON.stringify(window.__r06T01BoundaryTrace || [])")
            assert len(trace) >= 3, ("T01 outgoing boundary trace missing", trace)
            assert max(abs(gap) for gap in trace) <= 4.0, (
                "T01 list lower edge outpaces chat upper edge", trace)
            assert evaluate(pages[0], """document.getElementById(
              'list-composition').style.getPropertyValue('--r06-hidden-transform')""") \\
                == "translateY(-100%)", "T01 hide must travel exactly one List height"
            print("R06_T01_EQUAL_BOUNDARY_PASS", len(trace),
                  max(abs(gap) for gap in trace), flush=True)
            db.set_setting("multichat_appearance_common",
                           json.dumps({"visibility": "hide_empty"}))
            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 30)
            for p in pages:
                until(p, lambda m: m["count"] == 0 and m["height"] == 0,
                      "R06_T01_RESTORE: empty hide-empty chat hidden")
            QTest.qWait(1750)

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

            state.set_obs_enabled("twitch", False)
            for p in pages:
                until(p, lambda m: m["height"] == 0,
                      "Global OBS chat toggle releases area")
            state.set_obs_enabled("twitch", True)
            state.ingest(ChatMessage("twitch", "chan", "fresh", "alice", "new only"))
            for p in pages:
                until(p, lambda m: m["count"] == 1 and m["height"] >= 8,
                      "Fresh history after re-enabling chat")
            print("R06_BROWSER_FIX2_PASS", flush=True)
        finally:
            for v in views:
                v.close()
                v.deleteLater()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
