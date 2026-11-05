"""R06-010: Background Save writes exactly three keys without resetting List."""
from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "windows")

from PySide6.QtWidgets import QApplication, QMessageBox

from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database
from streaming_manager.media import (
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
    managed_media_directory,
)
from streaming_manager.multichat import ChatMessage, MultichatState
from streaming_manager.views.stream import StreamTab


class Clock:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def read_overlay(api: LocalApiServer) -> dict:
    with urlopen(api.base_url + "/api/data", timeout=5) as response:
        return json.load(response)


BACKGROUND_KEYS = {
    "overlay_background_media_id",
    "overlay_background_file",
    "overlay_background_mode",
}


def save_background(stream: StreamTab, db: Database, api: LocalApiServer) -> dict:
    before = db.get_settings()
    with patch.object(db, "set_settings_bulk", wraps=db.set_settings_bulk) as write:
        with patch.object(
            api, "configure_list_show", wraps=api.configure_list_show
        ) as controller:
            with patch.object(QMessageBox, "information") as notice:
                stream.main_save_buttons["background"].click()
            controller.assert_not_called()
        assert notice.call_count == 1, notice.call_args_list
        assert notice.call_args.args[1] == "Фон оверлея"
        assert write.call_count == 1, write.call_args_list
        committed = write.call_args.args[0]
    assert set(committed) == BACKGROUND_KEYS, committed
    after = db.get_settings()
    for key, value in committed.items():
        assert after[key] == value, (key, after.get(key), value)
    changed = {k for k in (set(before) | set(after))
               if before.get(k) != after.get(k)}
    assert changed <= BACKGROUND_KEYS, changed - BACKGROUND_KEYS
    return committed


def select_background(stream: StreamTab, asset_id: int | str) -> None:
    idx = stream.background_combo.findData(asset_id)
    assert idx >= 0, (asset_id, idx)
    stream.background_combo.setCurrentIndex(idx)
    assert stream.background_combo.currentData() == asset_id


def select_mode(stream: StreamTab, mode: str) -> None:
    idx = stream.background_mode.findData(mode)
    assert idx >= 0, (mode, idx)
    stream.background_mode.setCurrentIndex(idx)


def check_drafts(db: Database, api: LocalApiServer, timer: dict) -> None:
    overlay = read_overlay(api)
    assert overlay["visibility"]["list"]["show_mode"] == "slide"
    assert overlay["overlay"]["list_enabled"] is True
    assert overlay["overlay"]["list_slide_direction"] == "right"
    assert overlay["overlay"]["list_chat_layout"] == "split"
    assert overlay["game"]["reviews"] == "Saved information"
    assert overlay["overlay"]["info_position"] == "bottom_right"
    assert db.get_setting("list_slide_command") == "!list"
    assert db.get_setting("list_slide_duration") == "10"


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        db = Database(root / "background_save.db")
        backgrounds = managed_media_directory(root, MEDIA_CATEGORY_OVERLAY_BACKGROUNDS)
        backgrounds.mkdir(parents=True, exist_ok=True)
        (backgrounds / "managed-smoke.png").write_bytes(b"\x89PNG\r\n\x1a\nsmoke")
        managed = db.ensure_managed_media_asset(
            MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
            "managed-smoke.png", "managed-smoke.png",
        )
        external_path = root / "external-smoke.webp"
        external_path.write_bytes(b"RIFFsmokeWEBP")
        external = db.register_external_media_asset(
            MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, external_path
        )
        db.set_settings_bulk({
            "list_overlay_show_mode": "slide",
            "list_slide_command": "!list",
            "list_slide_duration": "10",
            "list_slide_direction": "right",
            "overlay_list_enabled": "1",
            "overlay_list_side": "auto",
            "combined_list_chat_layout": "split",
            "stream_info": "Saved information",
            "stream_info_enabled": "1",
            "overlay_info_position": "bottom_right",
            "overlay_webcam_enabled": "1",
            "overlay_webcam_position": "top_right",
            "stream_format": "16:9",
            "overlay_background_media_id": "",
            "overlay_background_file": "",
            "overlay_background_mode": "stretch",
        })
        clock = Clock()
        state = MultichatState(clock=clock, wall_clock=clock)
        api = LocalApiServer(db, port=free_port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.configure_list_show("slide", "!list", 10)
        api.start()
        stream = None
        try:
            stream = StreamTab(db, api)
            stream.resize(1130, 850)
            stream.show()
            app.processEvents()
            assert state.ingest(ChatMessage(
                "twitch", "ch", "background-cmd", "viewer", "!list",
            ))
            clock.advance(2.0)
            timer = state.snapshot()["list_show"]
            assert timer == {"remaining_ms": 8000, "sequence": 1}

            # A new library selection must not publish until Background Save.
            stream._select_imported_background("main", managed.id)
            assert db.get_setting("overlay_background_media_id") == ""
            assert read_overlay(api)["overlay"]["background"]["asset_id"] is None
            assert state.snapshot()["list_show"] == timer

            # Unsaved changes in other sections are deliberately left as drafts.
            list_mode = stream.obs_show_modes["list"]
            list_mode.setCurrentIndex(list_mode.findData("hidden"))
            stream.list_slide_duration.setValue(35)
            stream.list_slide_command.setText("!unsaved")
            stream.info_field.setText("DO NOT SAVE INFO")
            stream.webcam_enabled.setChecked(False)
            stream.format_combo.setCurrentIndex(
                stream.format_combo.findText("4:3")
            )
            stream.combined_list_chat_layout.setCurrentIndex(
                stream.combined_list_chat_layout.findData("replace")
            )
            assert list_mode.currentData() == "hidden"
            saved_others = db.get_settings()

            # Managed library copy: one asset, one mode, no other keys.
            select_background(stream, managed.id)
            select_mode(stream, "contain")
            committed = save_background(stream, db, api)
            assert committed == {
                "overlay_background_media_id": str(managed.id),
                "overlay_background_file": "managed-smoke.png",
                "overlay_background_mode": "contain",
            }, committed
            for key, value in saved_others.items():
                if key not in BACKGROUND_KEYS:
                    assert db.get_setting(key) == value, key
            assert state.snapshot()["list_show"] == timer
            check_drafts(db, api, timer)
            background = read_overlay(api)["overlay"]["background"]
            assert background["asset_id"] == managed.id
            assert background["mode"] == "contain"
            assert background["available"] is True
            assert background["status"] == "ready"
            assert background["url"] == f"/media/{managed.id}"
            print("R06_BACKGROUND_SAVE_MANAGED_ISOLATED_TIMER_PASS", flush=True)

            # External original: the legacy field never stores an absolute path.
            select_background(stream, external.id)
            select_mode(stream, "cover")
            committed = save_background(stream, db, api)
            assert committed == {
                "overlay_background_media_id": str(external.id),
                "overlay_background_file": "",
                "overlay_background_mode": "cover",
            }, committed
            assert str(external_path) not in str(committed)
            background = read_overlay(api)["overlay"]["background"]
            assert background["asset_id"] == external.id
            assert background["storage_mode"] == "external"
            assert background["url"] == f"/media/{external.id}"
            assert background["mode"] == "cover"
            assert state.snapshot()["list_show"] == timer
            print("R06_BACKGROUND_SAVE_EXTERNAL_NO_PATH_LEAK_PASS", flush=True)

            # Remove the user background; retain the selected display mode.
            select_background(stream, "")
            select_mode(stream, "center")
            committed = save_background(stream, db, api)
            assert committed == {
                "overlay_background_media_id": "",
                "overlay_background_file": "",
                "overlay_background_mode": "center",
            }, committed
            background = read_overlay(api)["overlay"]["background"]
            assert background["asset_id"] is None
            assert background["url"] == ""
            assert background["status"] == "none"
            assert background["mode"] == "center"
            assert state.snapshot()["list_show"] == timer
            print("R06_BACKGROUND_SAVE_CLEAR_NO_TIMER_RESET_PASS", flush=True)

            stream.refresh()
            assert stream.background_combo.currentData() == ""
            assert stream.background_mode.currentData() == "center"
            assert stream.obs_show_modes["list"].currentData() == "slide"
            assert stream.info_field.text() == "Saved information"
            assert stream.webcam_enabled.isChecked()
            assert stream.combined_list_chat_layout.currentData() == "split"

            clock.advance(1.25)
            assert state.snapshot()["list_show"] == {
                "remaining_ms": 6750, "sequence": 1,
            }
            clock.advance(7.0)
            assert state.snapshot()["list_show"]["remaining_ms"] == 0
            print("R06_BACKGROUND_SAVE_RELOAD_AND_EXPIRY_PASS", flush=True)
        finally:
            if stream is not None:
                stream.close()
                app.processEvents()
            api.stop()
    print("R06_BACKGROUND_SAVE_WINDOWS_QT_ALL_PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
