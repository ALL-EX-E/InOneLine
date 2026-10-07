from __future__ import annotations

"""Current-contract GUI regression smoke restored from the historical R1.0.10 suite."""

import gc
import os
import shutil
import socket
import sys
import tempfile
import time
import wave
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow

from streaming_manager.app_paths import AppPaths
from streaming_manager.ui_settings import open_ui_settings
from streaming_manager.constants import (
    APP_VERSION,
    AUCTION_SOUNDTRACK_LOOP_ONE_KEY,
    AUCTION_SOUNDTRACK_MEDIA_ID_KEY,
    AUCTION_SOUNDTRACK_MUTE_KEY,
    AUCTION_SOUNDTRACK_VOLUME_KEY,
    STATUS_NOT_PLAYED,
    STATUS_PLAYED,
    TIMER_OVERLAY_BACKGROUND_KEY,
    WHEEL_SOUNDTRACK_MEDIA_ID_KEY,
    WHEEL_SOUNDTRACK_MUTE_KEY,
    WHEEL_SOUNDTRACK_VOLUME_KEY,
)
from streaming_manager.database import Database, Game
from streaming_manager.media import MEDIA_CATEGORY_SOUNDTRACK
from streaming_manager.ui import MainWindow


def free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def make_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(8000)
        out.writeframes(b"\x00\x00" * 800)


def cleanup_tree(path: Path) -> None:
    gc.collect()
    last_error = None
    for _ in range(10):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except OSError as exc:
            last_error = exc
            gc.collect()
            time.sleep(0.15)
    if last_error is not None:
        raise last_error


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setOrganizationName("Local Streaming Tools QA")
    app.setApplicationName(f"InOneLine 1.0.8 GUI Regression Core {os.getpid()}")

    root = Path(tempfile.mkdtemp(prefix="inone_gui_regression_"))
    paths = AppPaths.from_root(root)
    paths.ensure_runtime_dirs()
    settings = open_ui_settings(paths.data_dir, migrate_native=False)
    settings.clear()
    probe = QMainWindow()
    probe.setMinimumSize(1100, 700)
    probe.setGeometry(120, 120, 1100, 700)
    settings.setValue("main_window/geometry", probe.saveGeometry())
    settings.setValue("main_window/maximized", False)
    settings.setValue("main_window/tab_index", 0)
    settings.sync()
    probe.deleteLater()

    window = None
    original_excepthook = sys.excepthook
    uncaught: list[tuple[type[BaseException], BaseException]] = []

    def capture(exc_type, exc_value, traceback):
        uncaught.append((exc_type, exc_value))
        original_excepthook(exc_type, exc_value, traceback)

    sys.excepthook = capture
    try:
        db = Database(paths.database_path)
        db.set_setting("api_port", str(free_local_port()))

        first_id = db.add_game(
            Game(None, "Smoke Game A", "2026-01-01", 10_000, 0, STATUS_PLAYED, "")
        )
        db.add_game(
            Game(None, "Smoke Game B", "2026-02-01", 5_000, 0, STATUS_NOT_PLAYED, "")
        )

        wheel_track = root / "wheel-smoke.wav"
        auction_track = root / "auction-smoke.wav"
        make_wav(wheel_track)
        make_wav(auction_track)
        wheel_asset = db.register_external_media_asset(MEDIA_CATEGORY_SOUNDTRACK, wheel_track)
        auction_asset = db.register_external_media_asset(MEDIA_CATEGORY_SOUNDTRACK, auction_track)
        db.set_settings_bulk({
            WHEEL_SOUNDTRACK_MEDIA_ID_KEY: str(wheel_asset.id),
            WHEEL_SOUNDTRACK_VOLUME_KEY: "37",
            WHEEL_SOUNDTRACK_MUTE_KEY: "0",
            AUCTION_SOUNDTRACK_MEDIA_ID_KEY: str(auction_asset.id),
            AUCTION_SOUNDTRACK_VOLUME_KEY: "29",
            AUCTION_SOUNDTRACK_MUTE_KEY: "0",
            AUCTION_SOUNDTRACK_LOOP_ONE_KEY: "0",
            TIMER_OVERLAY_BACKGROUND_KEY: "color",
        })

        print("[1/4] Main window / cold-start layout")
        window = MainWindow(db, paths)
        window.show()
        app.processEvents()
        QTest.qWait(250)
        app.processEvents()

        if APP_VERSION != "1.0.8":
            raise AssertionError(f"wrong app version: {APP_VERSION}")
        if window.minimumWidth() != 1100 or window.minimumHeight() != 700:
            raise AssertionError(
                f"product minimum changed: {window.minimumWidth()}x{window.minimumHeight()}"
            )
        if window.width() < 1100 or window.height() < 700:
            raise AssertionError(f"cold-start window below minimum: {window.size()}")

        expected_tabs = [
            "Список",
            "Публичный список",
            "Стрим / OBS",
            "Музыка",
            "Аукцион",
            "История аукционов",
            "Журнал",
            "Настройки",
        ]
        actual_tabs = [window.tabs.tabText(i) for i in range(window.tabs.count())]
        if actual_tabs != expected_tabs:
            raise AssertionError(f"main tabs mismatch: {actual_tabs}")

        if window.games_tab.add_btn.text() != "Добавить":
            raise AssertionError(
                f"add button label mismatch: {window.games_tab.add_btn.text()!r}"
            )

        # P01 shell contract: no top-level menus remain, the replacement hint
        # is informational only, and exactly one direct MainWindow F5 action
        # still performs the existing eager refresh_all() path.
        menu_actions = window.menuBar().actions()
        if menu_actions:
            raise AssertionError(
                f"unexpected top-level menu actions remain: "
                f"{[action.text() for action in menu_actions]}"
            )
        if window.refresh_hint_label.text() != "F5 — обновить данные во всех разделах":
            raise AssertionError(
                f"refresh hint mismatch: {window.refresh_hint_label.text()!r}"
            )
        if not window.refresh_hint_label.testAttribute(Qt.WA_TransparentForMouseEvents):
            raise AssertionError("refresh hint became interactive")

        f5_actions = [
            action
            for action in window.actions()
            if action.shortcut() == QKeySequence("F5")
        ]
        if len(f5_actions) != 1:
            raise AssertionError(
                f"expected one MainWindow F5 action, found {len(f5_actions)}"
            )

        original_games_refresh = window.games_tab.refresh
        f5_refresh_calls = 0

        def counted_games_refresh():
            nonlocal f5_refresh_calls
            f5_refresh_calls += 1
            return original_games_refresh()

        window.games_tab.refresh = counted_games_refresh
        try:
            f5_actions[0].trigger()
            app.processEvents()
        finally:
            window.games_tab.refresh = original_games_refresh
        if f5_refresh_calls != 1:
            raise AssertionError(
                f"F5 did not call refresh_all() exactly once: "
                f"Games refresh count={f5_refresh_calls}"
            )

        auction_tabs = [
            window.auction_tab.auction_tabs.tabText(i)
            for i in range(window.auction_tab.auction_tabs.count())
        ]
        if auction_tabs != ["Лоты", "Проведение"]:
            raise AssertionError(f"auction tabs mismatch: {auction_tabs}")

        settings_tabs = [
            window.settings_tab.settings_tabs.tabText(i)
            for i in range(window.settings_tab.settings_tabs.count())
        ]
        if settings_tabs != ["Общие", "Аукцион", "Интеграции", "Конвертация", "Экспорт"]:
            raise AssertionError(f"settings tabs mismatch: {settings_tabs}")

        pool = QThreadPool.globalInstance()
        if pool.maxThreadCount() > 8:
            raise AssertionError(f"global worker pool unbounded: {pool.maxThreadCount()}")
        if pool.expiryTimeout() != 10_000:
            raise AssertionError(f"worker expiry timeout changed: {pool.expiryTimeout()}")

        print("[2/4] Table reuse / conditional UI")
        window.games_tab.refresh()
        window.public_tab.refresh()
        app.processEvents()
        games_item = window.games_tab.table.item(0, 3)
        public_item = window.public_tab.table.item(0, 2)
        if games_item is None or public_item is None:
            raise AssertionError("table reuse smoke has no initial cells")
        window.games_tab.refresh()
        window.public_tab.refresh()
        app.processEvents()
        if window.games_tab.table.item(0, 3) is not games_item:
            raise AssertionError("Games refresh replaced an unchanged Qt cell")
        if window.public_tab.table.item(0, 2) is not public_item:
            raise AssertionError("Public refresh replaced an unchanged Qt cell")

        games = window.games_tab
        games._apply_action_state(SimpleNamespace(archived=False), 1)
        if games.archive_btn.isHidden() or not games.restore_btn.isHidden():
            raise AssertionError("1.0.8 active-game conditional actions are wrong")
        games._apply_action_state(SimpleNamespace(archived=True), 1)
        if not games.archive_btn.isHidden() or games.restore_btn.isHidden():
            raise AssertionError("1.0.8 archived-game conditional actions are wrong")
        games._apply_action_state(None, 0)
        if not games.archive_btn.isHidden() or not games.restore_btn.isHidden():
            raise AssertionError("1.0.8 no-selection actions are visible")

        stream = window.stream_tab
        stream.timer_background_transparent.setChecked(True)
        stream._update_timer_background_enabled_state()
        if not stream.timer_background_color_row.isHidden():
            raise AssertionError("Timer color row visible in transparent mode")
        stream.timer_background_color_mode.setChecked(True)
        stream._update_timer_background_enabled_state()
        if stream.timer_background_color_row.isHidden():
            raise AssertionError("Timer color row hidden in color mode")

        auto = window.settings_tab
        auto.auto_extend_leader_enabled.setChecked(False)
        auto._update_auto_extend_conditional_visibility()
        if not auto.auto_extend_leader_duration.isHidden():
            raise AssertionError("auto-extend duration visible while reason is disabled")
        auto.auto_extend_leader_enabled.setChecked(True)
        auto._update_auto_extend_conditional_visibility()
        if auto.auto_extend_leader_duration.isHidden():
            raise AssertionError("auto-extend duration hidden while reason is enabled")

        public = window.public_tab
        public._public_xlsx_path = None
        public._public_xlsx_update_controls()
        if not public.public_xlsx_disconnect_btn.isHidden():
            raise AssertionError("Public XLSX disconnect visible while disconnected")

        print("[3/4] D26 soundtrack selectors / live gain")
        auction = window.auction_tab
        if int(auction.wheel_soundtrack_combo.currentData() or 0) != wheel_asset.id:
            raise AssertionError("wheel soundtrack selection was not restored")
        if auction.wheel_soundtrack_volume.value() != 37:
            raise AssertionError("wheel soundtrack volume was not restored")
        if "доступен" not in auction.wheel_soundtrack_status.text().lower():
            raise AssertionError("healthy wheel soundtrack is not available")

        if int(auction.auction_soundtrack_combo.currentData() or 0) != auction_asset.id:
            raise AssertionError("auction soundtrack selection was not restored")
        if auction.auction_soundtrack_volume.value() != 29:
            raise AssertionError("auction soundtrack volume was not restored")
        if "доступен" not in auction.auction_soundtrack_status.text().lower():
            raise AssertionError("healthy auction soundtrack is not available")

        auction.wheel_soundtrack_volume.setValue(41)
        auction.wheel_soundtrack_mute.setChecked(True)
        app.processEvents()
        if db.get_setting(WHEEL_SOUNDTRACK_VOLUME_KEY) != "41":
            raise AssertionError("wheel volume did not persist")
        if db.get_setting(WHEEL_SOUNDTRACK_MUTE_KEY) != "1":
            raise AssertionError("wheel mute did not persist")
        if auction.wheel_audio.volume_percent != 41 or not auction.wheel_audio.muted:
            raise AssertionError("wheel live gain/mute did not reach audio engine")
        auction.wheel_soundtrack_mute.setChecked(False)

        auction.auction_soundtrack_volume.setValue(33)
        auction.auction_soundtrack_mute.setChecked(True)
        app.processEvents()
        if db.get_setting(AUCTION_SOUNDTRACK_VOLUME_KEY) != "33":
            raise AssertionError("auction volume did not persist")
        if db.get_setting(AUCTION_SOUNDTRACK_MUTE_KEY) != "1":
            raise AssertionError("auction mute did not persist")
        if auction.auction_audio.volume_percent != 33 or not auction.auction_audio.muted:
            raise AssertionError("auction live gain/mute did not reach audio engine")
        auction.auction_soundtrack_mute.setChecked(False)

        moved_track = root / "wheel-smoke-moved.wav"
        wheel_track.replace(moved_track)
        auction.refresh_force()
        app.processEvents()
        if auction.wheel_soundtrack_combo.currentData():
            raise AssertionError("missing external wheel soundtrack stayed selected")
        if db.get_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, ""):
            raise AssertionError("missing external wheel soundtrack setting was not cleared")
        if "не выбран" not in auction.wheel_soundtrack_status.text().lower():
            raise AssertionError("missing external wheel soundtrack did not fall back safely")

        replacement = db.register_external_media_asset(MEDIA_CATEGORY_SOUNDTRACK, moved_track)
        auction._adopt_wheel_soundtrack_asset(replacement.id)
        app.processEvents()
        if int(auction.wheel_soundtrack_combo.currentData() or 0) != replacement.id:
            raise AssertionError("re-selected external wheel soundtrack was not adopted")
        if "доступен" not in auction.wheel_soundtrack_status.text().lower():
            raise AssertionError("re-selected wheel soundtrack stayed unavailable")

        print("[4/4] Clean shutdown")
        window.close()
        app.processEvents()
        window = None
        QTest.qWait(450)
        QThreadPool.globalInstance().waitForDone(30_000)
        app.processEvents()
        gc.collect()

        if uncaught:
            exc_type, exc_value = uncaught[0]
            raise AssertionError(
                f"unhandled GUI exception: {exc_type.__name__}: {exc_value}"
            )
    finally:
        sys.excepthook = original_excepthook
        if window is not None:
            try:
                window.close()
                app.processEvents()
            except Exception:
                pass
        try:
            QTest.qWait(450)
            QThreadPool.globalInstance().waitForDone(30_000)
            app.processEvents()
        except Exception:
            pass
        cleanup_tree(root)

    print("1.0.8 GUI REGRESSION CORE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
