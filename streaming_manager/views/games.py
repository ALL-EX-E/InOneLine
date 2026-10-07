from __future__ import annotations

import time
from typing import Callable

from PySide6.QtCore import Qt, QThreadPool, QTimer
from PySide6.QtGui import QBrush, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..app_paths import AppPaths
from ..constants import (
    COOP_LABELS,
    STATUS_ABANDONED,
    STATUS_COMPLETED,
    STATUS_LABELS,
    STATUS_NOT_PLAYED,
    STATUS_PLAYED,
    STATUS_PLAYING,
)
from ..diagnostic_logs import append_performance_trace
from ..database import (
    Database,
    DuplicateGameError,
    Game,
    display_date,
    display_datetime_local,
    format_points,
    normalize_date_text,
    parse_date,
)
from ..workers import FunctionWorker
from .common import (
    ScrollSafeSpinBox,
    _selected_id,
    autosize_compact_columns_once,
    suspend_live_content_resize,
)

class GameDialog(QDialog):
    def __init__(
        self,
        parent=None,
        game: Game | None = None,
        duplicate_lookup: Callable[[str], Game | None] | None = None,
    ):
        super().__init__(parent)
        self.game = game
        self.duplicate_lookup = duplicate_lookup
        self.existing_game_id: int | None = None
        self._closing_after_save = False
        self._original_state = None
        self.setWindowTitle("Изменить игру" if game else "Добавить игру")
        self.setMinimumSize(620, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Редактирование записи" if game else "Новая игра")
        title.setStyleSheet("font-size: 15pt; font-weight: 700;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Например: Control")
        self.title_edit.setClearButtonEnabled(True)

        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("ДД.ММ.ГГГГ, 26012010 или 26 января 2010")
        self.date_edit.setClearButtonEnabled(True)
        self.date_edit.setMaximumWidth(320)
        self.date_edit.setToolTip(
            "Можно вводить: 26.01.2010, 26012010, 26-01-2010, "
            "26/01/2010 или 26 января 2010"
        )
        self.date_edit.textEdited.connect(self._format_date_while_typing)
        self.date_edit.editingFinished.connect(self._normalize_date_field)

        self.amount_edit = ScrollSafeSpinBox()
        self.amount_edit.setRange(0, 999_999_999)
        self.amount_edit.setSingleStep(100)
        self.amount_edit.setButtonSymbols(
            QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self.amount_edit.setMaximumWidth(220)

        self.coop_combo = QComboBox()
        self.coop_combo.addItem("НЕ КООП", 0)
        self.coop_combo.addItem("КООП", 1)
        self.coop_combo.setMaximumWidth(220)

        self.status_combo = QComboBox()
        for value in (
            STATUS_PLAYING,
            STATUS_NOT_PLAYED,
            STATUS_PLAYED,
            STATUS_COMPLETED,
            STATUS_ABANDONED,
        ):
            self.status_combo.addItem(STATUS_LABELS[value], value)
        self.status_combo.setMaximumWidth(220)

        self.review_edit = QTextEdit()
        self.review_edit.setPlaceholderText("Отзыв по игре — можно оставить пустым")
        self.review_edit.setMinimumHeight(150)

        form.addRow("Название игры:", self.title_edit)
        form.addRow("Дата выхода:", self.date_edit)
        form.addRow("Баллы:", self.amount_edit)
        form.addRow("Кооператив:", self.coop_combo)
        form.addRow("Статус:", self.status_combo)
        form.addRow("Отзыв:", self.review_edit)
        layout.addLayout(form)

        if game:
            info = QLabel(
                f"ID: {game.id}    •    Последнее изменение: {display_datetime_local(game.updated_at)}"
            )
            info.setProperty("muted", True)
            layout.addWidget(info)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Сохранить")
        buttons.button(QDialogButtonBox.Save).setProperty("primary", True)
        buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if game:
            self.title_edit.setText(game.title)
            self.date_edit.setText(display_date(game.release_date))
            self.amount_edit.setValue(game.amount)
            self.coop_combo.setCurrentIndex(self.coop_combo.findData(game.coop))
            self.status_combo.setCurrentIndex(self.status_combo.findData(game.status))
            self.review_edit.setPlainText(game.review)

        # Снимок формы нужен только для предупреждения о несохранённых изменениях.
        # Он хранит именно видимые значения, поэтому работает даже если пользователь
        # временно ввёл некорректную дату и пытается закрыть окно.
        self._original_state = self._form_state()
        self.title_edit.setFocus()

    def _format_date_while_typing(self, text: str):
        """Ставит точки автоматически при обычном цифровом вводе."""
        if not text:
            return

        # Если пользователь вводит слова, пробелы, дефисы или слеши,
        # не мешаем ему: такой ввод нормализуется после завершения поля.
        if any(ch not in "0123456789." for ch in text):
            return

        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) > 8:
            return

        trailing_dot = text.endswith(".")

        if len(digits) <= 2:
            formatted = digits
            if trailing_dot and len(digits) == 2:
                formatted += "."
        elif len(digits) <= 4:
            formatted = f"{digits[:2]}.{digits[2:]}"
            if trailing_dot and len(digits) == 4:
                formatted += "."
        else:
            formatted = f"{digits[:2]}.{digits[2:4]}.{digits[4:]}"

        if formatted == text:
            return

        self.date_edit.blockSignals(True)
        self.date_edit.setText(formatted)
        self.date_edit.setCursorPosition(len(formatted))
        self.date_edit.blockSignals(False)

    def _normalize_date_field(self):
        """Приводит распознанную дату к ДД.ММ.ГГГГ без всплывающей ошибки."""
        text = self.date_edit.text().strip()
        if not text:
            return

        try:
            normalized = normalize_date_text(text)
        except ValueError:
            # Ошибка будет показана только при попытке сохранения.
            return

        if normalized != text:
            self.date_edit.setText(normalized)

    def _form_state(self) -> tuple:
        return (
            self.title_edit.text(),
            self.date_edit.text(),
            int(self.amount_edit.value()),
            int(self.coop_combo.currentData()),
            str(self.status_combo.currentData()),
            self.review_edit.toPlainText(),
        )

    def _has_unsaved_changes(self) -> bool:
        return self._original_state is not None and self._form_state() != self._original_state

    def _ask_yes_no(self, title: str, text: str, default_no: bool = True) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle(title)
        box.setText(text)
        yes_btn = box.addButton("Да", QMessageBox.ButtonRole.YesRole)
        no_btn = box.addButton("Нет", QMessageBox.ButtonRole.NoRole)
        box.setDefaultButton(no_btn if default_no else yes_btn)
        box.exec()
        return box.clickedButton() is yes_btn

    def _validate_and_accept(self):
        # Перед проверкой приводим любой распознанный вариант даты
        # к единому отображаемому формату ДД.ММ.ГГГГ.
        self._normalize_date_field()

        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Проверка", "Введите название игры.")
            return
        try:
            parse_date(self.date_edit.text())
        except ValueError:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Такой даты не существует. Введите правильную дату",
            )
            return

        # Не допускаем одинаковые названия ни при добавлении, ни при
        # переименовании существующей игры.
        if self.duplicate_lookup is not None:
            existing = self.duplicate_lookup(self.title_edit.text())
            if existing is not None:
                archive_note = (
                    "\n\nИгра находится в архиве."
                    if existing.archived
                    else ""
                )
                QMessageBox.warning(
                    self,
                    "Игра уже существует",
                    f"Данная игра уже есть в списке:\n\n«{existing.title}»"
                    f"{archive_note}",
                )
                if self.game is None:
                    # Для добавления сохраняем прежнее поведение:
                    # закрываем форму и переходим к найденной записи.
                    self.existing_game_id = existing.id
                    self._closing_after_save = True
                    self.reject()
                else:
                    # При переименовании оставляем форму открытой, чтобы
                    # пользователь мог исправить название.
                    self.title_edit.setFocus()
                    self.title_edit.selectAll()
                return

        # Для существующей игры подтверждение показываем только тогда,
        # когда пользователь действительно что-то изменил.
        # Если форма не менялась (или изменения были полностью возвращены назад),
        # кнопка «Сохранить» просто закрывает окно без лишнего вопроса.
        if self.game and not self._has_unsaved_changes():
            self._closing_after_save = True
            self.accept()
            return

        prompt = (
            "Точно сохранить изменения?"
            if self.game
            else "Точно сохранить новую игру?"
        )
        if not self._ask_yes_no("Подтверждение сохранения", prompt):
            return

        self._closing_after_save = True
        self.accept()

    def reject(self):
        if self._closing_after_save:
            super().reject()
            return
        if self._has_unsaved_changes():
            if not self._ask_yes_no(
                "Несохранённые изменения",
                "Есть несохранённые изменения.\n\nЗакрыть без сохранения?",
            ):
                return
        super().reject()

    def closeEvent(self, event):
        if self._closing_after_save or not self._has_unsaved_changes():
            event.accept()
            return
        if self._ask_yes_no(
            "Несохранённые изменения",
            "Есть несохранённые изменения.\n\nЗакрыть без сохранения?",
        ):
            event.accept()
        else:
            event.ignore()

    def payload(self) -> dict:
        return {
            "title": self.title_edit.text().strip(),
            "release_date": parse_date(self.date_edit.text()),
            "sm_points": int(self.amount_edit.value()),
            "coop": int(self.coop_combo.currentData()),
            "status": str(self.status_combo.currentData()),
            "review": self.review_edit.toPlainText().strip(),
        }

class DeleteAllGamesDialog(QDialog):
    CONFIRM_TEXT = "УДАЛИТЬ ВСЕ ИГРЫ"

    def __init__(self, game_count: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Очистить все игры?")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel(f"Будут удалены все игры: {int(game_count)}")
        title.setStyleSheet("font-size: 14pt; font-weight: 700;")
        layout.addWidget(title)

        warning = QLabel(
            "Операция удалит обычные, архивные и временные игровые записи. "
            "Завершённая история аукционов и Журнал сохранятся. Перед удалением "
            "программа автоматически создаст резервную копию текущей базы."
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)

        prompt = QLabel(
            "Для подтверждения введите точно:\n" + self.CONFIRM_TEXT
        )
        prompt.setWordWrap(True)
        layout.addWidget(prompt)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setPlaceholderText(self.CONFIRM_TEXT)
        self.confirm_edit.setClearButtonEnabled(True)
        layout.addWidget(self.confirm_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.delete_button = QPushButton("Удалить все игры")
        self.delete_button.setProperty("danger", True)
        self.delete_button.setEnabled(False)
        buttons.addButton(self.delete_button, QDialogButtonBox.DestructiveRole)
        buttons.rejected.connect(self.reject)
        self.delete_button.clicked.connect(self.accept)
        layout.addWidget(buttons)

        self.confirm_edit.textChanged.connect(
            lambda text: self.delete_button.setEnabled(text == self.CONFIRM_TEXT)
        )
        self.confirm_edit.returnPressed.connect(self._accept_if_confirmed)
        self.confirm_edit.setFocus()

    def _accept_if_confirmed(self):
        if self.confirm_edit.text() == self.CONFIRM_TEXT:
            self.accept()


class GamesTab(QWidget):
    _COMPACT_COLUMNS = (0, 1, 2, 4, 5, 6, 7)

    def __init__(self, db: Database, changed: Callable[[], None]):
        super().__init__()
        self.db = db
        self.changed = changed
        self.thread_pool = QThreadPool.globalInstance()
        self._delete_worker: FunctionWorker | None = None
        self._clear_all_worker: FunctionWorker | None = None
        self._import_worker: FunctionWorker | None = None
        self.active_filter = "all"
        self.filter_buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по названию или отзыву…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._search_text_changed)
        self.search.returnPressed.connect(self.activate_search)

        self.search_btn = QPushButton("Найти")
        self.search_btn.setToolTip(
            "Показать список и перейти к первой найденной игре"
        )
        self.search_btn.clicked.connect(self.activate_search)

        self.reset_filters_btn = QPushButton("Сбросить фильтры")
        self.reset_filters_btn.setToolTip(
            "Очистить поиск и показать все игры, включая архив"
        )
        self.reset_filters_btn.clicked.connect(self.reset_filters)

        filters.addWidget(self.search, 1)
        filters.addWidget(self.search_btn)
        filters.addWidget(self.reset_filters_btn)
        layout.addLayout(filters)

        actions = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.setProperty("primary", True)
        self.edit_btn = QPushButton("Изменить")
        self.archive_btn = QPushButton("В архив")
        self.archive_btn.setProperty("danger", True)
        self.restore_btn = QPushButton("Восстановить из архива")
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.setProperty("danger", True)
        self.delete_btn.setToolTip("Безвозвратно удалить выбранную игру и все связанные с ней данные")
        self.import_btn = QPushButton("Импорт CSV")
        self.import_btn.setToolTip("Импортировать игры из CSV. Правила формата — кнопка ?")
        self.import_help_btn = QPushButton("?")
        self.import_help_btn.setFixedWidth(34)
        self.import_help_btn.setToolTip("Правила импорта CSV")
        self.clear_all_btn = QPushButton("Очистить все игры…")
        self.clear_all_btn.setProperty("danger", True)
        self.clear_all_btn.setToolTip(
            "Удалить все игровые записи после подтверждения и обязательного safety-backup"
        )

        self.add_btn.clicked.connect(self.add_game)
        self.edit_btn.clicked.connect(self.edit_game)
        self.archive_btn.clicked.connect(lambda: self.archive_selected(True))
        self.restore_btn.clicked.connect(lambda: self.archive_selected(False))
        self.delete_btn.clicked.connect(self.delete_selected)
        self.import_btn.clicked.connect(self.import_csv)
        self.import_help_btn.clicked.connect(self.show_import_csv_help)
        self.clear_all_btn.clicked.connect(self.clear_all_games)

        for w in (
            self.add_btn,
            self.edit_btn,
            self.archive_btn,
            self.restore_btn,
            self.delete_btn,
            self.import_btn,
            self.import_help_btn,
        ):
            actions.addWidget(w)
        actions.addStretch()
        actions.addWidget(self.clear_all_btn)
        layout.addLayout(actions)

        stats = QHBoxLayout()
        stats.setSpacing(8)

        def make_stat_button(key: str, tooltip: str) -> QPushButton:
            button = QPushButton()
            button.setProperty("statFilter", True)
            button.setCheckable(True)
            button.setAutoExclusive(False)
            button.setToolTip(tooltip)
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            button.setMinimumHeight(30)
            button.setMaximumHeight(34)
            button.clicked.connect(
                lambda checked=False, filter_key=key: self.apply_stat_filter(filter_key)
            )
            self.filter_buttons[key] = button
            stats.addWidget(button, 0, Qt.AlignTop)
            return button

        self.total_badge = make_stat_button(
            "all",
            "Показать все игры в базе, включая архив. Архивные записи идут внизу.",
        )
        self.playing_badge = make_stat_button(
            STATUS_PLAYING,
            "Показать только игры со статусом ПРОХОДИТСЯ",
        )
        self.auction_badge = make_stat_button(
            "middle",
            "Показать игры со статусами ИГРАЛ и НЕ ИГРАЛ",
        )
        self.played_badge = make_stat_button(
            STATUS_PLAYED,
            "Показать только игры со статусом ИГРАЛ",
        )
        self.not_played_badge = make_stat_button(
            STATUS_NOT_PLAYED,
            "Показать только игры со статусом НЕ ИГРАЛ",
        )
        self.completed_badge = make_stat_button(
            STATUS_COMPLETED,
            "Показать только игры со статусом ПРОЙДЕНО",
        )
        self.abandoned_badge = make_stat_button(
            STATUS_ABANDONED,
            "Показать только игры со статусом ЗАБРОШЕНО",
        )
        self.archived_badge = make_stat_button(
            "archive",
            "Показать только игры из архива",
        )

        # Ранее КООП / НЕ КООП были вариантами выпадающего меню.
        # Чтобы после удаления меню функциональность не пропала,
        # они также становятся кликабельными статистическими фильтрами.
        self.coop_badge = make_stat_button(
            "coop",
            "Показать только кооперативные игры",
        )
        self.noncoop_badge = make_stat_button(
            "noncoop",
            "Показать только некооперативные игры",
        )

        stats.addStretch()
        stats.setAlignment(Qt.AlignTop)
        layout.addLayout(stats)

        sorting_actions = QHBoxLayout()
        self.sorting_rules_btn = QPushButton("Правила сортировки")
        self.sorting_rules_btn.setToolTip(
            "Показать полный порядок автоматической сортировки списка"
        )
        self.sorting_rules_btn.clicked.connect(self.show_sorting_rules)

        self.list_toggle_btn = QPushButton("Скрыть список")
        self.list_toggle_btn.setToolTip("Скрыть или показать таблицу со списком игр")
        self.list_toggle_btn.clicked.connect(self.toggle_games_list)

        self.copy_list_overlay_url_btn = QPushButton("Копировать URL списка")
        self.copy_list_overlay_url_btn.setToolTip(
            "Скопировать URL отдельного OBS-списка с Top-3 и прокручиваемым списком"
        )
        self.open_list_overlay_preview_btn = QPushButton(
            "Открыть предпросмотр списка"
        )
        self.open_list_overlay_preview_btn.setToolTip(
            "Открыть отдельный OBS-список с Top-3 и прокручиваемым списком"
        )

        sorting_actions.addWidget(self.sorting_rules_btn)
        sorting_actions.addWidget(self.list_toggle_btn)
        sorting_actions.addWidget(self.copy_list_overlay_url_btn)
        sorting_actions.addWidget(self.open_list_overlay_preview_btn)
        sorting_actions.addStretch()
        layout.addLayout(sorting_actions)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "ID", "СТАРТ", "ТЕКУЩАЯ", "НАЗВАНИЕ ИГРЫ", "ДАТА ВЫХОДА",
            "БАЛЛЫ", "КООП/НЕ КООП", "СТАТУС", "ОТЗЫВ",
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.hideColumn(0)

        header = self.table.horizontalHeader()
        # ResizeToContents is useful for the compact metadata columns, but a
        # visible 100+ row QTableWidget can otherwise rescan every row during
        # each catch-up refresh.  Precision 0 asks Qt to measure only the
        # visible area while preserving the same resize mode and appearance.
        header.setResizeContentsPrecision(0)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        # The game-title header is longer than the short contents often shown
        # in the first visible rows. Keep it user-resizable but never allow the
        # native Windows section to become narrower than the full header label.
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.Stretch)
        header.sectionResized.connect(self._clamp_game_title_column_width)
        self._ensure_game_title_column_width()
        QTimer.singleShot(0, self._ensure_game_title_column_width)

        self.table.doubleClicked.connect(self.edit_game)
        self.table.itemSelectionChanged.connect(self._update_action_state)
        layout.addWidget(self.table, 1)

        # Когда таблица скрыта в развёрнутом/растянутом окне, это растяжение
        # забирает свободную высоту на себя. Панель управления остаётся сверху
        # и не деформируется.
        self.hidden_list_spacer = QWidget()
        self.hidden_list_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.hidden_list_spacer.hide()
        layout.addWidget(self.hidden_list_spacer, 1)

        self.shortcuts = []
        for key, handler in (
            ("Ctrl+N", self.add_game),
            ("Ctrl+E", self.edit_game),
            ("Ctrl+F", lambda: self.search.setFocus()),
            ("F5", self.refresh),
        ):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(handler)
            self.shortcuts.append(shortcut)

        self.refresh()

    def attach_shared_xlsx_controls(self, sync_host) -> None:
        """Host the existing shared-main-list XLSX controls on Games.

        R1.0.9 intentionally reuses the already-tested synchronization engine
        owned by AuctionTab; only its visible widgets are re-parented here.
        """
        if getattr(self, "shared_xlsx_section", None) is not None:
            return

        section = QFrame()
        section.setFrameShape(QFrame.StyledPanel)
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(10, 8, 10, 8)
        section_layout.setSpacing(6)

        title = QLabel("Совместная таблица")
        title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        section_layout.addWidget(title)

        description = QLabel(
            "Обычный XLSX с основным списком игр. Файл можно хранить в папке "
            "Google Drive Desktop и редактировать через Google Таблицы. Все "
            "подключённые экземпляры In one line равноправны; применяется "
            "последняя полученная версия файла."
        )
        description.setWordWrap(True)
        description.setProperty("muted", True)
        section_layout.addWidget(description)

        buttons = QHBoxLayout()
        buttons.addWidget(sync_host.shared_xlsx_create_btn)
        buttons.addWidget(sync_host.shared_xlsx_connect_btn)
        buttons.addWidget(sync_host.shared_xlsx_disconnect_btn)
        buttons.addStretch()
        section_layout.addLayout(buttons)

        form = QFormLayout()
        form.addRow("Таблица:", sync_host.shared_xlsx_path_label)
        form.addRow("Состояние:", sync_host.shared_xlsx_status_label)
        form.addRow("Последнее изменение:", sync_host.shared_xlsx_modified_label)
        section_layout.addLayout(form)

        self.shared_xlsx_section = section
        table_index = self.layout().indexOf(self.table)
        if table_index < 0:
            self.layout().addWidget(section)
        else:
            self.layout().insertWidget(table_index, section)

    def _game_title_header_min_width(self) -> int:
        """Return a DPI-aware floor that always fits ``НАЗВАНИЕ ИГРЫ``."""
        header = self.table.horizontalHeader()
        self.table.ensurePolished()
        header.ensurePolished()
        item = self.table.horizontalHeaderItem(3)
        text = item.text() if item is not None else "НАЗВАНИЕ ИГРЫ"
        metrics = header.fontMetrics()
        padding = max(44, metrics.horizontalAdvance("MMMM"))
        return max(
            header.minimumSectionSize(),
            header.sectionSizeHint(3),
            metrics.horizontalAdvance(text) + padding,
        )

    def _ensure_game_title_column_width(self) -> None:
        required = self._game_title_header_min_width()
        if self.table.columnWidth(3) < required:
            self.table.setColumnWidth(3, required)

    def _clamp_game_title_column_width(
        self, logical_index: int, old_size: int, new_size: int
    ) -> None:
        _ = old_size
        if logical_index != 3:
            return
        required = self._game_title_header_min_width()
        if new_size < required:
            self.table.setColumnWidth(3, required)

    def set_games_list_visible(self, visible: bool, adjust_window: bool = True):
        # R1.0.7: list visibility is a child-layout concern only. The previous
        # compact-window implementation changed MainWindow minimumHeight/resize
        # here, which caused tab jumps and the confirmed duplicate-game shrink.
        _ = adjust_window

        if not visible:
            self.table.clearSelection()
            self.table.setCurrentCell(-1, -1)

        self.table.setVisible(visible)
        self.hidden_list_spacer.setVisible(not visible)
        self.list_toggle_btn.setText(
            "Скрыть список" if visible else "Показать список"
        )
        self.list_toggle_btn.setToolTip(
            "Скрыть таблицу со списком игр"
            if visible
            else "Показать таблицу со списком игр"
        )
        self._update_action_state()

    def toggle_games_list(self):
        self.set_games_list_visible(self.table.isHidden())

    def _show_synced_lists(self):
        """Показывает оба синхронизированных списка через главное окно."""
        window = self.window()
        if hasattr(window, "set_synced_lists_visible"):
            window.set_synced_lists_visible(True)
        else:
            self.set_games_list_visible(True)

    def _search_text_changed(self, text: str):
        """Refresh the visible source once and synchronize hidden search views."""
        window = self.window()
        if hasattr(window, "sync_search_text"):
            window.sync_search_text("games", text)
        else:
            self.refresh()

    def _notify_search_text_changed(self):
        """Передаёт текущее содержимое поиска второй вкладке."""
        window = self.window()
        if hasattr(window, "sync_search_text"):
            window.sync_search_text("games", self.search.text())
        else:
            self.refresh()

    def _select_game_row(self, game_id: int) -> bool:
        """Выделяет игру в текущей таблице без изменения строки поиска."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                continue
            try:
                row_id = int(item.text())
            except ValueError:
                continue
            if row_id != game_id:
                continue

            self.table.selectRow(row)
            visible_item = self.table.item(row, 3)
            if visible_item is not None:
                self.table.scrollToItem(visible_item)
            self._update_action_state()
            return True
        return False

    def select_synced_search_result(self, game_id: int, ensure_visible: bool = False):
        """Выделяет тот же результат поиска, что и на второй вкладке."""
        game = self.db.get_game(game_id)
        if game is None:
            return

        if ensure_visible:
            # Публичный список содержит только активные записи.
            # Чтобы та же игра гарантированно была видна на вкладке «Игры»,
            # сбрасываем только статусный фильтр, но сохраняем строку поиска.
            self.active_filter = "all"
            self._sync_filter_buttons()
            self.refresh()

        self._select_game_row(game_id)

    def activate_search(self):
        """Показывает список и переходит к первой строке результата поиска."""
        query = self.search.text().strip()

        # Если список скрыт — поиск по Enter или кнопке «Найти»
        # раскрывает обе синхронизированные таблицы.
        self._show_synced_lists()
        self.refresh()

        if self.table.rowCount() == 0:
            if query:
                QMessageBox.information(
                    self,
                    "Поиск",
                    f"По запросу «{query}» ничего не найдено.",
                )
            return

        # Таблица уже отфильтрована текущей строкой поиска.
        # Выбираем первую найденную запись и синхронизируем этот же результат
        # со второй вкладкой.
        self.table.selectRow(0)
        target = self.table.item(0, 3)
        if target is not None:
            self.table.scrollToItem(target)
        self.table.setFocus()
        self._update_action_state()

        game_id = self.selected_game_id()
        window = self.window()
        if game_id is not None and hasattr(window, "sync_search_result"):
            window.sync_search_result(game_id, source="games")

    def show_sorting_rules(self):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("Правила сортировки")
        box.setText("Автоматическая сортировка списка игр")
        box.setInformativeText(
            "Сначала игры распределяются по статусу:\n\n"
            "1. ПРОХОДИТСЯ\n"
            "2. ИГРАЛ / НЕ ИГРАЛ\n"
            "3. ПРОЙДЕНО\n"
            "4. ЗАБРОШЕНО\n\n"
            "Внутри ПРОХОДИТСЯ:\n"
            "• Дата выхода — от новой к старой\n"
            "• Баллы — от большего к меньшему\n"
            "• Последнее изменение — новое выше\n"
            "• ID — технический финальный критерий\n\n"
            "Внутри ИГРАЛ / НЕ ИГРАЛ, ПРОЙДЕНО и ЗАБРОШЕНО:\n"
            "• Баллы — от большего к меньшему\n"
            "• Дата выхода — от новой к старой\n"
            "• Последнее изменение — новое выше\n"
            "• ID — технический финальный критерий\n\n"
            "Архив:\n"
            "• В режиме «Всего» все активные игры идут первыми\n"
            "• Архивные игры располагаются отдельным блоком в самом низу\n"
            "• Внутри архива применяются те же правила сортировки по статусам"
        )
        box.setStandardButtons(QMessageBox.Ok)
        box.exec()

    def selected_game_id(self) -> int | None:
        return _selected_id(self.table)

    def _apply_action_state(self, game: Game | None, total_games: int) -> None:
        # CSV import, single permanent delete and full clear are destructive/
        # mass operations that run in QThreadPool. Keep other game mutations disabled until the
        # active worker finishes so the same rows cannot be edited concurrently.
        worker_busy = (
            self._delete_worker is not None
            or self._clear_all_worker is not None
            or self._import_worker is not None
        )
        self.add_btn.setEnabled(not worker_busy)
        self.import_btn.setEnabled(not worker_busy)
        self.import_help_btn.setEnabled(not worker_busy)
        self.clear_all_btn.setEnabled(int(total_games) > 0 and not worker_busy)

        if self.table.isHidden():
            self.edit_btn.setEnabled(False)
            self.archive_btn.setVisible(False)
            self.restore_btn.setVisible(False)
            self.delete_btn.setEnabled(False)
            return

        self.edit_btn.setEnabled(bool(game) and not worker_busy)
        archive_visible = bool(game and not game.archived)
        restore_visible = bool(game and game.archived)
        self.archive_btn.setVisible(archive_visible)
        self.restore_btn.setVisible(restore_visible)
        self.archive_btn.setEnabled(archive_visible and not worker_busy)
        self.restore_btn.setEnabled(restore_visible and not worker_busy)
        self.delete_btn.setEnabled(bool(game) and not worker_busy)

    def _update_action_state(self):
        # Selection-only changes are infrequent and can query the database. The
        # full refresh path passes its already-loaded snapshot to avoid two extra
        # short SQLite connections on every table rebuild.
        game_id = self.selected_game_id()
        game = self.db.get_game(game_id) if game_id is not None else None
        self._apply_action_state(game, self.db.count_all_games())

    def _update_stats(self, stats: dict[str, int] | None = None):
        stats = self.db.game_stats() if stats is None else stats

        # «Всего» — это общее количество обычных записей, включая архив.
        # Временные auction_only-лоты до завершения сессии сюда не входят.
        self.total_badge.setText(f"Всего: {stats['total']}")
        self.playing_badge.setText(f"Проходится: {stats['playing']}")
        self.auction_badge.setText(f"ДЛЯ АУКА: {stats['for_auction']}")
        self.played_badge.setText(f"Играл: {stats['played']}")
        self.not_played_badge.setText(f"Не играл: {stats['not_played']}")
        self.completed_badge.setText(f"Пройдено: {stats['completed']}")
        self.abandoned_badge.setText(f"Заброшено: {stats['abandoned']}")
        self.archived_badge.setText(f"Архив: {stats['archived']}")
        self.coop_badge.setText(f"Кооп: {stats['coop']}")
        self.noncoop_badge.setText(f"Не кооп: {stats['noncoop']}")
        self._sync_filter_buttons()

    def refresh(self):
        started = time.perf_counter()
        selected = self.selected_game_id()
        snapshot = self.db.games_refresh_snapshot(
            self.search.text(),
            self.active_filter,
            include_archived=(self.active_filter in ("all", "archive")),
        )
        games = snapshot["games"]
        positions = snapshot["positions"]
        stats = snapshot["stats"]
        db_seconds = time.perf_counter() - started
        previous_blocked = self.table.blockSignals(True)
        suspend_live_content_resize(self.table, self._COMPACT_COLUMNS)
        self.table.setUpdatesEnabled(False)
        fill_started = time.perf_counter()
        fill_seconds = 0.0
        autosize_seconds = 0.0
        reactivate_seconds = 0.0
        post_seconds = 0.0
        selected_row = -1

        status_colors = {
            STATUS_PLAYING: QColor("#76c7f0"),
            STATUS_PLAYED: QColor("#9bd59b"),
            STATUS_NOT_PLAYED: QColor("#e6d58a"),
            STATUS_COMPLETED: QColor("#b3a4d9"),
            STATUS_ABANDONED: QColor("#c58f8f"),
        }

        try:
            self.table.setRowCount(len(games))
            for r, g in enumerate(games):
                start_position, current_position = positions.get(g.id, (None, None))
                values = [
                    str(g.id),
                    "" if start_position is None else str(start_position),
                    "" if current_position is None else str(current_position),
                    g.title,
                    display_date(g.release_date),
                    format_points(g.sm_points),
                    COOP_LABELS[g.coop],
                    g.status_label,
                    g.review,
                ]
                for c, value in enumerate(values):
                    # Reuse existing QTableWidgetItems whenever the row/cell
                    # still exists. Large lists otherwise allocate and destroy
                    # thousands of Qt objects on every refresh, increasing GUI
                    # latency and allocator/RAM churn without changing content.
                    item = self.table.item(r, c)
                    if item is None:
                        item = QTableWidgetItem()
                        self.table.setItem(r, c, item)
                    if item.text() != value:
                        item.setText(value)

                    if c in (1, 2, 4, 5, 6, 7):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                    tooltip = g.review if c == 8 and g.review else ""
                    if g.archived:
                        item.setForeground(QColor("#7e8489"))
                        tooltip = (tooltip + "\n" if tooltip else "") + "Запись находится в архиве"
                    elif c == 7:
                        item.setForeground(status_colors.get(g.status, QColor("#eeeeee")))
                    else:
                        item.setForeground(QBrush())
                    item.setToolTip(tooltip)
                if g.id == selected:
                    selected_row = r
            fill_seconds = time.perf_counter() - fill_started

            autosize_started = time.perf_counter()
            autosize_compact_columns_once(self.table, self._COMPACT_COLUMNS)
            autosize_seconds = time.perf_counter() - autosize_started

            reactivate_started = time.perf_counter()
            self.table.setUpdatesEnabled(True)
            reactivate_seconds = time.perf_counter() - reactivate_started

            post_started = time.perf_counter()
            if selected_row >= 0:
                self.table.selectRow(selected_row)
            elif games:
                self.table.selectRow(0)
            self._update_stats(stats)
        finally:
            if not self.table.updatesEnabled():
                self.table.setUpdatesEnabled(True)
            self.table.blockSignals(previous_blocked)
        selected_after_refresh = self.selected_game_id()
        selected_game = next(
            (game for game in games if game.id == selected_after_refresh),
            None,
        )
        self._apply_action_state(selected_game, stats["total"])
        post_seconds = time.perf_counter() - post_started
        try:
            append_performance_trace(
                AppPaths.from_database_path(self.db.path).logs_dir,
                "GAMES_REFRESH "
                f"rows={len(games)} db={db_seconds:.3f}s "
                f"fill={fill_seconds:.3f}s "
                f"autosize={autosize_seconds:.3f}s "
                f"reactivate={reactivate_seconds:.3f}s "
                f"post={post_seconds:.3f}s "
                f"total={time.perf_counter()-started:.3f}s",
            )
        except Exception:
            pass

    def add_game(self):
        dlg = GameDialog(self, duplicate_lookup=self.db.find_game_by_title)
        result = dlg.exec()

        if dlg.existing_game_id is not None:
            self.focus_game(dlg.existing_game_id)
            return

        if result == QDialog.Accepted:
            try:
                self.db.add_game(Game(id=None, archived=0, **dlg.payload()))
            except DuplicateGameError as exc:
                QMessageBox.warning(
                    self,
                    "Игра уже существует",
                    f"Данная игра уже есть в списке:\n\n«{exc.existing_title}»",
                )
                self.focus_game(exc.existing_id)
                return
            self.changed()

    def _sync_filter_buttons(self):
        for key, button in self.filter_buttons.items():
            button.blockSignals(True)
            button.setChecked(key == self.active_filter)
            button.blockSignals(False)

    def apply_stat_filter(self, filter_key: str):
        """Применяет фильтр по нажатию на показатель статистики."""
        self.active_filter = filter_key
        self._sync_filter_buttons()
        self.refresh()

        # Если список был скрыт, фильтрация сама по себе его не открывает:
        # пользователь может смотреть только статистику. Для просмотра результата
        # используется «Показать список», «Найти» или Enter в поиске.

    def reset_filters(self):
        """Сбрасывает поиск и показывает всю базу, включая архив."""
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)

        self.active_filter = "all"
        self._sync_filter_buttons()
        self._notify_search_text_changed()
        self.refresh()
        self.search.setFocus()

    def focus_game(self, game_id: int):
        """Сбрасывает скрывающие фильтры и выделяет нужную игру."""
        game = self.db.get_game(game_id)
        if not game:
            return

        # Если список был скрыт, показываем обе синхронизированные таблицы,
        # иначе состояние кнопок на двух вкладках разойдётся.
        self._show_synced_lists()

        # Поиск и статистический фильтр могут скрывать найденную запись.
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self._notify_search_text_changed()

        self.active_filter = "archive" if game.archived else "all"
        self._sync_filter_buttons()
        self.refresh()

        if self._select_game_row(game_id):
            self.table.setFocus()

    def edit_game(self, *_):
        game_id = self.selected_game_id()
        if game_id is None:
            return
        game = self.db.get_game(game_id)
        if not game:
            return
        dlg = GameDialog(
            self,
            game,
            duplicate_lookup=lambda title: self.db.find_game_by_title(
                title,
                exclude_id=game_id,
            ),
        )
        if dlg.exec() == QDialog.Accepted:
            try:
                changed = self.db.update_game(game_id, dlg.payload())
            except DuplicateGameError as exc:
                QMessageBox.warning(
                    self,
                    "Игра уже существует",
                    f"Данная игра уже есть в списке:\n\n«{exc.existing_title}»",
                )
                self.focus_game(exc.existing_id)
                return
            if changed:
                self.changed()
            else:
                self.refresh()

    def archive_selected(self, archived: bool):
        game_id = self.selected_game_id()
        if game_id is None:
            return
        game = self.db.get_game(game_id)
        if not game:
            return
        if archived:
            open_session = self.db.get_open_auction_session_for_game(game_id)
            if open_session is not None:
                QMessageBox.warning(
                    self,
                    "Архивирование недоступно",
                    f"«{game.title}» участвует в незавершённом аукционе.\n\n"
                    "Сначала завершите или отмените аукцион.",
                )
                return
            answer = QMessageBox.question(
                self,
                "Архив",
                f"Переместить «{game.title}» в архив?\n\nДанные игры не будут удалены.",
            )
            if answer != QMessageBox.Yes:
                return
        try:
            self.db.archive_game(game_id, archived)
        except RuntimeError as exc:
            QMessageBox.warning(self, "Архивирование недоступно", str(exc))
            return
        self.changed()

    def clear_all_games(self):
        if (
            self._clear_all_worker is not None
            or self._delete_worker is not None
            or self._import_worker is not None
        ):
            return

        open_session = self.db.get_open_auction_session()
        if open_session is not None:
            QMessageBox.warning(
                self,
                "Очистка недоступна",
                "Сначала завершите или отмените текущий аукцион.\n\n"
                f"Сейчас открыт: «{open_session.get('name') or 'Аукцион'}» "
                f"({open_session.get('status') or 'неизвестный статус'}).",
            )
            return

        game_count = self.db.count_all_games()
        if game_count <= 0:
            QMessageBox.information(self, "Очистить все игры", "Список игр уже пуст.")
            self._update_action_state()
            return

        dialog = DeleteAllGamesDialog(game_count, self)
        if dialog.exec() != QDialog.Accepted:
            return

        backup_dir = AppPaths.from_database_path(self.db.path).backups_dir

        def perform_clear():
            started = time.perf_counter()
            result = self.db.clear_all_games_with_backup(
                backup_dir, keep_backups=30
            )
            result["total_seconds"] = time.perf_counter() - started
            return result

        self.clear_all_btn.setEnabled(False)
        self.clear_all_btn.setText("Очистка…")
        worker = FunctionWorker(perform_clear)
        self._clear_all_worker = worker
        self._update_action_state()
        worker.signals.result.connect(self._clear_all_completed)
        worker.signals.error.connect(self._clear_all_failed)
        worker.signals.finished.connect(self._clear_all_worker_finished)
        self.thread_pool.start(worker)

    def _clear_all_completed(self, result):
        refresh_started = time.perf_counter()
        self.changed()
        refresh_seconds = time.perf_counter() - refresh_started
        try:
            append_performance_trace(
                AppPaths.from_database_path(self.db.path).logs_dir,
                "DELETE_ALL "
                f"refresh={refresh_seconds:.3f}s "
                f"total_worker={result['total_seconds']:.3f}s",
            )
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Игры удалены",
            f"Удалено игр: {result['deleted_games']}.\n"
            f"Сохранено записей истории аукционов: "
            f"{result['preserved_auction_entries']}.\n\n"
            f"Резервная копия перед очисткой:\n{result['backup_path']}",
        )

    def _clear_all_failed(self, exc):
        QMessageBox.critical(self, "Ошибка очистки", str(exc))

    def _clear_all_worker_finished(self):
        self._clear_all_worker = None
        self.clear_all_btn.setText("Очистить все игры…")
        self._update_action_state()

    def delete_selected(self):
        if (
            self._delete_worker is not None
            or self._clear_all_worker is not None
            or self._import_worker is not None
        ):
            return

        game_id = self.selected_game_id()
        if game_id is None:
            return
        game = self.db.get_game(game_id)
        if not game:
            return

        open_session = self.db.get_open_auction_session_for_game(game_id)
        if open_session is not None:
            QMessageBox.warning(
                self,
                "Удаление недоступно",
                f"«{game.title}» участвует в незавершённом аукционе.\n\n"
                "Сначала завершите или отмените аукцион.",
            )
            return

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Удалить игру навсегда?")
        box.setText(f"Удалить «{game.title}» полностью?")
        box.setInformativeText(
            "Будут безвозвратно удалены сама игра и связанные с ней рабочие данные.\n\n"
            "Предыдущая подробная история этой игры будет очищена; в журнале останется "
            "только факт удаления. Перед удалением программа автоматически создаст "
            "резервную копию базы."
        )
        delete_btn = box.addButton("Да, удалить", QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = box.addButton("Нет", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(cancel_btn)
        box.exec()

        if box.clickedButton() is not delete_btn:
            return

        backup_dir = AppPaths.from_database_path(self.db.path).backups_dir

        def perform_delete():
            # Keep the entire destructive path outside the GUI thread. For the
            # safety backup use a separate Python process as well: on Windows,
            # OneDrive/antivirus filesystem filters can otherwise stall the
            # whole Python process even when sqlite3.backup() runs in QThreadPool.
            started = time.perf_counter()
            backup_path = self.db.backup_isolated(backup_dir)
            after_backup = time.perf_counter()
            self.db.prune_backups(backup_dir, 30)
            after_prune = time.perf_counter()
            self.db.delete_game(game_id)
            finished = time.perf_counter()
            return {
                "backup_path": backup_path,
                "backup_seconds": after_backup - started,
                "prune_seconds": after_prune - after_backup,
                "delete_seconds": finished - after_prune,
                "total_seconds": finished - started,
            }

        self.delete_btn.setEnabled(False)
        self.delete_btn.setText("Удаление…")
        worker = FunctionWorker(perform_delete)
        self._delete_worker = worker
        self._update_action_state()
        worker.signals.result.connect(
            lambda result, title=game.title: self._delete_completed(title, result)
        )
        worker.signals.error.connect(self._delete_failed)
        worker.signals.finished.connect(self._delete_worker_finished)
        self.thread_pool.start(worker)

    def _delete_completed(self, title: str, result):
        refresh_started = time.perf_counter()
        self.changed()
        refresh_seconds = time.perf_counter() - refresh_started

        # Performance tracing is opt-in after the stabilization audit.  When
        # enabled it uses the same bounded technical log as Journal refreshes.
        try:
            append_performance_trace(
                AppPaths.from_database_path(self.db.path).logs_dir,
                "DELETE "
                f"backup={result['backup_seconds']:.3f}s "
                f"prune={result['prune_seconds']:.3f}s "
                f"db={result['delete_seconds']:.3f}s "
                f"refresh={refresh_seconds:.3f}s "
                f"total_worker={result['total_seconds']:.3f}s",
            )
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Игра удалена",
            f"«{title}» удалена полностью.\n\n"
            f"Резервная копия перед удалением:\n{result['backup_path']}",
        )

    def _delete_failed(self, exc):
        QMessageBox.critical(self, "Ошибка удаления", str(exc))

    def _delete_worker_finished(self):
        self._delete_worker = None
        self.delete_btn.setText("Удалить")
        self._update_action_state()

    def show_import_csv_help(self):
        QMessageBox.information(
            self,
            "Правила импорта CSV",
            "Поддерживаются два варианта CSV.\n\n"
            "1. Обычный CSV с заголовками\n"
            "Обязателен только столбец «НАЗВАНИЕ ИГРЫ».\n"
            "Дополнительные поддерживаемые столбцы: «ДАТА ВЫХОДА», «БАЛЛЫ» (старые «БАЛЛЫ SM» и «СУММА» тоже принимаются), "
            "«КООП/НЕ КООП», «СТАТУС», «ОТЗЫВ».\n"
            "Они могут идти в любом порядке. Отсутствующие столбцы не считаются ошибкой.\n"
            "Неизвестные дополнительные столбцы игнорируются.\n"
            "Пустая ячейка означает «значение не предоставлено» и не стирает уже "
            "существующие данные игры.\n\n"
            "Пример:\n"
            "НАЗВАНИЕ ИГРЫ;БАЛЛЫ;ДАТА ВЫХОДА\n"
            "Control;1500;27.08.2019\n\n"
            "2. CSV формата «Название игры|Баллы»\n"
            "Файл без заголовка, одна игра в строке:\n"
            "Название игры|Баллы\n\n"
            "Пример:\n"
            "Control|1500\n"
            "Alan Wake 2|2500\n\n"
            "Для уже существующей игры изменяются только реально переданные непустые "
            "значения. Для новой игры отсутствующие поля создаются с безопасными "
            "значениями по умолчанию и их можно заполнить позже в программе.\n\n"
            "Перед любым импортом In one line автоматически создаёт резервную копию базы.",
        )

    def import_csv(self):
        if (
            self._import_worker is not None
            or self._delete_worker is not None
            or self._clear_all_worker is not None
        ):
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт основной таблицы", "", "CSV (*.csv);;Все файлы (*.*)"
        )
        if not path:
            return

        backup_dir = AppPaths.from_database_path(self.db.path).backups_dir

        def perform_import():
            # The complete safety sequence stays outside the GUI thread.
            # import_csv_with_backup is only an orchestration wrapper around
            # the existing strict importer: backup -> prune -> import_csv.
            started = time.perf_counter()
            result = self.db.import_csv_with_backup(
                path, backup_dir, merge=True, keep_backups=30
            )
            result["total_seconds"] = time.perf_counter() - started
            return result

        self.import_btn.setText("Импорт…")
        worker = FunctionWorker(perform_import)
        self._import_worker = worker
        self._update_action_state()
        worker.signals.result.connect(self._import_completed)
        worker.signals.error.connect(self._import_failed)
        worker.signals.finished.connect(self._import_worker_finished)
        self.thread_pool.start(worker)

    def _import_completed(self, result):
        refresh_started = time.perf_counter()
        self.changed()
        refresh_seconds = time.perf_counter() - refresh_started

        try:
            append_performance_trace(
                AppPaths.from_database_path(self.db.path).logs_dir,
                "IMPORT "
                f"worker={result['total_seconds']:.3f}s "
                f"refresh={refresh_seconds:.3f}s",
            )
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Импорт завершён",
            f"Добавлено: {result['created']}\n"
            f"Изменено: {result['updated']}\n"
            f"Без изменений / пропущено: {result['skipped']}\n\n"
            f"Резервная копия перед импортом:\n{result['backup_path']}",
        )

    def _import_failed(self, exc):
        QMessageBox.critical(self, "Ошибка импорта", str(exc))

    def _import_worker_finished(self):
        self._import_worker = None
        self.import_btn.setText("Импорт CSV")
        self._update_action_state()

