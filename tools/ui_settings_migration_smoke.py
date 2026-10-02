from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QByteArray, QSettings

from streaming_manager.ui_settings import (
    UI_SETTINGS_MIGRATION_KEY,
    open_ui_settings,
    ui_settings_path,
)


def native_settings(organization: str, application: str) -> QSettings:
    return QSettings(
        QSettings.Format.NativeFormat,
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
    legacy = native_settings(*sources[0])
    reserved = native_settings(*sources[1])
    clear_store(legacy)
    clear_store(reserved)

    try:
        legacy.setValue("main_window/geometry", QByteArray(b"legacy-geometry"))
        legacy.setValue("main_window/maximized", True)
        legacy.setValue("main_window/tab_index", 4)
        legacy.setValue("lists/visible", False)
        reserved.setValue("main_window/geometry", QByteArray(b"reserved-geometry"))
        reserved.setValue("public/list_visible", True)
        legacy.sync()
        reserved.sync()
        assert legacy.status() == QSettings.Status.NoError
        assert reserved.status() == QSettings.Status.NoError

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            data_dir = Path(tmp) / "data"
            settings = open_ui_settings(
                data_dir,
                migrate_native=True,
                native_sources=sources,
            )
            settings.sync()

            target_path = ui_settings_path(data_dir)
            assert target_path.is_file(), target_path
            assert bytes(settings.value("main_window/geometry")) == b"legacy-geometry"
            assert settings.value("main_window/maximized", False, type=bool) is True
            assert settings.value("main_window/tab_index", 0, type=int) == 4
            assert settings.value("lists/visible", True, type=bool) is False
            assert settings.value("public/list_visible", False, type=bool) is True
            assert settings.value(UI_SETTINGS_MIGRATION_KEY, False, type=bool) is True

            assert native_settings(*sources[0]).allKeys() == []
            assert native_settings(*sources[1]).allKeys() == []

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

        print("UI_SETTINGS_NATIVE_MIGRATION=PASS")
        print("UI_SETTINGS_FILE_BACKEND=PASS")
    finally:
        clear_store(native_settings(*sources[0]))
        clear_store(native_settings(*sources[1]))


if __name__ == "__main__":
    main()
