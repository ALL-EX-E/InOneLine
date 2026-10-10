"""Exercise common OBS visibility through real SQLite, Qt and Browser Sources."""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streaming_manager.api_server import LocalApiServer
from streaming_manager.constants import STATUS_NOT_PLAYED
from streaming_manager.database import Database, Game


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def read_json(server, route):
    with urlopen(server.base_url + route, timeout=5) as response:
        assert response.headers.get_content_type() == "application/json"
        assert response.headers.get("Cache-Control") == "no-store"
        return json.load(response)


def policy_smoke() -> None:
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "data" / "streaming.db")
        assert "visibility" in db.current_stream_payload(), "Missing common OBS visibility contract"
        from streaming_manager.obs_visibility import (
            WIDGETS, show_mode, visibility_payload, wheel_context_relevant,
        )
        expected = {"overlay", "list", "timer", "music_player", "auction_lots", "rules", "wheel"}
        assert set(WIDGETS) == expected
        for widget, spec in WIDGETS.items():
            default = "track_change" if widget == "music_player" else "context" if widget == "wheel" else "always"
            assert spec.default == default
            assert show_mode({}, widget) == default
            assert show_mode({spec.key: "bogus"}, widget) == default
            for mode, label in spec.options:
                assert show_mode({spec.key: mode}, widget) == mode
                assert label in {"Не показывать", "При смене трека", "Когда колесо используется", "Показывать постоянно"}
            assert visibility_payload({spec.key: "hidden"}, widget, False) == {
                "show_mode": "hidden", "context_visible": False,
            }
        assert show_mode({"rules_overlay_visible": "0"}, "rules") == "hidden"
        assert show_mode({"rules_overlay_visible": "1"}, "rules") == "always"
        assert show_mode({"rules_overlay_visible": "0", "rules_overlay_show_mode": "always"}, "rules") == "always"
        assert show_mode({"rules_overlay_visible": "1", "rules_overlay_show_mode": "hidden"}, "rules") == "hidden"
        assert show_mode({"rules_overlay_visible": "0", "rules_overlay_show_mode": "invalid"}, "rules") == "always"

        cases = [
            (None, "max_amount", False), (None, "weighted_wheel", True),
            ({"mode": "max_amount", "status": "running"}, "weighted_wheel", False),
            ({"mode": "max_amount", "status": "paused"}, "weighted_wheel", False),
            ({"mode": "max_amount", "status": "awaiting_resolution"}, "weighted_wheel", False),
            ({"mode": "max_amount", "status": "tie_break_required"}, "weighted_wheel", False),
            ({"mode": "max_amount", "status": "awaiting_wheel"}, "max_amount", True),
            ({"mode": "max_amount", "status": "winner_selected", "wheel_spin_id": "spin"}, "max_amount", True),
        ]
        cases += [({"mode": "weighted_wheel", "status": status}, "max_amount", True)
                  for status in ("awaiting_wheel", "running", "winner_selected")]
        for session, selected, expected_context in cases:
            assert wheel_context_relevant(session, selected) is expected_context, (session, selected)

        db.add_game(Game(None, "Visibility contract lot", None, 100, 0, STATUS_NOT_PLAYED, ""))
        db.add_game(Game(None, "Visibility contract second lot", None, 100, 0, STATUS_NOT_PLAYED, ""))
        stream_before = db.current_stream_payload()
        timer_runtime = {"mode": "max_amount", "audio": {
            "enabled": True, "owner": "auction", "active": True, "kind": "auction",
            "media_id": 42, "playing": True, "position_ms": 5000, "gain": 0.4,
        }}
        timer_before = db.current_timer_payload(timer_runtime)
        lots_before = db.current_auction_lots_payload()
        reads = {
            "overlay": lambda: db.current_stream_payload()["visibility"]["overlay"],
            "list": lambda: db.current_stream_payload()["visibility"]["list"],
            "timer": lambda: db.current_timer_payload()["visibility"],
            "auction_lots": lambda: db.current_auction_lots_payload()["visibility"],
            "rules": lambda: db.current_rules_payload()["visibility"],
            "wheel": lambda: db.current_wheel_payload()["visibility"],
        }
        db.set_settings_bulk({spec.key: "hidden" for spec in WIDGETS.values()})
        with db.connect() as conn:
            before = "\n".join(conn.iterdump())
        for read in reads.values():
            assert read()["show_mode"] == "hidden"
        from streaming_manager.music_player import music_player_overlay_appearance
        assert music_player_overlay_appearance(db)["show_mode"] == "hidden"
        for before_payload, after_payload in (
            (stream_before, db.current_stream_payload()),
            (timer_before, db.current_timer_payload(timer_runtime)),
            (lots_before, db.current_auction_lots_payload()),
        ):
            assert {k: v for k, v in before_payload.items() if k != "visibility"} == {
                k: v for k, v in after_payload.items() if k != "visibility"
            }, "Mode changed business/audio/layout payload"
        with db.connect() as conn:
            assert "\n".join(conn.iterdump()) == before, "Presentation reads mutated SQLite"

        runtime = {"mode": "max_amount"}
        server = LocalApiServer(db, port=free_port())
        server.set_auction_lots_state_provider(lambda: runtime)
        server.start()
        try:
            broad = read_json(server, "/api/wheel")
            assert broad["visible"] and broad["sectors"]
            assert broad["visibility"]["context_visible"] is False
            runtime["mode"] = "weighted_wheel"
            assert read_json(server, "/api/wheel")["visibility"]["context_visible"] is True
            session_id = db.create_auction_session("max_amount", 60)
            assert read_json(server, "/api/wheel")["visibility"]["context_visible"] is False
            db.pause_auction(session_id)
            assert read_json(server, "/api/wheel")["visibility"]["context_visible"] is False
            db.finish_auction(session_id)
            assert db.get_open_auction_session()["status"] == "tie_break_required"
            assert read_json(server, "/api/wheel")["visibility"]["context_visible"] is False
            db.start_auction_tie_overtime(session_id, 10)
            assert read_json(server, "/api/wheel")["visibility"]["context_visible"] is False
            db.finish_auction(session_id)
            db.start_auction_tie_wheel(session_id)
            assert read_json(server, "/api/wheel")["visibility"]["context_visible"] is True
            db.run_weighted_wheel(session_id, pick=0)
            db.prepare_wheel_animation(session_id)
            assert read_json(server, "/api/wheel")["visibility"]["context_visible"] is True
            db.cancel_auction(session_id)
            assert read_json(server, "/api/wheel")["visibility"]["context_visible"] is True
            session_id = db.create_auction_session("weighted_wheel", 0, start_in_wheel_mode=True)
            assert read_json(server, "/api/wheel")["visibility"]["context_visible"] is True
            db.run_weighted_wheel(session_id, pick=0)
            assert read_json(server, "/api/wheel")["visibility"]["context_visible"] is True
            db.cancel_auction(session_id)
            runtime["mode"] = "max_amount"
            assert read_json(server, "/api/wheel")["visibility"]["context_visible"] is False
            for route in ("/api/data", "/api/timer", "/api/auction-lots", "/api/rules"):
                assert "visibility" in read_json(server, route)
        finally:
            server.stop()
    print("P10_OBS_VISIBILITY_POLICY_API_READONLY=PASS")


def ui_smoke() -> None:
    from PySide6.QtCore import QThreadPool, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
    from streaming_manager.app_paths import AppPaths
    from streaming_manager.obs_visibility import WIDGETS, show_mode
    from streaming_manager.ui import MainWindow
    from tools.gui_regression_smoke import (
        assert_p09_api_ui_cleanup, assert_p09_obs_access, assert_p09_list_group,
    )

    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        paths = AppPaths.from_root(Path(tmp))
        paths.ensure_runtime_dirs()
        db = Database(paths.database_path)
        db.set_settings_bulk({"api_port": str(free_port()), "rules_overlay_visible": "0"})
        window = MainWindow(db, paths)
        try:
            window.show()
            window._set_current_main_page(window.stream_tab)
            app.processEvents()
            QTest.qWait(600)  # Let scheduled startup work start before fixture teardown.
            stream = window.stream_tab
            assert hasattr(stream, "obs_show_modes"), "Missing seven common OBS mode controls"
            assert set(stream.obs_show_modes) == set(WIDGETS)
            assert not hasattr(stream, "rules_overlay_visible"), "Competing Rules visibility switch"
            assert stream.music_player_show_mode is stream.obs_show_modes["music_player"]
            assert stream.main_settings_form.rowCount() == 2, "Accepted typography group changed"
            forms = {
                "overlay": stream.main_visibility_form, "list": stream.overlay_form,
                "timer": stream.timer_overlay_form, "music_player": stream.music_player_overlay_form,
                "auction_lots": stream.auction_lots_overlay_form,
                "rules": stream.rules_overlay_form, "wheel": stream.wheel_overlay_form,
            }
            saved_before = db.get_settings()
            for widget, combo in stream.obs_show_modes.items():
                spec = WIDGETS[widget]
                assert tuple((combo.itemData(i), combo.itemText(i)) for i in range(combo.count())) == spec.options
                assert forms[widget].labelForField(combo).text() == "Показ виджета:"
                assert combo.currentData() == show_mode(saved_before, widget)
                assert forms[widget].getWidgetPosition(combo)[0] == (2 if widget == "list" else 0)
            assert db.get_settings() == saved_before, "Refresh wrote visibility defaults"
            auction = window.auction_tab
            auction.mode_combo.setCurrentIndex(auction.mode_combo.findData("max_amount"))
            stream.obs_show_modes["wheel"].setCurrentIndex(stream.obs_show_modes["wheel"].findData("always"))
            with patch.object(QMessageBox, "information"):
                stream._save_wheel_overlay_settings()
            assert auction._wheel_context_relevant(None) is False, "OBS Always changed local wheel visibility"
            assert read_json(window.api, "/api/wheel")["visibility"]["show_mode"] == "always"
            auction.mode_combo.setCurrentIndex(auction.mode_combo.findData("weighted_wheel"))
            assert auction._wheel_context_relevant(None) is True
            assert read_json(window.api, "/api/wheel")["visibility"]["context_visible"] is True
            auction.mode_combo.setCurrentIndex(auction.mode_combo.findData("max_amount"))
            stream.overlay_list_enabled.setChecked(False)
            app.processEvents()
            assert stream.obs_show_modes["list"].isVisible() and stream.obs_show_modes["list"].isEnabled()
            assert_p09_api_ui_cleanup(window, db)
            assert_p09_obs_access(app, window, db)
            assert_p09_list_group(app, stream, db)

            saves = {
                "overlay": "Сохранить", "list": "Сохранить",
                "timer": "Сохранить виджет таймера", "music_player": "Сохранить виджет плеера",
                "auction_lots": "Сохранить виджет списка лотов",
                "rules": "Сохранить виджет правил", "wheel": "Сохранить виджет колеса",
            }
            for widget in WIDGETS:
                combo = stream.obs_show_modes[widget]
                combo.setCurrentIndex(combo.findData("hidden"))
                before = db.get_settings()
                if widget in {"overlay", "list"}:
                    button = stream.main_save_buttons["current_game" if widget == "overlay" else "list"]
                else:
                    button, = [b for b in stream.findChildren(QPushButton) if b.text() == saves[widget]]
                with patch.object(QMessageBox, "information"):
                    button.click()
                after = db.get_settings()
                assert after[WIDGETS[widget].key] == "hidden", widget
                for other, spec in WIDGETS.items():
                    if other != widget and not (widget in {"overlay", "list"} and other in {"overlay", "list"}):
                        assert after.get(spec.key) == before.get(spec.key), (widget, other)
                assert after["rules_overlay_visible"] == "0", "Rules Save reactivated legacy switch"
                stream.refresh()
                assert combo.currentData() == "hidden"
            for width in (520, 1100, 2560, 520):
                window.resize(width, 900)
                app.processEvents()
                assert all(combo.isVisible() for combo in stream.obs_show_modes.values())
                assert all(combo.geometry().right() <= combo.parentWidget().width()
                           for combo in stream.obs_show_modes.values()), "Mode row overflows narrow page"
            saved = db.get_settings()
        finally:
            window.api.stop()
            QThreadPool.globalInstance().waitForDone(15000)
            window.close()
            app.processEvents()

        # A fresh window/server, not only refresh of the same controls.
        window = MainWindow(Database(paths.database_path), paths)
        try:
            QTest.qWait(600)
            assert window.db.get_settings() == saved
            assert all(combo.currentData() == "hidden" for combo in window.stream_tab.obs_show_modes.values())
        finally:
            window.api.stop()
            QThreadPool.globalInstance().waitForDone(15000)
            window.close()
            app.processEvents()
    print("P10_OBS_VISIBILITY_QT_SAVES_RESTART=PASS")


def browser_smoke() -> None:
    from PySide6.QtCore import QUrl, Qt
    from PySide6.QtGui import QColor
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from streaming_manager.obs_visibility import WIDGETS
    from streaming_manager.views.stream import StreamTab

    if sys.platform != "win32":
        os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")
    app = QApplication.instance() or QApplication([])

    def js(page, expression):
        result = []
        page.runJavaScript(expression, result.append)
        deadline = time.monotonic() + 5
        while not result and time.monotonic() < deadline:
            QTest.qWait(20)
        assert result, "JavaScript callback timed out"
        return result[0]

    def wait_js(page, expression, expected, label, timeout=8):
        deadline = time.monotonic() + timeout
        actual = None
        while time.monotonic() < deadline:
            actual = js(page, expression)
            if actual == expected:
                return
            QTest.qWait(50)
        raise AssertionError(f"{label}: {actual!r} != {expected!r}")

    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "data" / "streaming.db")
        db.set_settings_bulk({spec.key: "hidden" for spec in WIDGETS.values()})
        runtime = {"mode": "max_amount"}
        music = {"playing": True, "stopped": False, "suppressed": False,
                 "event_serial": 17, "event_started_at_ms": int(time.time() * 1000),
                 "display_title": "Visibility QA music", "filename": "visibility.wav",
                 "browser_audible": False, "position_ms": 0}
        server = LocalApiServer(db, port=free_port())
        server.set_auction_lots_state_provider(lambda: runtime)
        server.set_music_player_state_provider(lambda: music)
        server.start()
        stream = StreamTab(db, server)
        handlers = {
            "overlay": stream.save, "list": stream.save,
            "timer": stream._save_timer_overlay_settings,
            "music_player": stream._save_music_player_overlay_settings,
            "auction_lots": stream._save_auction_lots_overlay_settings,
            "rules": stream._save_rules_overlay_settings,
            "wheel": stream._save_wheel_overlay_settings,
        }

        def save(widget, mode):
            combo = stream.obs_show_modes[widget]
            combo.setCurrentIndex(combo.findData(mode))
            with patch.object(QMessageBox, "information"):
                handlers[widget]()

        routes = {"overlay": "/overlay", "list": "/list-overlay", "timer": "/timer-overlay",
                  "music_player": "/music-player-overlay", "auction_lots": "/auction-lots-overlay",
                  "rules": "/rules-overlay", "wheel": "/wheel-overlay"}
        visible = "document.documentElement?.dataset.obsVisible"
        mode_js = "document.documentElement?.dataset.obsShowMode"
        try:
            for widget, route in routes.items():
                views = [QWebEngineView(), QWebEngineView()]
                try:
                    before_settings = db.get_settings()
                    # On Windows, two same-position top-level Chromium windows
                    # occlude each other. The covered normal Browser Source can
                    # suspend its poll timer and never observe a live Save.
                    # Exercise normal and preview side-by-side on the actual
                    # available screen to test the real live-update contract.
                    screen = app.primaryScreen().availableGeometry()
                    view_width = min(720, max(320, (screen.width() - 32) // 2))
                    view_height = min(540, max(240, screen.height() - 80))
                    for index, (view, suffix) in enumerate(zip(views, ("", "?preview=1"))):
                        view.resize(view_width, view_height)
                        view.move(screen.x() + 8 + index * (view_width + 8), screen.y() + 8)
                        view.page().setBackgroundColor(QColor(Qt.transparent))
                        view.show()
                        view.load(QUrl(server.base_url + route + suffix))
                    normal, preview = (view.page() for view in views)
                    wait_js(normal, "document.documentElement?.dataset.obsPolicyReady", "true", route + " ready")
                    wait_js(preview, "document.documentElement?.dataset.obsPolicyReady", "true", route + " preview ready")
                    wait_js(normal, visible, "false", route + " hidden")
                    wait_js(normal, "getComputedStyle(document.documentElement).opacity", "0", route + " transparent")
                    wait_js(preview, visible, "true", route + " hidden-mode preview")
                    assert db.get_settings() == before_settings, "Preview changed persisted mode"
                    assert music["event_serial"] == 17, "Preview manufactured a music event"
                    if widget == "rules":
                        wait_js(preview, "document.querySelector('#root').classList.contains('visible')", True, "Empty Rules preview")
                        assert js(preview, "document.querySelector('#content').textContent.trim().length") > 0
                    if widget == "music_player":
                        wait_js(preview, "document.querySelector('#card').classList.contains('visible')", True, "Playing hidden Music preview")

                    polls = "performance.getEntriesByType('resource').filter(e => e.name.includes('/api/')).length"
                    count = js(normal, polls)
                    wait_js(normal, f"({polls}) > {count}", True, route + " hidden page still polls")
                    if widget in {"list", "auction_lots"}:
                        title = f"Hidden live {widget} lot"
                        db.add_game(Game(None, title, None, 100, 0, STATUS_NOT_PLAYED, ""))
                        wait_js(normal, f"document.body.textContent.includes({json.dumps(title)})", True,
                                route + " hidden content stays live")
                    if widget == "timer":
                        runtime["mode"] = "weighted_wheel"
                        wait_js(normal, "document.querySelector('#timer').getAttribute('aria-label')",
                                "00:00:08.000", "Hidden timer receives authoritative change")
                        runtime["mode"] = "max_amount"
                    if widget == "music_player":
                        music["display_title"] = "Hidden music stays live"
                        wait_js(normal, "document.querySelector('#titleInner').textContent",
                                "Hidden music stays live", "Hidden Music receives title without event")
                    save(widget, "always")
                    assert db.get_settings()[WIDGETS[widget].key] == "always", route + " Save did not persist"
                    if widget in {"overlay", "list"}:
                        assert read_json(server, "/api/data")["visibility"][widget]["show_mode"] == "always", route + " API stale after Save"
                    wait_js(normal, mode_js, "always", route + " live Save mode")
                    wait_js(normal, visible, "true", route + " live Save show")
                    assert views[0].url().toString() == server.base_url + route, "Save navigated Browser Source"
                    save(widget, "hidden")
                    wait_js(normal, visible, "false", route + " second live Save hide")
                    wait_js(preview, visible, "true", route + " preview after Save")
                    if widget == "music_player":
                        save(widget, "track_change")
                        wait_js(normal, mode_js, "track_change", "Music event mode")
                        wait_js(normal, "document.querySelector('#card').classList.contains('visible')", False, "Mode Save must wait for real next event")
                        assert music["event_serial"] == 17
                        music["event_serial"] = 18
                        music["event_started_at_ms"] = int(time.time() * 1000)
                        db.set_settings_bulk({"music_player_overlay_duration_seconds": "5"})
                        wait_js(normal, "document.querySelector('#card').classList.contains('visible')", True, "Real Music event")
                        QTest.qWait(5300)
                        wait_js(normal, "document.querySelector('#card').classList.contains('visible')", False, "Music event expires")
                        wait_js(preview, "document.querySelector('#card').classList.contains('visible')", True, "Music preview ignores event expiry")
                        music["event_serial"] = 17
                    if widget == "wheel":
                        save(widget, "context")
                        wait_js(normal, visible, "false", "Wheel Max prestart")
                        runtime["mode"] = "weighted_wheel"
                        wait_js(normal, visible, "true", "Wheel weighted prestart")
                        runtime["mode"] = "max_amount"
                        wait_js(normal, visible, "false", "Wheel restored Max prestart")
                        wait_js(preview, visible, "true", "Wheel context-false preview")
                    print(f"P10_OBS_BROWSER_{widget.upper()}_LIVE_PREVIEW=PASS")
                finally:
                    for view in views:
                        view.close()
                        view.deleteLater()
                    QTest.qWait(50)
            with urlopen(server.base_url + "/obs-visibility.js", timeout=5) as response:
                assert response.headers.get_content_type() == "application/javascript"
                assert "ObsVisibility" in response.read().decode("utf-8")
        finally:
            stream.deleteLater()
            app.processEvents()
            server.stop()
    print("P10_OBS_VISIBILITY_REAL_BROWSER=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", action="store_true")
    parser.add_argument("--ui", action="store_true")
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args()
    if args.browser:
        browser_smoke()
    elif args.ui:
        ui_smoke()
    elif args.policy:
        policy_smoke()
    else:
        policy_smoke()
        browser_smoke()
        ui_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
