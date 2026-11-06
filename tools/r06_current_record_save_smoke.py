"""R06-012: native Windows Qt, SQLite, Twitch timer and OBS HTTP current-title Save."""
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
from streaming_manager.constants import STATUS_PLAYING, STATUS_NOT_PLAYED
from streaming_manager.database import Database, Game
from streaming_manager.multichat import ChatMessage, MultichatState
from streaming_manager.views.stream import StreamTab

KEYS = {
    "stream_current_game_id",
    "overlay_font_title_family",
    "overlay_font_title_size",
    "overlay_font_title_color",
}


class Clock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def api_data(api):
    with urlopen(api.base_url + "/api/data", timeout=5) as response:
        return json.load(response)


def save_title(tab, db, api):
    before = db.get_settings()
    with patch.object(db, "set_settings_bulk", wraps=db.set_settings_bulk) as write:
        with patch.object(api, "configure_list_show") as configure:
            with patch.object(QMessageBox, "information") as notice:
                tab.main_save_buttons["current_game"].click()
            configure.assert_not_called()
    assert write.call_count == 1, write.call_args_list
    assert notice.call_count == 1
    assert notice.call_args.args[1] == "Заголовок над игровым окном"
    saved = write.call_args.args[0]
    assert set(saved) == KEYS, saved
    after = db.get_settings()
    assert {key for key in (set(before) | set(after))
            if before.get(key) != after.get(key)} <= KEYS
    assert all(after.get(key) == value for key, value in saved.items())
    return saved


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "current_record_save.db")
        auto_id = db.add_game(Game(None, "Автоматическая запись R06", None,
                                   status=STATUS_PLAYING))
        manual_id = db.add_game(Game(None, "Ручная запись R06", None,
                                     status=STATUS_NOT_PLAYED))
        db.set_settings_bulk({
            "stream_current_game_id": "",
            "overlay_font_title_family": "Segoe UI",
            "overlay_font_title_size": "30",
            "overlay_font_title_color": "#FFFFFF",
            "stream_format": "16:9",
            "stream_info": "SAVED",
            "overlay_webcam_enabled": "1",
            "overlay_background_mode": "stretch",
            "combined_list_chat_layout": "split",
            "list_overlay_show_mode": "slide",
            "list_slide_command": "!list",
            "list_slide_duration": "10",
            "overlay_list_enabled": "1",
        })
        clock = Clock()
        chat = MultichatState(clock=clock, wall_clock=clock)
        api = LocalApiServer(db, port=free_port())
        api.set_multichat_state_provider(chat.snapshot)
        api.set_list_show_controller(chat.configure_list_show)
        api.configure_list_show("slide", "!list", 10)
        api.start()
        tab = None
        restarted = None
        try:
            tab = StreamTab(db, api)
            tab.show()
            app.processEvents()
            assert tab.main_settings_form.labelForField(tab.game_combo).text() == "Запись в заголовке:"
            assert tab.typography_row_widgets["title"][0].text() == "Заголовок над игровым окном"
            assert api_data(api)["game"]["id"] == auto_id
            assert chat.ingest(ChatMessage("twitch", "ch", "r06-012", "viewer", "!list"))
            clock.advance(2)
            active = chat.snapshot()["list_show"]
            assert active == {"remaining_ms": 8000, "sequence": 1}, active

            # Leave unsaved changes in every neighboring section.
            mode = tab.obs_show_modes["list"]
            mode.setCurrentIndex(mode.findData("hidden"))
            tab.list_slide_duration.setValue(35)
            tab.list_slide_command.setText("!draft")
            tab.info_field.setText("UNSAVED")
            tab.webcam_enabled.setChecked(False)
            tab.format_combo.setCurrentIndex(tab.format_combo.findText("4:3"))
            tab.combined_list_chat_layout.setCurrentIndex(
                tab.combined_list_chat_layout.findData("replace"))
            before = db.get_settings()

            tab.game_combo.setCurrentIndex(tab.game_combo.findData(str(manual_id)))
            font, size, color = tab.typography_controls["title"]
            font.setCurrentFont(QFont("Arial"))
            size.setValue(43)
            tab._set_color_button(color, "#23AABB")
            assert api_data(api)["game"]["id"] == auto_id
            values = save_title(tab, db, api)
            assert values == {
                "stream_current_game_id": str(manual_id),
                "overlay_font_title_family": font.currentFont().family(),
                "overlay_font_title_size": "43",
                "overlay_font_title_color": "#23AABB",
            }, values
            assert all(db.get_setting(key) == value for key, value in before.items()
                       if key not in KEYS)
            assert chat.snapshot()["list_show"] == active
            payload = api_data(api)
            assert payload["game"]["id"] == manual_id
            assert payload["game"]["name"] == "Ручная запись R06"
            assert payload["overlay"]["typography"]["title"]["size"] == "43"
            assert payload["overlay"]["typography"]["title"]["color"] == "#23AABB"
            assert payload["visibility"]["list"]["show_mode"] == "slide"
            assert payload["game"]["reviews"] == "SAVED"
            assert payload["game"]["format"] == "16:9"
            assert payload["overlay"]["list_chat_layout"] == "split"
            print("R06_CURRENT_RECORD_ISOLATION_AND_OBS_HTTP_PASS", flush=True)

            # Empty ID is the existing automatic first-PLAYING fallback.
            tab.game_combo.setCurrentIndex(tab.game_combo.findData(""))
            values = save_title(tab, db, api)
            assert values["stream_current_game_id"] == ""
            assert api_data(api)["game"]["id"] == auto_id
            assert chat.snapshot()["list_show"] == active
            db.update_game(auto_id, {"status": STATUS_NOT_PLAYED})
            assert api_data(api)["game"]["id"] is None
            assert len(db.list_games()) == 2  # No phantom record is created.
            print("R06_CURRENT_RECORD_AUTOMATIC_AND_EMPTY_PASS", flush=True)

            # Persistence across a newly constructed UI using the same SQLite DB.
            tab.game_combo.setCurrentIndex(tab.game_combo.findData(str(manual_id)))
            save_title(tab, db, api)
            tab.close()
            tab = None
            app.processEvents()
            restarted = StreamTab(db, api)
            restarted.show()
            app.processEvents()
            assert restarted.game_combo.currentData() == str(manual_id)
            loaded_font, loaded_size, loaded_color = restarted.typography_controls["title"]
            assert loaded_font.currentFont().family() == values["overlay_font_title_family"]
            assert loaded_size.value() == 43
            assert loaded_color.property("fontColor") == "#23AABB"
            clock.advance(1.25)
            assert chat.snapshot()["list_show"] == {"remaining_ms": 6750, "sequence": 1}
            clock.advance(7)
            assert chat.snapshot()["list_show"]["remaining_ms"] == 0
            print("R06_CURRENT_RECORD_REOPEN_AND_TIMER_EXPIRY_PASS", flush=True)
        finally:
            if restarted is not None:
                restarted.close()
                app.processEvents()
            if tab is not None:
                tab.close()
                app.processEvents()
            api.stop()
    print("R06_CURRENT_RECORD_NATIVE_WINDOWS_ALL_PASS", flush=True)


if __name__ == "__main__":
    main()
