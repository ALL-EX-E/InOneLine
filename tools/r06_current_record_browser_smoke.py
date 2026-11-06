"""R06-012: real Chromium verifies the main OBS current-record title and typography."""
from __future__ import annotations

import json
import os
import socket
import sys
import time
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
from streaming_manager.constants import STATUS_NOT_PLAYED, STATUS_PLAYING
from streaming_manager.database import Database, Game
from streaming_manager.multichat import MultichatState

JS = """JSON.stringify((() => {
 const banner = document.getElementById('game-title-banner');
 if (!banner || !banner.offsetHeight) return {ready:false};
 const style = getComputedStyle(banner);
 return {
   ready:true,
   text:banner.textContent,
   size:style.fontSize,
   family:style.fontFamily,
   color:style.color,
   opacity:style.opacity,
   transition:style.transitionDuration
 };
})())"""


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def measure(page):
    replies = []
    page.runJavaScript(JS, replies.append)
    end = time.monotonic() + 8
    while not replies and time.monotonic() < end:
        QTest.qWait(25)
    if not replies:
        raise AssertionError("R06 title Chromium JS timeout")
    return json.loads(replies[0]) if isinstance(replies[0], str) else replies[0]


def until(page, text, size, rgb, family, label):
    end = time.monotonic() + 35
    last = None
    while time.monotonic() < end:
        last = measure(page)
        if (last and last.get("ready")
                and last["text"] == text
                and last["size"] == f"{size}px"
                and rgb in last["color"]
                and family in last["family"]):
            assert last["opacity"] == "1", last
            assert all(float(x.strip().rstrip("s")) == 0
                       for x in last["transition"].split(",")), last
            print("R06_CURRENT_RECORD_BROWSER_PASS", label, last, flush=True)
            return
        QTest.qWait(100)
    raise AssertionError(f"R06 current-title {label} timeout: {last!r}")


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "current_record_browser.db")
        db.add_game(Game(None, "Первая ПРОХОДИТСЯ", None, status=STATUS_PLAYING))
        manual_id = db.add_game(Game(None, "Выбранная запись OBS", None,
                                    status=STATUS_NOT_PLAYED))
        db.set_settings_bulk({
            "stream_current_game_id": "",
            "overlay_font_title_family": "Segoe UI",
            "overlay_font_title_size": "30",
            "overlay_font_title_color": "#FFFFFF",
            "list_overlay_show_mode": "hidden",
        })
        state = MultichatState()
        api = LocalApiServer(db, port=free_port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.start()
        view = QWebEngineView()
        try:
            view.resize(1280, 720)
            view.show()
            view.load(QUrl(api.base_url + "/overlay"))
            until(view.page(), "Первая ПРОХОДИТСЯ", 30, "255, 255, 255",
                  "Segoe UI", "automatic initial")
            db.set_settings_bulk({
                "stream_current_game_id": str(manual_id),
                "overlay_font_title_family": "Arial",
                "overlay_font_title_size": "43",
                "overlay_font_title_color": "#23AABB",
            })
            until(view.page(), "Выбранная запись OBS", 43, "35, 170, 187",
                  "Arial", "explicit record and typography")
            db.set_settings_bulk({"stream_current_game_id": ""})
            until(view.page(), "Первая ПРОХОДИТСЯ", 43, "35, 170, 187",
                  "Arial", "automatic restored")
            print("R06_CURRENT_RECORD_CHROMIUM_ALL_PASS", flush=True)
        finally:
            view.close()
            api.stop()


if __name__ == "__main__":
    main()
