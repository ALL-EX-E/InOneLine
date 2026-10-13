"""P11-K4 FIX: real Qt Chromium Rules selected-template preview vs live OBS.

This closes the coverage gap: checking only HTTP endpoints cannot demonstrate
that the browser actually renders a selected inactive template separately.
"""
from __future__ import annotations
import os
import socket
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "windows")
if sys.platform != "win32":
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtTest import QTest
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QTextEdit

from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database, Game
from streaming_manager.constants import STATUS_NOT_PLAYED, STATUS_PLAYED
from streaming_manager.views.rules_editor import AuctionRulesEditorDialog


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def js(page, expression: str):
    result = []
    page.runJavaScript(expression, result.append)
    end = time.monotonic() + 8
    while not result and time.monotonic() < end:
        QTest.qWait(25)
    if not result:
        raise AssertionError("Browser JavaScript callback timed out")
    return result[0]


def wait_js(page, expression: str, expected, label: str, timeout: float = 25):
    end = time.monotonic() + timeout
    actual = None
    while time.monotonic() < end:
        actual = js(page, expression)
        if actual == expected:
            return
        QTest.qWait(70)
    raise AssertionError(f"{label}: got {actual!r}, expected {expected!r}")


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        db = Database(Path(temp) / "rules_preview.db")
        active = int(db.get_active_rule_template()["id"])
        # QTextEdit canonical HTML avoids a spurious unsaved-change prompt
        # when the editor loads our test templates.
        editor_text = QTextEdit()
        editor_text.setPlainText("B CHOSEN")
        html_b = editor_text.toHtml()
        editor_text.setPlainText("A LIVE")
        html_a = editor_text.toHtml()
        inactive = db.create_rule_template("Browser secondary", content_html=html_b, make_active=False)
        db.save_rule_template(active, html_a)
        db.save_rule_template_presentation(active, {
            "autoscroll": False, "background": "color",
            "background_color": "#883311", "background_opacity": 99, "padding": 18,
        })
        db.save_rule_template_presentation(inactive, {
            "autoscroll": False, "background": "color",
            "background_color": "#2277DD", "background_opacity": 91, "padding": 74,
        })
        db.add_game(Game(None, "Browser Preview A", "2026-01-01", 100, 0, STATUS_PLAYED, ""))
        db.add_game(Game(None, "Browser Preview B", "2026-01-01", 100, 0, STATUS_NOT_PLAYED, ""))
        auction_id = db.create_auction_session("max_amount", 60)
        before_snapshot = db.get_auction_rules_snapshot(auction_id)
        before_live = db.current_rules_payload()
        settings_before = db.get_settings()
        templates_before = db.list_rule_templates()
        server = LocalApiServer(db, port=free_port())
        server.start()
        base_url = server.base_url + "/rules-overlay"
        editor = AuctionRulesEditorDialog(db, rules_overlay_url=lambda: base_url)
        views = []
        try:
            editor.show()
            app.processEvents()
            assert editor._loaded_template_id == active
            assert int(editor.template_combo.currentData()) == active
            other_index = editor.template_combo.findData(inactive)
            assert other_index >= 0
            editor.template_combo.setCurrentIndex(other_index)
            app.processEvents()
            assert int(editor.template_combo.currentData()) == inactive, "Qt combobox did not select B"
            assert editor._loaded_template_id == inactive, "Qt editor still edits A"
            assert editor._is_dirty() is False, "Switching saved templates marked editor dirty"
            assert "Browser secondary" in editor.rules_preview_target_label.text()
            assert "неактивный шаблон" in editor.rules_preview_target_label.text()
            assert f"template_id={inactive}" in editor.preview_rules_obs_btn.toolTip()

            urls = []
            with patch.object(QDesktopServices, "openUrl", side_effect=lambda url: urls.append(url.toString()) or True):
                editor.preview_rules_obs_btn.click()
            assert urls == [f"{base_url}?preview=1&template_id={inactive}"], urls
            preview_url = urls[0]
            assert db.current_rules_payload() == before_live, "Clicking preview changed live rules"

            # Both real Chromium Browser Sources are visible side by side, to
            # avoid Chromium background throttling hiding a polling regression.
            screen = app.primaryScreen().availableGeometry()
            width = min(700, max(320, (screen.width() - 48) // 2))
            height = min(520, max(240, screen.height() - 90))
            for i, url in enumerate((base_url, preview_url)):
                view = QWebEngineView()
                view.resize(width, height)
                view.move(screen.x() + 8 + i * (width + 8), screen.y() + 8)
                view.show()
                view.load(QUrl(url))
                views.append(view)
            views[0].raise_()
            views[0].activateWindow()
            app.processEvents()
            live_page, preview_page = (v.page() for v in views)
            expr = "document.getElementById('content')?.textContent.trim()"
            wait_js(live_page, expr, "A LIVE", "Real on-air browser rules")
            wait_js(preview_page, expr, "B CHOSEN", "Real browser inactive selected rules")
            wait_js(preview_page, "new URLSearchParams(location.search).get('template_id')", str(inactive), "Preview URL id")
            wait_js(preview_page, "document.querySelector('#viewport').style.padding", "74px", "Preview B styling")
            wait_js(live_page, "document.querySelector('#viewport').style.padding", "18px", "On-air A styling")
            # Saving a new style for inactive B changes preview only.
            db.save_rule_template_presentation(inactive, {
                "autoscroll": False, "background": "color",
                "background_color": "#2277DD", "background_opacity": 91, "padding": 91,
            })
            wait_js(preview_page, "document.querySelector('#viewport').style.padding", "91px", "Preview update B")
            wait_js(live_page, expr, "A LIVE", "On-air remains A")
            assert db.get_auction_rules_snapshot(auction_id) == before_snapshot
            assert db.current_rules_payload() == before_live
            assert db.list_rule_templates()[0]["id"] == templates_before[0]["id"]
            assert db.get_settings() == settings_before
        finally:
            for view in views:
                view.close()
                view.deleteLater()
            editor.close()
            editor.deleteLater()
            QTest.qWait(100)
            server.stop()

    print("P11_K4_SELECTED_RULES_QT_CHROMIUM_END_TO_END_ISOLATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
