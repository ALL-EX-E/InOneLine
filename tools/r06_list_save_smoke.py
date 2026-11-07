"""R06-008: List Save is scoped; timer keeps running in slide and resets on exit."""
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
from streaming_manager.obs_visibility import WIDGETS
from streaming_manager.views.stream import StreamTab


class Clock:
    def __init__(self):
        self.t = 200.0

    def __call__(self):
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def get_data(api: LocalApiServer) -> dict:
    with urlopen(api.base_url + "/api/data", timeout=5) as response:
        return json.load(response)


def set_mode(stream: StreamTab, value: str) -> None:
    combo = stream.obs_show_modes["list"]
    index = combo.findData(value)
    assert index >= 0, value
    combo.setCurrentIndex(index)
    assert combo.currentData() == value


def save_list(stream: StreamTab, db: Database, api: LocalApiServer) -> dict:
    button = stream.main_save_buttons["list"]
    before = db.get_settings()
    with patch.object(db, "set_settings_bulk", wraps=db.set_settings_bulk) as write:
        with patch.object(
            api, "configure_list_show", wraps=api.configure_list_show
        ) as timer:
            with patch.object(QMessageBox, "information") as notice:
                button.click()
            assert notice.call_count == 1, notice.call_args_list
            assert notice.call_args.args[1] == "Список"
            assert timer.call_count == 1, timer.call_args_list
        assert write.call_count == 1, write.call_args_list
        written = write.call_args.args[0]
    expected_keys = {
        WIDGETS["list"].key,
        "list_slide_direction", "list_slide_duration",
        "list_slide_animation_seconds", "list_slide_command",
        "overlay_list_enabled", "overlay_frame_list_color",
    }
    expected_keys.update({
        f"overlay_font_{key}_{part}"
        for key in ("top1", "top2", "top3", "list")
        for part in ("family", "size", "color")
    })
    assert len(expected_keys) == 19
    assert set(written) == expected_keys, set(written) ^ expected_keys
    assert timer.call_args.args == (
        written[WIDGETS["list"].key],
        written["list_slide_command"],
        int(written["list_slide_duration"]),
    ), timer.call_args
    after = db.get_settings()
    for key, value in written.items():
        assert after.get(key) == value, (key, after.get(key), value)
    changes = {
        key for key in (set(before) | set(after))
        if before.get(key) != after.get(key)
    }
    assert changes <= expected_keys, (changes - expected_keys)
    assert after["overlay_list_enabled"] == (
        "0" if after[WIDGETS["list"].key] == "hidden" else "1"
    )
    return written


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "list_save.db")
        db.set_settings_bulk({
            WIDGETS["list"].key: "slide",
            "list_slide_direction": "right",
            "list_slide_duration": "10",
            "list_slide_animation_seconds": "0.65",
            "list_slide_command": "!list",
            "overlay_list_enabled": "1",
            "overlay_list_side": "auto",
            "overlay_frame_list_color": "#FFFFFF",
            "stream_info": "Original unsaved draft must stay absent",
            "stream_info_enabled": "1",
            "overlay_info_position": "bottom_right",
            "overlay_frame_info_color": "#123456",
            "overlay_webcam_enabled": "1",
            "overlay_webcam_position": "top_right",
            "combined_list_chat_layout": "split",
        })
        clock = Clock()
        state = MultichatState(clock=clock, wall_clock=clock)
        api = LocalApiServer(db, port=port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.configure_list_show("slide", "!list", 10)
        api.start()
        stream = None
        try:
            stream = StreamTab(db, api)
            stream.resize(1120, 880)
            stream.show()
            app.processEvents()
            assert stream.obs_show_modes["list"].currentData() == "slide"
            assert state.ingest(ChatMessage(
                "twitch", "ch", "r06-cmd-1", "viewer", "!list"
            ))
            clock.advance(2)
            before_timer = state.snapshot()["list_show"]
            assert before_timer == {"remaining_ms": 8000, "sequence": 1}

            # Unconfirmed settings in other sections must not be written.
            stream.info_field.setText("DO NOT PUBLISH THIS DRAFT")
            stream.info_position.setCurrentIndex(
                stream.info_position.findData("top_left")
            )
            stream.webcam_enabled.setChecked(False)
            stream.combined_list_chat_layout.setCurrentIndex(
                stream.combined_list_chat_layout.findData("replace")
            )
            stream.background_mode.setCurrentIndex(
                stream.background_mode.findData("contain")
            )
            stream.game_combo.setCurrentIndex(0)
            baseline_other = {
                key: db.get_setting(key)
                for key in (
                    "stream_info", "stream_info_enabled", "overlay_info_position",
                    "overlay_frame_info_color", "overlay_webcam_enabled",
                    "overlay_webcam_position", "combined_list_chat_layout",
                    "overlay_list_side",
                    "overlay_background_mode",
                )
            }

            stream.list_slide_direction.setCurrentIndex(
                stream.list_slide_direction.findData("left")
            )
            stream.list_slide_animation_seconds.setValue(1.25)
            stream.overlay_list_side.setCurrentIndex(
                stream.overlay_list_side.findData("left")
            )
            stream._set_color_button(stream.frame_color_buttons["list"], "#ABCDEF")
            stream.typography_controls["top1"][1].setValue(28)
            stream._set_color_button(
                stream.typography_controls["list"][2], "#12ABCD"
            )
            written = save_list(stream, db, api)
            assert written["list_slide_direction"] == "left"
            assert written["list_slide_animation_seconds"] == "1.25"
            assert "overlay_list_side" not in written
            assert written["overlay_frame_list_color"] == "#ABCDEF"
            assert written["overlay_font_top1_size"] == "28"
            assert written["overlay_font_list_color"] == "#12ABCD"
            for key, value in baseline_other.items():
                assert db.get_setting(key) == value, key

            # The real runtime timer keeps its original deadline and sequence.
            assert state.snapshot()["list_show"] == before_timer
            clock.advance(1.5)
            assert state.snapshot()["list_show"] == {
                "remaining_ms": 6500, "sequence": 1,
            }
            payload = get_data(api)
            assert payload["visibility"]["list"]["show_mode"] == "slide"
            assert payload["overlay"]["list_slide_direction"] == "left"
            assert payload["overlay"]["list_slide_animation_seconds"] == "1.25"
            assert payload["overlay"]["list_slide_duration"] == "10"
            assert payload["overlay"]["list_side"] == "auto"
            assert payload["overlay"]["info_position"] == "bottom_right"
            assert payload["game"]["reviews"] == baseline_other["stream_info"]
            print("R06_LIST_SAVE_SLIDE_TIMER_AND_DRAFTS_PASS", flush=True)

            set_mode(stream, "hidden")
            save_list(stream, db, api)
            assert state.snapshot()["list_show"]["remaining_ms"] == 0
            assert get_data(api)["visibility"]["list"]["show_mode"] == "hidden"
            assert get_data(api)["overlay"]["list_enabled"] is False
            assert db.get_setting("list_overlay_show_mode") == "hidden"
            print("R06_LIST_SAVE_HIDDEN_RESET_PASS", flush=True)

            set_mode(stream, "slide")
            save_list(stream, db, api)
            assert state.snapshot()["list_show"]["remaining_ms"] == 0
            assert state.ingest(ChatMessage(
                "twitch", "ch", "r06-cmd-2", "viewer", "!list"
            ))
            clock.advance(2.5)
            assert state.snapshot()["list_show"] == {
                "remaining_ms": 7500, "sequence": 2,
            }
            set_mode(stream, "always")
            save_list(stream, db, api)
            assert state.snapshot()["list_show"]["remaining_ms"] == 0
            assert get_data(api)["visibility"]["list"]["show_mode"] == "always"
            assert get_data(api)["overlay"]["list_enabled"] is True
            set_mode(stream, "slide")
            save_list(stream, db, api)
            assert state.snapshot()["list_show"]["remaining_ms"] == 0
            assert state.snapshot()["list_show"]["sequence"] == 2
            clock.advance(1)
            assert state.snapshot()["list_show"]["remaining_ms"] == 0
            assert state.ingest(ChatMessage(
                "twitch", "ch", "r06-cmd-3", "viewer", "!list"
            ))
            assert state.snapshot()["list_show"] == {
                "remaining_ms": 10000, "sequence": 3,
            }
            print("R06_LIST_SAVE_ALWAYS_RESET_AND_NEW_COMMAND_PASS", flush=True)
        finally:
            if stream is not None:
                stream.close()
                app.processEvents()
            api.stop()
    print("R06_LIST_SAVE_WINDOWS_QT_ALL_PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
