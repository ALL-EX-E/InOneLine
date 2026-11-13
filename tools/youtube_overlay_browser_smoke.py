"""Render both platforms in the real OBS Chromium page without provider access."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtTest import QTest
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication


ROOT = Path(__file__).resolve().parents[1]


def evaluate(page, script):
    answers = []
    page.runJavaScript(script, answers.append)
    until = time.monotonic() + 8
    while not answers and time.monotonic() < until:
        QTest.qWait(20)
    if not answers:
        raise AssertionError("Chromium did not return a result")
    return answers[0]


def main():
    app = QApplication.instance() or QApplication([])
    view = QWebEngineView()
    view.resize(640, 480)
    url = QUrl.fromLocalFile(str(ROOT / "streaming_manager" / "web" / "multichat_overlay.html"))
    url.setQuery("embedded=1")
    view.load(url)
    view.show()
    until = time.monotonic() + 10
    while time.monotonic() < until:
        if evaluate(view.page(), "typeof window.IOLRenderEmbeddedChatState") == "function":
            break
        QTest.qWait(50)
    else:
        raise AssertionError("OBS renderer did not load")

    snapshot = {
        "appearance": {
            "twitch": {"mode": "custom", "card_color": "#112233", "card_opacity": 100,
                       "name_size": 20},
            "youtube": {"mode": "custom", "card_color": "#445566", "card_opacity": 100,
                        "name_size": 32},
            "common": {"visibility": "hide_empty"},
        },
        "obs_enabled": {"twitch": False, "youtube": False},
        "show_time": False,
        "show_platform_icons": True,
        "messages": [
            {"platform": "twitch", "author": "T", "text": "Twitch row"},
            {"platform": "youtube", "author": "Y", "text": "YouTube row"},
        ],
    }
    evaluate(view.page(), "window.IOLRenderEmbeddedChatState(" + json.dumps(snapshot) + "); true;")
    rows = json.loads(evaluate(view.page(), "JSON.stringify([...document.querySelectorAll('.message')].map(row => ({text:row.textContent,bg:row.style.background,icon:row.querySelector('.platform-icon')?.getAttribute('aria-label'),height:row.querySelector('.platform-icon')?.style.height})))"))
    assert [row["text"].endswith(suffix) for row, suffix in zip(rows, ("Twitch row", "YouTube row"))] == [True, True], rows
    assert "17, 34, 51" in rows[0]["bg"] and "68, 85, 102" in rows[1]["bg"], rows
    assert [row["icon"] for row in rows] == ["Twitch", "YouTube"], rows
    assert [row["height"] for row in rows] == ["20px", "32px"], rows
    assert evaluate(view.page(), "document.getElementById('shell').classList.contains('hidden')") is False
    view.close()
    app.processEvents()
    print("YOUTUBE_OBS_BROWSER_PASS", flush=True)


if __name__ == "__main__":
    sys.exit(main())
