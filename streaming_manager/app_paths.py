from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    """Authoritative filesystem layout for one InOneLine installation/source tree.

    R1.0.1 intentionally keeps every application-owned mutable file below the
    user-selected InOneLine root.  The installer may default that root to
    ``C:\\InOneLine`` and may let the user choose another drive/folder.  Source
    mode keeps the existing development layout beside ``app.py``.
    """

    root_dir: Path

    @classmethod
    def from_root(cls, root_dir: str | Path) -> "AppPaths":
        return cls(Path(root_dir).resolve())

    @classmethod
    def current_process(cls) -> "AppPaths":
        if getattr(sys, "frozen", False):
            root = Path(sys.executable).resolve().parent
        else:
            root = Path(__file__).resolve().parent.parent
        return cls(root)

    @classmethod
    def from_database_path(cls, database_path: str | Path) -> "AppPaths":
        database = Path(database_path).resolve()
        # Canonical layout: <root>/data/streaming.db.
        return cls(database.parent.parent)

    @property
    def resource_root(self) -> Path:
        """Return the immutable bundled-resource root for source/frozen modes."""
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(getattr(sys, "_MEIPASS")).resolve()
        return self.root_dir

    def resource_path(self, *parts: str) -> Path:
        return self.resource_root.joinpath(*parts)

    @property
    def data_dir(self) -> Path:
        return self.root_dir / "data"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "streaming.db"

    @property
    def backups_dir(self) -> Path:
        return self.root_dir / "backups"

    @property
    def logs_dir(self) -> Path:
        return self.root_dir / "logs"

    @property
    def restore_result_path(self) -> Path:
        return self.data_dir / "restore_result.json"

    def ensure_runtime_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
