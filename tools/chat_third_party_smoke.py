"""D41-05 offline channel/global third-party Twitch emote regression."""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from streaming_manager.chat_third_party import (
    make_catalog, resolve_fragments, resolve_text,
)
from streaming_manager.emote_catalog import (
    EmoteCatalogItem, fetch_third_party_chat_emotes,
)
from streaming_manager.chat_graphics import safe_image_url
from streaming_manager.multichat import MultichatState
from streaming_manager.twitch_b4 import TwitchEventSubRuntime


def emote(provider, code, url=None, animated=False):
    name = url or {
        "BTTV": "https://cdn.betterttv.net/emote/123/3x",
        "FFZ": "https://cdn.frankerfacez.com/emote/123/3",
        "7TV": "https://cdn.7tv.app/emote/123/4x.webp",
    }[provider]
    return EmoteCatalogItem(provider, "id", code, name, name, animated)


class ThirdPartySmoke(unittest.TestCase):
    def test_security_whitelist_and_no_forged_domain(self):
        for root in ("https://cdn.betterttv.net/emote/1/3x",
                     "https://cdn.frankerfacez.com/emote/2/3",
                     "https://cdn.7tv.app/emote/3/4x.webp"):
            self.assertEqual(safe_image_url(root), root)
        for spoof in ("http://cdn.7tv.app/e", "https://cdn.7tv.app.evil.org/x",
                      "https://admin@cdn.betterttv.net/x", "file:///etc/passwd",
                      "https://127.0.0.1/foo"):
            self.assertFalse(safe_image_url(spoof))
        self.assertEqual(make_catalog([emote("BTTV", "Pog",
                                  "https://not-approved.com/image.png")]), {})

    def test_text_exact_code_and_original_order_preserved(self):
        catalog = make_catalog([emote("BTTV", "OMEGALUL"), emote("7TV", "catJAM", animated=True)])
        fragments = resolve_text("Hello OMEGALUL! (catJAM) /OMEGALUL https://site/OMEGALUL", catalog)
        self.assertEqual("".join(f["text"] for f in fragments),
                         "Hello OMEGALUL! (catJAM) /OMEGALUL https://site/OMEGALUL")
        self.assertEqual([(p["kind"],p["text"]) for p in fragments if p["kind"] == "image"],
                         [("image","OMEGALUL"), ("image","catJAM")])
        self.assertEqual(sum(f["kind"] == "image" for f in fragments), 2)

    def test_ambiguous_provider_collisions_remain_literal(self):
        catalog = make_catalog([
            emote("7TV", "Dup", "https://cdn.7tv.app/emote/3/4x.webp"),
            emote("BTTV", "Dup", "https://cdn.betterttv.net/emote/123/3x"),
            emote("FFZ", "Unique"),
            emote("BTTV", "Same", "https://cdn.betterttv.net/emote/111/3x"),
            emote("BTTV", "Same", "https://cdn.betterttv.net/emote/111/3x"),
        ])
        self.assertIsNone(catalog["Dup"])
        parsed = resolve_text("Dup Unique Same", catalog)
        self.assertEqual([p["text"] for p in parsed if p["kind"] == "image"],
                         ["Unique","Same"])
        self.assertEqual("".join(f["text"] for f in parsed), "Dup Unique Same")

    def test_native_twitch_emotes_and_gifs_are_never_replaced(self):
        native = ({"kind": "text", "text": "Hey "},
                  {"kind": "image", "text": "Kappa",
                   "url": "https://static-cdn.jtvnw.net/emoticons/v2/25/static/dark/2.0"},
                  {"kind": "text", "text": " OMEGALUL"})
        got = resolve_fragments(native, "Hey Kappa OMEGALUL",
                                make_catalog([emote("7TV","OMEGALUL"),emote("FFZ","Kappa")]))
        self.assertEqual([f["text"] for f in got if f["kind"] == "image"],
                         ["Kappa","OMEGALUL"])
        self.assertEqual(got[1], native[1])
        self.assertEqual(resolve_fragments(native, "Hey Kappa OMEGALUL", {}), native)
        many = " ".join(["OMEGALUL"] * 100)
        parsed = resolve_fragments((), many, make_catalog([emote("BTTV","OMEGALUL")]))
        self.assertEqual("".join(f["text"] for f in parsed), many)
        self.assertLessEqual(sum(f["kind"]=="image" for f in parsed), 32)

    def test_global_api_only_ffz_default_sets(self):
        ffz = {
            "default_sets": [3],
            "sets": {
                "3": {"emoticons": [{"id": 9, "name": "Public",
                         "urls": {"1": "//cdn.frankerfacez.com/emote/9/1"}}]},
                "4": {"emoticons": [{"id": 10, "name": "UserGated",
                         "urls": {"1": "//cdn.frankerfacez.com/emote/10/1"}}]},
            },
        }
        seven = {"emotes": [{"id":"123","name":"GlobalSeven",
                            "data":{"animated":True}}]}
        def fetch(url):
            if url.endswith("set/global"): return ffz
            if url.endswith("emote-sets/global"): return seven
            return {}
        with patch("streaming_manager.emote_catalog._fetch_json", side_effect=fetch), \
             patch("streaming_manager.emote_catalog._fetch_list",
                   return_value=[{"id":"b123","code":"GlobalBttv","imageType":"gif"}]), \
             patch("streaming_manager.emote_catalog.fetch_third_party_channel_emotes",
                   return_value=[emote("BTTV", "RoomBttv")]):
            got = fetch_third_party_chat_emotes("12345")
        codes = {e.name for e in got}
        self.assertEqual(codes, {"Public","GlobalSeven","GlobalBttv","RoomBttv"})
        self.assertNotIn("UserGated", codes)
        self.assertEqual(fetch_third_party_chat_emotes("../../../etc"), [])

    def test_eventsub_freezes_content_at_receipt_including_pending(self):
        state = MultichatState(delay=30.0)
        state.set_obs_enabled("twitch", True)
        service = SimpleNamespace(connection_ready=lambda: True,
                                  db=SimpleNamespace(get_integration_connection=lambda _:{}))
        runtime = TwitchEventSubRuntime(service,chat_state=state)
        runtime._chat_source_id = "123"
        runtime._third_party_source = "123"
        word = emote("7TV", "catJAM", animated=True)
        runtime._third_party_catalog = make_catalog([word])
        def send(message_id, content):
            runtime._process_chat_notification("channel.chat.message",{
                "broadcaster_user_id":"123", "message_id":message_id,
                "chatter_user_id":"77", "chatter_user_name":"Viewer",
                "message":{"text":content,"fragments":[{"type":"text","text":content}]},
            },{})
        send("first","catJAM")
        runtime._third_party_catalog = {}
        send("second","catJAM")
        state.configure(delay=0.0)
        for obs in (True, False):
            data = state.snapshot(for_obs=obs)["messages"]
            self.assertEqual([m["external_id"] for m in data],["first","second"])
            self.assertEqual(data[0]["fragments"][0]["kind"],"image")
            self.assertEqual(data[1]["fragments"][0]["kind"],"text")
        runtime._process_chat_notification("channel.chat.message_delete",
                 {"broadcaster_user_id":"123","message_id":"first"}, {})
        self.assertEqual([m["external_id"] for m in state.snapshot()["messages"]],["second"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
