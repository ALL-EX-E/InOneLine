from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = PROJECT_ROOT / "installer" / "InOneLine.iss"
MAIN_WINDOW = PROJECT_ROOT / "streaming_manager" / "views" / "main_window.py"
UI_SETTINGS = PROJECT_ROOT / "streaming_manager" / "ui_settings.py"


def main() -> None:
    installer = INSTALLER.read_text(encoding="utf-8-sig")
    main_window = MAIN_WINDOW.read_text(encoding="utf-8")
    ui_settings = UI_SETTINGS.read_text(encoding="utf-8")

    assert "PrivilegesRequired=admin" in installer
    assert "DefaultDirName=C:\\InOneLine" in installer
    assert "Permissions: users-modify" in installer
    assert "Root: HKCU" not in installer
    assert "RegDeleteKeyIncludingSubkeys(HKCU" not in installer
    assert "UsedUserAreasWarning=no" not in installer

    assert "open_ui_settings(paths.data_dir)" in main_window
    assert "QSettings()" not in main_window
    assert "ui_state.ini" in ui_settings
    assert "QSettings.Format.IniFormat" in ui_settings
    assert "QSettings.Format.NativeFormat" in ui_settings
    assert "source.clear()" in ui_settings

    print("INSTALLER_ADMIN_MODE=PASS")
    print("INSTALLER_HKCU_FREE=PASS")
    print("UI_STATE_APP_OWNED=PASS")


if __name__ == "__main__":
    main()
