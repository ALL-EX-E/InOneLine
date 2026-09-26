from __future__ import annotations

import ctypes
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .app_paths import AppPaths
from .constants import SCHEMA_VERSION


class RestoreValidationError(ValueError):
    """Selected file is not a safe/compatible Streaming Manager backup."""


_REQUIRED_GAME_COLUMNS = {
    "id",
    "title",
    "release_date",
    "coop",
    "status",
    "review",
    "archived",
    "created_at",
    "updated_at",
}

FULL_BACKUP_FORMAT = "InOneLineFullBackup"
FULL_BACKUP_FORMAT_VERSION = 1
FULL_BACKUP_EXTENSION = ".iolbackup"
FULL_BACKUP_MANAGED_DIRS = (
    "credentials",
    "overlay_backgrounds",
    "music",
    "wheel_jingles",
    "wheel_center_icons",
)
_FULL_BACKUP_MANIFEST = "manifest.json"
_FULL_BACKUP_DATABASE = "data/streaming.db"
_FULL_BACKUP_MANIFEST_MAX_BYTES = 2 * 1024 * 1024


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_archive_name(name: str) -> PurePosixPath:
    if not name or "\\" in name:
        raise RestoreValidationError(f"Некорректный путь внутри полной резервной копии: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise RestoreValidationError(f"Небезопасный путь внутри полной резервной копии: {name!r}")
    return path


def _is_allowed_full_backup_member(name: str) -> bool:
    if name == _FULL_BACKUP_DATABASE:
        return True
    return any(name.startswith(f"data/{directory}/") for directory in FULL_BACKUP_MANAGED_DIRS)


def _path_is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate_full_backup_destination(
    destination: str | Path,
    installation_root: str | Path,
) -> Path:
    """Require uninstall-surviving full backups to live outside InOneLine root."""
    target = Path(destination).resolve()
    root = Path(installation_root).resolve()
    if _path_is_inside(target, root):
        raise ValueError(
            "Полную резервную копию нельзя сохранять внутри папки InOneLine, "
            "потому что при полном удалении программы эта папка будет удалена. "
            "Выберите другую папку или диск."
        )
    return target


def _zip_info_is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(mode)


def _full_backup_manifest_and_infos(
    archive: zipfile.ZipFile,
) -> tuple[dict[str, Any], dict[str, zipfile.ZipInfo]]:
    infos = archive.infolist()
    names = [info.filename for info in infos]
    if len(names) != len(set(names)):
        raise RestoreValidationError("В полной резервной копии есть дублирующиеся ZIP-пути.")
    for info in infos:
        _safe_archive_name(info.filename)
        if info.flag_bits & 0x1:
            raise RestoreValidationError("Зашифрованные ZIP-элементы не поддерживаются.")
        if _zip_info_is_symlink(info):
            raise RestoreValidationError("Символические ссылки в полной резервной копии запрещены.")

    by_name = {info.filename: info for info in infos}
    manifest_info = by_name.get(_FULL_BACKUP_MANIFEST)
    if manifest_info is None or manifest_info.is_dir():
        raise RestoreValidationError("В файле отсутствует manifest.json полной резервной копии.")
    if manifest_info.file_size > _FULL_BACKUP_MANIFEST_MAX_BYTES:
        raise RestoreValidationError("manifest.json полной резервной копии слишком велик.")
    try:
        manifest = json.loads(archive.read(manifest_info).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError, OSError, RuntimeError) as exc:
        raise RestoreValidationError("manifest.json повреждён или имеет неверный формат.") from exc
    if not isinstance(manifest, dict):
        raise RestoreValidationError("manifest.json должен содержать JSON-объект.")
    if manifest.get("format") != FULL_BACKUP_FORMAT:
        raise RestoreValidationError("Выбранный файл не является полной резервной копией In one line.")
    if manifest.get("format_version") != FULL_BACKUP_FORMAT_VERSION:
        raise RestoreValidationError(
            "Версия формата полной резервной копии не поддерживается текущей программой."
        )
    if manifest.get("database") != _FULL_BACKUP_DATABASE:
        raise RestoreValidationError("manifest.json содержит неверный путь рабочей базы.")
    if manifest.get("managed_directories") != list(FULL_BACKUP_MANAGED_DIRS):
        raise RestoreValidationError("manifest.json содержит неизвестный набор managed-каталогов.")

    raw_files = manifest.get("files")
    if not isinstance(raw_files, list):
        raise RestoreValidationError("manifest.json не содержит корректный список файлов.")
    manifest_files: dict[str, dict[str, Any]] = {}
    for item in raw_files:
        if not isinstance(item, dict):
            raise RestoreValidationError("Некорректная запись файла в manifest.json.")
        name = str(item.get("path", ""))
        _safe_archive_name(name)
        if not _is_allowed_full_backup_member(name):
            raise RestoreValidationError(f"Недопустимый файл в полной резервной копии: {name}")
        if name in manifest_files:
            raise RestoreValidationError(f"Дублирующийся файл в manifest.json: {name}")
        sha256 = str(item.get("sha256", "")).lower()
        size = item.get("size")
        if len(sha256) != 64 or any(ch not in "0123456789abcdef" for ch in sha256):
            raise RestoreValidationError(f"Некорректный SHA-256 в manifest.json: {name}")
        if not isinstance(size, int) or size < 0:
            raise RestoreValidationError(f"Некорректный размер в manifest.json: {name}")
        manifest_files[name] = {"path": name, "sha256": sha256, "size": size}

    actual_files = {
        name for name, info in by_name.items()
        if name != _FULL_BACKUP_MANIFEST and not info.is_dir()
    }
    if actual_files != set(manifest_files):
        missing = sorted(set(manifest_files) - actual_files)
        extra = sorted(actual_files - set(manifest_files))
        raise RestoreValidationError(
            "Состав ZIP не совпадает с manifest.json. "
            f"Отсутствуют: {missing or 'нет'}; лишние: {extra or 'нет'}."
        )
    if _FULL_BACKUP_DATABASE not in actual_files:
        raise RestoreValidationError("Полная резервная копия не содержит data/streaming.db.")

    for name, expected in manifest_files.items():
        info = by_name[name]
        if info.file_size != expected["size"]:
            raise RestoreValidationError(f"Размер файла не совпадает с manifest.json: {name}")
    return manifest, by_name


def validate_full_backup_archive(path: str | Path) -> dict[str, Any]:
    """Validate the full .iolbackup container without modifying user data."""
    source = Path(path)
    if not source.is_file():
        raise RestoreValidationError("Выбранная полная резервная копия не существует или недоступна.")
    try:
        with zipfile.ZipFile(source, "r") as archive:
            manifest, infos = _full_backup_manifest_and_infos(archive)
            total = 0
            for item in manifest["files"]:
                name = item["path"]
                digest = hashlib.sha256()
                read_size = 0
                with archive.open(infos[name], "r") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        read_size += len(chunk)
                        digest.update(chunk)
                if read_size != item["size"] or digest.hexdigest() != item["sha256"]:
                    raise RestoreValidationError(f"Контрольная сумма не совпадает: {name}")
                total += read_size
    except RestoreValidationError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise RestoreValidationError("Файл .iolbackup повреждён или не читается.") from exc

    return {
        "path": str(source.resolve()),
        "app_version": str(manifest.get("app_version", "")),
        "schema_version": manifest.get("schema_version"),
        "created_at_utc": str(manifest.get("created_at_utc", "")),
        "file_count": len(manifest["files"]),
        "payload_bytes": total,
        "credentials_present": any(
            item["path"].startswith("data/credentials/") for item in manifest["files"]
        ),
    }


def create_full_backup_archive(
    database_snapshot: str | Path,
    data_dir: str | Path,
    destination: str | Path,
    *,
    app_version: str,
    installation_root: str | Path | None = None,
    allow_inside_installation: bool = False,
) -> dict[str, Any]:
    """Create an uninstall-surviving full user-data backup container."""
    snapshot = Path(database_snapshot).resolve()
    data_root = Path(data_dir).resolve()
    target = Path(destination).resolve()
    if installation_root is not None and not allow_inside_installation:
        target = validate_full_backup_destination(target, installation_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix.lower() != FULL_BACKUP_EXTENSION:
        target = target.with_name(target.name + FULL_BACKUP_EXTENSION)
    validation = validate_streaming_manager_backup(snapshot)

    files: list[tuple[Path, str]] = [(snapshot, _FULL_BACKUP_DATABASE)]
    for directory in FULL_BACKUP_MANAGED_DIRS:
        source_dir = data_root / directory
        if not source_dir.is_dir():
            continue
        for item in sorted(source_dir.rglob("*"), key=lambda value: value.as_posix().lower()):
            if item.is_file():
                relative = item.relative_to(source_dir).as_posix()
                files.append((item, f"data/{directory}/{relative}"))

    manifest_files = [
        {
            "path": archive_name,
            "size": source.stat().st_size,
            "sha256": _sha256_file(source),
        }
        for source, archive_name in files
    ]
    manifest = {
        "format": FULL_BACKUP_FORMAT,
        "format_version": FULL_BACKUP_FORMAT_VERSION,
        "app_version": str(app_version),
        "schema_version": validation["schema_version"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "database": _FULL_BACKUP_DATABASE,
        "managed_directories": list(FULL_BACKUP_MANAGED_DIRS),
        "credentials_protection": "windows-dpapi-current-user",
        "files": manifest_files,
    }

    temporary = target.with_name(target.name + ".tmp")
    temporary.unlink(missing_ok=True)
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
            allowZip64=True,
        ) as archive:
            archive.writestr(
                _FULL_BACKUP_MANIFEST,
                json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
            )
            for source, archive_name in files:
                archive.write(source, archive_name)
        checked = validate_full_backup_archive(temporary)
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    return {
        **checked,
        "path": str(target),
        "database_schema": validation["schema_label"],
        "games_count": validation["games_count"],
    }


def stage_full_restore_candidate(
    source_path: str | Path,
    data_dir: str | Path,
) -> dict[str, Any]:
    """Validate and extract a full backup into a private same-volume staging tree."""
    source = Path(source_path).resolve()
    archive_validation = validate_full_backup_archive(source)
    data_root = Path(data_dir).resolve()
    data_root.mkdir(parents=True, exist_ok=True)
    stage_root = data_root / f".full_restore_pending_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    stage_root.mkdir(parents=True, exist_ok=False)
    try:
        with zipfile.ZipFile(source, "r") as archive:
            manifest, infos = _full_backup_manifest_and_infos(archive)
            for directory in FULL_BACKUP_MANAGED_DIRS:
                (stage_root / "data" / directory).mkdir(parents=True, exist_ok=True)
            for item in manifest["files"]:
                name = item["path"]
                relative = _safe_archive_name(name)
                target = stage_root.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                written = 0
                with archive.open(infos[name], "r") as src, target.open("wb") as dst:
                    for chunk in iter(lambda: src.read(1024 * 1024), b""):
                        dst.write(chunk)
                        digest.update(chunk)
                        written += len(chunk)
                if written != item["size"] or digest.hexdigest() != item["sha256"]:
                    raise RestoreValidationError(f"Файл изменился или повреждён при подготовке: {name}")
        db_validation = validate_streaming_manager_backup(stage_root / _FULL_BACKUP_DATABASE)
        schema_from_manifest = manifest.get("schema_version")
        if schema_from_manifest is not None and schema_from_manifest != db_validation["schema_version"]:
            raise RestoreValidationError(
                "schema_version в manifest.json не совпадает со схемой резервной базы."
            )
        return {
            "source_path": str(source),
            "staged_dir": str(stage_root),
            "archive_validation": archive_validation,
            "database_validation": db_validation,
        }
    except Exception:
        shutil.rmtree(stage_root, ignore_errors=True)
        raise


def _prune_full_restore_safety_backups(backup_dir: Path, keep: int = 10) -> None:
    files = sorted(
        backup_dir.glob("full_restore_safety_*.iolbackup"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for path in files[max(0, int(keep)):]:
        path.unlink(missing_ok=True)


def _create_full_restore_safety_backup(paths: AppPaths) -> Path:
    paths.backups_dir.mkdir(parents=True, exist_ok=True)
    work = paths.backups_dir / f".full_restore_safety_work_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    work.mkdir(parents=True, exist_ok=False)
    try:
        snapshot = create_sqlite_backup(paths.database_path, work)
        target = paths.backups_dir / (
            f"full_restore_safety_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')}.iolbackup"
        )
        from .constants import APP_VERSION
        create_full_backup_archive(
            snapshot,
            paths.data_dir,
            target,
            app_version=APP_VERSION,
            installation_root=paths.root_dir,
            allow_inside_installation=True,
        )
        _prune_full_restore_safety_backups(paths.backups_dir, 10)
        return target
    finally:
        shutil.rmtree(work, ignore_errors=True)


def apply_staged_full_restore(
    staged_dir: str | Path,
    project_dir: str | Path,
) -> dict[str, Any]:
    """Replace DB + app-owned credentials/managed media with rollback protection."""
    paths = AppPaths.from_root(project_dir)
    stage_root = Path(staged_dir).resolve()
    stage_data = stage_root / "data"
    staged_database = stage_data / "streaming.db"
    validation = validate_streaming_manager_backup(staged_database)
    if not paths.database_path.is_file():
        raise RuntimeError(f"Текущая база не найдена: {paths.database_path}")

    safety_backup = _create_full_restore_safety_backup(paths)
    rollback_root = paths.backups_dir / f".full_restore_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    rollback_root.mkdir(parents=True, exist_ok=False)
    rollback_database = create_sqlite_backup(paths.database_path, rollback_root)
    moved_directories: list[str] = []
    replacement_database = paths.data_dir / f".full_restore_database_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.db"

    try:
        for directory in FULL_BACKUP_MANAGED_DIRS:
            current = paths.data_dir / directory
            old = rollback_root / directory
            if current.exists():
                shutil.move(str(current), str(old))
                moved_directories.append(directory)

        shutil.copy2(staged_database, replacement_database)
        os.replace(replacement_database, paths.database_path)
        for sidecar in _sidecar_paths(paths.database_path):
            sidecar.unlink(missing_ok=True)

        for directory in FULL_BACKUP_MANAGED_DIRS:
            staged = stage_data / directory
            target = paths.data_dir / directory
            if target.exists():
                shutil.rmtree(target)
            if staged.exists():
                shutil.move(str(staged), str(target))
            else:
                target.mkdir(parents=True, exist_ok=True)

        final_validation = validate_streaming_manager_backup(paths.database_path)
        return {
            "success": True,
            "restore_kind": "full",
            "safety_backup": str(safety_backup),
            "restored_schema": validation["schema_label"],
            "restored_games": validation["games_count"],
            "final_validation": final_validation,
            "rollback_used": False,
        }
    except Exception as exc:
        rollback_error: Exception | None = None
        try:
            replacement_database.unlink(missing_ok=True)
            for directory in FULL_BACKUP_MANAGED_DIRS:
                target = paths.data_dir / directory
                if target.exists():
                    shutil.rmtree(target)
                old = rollback_root / directory
                if old.exists():
                    shutil.move(str(old), str(target))
            rollback_stage = paths.data_dir / f".full_restore_db_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.db"
            shutil.copy2(rollback_database, rollback_stage)
            os.replace(rollback_stage, paths.database_path)
            for sidecar in _sidecar_paths(paths.database_path):
                sidecar.unlink(missing_ok=True)
            validate_streaming_manager_backup(paths.database_path)
        except Exception as nested:
            rollback_error = nested
        if rollback_error is not None:
            raise RuntimeError(
                "Полное восстановление завершилось ошибкой, и автоматический rollback тоже не удался. "
                f"Полная safety-копия сохранена здесь: {safety_backup}.\n\n"
                f"Ошибка восстановления: {exc}\nОшибка rollback: {rollback_error}"
            ) from rollback_error
        raise RuntimeError(
            "Полное восстановление завершилось ошибкой; исходное состояние автоматически возвращено. "
            f"Полная safety-копия сохранена здесь: {safety_backup}.\n\n{exc}"
        ) from exc
    finally:
        replacement_database.unlink(missing_ok=True)
        shutil.rmtree(stage_root, ignore_errors=True)
        shutil.rmtree(rollback_root, ignore_errors=True)



def _open_read_only(path: Path) -> sqlite3.Connection:
    uri = path.resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=10)


def _check_result_is_ok(rows: list[tuple[Any, ...]], label: str) -> None:
    values = [str(row[0]) for row in rows]
    if values != ["ok"]:
        preview = "; ".join(values[:5]) or "нет результата"
        raise RestoreValidationError(f"{label} не пройден: {preview}")


def validate_streaming_manager_backup(path: str | Path) -> dict[str, Any]:
    """Validate a restore candidate without modifying it.

    Older recognizable Streaming Manager databases are accepted and will be
    migrated by the normal Database startup path after restore. A database from
    a newer schema is rejected because the running program cannot safely infer
    how to downgrade it.
    """
    candidate = Path(path)
    if not candidate.is_file():
        raise RestoreValidationError("Выбранный файл не существует или недоступен.")
    if candidate.stat().st_size < 100:
        raise RestoreValidationError("Выбранный файл слишком мал и не похож на базу SQLite.")

    conn: sqlite3.Connection | None = None
    try:
        conn = _open_read_only(candidate)
        conn.row_factory = sqlite3.Row

        quick_rows = conn.execute("PRAGMA quick_check").fetchall()
        _check_result_is_ok(quick_rows, "PRAGMA quick_check")

        integrity_rows = conn.execute("PRAGMA integrity_check").fetchall()
        _check_result_is_ok(integrity_rows, "PRAGMA integrity_check")

        foreign_rows = conn.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_rows:
            first = foreign_rows[0]
            raise RestoreValidationError(
                "PRAGMA foreign_key_check обнаружил нарушение внешних связей: "
                + ", ".join(str(value) for value in first)
            )

        tables = {
            str(row[0])
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "games" not in tables:
            raise RestoreValidationError(
                "В файле нет основной таблицы games. Это не база In one line."
            )

        game_columns = {
            str(row[1]) for row in conn.execute("PRAGMA table_info(games)").fetchall()
        }
        missing = sorted(_REQUIRED_GAME_COLUMNS - game_columns)
        if missing:
            raise RestoreValidationError(
                "Структура games несовместима с In one line. "
                "Отсутствуют поля: " + ", ".join(missing)
            )
        if "sm_points" not in game_columns and "amount_kopecks" not in game_columns:
            raise RestoreValidationError(
                "Структура games несовместима с In one line. "
                "Нет ни нового поля sm_points, ни legacy-поля amount_kopecks."
            )

        schema_version: int | None = None
        if "schema_meta" in tables:
            row = conn.execute(
                "SELECT value FROM schema_meta WHERE key='schema_version'"
            ).fetchone()
            if row is not None:
                try:
                    schema_version = int(str(row[0]))
                except (TypeError, ValueError) as exc:
                    raise RestoreValidationError(
                        "Некорректное значение schema_version в резервной копии."
                    ) from exc
                if schema_version < 1:
                    raise RestoreValidationError(
                        f"Некорректная версия схемы: {schema_version}."
                    )
                if schema_version > SCHEMA_VERSION:
                    raise RestoreValidationError(
                        "Резервная копия создана более новой версией In one line "
                        f"(schema {schema_version}), а текущая программа поддерживает "
                        f"schema {SCHEMA_VERSION}. Восстановление запрещено."
                    )

        games_count = int(conn.execute("SELECT COUNT(*) FROM games").fetchone()[0])
        return {
            "path": str(candidate.resolve()),
            "schema_version": schema_version,
            "schema_label": str(schema_version) if schema_version is not None else "legacy",
            "games_count": games_count,
            "quick_check": "ok",
            "integrity_check": "ok",
            "foreign_key_violations": 0,
        }
    except RestoreValidationError:
        raise
    except sqlite3.DatabaseError as exc:
        raise RestoreValidationError(
            "Файл не является исправной SQLite-базой или повреждён: " + str(exc)
        ) from exc
    except OSError as exc:
        raise RestoreValidationError("Не удалось прочитать выбранный файл: " + str(exc)) from exc
    finally:
        if conn is not None:
            conn.close()


def create_sqlite_backup(source_path: str | Path, backup_dir: str | Path) -> Path:
    """Create a consistent SQLite snapshot using SQLite's online backup API."""
    source = Path(source_path)
    destination_dir = Path(backup_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    target = destination_dir / f"streaming_{stamp}.db"

    src = sqlite3.connect(source, timeout=10)
    dst = sqlite3.connect(target, timeout=10)
    try:
        src.backup(dst)
        dst.commit()
    finally:
        try:
            dst.close()
        finally:
            src.close()
    return target


def prune_backup_files(backup_dir: str | Path, keep: int = 30) -> None:
    files = sorted(
        Path(backup_dir).glob("streaming_*.db"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for path in files[max(0, int(keep)):]:
        path.unlink(missing_ok=True)


def stage_restore_candidate(
    source_path: str | Path,
    data_dir: str | Path,
) -> dict[str, Any]:
    """Validate and copy a candidate to a private same-volume staging file."""
    source = Path(source_path).resolve()
    validation = validate_streaming_manager_backup(source)
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    staged = data_path / f".restore_pending_{stamp}.db"
    try:
        shutil.copy2(source, staged)
        staged_validation = validate_streaming_manager_backup(staged)
    except Exception:
        staged.unlink(missing_ok=True)
        raise
    return {
        "source_path": str(source),
        "staged_path": str(staged),
        "validation": staged_validation,
    }


def _sidecar_paths(database_path: Path) -> tuple[Path, Path]:
    return (
        Path(str(database_path) + "-wal"),
        Path(str(database_path) + "-shm"),
    )


def apply_staged_restore(
    staged_path: str | Path,
    target_database: str | Path,
    backup_dir: str | Path,
    *,
    keep_backups: int = 30,
) -> dict[str, Any]:
    """Apply a staged restore after the application has completely stopped.

    The current database is backed up *before* replacement. Replacement uses
    os.replace on a staging file on the same volume. Any failure after the
    replacement triggers an immediate rollback from the freshly created safety
    backup.
    """
    staged = Path(staged_path)
    target = Path(target_database)
    backup_path: Path | None = None
    replaced = False

    validation = validate_streaming_manager_backup(staged)
    if not target.is_file():
        raise RuntimeError(f"Текущая база не найдена: {target}")

    try:
        backup_path = create_sqlite_backup(target, backup_dir)
        # A safety copy that cannot itself pass validation is not a valid safety net.
        validate_streaming_manager_backup(backup_path)
        prune_backup_files(backup_dir, keep_backups)

        # No Streaming Manager process is alive here. Keeping the old sidecars
        # until os.replace succeeds means a failed replacement cannot strand the
        # original main database without its WAL state.
        os.replace(staged, target)
        replaced = True
        for sidecar in _sidecar_paths(target):
            sidecar.unlink(missing_ok=True)

        restored_validation = validate_streaming_manager_backup(target)
        return {
            "success": True,
            "safety_backup": str(backup_path),
            "restored_schema": validation["schema_label"],
            "restored_games": validation["games_count"],
            "final_validation": restored_validation,
            "rollback_used": False,
        }
    except Exception as exc:
        if replaced and backup_path is not None:
            try:
                rollback_stage = target.parent / (
                    f".restore_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.db"
                )
                shutil.copy2(backup_path, rollback_stage)
                os.replace(rollback_stage, target)
                for sidecar in _sidecar_paths(target):
                    sidecar.unlink(missing_ok=True)
                validate_streaming_manager_backup(target)
            except Exception as rollback_exc:
                raise RuntimeError(
                    "Восстановление завершилось ошибкой, и автоматический rollback тоже не удался. "
                    f"Safety-backup сохранён здесь: {backup_path}.\n\n"
                    f"Ошибка восстановления: {exc}\n"
                    f"Ошибка rollback: {rollback_exc}"
                ) from rollback_exc
            raise RuntimeError(
                "Восстановление завершилось ошибкой; исходное состояние автоматически "
                f"возвращено из safety-backup: {backup_path}.\n\n{exc}"
            ) from exc
        raise
    finally:
        staged.unlink(missing_ok=True)


def restore_result_path(project_dir: str | Path) -> Path:
    return AppPaths.from_root(project_dir).restore_result_path


def write_restore_result(project_dir: str | Path, payload: dict[str, Any]) -> None:
    path = restore_result_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def read_and_clear_restore_result(project_dir: str | Path) -> dict[str, Any] | None:
    path = restore_result_path(project_dir)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None
    finally:
        path.unlink(missing_ok=True)


def run_backup_helper(
    source_path: str | Path,
    target_path: str | Path,
    error_path: str | Path,
) -> int:
    """Create one SQLite snapshot for the parent process without loading Qt.

    The helper is intentionally usable both as ``python app.py --create-backup``
    and as ``InOneLine.exe --create-backup`` in a frozen build.  Errors are
    written to a small sidecar because a windowed PyInstaller executable does
    not have a reliable stderr stream.
    """
    source = Path(source_path).resolve()
    target = Path(target_path).resolve()
    error_file = Path(error_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    error_file.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    error_file.unlink(missing_ok=True)

    src: sqlite3.Connection | None = None
    dst: sqlite3.Connection | None = None
    try:
        src = sqlite3.connect(source, timeout=10)
        dst = sqlite3.connect(target, timeout=10)
        src.backup(dst)
        dst.commit()
        if target.stat().st_size <= 0:
            raise RuntimeError("Создана пустая резервная копия.")
        return 0
    except Exception as exc:
        target.unlink(missing_ok=True)
        try:
            error_file.write_text(
                f"{type(exc).__name__}: {exc}",
                encoding="utf-8",
            )
        except Exception:
            pass
        return 1
    finally:
        if dst is not None:
            try:
                dst.close()
            except Exception:
                pass
        if src is not None:
            try:
                src.close()
            except Exception:
                pass


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(  # type: ignore[attr-defined]
            PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            int(pid),
        )
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]
            return True
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _app_command(project_dir: Path) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [sys.executable, str((project_dir / "app.py").resolve())]


def _popen_detached(args: list[str], *, cwd: Path) -> subprocess.Popen[Any]:
    kwargs: dict[str, Any] = {
        "cwd": str(cwd),
        "close_fds": True,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        kwargs["creationflags"] = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        if getattr(sys, "frozen", False):
            # E4: a frozen executable may itself live beyond classic MAX_PATH.
            # Supplying executable= makes CPython pass a non-NULL
            # lpApplicationName to CreateProcessW; omitting a deep cwd avoids
            # the separate lpCurrentDirectory MAX_PATH restriction. All helper
            # arguments are already absolute, so no product behavior depends on
            # the application directory being the child process' cwd.
            kwargs["executable"] = sys.executable
            kwargs.pop("cwd", None)
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(args, **kwargs)


def launch_full_restore_helper(
    project_dir: str | Path,
    staged_dir: str | Path,
    parent_pid: int,
) -> None:
    project = Path(project_dir).resolve()
    command = _app_command(project) + [
        "--apply-full-restore",
        str(Path(staged_dir).resolve()),
        str(int(parent_pid)),
    ]
    _popen_detached(command, cwd=project)


def run_full_restore_helper(
    project_dir: str | Path,
    staged_dir: str | Path,
    parent_pid: int,
) -> int:
    """Wait for GUI exit, restore full user data, then relaunch InOneLine."""
    project = Path(project_dir).resolve()
    deadline = time.monotonic() + 60.0
    while _process_exists(int(parent_pid)) and time.monotonic() < deadline:
        time.sleep(0.1)

    if _process_exists(int(parent_pid)):
        try:
            write_restore_result(project, {
                "success": False,
                "restore_kind": "full",
                "error": "Не удалось дождаться полного завершения In one line. Данные не изменены.",
            })
        finally:
            shutil.rmtree(Path(staged_dir), ignore_errors=True)
        return 2

    try:
        result = apply_staged_full_restore(staged_dir, project)
    except Exception as exc:
        result = {
            "success": False,
            "restore_kind": "full",
            "error": str(exc),
        }
        shutil.rmtree(Path(staged_dir), ignore_errors=True)

    try:
        write_restore_result(project, result)
    except Exception:
        pass

    try:
        _popen_detached(_app_command(project), cwd=project)
    except Exception:
        return 3
    return 0 if result.get("success") else 1


def launch_restore_helper(
    project_dir: str | Path,
    staged_path: str | Path,
    target_database: str | Path,
    parent_pid: int,
) -> None:
    project = Path(project_dir).resolve()
    command = _app_command(project) + [
        "--apply-restore",
        str(Path(staged_path).resolve()),
        str(Path(target_database).resolve()),
        str(int(parent_pid)),
    ]
    _popen_detached(command, cwd=project)


def run_restore_helper(
    project_dir: str | Path,
    staged_path: str | Path,
    target_database: str | Path,
    parent_pid: int,
) -> int:
    """Wait for the GUI process, restore safely, then relaunch the application."""
    project = Path(project_dir).resolve()
    paths = AppPaths.from_root(project)
    deadline = time.monotonic() + 60.0
    while _process_exists(int(parent_pid)) and time.monotonic() < deadline:
        time.sleep(0.1)

    if _process_exists(int(parent_pid)):
        try:
            write_restore_result(project, {
                "success": False,
                "error": "Не удалось дождаться полного завершения In one line. База не изменена.",
            })
        finally:
            Path(staged_path).unlink(missing_ok=True)
        return 2

    result: dict[str, Any]
    try:
        result = apply_staged_restore(
            staged_path,
            target_database,
            paths.backups_dir,
            keep_backups=30,
        )
    except Exception as exc:
        result = {
            "success": False,
            "error": str(exc),
        }
        Path(staged_path).unlink(missing_ok=True)

    try:
        write_restore_result(project, result)
    except Exception:
        # The restore result marker is informational. Never undo a successful
        # restore merely because a one-shot status file could not be written.
        pass

    try:
        _popen_detached(_app_command(project), cwd=project)
    except Exception:
        return 3
    return 0 if result.get("success") else 1
