from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QSettings

UI_SETTINGS_FILENAME = "ui_state.ini"
UI_SETTINGS_MIGRATION_KEY = "migration/native_qsettings_v1"
UI_SETTINGS_ORGANIZATION = "Local Streaming Tools"
LEGACY_NATIVE_SETTINGS_SOURCES: tuple[tuple[str, str], ...] = (
    (UI_SETTINGS_ORGANIZATION, "Streaming Manager"),
    (UI_SETTINGS_ORGANIZATION, "InOneLine"),
)


def ui_settings_path(data_dir: str | Path) -> Path:
    return Path(data_dir).resolve() / UI_SETTINGS_FILENAME


def _native_user_settings(organization: str, application: str) -> QSettings:
    return QSettings(
        QSettings.Format.NativeFormat,
        QSettings.Scope.UserScope,
        str(organization),
        str(application),
    )


def _copy_missing_settings(target: QSettings, source: QSettings) -> None:
    existing = set(target.allKeys())
    for key in source.allKeys():
        if key in existing:
            continue
        target.setValue(key, source.value(key))
        existing.add(key)


def open_ui_settings(
    data_dir: str | Path,
    *,
    migrate_native: bool | None = None,
    native_sources: Iterable[tuple[str, str]] = LEGACY_NATIVE_SETTINGS_SOURCES,
) -> QSettings:
    """Open app-owned UI state and migrate legacy native QSettings once.

    Frozen Windows builds previously stored MainWindow state in HKCU through
    Qt default QSettings backend. An administrative installer cannot safely
    own those per-user registry keys because after UAC it may run under
    another administrator account. The application itself therefore performs
    the one-time migration under the actual interactive user and then owns
    the settings as data/ui_state.ini.

    Source-mode development does not migrate the production registry by
    default. Tests may force migration with migrate_native=True.
    """

    path = ui_settings_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    target = QSettings(str(path), QSettings.Format.IniFormat)

    if migrate_native is None:
        migrate_native = os.name == "nt" and bool(getattr(sys, "frozen", False))
    if not migrate_native:
        return target

    if target.value(UI_SETTINGS_MIGRATION_KEY, False, type=bool):
        return target

    sources = [
        _native_user_settings(organization, application)
        for organization, application in tuple(native_sources)
    ]

    for source in sources:
        _copy_missing_settings(target, source)

    target.sync()
    if target.status() != QSettings.Status.NoError:
        return target

    cleared = True
    for source in sources:
        source.clear()
        source.sync()
        if source.status() != QSettings.Status.NoError:
            cleared = False

    if cleared:
        target.setValue(UI_SETTINGS_MIGRATION_KEY, True)
        target.sync()

    return target
