from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QLockFile

INSTANCE_LOCK_FILENAME = ".inone_line.instance.lock"


def acquire_instance_lock(data_dir: str | Path) -> QLockFile | None:
    path = Path(data_dir).resolve() / INSTANCE_LOCK_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(path))
    lock.setStaleLockTime(0)
    if lock.tryLock(0):
        return lock
    if lock.error() == QLockFile.LockError.LockFailedError:
        return None
    raise RuntimeError(f"Не удалось создать файл блокировки экземпляра: {path}")
