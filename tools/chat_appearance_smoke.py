"""D41-06: no-network presentation model and native Qt draft lifecycle smoke."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from streaming_manager.chat_appearance import (
    COMMON_KEY, TWITCH_KEY, normalize_common, normalize_twitch,
    public_appearance, save_appearance, saved_appearance,
)


class StubDatabase:
    def __init__(self, base):
        self.values = {}
        self.path = Path(base) / "inone.db"
        self.assets = {}

    def get_setting(self, key, default=""):
        return self.values.get(key, default)

    def set_setting(self, key, value):
        self.values[key] = value

    def get_media_asset(self, asset_id):
        return self.assets.get(asset_id)

    def sync_managed_media_category(self, category):
        return None

    def list_media_assets(self, category):
        return []


class AppearanceModelTests(unittest.TestCase):
    def test_invalid_and_unsafe_values_are_bounded(self):
        t = normalize_twitch({
            "mode":"custom", "text_font":"Arial;};alert(1)",
            "text_color":"url(javascript:bad)", "name_size":10000,
            "card_opacity":-23, "avatar_size":0, "card_border_width":999,
        })
        self.assertEqual(t["mode"], "custom")
        self.assertEqual(t["text_font"], "Segoe UI")
        self.assertEqual(t["text_color"], "#FFFFFF")
        self.assertEqual(t["name_size"], 96)
        self.assertEqual(t["card_opacity"], 0)
        self.assertEqual(t["avatar_size"], 8)
        self.assertEqual(t["card_border_width"], 12)
        c = normalize_common({
            "background":"media", "background_media_id":"../../../etc/passwd",
            "background_fit":"stretch", "visibility":"auto",
            "glow":"true", "background_opacity":200,
        })
        self.assertIsNone(c["background_media_id"])
        self.assertEqual(c["background_fit"], "cover")
        self.assertEqual(c["visibility"], "hide_empty")
        self.assertFalse(c["glow"])
        self.assertEqual(c["background_opacity"], 100)

    def test_draft_does_not_touch_db_and_saved_api_only_after_save(self):
        with tempfile.TemporaryDirectory() as folder:
            db = StubDatabase(folder)
            before = public_appearance(db)
            self.assertEqual(before["twitch"]["mode"], "original")
            draft = normalize_twitch({"mode":"custom","text_size":29})
            self.assertEqual(public_appearance(db), before)
            save_appearance(db,draft,{"background":"color","background_opacity":30})
            after = public_appearance(db)
            self.assertEqual(after["twitch"]["text_size"],29)
            self.assertEqual(after["common"]["background"],"color")
            self.assertNotIn("text"," ".join(db.values.keys()))
            self.assertEqual(set(db.values), {TWITCH_KEY,COMMON_KEY})
            self.assertFalse(after["common"]["media_url"])
            self.assertEqual(saved_appearance(db)["twitch"],after["twitch"])
            db.set_setting(TWITCH_KEY,"{{INVALID")
            self.assertEqual(saved_appearance(db)["twitch"]["mode"],"original")

    def test_qt_control_draft_save_and_test_never_persist(self):
        os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
        from PySide6.QtWidgets import QApplication
        from streaming_manager.views.chat_appearance_controls import ChatAppearanceEditor
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            db = StubDatabase(folder)
            editor = ChatAppearanceEditor(db)
            self.assertEqual(editor.values(), editor.saved)
            editor.mode.setCurrentIndex(1)
            editor.text_size.setValue(31)
            self.assertTrue(editor.is_dirty())
            self.assertEqual(db.values,{})
            editor.test.click()
            self.assertTrue(editor.test_visible)
            self.assertEqual(db.values,{})
            self.assertTrue(editor.save())
            self.assertFalse(editor.is_dirty())
            self.assertNotIn("Пример Twitch",str(db.values))
            editor.text_size.setValue(45)
            self.assertTrue(editor.is_dirty())
            editor.discard()
            self.assertFalse(editor.is_dirty())
            self.assertEqual(editor.text_size.value(),31)
            editor.close()
        app.processEvents()


    def test_operator_preview_is_visible_above_background(self):
        """Regression: StackAll index 0 (media) hid the real Qt operator feed."""
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication, QStackedLayout
        from streaming_manager.views.chat_appearance_background import ChatBackgroundFrame
        from streaming_manager.views.chat_rich_feed import ChatRichFeed
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            feed = ChatRichFeed()
            frame = ChatBackgroundFrame(StubDatabase(folder), feed)
            frame.resize(720, 420)
            frame.show()
            app.processEvents()
            self.assertIsInstance(frame.layout(), QStackedLayout)
            self.assertIs(frame.layout().currentWidget(), feed)
            self.assertTrue(feed.isVisible())
            frame.apply({"background":"color", "background_color":"#606554",
                         "background_opacity":65, "glow":True},
                        has_content=True)
            feed.display(
                [{"platform":"twitch", "author":"Alex_say62",
                  "text":"Привет", "fragments":[{"kind":"text","text":"Привет"}],
                  "color":"#FAC21F"}],
                show_time=False,show_icons=True,
                appearance={"mode":"custom", "text_color":"#176DA5",
                            "text_size":30, "card_opacity":0},
                test_visible=False,
            )
            app.processEvents()
            self.assertIn("Привет",feed.toPlainText())
            self.assertIn("Alex_say62",feed.toPlainText())
            before = frame.grab().toImage()
            feed.display(
                [{"platform":"twitch", "author":"Alex_say62",
                  "text":"Привет", "fragments":[{"kind":"text","text":"Привет"}],
                  "color":"#FAC21F"}],
                show_time=False,show_icons=True,
                appearance={"mode":"custom", "text_color":"#176DA5",
                            "text_size":30, "card_opacity":0},
                test_visible=True,
            )
            app.processEvents()
            self.assertIn("Тестовое сообщение",feed.toPlainText())
            after = frame.grab().toImage()
            self.assertFalse(before == after,
                             "Local preview must visibly change on test message")
            frame.shutdown()
            feed._poll.stop()
            frame.close()
        app.processEvents()

    def test_browser_box_safe_area_does_not_clip_edges(self):
        html = Path("streaming_manager/web/multichat_overlay.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("--chat-edge-inset:12px", html)
        self.assertIn("left:var(--chat-edge-inset)", html)
        self.assertIn("right:var(--chat-edge-inset)", html)
        self.assertIn("bottom:var(--chat-edge-inset)", html)
        self.assertIn("#shell.always {top:var(--chat-edge-inset)", html)
        self.assertIn("max-height:calc(100% - 2 * var(--chat-edge-inset))",html)
        self.assertIn("0 0 6px",html)

    def test_overlay_never_renders_provider_html(self):
        overlay = Path("streaming_manager/web/multichat_overlay.html").read_text(encoding="utf-8")
        self.assertIn('row.style.background = rgba(',overlay)
        self.assertIn('shell.classList.toggle("hidden"',overlay)
        self.assertIn("applyAppearance(state.appearance)",overlay)
        self.assertIn("body.textContent = String(message.text || \"\")",overlay)
        self.assertNotIn("innerHTML",overlay)
        self.assertIn("bgVideo.muted = true",overlay)


if __name__ == "__main__":
    unittest.main()
