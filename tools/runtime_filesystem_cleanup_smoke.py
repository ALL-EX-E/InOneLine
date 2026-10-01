from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import os
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streaming_manager.app_paths import AppPaths
from streaming_manager.backup_restore import cleanup_stale_runtime_artifacts


LEGACY_TEMPLATE = (
    "НАЗВАНИЕ ИГРЫ;ДАТА ВЫХОДА;БАЛЛЫ;КООП/НЕ КООП;СТАТУС;ОТЗЫВ\r\n"
    "Control;27.08.2019;0;НЕ КООП;НЕ ИГРАЛ;\r\n"
).encode("utf-8")


def age(path: Path, seconds: float) -> None:
    stamp = time.time() - seconds
    os.utime(path, (stamp, stamp))


with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    root = Path(tmp) / "InOneLine"
    paths = AppPaths.from_root(root)
    paths.ensure_runtime_dirs()

    old_file = paths.data_dir / ".restore_pending_old.db"
    old_file.write_bytes(b"copy")
    age(old_file, 48 * 60 * 60)

    fresh_file = paths.data_dir / ".restore_pending_fresh.db"
    fresh_file.write_bytes(b"copy")

    old_full_stage = paths.data_dir / ".full_restore_pending_old"
    old_full_stage.mkdir()
    (old_full_stage / "copy.bin").write_bytes(b"copy")
    age(old_full_stage / "copy.bin", 48 * 60 * 60)
    age(old_full_stage, 48 * 60 * 60)

    fresh_full_stage = paths.data_dir / ".full_restore_pending_fresh"
    fresh_full_stage.mkdir()

    old_backup_work = paths.data_dir / ".full_backup_create_old"
    old_backup_work.mkdir()
    age(old_backup_work, 48 * 60 * 60)

    old_safety_work = paths.backups_dir / ".full_restore_safety_work_old"
    old_safety_work.mkdir()
    age(old_safety_work, 48 * 60 * 60)

    old_error = paths.backups_dir / ".backup_old.error.txt"
    old_error.write_text("error", encoding="utf-8")
    age(old_error, 48 * 60 * 60)

    old_result_tmp = paths.data_dir / "restore_result.json.tmp"
    old_result_tmp.write_text("partial", encoding="utf-8")
    age(old_result_tmp, 48 * 60 * 60)

    # Recovery material must never be treated as disposable cleanup.
    rollback = paths.backups_dir / ".full_restore_rollback_old"
    rollback.mkdir()
    (rollback / "streaming.db").write_bytes(b"recovery")
    age(rollback / "streaming.db", 48 * 60 * 60)
    age(rollback, 48 * 60 * 60)

    replacement_db = paths.data_dir / ".full_restore_database_old.db"
    replacement_db.write_bytes(b"recovery")
    age(replacement_db, 48 * 60 * 60)

    rollback_db = paths.data_dir / ".full_restore_db_rollback_old.db"
    rollback_db.write_bytes(b"recovery")
    age(rollback_db, 48 * 60 * 60)

    template = paths.data_dir / "import_template.csv"
    template.write_bytes(LEGACY_TEMPLATE)

    result = cleanup_stale_runtime_artifacts(root)

    assert not old_file.exists()
    assert fresh_file.exists()
    assert not old_full_stage.exists()
    assert fresh_full_stage.exists()
    assert not old_backup_work.exists()
    assert not old_safety_work.exists()
    assert not old_error.exists()
    assert not old_result_tmp.exists()

    assert rollback.is_dir()
    assert replacement_db.is_file()
    assert rollback_db.is_file()

    assert not template.exists()
    assert result["removed_files"] >= 3, result
    assert result["removed_directories"] >= 3, result
    assert result["errors"] == 0, result

    # User-edited former template is preserved.
    template.write_text("МОЙ ШАБЛОН\n", encoding="utf-8")
    result = cleanup_stale_runtime_artifacts(root, minimum_age_seconds=0)
    assert template.read_text(encoding="utf-8") == "МОЙ ШАБЛОН\n"
    assert result["preserved_user_files"] == 1, result

print("RUNTIME_FILESYSTEM_CLEANUP=PASS")
