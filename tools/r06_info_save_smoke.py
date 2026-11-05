"""R06-007: Information Save must not commit unrelated List drafts or reset timer."""
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

from PySide6.QtGui import QFont
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
        return sock.getsockname()[1]


def api_data(api: LocalApiServer) -> dict:
    with urlopen(api.base_url + "/api/data", timeout=5) as response:
        return json.load(response)


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "r06_info_save.db")
        db.set_settings_bulk({
            "list_overlay_show_mode": "slide",
            "list_slide_command": "!list",
            "list_slide_duration": "10",
            "list_slide_direction": "right",
            "overlay_list_enabled": "1",
            "overlay_list_side": "right",
            "combined_list_chat_layout": "split",
            "overlay_webcam_enabled": "1",
            "stream_info": "Before information Save",
            "stream_info_enabled": "0",
            "overlay_info_position": "bottom_right",
            "overlay_frame_info_color": "#112233",
            "overlay_font_info_family": "Segoe UI",
            "overlay_font_info_size": "19",
            "overlay_font_info_color": "#445566",
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
            stream.resize(1100, 850)
            stream.show()
            app.processEvents()
            assert db.get_setting("list_overlay_show_mode") == "slide"
            assert stream.obs_show_modes["list"].currentData() == "slide"

            # Exactly one authenticated Twitch command starts the shared timer.
            assert state.ingest(ChatMessage(
                "twitch", "channel", "cmd-r06-save", "viewer", "!list"
            ))
            clock.advance(2)
            before_timer = state.snapshot()["list_show"]
            assert before_timer["remaining_ms"] == 8000, before_timer
            assert before_timer["sequence"] == 1

            # Make several unrelated unsaved edits in the actual Qt controls.
            list_mode = stream.obs_show_modes["list"]
            list_mode.setCurrentIndex(list_mode.findData("hidden"))
            assert list_mode.currentData() == "hidden"
            stream.list_slide_command.setText("!not-saved")
            stream.list_slide_duration.setValue(35)
            stream.overlay_list_side.setCurrentIndex(
                stream.overlay_list_side.findData("left")
            )
            stream.webcam_enabled.setChecked(False)
            stream.combined_list_chat_layout.setCurrentIndex(
                stream.combined_list_chat_layout.findData("replace")
            )
            stream._set_color_button(
                stream.frame_color_buttons["list"], "#ABCDEF"
            )

            # Info settings alone are the confirmed scope of this Save.
            stream.info_enabled.setChecked(True)
            stream.info_field.setText("Information only, published now")
            stream.info_position.setCurrentIndex(
                stream.info_position.findData("top_left")
            )
            stream._set_color_button(
                stream.frame_color_buttons["info"], "#ACBDCE"
            )
            info_font, info_size, info_color = stream.typography_controls["info"]
            info_font.setCurrentFont(QFont("Consolas"))
            info_size.setValue(26)
            stream._set_color_button(info_color, "#AABBCC")
            expected = {
                "stream_info": "Information only, published now",
                "stream_info_enabled": "1",
                "overlay_info_position": "top_left",
                "overlay_frame_info_color": "#ACBDCE",
                "overlay_font_info_family": info_font.currentFont().family(),
                "overlay_font_info_size": "26",
                "overlay_font_info_color": "#AABBCC",
            }
            before = db.get_settings()
            for key, value in expected.items():
                assert before.get(key) != value, (key, before.get(key), value)

            # Real Info button click, not a direct call to the new method.
            with patch.object(QMessageBox, "information") as notice:
                with patch.object(
                    api, "configure_list_show", wraps=api.configure_list_show
                ) as timer_config:
                    stream.main_save_buttons["info"].click()
                    timer_config.assert_not_called()
                assert notice.call_count == 1
                assert notice.call_args.args[1] == "Информационный блок"

            after = db.get_settings()
            changes = {
                key for key in set(before) | set(after)
                if before.get(key) != after.get(key)
            }
            assert changes == set(expected), (changes, expected)
            for key, value in expected.items():
                assert after[key] == value, (key, after[key], value)
            assert after["list_overlay_show_mode"] == "slide"
            assert after["list_slide_command"] == "!list"
            assert after["list_slide_duration"] == "10"
            assert after["combined_list_chat_layout"] == "split"
            assert after["overlay_webcam_enabled"] == "1"
            assert stream.obs_show_modes["list"].currentData() == "hidden"

            # Info reaches OBS API now, but the real timer is not reset or
            # restarted until its normal expiry (no animation triggered).
            payload = api_data(api)
            assert payload["game"]["reviews"] == expected["stream_info"], payload["game"]
            assert payload["overlay"]["info_position"] == "top_left"
            assert payload["visibility"]["list"]["show_mode"] == "slide"
            assert payload["overlay"]["list_enabled"] is True
            timer_after = state.snapshot()["list_show"]
            assert timer_after == before_timer, (before_timer, timer_after)
            clock.advance(1.25)
            assert state.snapshot()["list_show"] == {
                "remaining_ms": 6750, "sequence": 1,
            }
            clock.advance(7)
            assert state.snapshot()["list_show"]["remaining_ms"] == 0
            assert db.get_setting("list_overlay_show_mode") == "slide"
            print("R06_INFO_SAVE_ONLY_KEYS_PASS", sorted(changes), flush=True)
            print("R06_INFO_SAVE_TIMER_AND_UNSAVED_LIST_PASS", flush=True)
        finally:
            if stream is not None:
                stream.close()
                app.processEvents()
            api.stop()
    print("R06_INFO_SAVE_WINDOWS_QT_ALL_PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
