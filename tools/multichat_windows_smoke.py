"""D41-01 Windows/Qt/API integration smoke (no real platform credentials).

Run with QT_QPA_PLATFORM=offscreen in the existing regression workflow.
"""
from __future__ import annotations

import json
import socket
import tempfile
import unittest
import urllib.request
from pathlib import Path

from PySide6.QtWidgets import QApplication, QAbstractSpinBox, QBoxLayout, QPushButton

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.multichat import ChatMessage, MultichatState
from streaming_manager.views.multichat import MultichatTab


def unused_local_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class MultichatWindowsSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_existing_http_server_and_operator_view(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            paths = AppPaths.from_root(Path(tmp))
            paths.ensure_runtime_dirs()
            db = Database(paths.database_path)
            state = MultichatState()
            api = LocalApiServer(db, "127.0.0.1", unused_local_port())
            api.set_multichat_state_provider(state.snapshot)
            api.start()
            tab = None
            try:
                tab = MultichatTab(db, state, api)
                tab.resize(520, 360)
                tab.show()
                self.app.processEvents()
                self.assertEqual(tab.columns.direction(), QBoxLayout.TopToBottom)
                self.assertTrue(tab.feed.isVisible())

                # The already shared P06 control replaces broken native
                # Windows spin arrows without changing limit validation.
                self.assertEqual(tab.limit.buttonSymbols(), QAbstractSpinBox.NoButtons)
                limit_wrapper = tab.limit.parentWidget()
                buttons = {button.text(): button for button in limit_wrapper.findChildren(QPushButton)}
                self.assertEqual(set(buttons), {"▲", "▼"})
                self.assertEqual(tab.limit.value(), 100)
                buttons["▲"].click()
                self.assertEqual(tab.limit.value(), 101)
                self.assertEqual(db.get_setting("multichat_limit", ""), "101")
                buttons["▼"].click()
                self.assertEqual(tab.limit.value(), 100)
                self.assertEqual(db.get_setting("multichat_limit", ""), "100")

                tab.resize(1200, 700)
                self.app.processEvents()
                self.assertEqual(tab.columns.direction(), QBoxLayout.LeftToRight)

                # One real RAM event is read both by Qt and by the EXISTING
                # localhost service; the browser page itself has no provider.
                message = ChatMessage("twitch", "ch", "m1", "Автор", "<script>hello</script>")
                state.ingest(message)
                tab.refresh()
                self.assertIn("<script>hello</script>", tab.feed.toPlainText())
                with urllib.request.urlopen(api.base_url + "/api/multichat", timeout=10) as response:
                    payload = json.load(response)
                self.assertEqual(len(payload["messages"]), 1)
                self.assertEqual(payload["messages"][0]["text"], "<script>hello</script>")
                with urllib.request.urlopen(api.base_url + "/multichat-overlay", timeout=10) as response:
                    html = response.read().decode("utf-8")
                self.assertIn("textContent", html)
                self.assertIn("/api/multichat", html)
                self.assertIn('iol-version-handshake', html)

                # Checkbox routing affects OBS, NOT the operator chat.
                state.set_obs_enabled("twitch", False)
                state.ingest(ChatMessage("twitch", "ch", "m2", "Автор", "Только локально"))
                with urllib.request.urlopen(api.base_url + "/api/multichat", timeout=10) as response:
                    obs = json.load(response)
                self.assertEqual([x["external_id"] for x in obs["messages"]], ["m1"])
                self.assertEqual(len(state.snapshot()["messages"]), 2)

                # Invalid delay does not get persisted and is visibly restored.
                tab.delay.setText("-5")
                tab._on_delay()
                self.assertEqual(tab.delay.text(), "0.0")
                self.assertEqual(db.get_setting("multichat_delay", ""), "0.0")
                tab.show_time.setChecked(False)
                self.assertEqual(db.get_setting("multichat_show_time", ""), "0")
                self.assertFalse(api.multichat_state()["show_time"])
            finally:
                if tab is not None:
                    tab.refresh_timer.stop()
                    tab.close()
                api.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
