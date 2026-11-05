"""R06-009: Webcam Save writes only its three keys; shared Twitch timer is untouched."""
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
from streaming_manager.multichat import ChatMessage, MultichatState
from streaming_manager.views.stream import StreamTab


class Clock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
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


def save_webcam(stream: StreamTab, db: Database, api: LocalApiServer) -> dict:
    before = db.get_settings()
    with patch.object(db, "set_settings_bulk", wraps=db.set_settings_bulk) as write:
        with patch.object(
            api, "configure_list_show", wraps=api.configure_list_show
        ) as controller:
            with patch.object(QMessageBox, "information") as notice:
                stream.main_save_buttons["webcam"].click()
            controller.assert_not_called()
        assert notice.call_count == 1
        assert notice.call_args.args[1] == "Веб-камера"
        assert write.call_count == 1
        committed = write.call_args.args[0]
    keys = {
        "overlay_webcam_enabled",
        "overlay_webcam_position",
        "overlay_frame_webcam_color",
    }
    assert set(committed) == keys, committed
    after = db.get_settings()
    for key, value in committed.items():
        assert after[key] == value, (key, after[key], value)
    changes = {k for k in set(after) | set(before) if after.get(k) != before.get(k)}
    assert changes <= keys, changes - keys
    return committed


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as root:
        db = Database(Path(root) / "webcam_save.db")
        db.set_settings_bulk({
            "list_overlay_show_mode": "slide",
            "list_slide_command": "!list",
            "list_slide_duration": "10",
            "list_slide_direction": "right",
            "overlay_list_enabled": "1",
            "overlay_list_side": "auto",
            "overlay_webcam_enabled": "1",
            "overlay_webcam_position": "top_right",
            "overlay_frame_webcam_color": "#FFFFFF",
            "stream_info": "Existing information",
            "stream_info_enabled": "1",
            "overlay_info_position": "bottom_right",
            "combined_list_chat_layout": "split",
            "stream_format": "16:9",
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
            assert stream.webcam_enabled.isChecked()
            assert state.ingest(ChatMessage(
                "twitch", "channel", "webcam-cmd", "viewer", "!list"
            ))
            clock.advance(2.0)
            initial_timer = state.snapshot()["list_show"]
            assert initial_timer == {"remaining_ms": 8000, "sequence": 1}

            # Unconfirmed drafts from every other main overlay section.
            list_mode = stream.obs_show_modes["list"]
            list_mode.setCurrentIndex(list_mode.findData("hidden"))
            stream.list_slide_duration.setValue(35)
            stream.list_slide_command.setText("!unsaved")
            stream.info_field.setText("UNSAVED INFORMATION DRAFT")
            stream.info_position.setCurrentIndex(
                stream.info_position.findData("top_left")
            )
            stream.combined_list_chat_layout.setCurrentIndex(
                stream.combined_list_chat_layout.findData("replace")
            )
            stream.background_mode.setCurrentIndex(
                stream.background_mode.findData("contain")
            )
            stream.format_combo.setCurrentIndex(
                stream.format_combo.findText("4:3")
            )
            assert list_mode.currentData() == "hidden"
            before_other = db.get_settings()

            # Choose a new position and frame color while Webcam is visible;
            # then disable. Both should survive a disabled Save.
            stream.webcam_position.setCurrentIndex(
                stream.webcam_position.findData("bottom_left")
            )
            stream._set_color_button(
                stream.frame_color_buttons["webcam"], "#AABBCC"
            )
            stream.webcam_enabled.setChecked(False)
            app.processEvents()
            saved = save_webcam(stream, db, api)
            assert saved == {
                "overlay_webcam_enabled": "0",
                "overlay_webcam_position": "bottom_left",
                "overlay_frame_webcam_color": "#AABBCC",
            }, saved
            for key, value in before_other.items():
                if key not in saved:
                    assert db.get_setting(key) == value, key
            assert list_mode.currentData() == "hidden"
            assert state.snapshot()["list_show"] == initial_timer
            overlay = read_overlay(api)
            assert overlay["visibility"]["list"]["show_mode"] == "slide"
            assert overlay["overlay"]["list_enabled"] is True
            assert overlay["overlay"]["webcam_enabled"] is False
            assert overlay["overlay"]["webcam_position"] == "bottom_left"
            assert overlay["overlay"]["frame_colors"]["webcam"] == "#AABBCC"
            assert overlay["game"]["reviews"] == "Existing information"
            assert overlay["overlay"]["info_position"] == "bottom_right"
            assert overlay["overlay"]["list_slide_direction"] == "right"
            assert overlay["overlay"]["list_chat_layout"] == "split"
            assert state.snapshot()["list_show"]["remaining_ms"] == 8000
            print("R06_WEBCAM_SAVE_OFF_ONLY_THREE_KEYS_PASS", flush=True)

            # Only saved values, not other drafts, are reloaded.
            stream.refresh()
            assert not stream.webcam_enabled.isChecked()
            assert stream.webcam_position.currentData() == "bottom_left"
            assert (
                stream.frame_color_buttons["webcam"].property("fontColor") == "#AABBCC"
            )
            assert stream.obs_show_modes["list"].currentData() == "slide"
            assert stream.info_field.text() == "Existing information"
            stream.webcam_enabled.setChecked(True)
            saved = save_webcam(stream, db, api)
            assert saved == {
                "overlay_webcam_enabled": "1",
                "overlay_webcam_position": "bottom_left",
                "overlay_frame_webcam_color": "#AABBCC",
            }
            overlay = read_overlay(api)
            assert overlay["overlay"]["webcam_enabled"] is True
            assert overlay["overlay"]["webcam_position"] == "bottom_left"
            assert overlay["overlay"]["frame_colors"]["webcam"] == "#AABBCC"
            assert state.snapshot()["list_show"] == initial_timer
            clock.advance(1.25)
            assert state.snapshot()["list_show"] == {
                "remaining_ms": 6750, "sequence": 1,
            }
            clock.advance(7)
            assert state.snapshot()["list_show"]["remaining_ms"] == 0
            assert db.get_setting("list_overlay_show_mode") == "slide"
            print("R06_WEBCAM_SAVE_ON_POSITION_FRAME_TIMER_PASS", flush=True)
        finally:
            if stream is not None:
                stream.close()
                app.processEvents()
            api.stop()
    print("R06_WEBCAM_SAVE_WINDOWS_QT_ALL_PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
