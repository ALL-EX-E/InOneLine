from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())

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
from streaming_manager.remote_image import (
    load_local_image_as_png,
    resolve_external_image_source,
)
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
        }
        sectors_before = json.dumps(
            before["sectors"], ensure_ascii=False, sort_keys=True
        )

        local_source = Path(root) / "source.png"
        write_test_png(local_source)
        normalized = load_local_image_as_png(str(local_source))
        assert normalized.startswith(b"\x89PNG\r\n\x1a\n")

        media_dir = managed_media_directory(
            db.path.parent, MEDIA_CATEGORY_WHEEL_CENTER_ICONS
        )
        media_dir.mkdir(parents=True, exist_ok=True)
        managed_path = media_dir / "candidate-center.png"
        managed_path.write_bytes(normalized)
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

        window = MainWindow(db, paths)
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
            assert auction.wheel_widget._center_image_pixmap is not None
            assert not auction.wheel_widget._center_image_pixmap.isNull()

            with urllib.request.urlopen(
                window.api.base_url + "/api/wheel", timeout=5
            ) as response:
                api_payload = json.loads(response.read().decode("utf-8"))
            assert api_payload["center_image"]["asset_id"] == asset.id

            with urllib.request.urlopen(
                window.api.base_url + f"/media/{asset.id}", timeout=5
            ) as response:
                media_bytes = response.read()
            assert media_bytes.startswith(b"\x89PNG\r\n\x1a\n")

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
