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


    def test_reset_to_defaults_keeps_db_until_save_and_preserves_media(self):
        """FIX3: confirmed reset is local draft; Cancel and Exit don't mutate OBS."""
        from unittest.mock import patch
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication, QMessageBox
        from streaming_manager.media import MediaAsset, MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
        from streaming_manager.views.chat_appearance_controls import ChatAppearanceEditor
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            db = StubDatabase(folder)
            # Simulate existing customized style, registered file and global switch.
            save_appearance(
                db,
                {"mode":"custom", "text_size":42, "name_size":25,
                 "text_color":"#12AB34", "avatar_size":36,
                 "card_border_width":3, "card_radius":20},
                {"background":"media", "background_media_id":42,
                 "glow":True, "glow_color":"#00FF00",
                 "visibility":"always"},
            )
            original_media = Path(folder) / "user_background.png"
            original_media.write_bytes(b"existing user media must be retained")
            db.assets[42] = MediaAsset(
                id=42, category=MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
                storage_mode="external", managed_name="",
                external_path=str(original_media),
                original_name="user_background.png",
                created_at="", updated_at="",
            )
            db.set_setting("multichat_show_time", "false")
            saved = saved_appearance(db)
            original_public = public_appearance(db)
            editor = ChatAppearanceEditor(db)
            editor.resize(520, 360)
            self.assertEqual(editor.values(),saved)
            self.assertFalse(editor.is_dirty())
            updates = []
            editor.changed.connect(
                lambda twitch, common, test: updates.append((twitch, common, test))
            )
            editor.test.click()
            self.assertTrue(editor.test_visible)
            editor.text_size.setValue(64)
            current_draft = editor.values()
            with patch.object(
                QMessageBox, "question", return_value=QMessageBox.StandardButton.No
            ) as confirm:
                editor.reset_button.click()
                self.assertEqual(confirm.call_count,1)
            self.assertEqual(editor.values(),current_draft)
            self.assertTrue(editor.is_dirty())
            self.assertEqual(saved_appearance(db),saved)
            self.assertEqual(public_appearance(db),original_public)

            with patch.object(
                QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes
            ):
                editor.reset_button.click()
            defaults = {
                "twitch":normalize_twitch({}),
                "common":normalize_common({}),
            }
            self.assertEqual(editor.values(),defaults)
            self.assertTrue(editor.is_dirty())
            self.assertTrue(editor.test_visible)
            self.assertTrue(updates)
            self.assertEqual(updates[-1][0],defaults["twitch"])
            self.assertEqual(updates[-1][1],defaults["common"])
            self.assertTrue(updates[-1][2])
            self.assertEqual(saved_appearance(db),saved)
            self.assertEqual(public_appearance(db),original_public)
            self.assertIn(42,db.assets)
            self.assertEqual(db.get_setting("multichat_show_time"),"false")

            # Discard/close without Save restores old custom design.
            editor.discard()
            self.assertFalse(editor.is_dirty())
            self.assertEqual(editor.values(),saved)
            with patch.object(
                QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes
            ):
                editor.reset_button.click()
            self.assertTrue(editor.save())
            self.assertFalse(editor.is_dirty())
            self.assertEqual(saved_appearance(db),defaults)
            self.assertEqual(public_appearance(db)["twitch"],defaults["twitch"])
            self.assertEqual(public_appearance(db)["common"]["background"],"transparent")
            self.assertEqual(db.get_setting("multichat_show_time"),"false")
            self.assertIn(42,db.assets, "Reset must never delete any media entry")
            self.assertTrue(original_media.exists(), "Reset must not delete user files")
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

    def test_saved_png_gif_video_preview_refresh_and_cleanup(self):
        """Regression for user-reported close after saving any media background.

        Exercise the REAL registered library, Qt layer and save controls through
        repeated 250-ms-equivalent refreshes, not only color/static CSS tests.
        """
        import base64
        import time
        os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QColor, QImage
        from PySide6.QtMultimedia import QMediaPlayer
        from streaming_manager.database import Database
        from streaming_manager.media import (
            MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, managed_media_directory,
        )
        from streaming_manager.views.chat_appearance_background import ChatBackgroundFrame
        from streaming_manager.views.chat_appearance_controls import ChatAppearanceEditor
        from streaming_manager.views.chat_rich_feed import ChatRichFeed

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            db = Database(Path(folder) / "chat_media.db")
            media_dir = managed_media_directory(
                db.path.parent, MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
            )
            media_dir.mkdir(parents=True, exist_ok=True)
            still = media_dir / "chat_background.png"
            still_image = QImage(640, 360, QImage.Format_RGB32)
            still_image.fill(QColor("#428A91"))
            self.assertTrue(still_image.save(str(still)))
            gif = media_dir / "chat_background.gif"
            gif.write_bytes(base64.b64decode(
                "R0lGODlhEAAQAIEAAP8AAAAAAAAAAAAAACH/C05FVFNDQVBFMi4w"
                "AwEAAAAh+QQAGQAAACwAAAAAEAAQAAAIHQABCBxIsKDBgwgTKlz"
                "IsKHDhxAjSpxIsaLFgQEBACH5BAEZAAEALAAAAAAQABAAgQAA"
                "/wAAAAAAAAAAAAgdAAEIHEiwoMGDCBMqXMiwocOHECNKnEixosWBAQEAOw=="
            ))
            video = media_dir / "chat_background.webm"
            # Valid five-frame VP8 WebM; exercise real Windows video decoding,
            # not just QMediaPlayer's handling of a placeholder EBML header.
            video.write_bytes(base64.b64decode("GkXfo59ChoEBQveBAULygQRC84EIQoKEd2VibUKHgQJChYECGFOAZwEAAAAAAAKWEU2bdLpNu4tTq4QVSalmU6yBoU27i1OrhBZUrmtTrIHWTbuMU6uEElTDZ1OsggEjTbuMU6uEHFO7a1OsggKA7AEAAAAAAABZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAVSalmsCrXsYMPQkBNgIxMYXZmNjEuNy4xMDNXQYxMYXZmNjEuNy4xMDNEiYhAlNQAAAAAABZUrmvIrgEAAAAAAAA/14EBc8WIULi87M8V5IicgQAitZyDdW5kiIEAhoVWX1ZQOIOBASPjg4QT3kNV4JCwgTC6gSCagQJVsIRVuYEBElTDZ/tzc59jwIBnyJlFo4dFTkNPREVSRIeMTGF2ZjYxLjcuMTAzc3PWY8CLY8WIULi87M8V5IhnyKFFo4dFTkNPREVSRIeUTGF2YzYxLjE5LjEwMSBsaWJ2cHhnyKFFo4hEVVJBVElPTkSHkzAwOjAwOjAxLjMzMzAwMDAwMAAfQ7Z1QNfngQCjv4EAAIDwAgCdASowACAAAEcIhYWImYSIAgICdaoD+AIHkcI+qoD+/00S//xKp/Eqn8Sqf/Eqn/0Yfww/hh/eEKOvgQFNANEBAAEQEAAYABxH9AwAKTGI/v9NEv/8SqfxKp/Eqn/xKp/9GH8MP4Yf3hCjr4ECmwDRAQABEBAAGAAcR/QMACkxiP7/TRL//Eqn8SqfxKp/8Sqf/Rh/DD+GH94Qo6+BA+gA0QEAARAQABgAHEf0DAApMYj+/00S//xKp/Eqn8Sqf/Eqn/0Yfww/hh/eEBxTu2uRu4+zgQC3iveBAfGCAaPwgQM="))
            asset_ids = []
            for path in (still, gif, video):
                asset = db.ensure_managed_media_asset(
                    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, path.name, path.name
                )
                asset_ids.append(asset.id)

            feed = ChatRichFeed()
            frame = ChatBackgroundFrame(db, feed)
            editor = ChatAppearanceEditor(db)
            frame.resize(650, 400)
            frame.show()
            app.processEvents()
            try:
                editor._set_combo(editor.background, "media")
                # Actual report used a bright outer glow while cycling media.
                editor.glow.setChecked(True)
                frame.feed.display(
                    [{"platform":"twitch", "author":"test",
                      "text":"Media regression",
                      "fragments":[{"kind":"text","text":"Media regression"}]}],
                    show_time=False, show_icons=True,
                )
                for id_, kind in zip(asset_ids, ("image", "gif", "video")):
                    editor._refresh_media(id_)
                    self.assertEqual(editor.media_combo.currentData(), id_)
                    self.assertTrue(editor.save())
                    current = saved_appearance(db)["common"]
                    self.assertEqual(current["background_media_id"], id_)
                    self.assertTrue(current["glow"])
                    frame.apply(current, has_content=True)
                    self.assertTrue(frame.effect.isEnabled())
                    app.processEvents()
                    # The canvas must not grow to its own scaled pixmap's
                    # size: this feedback loop closed the Windows process.
                    start_width, start_height = frame.width(), frame.height()
                    self.assertEqual(frame.media.sizeHint().width(), 0)
                    self.assertEqual(frame.media.sizeHint().height(), 0)
                    self.assertEqual(frame._movie_kind,kind)
                    self.assertIsNotNone(frame._source_key)
                    if kind == "gif":
                        self.assertTrue(frame._movie.isValid())
                    if kind == "video":
                        self.assertIsInstance(frame._player,QMediaPlayer)
                        self.assertIsNone(frame._player.audioOutput())
                    # Keep a real Qt event loop active for delayed QMovie,
                    # QVideoSink and 250-ms operator refresh cycles.
                    deadline = time.monotonic() + 2.0
                    while time.monotonic() < deadline:
                        frame.apply(current,has_content=True)
                        app.processEvents()
                        time.sleep(.025)
                    self.assertEqual(frame._movie_kind,kind)
                    if kind == "video":
                        self.assertFalse(frame._original.isNull(),
                            "Windows must decode real WebM frames in Qt preview")
                    self.assertLessEqual(frame.width(), start_width + 2,
                        "Scaled media must not cause growing Qt layout width")
                    self.assertLessEqual(frame.height(), start_height + 2,
                        "Scaled media must not cause growing Qt layout height")
                    self.assertIs(frame.layout().currentWidget(),feed)
                    self.assertIn("Media regression",feed.toPlainText())
                    if kind == "image":
                        # Pump any pending Qt resize/layout events before
                        # recording the stable pixmap render key.
                        for _ in range(4):
                            frame.apply(current,has_content=True)
                            app.processEvents()
                        before = frame._paint_key
                        for _ in range(12):
                            frame.apply(current,has_content=True)
                            app.processEvents()
                        self.assertEqual(frame._paint_key,before,
                            "Static media must NOT redraw every 250 ms")
                # Leaving media releases native Qt decoder/animations cleanly.
                editor._set_combo(editor.background,"transparent")
                self.assertTrue(editor.save())
                frame.apply(saved_appearance(db)["common"],has_content=True)
                app.processEvents()
                self.assertIsNone(frame._player)
                self.assertIsNone(frame._movie)
                self.assertIsNone(frame._source_key)
            finally:
                frame.shutdown()
                feed._poll.stop()
                editor.close()
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
        self.assertIn(".message + .message {margin-top:10px}", html)

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
