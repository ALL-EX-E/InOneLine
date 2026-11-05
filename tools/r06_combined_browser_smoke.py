"""Separate R06 combined OBS URL, real native Chromium, static transitions.

Does not re-run the long legacy main-overlap browser test in parallel. Verifies
new URL live DOM and the accepted split/replace/show/hide contracts.
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
    rootHeight:rs.height, listHeight:ls.height, chatHeight:cs.height,
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
            "list_slide_duration": "3",
            "list_chat_layout": "replace",  # legacy must not control new source
            "combined_list_chat_layout": "split",
            "multichat_appearance_common": json.dumps({"visibility": "always"}),
        })
        state = MultichatState()
        api = LocalApiServer(db, port=free_port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.configure_list_show("always", "!list", 3)
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
            api.configure_list_show("slide", "!list", 3)
            until(view.page(), lambda a: not a["shown"] and
                  a["listHeight"] < 2 and
                  abs(a["chatHeight"]-a["rootHeight"]) < 3,
                  "slide idle chat owns full area")

            assert state.ingest(ChatMessage(
                "twitch", "ch", "combined-command", "qa_user", "!list",
            ))
            until(view.page(), lambda a: a["shown"] and a["replace"] and
                  a["listHeight"] >= a["rootHeight"] - 3,
                  "command replacement, instant without opacity animation")
            until(view.page(), lambda a: not a["shown"] and not a["replace"] and
                  a["listHeight"] < 2, "command expiry restores chat")

            db.set_settings_bulk({
                "list_overlay_show_mode": "always",
                "combined_list_chat_layout": "split",
            })
            api.configure_list_show("always", "!list", 3)
            until(view.page(), lambda a: a["shown"] and not a["replace"] and
                  a["chatHeight"] > 15 and a["listHeight"] > 15,
                  "saved split mode restored")

            state.set_obs_enabled("twitch", False)
            until(view.page(), lambda a: a["shown"] and a["chatHeight"] < 2
                  and a["listHeight"] >= a["rootHeight"] - 3,
                  "chat off, list owns full area")

            db.set_setting("list_overlay_show_mode", "hidden")
            api.configure_list_show("hidden", "!list", 3)
            until(view.page(), lambda a: not a["shown"] and
                  a["chatHeight"] < 2 and a["listHeight"] < 2 and
                  a["obsVisible"] == "false",
                  "both hidden, no visible content")
            print("R06_COMBINED_BROWSER_ALL_PASS", flush=True)
        finally:
            view.close()
            api.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
