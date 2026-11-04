"""D41 response-order regression in actual Qt Chromium (no Twitch credentials).

Hold two overlapping local OBS requests, return the second first, and check
that a late older state cannot restore prior text or deleted cards. Repeat
for the standalone chat and the same embedded renderer.
"""
from __future__ import annotations

import os
import socket
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "windows" if sys.platform == "win32" else "offscreen")
if sys.platform != "win32":
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")

from PySide6.QtCore import QUrl
from PySide6.QtTest import QTest
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from streaming_manager.api_server import LocalApiServer
from streaming_manager.chat_appearance import save_appearance
from streaming_manager.database import Database
from streaming_manager.multichat import MultichatState


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def evaluate(page, script):
    values = []
    page.runJavaScript(script, values.append)
    deadline = time.monotonic() + 8
    while not values and time.monotonic() < deadline:
        QTest.qWait(25)
    if not values:
        raise AssertionError("Chromium JS callback timed out")
    return values[0]


# The live renderer's 500ms interval calls the mocked fetch; promises are
# deliberately resolved out of order. Test runs inside a real Chromium page.
HARNESS = r"""
(() => {
  if (window.__iolResponseOrderQA) return;
  const originalFetch = window.fetch.bind(window);
  const pending = [];
  const root = document.getElementById("messages");
  window.__iolResponseOrderQA = {stage:"running", pass:false};
  window.fetch = (url, options) => {
    if (String(url) !== "/api/multichat") return originalFetch(url, options);
    return new Promise(resolve => pending.push(resolve));
  };
  const message = text => ({
    platform:"twitch", source_id:"qa", external_id:text,
    author:"QA", text, fragments:[], badges:[], color:"",
    received_at:1730000000
  });
  const state = text => ({
    messages:text ? [message(text)] : [], show_time:false,
    show_platform_icons:false, obs_enabled:{twitch:true},
    appearance:{twitch:{mode:"original"},
      common:{visibility:"always", background:"transparent"}}
  });
  const answer = text => ({ok:true, json: async () => state(text)});
  const hold = ms => new Promise(resolve => setTimeout(resolve, ms));
  const wait = async (predicate, label, timeout=5500) => {
    const start = Date.now();
    while (!predicate()) {
      if (Date.now()-start > timeout) throw new Error("Timeout: " + label);
      await hold(20);
    }
  };
  const visible = () => root?.textContent || "";
  const done = (pass, stage, error) => {
    window.__iolResponseOrderQA = {pass, stage, error:error || ""};
    window.fetch = originalFetch;
  };
  (async () => {
    await wait(() => pending.length >= 2, "two overlapping requests");
    pending[1](answer("NEWER_MESSAGE"));
    await wait(() => visible().includes("NEWER_MESSAGE"), "newer arrived");
    pending[0](answer("STALE_OLDER_MESSAGE"));
    await hold(110);
    if (!visible().includes("NEWER_MESSAGE") ||
        visible().includes("STALE_OLDER_MESSAGE"))
      throw new Error("Older response overwrote newer message");

    const failedPair = pending.length;
    await wait(() => pending.length >= failedPair + 2, "failed newer pair");
    pending[failedPair+1]({ok:false});
    pending[failedPair](answer("AFTER_FAILED_NEWER"));
    await wait(() => visible().includes("AFTER_FAILED_NEWER"),
               "older successful reply survives newer failure");

    // After deletion, an older HTTP state must not resurrect the card.
    const deletionPair = pending.length;
    await wait(() => pending.length >= deletionPair + 2, "deletion pair");
    pending[deletionPair+1](answer(""));
    await wait(() => root.children.length === 0, "deleted rows");
    pending[deletionPair](answer("DELETED_OLD_MESSAGE"));
    await hold(110);
    if (root.children.length !== 0)
      throw new Error("Late response resurrected deleted message");

    if (location.search.includes("embedded=1")) {
      const inflight = pending.length;
      await wait(() => pending.length >= inflight + 1, "parent refresh");
      if (typeof window.IOLRenderEmbeddedChatState !== "function")
        throw new Error("Embedded recovery hook missing");
      window.IOLRenderEmbeddedChatState(state("PARENT_NEW_STATE"));
      await wait(() => visible().includes("PARENT_NEW_STATE"),
                 "direct parent resync");
      pending[inflight](answer("PRE_PARENT_OLD_STATE"));
      await hold(110);
      if (!visible().includes("PARENT_NEW_STATE") ||
          visible().includes("PRE_PARENT_OLD_STATE"))
        throw new Error("Old child poll overwrote parent recovery");
    }
    done(true, "passed");
  })().catch(error => done(false, "failed", String(error)));
})();
""";


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
        db = Database(Path(temporary) / "chat_poll_order.db")
        save_appearance(db, {}, {"visibility":"always"})
        chat = MultichatState()
        api = LocalApiServer(db, port=free_port())
        api.set_multichat_state_provider(chat.snapshot)
        api.start()
        views = []
        try:
            for route in ("/multichat-overlay", "/multichat-overlay?embedded=1"):
                view = QWebEngineView()
                view.resize(420, 360)
                completed = []
                view.loadFinished.connect(completed.append)
                view.show()
                view.load(QUrl(api.base_url + route))
                views.append(view)
                deadline = time.monotonic() + 16
                while not completed and time.monotonic() < deadline:
                    QTest.qWait(40)
                assert completed == [True], (route, completed)
                assert evaluate(view.page(), "Boolean(document.getElementById('messages'))")
                evaluate(view.page(), HARNESS + " true")
                deadline = time.monotonic() + 18
                outcome = None
                while time.monotonic() < deadline:
                    outcome = evaluate(view.page(), "window.__iolResponseOrderQA")
                    if outcome and outcome.get("stage") != "running":
                        break
                    QTest.qWait(60)
                assert outcome and outcome.get("pass"), (route, outcome)
                print("D41_ORDER_PASS", route, outcome, flush=True)
        finally:
            for view in views:
                view.close()
                view.deleteLater()
            app.processEvents()
            api.stop()
    print("D41_ORDER_PASS: standalone and embedded response order", flush=True)


if __name__ == "__main__":
    main()
