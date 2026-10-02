from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QByteArray, QSettings

from streaming_manager.ui_settings import (
    UI_SETTINGS_MIGRATION_KEY,
    legacy_ui_settings_backup_path,
    open_ui_settings,
    ui_settings_path,
)


def registry_settings(
    fmt: QSettings.Format,
    organization: str,
    application: str,
) -> QSettings:
    return QSettings(
        fmt,
        QSettings.Scope.UserScope,
        organization,
        application,
    )


def clear_store(settings: QSettings) -> None:
    settings.clear()
    settings.sync()
    assert settings.status() == QSettings.Status.NoError


def main() -> None:
    organization = f"Local Streaming Tools A9 QA {os.getpid()}"
    sources = (
        (organization, "Streaming Manager"),
        (organization, "InOneLine"),
    )

    stores = [
        registry_settings(fmt, organization, application)
        for organization, application in sources
        for fmt in (QSettings.Format.Registry64Format, QSettings.Format.Registry32Format)
    ]
    for store in stores:
        clear_store(store)

    legacy64 = registry_settings(QSettings.Format.Registry64Format, *sources[0])
    legacy32 = registry_settings(QSettings.Format.Registry32Format, *sources[0])
    reserved64 = registry_settings(QSettings.Format.Registry64Format, *sources[1])

    try:
        # Older/stale view first.
        legacy32.setValue("main_window/geometry", QByteArray(b"stale-geometry"))
        legacy32.setValue("main_window/tab_index", 4)
        legacy32.setValue("lists/visible", True)
        legacy32.sync()
        assert legacy32.status() == QSettings.Status.NoError

        time.sleep(0.15)

        # Newer production view must win for overlapping keys.
        legacy64.setValue("main_window/geometry", QByteArray(b"current-geometry"))
        legacy64.setValue("main_window/maximized", False)
        legacy64.setValue("main_window/tab_index", 3)
        legacy64.setValue("lists/visible", False)
        legacy64.setValue("games/list_visible", False)
        legacy64.sync()
        assert legacy64.status() == QSettings.Status.NoError

        # Reserved final-name store may only backfill missing keys.
        reserved64.setValue("public/list_visible", False)
        reserved64.sync()
        assert reserved64.status() == QSettings.Status.NoError

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            data_dir = Path(tmp) / "data"
            settings = open_ui_settings(
                data_dir,
                migrate_native=True,
                native_sources=sources,
            )
            settings.sync()

            target_path = ui_settings_path(data_dir)
            backup_path = legacy_ui_settings_backup_path(data_dir)
            assert target_path.is_file(), target_path
            assert backup_path.is_file(), backup_path
            assert bytes(settings.value("main_window/geometry")) == b"current-geometry"
            assert settings.value("main_window/maximized", True, type=bool) is False
            assert settings.value("main_window/tab_index", 0, type=int) == 3
            assert settings.value("lists/visible", True, type=bool) is False
            assert settings.value("games/list_visible", True, type=bool) is False
            assert settings.value("public/list_visible", True, type=bool) is False
            assert settings.value(UI_SETTINGS_MIGRATION_KEY, False, type=bool) is True
            assert settings.value("migration/legacy_backup_created", False, type=bool) is True
            assert settings.value("migration/native_qsettings_cleared", False, type=bool) is True
            assert "Streaming Manager/registry64" in str(settings.value("migration/source", ""))

            for store in stores:
                assert store.allKeys() == [], store.allKeys()

            settings.setValue("main_window/tab_index", 6)
            settings.sync()
            reopened = QSettings(str(target_path), QSettings.Format.IniFormat)
            assert reopened.value("main_window/tab_index", 0, type=int) == 6

            again = open_ui_settings(
                data_dir,
                migrate_native=True,
                native_sources=sources,
            )
            assert again.value("main_window/tab_index", 0, type=int) == 6

        print("UI_SETTINGS_DUAL_REGISTRY_VIEW_MIGRATION=PASS")
        print("UI_SETTINGS_LEGACY_BACKUP=PASS")
        print("UI_SETTINGS_FILE_BACKEND=PASS")
    finally:
        for store in stores:
            clear_store(store)


if __name__ == "__main__":
    main()
