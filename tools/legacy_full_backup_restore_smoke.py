from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import sqlite3
import sys
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streaming_manager.app_paths import AppPaths
from streaming_manager.backup_restore import (
    FULL_BACKUP_FORMAT,
    FULL_BACKUP_FORMAT_VERSION,
    LEGACY_FULL_BACKUP_MANAGED_DIRS,
    apply_staged_full_restore,
    create_sqlite_backup,
    stage_full_restore_candidate,
    validate_full_backup_archive,
)
from streaming_manager.constants import WHEEL_SOUNDTRACK_MEDIA_ID_KEY
from streaming_manager.database import Database
from streaming_manager.db.common import utc_now
from streaming_manager.media import (
    LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES,
    MEDIA_CATEGORY_SOUNDTRACK,
    MEDIA_STORAGE_MANAGED,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    base = Path(tmp)
    root = base / "InOneLine"
    paths = AppPaths.from_root(root)
    paths.ensure_runtime_dirs()
    db = Database(paths.database_path)

    legacy_name = "legacy-wheel.wav"
    legacy_bytes = b"LEGACY-WHEEL-AUDIO"
    now = utc_now()

    # Recreate the persisted state written by 1.0.6: wheel soundtrack metadata
    # pointed at category=wheel_jingles and the file itself lived in that
    # managed directory.
    with closing(sqlite3.connect(paths.database_path)) as conn, conn:
        cursor = conn.execute(
            """
            INSERT INTO media_assets(
                category,storage_mode,managed_name,external_path,
                original_name,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?)
            """,
            (
                LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES,
                MEDIA_STORAGE_MANAGED,
                legacy_name,
                "",
                legacy_name,
                now,
                now,
            ),
        )
        legacy_asset_id = int(cursor.lastrowid)
        conn.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (WHEEL_SOUNDTRACK_MEDIA_ID_KEY, str(legacy_asset_id)),
        )

    work = base / "legacy-work"
    work.mkdir()
    legacy_db = create_sqlite_backup(paths.database_path, work)
    database_bytes = legacy_db.read_bytes()

    archive_path = base / "legacy_1_0_6.iolbackup"
    file_entries = [
        {
            "path": "data/streaming.db",
            "size": len(database_bytes),
            "sha256": sha256_bytes(database_bytes),
        },
        {
            "path": f"data/wheel_jingles/{legacy_name}",
            "size": len(legacy_bytes),
            "sha256": sha256_bytes(legacy_bytes),
        },
    ]
    manifest = {
        "format": FULL_BACKUP_FORMAT,
        "format_version": FULL_BACKUP_FORMAT_VERSION,
        "app_version": "1.0.6",
        "schema_version": 19,
        "created_at_utc": "2026-09-29T00:00:00+00:00",
        "database": "data/streaming.db",
        "managed_directories": list(LEGACY_FULL_BACKUP_MANAGED_DIRS),
        "credentials_protection": "windows-dpapi-current-user",
        "files": file_entries,
    }
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False).encode("utf-8"),
        )
        archive.writestr("data/streaming.db", database_bytes)
        archive.writestr(f"data/wheel_jingles/{legacy_name}", legacy_bytes)

    checked = validate_full_backup_archive(archive_path)
    assert checked["app_version"] == "1.0.6"
    with zipfile.ZipFile(archive_path, "r") as archive:
        assert "data/ui_state.ini" not in archive.namelist()
        legacy_manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        assert "ui_state" not in legacy_manifest
    live_ui_state = paths.data_dir / "ui_state.ini"
    live_ui_state.write_text("LIVE_UI_STATE", encoding="utf-8")
    assert checked["file_count"] == 2

    # Simulate data created by a newer D26 installation after that old backup.
    # A full restore of the old snapshot must not leave this newer soundtrack.
    soundtrack_dir = paths.data_dir / MEDIA_CATEGORY_SOUNDTRACK
    soundtrack_dir.mkdir(parents=True, exist_ok=True)
    (soundtrack_dir / "newer-only.wav").write_bytes(b"NEWER")
    current_asset = db.ensure_managed_media_asset(
        MEDIA_CATEGORY_SOUNDTRACK,
        "newer-only.wav",
        "newer-only.wav",
    )
    db.set_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, str(current_asset.id))

    staged = stage_full_restore_candidate(archive_path, paths.data_dir)
    staged_legacy = Path(staged["staged_dir"]) / "data" / "wheel_jingles" / legacy_name
    assert staged_legacy.read_bytes() == legacy_bytes

    result = apply_staged_full_restore(staged["staged_dir"], root)
    assert result["success"] is True
    assert live_ui_state.read_text(encoding="utf-8") == "LIVE_UI_STATE"
    assert not (soundtrack_dir / "newer-only.wav").exists()
    assert (paths.data_dir / "wheel_jingles" / legacy_name).read_bytes() == legacy_bytes

    # The real application relaunch constructs Database again. That is the
    # compatibility boundary where legacy wheel storage is adopted into D26.
    restored = Database(paths.database_path)

    assert restored.get_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, "") == str(legacy_asset_id)
    asset = restored.get_media_asset(legacy_asset_id)
    assert asset is not None
    assert asset.category == MEDIA_CATEGORY_SOUNDTRACK
    assert asset.storage_mode == MEDIA_STORAGE_MANAGED
    assert asset.managed_name == legacy_name
    assert (soundtrack_dir / legacy_name).read_bytes() == legacy_bytes
    assert not (paths.data_dir / "wheel_jingles").exists()

    with closing(sqlite3.connect(paths.database_path)) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM media_assets WHERE category=?",
            (LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES,),
        ).fetchone()[0]
        assert count == 0

print("LEGACY_1_0_6_FULL_BACKUP_RESTORE=PASS")
