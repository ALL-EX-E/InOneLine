"""R06-011: native Chromium verifies Game Window frame, cutout, color."""
from __future__ import annotations
import json
import os
import socket
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "windows")
if sys.platform != "win32":
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from tools.qt_browser_test_wait import wait_with_http_workers
from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database
from streaming_manager.multichat import MultichatState

JS = '''JSON.stringify((() => {
 const frame=document.getElementById("game-frame");
 const hole=document.getElementById("game-cutout");
 if (!frame || !hole || !frame.offsetHeight) return {ready:false};
 const css=getComputedStyle(frame);
 return {
   ready:true,
   width:frame.offsetWidth,height:frame.offsetHeight,
   ratio:frame.offsetWidth/frame.offsetHeight,
   cutWidth:Number(hole.getAttribute("width")),
   cutHeight:Number(hole.getAttribute("height")),
   cutX:Number(hole.getAttribute("x")),
   cutY:Number(hole.getAttribute("y")),
   color:css.borderTopColor,opacity:css.opacity,
   transition:css.transitionDuration
 };
})())'''


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        return sock.getsockname()[1]


def measure(page):
    replies=[]
    page.runJavaScript(JS,replies.append)
    end=time.monotonic()+8
    while not replies and time.monotonic()<end:
        wait_with_http_workers(25)
    if not replies:
        raise AssertionError("R06 Game Window Chromium JS timeout")
    return json.loads(replies[0]) if isinstance(replies[0],str) else replies[0]


def until(page, ratio, rgb, label):
    end=time.monotonic()+35
    last=None
    while time.monotonic()<end:
        last=measure(page)
        if last and last.get("ready") and abs(last["ratio"]-ratio)<0.025 and rgb in last["color"]:
            assert abs(last["cutWidth"]-(last["width"]-6))<=1,last
            assert abs(last["cutHeight"]-(last["height"]-6))<=1,last
            assert last["cutX"]>0 and last["cutY"]>0,last
            assert last["opacity"]=="1",last
            assert all(float(v.strip().rstrip("s"))==0
                       for v in last["transition"].split(",")),last
            print("R06_GAME_WINDOW_BROWSER_PASS",label,last,flush=True)
            return
        wait_with_http_workers(100)
    raise AssertionError(f"R06 {label} timeout: {last!r}")


def main():
    app=QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db=Database(Path(tmp)/"game_frame_browser.db")
        db.set_settings_bulk({
            "stream_format":"16:9",
            "overlay_frame_game_color":"#FFFFFF",
            "list_overlay_show_mode":"hidden",
        })
        state=MultichatState()
        api=LocalApiServer(db,port=port())
        api.set_multichat_state_provider(state.snapshot)
        api.set_list_show_controller(state.configure_list_show)
        api.start()
        view=QWebEngineView()
        try:
            view.resize(1280,720)
            view.show()
            view.load(QUrl(api.base_url+"/overlay"))
            until(view.page(),16/9,"255, 255, 255","16:9 initial")
            db.set_settings_bulk({
                "stream_format":"4:3",
                "overlay_frame_game_color":"#23AABB",
            })
            until(view.page(),4/3,"35, 170, 187","4:3 changed")
            db.set_settings_bulk({
                "stream_format":"16:9",
                "overlay_frame_game_color":"#FFFFFF",
            })
            until(view.page(),16/9,"255, 255, 255","16:9 restored")
            print("R06_GAME_WINDOW_CHROMIUM_ALL_PASS",flush=True)
        finally:
            view.close()
            api.stop()


if __name__=="__main__":
    main()
