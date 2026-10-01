from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streaming_manager.app_paths import AppPaths
from streaming_manager.constants import WHEEL_SOUNDTRACK_MEDIA_ID_KEY
from streaming_manager.database import Database
from streaming_manager.media import (
    LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES,
    MEDIA_CATEGORY_SOUNDTRACK,
    MEDIA_STORAGE_EXTERNAL,
    MEDIA_STORAGE_MANAGED,
)
from streaming_manager.db.common import utc_now


def add_asset(conn, category, storage_mode, *, managed_name="", external_path="", original_name=""):
    now = utc_now()
    cursor = conn.execute(
        """
        INSERT INTO media_assets(
            category,storage_mode,managed_name,external_path,
            original_name,created_at,updated_at
        ) VALUES(?,?,?,?,?,?,?)
        """,
        (
            category,
            storage_mode,
            managed_name,
            external_path,
            original_name,
            now,
            now,
        ),
    )
    return int(cursor.lastrowid)


with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    root = Path(tmp) / "InOneLine"
    paths = AppPaths.from_root(root)
    paths.ensure_runtime_dirs()

    db = Database(paths.database_path)
    legacy_dir = paths.data_dir / LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES
    soundtrack_dir = paths.data_dir / MEDIA_CATEGORY_SOUNDTRACK

    assert not legacy_dir.exists(), "fresh Database recreated legacy wheel_jingles"

    legacy_dir.mkdir(parents=True)
    soundtrack_dir.mkdir(parents=True, exist_ok=True)

    # Same-name/same-content duplicate: selected wheel asset should re-point to
    # the already-current soundtrack row and the legacy row should disappear.
    (soundtrack_dir / "same.wav").write_bytes(b"SAME")
    (legacy_dir / "same.wav").write_bytes(b"SAME")

    # Same-name/different-content collision: legacy bytes must survive under a
    # deterministic non-overwriting name while keeping the legacy media ID.
    (soundtrack_dir / "collision.wav").write_bytes(b"CURRENT")
    (legacy_dir / "collision.wav").write_bytes(b"LEGACY")

    # Managed unique + manually copied orphan.
    (legacy_dir / "unique.ogg").write_bytes(b"UNIQUE")
    (legacy_dir / "orphan.mp3").write_bytes(b"ORPHAN")

    # Unknown user content is never removed implicitly.
    (legacy_dir / "keep.txt").write_text("KEEP", encoding="utf-8")

    external = Path(tmp) / "external-wheel.wav"
    external.write_bytes(b"EXTERNAL")

    with sqlite3.connect(paths.database_path) as conn:
        conn.row_factory = sqlite3.Row
        current_same_id = add_asset(
            conn,
            MEDIA_CATEGORY_SOUNDTRACK,
            MEDIA_STORAGE_MANAGED,
            managed_name="same.wav",
            original_name="same.wav",
        )
        legacy_same_id = add_asset(
            conn,
            LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES,
            MEDIA_STORAGE_MANAGED,
            managed_name="same.wav",
            original_name="same.wav",
        )
        legacy_collision_id = add_asset(
            conn,
            LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES,
            MEDIA_STORAGE_MANAGED,
            managed_name="collision.wav",
            original_name="collision.wav",
        )
        legacy_unique_id = add_asset(
            conn,
            LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES,
            MEDIA_STORAGE_MANAGED,
            managed_name="unique.ogg",
            original_name="unique.ogg",
        )
        legacy_external_id = add_asset(
            conn,
            LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES,
            MEDIA_STORAGE_EXTERNAL,
            external_path=str(external.resolve()),
            original_name=external.name,
        )
        conn.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (WHEEL_SOUNDTRACK_MEDIA_ID_KEY, str(legacy_same_id)),
        )
        conn.commit()

    migrated = Database(paths.database_path)

    assert migrated.get_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, "") == str(current_same_id)
    assert migrated.get_media_asset(legacy_same_id) is None

    collision = migrated.get_media_asset(legacy_collision_id)
    assert collision is not None
    assert collision.category == MEDIA_CATEGORY_SOUNDTRACK
    assert collision.managed_name == "collision (legacy wheel 2).wav"
    assert (soundtrack_dir / collision.managed_name).read_bytes() == b"LEGACY"
    assert (soundtrack_dir / "collision.wav").read_bytes() == b"CURRENT"

    unique = migrated.get_media_asset(legacy_unique_id)
    assert unique is not None
    assert unique.category == MEDIA_CATEGORY_SOUNDTRACK
    assert unique.managed_name == "unique.ogg"
    assert (soundtrack_dir / "unique.ogg").read_bytes() == b"UNIQUE"

    external_asset = migrated.get_media_asset(legacy_external_id)
    assert external_asset is not None
    assert external_asset.category == MEDIA_CATEGORY_SOUNDTRACK
    assert external_asset.external_path == str(external.resolve())

    orphan = migrated.media_assets_by_filename(MEDIA_CATEGORY_SOUNDTRACK, "orphan.mp3")
    assert len(orphan) == 1
    assert orphan[0].storage_mode == MEDIA_STORAGE_MANAGED
    assert (soundtrack_dir / "orphan.mp3").read_bytes() == b"ORPHAN"

    assert not (legacy_dir / "same.wav").exists()
    assert not (legacy_dir / "collision.wav").exists()
    assert not (legacy_dir / "unique.ogg").exists()
    assert not (legacy_dir / "orphan.mp3").exists()
    assert (legacy_dir / "keep.txt").read_text(encoding="utf-8") == "KEEP"

    with sqlite3.connect(paths.database_path) as conn:
        remaining = conn.execute(
            "SELECT COUNT(*) FROM media_assets WHERE category=?",
            (LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES,),
        ).fetchone()[0]
        assert remaining == 0

    # Second startup must be a no-op and must not recreate legacy storage.
    Database(paths.database_path)
    assert (legacy_dir / "keep.txt").is_file()

    # Once unknown user data is removed manually, the next startup leaves no
    # legacy directory behind.
    (legacy_dir / "keep.txt").unlink()
    legacy_dir.rmdir()
    Database(paths.database_path)
    assert not legacy_dir.exists()

print("LEGACY_WHEEL_JINGLES_MIGRATION=PASS")
