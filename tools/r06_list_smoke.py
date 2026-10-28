"""R06 first package: shared List show, command timer, and read-only OBS API."""
from __future__ import annotations

import json
import socket
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database
from streaming_manager.multichat import ChatMessage, MultichatState


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class R06ListApiSmoke(unittest.TestCase):
    def test_shared_list_mode_and_chat_are_read_only(self):
        with TemporaryDirectory(ignore_cleanup_errors=True) as temp:
            db = Database(Path(temp) / "streaming.db")
            db.set_settings_bulk({
                "list_overlay_show_mode": "slide",
                "list_slide_direction": "top",
                "list_slide_duration": "30",
                "list_animation_seconds": "1.50",
                "list_slide_command": "!list",
                "list_chat_layout": "replace",
                "list_with_chat": "1",
            })
            clock = Clock()
            state = MultichatState(clock=clock, wall_clock=clock)
            api = LocalApiServer(db, port=port())
            api.set_multichat_state_provider(state.snapshot)
            api.set_list_show_controller(state.configure_list_show)
            api.configure_list_show("slide", "!list", 30)
            api.start()
            try:
                def get(path):
                    with urlopen(api.base_url + path, timeout=5) as response:
                        return response.read().decode("utf-8")

                def data():
                    return json.loads(get("/api/data"))

                before = db.get_settings()
                current = data()
                self.assertEqual(current["visibility"]["list"]["show_mode"], "slide")
                self.assertEqual(current["overlay"]["list_slide_direction"], "top")
                self.assertEqual(current["overlay"]["list_animation_seconds"], "1.50")
                self.assertEqual(current["overlay"]["list_chat_layout"], "replace")
                self.assertTrue(current["overlay"]["list_with_chat"])
                self.assertEqual(current["list_show"]["remaining_ms"], 0)
                self.assertFalse(current["multichat"]["has_messages"])
                self.assertTrue(current["multichat"]["enabled"])
                self.assertIn("/list-composition.js", get("/list-overlay"))
                self.assertIn("/list-composition.js", get("/overlay"))
                composition = get("/list-composition.js")
                self.assertIn("IOLListComposition", composition)
                self.assertIn("card.getBoundingClientRect().height", composition)
                self.assertNotIn("messages.scrollHeight", composition)
                self.assertIn("list_animation_seconds", composition)
                self.assertIn('embedded=1', get("/list-overlay"))

                state.ingest(ChatMessage("twitch", "ch", "first", "viewer", "!list"))
                self.assertEqual(data()["list_show"]["remaining_ms"], 30000)
                self.assertEqual(data()["list_show"]["sequence"], 1)
                self.assertTrue(data()["multichat"]["has_messages"])
                clock.advance(10)
                self.assertEqual(data()["list_show"]["remaining_ms"], 20000)
                state.set_obs_enabled("twitch", False)
                hidden = data()
                self.assertFalse(hidden["multichat"]["enabled"])
                self.assertFalse(hidden["multichat"]["has_messages"])
                self.assertEqual(json.loads(get("/api/multichat"))["messages"], [])
                state.ingest(ChatMessage("twitch", "ch", "second", "viewer", "!list"))
                self.assertEqual(data()["list_show"]["sequence"], 2)
                self.assertEqual(data()["list_show"]["remaining_ms"], 30000)
                self.assertEqual(len(state.snapshot()["messages"]), 2)
                state.set_obs_enabled("twitch", True)
                self.assertFalse(data()["multichat"]["has_messages"])
                state.ingest(ChatMessage("twitch", "ch", "fresh", "viewer", "hello"))
                self.assertTrue(data()["multichat"]["has_messages"])
                self.assertEqual([m["external_id"] for m in json.loads(get("/api/multichat"))["messages"]], ["fresh"])
                self.assertEqual(db.get_settings(), before, "A read-only API request changed saved settings")
            finally:
                api.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
