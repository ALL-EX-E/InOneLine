from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

from streaming_manager.app_paths import AppPaths
from streaming_manager.diagnostic_logs import STARTUP_ERROR_MAX_BYTES, append_capped_log
from streaming_manager.constants import APP_NAME, LEGACY_SETTINGS_APP_NAME
from streaming_manager.windows_long_path import (
    install_frozen_windows_long_path_compat,
    prepare_frozen_qt_plugins_for_long_path,
)

# E4: install before any helper or Qt/native extension import.  In source mode
# and on non-Windows platforms this is a no-op.
install_frozen_windows_long_path_compat()


def project_directory() -> Path:
    # Compatibility helper for maintenance code/tests. R1.0.1 makes AppPaths
    # the authoritative layout resolver.
    return AppPaths.current_process().root_dir


def write_startup_error(paths: AppPaths, exc: BaseException) -> Path:
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = paths.logs_dir / "startup_error.log"
    entry = (
        "\n" + "=" * 72 + "\n"
        + datetime.now().isoformat(timespec="seconds") + "\n"
        + f"{type(exc).__name__}: {exc}\n"
        + traceback.format_exc()
    )
    append_capped_log(
        log_path,
        entry,
        max_bytes=STARTUP_ERROR_MAX_BYTES,
        backup_count=1,
    )
    return log_path


def run_internal_helper_if_requested() -> int | None:
    """Run frozen/source maintenance helpers before importing Qt GUI modules."""
    if len(sys.argv) < 2:
        return None

    command = sys.argv[1]
    if command == "--apply-restore":
        if len(sys.argv) != 5:
            return 2
        from streaming_manager.backup_restore import run_restore_helper

        paths = AppPaths.current_process()
        staged_path = Path(sys.argv[2])
        target_database = Path(sys.argv[3])
        try:
            parent_pid = int(sys.argv[4])
        except ValueError:
            return 2
        return run_restore_helper(paths.root_dir, staged_path, target_database, parent_pid)

    if command == "--create-backup":
        if len(sys.argv) != 5:
            return 2
        from streaming_manager.backup_restore import run_backup_helper

        return run_backup_helper(
            Path(sys.argv[2]),
            Path(sys.argv[3]),
            Path(sys.argv[4]),
        )

    if command == "--apply-full-restore":
        if len(sys.argv) != 4:
            return 2
        from streaming_manager.backup_restore import run_full_restore_helper

        paths = AppPaths.current_process()
        try:
            parent_pid = int(sys.argv[3])
        except ValueError:
            return 2
        return run_full_restore_helper(paths.root_dir, Path(sys.argv[2]), parent_pid)

    return None


def main() -> int:
    paths = AppPaths.current_process()

    try:
        paths.ensure_runtime_dirs()
        from streaming_manager.backup_restore import cleanup_stale_runtime_artifacts

        cleanup_stale_runtime_artifacts(paths.root_dir)
        # E4 FIX7: Qt's own plugin loader is outside CPython's extension loader.
        # Stage plugins proactively once the native-loader safety headroom is
        # reached, before QApplication is created.
        prepare_frozen_qt_plugins_for_long_path()

        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication, QMessageBox

        from streaming_manager.database import Database
        from streaming_manager.input_guard import WindowsInputGuard
        from streaming_manager.ui import MainWindow

        db = Database(paths.database_path)
        app = QApplication(sys.argv)
        app.setApplicationName(LEGACY_SETTINGS_APP_NAME)
        app.setApplicationDisplayName(APP_NAME)
        app.setOrganizationName("Local Streaming Tools")

        icon_path = paths.resource_path("assets", "InOneLine_icon_master.png")
        if icon_path.is_file():
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                app.setWindowIcon(icon)

        # Глобальная защита от случайных кликов по In one line через
        # окно другой программы. Сохраняем объект на QApplication, чтобы
        # eventFilter жил до завершения приложения.
        input_guard = WindowsInputGuard(app)
        app.installEventFilter(input_guard)
        app._streaming_input_guard = input_guard

        window = MainWindow(db, paths)
        window.show()
        return app.exec()

    except BaseException as exc:
        log_path = write_startup_error(paths, exc)
        print(f"Ошибка запуска: {exc}", file=sys.stderr)
        print(f"Лог: {log_path}", file=sys.stderr)

        # If Qt itself loaded successfully, try to show a visible error dialog.
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox

            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                f"{APP_NAME} — ошибка запуска",
                f"{type(exc).__name__}: {exc}\n\n"
                f"Подробности записаны в:\n{log_path}",
            )
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    helper_code = run_internal_helper_if_requested()
    raise SystemExit(main() if helper_code is None else helper_code)
