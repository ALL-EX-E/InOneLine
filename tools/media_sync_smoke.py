from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streaming_manager.database import Database
from streaming_manager.media import (
    MEDIA_CATEGORY_MUSIC,
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
    MEDIA_CATEGORY_SOUNDTRACK,
    MEDIA_STORAGE_EXTERNAL,
    MEDIA_STORAGE_MANAGED,
    managed_media_directory,
)


def main() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        db = Database(root / "streaming.db")

        music_dir = managed_media_directory(root, MEDIA_CATEGORY_MUSIC)
        for index in range(20):
            (music_dir / f"Track {index:02d}.wav").write_bytes(
                f"track-{index}".encode("ascii")
            )
        (music_dir / "ignore.txt").write_text("not media", encoding="utf-8")

        existing = db.ensure_managed_media_asset(
            MEDIA_CATEGORY_MUSIC,
            "Track 00.wav",
            "Preserved original label.wav",
        )
        stale_music = db.ensure_managed_media_asset(
            MEDIA_CATEGORY_MUSIC,
            "stale.wav",
            "stale.wav",
        )

        external_path = root / "external.wav"
        external_path.write_bytes(b"external")
        external = db.register_external_media_asset(
            MEDIA_CATEGORY_MUSIC,
            external_path,
        )

        soundtrack_dir = managed_media_directory(root, MEDIA_CATEGORY_SOUNDTRACK)
        for index in range(3):
            (soundtrack_dir / f"Soundtrack {index:02d}.ogg").write_bytes(
                f"soundtrack-{index}".encode("ascii")
            )
        stale_soundtrack = db.ensure_managed_media_asset(
            MEDIA_CATEGORY_SOUNDTRACK,
            "stale.ogg",
            "stale.ogg",
        )

        overlay_stale = db.ensure_managed_media_asset(
            MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
            "missing-but-preserved.png",
            "missing-but-preserved.png",
        )

        original_connect = db.connect
        counter = {"value": 0}

        @contextmanager
        def counted_connect():
            counter["value"] += 1
            with original_connect() as conn:
                yield conn

        db.connect = counted_connect  # type: ignore[method-assign]

        counter["value"] = 0
        music_assets = db.sync_managed_media_category(MEDIA_CATEGORY_MUSIC)
        assert counter["value"] == 1, (
            "Music sync must use exactly one SQLite connection, got "
            f"{counter['value']}"
        )

        managed_music = [
            asset
            for asset in music_assets
            if asset.storage_mode == MEDIA_STORAGE_MANAGED
        ]
        assert len(managed_music) == 20
        assert {asset.managed_name for asset in managed_music} == {
            f"Track {index:02d}.wav" for index in range(20)
        }
        assert all(asset.id != stale_music.id for asset in music_assets)
        assert any(
            asset.id == external.id
            and asset.storage_mode == MEDIA_STORAGE_EXTERNAL
            for asset in music_assets
        )
        preserved = next(asset for asset in music_assets if asset.id == existing.id)
        assert preserved.original_name == "Preserved original label.wav"
        assert not any(asset.managed_name == "ignore.txt" for asset in music_assets)

        first_ids = {
            (asset.storage_mode, asset.managed_name, asset.external_path): asset.id
            for asset in music_assets
        }
        counter["value"] = 0
        second_music_assets = db.sync_managed_media_category(MEDIA_CATEGORY_MUSIC)
        assert counter["value"] == 1
        second_ids = {
            (asset.storage_mode, asset.managed_name, asset.external_path): asset.id
            for asset in second_music_assets
        }
        assert second_ids == first_ids, "Repeated sync must be idempotent"

        counter["value"] = 0
        soundtrack_assets = db.sync_managed_media_category(
            MEDIA_CATEGORY_SOUNDTRACK
        )
        assert counter["value"] == 1
        assert all(asset.id != stale_soundtrack.id for asset in soundtrack_assets)
        assert {
            asset.managed_name
            for asset in soundtrack_assets
            if asset.storage_mode == MEDIA_STORAGE_MANAGED
        } == {f"Soundtrack {index:02d}.ogg" for index in range(3)}

        counter["value"] = 0
        overlay_assets = db.sync_managed_media_category(
            MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
        )
        assert counter["value"] == 1
        assert any(
            asset.id == overlay_stale.id
            for asset in overlay_assets
        ), "Non-D26 categories must preserve established missing-file recovery rows"

    print("MEDIA_SYNC_SINGLE_TRANSACTION=PASS")


if __name__ == "__main__":
    main()
