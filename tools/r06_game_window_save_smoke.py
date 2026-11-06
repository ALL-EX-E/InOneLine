"""R06-011 independent Game Window Qt/SQLite/Twitch/API regression."""
from __future__ import annotations
import json, os, socket, sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM","windows")
from PySide6.QtWidgets import QApplication,QMessageBox
from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database
from streaming_manager.multichat import ChatMessage,MultichatState
from streaming_manager.views.stream import StreamTab
KEYS={"stream_format","overlay_frame_game_color"}

class Clock:
    def __init__(self): self.value=100.0
    def __call__(self): return self.value
    def advance(self,t): self.value+=t

def port():
    with socket.socket() as s:
        s.bind(("127.0.0.1",0))
        return s.getsockname()[1]

def data(api):
    with urlopen(api.base_url+"/api/data",timeout=5) as r: return json.load(r)

def save(stream,db,api):
    before=db.get_settings()
    with patch.object(db,"set_settings_bulk",wraps=db.set_settings_bulk) as writes:
        with patch.object(api,"configure_list_show") as configure:
            with patch.object(QMessageBox,"information") as notice:
                stream.main_save_buttons["game_window"].click()
            configure.assert_not_called()
        assert notice.call_count==1 and notice.call_args.args[1]=="Игровое окно"
        assert writes.call_count==1,writes.call_args_list
        result=writes.call_args.args[0]
    assert set(result)==KEYS,result
    after=db.get_settings()
    assert all(after.get(k)==v for k,v in result.items())
    assert {k for k in (set(before)|set(after)) if before.get(k)!=after.get(k)}<=KEYS
    return result

def main():
    app=QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        db=Database(Path(temp)/"game_save.db")
        db.set_settings_bulk({
            "stream_format":"16:9","overlay_frame_game_color":"#FFFFFF",
            "list_overlay_show_mode":"slide","list_slide_command":"!list",
            "list_slide_duration":"10","overlay_list_enabled":"1",
            "stream_info":"SAVED","stream_info_enabled":"1",
            "overlay_webcam_enabled":"1","combined_list_chat_layout":"split",
            "overlay_background_mode":"stretch","overlay_font_title_size":"30"
        })
        clock=Clock()
        chat=MultichatState(clock=clock,wall_clock=clock)
        api=LocalApiServer(db,port=port())
        api.set_multichat_state_provider(chat.snapshot)
        api.set_list_show_controller(chat.configure_list_show)
        api.configure_list_show("slide","!list",10)
        api.start()
        tab=None
        try:
            tab=StreamTab(db,api)
            tab.show()
            app.processEvents()
            assert chat.ingest(ChatMessage("twitch","ch","r06-011","viewer","!list"))
            clock.advance(2)
            timer=chat.snapshot()["list_show"]
            assert timer=={"remaining_ms":8000,"sequence":1},timer
            mode=tab.obs_show_modes["list"]
            mode.setCurrentIndex(mode.findData("hidden"))
            tab.list_slide_duration.setValue(35)
            tab.list_slide_command.setText("!draft")
            tab.info_field.setText("UNSAVED")
            tab.webcam_enabled.setChecked(False)
            tab.combined_list_chat_layout.setCurrentIndex(
                tab.combined_list_chat_layout.findData("replace"))
            tab.typography_controls["title"][1].setValue(61)
            old=db.get_settings()
            tab.format_combo.setCurrentIndex(tab.format_combo.findText("4:3"))
            tab._set_color_button(tab.frame_color_buttons["game"],"#23AABB")
            assert data(api)["game"]["format"]=="16:9"
            assert save(tab,db,api)=={
                "stream_format":"4:3","overlay_frame_game_color":"#23AABB"}
            assert all(db.get_setting(k)==v for k,v in old.items() if k not in KEYS)
            assert chat.snapshot()["list_show"]==timer
            out=data(api)
            assert out["game"]["format"]=="4:3"
            assert out["overlay"]["frame_colors"]["game"]=="#23AABB"
            assert out["visibility"]["list"]["show_mode"]=="slide"
            assert out["game"]["reviews"]=="SAVED"
            assert out["overlay"]["list_chat_layout"]=="split"
            print("R06_GAME_WINDOW_ISOLATED_SAVE_AND_TIMER_PASS",flush=True)
            tab.format_combo.setCurrentIndex(tab.format_combo.findText("16:9"))
            tab._set_color_button(tab.frame_color_buttons["game"],"#FFFFFF")
            assert save(tab,db,api)=={
                "stream_format":"16:9","overlay_frame_game_color":"#FFFFFF"}
            assert chat.snapshot()["list_show"]==timer
            assert data(api)["game"]["format"]=="16:9"
            tab.format_combo.setCurrentIndex(tab.format_combo.findText("4:3"))
            tab._set_color_button(tab.frame_color_buttons["game"],"#23AABB")
            save(tab,db,api)
            tab.refresh()
            assert tab.format_combo.currentText()=="4:3"
            assert tab.frame_color_buttons["game"].property("fontColor")=="#23AABB"
            assert tab.obs_show_modes["list"].currentData()=="slide"
            assert tab.info_field.text()=="SAVED"
            assert db.get_setting("overlay_font_title_size")=="30"
            clock.advance(1.25)
            assert chat.snapshot()["list_show"]=={"remaining_ms":6750,"sequence":1}
            clock.advance(7)
            assert chat.snapshot()["list_show"]["remaining_ms"]==0
            print("R06_GAME_WINDOW_REVERSE_RELOAD_TIMER_EXPIRY_PASS",flush=True)
        finally:
            if tab is not None:
                tab.close()
                app.processEvents()
            api.stop()
    print("R06_GAME_WINDOW_WINDOWS_QT_ALL_PASS",flush=True)

if __name__=="__main__":
    main()
