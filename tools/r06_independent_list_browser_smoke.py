"""Standalone List: approved child-only motion; no Twitch iframe or chat layout.

The main and dedicated combined composition retain their previous regressions.
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


JS = """JSON.stringify((() => {
  const root=document.getElementById("list-composition"),
        layer=document.getElementById("list-layer"),
        panel=document.getElementById("list-panel"),
        chat=document.getElementById("list-chat");
  if (!root || !layer || !panel || !chat) return {ready:false};
  const css=getComputedStyle(panel);
  return {
    ready: true,
    shown:root.classList.contains("r06-shown"),
    motion:root.classList.contains("r06-standalone-motion"),
    motionKind:root.dataset.r06StandaloneMotionKind || "idle",
    motionDurationMs:Number(root.dataset.r06StandaloneLastMotionDurationMs || 0),
    phase:root.dataset.r06StandalonePhase || "idle",
    holdDurationMs:Number(root.dataset.r06StandaloneHoldDurationMs || 0),
    holdAgeMs:Math.max(0,performance.now() -
      Number(root.dataset.r06StandaloneHoldStartMs || performance.now())),
    lastExit:root.dataset.r06StandaloneLastExit || "",
    layerTransform:getComputedStyle(layer).transform,
    entranceCount:Number(root.dataset.r06StandaloneEntranceCount || 0),
    exitCount:Number(root.dataset.r06StandaloneExitCount || 0),
    lastEntrance:root.dataset.r06StandaloneLastEntrance || "",
    configuredDirection:document.documentElement.dataset.obsSlideDirection || "",
    replace:root.classList.contains("r06-replace"),
    listHeight:layer.getBoundingClientRect().height,
    chatHeight:chat.getBoundingClientRect().height,
    iframes:document.querySelectorAll("iframe").length,
    opacity:css.opacity,
    transform:css.transform,
    transition:css.transitionDuration,
    animation:css.animationName,
    hasTopThree:document.querySelectorAll(".top-three-row").length > 0,
    scrollTransform:document.getElementById("game-list")?.style.transform || "",
    scrollingRowCount:document.querySelectorAll("#game-list .game-row").length,
    policy: document.documentElement.dataset.obsShowMode || ""
  };
})())"""


class Clock:
    """Deterministic Twitch command time; no dependence on Windows CI load."""
    def __init__(self):
        self.t = 200.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


def port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def metrics(page):
    replies = []
    page.runJavaScript(JS, replies.append)
    timeout = time.monotonic() + 8
    while not replies and time.monotonic() < timeout:
        QTest.qWait(25)
    if not replies:
        raise AssertionError("Standalone List Chromium callback timed out")
    value = replies[0]
    return json.loads(value) if isinstance(value, str) else value


def until(page, condition, label, *, settled=True):
    timeout = time.monotonic() + 35
    last = None
    while time.monotonic() < timeout:
        last = metrics(page)
        if (last and last.get("ready") and condition(last) and
                (not settled or not last["motion"])):
            assert last["iframes"] == 0, (label, last)
            assert last["replace"] is False, (label, last)
            assert last["chatHeight"] <= 2, (label, last)
            assert float(last["opacity"]) >= .99, (label, last)
            assert last["transform"] == "none", (label, last)
            assert all(float(x.rstrip("s")) == 0
                       for x in last["transition"].split(", ")), (label, last)
            assert last["animation"] == "none", (label, last)
            print("R06_INDEPENDENT_LIST_PASS", label, last, flush=True)
            return
        QTest.qWait(100)
    raise AssertionError(f"{label} timed out: {last!r}")


def observe_motion(page, label, *, entering, previous_count, direction="top"):
    """See a real WebEngine animation frame, not merely its final geometry."""
    timeout = time.monotonic() + 12
    last = None
    while time.monotonic() < timeout:
        last = metrics(page)
        if not last or not last.get("ready"):
            QTest.qWait(30)
            continue
        count = last["entranceCount"] if entering else last["exitCount"]
        if (last["motion"] and count > previous_count and
                last["layerTransform"] != "none" and
                last["motionKind"] == ("enter" if entering else "exit") and
                (last["lastEntrance"] if entering else last["lastExit"]) == direction):
            assert last["iframes"] == 0 and last["chatHeight"] <= 2, (label, last)
            assert float(last["opacity"]) >= .99, (label, last)
            print("R06_INDEPENDENT_LIST_MOTION_PASS", label, last, flush=True)
            return last
        QTest.qWait(30)
    raise AssertionError(f"{label}: no Chromium motion frame: {last!r}")


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "list_only.db")
        db.add_game(Game(None, "QA standalone list", "2026-01-01",
                         10, 0, STATUS_NOT_PLAYED, ""))
        for row in range(14):
            db.add_game(Game(None, f"QA scrolling row {row:02d}", "2026-01-01",
                             9 - row, 0, STATUS_NOT_PLAYED, ""))
        db.set_settings_bulk({
            "list_overlay_show_mode": "always",
            "list_slide_duration": "5",
            "list_slide_animation_seconds": "0.65",
            "list_slide_command": "!list",
            # Retained legacy settings must not affect the standalone List.
            "list_animation_seconds": "2.75",
            "list_chat_layout": "replace",
            "list_with_chat": "1",
        })
        old = db.get_settings(["list_animation_seconds",
                               "list_chat_layout", "list_with_chat"])
        clock = Clock()
        state = MultichatState(clock=clock, wall_clock=clock)
        api = LocalApiServer(db, port=port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.configure_list_show("always", "!list", 15)
        api.start()
        view = QWebEngineView()
        try:
            view.resize(390, 630)
            view.show()
            view.load(QUrl(api.base_url + "/list-overlay"))
            until(view.page(), lambda v: v["shown"] and
                  v["listHeight"] > 100 and v["hasTopThree"], "always")
            initial = metrics(view.page())
            assert not initial["motion"] and initial["entranceCount"] == 0, initial
            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 15)
            with urlopen(api.base_url + "/api/data", timeout=8) as response:
                state_payload = json.load(response)
            assert state_payload["visibility"]["list"]["show_mode"] == "hidden", (
                "Backend did not apply saved hidden mode", state_payload["visibility"]["list"]
            )
            observe_motion(view.page(), "save Hidden exits upward",
                           entering=False, previous_count=0)
            until(view.page(), lambda v: not v["shown"] and
                  v["listHeight"] <= 2, "hidden after animation")
            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 15)
            observe_motion(view.page(), "save Always enters from top",
                           entering=True, previous_count=0, direction="top")
            until(view.page(), lambda v: v["shown"] and
                  v["listHeight"] > 100, "always restored")
            stable = metrics(view.page())
            api.configure_list_show("always", "!list", 15)
            QTest.qWait(1300)
            assert not metrics(view.page())["motion"], "Repeated Always Save animated"
            assert metrics(view.page())["entranceCount"] == stable["entranceCount"], (
                "Repeated Always Save replayed entrance", stable, metrics(view.page())
            )
            db.set_setting("list_overlay_show_mode", "slide")
            api.configure_list_show("slide", "!list", 15)
            until(view.page(), lambda v: not v["shown"] and
                  v["listHeight"] <= 2, "command idle")
            for direction in ("left", "right", "top", "bottom"):
                # Two distinct durations verify that the new control actually
                # changes Chromium animation timing (not the full-show hold).
                animation_s = 1.50 if direction in ("top", "bottom") else 0.65
                db.set_settings_bulk({
                    "list_slide_direction": direction,
                    "list_slide_animation_seconds": f"{animation_s:.2f}",
                    "list_slide_duration": "5",
                })
                api.configure_list_show("slide", "!list", 5)
                until(view.page(), lambda v: (
                    v["configuredDirection"] == direction and not v["shown"]
                ), "new direction applied "+direction)
                before = metrics(view.page())
                assert not before["shown"] and not before["motion"], before
                assert state.ingest(ChatMessage(
                    "twitch", "ch", "standalone-"+direction, "viewer", "!list"
                ))
                with urlopen(api.base_url + "/api/data", timeout=8) as response:
                    command_payload = json.load(response)
                assert command_payload["list_show"]["remaining_ms"] > 0, (
                    "Standalone command timer did not start",
                    direction, command_payload["list_show"],
                )
                entrant = observe_motion(
                    view.page(), "command "+direction, entering=True,
                    previous_count=before["entranceCount"], direction=direction,
                )
                expected_ms = round(animation_s * 1000)
                assert entrant["motionDurationMs"] == expected_ms, (
                    "Saved animation duration not used by Chromium",
                    direction, entrant,
                )
                # The full 5 seconds begin only after the transition is done.
                until(view.page(), lambda v: (
                    v["shown"] and v["phase"] == "hold" and
                    v["listHeight"] > 100 and v["holdDurationMs"] == 5000
                ), "full visible hold starts AFTER entrance "+direction)
                held = metrics(view.page())
                assert held["entranceCount"] == before["entranceCount"] + 1, (
                    "One Twitch command produced duplicate entrances",
                    direction, before, held,
                )
                # This simulates the old server-side timer reaching zero
                # before the 5-second *post-entrance* display has finished.
                # The independent source must not disappear at that moment.
                clock.advance(91)
                if direction == "right":
                    # A settings change during the hold must not change the
                    # reversing speed of this already-started command cycle.
                    db.set_setting("list_slide_animation_seconds", "3.00")
                    QTest.qWait(1150)
                with urlopen(api.base_url + "/api/data", timeout=8) as response:
                    expired_server = json.load(response)
                assert expired_server["list_show"]["remaining_ms"] == 0, (
                    "Manual server time advance failed", direction, expired_server,
                )
                QTest.qWait(1000)
                still_held = metrics(view.page())
                assert still_held["shown"] and still_held["phase"] == "hold", (
                    "Server expiry ended the List hold before local five seconds",
                    direction, still_held,
                )
                reverse = observe_motion(
                    view.page(), "reverse exit "+direction, entering=False,
                    previous_count=before["exitCount"], direction=direction,
                )
                assert reverse["motionDurationMs"] == expected_ms, (
                    "Reverse exit duration differs from entrance",
                    direction, reverse,
                )
                until(view.page(), lambda v: (
                    not v["shown"] and v["phase"] == "idle" and
                    v["listHeight"] <= 2
                ), "reverse exit finished "+direction)
                after = metrics(view.page())
                assert after["entranceCount"] == before["entranceCount"] + 1, (
                    "Expired command replayed entrance", direction, after,
                )
                assert after["exitCount"] == before["exitCount"] + 1, (
                    "One command must produce exactly one reverse exit",
                    direction, after,
                )
                assert after["lastExit"] == direction, (
                    "Exit did not use the reverse of the entrance direction",
                    direction, after,
                )
            # A 0-second command is a persistent server-owned toggle.
            db.set_settings_bulk({
                "list_slide_duration": "0",
                "list_slide_direction": "left",
                "list_slide_animation_seconds": "0.65",
            })
            api.configure_list_show("slide", "!list", 0)
            until(view.page(), lambda v: (v["configuredDirection"] == "left" and
                  not v["shown"]), "0-second toggle idle")
            QTest.qWait(1550)  # Virtual scroll clock advances behind the scene.
            before_zero = metrics(view.page())
            self_old_exit = before_zero["exitCount"]
            assert state.ingest(ChatMessage(
                "twitch", "ch", "zero-open", "viewer", "!list"
            ))
            observe_motion(view.page(), "0-second command enters", entering=True,
                           previous_count=before_zero["entranceCount"], direction="left")
            until(view.page(), lambda v: (v["shown"] and v["phase"] == "hold" and
                  v["holdDurationMs"] == 0 and v["scrollingRowCount"] > 10),
                  "zero held after entrance")
            zero_active = metrics(view.page())
            assert zero_active["scrollTransform"] not in ("", "translateY(0px)"), (
                "Hidden List restarted its scrolling position", zero_active
            )
            QTest.qWait(1900)
            still_zero = metrics(view.page())
            assert still_zero["shown"] and still_zero["exitCount"] == self_old_exit, (
                "0-second List expired without a repeated command", still_zero
            )
            assert not state.ingest(ChatMessage(
                "twitch", "ch", "zero-open", "viewer", "!list"
            )), "Duplicate Twitch event must not toggle the List"
            assert state.ingest(ChatMessage(
                "twitch", "ch", "zero-close", "viewer", "!list"
            ))
            observe_motion(view.page(), "0-second command exits", entering=False,
                           previous_count=still_zero["exitCount"], direction="left")
            until(view.page(), lambda v: (not v["shown"] and
                  v["phase"] == "idle" and v["listHeight"] <= 2),
                  "zero held off after second command")
            QTest.qWait(1400)
            assert not metrics(view.page())["shown"], "Toggle replayed old command"
            assert state.ingest(ChatMessage(
                "twitch", "ch", "zero-third", "viewer", "!list"
            ))
            until(view.page(), lambda v: (v["shown"] and v["phase"] == "hold" and
                  v["holdDurationMs"] == 0), "third command restores held List")
            assert db.get_settings(old.keys()) == old, "Legacy values modified"
            print("R06_INDEPENDENT_LIST_BROWSER_ALL_PASS", flush=True)
        finally:
            view.close()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
