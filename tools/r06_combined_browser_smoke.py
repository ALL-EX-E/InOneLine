"""Separate R06 combined OBS URL: accepted split and Twitch-command motions.

Verifies split/replace contracts, both empty/nonempty Always-chat directions,
plus four command entrance directions over chat without iframe/message loss.
"""
from __future__ import annotations

import json
import os
import re
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
    rootHeight:rs.height, rootTop:rs.top, rootLeft:rs.left, rootWidth:rs.width,
    listHeight:ls.height, listTop:ls.top, listBottom:ls.bottom,
    listLeft:ls.left, listRight:ls.right, layerTransform:getComputedStyle(layer).transform,
    listClipPath:getComputedStyle(layer).clipPath,
    chatClipPath:csStyle.clipPath,
    lastEntrance:root.dataset.r06StandaloneLastEntrance || "",
    lastExit:root.dataset.r06StandaloneLastExit || "",
    appliedDirection:root.dataset.r06AppliedListDirection || "",
    appliedComposeMode:root.dataset.r06AppliedComposeMode || "",
    phase:root.dataset.r06StandalonePhase || "idle",
    holdDurationMs:Number(root.dataset.r06StandaloneHoldDurationMs || 0),
    holdAgeMs:performance.now()-Number(root.dataset.r06StandaloneHoldStartMs || 0),
    chatHeight:cs.height, chatTop:cs.top, chatBottom:cs.bottom,
    combinedSync:root.dataset.r06CombinedSync || "idle",
    motionKind:root.dataset.r06StandaloneMotionKind || "idle",
    motionDuration:Number(root.dataset.r06StandaloneLastMotionDurationMs || 0),
    entranceCount:Number(root.dataset.r06StandaloneEntranceCount || 0),
    exitCount:Number(root.dataset.r06StandaloneExitCount || 0),
    iframeCount:document.querySelectorAll("iframe").length,
    childUrl:doc?.location?.href || "",
    messageCount:cards?.children?.length ?? -1,
    messageTexts:[...(cards?.children || [])].map(node=>node.textContent),
    sameChatFrame:!window.__r06QaChatFrame || frame===window.__r06QaChatFrame,
    sameChatDocument:!window.__r06QaChatDoc || doc===window.__r06QaChatDoc,
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


def until(page, expected, label, timeout=35, dynamic_chat=False):
    deadline = time.monotonic() + timeout
    latest = None
    while time.monotonic() < deadline:
        latest = inspect(page)
        if latest and latest.get("ready") and expected(latest):
            assert latest["iframeCount"] == 1, (label, latest)
            if not dynamic_chat:
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
            entering = until(view.page(), lambda a:
                             a["combinedSync"] == "replace-command-enter" and
                             a["motionKind"] == "enter",
                             "command replacement shares List entry clock")
            assert entering["motionDuration"] >= 650, entering
            assert entering["chatClipPath"].startswith("inset("), entering
            shown = until(view.page(), lambda a: a["shown"] and a["replace"] and
                          a["phase"] == "hold" and
                          a["listHeight"] >= a["rootHeight"] - 3,
                          "replacement fills whole area after its entrance")
            assert shown["holdDurationMs"] == 15000, shown
            exiting = until(view.page(), lambda a:
                            a["combinedSync"] == "replace-command-exit" and
                            a["motionKind"] == "exit",
                            "command replacement reverse expiry")
            assert exiting["chatClipPath"].startswith("inset("), exiting
            until(view.page(), lambda a: not a["shown"] and not a["replace"] and
                  a["listHeight"] < 2 and
                  a["motionKind"] == "idle", "command expiry restores chat")

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
            state.clear_chat("twitch", "ch")
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

            # Second approved scenario: reverse the same top List motion.
            # The chat's top edge rises simultaneously, never moving its
            # bottom edge and never overlapping the departing List.
            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 15)
            started = until(
                view.page(),
                lambda a: a["combinedSync"] == "split-exit" and
                          a["motionKind"] == "exit",
                "shared list reverse exit and empty chat expansion started")
            assert started["motionDuration"] == 2000, started
            assert abs(started["chatBottom"] -
                       (started["rootTop"] + started["rootHeight"])) < 2, started
            frames = []
            for _ in range(9):
                frame = inspect(view.page())
                if frame["combinedSync"] == "split-exit":
                    frames.append(frame)
                    assert -2 <= frame["chatTop"] - frame["listBottom"] <= 18, frame
                    assert abs(frame["chatBottom"] -
                               (frame["rootTop"] + frame["rootHeight"])) < 2, frame
                    assert float(frame["panelOpacity"]) >= .99, frame
                QTest.qWait(125)
            assert frames, "No intermediate reverse List/chat frames"
            done = until(
                view.page(),
                lambda a: not a["shown"] and a["combinedSync"] == "idle" and
                          a["motionKind"] == "idle" and
                          a["listHeight"] < 2 and
                          abs(a["chatHeight"] - a["rootHeight"]) < 3 and
                          abs(a["chatTop"] - a["rootTop"]) < 2,
                "reverse exit completed with empty chat owning full area")
            exit_count = done["exitCount"]
            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 15)
            QTest.qWait(1300)
            stable = inspect(view.page())
            assert stable["exitCount"] == exit_count, stable
            assert stable["combinedSync"] == "idle", stable

            # Third approved scenario: a NONEMPTY permanent chat has the
            # same geometry as the already accepted empty-chat entrance.
            # Record the actual iframe and document identities before Save;
            # resizing must not reload either or duplicate rendered cards.
            chat_lines = ["QA Nonempty alpha", "QA Nonempty beta",
                          "QA Nonempty gamma", "QA Nonempty delta"]
            for index, message in enumerate(chat_lines):
                assert state.ingest(ChatMessage(
                    "twitch", "ch", f"nonempty-{index}", "qa_viewer",
                    message,
                )), message
            before = until(
                view.page(),
                lambda a: not a["shown"] and a["messageCount"] == 4 and
                          abs(a["chatHeight"] - a["rootHeight"]) < 3 and
                          all(any(message in row for row in a["messageTexts"])
                              for message in chat_lines),
                "nonempty permanent Twitch chat fully visible before List")
            assert before["childUrl"].endswith(
                "/multichat-overlay?embedded=1"), before
            capture = []
            view.page().runJavaScript(
                """(() => {
                  window.__r06QaChatFrame =
                    document.querySelector("#list-chat iframe");
                  window.__r06QaChatDoc =
                    window.__r06QaChatFrame.contentDocument;
                  return !!window.__r06QaChatDoc;
                })()""", capture.append,
            )
            capture_deadline = time.monotonic() + 8
            while not capture and time.monotonic() < capture_deadline:
                QTest.qWait(25)
            assert capture == [True], capture

            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 15)
            started = until(
                view.page(),
                lambda a: a["combinedSync"] == "split-enter" and
                          a["motionKind"] == "enter",
                "nonempty chat reused synchronized List entrance")
            assert started["motionDuration"] == 2000, started
            assert started["messageCount"] == 4, started
            assert started["sameChatFrame"] and started["sameChatDocument"], started
            frames = []
            for _ in range(9):
                frame = inspect(view.page())
                if frame["combinedSync"] == "split-enter":
                    frames.append(frame)
                    assert frame["messageCount"] == 4, frame
                    assert frame["sameChatFrame"] and frame["sameChatDocument"], frame
                    assert all(any(message in row for row in frame["messageTexts"])
                               for message in chat_lines), frame
                    assert 0 <= frame["chatTop"] - frame["listBottom"] <= 18, frame
                    assert abs(frame["chatBottom"] -
                               (frame["rootTop"] + frame["rootHeight"])) < 2, frame
                    assert float(frame["panelOpacity"]) >= .99, frame
                QTest.qWait(125)
            assert frames, "Missing nonempty split-entry intermediate frames"
            done = until(
                view.page(),
                lambda a: a["shown"] and a["combinedSync"] == "idle" and
                          a["motionKind"] == "idle" and a["messageCount"] == 4 and
                          a["sameChatFrame"] and a["sameChatDocument"] and
                          abs(a["listHeight"] - a["chatHeight"]) < 18 and
                          9 <= a["chatTop"] - a["listBottom"] <= 15,
                "nonempty chat keeps four messages and original iframe at 50/50")
            assert all(any(message in row for row in done["messageTexts"])
                       for message in chat_lines), done
            entrance_count = done["entranceCount"]
            db.set_setting("list_overlay_show_mode", "always")
            api.configure_list_show("always", "!list", 15)
            QTest.qWait(1300)
            stable = inspect(view.page())
            assert stable["entranceCount"] == entrance_count, stable
            assert stable["messageCount"] == 4, stable
            assert stable["sameChatFrame"] and stable["sameChatDocument"], stable
            assert stable["combinedSync"] == "idle", stable
            # Fourth approved scenario: hide the permanently visible List
            # while a NONEMPTY Always chat preserves its rendered messages.
            # Exact reverse of the previously tested entrance, not a new
            # animation or reload of the existing embedded Twitch iframe.
            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 15)
            started = until(
                view.page(),
                lambda a: a["combinedSync"] == "split-exit" and
                          a["motionKind"] == "exit",
                "nonempty chat reused synchronized List reverse exit")
            assert started["motionDuration"] == 2000, started
            assert started["messageCount"] == 4, started
            assert started["sameChatFrame"] and started["sameChatDocument"], started
            assert abs(started["chatBottom"] -
                       (started["rootTop"] + started["rootHeight"])) < 2, started
            frames = []
            for _ in range(9):
                frame = inspect(view.page())
                if frame["combinedSync"] == "split-exit":
                    frames.append(frame)
                    assert frame["messageCount"] == 4, frame
                    assert frame["sameChatFrame"] and frame["sameChatDocument"], frame
                    assert all(any(message in row for row in frame["messageTexts"])
                               for message in chat_lines), frame
                    assert -2 <= frame["chatTop"] - frame["listBottom"] <= 18, frame
                    assert abs(frame["chatBottom"] -
                               (frame["rootTop"] + frame["rootHeight"])) < 2, frame
                    assert float(frame["panelOpacity"]) >= .99, frame
                QTest.qWait(125)
            assert frames, "Missing nonempty split-exit intermediate frames"
            done = until(
                view.page(),
                lambda a: not a["shown"] and a["combinedSync"] == "idle" and
                          a["motionKind"] == "idle" and a["messageCount"] == 4 and
                          a["sameChatFrame"] and a["sameChatDocument"] and
                          a["listHeight"] < 2 and
                          abs(a["chatHeight"] - a["rootHeight"]) < 3 and
                          abs(a["chatTop"] - a["rootTop"]) < 2,
                "nonempty chat keeps four messages and original iframe at 100 percent")
            assert all(any(message in row for row in done["messageTexts"])
                       for message in chat_lines), done
            exit_count = done["exitCount"]
            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 15)
            QTest.qWait(1300)
            stable = inspect(view.page())
            assert stable["exitCount"] == exit_count, stable
            assert stable["messageCount"] == 4, stable
            assert stable["sameChatFrame"] and stable["sameChatDocument"], stable
            assert stable["combinedSync"] == "idle", stable
            assert all(any(message in row for row in stable["messageTexts"])
                       for message in chat_lines), stable
            # Fifth accepted scenario: four command entrances. The next
            # independently approved scenario reuses their precise reverse
            # frames after the complete hold, leaving replacement untouched.
            db.set_settings_bulk({
                "combined_list_chat_layout": "split",
                "list_overlay_show_mode": "slide",
                "list_slide_animation_seconds": "2.00",
                "list_slide_duration": "5",
            })
            api.configure_list_show("slide", "!list", 5)
            until(
                view.page(),
                lambda a: not a["shown"] and a["messageCount"] == 4 and
                          a["listHeight"] < 2 and
                          abs(a["chatHeight"] - a["rootHeight"]) < 3,
                "command split idle with existing four chat messages")
            for direction in ("left", "right", "top", "bottom"):
                db.set_setting("list_slide_direction", direction)
                # /overlay and /combined-overlay apply saved settings via
                # their existing 1-second /api/data poll. Wait for the next
                # full poll before issuing a Twitch command, otherwise this
                # test races a newly saved direction against the old one.
                QTest.qWait(1600)
                baseline = until(
                    view.page(),
                    lambda a: not a["shown"] and a["motionKind"] == "idle" and
                              abs(a["chatHeight"] - a["rootHeight"]) < 3,
                    "command idle before " + direction)
                prior_enter = baseline["entranceCount"]
                prior_exit = baseline["exitCount"]
                assert state.ingest(ChatMessage(
                    "twitch", "ch", "combined-cmd-" + direction, "qa_viewer", "!list"
                )), direction
                with urlopen(api.base_url + "/api/data", timeout=8) as response:
                    accepted = json.load(response)
                assert accepted["list_show"]["remaining_ms"] > 3000, accepted
                started = until(
                    view.page(),
                    lambda a: a["combinedSync"] == "command-enter" and
                              a["motionKind"] == "enter" and
                              a["entranceCount"] > prior_enter and
                              a["lastEntrance"] == direction,
                    "four-direction combined command entrance " + direction)
                assert started["motionDuration"] == 2000, started
                assert abs(started["chatHeight"] - started["rootHeight"]) < 3, started
                assert started["sameChatFrame"] and started["sameChatDocument"], started
                frames = []
                for _ in range(16):
                    frame = inspect(view.page())
                    if frame["combinedSync"] == "command-enter":
                        frames.append(frame)
                        assert abs(frame["chatHeight"] - frame["rootHeight"]) < 3, frame
                        assert abs(frame["chatTop"] - frame["rootTop"]) < 3, frame
                        assert abs(frame["chatBottom"] -
                                   (frame["rootTop"] + frame["rootHeight"])) < 2, frame
                        assert frame["sameChatFrame"] and frame["sameChatDocument"], frame
                        assert all(any(msg in row for row in frame["messageTexts"])
                                   for msg in chat_lines), frame
                        assert float(frame["panelOpacity"]) >= .99, frame
                        assert frame["motionKind"] == "enter", frame
                        assert frame["chatClipPath"] != "none", frame
                        # The masked chat edge must track the ACTUAL moving
                        # List footprint, not just change after it arrives.
                        own_slot = (frame["rootHeight"] - 12) / 2
                        chat_clip = frame["chatClipPath"]
                        if direction == "left":
                            assert frame["listLeft"] <= frame["rootLeft"] + 3, frame
                            match = re.search(r"polygon\(\s*([0-9.]+)% 0%", chat_clip)
                            assert match, frame
                            mask_edge = float(match.group(1)) * frame["rootWidth"] / 100
                            list_edge = frame["listRight"] - frame["rootLeft"]
                            assert abs(mask_edge - list_edge) < 15, frame
                        elif direction == "right":
                            assert frame["listLeft"] >= frame["rootLeft"] - 3, frame
                            match = re.search(
                                r"polygon\(\s*0% 0%,\s*([0-9.]+)% 0%", chat_clip)
                            assert match, frame
                            mask_edge = float(match.group(1)) * frame["rootWidth"] / 100
                            list_edge = frame["listLeft"] - frame["rootLeft"]
                            assert abs(mask_edge - list_edge) < 15, frame
                        elif direction == "top":
                            assert frame["listTop"] <= frame["rootTop"] + 3, frame
                            match = re.search(r"inset\(([0-9.]+)px", chat_clip)
                            assert match, frame
                            mask_edge = float(match.group(1))
                            list_edge = frame["listBottom"] - frame["rootTop"]
                            assert -3 <= mask_edge - list_edge <= 15, frame
                        elif direction == "bottom":
                            # The old test checked only listTop and missed
                            # that the entire translated List extended into
                            # the lower CHAT region. Now its bottom never
                            # extends beyond its own upper slot, at ANY frame.
                            assert frame["listTop"] >= frame["rootTop"] - 3, frame
                            assert frame["listBottom"] <= (
                                frame["rootTop"] + own_slot + 3), frame
                            assert frame["listClipPath"].startswith("inset("), frame
                            mask_match = re.search(
                                r"polygon\(\s*0% 0%,\s*100% 0%,\s*100% ([0-9.]+)px",
                                chat_clip)
                            list_match = re.search(
                                r"inset\(([0-9.]+)px", frame["listClipPath"])
                            assert mask_match and list_match, frame
                            # The dividing mask moves with the visible top of
                            # the upward-revealed List, including the 12px gap.
                            assert abs(float(mask_match.group(1)) -
                                       float(list_match.group(1))) < 4, frame
                    QTest.qWait(125)
                assert len(frames) >= 3, (
                    "Insufficient intermediate combined command frames", direction, frames)
                assert len({a["chatClipPath"] for a in frames}) >= 3, (
                    "Chat cover did not continuously move with List", direction, frames)
                done = until(
                    view.page(),
                    lambda a: a["shown"] and a["combinedSync"] == "idle" and
                              a["motionKind"] == "idle" and a["phase"] == "hold" and
                              a["holdDurationMs"] == 5000 and
                              abs(a["listHeight"] - a["chatHeight"]) < 18 and
                              9 <= a["chatTop"] - a["listBottom"] <= 15,
                    "combined command settled to split after " + direction)
                assert done["holdAgeMs"] < 1000, done
                assert done["sameChatFrame"] and done["sameChatDocument"], done
                assert done["chatClipPath"] == "none", done
                assert done["listClipPath"] == "none", done
                assert 9 <= done["chatTop"] - done["listBottom"] <= 15, done
                assert all(any(msg in row for row in done["messageTexts"])
                           for msg in chat_lines), done
                QTest.qWait(600)
                stable = inspect(view.page())
                assert stable["entranceCount"] == done["entranceCount"], stable
                assert stable["phase"] == "hold", stable
                # The 5s hold begins AFTER the completed 2s entrance.
                # Expiry must start the exact reverse of the accepted motion.
                exiting = until(
                    view.page(),
                    lambda a: a["combinedSync"] == "command-exit" and
                              a["motionKind"] == "exit" and
                              a["phase"] == "exit" and
                              a["exitCount"] == prior_exit + 1 and
                              a["lastExit"] == direction,
                    "reverse command expiry starts " + direction)
                assert exiting["motionDuration"] == 2000, exiting
                assert exiting["sameChatFrame"] and exiting["sameChatDocument"], exiting
                # Twitch commands are ordinary chat messages: the command
                # itself can already be rendered as a fifth (or later) card.
                # Preserve all four original texts and the iframe, without
                # incorrectly interpreting an additional card as data loss.
                assert exiting["messageCount"] >= 4, exiting
                assert all(any(msg in row for row in exiting["messageTexts"])
                           for msg in chat_lines), exiting
                assert abs(exiting["chatHeight"] - exiting["rootHeight"]) < 3, exiting
                exit_frames = []
                for _ in range(16):
                    frame = inspect(view.page())
                    if frame["combinedSync"] == "command-exit":
                        exit_frames.append(frame)
                        assert frame["motionKind"] == "exit", frame
                        assert frame["phase"] == "exit", frame
                        assert frame["exitCount"] == prior_exit + 1, frame
                        assert frame["lastExit"] == direction, frame
                        assert frame["messageCount"] >= 4, frame
                        assert frame["sameChatFrame"] and frame["sameChatDocument"], frame
                        assert all(any(msg in row for row in frame["messageTexts"])
                                   for msg in chat_lines), frame
                        assert float(frame["panelOpacity"]) >= .99, frame
                        assert frame["panelTransform"] == "none", frame
                        assert abs(frame["chatHeight"] - frame["rootHeight"]) < 3, frame
                        assert abs(frame["chatBottom"] -
                                   (frame["rootTop"] + frame["rootHeight"])) < 2, frame
                        assert frame["chatClipPath"] != "none", frame
                        own_slot = (frame["rootHeight"] - 12) / 2
                        chat_clip = frame["chatClipPath"]
                        if direction == "left":
                            match = re.search(r"polygon\(\s*([0-9.]+)% 0%", chat_clip)
                            assert match, frame
                            mask_edge = float(match.group(1)) * frame["rootWidth"] / 100
                            list_edge = frame["listRight"] - frame["rootLeft"]
                            assert abs(mask_edge - list_edge) < 15, frame
                        elif direction == "right":
                            match = re.search(
                                r"polygon\(\s*0% 0%,\s*([0-9.]+)% 0%", chat_clip)
                            assert match, frame
                            mask_edge = float(match.group(1)) * frame["rootWidth"] / 100
                            list_edge = frame["listLeft"] - frame["rootLeft"]
                            assert abs(mask_edge - list_edge) < 15, frame
                        elif direction == "top":
                            match = re.search(r"inset\(([0-9.]+)px", chat_clip)
                            assert match, frame
                            mask_edge = float(match.group(1))
                            list_edge = frame["listBottom"] - frame["rootTop"]
                            assert -3 <= mask_edge - list_edge <= 15, frame
                        else:  # bottom: reverse the reveal in the OWN upper slot.
                            assert frame["listBottom"] <= (
                                frame["rootTop"] + own_slot + 3), frame
                            assert frame["listClipPath"].startswith("inset("), frame
                            mask_match = re.search(
                                r"polygon\(\s*0% 0%,\s*100% 0%,\s*100% ([0-9.]+)px",
                                chat_clip)
                            list_match = re.search(
                                r"inset\(([0-9.]+)px", frame["listClipPath"])
                            assert mask_match and list_match, frame
                            assert abs(float(mask_match.group(1)) -
                                       float(list_match.group(1))) < 4, frame
                    QTest.qWait(125)
                assert len(exit_frames) >= 3, (
                    "Insufficient intermediate reverse expiry frames", direction, exit_frames)
                assert len({a["chatClipPath"] for a in exit_frames}) >= 3, (
                    "Reverse chat mask was not continuous", direction, exit_frames)
                expired = until(
                    view.page(),
                    lambda a: not a["shown"] and a["phase"] == "idle" and
                              a["combinedSync"] == "idle" and
                              a["motionKind"] == "idle" and
                              a["listHeight"] < 2 and
                              abs(a["chatHeight"] - a["rootHeight"]) < 3 and
                              abs(a["chatTop"] - a["rootTop"]) < 2,
                    "reverse command expiry leaves full chat " + direction)
                assert expired["exitCount"] == prior_exit + 1, expired
                assert expired["lastExit"] == direction, expired
                assert expired["chatClipPath"] == "none", expired
                assert expired["listClipPath"] == "none", expired
                assert expired["sameChatFrame"] and expired["sameChatDocument"], expired
                assert all(any(msg in row for row in expired["messageTexts"])
                           for msg in chat_lines), expired
                QTest.qWait(600)
                stable_exit = inspect(view.page())
                assert stable_exit["exitCount"] == expired["exitCount"], stable_exit
                assert stable_exit["phase"] == "idle", stable_exit
            # Zero-second List command: separate /combined-overlay must use
            # the SAME server-owned latch and reverse motion as main /overlay.
            db.set_settings_bulk({
                "list_slide_duration": "0",
                "list_slide_direction": "top",
            })
            api.configure_list_show("slide", "!list", 0)
            QTest.qWait(1600)
            baseline = until(view.page(), lambda a: not a["shown"] and
                             a["motionKind"] == "idle",
                             "combined 0-second command idle")
            assert state.ingest(ChatMessage(
                "twitch", "ch", "combined-zero-on", "qa_viewer", "!list"
            ))
            zero_enter = until(view.page(), lambda a: a["motionKind"] == "enter" and
                               a["lastEntrance"] == "top",
                               "combined 0-second List enters")
            assert zero_enter["sameChatFrame"] and zero_enter["sameChatDocument"], zero_enter
            zero_hold = until(view.page(), lambda a: a["shown"] and
                              a["phase"] == "hold" and a["holdDurationMs"] == 0 and
                              a["combinedSync"] == "idle",
                              "combined 0-second List stays visible")
            assert zero_hold["sameChatFrame"] and zero_hold["sameChatDocument"], zero_hold
            QTest.qWait(1800)
            retained = inspect(view.page())
            assert retained["shown"] and retained["exitCount"] == baseline["exitCount"], retained
            assert state.ingest(ChatMessage(
                "twitch", "ch", "combined-zero-off", "qa_viewer", "!list"
            ))
            zero_exit = until(view.page(), lambda a: a["motionKind"] == "exit" and
                              a["lastExit"] == "top" and
                              a["exitCount"] == baseline["exitCount"] + 1,
                              "combined second 0-second command reverses")
            assert zero_exit["chatClipPath"] != "none", zero_exit
            zero_hidden = until(view.page(), lambda a: not a["shown"] and
                                a["phase"] == "idle" and
                                a["combinedSync"] == "idle" and
                                abs(a["chatHeight"] - a["rootHeight"]) <= 3,
                                "combined zero toggle returns full chat")
            assert zero_hidden["sameChatFrame"] and zero_hidden["sameChatDocument"], zero_hidden
            assert all(any(msg in row for row in zero_hidden["messageTexts"])
                       for msg in chat_lines), zero_hidden
            # Newly approved Replace: preserve the Split List engine,
            # but enter across 100% of the shared area, from all directions.
            # Zero-second toggle also reverses with its original duration.
            db.set_settings_bulk({
                "combined_list_chat_layout": "replace",
                "list_slide_duration": "0",
                "list_slide_animation_seconds": "2.00",
            })
            api.configure_list_show("slide", "!list", 0)
            QTest.qWait(1600)
            for direction in ("left", "right", "top", "bottom"):
                db.set_setting("list_slide_direction", direction)
                QTest.qWait(1600)  # Snapshot poll must read the saved direction.
                prior = until(
                    view.page(), lambda a: not a["shown"] and
                    a["motionKind"] == "idle" and
                    abs(a["chatHeight"] - a["rootHeight"]) < 3,
                    "replace zero idle before " + direction)
                assert state.ingest(ChatMessage(
                    "twitch", "ch", "replace-on-" + direction, "qa_viewer", "!list"
                )), direction
                entering = until(view.page(), lambda a:
                    a["combinedSync"] == "replace-command-enter" and
                    a["motionKind"] == "enter" and
                    a["entranceCount"] == prior["entranceCount"] + 1 and
                    a["lastEntrance"] == direction,
                    "replace full-size motion enters " + direction)
                assert entering["motionDuration"] == 2000, entering
                samples = []
                for _ in range(9):
                    frame = inspect(view.page())
                    if frame["combinedSync"] == "replace-command-enter":
                        samples.append(frame)
                        assert abs(frame["listHeight"] - frame["rootHeight"]) < 3, frame
                        assert abs(frame["chatHeight"] - frame["rootHeight"]) < 3, frame
                        assert frame["sameChatFrame"] and frame["sameChatDocument"], frame
                        assert float(frame["panelOpacity"]) >= .99, frame
                        assert frame["panelTransform"] == "none", frame
                        assert frame["chatClipPath"].startswith("inset("), frame
                        clip = re.search(
                            r"inset\(([-0-9.]+)px ([-0-9.]+)px ([-0-9.]+)px ([-0-9.]+)px\)",
                            frame["chatClipPath"])
                        assert clip, frame
                        top, right, bottom, left = map(float, clip.groups())
                        if direction == "left":
                            edge = frame["listRight"] - frame["rootLeft"]
                            assert abs(left - edge) <= 16, frame
                        elif direction == "right":
                            edge = frame["rootWidth"] - (frame["listLeft"] - frame["rootLeft"])
                            assert abs(right - edge) <= 16, frame
                        elif direction == "top":
                            edge = frame["listBottom"] - frame["rootTop"]
                            assert abs(top - edge) <= 16, frame
                        else:
                            edge = frame["rootHeight"] - (frame["listTop"] - frame["rootTop"])
                            assert abs(bottom - edge) <= 16, frame
                        assert frame["messageCount"] >= 4, frame
                        assert all(any(msg in row for row in frame["messageTexts"])
                                   for msg in chat_lines), frame
                    QTest.qWait(125)
                assert len(samples) >= 3, (direction, samples)
                assert len({a["chatClipPath"] for a in samples}) >= 3, samples
                full = until(view.page(), lambda a:
                             a["shown"] and a["replace"] and
                             a["phase"] == "hold" and a["holdDurationMs"] == 0 and
                             a["combinedSync"] == "idle" and
                             abs(a["listHeight"] - a["rootHeight"]) < 3,
                             "replace zero toggle holds full area " + direction)
                assert full["sameChatFrame"] and full["sameChatDocument"], full
                QTest.qWait(700)
                retained = inspect(view.page())
                assert retained["shown"] and retained["replace"], retained
                assert retained["exitCount"] == prior["exitCount"], retained
                assert state.ingest(ChatMessage(
                    "twitch", "ch", "replace-off-" + direction, "qa_viewer", "!list"
                )), direction
                exiting = until(view.page(), lambda a:
                            a["combinedSync"] == "replace-command-exit" and
                            a["motionKind"] == "exit" and
                            a["lastExit"] == direction and
                            a["exitCount"] == prior["exitCount"] + 1,
                            "replace zero reverse exits " + direction)
                assert exiting["motionDuration"] == 2000, exiting
                exit_samples = []
                for _ in range(9):
                    frame = inspect(view.page())
                    if frame["combinedSync"] == "replace-command-exit":
                        exit_samples.append(frame)
                        assert abs(frame["listHeight"] - frame["rootHeight"]) < 3, frame
                        assert frame["chatClipPath"].startswith("inset("), frame
                        assert frame["sameChatFrame"] and frame["sameChatDocument"], frame
                        assert all(any(msg in row for row in frame["messageTexts"])
                                   for msg in chat_lines), frame
                    QTest.qWait(125)
                assert len(exit_samples) >= 3, (direction, exit_samples)
                hidden = until(view.page(), lambda a:
                               not a["shown"] and not a["replace"] and
                               a["motionKind"] == "idle" and
                               abs(a["chatHeight"] - a["rootHeight"]) < 3,
                               "replace zero toggle restores chat " + direction)
                assert hidden["sameChatFrame"] and hidden["sameChatDocument"], hidden
                assert all(any(msg in row for row in hidden["messageTexts"])
                           for msg in chat_lines), hidden
            # Regression: hide-empty Twitch chat has no reserved frame until
            # messages arrive. Its lower edge stays fixed and grows upward.
            db.set_settings_bulk({
                "multichat_appearance_common": json.dumps({"visibility": "hide_empty"}),
                "list_overlay_show_mode": "slide",
                "combined_list_chat_layout": "split",
                "list_slide_duration": "0",
                "list_slide_animation_seconds": "1.00",
                "list_animation_seconds": "0.60",
            })
            api.configure_list_show("slide", "!list", 0)
            state.clear_chat("twitch", "ch")
            empty = until(view.page(), lambda a:
                          not a["shown"] and a["chatHeight"] <= 2 and
                          a["motionKind"] == "idle",
                          "hide-empty combined starts with no chat",
                          dynamic_chat=True)
            assert state.ingest(ChatMessage(
                "twitch", "ch", "hide-empty-first", "qa_viewer",
                "R06 dynamic first message"))
            first = until(view.page(), lambda a:
                          not a["shown"] and a["messageCount"] == 1 and
                          10 < a["chatHeight"] < a["rootHeight"] / 2,
                          "one message occupies compact bottom chat",
                          dynamic_chat=True)
            assert first["chatTransition"].startswith("0.6s"), first
            assert abs(first["chatBottom"] -
                       (first["rootTop"] + first["rootHeight"])) <= 3, first

            # Share the exact same List WAAPI in Split; no 50/50 reservation
            # while the chat contains only a few short messages.
            for direction in ("left", "right", "top", "bottom"):
                db.set_setting("list_slide_direction", direction)
 
                until(view.page(), lambda a:
                      a["appliedDirection"] == direction and
                      a["appliedComposeMode"] == "split",
                      "Chromium applied hide-empty split "+direction,
                      dynamic_chat=True)

                assert state.ingest(ChatMessage(
                    "twitch", "ch", "hide-empty-on-" + direction,
                    "qa_viewer", "!list")), direction
                entered = until(view.page(), lambda a:
                    a["combinedSync"] == "command-enter" and
                    a["motionKind"] == "enter" and
                    a["lastEntrance"] == direction,
                    "hide-empty Split enters " + direction, dynamic_chat=True)
                assert entered["motionDuration"] == 1000, entered
                held = until(view.page(), lambda a:
                    a["phase"] == "hold" and a["shown"] and
                    a["combinedSync"] == "idle" and
                    a["chatHeight"] <= a["rootHeight"] / 2 + 4 and
                    a["listHeight"] >= (a["rootHeight"]-12) / 2 - 4,
                    "hide-empty Split List fills free area " + direction,
                    dynamic_chat=True)
                assert held["sameChatFrame"] and held["sameChatDocument"], held
                assert abs(held["listBottom"] + 12 - held["chatTop"]) <= 18, held
                if direction == "left":
                    for n in range(8):
                        assert state.ingest(ChatMessage(
                            "twitch", "ch", "hide-empty-grow-" + str(n),
                            "qa_viewer", "Dynamic message %d preserved" % n))
                    growing = until(view.page(), lambda a:
                        a["phase"] == "hold" and a["chatHeight"] > first["chatHeight"] + 50
                        and a["chatHeight"] <= (a["rootHeight"] - 12) / 2 + 4,
                        "new messages expand chat upward under List",
                        dynamic_chat=True)
                    assert growing["sameChatFrame"] and growing["sameChatDocument"], growing
                assert state.ingest(ChatMessage(
                    "twitch", "ch", "hide-empty-off-" + direction,
                    "qa_viewer", "!list")), direction
                left = until(view.page(), lambda a:
                    a["combinedSync"] == "command-exit" and
                    a["motionKind"] == "exit" and a["lastExit"] == direction,
                    "hide-empty Split reverses " + direction, dynamic_chat=True)
                assert left["motionDuration"] == 1000, left
                exposed = until(view.page(), lambda a:
                    not a["shown"] and a["motionKind"] == "idle" and
                    a["chatHeight"] > 10 and a["chatHeight"] <= a["rootHeight"] + 3,
                    "hide-empty chat returns to content height " + direction,
                    dynamic_chat=True)
                assert exposed["sameChatFrame"] and exposed["sameChatDocument"], exposed
                assert exposed["messageCount"] >= 1, exposed

            # Replace uses exactly the same command timings but the List covers
            # the entire parent. The clipped Twitch iframe stays alive.
            db.set_setting("combined_list_chat_layout", "replace")
            QTest.qWait(1300)
            for direction in ("left", "right", "top", "bottom"):
                db.set_setting("list_slide_direction", direction)
 
                until(view.page(), lambda a:
                      a["appliedDirection"] == direction and
                      a["appliedComposeMode"] == "replace",
                      "Chromium applied hide-empty replace "+direction,
                      dynamic_chat=True)

                assert state.ingest(ChatMessage(
                    "twitch", "ch", "hide-empty-replace-on-" + direction,
                    "qa_viewer", "!list")), direction
                entered = until(view.page(), lambda a:
                    a["combinedSync"] == "replace-command-enter" and
                    a["motionKind"] == "enter" and
                    a["lastEntrance"] == direction,
                    "hide-empty Replace enters " + direction,
                    dynamic_chat=True)
                assert entered["chatClipPath"].startswith("inset("), entered
                held = until(view.page(), lambda a:
                    a["shown"] and a["replace"] and a["phase"] == "hold" and
                    a["listHeight"] >= a["rootHeight"] - 3,
                    "hide-empty Replace fully covers " + direction,
                    dynamic_chat=True)
                assert held["sameChatFrame"] and held["sameChatDocument"], held
                assert state.ingest(ChatMessage(
                    "twitch", "ch", "hide-empty-replace-off-" + direction,
                    "qa_viewer", "!list")), direction
                left = until(view.page(), lambda a:
                    a["combinedSync"] == "replace-command-exit" and
                    a["motionKind"] == "exit",
                    "hide-empty Replace reverses " + direction,
                    dynamic_chat=True)
                exposed = until(view.page(), lambda a:
                    not a["shown"] and not a["replace"] and
                    a["motionKind"] == "idle" and a["chatHeight"] > 10,
                    "hide-empty Replace returns chat " + direction,
                    dynamic_chat=True)
                assert exposed["sameChatFrame"] and exposed["sameChatDocument"], exposed
                assert exposed["messageCount"] >= held["messageCount"], exposed

            # Positive hold is independent of 1-second motion; a repeat extends
            # the full hold instead of hiding as in zero-second toggle.
            db.set_settings_bulk({
                "combined_list_chat_layout": "split",
                "list_slide_duration": "5",
                "list_slide_direction": "top",
            })
            api.configure_list_show("slide", "!list", 5)
            QTest.qWait(2200)  # Saved Split layout and duration must reach Chromium
            assert state.ingest(ChatMessage(
                "twitch", "ch", "hide-empty-timed-on",
                "qa_viewer", "!list"))
            timed = until(view.page(), lambda a:
                a["shown"] and a["phase"] == "hold" and
                a["holdDurationMs"] == 5000 and a["motionKind"] == "idle",
                "hide-empty positive hold begins AFTER entrance",
                dynamic_chat=True)
            assert timed["holdAgeMs"] < 1200, timed
            QTest.qWait(1500)
            assert state.ingest(ChatMessage(
                "twitch", "ch", "hide-empty-timed-extend",
                "qa_viewer", "!list"))
            extended = until(view.page(), lambda a:
                a["shown"] and a["phase"] == "hold" and
                a["holdAgeMs"] < 1300 and a["exitCount"] == timed["exitCount"],
                "hide-empty positive repeat extends rather than toggles",
                dynamic_chat=True)
            expired = until(view.page(), lambda a:
                not a["shown"] and a["phase"] == "idle" and
                a["lastExit"] == "top" and a["motionKind"] == "idle",
                "hide-empty positive hold ends with reverse exit",
                timeout=13, dynamic_chat=True)
            assert expired["sameChatFrame"] and expired["sameChatDocument"], expired
            print("R06_COMBINED_HIDE_EMPTY_SPLIT_REPLACE_PASS", flush=True)

            print("R06_REPLACE_ALL_DIRECTIONS_AND_ZERO_PASS", flush=True)
            print("R06_COMBINED_BROWSER_ALL_PASS", flush=True)
        finally:
            view.close()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
