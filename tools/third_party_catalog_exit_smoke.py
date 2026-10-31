"""PERF-01: former nested emote catalog network pools must not keep Python alive."""
from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from streaming_manager.chat_third_party import make_catalog
from streaming_manager.emote_catalog import (
    EmoteCatalogItem,
    run_chat_catalog_helper,
)
from streaming_manager.twitch_b4 import TwitchEventSubRuntime


def runtime_for_test():
    service = SimpleNamespace(connection_ready=lambda: True)
    runtime = TwitchEventSubRuntime(service)
    runtime._chat_source_id = "12345"
    runtime._third_party_source = "12345"
    return runtime


class FrozenCatalogChild:
    def __init__(self, *, hang=False, items=None):
        self.hang = hang
        self.items = items or []
        self.started = threading.Event()
        self.released = threading.Event()
        self.killed = False
        self.returncode = None

    def popen(self, args, **kwargs):
        assert args[-3] == "--fetch-chat-catalog"
        assert args[-2] == "12345"
        if not self.hang:
            Path(args[-1]).write_text(json.dumps(self.items), encoding="utf-8")
        return self

    def communicate(self, timeout=None):
        self.started.set()
        if self.hang:
            if not self.released.wait(2 if timeout and timeout > 1 else timeout):
                raise subprocess.TimeoutExpired("frozen-catalog-test", timeout)
        self.returncode = -9 if self.killed else 0
        return b"", b""

    def kill(self):
        self.killed = True
        self.returncode = -9
        self.released.set()

    def poll(self):
        return self.returncode


class CatalogExitSmoke(unittest.TestCase):
    def test_active_catalog_dns_block_is_cancelled_on_shutdown(self):
        runtime = runtime_for_test()
        fake = FrozenCatalogChild(hang=True)
        with patch("streaming_manager.twitch_b4.subprocess.Popen", side_effect=fake.popen):
            worker = threading.Thread(target=runtime._load_third_party_catalog, args=("12345",))
            worker.start()
            try:
                self.assertTrue(fake.started.wait(2))
                before = time.monotonic()
                runtime.stop()
                worker.join(timeout=2)
                self.assertLess(time.monotonic() - before, 2.5)
                self.assertFalse(worker.is_alive())
                self.assertTrue(fake.killed)
                self.assertIsNone(runtime._third_party_process)
            finally:
                fake.kill()
                worker.join(2)

    def test_real_os_child_is_reaped_after_runtime_stop(self):
        import sys

        runtime = runtime_for_test()
        spawned = []
        real_popen = subprocess.Popen

        def spawn_stalled_child(_args, **kwargs):
            child = real_popen(
                [sys.executable, "-c", "import time;time.sleep(60)"],
                **kwargs,
            )
            spawned.append(child)
            return child

        try:
            with patch("streaming_manager.twitch_b4.subprocess.Popen", side_effect=spawn_stalled_child):
                worker = threading.Thread(
                    target=runtime._load_third_party_catalog,
                    args=("12345",),
                )
                worker.start()
                deadline = time.monotonic() + 5
                while not spawned and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(spawned, "catalog helper not launched")
                start = time.monotonic()
                runtime.stop()
                worker.join(timeout=3)
                self.assertLess(time.monotonic() - start, 3)
                self.assertFalse(worker.is_alive())
                self.assertIsNotNone(spawned[0].poll(),
                    "No orphaned catalog helper may survive application stop")
        finally:
            for process in spawned:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)

    def test_existing_catalog_is_preserved_through_json_protocol(self):
        runtime = runtime_for_test()
        rows = [
            {"source": "7TV", "emote_id": "one", "name": "catJAM",
             "image_url": "https://cdn.7tv.app/emote/one/4x.webp",
             "preview_url": "https://cdn.7tv.app/emote/one/2x.webp", "animated": True},
            {"source": "BTTV", "emote_id": "two", "name": "OMEGALUL",
             "image_url": "https://cdn.betterttv.net/emote/two/3x",
             "preview_url": "https://cdn.betterttv.net/emote/two/1x", "animated": False},
        ]
        fake = FrozenCatalogChild(items=rows)
        with patch("streaming_manager.twitch_b4.subprocess.Popen", side_effect=fake.popen):
            runtime._load_third_party_catalog("12345")
        original = make_catalog([EmoteCatalogItem(**x) for x in rows])
        self.assertEqual(runtime._third_party_catalog, original)
        self.assertIsNone(runtime._third_party_process)
        runtime.stop()

    def test_unsuccessful_and_cancelled_catalog_never_applied(self):
        runtime = runtime_for_test()
        fake = FrozenCatalogChild(items=[{"source": "7TV", "emote_id": "a", "name": "A",
            "image_url": "https://cdn.7tv.app/emote/a/4x.webp",
            "preview_url": "https://cdn.7tv.app/emote/a/2x.webp", "animated": False}])
        with patch("streaming_manager.twitch_b4.subprocess.Popen", side_effect=fake.popen):
            runtime._stop.set()
            runtime._load_third_party_catalog("12345")
        self.assertEqual(runtime._third_party_catalog, {})
        self.assertFalse(fake.started.is_set())
        runtime.stop()

    def test_helper_protocol_contains_provider_metadata_not_credentials(self):
        item = EmoteCatalogItem("7TV", "e1", "catJAM",
            "https://cdn.7tv.app/emote/e1/4x.webp",
            "https://cdn.7tv.app/emote/e1/2x.webp", True)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "result.json"
            self.assertEqual(run_chat_catalog_helper("invalid/../../", str(target)), 2)
            self.assertFalse(target.exists())
            with patch("streaming_manager.emote_catalog.fetch_third_party_chat_emotes", return_value=[item]):
                self.assertEqual(run_chat_catalog_helper("12345", str(target)), 0)
            value = json.loads(target.read_text("utf-8"))
            self.assertEqual(value[0]["name"], "catJAM")
            self.assertTrue(value[0]["animated"])
            self.assertNotIn("thumbnail_bytes", value[0])
            self.assertEqual(set(value[0]), {
                "source", "emote_id", "name", "image_url", "preview_url", "animated"
            })


if __name__ == "__main__":
    unittest.main(verbosity=2)
