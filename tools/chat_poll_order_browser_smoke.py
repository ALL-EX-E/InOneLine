"""D41: real Chromium proof that late Twitch OBS poll responses cannot roll back state.

No Twitch credentials, production animation changes or provider network traffic.
"""
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
from PySide6.QtTest import QTest
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database
from streaming_manager.multichat import MultichatState


INJECT_FETCH = r"""
(() => {
  const original = window.fetch.bind(window);
  const requests = [];
  window.__chatPollQA = {requests};
  window.fetch = function(resource, options) {
    if (String(resource) !== "/api/multichat") return original(resource, options);
    return new Promise((resolve, reject) => {
      requests.push({
        succeed(snapshot) {
          resolve({ok: true, json: async () => snapshot});
        },
        fail() {reject(new Error("simulated network failure"));}
      });
    });
  };
})();
"""

DOM = """JSON.stringify((() => ({
  ready: Boolean(window.__chatPollQA && document.getElementById('messages')),
  requests: window.__chatPollQA?.requests.length ?? -1,
  messages: [...(document.getElementById('messages')?.children ?? [])]
    .map(n => n.textContent),
  shellHidden: document.getElementById('shell')?.classList.contains('hidden')
}))())"""


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def evaluate(page, script: str):
    result = []
    page.runJavaScript(script, result.append)
    end = time.monotonic() + 8
    while not result and time.monotonic() < end:
        QTest.qWait(20)
    if not result:
        raise AssertionError("Chromium JavaScript callback timeout")
    return json.loads(result[0]) if isinstance(result[0], str) and script.startswith("JSON.stringify") else result[0]


def until(page, check, description, timeout=12):
    end = time.monotonic() + timeout
    latest = None
    while time.monotonic() < end:
        latest = evaluate(page, DOM)
        if check(latest):
            return latest
        QTest.qWait(60)
    raise AssertionError(f"{description}: {latest!r}")


def snapshot(messages):
    return {
        "appearance": {
            "twitch": {"mode": "original"},
            "common": {"visibility": "always", "background": "transparent"},
        },
        "obs_enabled": {"twitch": True},
        "show_time": False,
        "show_platform_icons": False,
        "messages": [{"platform": "twitch", "author": "QA",
                      "external_id": f"qa-{message}", "text": message}
                     for message in messages],
    }


def reply(page, index, messages):
    payload = json.dumps(snapshot(messages), ensure_ascii=False)
    assert evaluate(
        page, f"window.__chatPollQA.requests[{index}].succeed({payload}); true;"
    ) is True


def fail(page, index):
    assert evaluate(
        page, f"window.__chatPollQA.requests[{index}].fail(); true;"
    ) is True


def verify_page(page, *, embedded: bool):
    until(page, lambda s: s["ready"] and s["requests"] >= 2,
          "two overlapped mock polls")
    # Response #2 finishes before #1. The late stale #1 must not restore
    # previously deleted messages or replace the newer text.
    reply(page, 1, ["CURRENT"])
    until(page, lambda s: s["messages"] and "CURRENT" in s["messages"][0],
          "newer successful response")
    reply(page, 0, ["STALE"])
    QTest.qWait(120)
    state = evaluate(page, DOM)
    assert len(state["messages"]) == 1 and "CURRENT" in state["messages"][0], state

    until(page, lambda s: s["requests"] >= 4, "next two polls")
    reply(page, 3, [])
    until(page, lambda s: s["messages"] == [], "newer response deletes messages")
    reply(page, 2, ["STALE-RESTORE"])
    QTest.qWait(120)
    state = evaluate(page, DOM)
    assert state["messages"] == [], ("late deletion rollback", state)

    # A failed newer request does NOT prevent an older successful response
    # from updating the UI; only already applied newer data wins.
    until(page, lambda s: s["requests"] >= 6, "retry pair")
    fail(page, 5)
    reply(page, 4, ["RECOVERED"])
    until(page, lambda s: s["messages"] and "RECOVERED" in s["messages"][0],
          "older success still works when newer request failed")

    if embedded:
        until(page, lambda s: s["requests"] >= 7, "parent resync in flight")
        direct = json.dumps(snapshot(["PARENT-NEW"]), ensure_ascii=False)
        assert evaluate(
            page, f"window.IOLRenderEmbeddedChatState({direct}); true;"
        ) is True
        until(page, lambda s: s["messages"] and "PARENT-NEW" in s["messages"][0],
              "direct parent resync")
        reply(page, 6, ["OLDER-THAN-PARENT"])
        QTest.qWait(120)
        state = evaluate(page, DOM)
        assert state["messages"] and "PARENT-NEW" in state["messages"][0], state

    print("D41_POLL_ORDER_PASS", "embedded" if embedded else "standalone", flush=True)


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as root:
        db = Database(Path(root) / "chat_order.db")
        api = LocalApiServer(db, port=free_port())
        state = MultichatState()
        api.set_multichat_state_provider(state.snapshot)
        api.start()
        try:
            for embedded in (False, True):
                view = QWebEngineView()
                view.resize(480, 520)
                script = QWebEngineScript()
                script.setName("qa-disordered-chat-fetch")
                script.setInjectionPoint(QWebEngineScript.DocumentCreation)
                script.setWorldId(QWebEngineScript.MainWorld)
                script.setRunsOnSubFrames(True)
                script.setSourceCode(INJECT_FETCH)
                view.page().scripts().insert(script)
                try:
                    view.show()
                    route = "/multichat-overlay?embedded=1" if embedded else "/multichat-overlay"
                    view.load(QUrl(api.base_url + route))
                    until(view.page(), lambda s: s["ready"], "standalone chat document")
                    verify_page(view.page(), embedded=embedded)
                finally:
                    view.close()
                    view.deleteLater()
                    app.processEvents()
        finally:
            api.stop()


if __name__ == "__main__":
    main()
