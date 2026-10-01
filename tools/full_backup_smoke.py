from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import sys
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streaming_manager.app_paths import AppPaths
from streaming_manager.backup_restore import (
    RestoreValidationError,
    apply_staged_full_restore,
    create_full_backup_archive,
    create_sqlite_backup,
    stage_full_restore_candidate,
    validate_full_backup_archive,
    validate_full_backup_destination,
    validate_streaming_manager_backup,
)
from streaming_manager.database import Database


with TemporaryDirectory() as tmp:
    base = Path(tmp)
    root = base / "InOneLine"
    paths = AppPaths.from_root(root)
    paths.ensure_runtime_dirs()
    Database(paths.database_path)

    with closing(sqlite3.connect(paths.database_path)) as conn, conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(games)")}
        assert "sm_points" in cols
        conn.execute(
            "INSERT INTO games(title, release_date, sm_points, coop, status, review, archived, created_at, updated_at) "
            "VALUES(?, ?, ?, ?, ?, ?, 0, datetime('now'), datetime('now'))",
            ("FULL BACKUP MARKER", None, 123, 0, "not_played", ""),
        )

    payloads = {
        "credentials/cred_test.bin": b"dpapi-ciphertext-placeholder",
        "music/theme.wav": b"MUSIC-ORIGINAL",
        "soundtrack/event.wav": b"SOUNDTRACK-ORIGINAL",
        "wheel_jingles/jingle.wav": b"JINGLE-ORIGINAL",
        "wheel_center_icons/icon.png": b"ICON-ORIGINAL",
        "overlay_backgrounds/bg.png": b"BG-ORIGINAL",
    }
    for rel, content in payloads.items():
        path = paths.data_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    external_dir = base / "ExternalBackups"
    external_dir.mkdir()
    dest = external_dir / "backup.iolbackup"

    try:
        validate_full_backup_destination(root / "bad.iolbackup", root)
        raise AssertionError("inside-root destination accepted")
    except ValueError:
        pass

    snap_dir = root / ".test_snapshot"
    snap_dir.mkdir()
    snapshot = create_sqlite_backup(paths.database_path, snap_dir)
    create_full_backup_archive(
        snapshot,
        paths.data_dir,
        dest,
        app_version="1.0.8",
        installation_root=root,
    )

    checked = validate_full_backup_archive(dest)
    assert checked["file_count"] == 7, checked
    assert checked["credentials_present"] is True

    with zipfile.ZipFile(dest) as archive:
        names = set(archive.namelist())
        assert "data/streaming.db" in names
        assert "data/soundtrack/event.wav" in names
        assert not any(name.startswith("logs/") or name.startswith("backups/") for name in names)

    with closing(sqlite3.connect(paths.database_path)) as conn, conn:
        conn.execute("UPDATE games SET title='MUTATED' WHERE title='FULL BACKUP MARKER'")
    (paths.data_dir / "music/theme.wav").write_bytes(b"MUTATED")
    (paths.data_dir / "soundtrack/event.wav").write_bytes(b"MUTATED")
    (paths.data_dir / "overlay_backgrounds/new-only.txt").write_text("remove me", encoding="utf-8")

    staged = stage_full_restore_candidate(dest, paths.data_dir)
    result = apply_staged_full_restore(staged["staged_dir"], root)
    assert result["success"] and result["restore_kind"] == "full"

    with closing(sqlite3.connect(paths.database_path)) as conn, conn:
        title = conn.execute("SELECT title FROM games WHERE sm_points=123").fetchone()[0]
        assert title == "FULL BACKUP MARKER", title

    for rel, content in payloads.items():
        assert (paths.data_dir / rel).read_bytes() == content
    assert not (paths.data_dir / "overlay_backgrounds/new-only.txt").exists()
    assert Path(result["safety_backup"]).is_file()
    validate_full_backup_archive(result["safety_backup"])
    validate_streaming_manager_backup(paths.database_path)

    tampered = external_dir / "tampered.iolbackup"
    with zipfile.ZipFile(dest, "r") as src, zipfile.ZipFile(tampered, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "data/music/theme.wav":
                data += b"X"
            dst.writestr(info.filename, data)

    try:
        validate_full_backup_archive(tampered)
        raise AssertionError("tampered archive accepted")
    except RestoreValidationError:
        pass

print("1.0.8 FULL BACKUP/RESTORE REGRESSION SMOKE: OK")
