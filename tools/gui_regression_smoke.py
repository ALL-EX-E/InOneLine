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
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QMainWindow, QMessageBox, QPushButton

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
from streaming_manager.database import Database, DuplicateGameError, Game
from streaming_manager.media import MEDIA_CATEGORY_SOUNDTRACK
from streaming_manager.ui import MainWindow
from streaming_manager.views.games import DeleteAllGamesDialog, GameDialog


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
        import_db = Database(root / "p03_import_aliases.db")
        neutral_csv = root / "p03_neutral_headers.csv"
        neutral_csv.write_text(
            "НАЗВАНИЕ;ДАТА;БАЛЛЫ\n"
            "P03 Neutral;27.08.2019;1500\n",
            encoding="utf-8",
        )
        neutral_result = import_db.import_csv(neutral_csv)
        if neutral_result["created"] != 1:
            raise AssertionError(f"neutral CSV import result mismatch: {neutral_result!r}")
        neutral_game = import_db.find_game_by_title("P03 Neutral")
        if neutral_game is None:
            raise AssertionError("neutral CSV title header was not accepted")
        if neutral_game.release_date != "2019-08-27" or neutral_game.amount != 1500:
            raise AssertionError(
                "neutral CSV field mapping mismatch: "
                f"{neutral_game.release_date!r}, {neutral_game.amount!r}"
            )

        legacy_csv = root / "p03_legacy_headers.csv"
        legacy_csv.write_text(
            "НАЗВАНИЕ ИГРЫ;ДАТА ВЫХОДА;БАЛЛЫ\n"
            "P03 Legacy;28.08.2019;1600\n",
            encoding="utf-8",
        )
        legacy_result = import_db.import_csv(legacy_csv)
        if legacy_result["created"] != 1:
            raise AssertionError(f"legacy CSV import result mismatch: {legacy_result!r}")
        legacy_game = import_db.find_game_by_title("P03 Legacy")
        if legacy_game is None:
            raise AssertionError("legacy CSV title alias stopped working")
        if legacy_game.release_date != "2019-08-28" or legacy_game.amount != 1600:
            raise AssertionError(
                "legacy CSV alias mapping mismatch: "
                f"{legacy_game.release_date!r}, {legacy_game.amount!r}"
            )

        def expect_csv_error(name, content, expected_parts, *, with_backup=False):
            csv_path = root / name
            csv_path.write_text(content, encoding="utf-8")
            try:
                if with_backup:
                    import_db.import_csv_with_backup(
                        csv_path,
                        root / "p03_error_backups",
                        merge=True,
                        keep_backups=3,
                    )
                else:
                    import_db.import_csv(csv_path)
            except Exception as exc:
                message = str(exc)
            else:
                raise AssertionError(f"CSV error case unexpectedly passed: {name}")
            for expected in expected_parts:
                if expected not in message:
                    raise AssertionError(
                        f"CSV error wording missing {expected!r} for {name}: {message!r}"
                    )
            return message

        expect_csv_error(
            "p03_duplicate.csv",
            "НАЗВАНИЕ;БАЛЛЫ\n"
            "P03 Duplicate;10\n"
            " p03 duplicate ;20\n",
            (
                "Повторяется название «p03 duplicate» (строка 3).",
                "Ранее это же название указано в строке 2 как «P03 Duplicate».",
                "Оставьте в CSV только одну запись с этим названием.",
            ),
        )

        expect_csv_error(
            "p03_invalid_status.csv",
            "НАЗВАНИЕ;СТАТУС\n"
            "P03 Bad Status;НЕИЗВЕСТНО\n",
            (
                "Некорректное значение в поле «СТАТУС»",
                "строка 2",
                "«НЕИЗВЕСТНО»",
                "ПРОХОДИТСЯ, НЕ ИГРАЛ, ИГРАЛ, ПРОЙДЕНО или ЗАБРОШЕНО",
            ),
        )

        expect_csv_error(
            "p03_invalid_coop.csv",
            "НАЗВАНИЕ;КООП/НЕ КООП\n"
            "P03 Bad Coop;ДА\n",
            (
                "Некорректное значение в поле «КООП/НЕ КООП»",
                "строка 2",
                "«ДА»",
                "Допустимо: КООП или НЕ КООП.",
            ),
        )

        expect_csv_error(
            "p03_invalid_date.csv",
            "НАЗВАНИЕ;ДАТА\n"
            "P03 Bad Date;31.02.2019\n",
            (
                "Некорректное значение в поле «ДАТА»",
                "строка 2",
                "«31.02.2019»",
                "например 27.08.2019",
                "или оставьте поле пустым.",
            ),
        )

        expect_csv_error(
            "p03_invalid_points.csv",
            "НАЗВАНИЕ;БАЛЛЫ\n"
            "P03 Bad Points;abc\n",
            (
                "Некорректное значение в поле «БАЛЛЫ»",
                "строка 2",
                "«abc»",
                "Укажите целое число; если баллов нет, укажите 0.",
            ),
        )

        missing_header_message = expect_csv_error(
            "p03_missing_title_header.csv",
            "БАЛЛЫ;ДАТА\n"
            "10;27.08.2019\n",
            (
                "Не найден обязательный столбец «НАЗВАНИЕ».",
                "старое «НАЗВАНИЕ ИГРЫ» также принимается",
                "«Название|Баллы»",
            ),
        )
        if "Название игры|Баллы" in missing_header_message:
            raise AssertionError(
                "missing-header error exposes legacy game-centric format wording"
            )

        expect_csv_error(
            "p03_legacy_missing_points.csv",
            "P03 Legacy Missing|\n",
            (
                "Не указаны баллы у «P03 Legacy Missing» (строка 1).",
                "значение после «|» обязательно",
                "если баллов нет, укажите 0.",
            ),
        )

        atomic_message = expect_csv_error(
            "p03_atomicity.csv",
            "НАЗВАНИЕ;СТАТУС\n"
            "P03 Atomic Good;НЕ ИГРАЛ\n"
            "P03 Atomic Bad;НЕИЗВЕСТНО\n",
            (
                "Некорректное значение в поле «СТАТУС»",
                "P03 Atomic Bad",
                "строка 3",
            ),
        )
        if import_db.find_game_by_title("P03 Atomic Good") is not None:
            raise AssertionError(
                f"CSV atomicity changed after error wording update: {atomic_message!r}"
            )

        backup_error = expect_csv_error(
            "p03_backup_path_error.csv",
            "НАЗВАНИЕ;БАЛЛЫ\n"
            "P03 Backup Error;abc\n",
            (
                "Импорт не выполнен:",
                "Некорректное значение в поле «БАЛЛЫ»",
                "Резервная копия перед попыткой импорта:",
            ),
            with_backup=True,
        )
        if "Резервная копия перед попыткой импорта:" not in backup_error:
            raise AssertionError("CSV error lost safety-backup path")

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

        public_descriptions = [
            label.text()
            for label in window.public_tab.findChildren(QLabel)
            if label.text().startswith("Публичный список формируется напрямую")
        ]
        if len(public_descriptions) != 1:
            raise AssertionError(
                f"public-list description lookup mismatch: {public_descriptions!r}"
            )
        public_description = public_descriptions[0]
        if "НАЗВАНИЕ / БАЛЛЫ / ОТЗЫВ / СТАТУС" not in public_description:
            raise AssertionError(
                f"public-list description title label mismatch: {public_description!r}"
            )
        if "НАЗВАНИЕ ИГРЫ" in public_description:
            raise AssertionError("legacy public-list description title label remains")
        public_title_header = window.public_tab.table.horizontalHeaderItem(2)
        if public_title_header is None or public_title_header.text() != "НАЗВАНИЕ":
            raise AssertionError(
                "public-list table title header mismatch: "
                f"{public_title_header.text() if public_title_header else None!r}"
            )

        public_button_texts = {
            button.text() for button in window.public_tab.findChildren(QPushButton)
        }
        if "Открыть локальный JSON" in public_button_texts:
            raise AssertionError("legacy Public List local JSON button remains")

        if window.games_tab.add_btn.text() != "Добавить":
            raise AssertionError(
                f"add button label mismatch: {window.games_tab.add_btn.text()!r}"
            )

        games_title_header = window.games_tab.table.horizontalHeaderItem(3)
        if games_title_header is None or games_title_header.text() != "НАЗВАНИЕ":
            raise AssertionError(
                "main-list title header mismatch: "
                f"{games_title_header.text() if games_title_header else None!r}"
            )
        if window.games_tab.search_btn.toolTip() != (
            "Показать список и перейти к первой найденной записи"
        ):
            raise AssertionError(
                f"main-list search tooltip mismatch: {window.games_tab.search_btn.toolTip()!r}"
            )
        if window.public_tab.search_btn.toolTip() != (
            "Показать список и перейти к первой найденной записи"
        ):
            raise AssertionError(
                f"public-list search tooltip mismatch: {window.public_tab.search_btn.toolTip()!r}"
            )

        if window.games_tab.list_toggle_btn.toolTip() != "Скрыть таблицу списка":
            raise AssertionError(
                f"list-toggle tooltip mismatch: {window.games_tab.list_toggle_btn.toolTip()!r}"
            )
        duplicate_error = DuplicateGameError(1, "QA")
        if str(duplicate_error) != "Запись «QA» уже существует в списке.":
            raise AssertionError(
                f"duplicate fallback wording mismatch: {str(duplicate_error)!r}"
            )

        terminology_sources = {
            PROJECT_ROOT / "streaming_manager/views/main_window.py": (
                "Игр в восстановленной копии:",
            ),
            PROJECT_ROOT / "streaming_manager/db/services.py": (
                "Не удалось создать резервную копию перед очисткой игр.",
                "Ни одна игра не была удалена.",
                "Игры не были удалены.",
            ),
        }
        for source_path, forbidden_terms in terminology_sources.items():
            source_text = source_path.read_text(encoding="utf-8")
            for forbidden in forbidden_terms:
                if forbidden in source_text:
                    raise AssertionError(
                        f"legacy game wording remains in {source_path.name}: {forbidden!r}"
                    )

        if window.games_tab.clear_all_btn.text() != "Очистить список":
            raise AssertionError(
                f"clear-list button label mismatch: {window.games_tab.clear_all_btn.text()!r}"
            )

        original_messagebox_exec = QMessageBox.exec
        sorting_rules_capture = {}

        def capture_sorting_rules_exec(box):
            sorting_rules_capture["title"] = box.windowTitle()
            sorting_rules_capture["text"] = box.text()
            sorting_rules_capture["informative"] = box.informativeText()
            return QMessageBox.Ok

        QMessageBox.exec = capture_sorting_rules_exec
        try:
            window.games_tab.show_sorting_rules()
        finally:
            QMessageBox.exec = original_messagebox_exec

        if sorting_rules_capture.get("title") != "Правила сортировки":
            raise AssertionError(
                f"sorting-rules window title mismatch: {sorting_rules_capture!r}"
            )
        if sorting_rules_capture.get("text") != "Автоматическая сортировка списка":
            raise AssertionError(
                f"sorting-rules heading mismatch: {sorting_rules_capture!r}"
            )
        sorting_info = sorting_rules_capture.get("informative", "")
        for expected_text in (
            "Сначала список распределяется по статусу:",
            "• В режиме «Всего» сначала идут все записи вне архива",
            "• Архивные записи располагаются отдельным блоком в самом низу",
        ):
            if expected_text not in sorting_info:
                raise AssertionError(
                    f"sorting-rules wording missing {expected_text!r}: {sorting_info!r}"
                )
        for legacy_text in (
            "Сначала игры распределяются по статусу:",
            "• В режиме «Всего» все активные игры идут первыми",
            "• Архивные игры располагаются отдельным блоком в самом низу",
        ):
            if legacy_text in sorting_info:
                raise AssertionError(
                    f"legacy sorting-rules wording remains {legacy_text!r}"
                )

        original_information = QMessageBox.information
        import_help_capture = {}

        def capture_import_help(parent, title, message, *args, **kwargs):
            import_help_capture["title"] = title
            import_help_capture["message"] = message
            return QMessageBox.Ok

        QMessageBox.information = capture_import_help
        try:
            window.games_tab.show_import_csv_help()
        finally:
            QMessageBox.information = original_information

        if import_help_capture.get("title") != "Правила импорта CSV":
            raise AssertionError(
                f"CSV help title mismatch: {import_help_capture!r}"
            )
        import_help = import_help_capture.get("message", "")
        for expected_text in (
            "Обязательный столбец:\n• НАЗВАНИЕ",
            "• ДАТА",
            "• СТАТУС: ПРОХОДИТСЯ, НЕ ИГРАЛ, ИГРАЛ, ПРОЙДЕНО или ЗАБРОШЕНО",
            "Если баллов нет, рекомендуется указать 0.",
            "2. Формат «Название|Баллы»",
            "Файл без заголовка, одна запись в строке:",
            "Для совместимости также принимаются старые названия столбцов:",
            "• НАЗВАНИЕ ИГРЫ",
            "• ДАТА ВЫХОДА",
            "Если в файле найдена ошибка, импорт не применяется частично.",
        ):
            if expected_text not in import_help:
                raise AssertionError(
                    f"CSV help wording missing {expected_text!r}: {import_help!r}"
                )
        for legacy_text in (
            "Обязателен только столбец «НАЗВАНИЕ ИГРЫ».",
            "Для уже существующей игры",
            "Для новой игры",
            "одна игра в строке",
            "Название игры|Баллы",
        ):
            if legacy_text in import_help:
                raise AssertionError(
                    f"legacy CSV help wording remains {legacy_text!r}"
                )

        clear_dialog = DeleteAllGamesDialog(7)
        if clear_dialog.windowTitle() != "Очистить список":
            raise AssertionError(
                f"clear-list dialog title mismatch: {clear_dialog.windowTitle()!r}"
            )
        clear_labels = {label.text() for label in clear_dialog.findChildren(QLabel)}
        if "Будут удалены все записи: 7" not in clear_labels:
            raise AssertionError(f"clear-list heading mismatch: {sorted(clear_labels)!r}")
        expected_warning = (
            "Операция удалит обычные, архивные и временные записи. "
            "Завершённая история аукционов и Журнал сохранятся. Перед удалением "
            "программа автоматически создаст резервную копию текущей базы."
        )
        if expected_warning not in clear_labels:
            raise AssertionError(f"clear-list warning mismatch: {sorted(clear_labels)!r}")
        if DeleteAllGamesDialog.CONFIRM_TEXT != "УДАЛИТЬ ЗАПИСИ":
            raise AssertionError(
                f"clear-list confirm text mismatch: {DeleteAllGamesDialog.CONFIRM_TEXT!r}"
            )
        if clear_dialog.confirm_edit.placeholderText() != "УДАЛИТЬ ЗАПИСИ":
            raise AssertionError(
                f"clear-list placeholder mismatch: {clear_dialog.confirm_edit.placeholderText()!r}"
            )
        if clear_dialog.delete_button.text() != "Удалить записи":
            raise AssertionError(
                f"clear-list destructive button mismatch: {clear_dialog.delete_button.text()!r}"
            )
        clear_dialog.confirm_edit.setText("УДАЛИТЬ ЗАПИСИ ")
        app.processEvents()
        if clear_dialog.delete_button.isEnabled():
            raise AssertionError("clear-list destructive button enabled for inexact confirmation")
        clear_dialog.confirm_edit.setText("УДАЛИТЬ ЗАПИСИ")
        app.processEvents()
        if not clear_dialog.delete_button.isEnabled():
            raise AssertionError("clear-list destructive button not enabled for exact confirmation")
        clear_dialog.confirm_edit.returnPressed.emit()
        app.processEvents()
        if clear_dialog.result() != QDialog.Accepted:
            raise AssertionError("clear-list Enter confirmation semantics changed")
        clear_dialog.deleteLater()

        window.games_tab.clear_all_btn.setText("Очистка…")
        window.games_tab._clear_all_worker_finished()
        if window.games_tab.clear_all_btn.text() != "Очистить список":
            raise AssertionError(
                "clear-list button reverted to legacy text after worker completion"
            )

        add_dialog = GameDialog()
        if add_dialog.windowTitle() != "Добавить":
            raise AssertionError(
                f"add dialog title mismatch: {add_dialog.windowTitle()!r}"
            )

        if add_dialog.title_edit.placeholderText() != "Введите название":
            raise AssertionError(
                f"add dialog title placeholder mismatch: {add_dialog.title_edit.placeholderText()!r}"
            )
        if add_dialog.review_edit.placeholderText() != "Отзыв — можно оставить пустым":
            raise AssertionError(
                f"add dialog review placeholder mismatch: {add_dialog.review_edit.placeholderText()!r}"
            )
        add_dialog_labels = {label.text() for label in add_dialog.findChildren(QLabel)}
        if "Новая игра" in add_dialog_labels:
            raise AssertionError("legacy add dialog heading remains")
        expected_add_labels = {
            "Название:",
            "Дата (необязательно):",
            "Баллы (необязательно):",
            "Кооператив:",
            "Статус:",
            "Отзыв (необязательно):",
        }
        if not expected_add_labels.issubset(add_dialog_labels):
            raise AssertionError(
                f"add dialog field labels mismatch: {sorted(add_dialog_labels)!r}"
            )
        if (
            "Название игры:" in add_dialog_labels
            or "Дата выхода:" in add_dialog_labels
            or "Дата:" in add_dialog_labels
            or "Баллы:" in add_dialog_labels
            or "Отзыв:" in add_dialog_labels
            or "Кооператив (необязательно):" in add_dialog_labels
            or "Статус (необязательно):" in add_dialog_labels
        ):
            raise AssertionError("legacy/incorrect add dialog field labels remain")
        if add_dialog.amount_edit.value() != 0:
            raise AssertionError("optional points default changed from 0")

        def assert_date_caret_contract(dialog, mode):
            # Directly exercise the formatter with a caret in the middle:
            # auto-inserted separators must not force the caret to the end.
            dialog.date_edit.setText("26012010")
            dialog.date_edit.setCursorPosition(4)
            dialog._format_date_while_typing(dialog.date_edit.text())
            if dialog.date_edit.text() != "26.01.2010":
                raise AssertionError(
                    f"{mode} date auto-format changed: {dialog.date_edit.text()!r}"
                )
            if dialog.date_edit.cursorPosition() != 5:
                raise AssertionError(
                    f"{mode} date caret mapping mismatch after auto-format: "
                    f"{dialog.date_edit.cursorPosition()}"
                )

            # Backspace in the middle previously reproduced BUG-002:
            # the old code always jumped to len(formatted).
            dialog.date_edit.setText("26.01.2010")
            dialog.date_edit.setCursorPosition(4)
            QTest.keyClick(dialog.date_edit, Qt.Key.Key_Backspace)
            app.processEvents()
            if dialog.date_edit.cursorPosition() != 3:
                raise AssertionError(
                    f"{mode} date Backspace moved caret unexpectedly: "
                    f"{dialog.date_edit.cursorPosition()}, {dialog.date_edit.text()!r}"
                )
            if dialog.date_edit.cursorPosition() == len(dialog.date_edit.text()):
                raise AssertionError(f"{mode} date Backspace still jumps caret to end")

            # Delete in the middle follows the same ordinary QLineEdit caret rule.
            dialog.date_edit.setText("26.01.2010")
            dialog.date_edit.setCursorPosition(3)
            QTest.keyClick(dialog.date_edit, Qt.Key.Key_Delete)
            app.processEvents()
            if dialog.date_edit.cursorPosition() != 3:
                raise AssertionError(
                    f"{mode} date Delete moved caret unexpectedly: "
                    f"{dialog.date_edit.cursorPosition()}, {dialog.date_edit.text()!r}"
                )
            if dialog.date_edit.cursorPosition() == len(dialog.date_edit.text()):
                raise AssertionError(f"{mode} date Delete still jumps caret to end")

            # Replacing a selection should keep the ordinary collapsed caret
            # directly after the replacement, just like the title field.
            dialog.date_edit.setText("26.01.2010")
            dialog.date_edit.setSelection(3, 2)
            QTest.keyClicks(dialog.date_edit, "12")
            app.processEvents()
            if dialog.date_edit.text() != "26.12.2010":
                raise AssertionError(
                    f"{mode} date selection replacement changed text unexpectedly: "
                    f"{dialog.date_edit.text()!r}"
                )
            if dialog.date_edit.cursorPosition() != 5:
                raise AssertionError(
                    f"{mode} date selection replacement caret mismatch: "
                    f"{dialog.date_edit.cursorPosition()}"
                )

            # Sequential compact input must retain the established auto-dot behavior.
            dialog.date_edit.clear()
            QTest.keyClicks(dialog.date_edit, "26012010")
            app.processEvents()
            if dialog.date_edit.text() != "26.01.2010":
                raise AssertionError(
                    f"{mode} sequential compact date formatting changed: "
                    f"{dialog.date_edit.text()!r}"
                )
            if dialog.date_edit.cursorPosition() != len(dialog.date_edit.text()):
                raise AssertionError(
                    f"{mode} sequential date caret should remain at the end"
                )

        assert_date_caret_contract(add_dialog, "add")
        add_dialog.deleteLater()

        edit_game = Game(
            1,
            "QA",
            None,
            0,
            0,
            STATUS_NOT_PLAYED,
            "",
            updated_at=None,
        )
        edit_dialog = GameDialog(game=edit_game)
        if edit_dialog.windowTitle() != "Изменить":
            raise AssertionError(
                f"edit dialog title mismatch: {edit_dialog.windowTitle()!r}"
            )
        edit_dialog_labels = {label.text() for label in edit_dialog.findChildren(QLabel)}
        if "Редактирование записи" in edit_dialog_labels:
            raise AssertionError("legacy edit dialog heading remains")
        expected_edit_labels = {
            "Название:",
            "Дата (необязательно):",
            "Баллы (необязательно):",
            "Кооператив:",
            "Статус:",
            "Отзыв (необязательно):",
        }
        if not expected_edit_labels.issubset(edit_dialog_labels):
            raise AssertionError(
                f"edit dialog field labels mismatch: {sorted(edit_dialog_labels)!r}"
            )
        if (
            "Название игры:" in edit_dialog_labels
            or "Дата выхода:" in edit_dialog_labels
            or "Дата:" in edit_dialog_labels
            or "Баллы:" in edit_dialog_labels
            or "Отзыв:" in edit_dialog_labels
            or "Кооператив (необязательно):" in edit_dialog_labels
            or "Статус (необязательно):" in edit_dialog_labels
        ):
            raise AssertionError("legacy/incorrect edit dialog field labels remain")
        assert_date_caret_contract(edit_dialog, "edit")
        edit_dialog.deleteLater()
        app.processEvents()

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
