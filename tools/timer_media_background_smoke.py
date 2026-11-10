"""UI-045: real shared timer background, Qt Save/restart and Chromium smoke."""
from __future__ import annotations

import argparse
import os
import socket
import sys
import time
from pathlib import Path
from threading import Event
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.request import urlopen
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database
from streaming_manager.media import (
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, MEDIA_STORAGE_EXTERNAL,
    MEDIA_STORAGE_MANAGED,
)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def read_json(server, route):
    with urlopen(server.base_url + route, timeout=5) as response:
        assert response.status == 200
        assert response.headers.get("Cache-Control") == "no-store"
        return json.load(response)


def fixture_media(tmp: Path, suffix: str = ".gif") -> Path:
    source = tmp / ("P10-UI045-" + ("Video" if suffix == ".mp4" else "Image") + suffix)
    if suffix == ".gif":
        # Valid transparent 1x1 GIF; no optional Pillow/decode dependency.
        source.write_bytes(
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
            b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        )
    else:
        # Availability tests need a local resource, not a playable recording.
        source.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42")
    return source


def api_smoke() -> None:
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        db = Database(root / "data" / "streaming.db")
        source = fixture_media(root)
        asset = db.register_external_media_asset(
            MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, source,
        )
        default = db.current_timer_payload()
        assert default["tab_motion"] == {
            "follow_auction_tab": False, "auction_widgets_visible": False,
            "direction": "left", "duration_seconds": 0.65,
        }
        lots = db.current_auction_lots_payload()
        assert lots["visibility"]["show_mode"] == "always"
        assert lots["tab_motion"] == default["tab_motion"]
        assert default["presentation"]["background"] == "transparent"
        assert default["presentation"]["background_media"]["url"] == ""
        before_audio = default["audio"]
        before_state = {k: value for k, value in default.items()
                        if k not in {"presentation", "visibility"}}

        db.set_settings_bulk({
            "timer_overlay_background": "media",
            "timer_overlay_background_media_id": str(asset.id),
        })
        with db.connect() as conn:
            snapshot = "\n".join(conn.iterdump())
        media = db.current_timer_payload()["presentation"]["background_media"]
        assert media == {
            "asset_id": asset.id, "file": source.name, "type": "image",
            "available": True, "url": f"/media/{asset.id}",
        }, media
        result = db.current_timer_payload()
        assert result["audio"] == before_audio
        assert {k: value for k, value in result.items()
                if k not in {"presentation", "visibility"}} == before_state
        with db.connect() as conn:
            assert "\n".join(conn.iterdump()) == snapshot, "Read-only timer API mutated settings"

        server = LocalApiServer(db, port=free_port())
        server.start()
        try:
            live = read_json(server, "/api/timer")
            assert live["presentation"]["background_media"] == media
            with urlopen(server.base_url + f"/media/{asset.id}", timeout=5) as response:
                assert response.status == 200
                assert response.headers.get_content_type() == "image/gif"
                assert response.read() == source.read_bytes()

            source.unlink()
            missing = read_json(server, "/api/timer")
            assert missing["presentation"]["background"] == "media"
            assert missing["presentation"]["background_media"]["asset_id"] == asset.id
            assert missing["presentation"]["background_media"]["available"] is False
            assert missing["presentation"]["background_media"]["url"] == ""
            assert missing["remaining_ms"] == live["remaining_ms"]
            assert missing["audio"] == live["audio"]
            source = fixture_media(root)
            restored = read_json(server, "/api/timer")
            assert restored["presentation"]["background_media"] == media

            db.set_settings_bulk({"timer_overlay_background_media_id": "bogus"})
            bad = read_json(server, "/api/timer")["presentation"]["background_media"]
            assert bad["url"] == "" and bad["asset_id"] is None
            db.set_settings_bulk({"timer_overlay_background": "color"})
            assert read_json(server, "/api/timer")["presentation"]["background"] == "color"
            db.set_settings_bulk({"timer_overlay_background": "wrong"})
            assert read_json(server, "/api/timer")["presentation"]["background"] == "transparent"
        finally:
            server.stop()
    print("UI045_TIMER_MEDIA_API_SHARED_READONLY_MISSING_RESTORE=PASS")


def ui_smoke() -> None:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtTest import QTest
    from streaming_manager.views.stream import StreamTab

    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        db = Database(root / "data" / "streaming.db")
        source = fixture_media(root)
        server = LocalApiServer(db, port=free_port())
        server.start()
        stream = StreamTab(db, server)
        try:
            stream.show()
            app.processEvents()
            assert stream.timer_overlay_form.labelForField(
                stream.timer_overlay_font_size_control
            ).text() == "Размер шрифта:"
            assert stream.timer_overlay_form.labelForField(
                stream.timer_overlay_font_color_btn.parentWidget()
            ) is not None or stream.timer_overlay_form.rowCount() > 6
            assert (stream.timer_background_transparent.text(),
                    stream.timer_background_color_mode.text(),
                    stream.timer_background_media_mode.text()) == (
                        "Прозрачный", "Цвет", "Свой",
                    )
            assert stream.timer_overlay_form.labelForField(
                stream.timer_background_media_row
            ).text() == "Свой фон:"
            assert stream.timer_background_media_row.isHidden()
            assert stream.timer_background_color_row.isHidden()
            assert "Вывод музыки" in " ".join(
                label.text() for label in stream.findChildren(
                    __import__("PySide6.QtWidgets", fromlist=["QLabel"]).QLabel
                )
            )

            mode_combo = stream.obs_show_modes["timer"]
            assert not stream.timer_follow_auction_tab.isChecked()
            assert mode_combo.findData("slide") == -1
            assert stream.timer_slide_direction.currentData() == "left"
            assert stream.timer_slide_seconds.value() == 0.65
            assert not stream.timer_slide_direction.isEnabled()
            stream.timer_follow_auction_tab.setChecked(True)
            assert stream.timer_slide_direction.isEnabled()
            assert mode_combo.itemText(mode_combo.findData("slide")) == "Выезд"
            mode_combo.setCurrentIndex(mode_combo.findData("slide"))
            stream.timer_slide_direction.setCurrentIndex(
                stream.timer_slide_direction.findData("top")
            )
            stream.timer_slide_seconds.setValue(1.25)
            assert not read_json(server, "/api/timer")["tab_motion"]["follow_auction_tab"]
            with patch.object(QMessageBox, "information"):
                stream.timer_save_button.click()
            assert read_json(server, "/api/timer")["tab_motion"] == {
                "follow_auction_tab": True, "auction_widgets_visible": False,
                "direction": "top", "duration_seconds": 1.25,
            }
            assert read_json(server, "/api/timer")["visibility"]["show_mode"] == "slide"
            stream.timer_follow_auction_tab.setChecked(False)
            assert mode_combo.findData("slide") == -1
            assert mode_combo.currentData() == "always"
            stream.timer_slide_seconds.setValue(2)
            stream.refresh()
            assert stream.timer_follow_auction_tab.isChecked()
            assert mode_combo.currentData() == "slide"
            assert stream.timer_slide_direction.currentData() == "top"
            assert stream.timer_slide_seconds.value() == 1.25

            # Import exactly one shared external media asset using the original
            # P08 workflow, not an isolated timer registry or separate folder.
            with patch.object(QMessageBox, "information"):
                stream._apply_background_import(
                    source, MEDIA_STORAGE_EXTERNAL, "timer",
                )
                stream._apply_background_import(
                    source, MEDIA_STORAGE_EXTERNAL, "timer",
                )
            assets = db.media_assets_by_filename(
                MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, source.name,
            )
            assert len(assets) == 1, "Timer imported a duplicate media row"
            asset = assets[0]
            assert stream.timer_background_combo.currentData() == asset.id
            assert stream.background_combo.findData(asset.id) >= 0
            assert stream.auction_lots_background_combo.findData(asset.id) >= 0

            stream.timer_background_media_mode.setChecked(True)
            app.processEvents()
            assert stream.timer_background_media_row.isVisible()
            assert stream.timer_background_color_row.isHidden()
            untouched = db.get_settings([
                "overlay_background_media_id",
                "auction_lots_overlay_background_media_id",
            ])
            with patch.object(QMessageBox, "information"):
                stream._save_timer_overlay_settings()
            assert db.get_settings([
                "overlay_background_media_id",
                "auction_lots_overlay_background_media_id",
            ]) == untouched
            assert db.get_setting("timer_overlay_background") == "media"
            assert db.get_setting("timer_overlay_background_media_id") == str(asset.id)
            assert db.current_timer_payload()["presentation"]["background_media"]["url"] == f"/media/{asset.id}"

            stream.refresh()
            assert stream.timer_background_combo.currentData() == asset.id
            assert stream.timer_background_media_mode.isChecked()
            stream.timer_background_color_mode.setChecked(True)
            app.processEvents()
            assert stream.timer_background_color_row.isVisible()
            assert stream.timer_background_media_row.isHidden()
            with patch.object(QMessageBox, "information"):
                stream._save_timer_overlay_settings()
            assert db.get_setting("timer_overlay_background") == "color"
            # Changing modes must retain the chosen media for the next Save.
            assert db.get_setting("timer_overlay_background_media_id") == str(asset.id)

            # Reproduce the user's exact race: GIF is already saved, user
            # selects a new MP4 and presses Save while the managed copy is
            # still in flight. One click must save the NEW video automatically
            # after registration, without reselecting it in the combo.
            stream.timer_background_media_mode.setChecked(True)
            app.processEvents()
            video_source = fixture_media(root, ".mp4")
            copy_started, allow_copy = Event(), Event()
            actual_copy = stream._copy_background_video

            def delayed_copy(source_path, target_path):
                copy_started.set()
                if not allow_copy.wait(10):
                    raise TimeoutError("Test worker never received copy release")
                return actual_copy(source_path, target_path)

            with (
                patch.object(StreamTab, "_copy_background_video", staticmethod(delayed_copy)),
                patch.object(QMessageBox, "information") as notices,
            ):
                try:
                    stream._apply_background_import(
                        video_source, MEDIA_STORAGE_MANAGED, "timer",
                    )
                    deadline = time.monotonic() + 8
                    while not copy_started.is_set() and time.monotonic() < deadline:
                        QTest.qWait(20)
                    assert copy_started.is_set(), "Managed MP4 copy never began"
                    assert stream._background_copy_worker is not None
                    assert stream.timer_background_combo.currentData() == asset.id
                    stream._save_timer_overlay_settings()
                    assert stream._timer_save_waiting_for_video_copy, (
                        "First Save did not wait for the pending managed MP4"
                    )
                    assert db.get_setting("timer_overlay_background_media_id") == str(asset.id), (
                        "First Save incorrectly persisted the old selected GIF"
                    )
                finally:
                    allow_copy.set()
                deadline = time.monotonic() + 10
                while stream._background_copy_worker is not None and time.monotonic() < deadline:
                    QTest.qWait(20)
                app.processEvents()
                assert stream._background_copy_worker is None, "MP4 worker stuck"
                video_rows = db.media_assets_by_filename(
                    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, video_source.name,
                )
                assert len(video_rows) == 1 and video_rows[0].storage_mode == MEDIA_STORAGE_MANAGED
                video_asset = video_rows[0]
                assert stream.timer_background_combo.currentData() == video_asset.id
                assert db.get_setting("timer_overlay_background_media_id") == str(video_asset.id), (
                    "A single Save during copy did not apply the new MP4"
                )
                assert db.current_timer_payload()["presentation"]["background_media"]["url"] == (
                    f"/media/{video_asset.id}"
                )
                assert notices.call_count == 1, "Deferred MP4 Save was not acknowledged once"
                assert not stream._timer_save_waiting_for_video_copy
                assert stream.timer_save_button.text() == "Сохранить виджет таймера"

            # Return to the original GIF before the existing missing-source
            # regression; this also proves the new asynchronous code doesn't
            # prevent later manual selection and Save.
            stream.timer_background_combo.setCurrentIndex(
                stream.timer_background_combo.findData(asset.id)
            )
            with patch.object(QMessageBox, "information"):
                stream._save_timer_overlay_settings()
            assert db.get_setting("timer_overlay_background_media_id") == str(asset.id)

            source.unlink()
            stream._refresh_selected_background_availability()
            assert stream.timer_background_combo.findData(asset.id) < 0
            stream.refresh()
            assert not db.get_setting("timer_overlay_background_media_id"), (
                "Missing original persisted as a selectable Timer background"
            )
            fixture_media(root)
            stream._refresh_selected_background_availability()
            assert stream.timer_background_combo.findData(asset.id) >= 0
        finally:
            server.stop()
            stream.close()
            stream.deleteLater()
            QTest.qWait(100)
    print("UI045_TIMER_MEDIA_QT_IMPORT_DEDUP_SAVE_REFRESH=PASS")


def browser_smoke() -> None:
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtWebEngineWidgets import QWebEngineView

    from streaming_manager.app_paths import AppPaths
    from streaming_manager.views.main_window import MainWindow
    from tools.qt_browser_test_wait import wait_with_http_workers

    if sys.platform != "win32":
        os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")
    app = QApplication.instance() or QApplication([])

    def js(page, expression):
        result = []
        page.runJavaScript(f"JSON.stringify(({expression}) ?? null)", result.append)
        deadline = time.monotonic() + 5
        while not result and time.monotonic() < deadline:
            wait_with_http_workers(20)
        assert result, "Browser JavaScript callback timed out"
        return json.loads(result[0])

    def wait_js(page, expression, expected, label, timeout=8):
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            last = js(page, expression)
            if last == expected:
                return
            wait_with_http_workers(50)
        raise AssertionError(f"{label}: {last!r} != {expected!r}")

    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        db = Database(root / "data" / "streaming.db")
        paths = AppPaths.from_root(root)
        paths.ensure_runtime_dirs()
        image_file = fixture_media(root)
        image = db.register_external_media_asset(MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, image_file)
        video_file = fixture_media(root, ".mp4")
        video = db.register_external_media_asset(MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, video_file)
        db.set_settings_bulk({
            "timer_overlay_background": "media",
            "timer_overlay_background_media_id": str(image.id),
        })
        db.set_setting("api_port", str(free_port()))
        window = MainWindow(db, paths)
        window.show()
        window._set_current_main_page(window.stream_tab)
        server = window.api
        view = QWebEngineView()
        try:
            view.resize(800, 450)
            view.page().setBackgroundColor(QColor(Qt.transparent))
            view.show()
            view.load(QUrl(server.base_url + "/timer-overlay?preview=1"))
            page = view.page()
            ready = "document.documentElement?.dataset.obsPolicyReady"
            wait_js(page, ready, "true", "Timer policy ready")
            image_src = "document.querySelector('#timer-background-image').getAttribute('src')"
            video_src = "document.querySelector('#timer-background-video').getAttribute('src')"
            image_display = "document.querySelector('#timer-background-image').style.display"
            video_display = "document.querySelector('#timer-background-video').style.display"
            wait_js(page, image_src, f"/media/{image.id}", "Image URL")
            wait_js(page, image_display, "block", "Image visible")
            wait_js(page, video_display, "none", "Video hidden in image mode")
            # Existing timer audio sync can leave an empty src attribute: only
            # nonempty URLs would indicate that the visual background owns audio.
            assert js(page, "document.querySelector('#auction-audio').getAttribute('src')") in (None, ""), (
                "Visual timer background unexpectedly started auction audio"
            )

            db.set_settings_bulk({"timer_overlay_background_media_id": str(video.id)})
            wait_js(page, video_src, f"/media/{video.id}", "Video URL")
            wait_js(page, video_display, "block", "Video visible")
            wait_js(page, image_display, "none", "Image hidden in video mode")
            assert js(page, "document.querySelector('#timer-background-video').muted") is True
            assert js(page, "document.querySelector('#timer-background-video').loop") is True
            assert js(page, "document.querySelector('#timer-background-video').autoplay") is True
            assert js(page, "document.querySelector('#timer').getAttribute('aria-label')"), (
                "Authoritative timer text disappeared with video background"
            )

            # A concurrent localhost Range response can briefly hold the
            # external fixture open on Windows. Keep exercising deletion of
            # the live source once that reader has closed its file handle.
            delete_deadline = time.monotonic() + 5
            while True:
                try:
                    video_file.unlink()
                    break
                except PermissionError as error:
                    if getattr(error, "winerror", None) != 32 or time.monotonic() >= delete_deadline:
                        raise
                    wait_with_http_workers(25)
            wait_js(page, video_display, "none", "Missing original hides video")
            # Qt Chromium may return an empty string after removeAttribute;
            # either representation is safe as long as no media URL remains.
            assert js(page, video_src) in (None, ""), "Missing original still has a media URL"
            assert js(page, "document.querySelector('#timer').getAttribute('aria-label')")
            db.set_settings_bulk({"timer_overlay_background": "color",
                                  "timer_overlay_background_color": "#123456"})
            wait_js(page, "document.querySelector('#root').style.background",
                    "rgb(18, 52, 86)", "Color fallback")
            db.set_settings_bulk({"timer_overlay_background": "transparent"})
            wait_js(page, "document.querySelector('#root').style.background",
                    "transparent", "Transparent mode")

            stream = window.stream_tab
            auction = window.auction_tab
            button = auction.auction_widgets_button
            mode_combo = stream.obs_show_modes["timer"]

            def save_mode(mode):
                mode_combo.setCurrentIndex(mode_combo.findData(mode))
                assert mode_combo.currentData() == mode
                with patch.object(QMessageBox, "information"):
                    stream.timer_save_button.click()

            assert button.isHidden()
            stream.timer_follow_auction_tab.setChecked(True)
            stream.timer_slide_seconds.setValue(1.2)
            assert button.isHidden(), "Unsaved link created a control on Auction"
            save_mode("hidden")
            assert not button.isHidden()
            assert button.text() == "Показать виджеты аукциона"
            visible = "document.documentElement?.dataset.obsVisible"
            mode = "document.documentElement?.dataset.obsShowMode"
            pose = """(() => {
              const r = document.querySelector('#root')?.getBoundingClientRect();
              return r ? [Math.round(r.left), Math.round(r.top)] : null;
            })()"""
            wait_js(page, mode, "hidden", "Preview received saved mode")
            assert js(page, visible) == "true" and js(page, pose) == [0, 0]

            view.load(QUrl(server.base_url + "/timer-overlay"))
            wait_js(page, "location.search", "", "Live source loaded")
            wait_js(page, visible, "false", "Hidden takes priority in live source")
            window._set_current_main_page(auction)
            window.resize(1280, 760)
            wait_with_http_workers(150)
            rules_button = auction.auction_rules_editor_btn
            assert button.isVisible()
            assert button.y() == rules_button.y()
            assert button.x() > rules_button.geometry().right()
            window.resize(window.minimumWidth(), 640)
            wait_with_http_workers(150)
            viewport = window._main_tab_scroll_by_page[auction].viewport()
            assert button.mapTo(viewport, button.rect().topRight()).x() < viewport.width()
            button.click()
            assert button.text() == "Скрыть виджеты аукциона"
            assert read_json(server, "/api/timer")["tab_motion"]["auction_widgets_visible"]
            assert js(page, visible) == "false"
            button.click()

            save_mode("slide")
            wait_js(page, mode, "slide", "Live source received slide mode")
            axis_duration = """(() => {
              const motion = document.querySelector('#root').getAnimations()[0];
              return motion?.effect.getTiming().duration ?? null;
            })()"""
            for direction, outside in (
                ("left", [-800, 0]), ("right", [800, 0]),
                ("top", [0, -450]), ("bottom", [0, 450]),
            ):
                db.set_setting("timer_overlay_slide_direction", direction)
                wait_js(page, pose, outside, f"{direction} hidden position")
                axis = 0 if outside[0] else 1
                minimum, maximum = sorted([0, outside[axis]])
                intermediate = (
                    f"(({pose})[{axis}] > {minimum + 10} && "
                    f"({pose})[{axis}] < {maximum - 10} && ({pose})[{1 - axis}] === 0)"
                )

                button.click()
                assert button.text() == "Скрыть виджеты аукциона"
                wait_js(page, axis_duration, 1200, f"{direction} enter duration")
                wait_js(page, intermediate, True, f"{direction} moving in")
                wait_js(page, pose, [0, 0], f"{direction} entered")
                wait_js(page, axis_duration, None, f"{direction} entry complete")

                if direction == "left":
                    window._set_current_main_page(stream)
                    wait_with_http_workers(1600)
                    assert js(page, pose) == [0, 0], "Tab change hid the shown timer"
                    window._set_current_main_page(auction)
                    assert button.text() == "Скрыть виджеты аукциона"

                button.click()
                assert button.text() == "Показать виджеты аукциона"
                assert not read_json(server, "/api/timer")["tab_motion"]["auction_widgets_visible"]
                wait_js(page, axis_duration, 1200, f"{direction} exit duration")
                wait_js(page, intermediate, True, f"{direction} moving out")
                wait_js(page, pose, outside, f"{direction} exited")
                wait_js(page, axis_duration, None, f"{direction} exit complete")

            # Reverse before the entry settles and observe the outward leg.
            window._set_current_main_page(stream)
            wait_with_http_workers(300)
            window._set_current_main_page(auction)
            wait_with_http_workers(300)
            assert js(page, pose) == [0, 450], "Tab change revealed the hidden timer"

            button.click()
            wait_js(page, f"({pose})[1] < 300 && ({pose})[1] > 160",
                    True, "Partial entry before pressing Hide")
            button.click()
            wait_js(page, f"({pose})[1] > 310 && ({pose})[1] < 450",
                    True, "Rapid reversal travels back down")
            wait_js(page, pose, [0, 450], "Rapid reversal finished")

            save_mode("always")
            root_visibility = "getComputedStyle(document.querySelector('#root')).visibility"
            wait_js(page, root_visibility, "hidden", "Linked always mode waits for Show")
            button.click()
            wait_js(page, root_visibility, "visible", "Linked always mode appears immediately")
            assert js(page, axis_duration) is None

            stream.timer_follow_auction_tab.setChecked(False)
            save_mode("always")
            assert button.isHidden()
            assert not read_json(server, "/api/timer")["tab_motion"]["auction_widgets_visible"]
            assert mode_combo.findData("slide") == -1
            wait_js(page, pose, [0, 0], "Unlinked widget stays visible")
            window._set_current_main_page(stream)
            window._set_current_main_page(auction)
            wait_with_http_workers(400)
            assert js(page, root_visibility) == "visible"
            assert js(page, pose) == [0, 0] and js(page, axis_duration) is None

            lots_mode = stream.obs_show_modes["auction_lots"]
            assert lots_mode.findData("slide") == -1

            def save_lots(mode_name):
                lots_mode.setCurrentIndex(lots_mode.findData(mode_name))
                assert lots_mode.currentData() == mode_name
                with patch.object(QMessageBox, "information"):
                    stream._save_auction_lots_overlay_settings()

            stream.auction_lots_follow_auction_tab.setChecked(True)
            assert lots_mode.itemText(lots_mode.findData("slide")) == "Выезд"
            stream.auction_lots_slide_direction.setCurrentIndex(
                stream.auction_lots_slide_direction.findData("right")
            )
            stream.auction_lots_slide_seconds.setValue(1.8)
            assert button.isHidden(), "Unsaved lots binding enabled the Auction button"
            save_lots("slide")
            assert not button.isHidden(), "Lots binding alone must enable the Auction button"
            assert read_json(server, "/api/auction-lots")["tab_motion"] == {
                "follow_auction_tab": True, "auction_widgets_visible": False,
                "direction": "right", "duration_seconds": 1.8,
            }
            assert not read_json(server, "/api/timer")["tab_motion"]["follow_auction_tab"]
            stream.refresh()
            assert stream.auction_lots_follow_auction_tab.isChecked()
            assert lots_mode.currentData() == "slide"
            assert stream.auction_lots_slide_direction.currentData() == "right"
            assert stream.auction_lots_slide_seconds.value() == 1.8

            stream.timer_follow_auction_tab.setChecked(True)
            stream.timer_slide_direction.setCurrentIndex(stream.timer_slide_direction.findData("top"))
            stream.timer_slide_seconds.setValue(1.2)
            save_mode("slide")
            screen = app.primaryScreen().availableGeometry()
            source_width = min(800, (screen.width() - 36) // 2)
            view.resize(source_width, 450)
            view.move(screen.x() + 8, screen.y() + 8)
            lots_view = QWebEngineView()
            try:
                lots_view.resize(source_width, 450)
                lots_view.move(screen.x() + source_width + 16, screen.y() + 8)
                lots_view.page().setBackgroundColor(QColor(Qt.transparent))
                lots_view.show()
                lots_view.load(QUrl(server.base_url + "/auction-lots-overlay"))
                lots_page = lots_view.page()
                lots_pose = pose.replace("document.querySelector('#root')", "document.body")
                lots_duration = axis_duration.replace("document.querySelector('#root')", "document.body")

                wait_js(page, pose, [0, -450], "Timer hidden above its source")
                wait_js(lots_page, lots_pose, [source_width, 0], "Whole lots source hidden to its right")
                button.click()
                wait_js(page, axis_duration, 1200, "Timer enters in 1.2 seconds")
                wait_js(lots_page, lots_duration, 1800, "Lots enter in 1.8 seconds")
                wait_js(lots_page, f"({lots_pose})[0] > 10 && ({lots_pose})[0] < {source_width - 10}",
                        True, "Lots moving in horizontally")
                wait_js(page, pose, [0, 0], "Shared command showed timer")
                wait_js(lots_page, lots_pose, [0, 0], "Shared command showed lots")
                wait_js(lots_page, lots_duration, None, "Lots entry completed")

                window._set_current_main_page(stream)
                wait_with_http_workers(2100)
                assert js(lots_page, lots_pose) == [0, 0]
                assert js(page, pose) == [0, 0]
                window._set_current_main_page(auction)
                button.click()
                wait_js(page, axis_duration, 1200, "Timer leaves in 1.2 seconds")
                wait_js(lots_page, lots_duration, 1800, "Lots leave in 1.8 seconds")
                wait_js(page, pose, [0, -450], "Timer left by the same side")
                wait_js(lots_page, lots_pose, [source_width, 0], "Lots left by the same side")

                save_lots("hidden")
                wait_js(lots_page, visible, "false", "Lots Never Show has priority")
                button.click()
                wait_js(page, pose, [0, 0], "Timer shows even when lots are explicitly hidden")
                assert js(lots_page, visible) == "false"
                lots_view.load(QUrl(server.base_url + "/auction-lots-overlay?preview=1"))
                wait_js(lots_page, visible, "true", "Lots preview ignores saved hide")
                assert js(lots_page, lots_pose) == [0, 0]

                stream.auction_lots_follow_auction_tab.setChecked(False)
                assert lots_mode.findData("slide") == -1
                save_lots("always")
                assert not button.isHidden(), "Unbinding lots must preserve the linked timer"
                assert read_json(server, "/api/timer")["tab_motion"]["auction_widgets_visible"]
            finally:
                lots_view.close()
                lots_view.deleteLater()
        finally:
            view.close()
            view.deleteLater()
            wait_with_http_workers(100)
            window.close()
            server.stop()
            window.thread_pool.waitForDone(15000)
            app.processEvents()
    print("UI045_TIMER_MEDIA_REAL_CHROMIUM_IMAGE_VIDEO_MISSING_FALLBACK=PASS")
    print("R06_TIMER_BUTTON_SLIDE_REAL_CHROMIUM_FOUR_SIDES=PASS")
    print("R06_AUCTION_LOTS_AND_TIMER_SHARED_BUTTON_CHROMIUM=PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", action="store_true")
    parser.add_argument("--ui", action="store_true")
    parser.add_argument("--browser", action="store_true")
    flags = parser.parse_args()
    if flags.api:
        api_smoke()
    elif flags.ui:
        ui_smoke()
    elif flags.browser:
        browser_smoke()
    else:
        api_smoke()
        ui_smoke()
        browser_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
