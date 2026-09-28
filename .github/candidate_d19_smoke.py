from __future__ import annotations

import base64
import json
import os
import sys
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QMessageBox

from streaming_manager.app_paths import AppPaths
from streaming_manager.constants import (
    APP_VERSION,
    SCHEMA_VERSION,
    WHEEL_CENTER_IMAGE_MEDIA_ID_KEY,
)
from streaming_manager.database import Database, Game
from streaming_manager.media import (
    MEDIA_CATEGORY_WHEEL_CENTER_ICONS,
    managed_media_directory,
)
from streaming_manager.emote_catalog import (
    EmoteCatalogItem,
    _parse_7tv_emotes,
    _parse_bttv_emotes,
    _parse_ffz_emotes,
)
from streaming_manager.remote_image import (
    load_local_image,
    resolve_external_image_source,
)
from streaming_manager.twitch import TwitchAdapter
from streaming_manager.views.main_window import MainWindow


assert APP_VERSION == "1.0.4", APP_VERSION
assert SCHEMA_VERSION == 18, SCHEMA_VERSION


def write_test_png(path: Path) -> None:
    image = QImage(96, 64, QImage.Format_ARGB32)
    image.fill(0xFF336699)
    assert image.save(str(path), "PNG")


app = QApplication.instance() or QApplication([])
old_info = QMessageBox.information
old_warn = QMessageBox.warning
old_critical = QMessageBox.critical
QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: QMessageBox.Ok)

try:
    with TemporaryDirectory() as root:
        paths = AppPaths.from_root(root)
        paths.ensure_runtime_dirs()
        db = Database(paths.database_path)
        db.set_setting("api_port", "18769")

        with db.connect() as conn:
            migration_count = int(
                conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
            )
        assert migration_count == 14, migration_count

        db.add_game(Game(None, "Alpha", None, 100, status="not_played"))
        db.add_game(Game(None, "Beta", None, 50, status="played"))

        before = db.current_wheel_payload()
        assert before["center_image"] == {
            "enabled": False,
            "asset_id": None,
            "url": "",
            "animated": False,
        }
        sectors_before = json.dumps(
            before["sectors"], ensure_ascii=False, sort_keys=True
        )

        local_source = Path(root) / "source.png"
        write_test_png(local_source)
        static_image = load_local_image(str(local_source))
        assert static_image.extension == ".png"
        assert static_image.animated is False
        assert static_image.image_bytes.startswith(b"\x89PNG\r\n\x1a\n")

        # Deterministic two-frame GIF: D19 must preserve the animation bytes
        # instead of flattening them to PNG frame 1.
        animated_gif = base64.b64decode(
            "R0lGODlhBAAEAIEAAP8AAAAAAAAAAAAAACH/C05FVFNDQVBFMi4wAwEAAAAh+QQACgAAACwAAAAABAAEAAAICQABCBxIsCCAgAAh+QQBCgABACwAAAAABAAEAIEA/wAAAAAAAAAAAAAICQABCBxIsCCAgAA7"
        )
        animated_source = Path(root) / "source.gif"
        animated_source.write_bytes(animated_gif)
        animated_image = load_local_image(str(animated_source))
        assert animated_image.extension == ".gif", animated_image
        assert animated_image.animated is True, animated_image
        assert animated_image.image_bytes.startswith(b"GIF8")

        media_dir = managed_media_directory(
            db.path.parent, MEDIA_CATEGORY_WHEEL_CENTER_ICONS
        )
        media_dir.mkdir(parents=True, exist_ok=True)
        managed_path = media_dir / "candidate-center.gif"
        managed_path.write_bytes(animated_image.image_bytes)
        asset = db.ensure_managed_media_asset(
            MEDIA_CATEGORY_WHEEL_CENTER_ICONS,
            managed_path.name,
            "Candidate Center",
        )
        db.set_setting(WHEEL_CENTER_IMAGE_MEDIA_ID_KEY, str(asset.id))

        after = db.current_wheel_payload()
        assert after["center_image"]["enabled"] is True, after["center_image"]
        assert after["center_image"]["asset_id"] == asset.id
        assert after["center_image"]["url"] == f"/media/{asset.id}"
        assert after["center_image"]["animated"] is True
        assert (
            json.dumps(after["sectors"], ensure_ascii=False, sort_keys=True)
            == sectors_before
        )

        url, label = resolve_external_image_source("7tv:01ABCxyz")
        assert "cdn.7tv.app/emote/01ABCxyz/4x.webp" in url
        assert label.startswith("7TV ")

        url, label = resolve_external_image_source(
            "bttv:abcdef0123456789abcdef01"
        )
        assert "cdn.betterttv.net/emote/abcdef0123456789abcdef01/3x" in url
        assert label.startswith("BetterTTV ")

        url, label = resolve_external_image_source(
            "twitch:Example_Channel",
            twitch_profile_resolver=lambda login: (
                f"https://example.invalid/{login}.png"
            ),
        )
        assert url.endswith("/Example_Channel.png")
        assert label == "Twitch @Example_Channel"

        seven = _parse_7tv_emotes(
            {
                "emote_set": {
                    "emotes": [
                        {
                            "id": "seven-id",
                            "name": "SevenSmile",
                            "data": {"animated": True},
                        }
                    ]
                }
            }
        )
        assert len(seven) == 1
        assert seven[0].source == "7TV"
        assert seven[0].image_url.endswith("/seven-id/4x.webp")

        bttv = _parse_bttv_emotes(
            {
                "channelEmotes": [
                    {
                        "id": "bttv-id",
                        "code": "BttvSmile",
                        "imageType": "gif",
                    }
                ],
                "sharedEmotes": [],
            }
        )
        assert len(bttv) == 1
        assert bttv[0].source == "BTTV"
        assert bttv[0].animated is True

        ffz = _parse_ffz_emotes(
            {
                "sets": {
                    "1": {
                        "emoticons": [
                            {
                                "id": 123,
                                "name": "FfzSmile",
                                "urls": {
                                    "1": "//cdn.example/ffz-1.png",
                                    "4": "//cdn.example/ffz-4.png",
                                },
                            }
                        ]
                    }
                }
            }
        )
        assert len(ffz) == 1
        assert ffz[0].source == "FFZ"
        assert ffz[0].image_url == "https://cdn.example/ffz-4.png"
        assert ffz[0].preview_url == "https://cdn.example/ffz-1.png"

        twitch_payload = {
            "template": (
                "https://static-cdn.jtvnw.net/emoticons/v2/"
                "{{id}}/{{format}}/{{theme_mode}}/{{scale}}"
            )
        }
        twitch_row = {
            "id": "42",
            "format": ["static", "animated"],
            "scale": ["1.0", "2.0", "3.0"],
            "theme_mode": ["light", "dark"],
        }
        assert TwitchAdapter._emote_image_url(
            twitch_payload, twitch_row, preview=False
        ).endswith("/42/animated/dark/3.0")
        assert TwitchAdapter._emote_image_url(
            twitch_payload, twitch_row, preview=True
        ).endswith("/42/animated/dark/1.0")

        import streaming_manager.remote_image as remote_image

        original_fetch_json = remote_image._fetch_json
        remote_image._fetch_json = lambda _url: {
            "emote": {
                "name": "TestFFZ",
                "urls": {
                    "1": "//cdn.example/1.png",
                    "4": "//cdn.example/4.png",
                },
            }
        }
        try:
            url, label = resolve_external_image_source("ffz:12345")
            assert url == "https://cdn.example/4.png"
            assert label == "FFZ TestFFZ"
        finally:
            remote_image._fetch_json = original_fetch_json

        # This focused smoke does not test the already-existing startup
        # backup worker. Disable only that deferred QA side effect so the
        # TemporaryDirectory cannot disappear while its worker is still active.
        original_startup_backup = MainWindow._startup_backup
        MainWindow._startup_backup = lambda self: None
        try:
            window = MainWindow(db, paths)
        finally:
            MainWindow._startup_backup = original_startup_backup
        try:
            settings = window.settings_tab
            index = settings.wheel_center_image_combo.findData(asset.id)
            assert index >= 0
            settings.wheel_center_image_combo.setCurrentIndex(index)
            settings.save_auction_settings()
            assert (
                db.get_setting(WHEEL_CENTER_IMAGE_MEDIA_ID_KEY, "")
                == str(asset.id)
            )

            auction = window.auction_tab
            weighted_index = auction.mode_combo.findData("weighted_wheel")
            assert weighted_index >= 0
            auction.mode_combo.setCurrentIndex(weighted_index)
            auction._update_wheel_panel(None)
            assert auction.wheel_widget._center_image_path == str(managed_path)

            # Pointauc-like D19 quick picker: one upload action + one unified
            # visual grid. No search/filter controls are part of this dialog.
            auction._wheel_center_catalog_cache = []
            auction._open_wheel_center_picker()
            picker = auction._wheel_center_picker
            assert picker is not None
            assert picker.upload_btn.text() == "Загрузить своё изображение"
            assert any(
                int(item.get("asset_id") or 0) == int(asset.id)
                for item in picker._local_items
            )
            picker.set_remote_items(
                [
                    EmoteCatalogItem(
                        source="7TV",
                        emote_id="preview-id",
                        name="PreviewSmile",
                        image_url="https://example.invalid/full.webp",
                        preview_url="https://example.invalid/preview.webp",
                        animated=True,
                        thumbnail_bytes=animated_gif,
                    ),
                    EmoteCatalogItem(
                        source="Twitch",
                        emote_id="static-preview-id",
                        name="StaticSmile",
                        image_url="https://example.invalid/static.png",
                        preview_url="https://example.invalid/static.png",
                        animated=False,
                        thumbnail_bytes=static_image.image_bytes,
                    ),
                ]
            )
            assert len(picker._buttons) >= 3
            animated_buttons = [
                button
                for button in picker._buttons
                if button.is_animated_preview
            ]
            # One local managed GIF + one remote animated emote must both play
            # inside the picker before the user selects either one.
            assert len(animated_buttons) >= 2, len(animated_buttons)
            picker_frames = [set() for _ in animated_buttons]
            for button, frames in zip(animated_buttons, picker_frames):
                button._movie.frameChanged.connect(
                    lambda frame, bucket=frames: bucket.add(int(frame))
                )
            picker_loop = QEventLoop()
            QTimer.singleShot(450, picker_loop.quit)
            picker_loop.exec()
            assert all(len(frames) >= 2 for frames in picker_frames), picker_frames

            # Quick selection updates the same persisted D19 setting and the
            # Settings combo through MainWindow's synchronization signal.
            settings.wheel_center_image_combo.setCurrentIndex(0)
            auction._apply_wheel_center_asset(int(asset.id))
            assert db.get_setting(
                WHEEL_CENTER_IMAGE_MEDIA_ID_KEY, ""
            ) == str(asset.id)
            assert settings.wheel_center_image_combo.currentData() == asset.id

            assert auction.wheel_widget._center_image_path == str(managed_path)
            assert auction.wheel_widget._center_image_pixmap is not None
            assert not auction.wheel_widget._center_image_pixmap.isNull()
            assert auction.wheel_widget._center_image_movie is not None
            assert auction.wheel_widget._center_image_movie.isValid()
            observed_frames = set()
            auction.wheel_widget._center_image_movie.frameChanged.connect(
                lambda frame: observed_frames.add(int(frame))
            )
            loop = QEventLoop()
            QTimer.singleShot(450, loop.quit)
            loop.exec()
            assert len(observed_frames) >= 2, observed_frames

            with urllib.request.urlopen(
                window.api.base_url + "/api/wheel", timeout=5
            ) as response:
                api_payload = json.loads(response.read().decode("utf-8"))
            assert api_payload["center_image"]["asset_id"] == asset.id
            assert api_payload["center_image"]["animated"] is True

            with urllib.request.urlopen(
                window.api.base_url + f"/media/{asset.id}", timeout=5
            ) as response:
                media_bytes = response.read()
                media_type = str(response.headers.get("Content-Type") or "")
            assert media_bytes.startswith(b"GIF8")
            assert media_type.startswith("image/gif"), media_type

            auction.wheel_widget.set_center_image_path(None)
            app.processEvents()
            managed_path.unlink()
            missing = db.current_wheel_payload()
            assert missing["center_image"]["enabled"] is False
            assert (
                json.dumps(
                    missing["sectors"], ensure_ascii=False, sort_keys=True
                )
                == sectors_before
            )
        finally:
            window.api.stop()
            window.close()
            app.processEvents()
finally:
    QMessageBox.information = old_info
    QMessageBox.warning = old_warn
    QMessageBox.critical = old_critical

print("D19 SOURCE/DB/UI/API/MEDIA SMOKE: PASS")
