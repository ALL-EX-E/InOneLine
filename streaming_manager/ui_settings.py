from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QSettings

try:
    import winreg
except ImportError:  # pragma: no cover - Windows-only migration support
    winreg = None

UI_SETTINGS_FILENAME = "ui_state.ini"
LEGACY_UI_SETTINGS_BACKUP_FILENAME = "legacy_ui_state_backup.ini"
UI_SETTINGS_MIGRATION_KEY = "migration/native_qsettings_v2"
UI_SETTINGS_ORGANIZATION = "Local Streaming Tools"
LEGACY_NATIVE_SETTINGS_SOURCES: tuple[tuple[str, str], ...] = (
    (UI_SETTINGS_ORGANIZATION, "Streaming Manager"),
    (UI_SETTINGS_ORGANIZATION, "InOneLine"),
)


def ui_settings_path(data_dir: str | Path) -> Path:
    return Path(data_dir).resolve() / UI_SETTINGS_FILENAME


def legacy_ui_settings_backup_path(data_dir: str | Path) -> Path:
    return Path(data_dir).resolve() / LEGACY_UI_SETTINGS_BACKUP_FILENAME


def _user_settings(
    fmt: QSettings.Format,
    organization: str,
    application: str,
) -> QSettings:
    return QSettings(
        fmt,
        QSettings.Scope.UserScope,
        str(organization),
        str(application),
    )


def _registry_last_write(
    organization: str,
    application: str,
    wow_flag: int,
) -> int:
    if winreg is None:
        return 0
    key_path = rf"Software\{organization}\{application}"
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_READ | wow_flag,
        ) as key:
            return int(winreg.QueryInfoKey(key)[2])
    except OSError:
        return 0


def _legacy_user_settings(
    native_sources: Iterable[tuple[str, str]],
) -> list[tuple[str, QSettings, int]]:
    definitions = tuple(native_sources)
    rows: list[tuple[int, int, str, QSettings, int]] = []

    if os.name == "nt" and winreg is not None:
        views = (
            (QSettings.Format.Registry64Format, winreg.KEY_WOW64_64KEY, "registry64"),
            (QSettings.Format.Registry32Format, winreg.KEY_WOW64_32KEY, "registry32"),
        )
        for app_priority, (organization, application) in enumerate(definitions):
            for fmt, wow_flag, view_name in views:
                settings = _user_settings(fmt, organization, application)
                if not settings.allKeys():
                    continue
                modified = _registry_last_write(organization, application, wow_flag)
                label = f"{organization}/{application}/{view_name}"
                rows.append((app_priority, -modified, label, settings, modified))
    else:
        for app_priority, (organization, application) in enumerate(definitions):
            settings = _user_settings(QSettings.Format.NativeFormat, organization, application)
            if settings.allKeys():
                label = f"{organization}/{application}/native"
                rows.append((app_priority, 0, label, settings, 0))

    rows.sort(key=lambda row: (row[0], row[1], row[2]))
    return [(label, settings, modified) for _, _, label, settings, modified in rows]


def _copy_missing_settings(target: QSettings, source: QSettings) -> None:
    existing = set(target.allKeys())
    for key in source.allKeys():
        if key in existing:
            continue
        target.setValue(key, source.value(key))
        existing.add(key)


def _backup_legacy_settings(
    data_dir: str | Path,
    sources: list[tuple[str, QSettings, int]],
) -> bool:
    if not sources:
        return True

    backup = QSettings(
        str(legacy_ui_settings_backup_path(data_dir)),
        QSettings.Format.IniFormat,
    )
    backup.clear()
    for index, (label, source, modified) in enumerate(sources):
        backup.beginGroup(f"source_{index}")
        backup.setValue("label", label)
        backup.setValue("registry_last_write", str(modified))
        backup.beginGroup("values")
        for key in source.allKeys():
            backup.setValue(key, source.value(key))
        backup.endGroup()
        backup.endGroup()
    backup.sync()
    return backup.status() == QSettings.Status.NoError


def open_ui_settings(
    data_dir: str | Path,
    *,
    migrate_native: bool | None = None,
    native_sources: Iterable[tuple[str, str]] = LEGACY_NATIVE_SETTINGS_SOURCES,
) -> QSettings:
    """Open app-owned UI state and migrate legacy Windows QSettings once.

    The migration checks both 64-bit and 32-bit per-user Registry views. Within
    the production legacy application name, the most recently modified view is
    copied first; missing keys may be backfilled from the other view and then
    from the reserved final-name store. Before Registry cleanup, every source
    is copied into data/legacy_ui_state_backup.ini for recovery/audit.
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

    sources = _legacy_user_settings(native_sources)
    for _, source, _ in sources:
        _copy_missing_settings(target, source)

    target.setValue(UI_SETTINGS_MIGRATION_KEY, True)
    target.setValue("migration/source", sources[0][0] if sources else "none")
    target.setValue("migration/source_count", len(sources))
    target.sync()
    if target.status() != QSettings.Status.NoError:
        return target

    backup_ok = _backup_legacy_settings(data_dir, sources)
    target.setValue("migration/legacy_backup_created", backup_ok)

    cleared = bool(backup_ok)
    if backup_ok:
        for _, source, _ in sources:
            source.clear()
            source.sync()
            if source.status() != QSettings.Status.NoError:
                cleared = False
    target.setValue("migration/native_qsettings_cleared", cleared)
    target.sync()
    return target
