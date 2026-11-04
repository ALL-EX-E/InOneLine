"""D41-AUDIT-FONT-003: Python/Chromium parity for OBS Twitch font names.

Exercises the real standalone and embedded HTML renderers with controlled
HTTP responses, independent of Twitch credentials or installed font families.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "windows")
if sys.platform != "win32":
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from streaming_manager.api_server import LocalApiServer
from streaming_manager.chat_appearance import normalize_twitch
from streaming_manager.database import Database
from streaming_manager.multichat import MultichatState
from tools.chat_poll_order_browser_smoke import (
    INJECT_FETCH, evaluate, free_port, snapshot, until,
)

FONT_DOM = """JSON.stringify((() => ({
  text: document.querySelector('.message .text')?.textContent ?? '',
  messageFont: document.querySelector('.message')?.style.fontFamily ?? '',
  nameFont: document.querySelector('.message .name')?.style.fontFamily ?? ''
}))())"""

# Last two fields are the expected Python/backend values after normalization.
CASES = (
    ("ascii", "Segoe UI", "Arial", "Segoe UI", "Arial"),
    ("cyrillic_cjk", "Шрифт Тест", "字体中文", "Шрифт Тест", "字体中文"),
    ("latin_accents", "École", "Çeşit", "École", "Çeşit"),
    ("astral_codepoint", "𠀀", "𠀀 Mono", "𠀀", "𠀀 Mono"),
    ("max_80_codepoints", "字" * 80, "𠀀" * 80, "字" * 80, "𠀀" * 80),
    ("over_80_codepoints", "字" * 81, "𠀀" * 81, "Segoe UI", "Segoe UI"),
    ("unsafe_css", "Arial;};alert(1)", "Roboto\nInjected", "Segoe UI", "Segoe UI"),
    ("combining_mark", "A\u0301", "B\u0301", "Segoe UI", "Segoe UI"),
)


def verify(page, *, embedded: bool):
    last_request_index = -1
    for label, text_font, name_font, expected_text, expected_name in CASES:
        normalized = normalize_twitch({
            "mode": "custom", "text_font": text_font, "name_font": name_font,
        })
        assert normalized["text_font"] == expected_text, (label, "Python text", normalized)
        assert normalized["name_font"] == expected_name, (label, "Python name", normalized)

        # Preserve the original values in the mock HTTP response, so Chromium's
        # own validation is exercised rather than relying on Python fallback.
        state = snapshot([f"UNICODE-{label}"])
        state["appearance"]["twitch"].update({
            "mode": "custom", "text_font": text_font, "name_font": name_font,
        })
        until(page, lambda s: s["ready"] and s["requests"] > last_request_index + 1,
              "fresh Chromium font poll available")
        request_index = evaluate(page, "window.__chatPollQA.requests.length - 1")
        last_request_index = request_index
        assert evaluate(
            page,
            f"window.__chatPollQA.requests[{request_index}].succeed("
            f"{json.dumps(state, ensure_ascii=False)}); true;",
        ) is True
        until(page, lambda s: s["messages"] and
              f"UNICODE-{label}" in s["messages"][0],
              f"Chromium rendered {label}")
        dom = evaluate(page, FONT_DOM)
        assert f"UNICODE-{label}" in dom["text"], (label, dom)
        assert expected_text in dom["messageFont"], (label, "text font", dom)
        assert expected_name in dom["nameFont"], (label, "name font", dom)
        if expected_text == "Segoe UI" and text_font != "Segoe UI":
            assert text_font not in dom["messageFont"], (label, dom)
        if expected_name == "Segoe UI" and name_font != "Segoe UI":
            assert name_font not in dom["nameFont"], (label, dom)
    print("D41_UNICODE_FONTS_PASS", "embedded" if embedded else "standalone", flush=True)


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as root:
        db = Database(Path(root) / "unicode_font.db")
        api = LocalApiServer(db, port=free_port())
        state = MultichatState()
        api.set_multichat_state_provider(state.snapshot)
        api.start()
        try:
            for embedded in (False, True):
                view = QWebEngineView()
                view.resize(480, 520)
                script = QWebEngineScript()
                script.setName("qa-unicode-chat-fonts")
                script.setInjectionPoint(QWebEngineScript.DocumentCreation)
                script.setWorldId(QWebEngineScript.MainWorld)
                script.setRunsOnSubFrames(True)
                script.setSourceCode(INJECT_FETCH)
                view.page().scripts().insert(script)
                try:
                    view.show()
                    route = "/multichat-overlay?embedded=1" if embedded else "/multichat-overlay"
                    view.load(QUrl(api.base_url + route))
                    until(view.page(), lambda s: s["ready"], "Twitch font document ready")
                    verify(view.page(), embedded=embedded)
                finally:
                    view.close()
                    view.deleteLater()
                    app.processEvents()
        finally:
            api.stop()


if __name__ == "__main__":
    main()
