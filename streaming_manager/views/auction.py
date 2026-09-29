from __future__ import annotations

import hashlib
import json
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QSettings, Signal, Qt, QThreadPool, QTimer, QUrl
from PySide6.QtGui import QAction, QBrush, QColor, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QAbstractSpinBox, QCheckBox, QComboBox, QColorDialog, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFontComboBox, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit,
    QLayout, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ..app_paths import AppPaths
from ..api_server import LocalApiServer
from ..audio import AudioCoordinator
from ..constants import (
    APP_NAME, APP_VERSION, AUCTION_MANUAL_BID_POINTS_MAX,
    AUCTION_MANUAL_BID_POINTS_MIN, AUCTION_MIN_DURATION_MS, AUCTION_MAX_DURATION_MS,
    AUCTION_WHEEL_FORMAT_DEFAULT, AUCTION_WHEEL_FORMAT_ELIMINATION,
    AUCTION_WHEEL_FORMAT_KEY, AUCTION_WHEEL_FORMAT_STANDARD,
    COOP_LABELS, DEFAULT_API_HOST,
    SHARED_XLSX_ENABLED_KEY, SHARED_XLSX_LOCAL_WRITE_DEBOUNCE_MS,
    SHARED_XLSX_PATH_KEY, SHARED_XLSX_POLL_INTERVAL_MS,
    STATUS_ABANDONED, STATUS_COMPLETED, STATUS_LABELS, STATUS_NOT_PLAYED,
    STATUS_PLAYED, STATUS_PLAYING, STREAM_FORMATS,
    WHEEL_CENTER_IMAGE_MEDIA_ID_KEY,
)
from ..database import (
    Database, DuplicateGameError, Game, display_date, display_datetime_local,
    format_points, normalize_date_text, normalize_text_key, parse_date,
)
from ..exporters import (
    export_auction_pipe_csv, export_public_csv, export_public_json, export_public_xlsx,
    auction_pipe_text,
)
from ..random_sources import RandomDraw, RandomOrgClient
from ..integrations import IntegrationManager
from ..emote_catalog import (
    EmoteCatalogItem,
    fetch_third_party_channel_emotes,
    hydrate_emote_thumbnails,
)
from ..media import (
    MEDIA_CATEGORY_WHEEL_CENTER_ICONS,
    media_asset_available,
    resolve_media_asset_path,
)
from ..wheel_center_media import (
    prepare_local_center_image,
    prepare_remote_center_image,
    store_prepared_center_image,
)
from ..shared_xlsx import (
    SharedXlsxError, SharedXlsxTransientError, main_games_rows, read_shared_xlsx,
    state_hash, write_shared_xlsx,
)
from ..time_input import parse_duration_input
from ..workers import FunctionWorker
from .common import (
    APP_STYLE, FocusClearingWidget, ScrollSafeComboBox, ScrollSafeFontComboBox,
    ScrollSafeSpinBox, _center, _selected_id, autosize_compact_columns_once,
    suspend_live_content_resize,
)
from .wheel import AuctionWheelWidget
from .wheel_center_picker import WheelCenterPickerDialog
from .auction_history import format_auction_history_event
from .auction_bets import format_integration_bet_event
from .rules_editor import AuctionRulesEditorDialog, AuctionRulesPreviewDialog


class _AuctionHistoryList(QListWidget):
    """List widget that can clear Conduct hover highlight on mouse leave."""

    hoverCleared = Signal()

    def leaveEvent(self, event):
        self.hoverCleared.emit()
        super().leaveEvent(event)


from .auction_dialogs import AuctionTimeDialog
from .auction_parts.state import AuctionStateMixin
from .auction_parts.audio import AuctionAudioMixin
from .auction_parts.search import AuctionSearchMixin
from .auction_parts.actions import AuctionActionMixin
from .auction_parts.rng import AuctionRngMixin


class AuctionTab(AuctionStateMixin, AuctionSearchMixin, AuctionActionMixin, AuctionRngMixin, AuctionAudioMixin, QWidget):
    centerImageChanged = Signal(int)

    _LOT_COMPACT_COLUMNS = (0, 1, 3)
    _CONDUCT_COMPACT_COLUMNS = (0, 1, 3, 4)

    MODE_LABELS = {
        "max_amount": "Максимальная сумма",
        "weighted_wheel": "Взвешенное колесо",
    }
    RNG_LABELS = {
        "local": "Стандартный (локальный)",
        "random_org": "Random.org",
        "random_org_plus": "Random.org+",
    }
    WHEEL_FORMAT_LABELS = {
        AUCTION_WHEEL_FORMAT_STANDARD: "Обычное",
        AUCTION_WHEEL_FORMAT_ELIMINATION: "Выбывание",
    }
    STATUS_LABELS = {
        "running": "ИДЁТ",
        "paused": "ПАУЗА",
        "awaiting_wheel": "ОЖИДАНИЕ КОЛЕСА",
        "winner_selected": "ПОБЕДИТЕЛЬ ВЫБРАН",
        "tie_break_required": "НЕСКОЛЬКО ПОБЕДИТЕЛЕЙ",
        "finished_no_winner": "ЗАВЕРШЁН БЕЗ ПОБЕДИТЕЛЯ",
        "confirmed": "ЗАВЕРШЁН",
        "cancelled": "ОТМЕНЁН",
    }
    def __init__(
        self,
        db: Database,
        changed: Callable[[], None] | None = None,
        integration_manager: IntegrationManager | None = None,
        open_integrations: Callable[[], None] | None = None,
        integration_runtime_health: Callable[[], dict[str, dict]] | None = None,
        audio_coordinator: AudioCoordinator | None = None,
    ):
        super().__init__()
        self.db = db
        self.changed = changed or (lambda: None)
        self.integration_manager = integration_manager or IntegrationManager(db)
        self.open_integrations = open_integrations or (lambda: None)
        self.integration_runtime_health = integration_runtime_health or (lambda: {})
        self.audio_coordinator = audio_coordinator or AudioCoordinator(self)
        self._integration_status_dialog: QDialog | None = None
        self._active_auction_id: int | None = None
        self.thread_pool = QThreadPool.globalInstance()
        self._auction_rng_worker = None
        self._wheel_rng_worker = None
        self._wheel_center_picker: WheelCenterPickerDialog | None = None
        self._wheel_center_catalog_worker = None
        self._wheel_center_import_worker = None
        self._wheel_center_catalog_cache: list[EmoteCatalogItem] | None = None
        self._timer_context = "auction"
        self._default_auction_duration_ms = (
            self._saved_max_amount_default_duration_ms()
        )
        self._prestart_auction_duration_ms = self._default_auction_duration_ms
        self._default_wheel_duration_ms = self._saved_wheel_default_duration_ms()
        self._prestart_wheel_duration_ms = self._default_wheel_duration_ms
        self._pending_tie_overtime = False
        saved_wheel_format = str(
            self.db.get_setting(
                AUCTION_WHEEL_FORMAT_KEY,
                AUCTION_WHEEL_FORMAT_DEFAULT,
            )
            or AUCTION_WHEEL_FORMAT_DEFAULT
        )
        self._prestart_wheel_format = (
            saved_wheel_format
            if saved_wheel_format in self.WHEEL_FORMAT_LABELS
            else AUCTION_WHEEL_FORMAT_DEFAULT
        )
        # MainWindow переключает это состояние вместе с основной вкладкой.
        # До привязки к MainWindow сохраняем прежнее standalone-поведение.
        self._main_tab_visible = True
        self._refresh_pending = False
        self._wheel_chance_visible = self.db.get_auction_wheel_chance_visible()
        self._history_auction_id: int | None = None
        self._history_last_log_id = 0
        self._bets_auction_id: int | None = None
        self._bets_last_log_id = 0
        self._history_hover_brushes: list[tuple[QTableWidgetItem, QBrush]] = []
        # A7: while a history-linked lot is hovered, the Conduct auto-scroll
        # must stay frozen at the revealed row without changing operator selection.
        self._history_hover_pauses_auto_scroll = False
        # Both inner auction tables and the dedicated auction-lots OBS overlay
        # share one session-only auto-scroll switch. It deliberately starts OFF
        # on every application launch and is never stored in settings.
        self._desktop_lot_auto_scroll_enabled = False
        self._lots_scroll_direction = 1
        self._conduct_scroll_direction = 1
        self._init_wheel_audio()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)

        # Внутренние вкладки разделяют подготовку лотов, управление сессией
        # и совместимость с внешними форматами. Так на одном экране больше нет ряда
        # неактуальных кнопок.
        self.auction_tabs = QTabWidget()
        layout.addWidget(self.auction_tabs, 1)

        # ==========================================================
        # ЛОТЫ
        # ==========================================================
        self.lots_page = QWidget()
        lots_layout = QVBoxLayout(self.lots_page)
        lots_layout.setContentsMargins(10, 10, 10, 10)
        lots_layout.setSpacing(9)

        lots_rules_row = QHBoxLayout()
        self.lots_rules_btn = QPushButton("Правила вкладки")
        self.lots_rules_btn.clicked.connect(
            lambda: self._toggle_rules(
                self.lots_rules_label,
                self.lots_rules_btn,
            )
        )
        lots_rules_row.addWidget(self.lots_rules_btn)
        lots_rules_row.addStretch()
        lots_layout.addLayout(lots_rules_row)

        self.lots_rules_label = QLabel(
            "Список лотов формируется из активных игр со статусами ИГРАЛ + НЕ ИГРАЛ. "
            "ПРОХОДИТСЯ, ПРОЙДЕНО, ЗАБРОШЕНО и архив в список не попадают. "
            "До запуска отображается текущий список ДЛЯ АУКА. После запуска состав "
            "лотов фиксируется для этой сессии; ставки изменяют баллы выбранного лота."
        )
        self.lots_rules_label.setWordWrap(True)
        self.lots_rules_label.setProperty("muted", True)
        self.lots_rules_label.setVisible(False)
        lots_layout.addWidget(self.lots_rules_label)

        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(
            lambda text: self._search_text_changed("auction", text)
        )
        self.search.returnPressed.connect(self.activate_search)

        self.search_btn = QPushButton("Найти")
        self.search_btn.setToolTip(
            "Перейти к первому найденному лоту"
        )
        self.search_btn.clicked.connect(self.activate_search)

        self.count_label = QLabel()
        self.count_label.setProperty("badge", True)
        self.lots_scroll_btn = QPushButton("Включить прокрутку")
        self.lots_scroll_btn.setToolTip(
            "Включить/выключить автоматическую прокрутку обоих локальных списков лотов "
            "и OBS-оверлея списка лотов."
        )
        self.lots_scroll_btn.clicked.connect(self._toggle_desktop_lot_auto_scroll)

        top.addWidget(self.search, 1)
        top.addWidget(self.search_btn)
        top.addWidget(self.lots_scroll_btn)
        top.addWidget(self.count_label)
        lots_layout.addLayout(top)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["СТАРТ", "ТЕКУЩАЯ", "НАЗВАНИЕ", "БАЛЛЫ"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.horizontalHeader().setResizeContentsPrecision(0)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        lots_layout.addWidget(self.table, 1)

        self.auction_tabs.addTab(self.lots_page, "Лоты")

        # ==========================================================
        # ПРОВЕДЕНИЕ
        # ==========================================================
        # R1.0.8: Conduct is a long-form operator page. Keep its content at a
        # usable minimum height and let the page scroll vertically when the
        # main window is near its 1100x700 minimum. This prevents the table,
        # history and wheel area from collapsing to a few rows.
        self.conduct_page = QScrollArea()
        self.conduct_page.setFrameShape(QFrame.NoFrame)
        self.conduct_page.setWidgetResizable(True)
        self.conduct_page.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.conduct_page.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.conduct_page_content = FocusClearingWidget()
        self.conduct_page_content.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        conduct_layout = QVBoxLayout(self.conduct_page_content)
        conduct_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        conduct_layout.setContentsMargins(10, 10, 10, 10)
        conduct_layout.setSpacing(12)
        self.conduct_page.setWidget(self.conduct_page_content)

        conduct_rules_row = QHBoxLayout()
        self.conduct_rules_btn = QPushButton("Правила вкладки")
        self.conduct_rules_btn.clicked.connect(
            lambda: self._toggle_rules(
                self.conduct_rules_label,
                self.conduct_rules_btn,
            )
        )
        conduct_rules_row.addWidget(self.conduct_rules_btn)
        self.auction_rules_editor_btn = QPushButton("Правила аукциона")
        self.auction_rules_editor_btn.setToolTip(
            "Открыть WYSIWYG-редактор шаблонов правил аукциона"
        )
        self.auction_rules_editor_btn.clicked.connect(self.open_auction_rules_editor)
        conduct_rules_row.addWidget(self.auction_rules_editor_btn)
        self.auction_rules_preview_btn = QPushButton("Показать правила")
        self.auction_rules_preview_btn.setToolTip(
            "Показать сохранённые правила; для запущенного аукциона используется его замороженный снимок"
        )
        self.auction_rules_preview_btn.clicked.connect(self.show_auction_rules_preview)
        conduct_rules_row.addWidget(self.auction_rules_preview_btn)
        self.auction_rules_copy_url_btn = QPushButton("Копировать URL правил")
        self.auction_rules_copy_url_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(self._rules_overlay_url())
        )
        conduct_rules_row.addWidget(self.auction_rules_copy_url_btn)
        self.auction_rules_obs_preview_btn = QPushButton("Предпросмотр OBS")
        self.auction_rules_obs_preview_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(self._rules_overlay_url() + "?preview=1"))
        )
        conduct_rules_row.addWidget(self.auction_rules_obs_preview_btn)
        conduct_rules_row.addStretch()
        conduct_layout.addLayout(conduct_rules_row)

        self.conduct_rules_label = QLabel(
            "Перед запуском выберите способ определения победителя. Большой таймер "
            "меняет назначение вместе с выбранным режимом.\n\n"
            "Максимальная сумма: таймер задаёт время приёма ставок. Кнопка «Старт» "
            "запускает отсчёт, после чего становится «Пауза» / «Продолжить». При нуле "
            "побеждает единственный лот с максимальным количеством баллов; при точной ничьей можно "
            "дать дополнительное время только лидерам или перейти к колесу.\n"
            "Взвешенное колесо: таймер задаёт только время вращения (от 3 секунд до 24 часов), "
            "а кнопка называется «Крутить». Отдельного периода приёма ставок в этом "
            "режиме нет: победитель определяется выпавшим сектором.\n\n"
            "Кнопки −10 мин, −1 мин, +1 мин и +10 мин доступны только для приёма ставок "
            "и дополнительного времени. В контексте колеса они скрыты. «Сбросить» "
            "возвращает исходное время текущего контекста.\n\n"
            "Для колеса результат фиксируется существующим генератором, после чего "
            "локальный виджет и OBS используют одну и ту же сохранённую анимацию и "
            "wheel_duration_ms. Большой таймер синхронно показывает оставшееся время "
            "вращения и после определения победителя остаётся видимым со значением "
            "00:00:00.000, чтобы оператор мог при необходимости отменить результат.\n\n"
            "После завершения результата победителя необходимо подтвердить; после "
            "подтверждения его игра получает статус ПРОХОДИТСЯ."
        )
        self.conduct_rules_label.setWordWrap(True)
        self.conduct_rules_label.setProperty("muted", True)
        self.conduct_rules_label.setVisible(False)
        conduct_layout.addWidget(self.conduct_rules_label)

        self.integration_status_widget = QWidget()
        integration_status_row = QHBoxLayout(self.integration_status_widget)
        integration_status_row.setContentsMargins(0, 0, 0, 0)
        integration_status_row.setSpacing(8)
        self.integration_status_btn = QPushButton("Интеграции: не настроены")
        self.integration_status_btn.setProperty("badge", True)
        self.integration_status_btn.setToolTip(
            "Открыть состояние подключённых сервисов. Подключённые источники пополнений "
            "работают постоянно — отдельного включения для текущего аукциона нет."
        )
        self.integration_status_btn.clicked.connect(self._show_integration_status_dialog)
        integration_status_row.addWidget(self.integration_status_btn)
        integration_status_row.addStretch()
        conduct_layout.addWidget(self.integration_status_widget)

        self.setup_widget = QWidget()
        setup = QGridLayout(self.setup_widget)
        setup.setContentsMargins(0, 0, 0, 0)
        setup.setHorizontalSpacing(8)
        setup.setVerticalSpacing(8)

        setup.addWidget(QLabel("Способ определения победителя:"), 0, 0)
        self.mode_combo = ScrollSafeComboBox()
        self.mode_combo.addItem("Максимальная сумма", "max_amount")
        self.mode_combo.addItem("Взвешенное колесо", "weighted_wheel")
        self.mode_combo.setMinimumWidth(180)
        setup.addWidget(self.mode_combo, 0, 1)

        self.rng_selector_label = QLabel("Генератор:")
        setup.addWidget(self.rng_selector_label, 0, 2)
        self.rng_combo = ScrollSafeComboBox()
        self.rng_combo.addItem("Стандартный (локальный)", "local")
        self.rng_combo.addItem("Random.org", "random_org")
        self.rng_combo.addItem("Random.org+", "random_org_plus")
        self.rng_combo.setMinimumWidth(170)
        setup.addWidget(self.rng_combo, 0, 3)

        self.rng_methods_btn = QPushButton("О методах")
        self.rng_methods_btn.clicked.connect(self.show_rng_methods)
        setup.addWidget(self.rng_methods_btn, 0, 4)

        self.verification_data_btn = QPushButton("Данные проверки")
        self.verification_data_btn.setToolTip(
            "Предварительный read-only состав и математические диапазоны будущего вращения"
        )
        self.verification_data_btn.clicked.connect(self.show_pre_spin_verification)
        setup.addWidget(self.verification_data_btn, 0, 5)
        setup.setColumnStretch(6, 1)

        self.wheel_format_label = QLabel("Формат колеса:")
        setup.addWidget(self.wheel_format_label, 1, 0)
        self.wheel_format_combo = ScrollSafeComboBox()
        self.wheel_format_combo.addItem(
            "Обычное",
            AUCTION_WHEEL_FORMAT_STANDARD,
        )
        self.wheel_format_combo.addItem(
            "Выбывание",
            AUCTION_WHEEL_FORMAT_ELIMINATION,
        )
        format_index = self.wheel_format_combo.findData(
            self._prestart_wheel_format
        )
        self.wheel_format_combo.setCurrentIndex(max(0, format_index))
        self.wheel_format_combo.setToolTip(
            "Обычное — одно вращение с итоговым победителем. "
            "Выбывание — каждый выпавший лот подтверждается кнопкой «В архив», "
            "после чего можно продолжить или переключиться обратно."
        )
        self.wheel_format_combo.currentIndexChanged.connect(
            self._handle_wheel_format_changed
        )
        setup.addWidget(self.wheel_format_combo, 1, 1)

        conduct_layout.addWidget(self.setup_widget)

        self.wheel_obs_widget = QWidget()
        wheel_obs_row = QHBoxLayout(self.wheel_obs_widget)
        wheel_obs_row.setContentsMargins(0, 0, 0, 0)
        wheel_obs_row.addWidget(QLabel("OBS колесо:"))
        self.copy_wheel_url_btn = QPushButton("Копировать URL колеса")
        self.copy_wheel_url_btn.clicked.connect(self.copy_wheel_overlay_url)
        self.preview_wheel_btn = QPushButton("Открыть предпросмотр колеса")
        self.preview_wheel_btn.clicked.connect(self.open_wheel_preview)
        wheel_obs_row.addWidget(self.copy_wheel_url_btn)
        wheel_obs_row.addWidget(self.preview_wheel_btn)
        wheel_obs_row.addStretch()
        conduct_layout.addWidget(self.wheel_obs_widget)

        self.state_widget = QWidget()
        state_row = QHBoxLayout(self.state_widget)
        state_row.setContentsMargins(0, 0, 0, 0)

        self.state_label = QLabel("Состояние: НЕТ АКТИВНОГО АУКЦИОНА")
        self.state_label.setProperty("badge", True)
        self.mode_label = QLabel("Режим: —")
        self.mode_label.setProperty("badge", True)
        self.rng_label = QLabel("RNG: —")
        self.rng_label.setProperty("badge", True)
        self.time_label = QLabel("Осталось: —")
        self.time_label.setProperty("badge", True)
        self.leader_label = QLabel("Лидер: —")
        self.leader_label.setProperty("badge", True)

        state_row.addWidget(self.state_label)
        state_row.addWidget(self.mode_label)
        state_row.addWidget(self.rng_label)
        state_row.addWidget(self.time_label)
        state_row.addWidget(self.leader_label, 1)
        conduct_layout.addWidget(self.state_widget)

        self.winner_chance_label = QLabel("")
        self.winner_chance_label.setWordWrap(True)
        self.winner_chance_label.setProperty("badge", True)
        self.winner_chance_label.setVisible(False)
        conduct_layout.addWidget(self.winner_chance_label)

        # Большой таймер является полем ввода до старта и точным индикатором
        # после старта. Миллисекунды отображаются всегда, а быстрые кнопки
        # изменяют именно минуты.
        self.timer_widget = QFrame()
        self.timer_widget.setFrameShape(QFrame.StyledPanel)
        timer_layout = QVBoxLayout(self.timer_widget)
        timer_layout.setContentsMargins(10, 8, 10, 8)
        timer_layout.setSpacing(6)

        self.timer_edit = QLineEdit(
            self._format_milliseconds(self._prestart_auction_duration_ms)
        )
        self.timer_edit.setAlignment(Qt.AlignCenter)
        self.timer_edit.setMinimumWidth(280)
        self.timer_edit.setMaximumWidth(360)
        timer_font = self.timer_edit.font()
        timer_font.setPointSize(22)
        timer_font.setBold(True)
        self.timer_edit.setFont(timer_font)
        self.timer_edit.setToolTip(
            "Ввод: 6 цифр ЧЧММСС (например 001530 → 00:15:30.000) или "
            "полный формат ЧЧ:ММ:СС.мс. Для приёма ставок: от 00:00:01.000 "
            "до 24:00:00.000. Для колеса: от 00:00:03.000 до 24:00:00.000."
        )
        self.timer_edit.editingFinished.connect(self._timer_editing_finished)
        timer_layout.addWidget(self.timer_edit, 0, Qt.AlignHCenter)

        self.auction_soundtrack_widget = self._build_auction_soundtrack_controls()
        timer_layout.addWidget(self.auction_soundtrack_widget)

        timer_buttons = QHBoxLayout()
        timer_buttons.setSpacing(5)
        self.start_btn = QPushButton("Старт")
        self.start_btn.setProperty("primary", True)
        self.start_btn.clicked.connect(self.handle_timer_action)

        self.timer_minus10_btn = QPushButton("−10 мин")
        self.timer_minus10_btn.clicked.connect(lambda: self.adjust_timer_minutes(-10))
        self.timer_minus_btn = QPushButton("−1 мин")
        self.timer_minus_btn.clicked.connect(lambda: self.adjust_timer_minutes(-1))
        self.timer_plus_btn = QPushButton("+1 мин")
        self.timer_plus_btn.clicked.connect(lambda: self.adjust_timer_minutes(1))
        self.timer_plus10_btn = QPushButton("+10 мин")
        self.timer_plus10_btn.clicked.connect(lambda: self.adjust_timer_minutes(10))

        for button, delta in (
            (self.timer_minus10_btn, -10),
            (self.timer_minus_btn, -1),
            (self.timer_plus_btn, 1),
            (self.timer_plus10_btn, 10),
        ):
            action = "Уменьшить" if delta < 0 else "Увеличить"
            button.setToolTip(
                f"{action} время аукциона на {abs(delta)} мин"
            )

        self.timer_reset_btn = QPushButton("Сбросить")
        self.timer_reset_btn.setToolTip(
            "Контекстный сброс: аукцион — 10 минут, допвремя — исходная длительность, "
            "колесо — 8 секунд"
        )
        self.timer_reset_btn.clicked.connect(self.reset_auction_timer)

        timer_buttons.addWidget(self.start_btn)
        timer_buttons.addWidget(self.timer_minus10_btn)
        timer_buttons.addWidget(self.timer_minus_btn)
        timer_buttons.addWidget(self.timer_plus_btn)
        timer_buttons.addWidget(self.timer_plus10_btn)
        timer_buttons.addWidget(self.timer_reset_btn)
        timer_layout.addLayout(timer_buttons)

        timer_obs_row = QHBoxLayout()
        timer_obs_row.setSpacing(5)
        self.copy_timer_overlay_btn = QPushButton("Копировать URL таймера")
        self.copy_timer_overlay_btn.setToolTip(
            "Скопировать существующий OBS Browser Source таймера"
        )
        self.copy_timer_overlay_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(
                f"{self.window().api.base_url}/timer-overlay"
            )
        )
        timer_obs_row.addStretch()
        timer_obs_row.addWidget(self.copy_timer_overlay_btn)
        timer_obs_row.addStretch()
        timer_layout.addLayout(timer_obs_row)

        audio_output_row = QHBoxLayout()
        audio_output_row.setSpacing(6)
        audio_output_row.addWidget(QLabel("Вывод музыки:"))
        self.audio_output_mode_combo = ScrollSafeComboBox()
        self.audio_output_mode_combo.addItem("В приложении", "application")
        self.audio_output_mode_combo.addItem(
            "Через OBS Browser Source таймера",
            "obs_timer",
        )
        saved_audio_output_mode = self._saved_audio_output_mode()
        saved_audio_output_index = self.audio_output_mode_combo.findData(
            saved_audio_output_mode
        )
        self.audio_output_mode_combo.setCurrentIndex(
            max(0, saved_audio_output_index)
        )
        self.audio_output_mode_combo.setToolTip(
            "Музыка аукциона и колеса использует один маршрут. "
            "В режиме OBS звук воспроизводит Browser Source таймера; "
            "локальный Qt-транспорт остаётся беззвучным и хранит точную позицию."
        )
        self.audio_output_mode_combo.currentIndexChanged.connect(
            self._audio_output_mode_changed
        )
        audio_output_row.addWidget(self.audio_output_mode_combo, 1)
        timer_layout.addLayout(audio_output_row)

        self.audio_output_hint = QLabel(
            "OBS-режим: звук аукциона и колеса идёт через этот же источник таймера. "
            "Не включайте в OBS отключение Browser Source, когда он не виден."
        )
        self.audio_output_hint.setWordWrap(True)
        self.audio_output_hint.setProperty("muted", True)
        timer_layout.addWidget(self.audio_output_hint)

        self.timer_finish_widget = QWidget()
        timer_finish_row = QHBoxLayout(self.timer_finish_widget)
        timer_finish_row.setContentsMargins(0, 0, 0, 0)
        timer_finish_row.setSpacing(5)
        self.finish_btn = QPushButton("Завершить приём ставок")
        self.finish_btn.clicked.connect(self.finish_auction)
        self.cancel_btn = QPushButton("Остановить аукцион")
        self.cancel_btn.setProperty("danger", True)
        self.cancel_btn.clicked.connect(self.cancel_auction)
        timer_finish_row.addWidget(self.finish_btn)
        timer_finish_row.addWidget(self.cancel_btn)
        timer_layout.addWidget(self.timer_finish_widget)

        timer_align_row = QHBoxLayout()
        timer_align_row.addStretch()
        timer_align_row.addWidget(self.timer_widget)
        conduct_layout.addLayout(timer_align_row)

        # Остальные контекстные действия относятся к ничьей, подтверждению
        # результата и проверке RNG. Запуск колеса находится в самом таймере.
        self.session_buttons_widget = QWidget()
        session_buttons = QHBoxLayout(self.session_buttons_widget)
        session_buttons.setContentsMargins(0, 0, 0, 0)

        self.confirm_btn = QPushButton("Подтвердить победителя")
        self.confirm_btn.setProperty("primary", True)
        self.confirm_btn.clicked.connect(self.handle_wheel_result_action)

        self.tie_overtime_btn = QPushButton("Дополнительное время")
        self.tie_overtime_btn.clicked.connect(self.start_tie_overtime)
        self.tie_wheel_btn = QPushButton("Использовать колесо")
        self.tie_wheel_btn.setProperty("primary", True)
        self.tie_wheel_btn.clicked.connect(self.use_wheel_for_tie)

        self.copy_ticket_btn = QPushButton("Копировать билет Random.org+")
        self.copy_ticket_btn.clicked.connect(self.copy_rng_ticket)
        self.verify_rng_btn = QPushButton("Проверить Random.org+")
        self.verify_rng_btn.clicked.connect(self.open_rng_verification)

        session_buttons.setSpacing(5)
        session_buttons.addWidget(self.confirm_btn)
        session_buttons.addWidget(self.tie_overtime_btn)
        session_buttons.addWidget(self.tie_wheel_btn)
        session_buttons.addWidget(self.copy_ticket_btn)
        session_buttons.addWidget(self.verify_rng_btn)
        session_buttons.addStretch()
        conduct_layout.addWidget(self.session_buttons_widget)

        # Поиск на «Проведение» такой же, как на остальных списках, и
        # синхронизируется с ними через MainWindow.
        conduct_search_row = QHBoxLayout()
        self.conduct_search = QLineEdit()
        self.conduct_search.setPlaceholderText("Поиск")
        self.conduct_search.setClearButtonEnabled(True)
        self.conduct_search.textChanged.connect(
            lambda text: self._search_text_changed("auction_conduct", text)
        )
        self.conduct_search.returnPressed.connect(
            self.activate_conduct_search
        )

        self.conduct_search_btn = QPushButton("Найти")
        self.conduct_search_btn.setToolTip(
            "Перейти к первому найденному лоту"
        )
        self.conduct_search_btn.clicked.connect(
            self.activate_conduct_search
        )

        conduct_search_row.addWidget(self.conduct_search, 1)
        conduct_search_row.addWidget(self.conduct_search_btn)
        conduct_layout.addLayout(conduct_search_row)

        # Ручная ставка теперь находится непосредственно на вкладке
        # «Проведение». Значок валюты в поле намеренно не показывается.
        self.bid_widget = QWidget()
        bid_row = QHBoxLayout(self.bid_widget)
        bid_row.setContentsMargins(0, 0, 0, 0)
        bid_row.addWidget(QLabel("Баллы к выбранному лоту:"))

        self.bid_amount = ScrollSafeSpinBox()
        self.bid_amount.setRange(
            AUCTION_MANUAL_BID_POINTS_MIN,
            AUCTION_MANUAL_BID_POINTS_MAX,
        )
        self.bid_amount.setSingleStep(10)
        self.bid_amount.setButtonSymbols(
            QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self.bid_amount.setValue(self.db.get_auction_manual_bid_points())
        self.bid_amount.editingFinished.connect(
            self._persist_manual_bid_points
        )
        self.bid_amount.setMinimumWidth(130)
        bid_row.addWidget(self.bid_amount)

        self.add_bid_btn = QPushButton("Добавить")
        self.add_bid_btn.clicked.connect(self.add_manual_bid)
        bid_row.addWidget(self.add_bid_btn)

        self.decrease_bid_btn = QPushButton("Уменьшить")
        self.decrease_bid_btn.clicked.connect(self.decrease_manual_bid)
        bid_row.addWidget(self.decrease_bid_btn)

        self.delete_lot_btn = QPushButton("Удалить лот")
        self.delete_lot_btn.setProperty("danger", True)
        self.delete_lot_btn.setToolTip(
            "Удалить ошибочно созданный временный лот текущего аукциона"
        )
        self.delete_lot_btn.clicked.connect(self.delete_temporary_lot)
        bid_row.addWidget(self.delete_lot_btn)
        bid_row.addStretch()
        conduct_layout.addWidget(self.bid_widget)

        # A2: постоянная inline-строка нового лота вместо модального диалога.
        # Видимость управляется состоянием сессии ниже: строка доступна только
        # во время реального приёма ставок.
        self.new_lot_widget = QWidget()
        new_lot_layout = QVBoxLayout(self.new_lot_widget)
        new_lot_layout.setContentsMargins(0, 0, 0, 0)
        new_lot_layout.setSpacing(6)

        new_lot_row = QHBoxLayout()
        new_lot_row.addWidget(QLabel("Название нового лота:"))

        self.new_lot_title = QLineEdit()
        self.new_lot_title.setPlaceholderText("Название нового лота")
        self.new_lot_title.setClearButtonEnabled(True)
        self.new_lot_title.setMinimumWidth(260)
        new_lot_row.addWidget(self.new_lot_title, 1)

        new_lot_row.addWidget(QLabel("Баллы:"))
        self.new_lot_points = ScrollSafeSpinBox()
        self.new_lot_points.setRange(0, 10_000_000)
        self.new_lot_points.setSingleStep(10)
        self.new_lot_points.setValue(0)
        self.new_lot_points.setButtonSymbols(
            QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self.new_lot_points.setMinimumWidth(130)
        new_lot_row.addWidget(self.new_lot_points)

        self.new_lot_btn = QPushButton("Добавить лот")
        self.new_lot_btn.clicked.connect(self.add_new_auction_lot)
        new_lot_row.addWidget(self.new_lot_btn)
        new_lot_layout.addLayout(new_lot_row)

        self.new_lot_rule = QLabel(
            "Новый лот будет виден только в текущем аукционе. "
            "После завершения или отмены аукциона он будет перенесён "
            "в основной список. Если лот станет подтверждённым победителем, "
            "его статус изменится на ПРОХОДИТСЯ; в остальных случаях он "
            "останется со статусом НЕ ИГРАЛ. После этого лот можно будет "
            "отредактировать в разделе «Игры»."
        )
        self.new_lot_rule.setWordWrap(True)
        self.new_lot_rule.setProperty("muted", True)
        new_lot_layout.addWidget(self.new_lot_rule)
        conduct_layout.addWidget(self.new_lot_widget)

        conduct_heading_row = QHBoxLayout()
        conduct_list_heading = QLabel("Список лотов")
        conduct_list_heading.setStyleSheet(
            "font-size: 11pt; font-weight: 600;"
        )
        conduct_heading_row.addWidget(conduct_list_heading)

        self.wheel_chance_checkbox = QCheckBox("Показывать шанс в колесе")
        self.wheel_chance_checkbox.setChecked(self._wheel_chance_visible)
        self.wheel_chance_checkbox.toggled.connect(
            self._set_wheel_chance_visible
        )
        conduct_heading_row.addWidget(self.wheel_chance_checkbox)

        self.conduct_scroll_btn = QPushButton("Включить прокрутку")
        self.conduct_scroll_btn.setToolTip(
            "Включить/выключить автоматическую прокрутку обоих локальных списков лотов "
            "и OBS-оверлея списка лотов."
        )
        self.conduct_scroll_btn.clicked.connect(self._toggle_desktop_lot_auto_scroll)
        conduct_heading_row.addWidget(self.conduct_scroll_btn)

        self.conduct_copy_lots_overlay_url_btn = QPushButton(
            "Копировать URL списка лотов"
        )
        self.conduct_copy_lots_overlay_url_btn.setToolTip(
            "Скопировать URL OBS-оверлея текущего списка лотов"
        )
        conduct_heading_row.addWidget(self.conduct_copy_lots_overlay_url_btn)

        self.conduct_open_lots_overlay_preview_btn = QPushButton(
            "Открыть предпросмотр списка лотов"
        )
        self.conduct_open_lots_overlay_preview_btn.setToolTip(
            "Открыть предпросмотр OBS-оверлея текущего списка лотов"
        )
        conduct_heading_row.addWidget(
            self.conduct_open_lots_overlay_preview_btn
        )

        conduct_heading_row.addStretch()
        self._sync_lot_scroll_buttons()

        self.auction_total_label = QLabel("Всего: 0 баллов")
        self.auction_total_label.setStyleSheet(
            "font-size: 10.5pt; font-weight: 600;"
        )
        conduct_heading_row.addWidget(self.auction_total_label)

        conduct_layout.addLayout(conduct_heading_row)

        self.conduct_table = QTableWidget(0, 5)
        # Keep the operator table readable when the optional wheel panel appears.
        # The enclosing QScrollArea below absorbs width pressure instead of
        # collapsing columns or requesting a wider top-level window.
        self.conduct_table.setMinimumWidth(520)
        self.conduct_table.setHorizontalHeaderLabels(
            ["СТАРТ", "ТЕКУЩАЯ", "НАЗВАНИЕ", "Шанс в колесе", "БАЛЛЫ"]
        )
        self.conduct_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.conduct_table.setAlternatingRowColors(True)
        self.conduct_table.setShowGrid(False)
        self.conduct_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )
        self.conduct_table.setSelectionMode(
            QTableWidget.SingleSelection
        )
        self.conduct_table.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel
        )
        self.conduct_table.verticalHeader().setVisible(False)
        self.conduct_table.verticalHeader().setDefaultSectionSize(32)
        self.conduct_table.horizontalHeader().setResizeContentsPrecision(0)
        self.conduct_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.conduct_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.conduct_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        self.conduct_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )
        self.conduct_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )
        self.conduct_content = QWidget()
        conduct_content_layout = QHBoxLayout(self.conduct_content)
        conduct_content_layout.setContentsMargins(0, 0, 0, 0)
        conduct_content_layout.setSpacing(12)
        self.conduct_table.itemSelectionChanged.connect(
            self._update_delete_lot_action_state
        )
        conduct_content_layout.addWidget(self.conduct_table, 3)

        # A7/B5: one compact operator-side area.  История keeps the full
        # current-session audit feed; Ставки is a filtered read-only feed of
        # successfully applied integration events for this exact auction.
        self.auction_activity_tabs = QTabWidget()
        self.auction_activity_tabs.setMinimumWidth(300)
        self.auction_activity_tabs.setMaximumWidth(390)
        self.auction_activity_tabs.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding
        )

        bets_page = QWidget()
        bets_layout = QVBoxLayout(bets_page)
        bets_layout.setContentsMargins(6, 6, 6, 6)
        bets_layout.setSpacing(6)
        self.auction_bets_status = QLabel(
            "Ставки появятся после запуска аукциона."
        )
        self.auction_bets_status.setWordWrap(True)
        self.auction_bets_status.setProperty("muted", True)
        bets_layout.addWidget(self.auction_bets_status)

        self.auction_bets_list = QListWidget()
        self.auction_bets_list.setWordWrap(True)
        self.auction_bets_list.setSpacing(4)
        self.auction_bets_list.setSelectionMode(QAbstractItemView.NoSelection)
        bets_layout.addWidget(self.auction_bets_list, 1)
        bets_index = self.auction_activity_tabs.addTab(bets_page, "Ставки")
        self.auction_activity_tabs.setTabToolTip(
            bets_index,
            "Автоматически принятые интеграционные ставки текущего аукциона.",
        )

        history_page = QWidget()
        history_layout = QVBoxLayout(history_page)
        history_layout.setContentsMargins(6, 6, 6, 6)
        history_layout.setSpacing(6)
        self.auction_history_status = QLabel(
            "История появится после запуска аукциона."
        )
        self.auction_history_status.setWordWrap(True)
        self.auction_history_status.setProperty("muted", True)
        history_layout.addWidget(self.auction_history_status)

        self.auction_history_list = _AuctionHistoryList()
        self.auction_history_list.setMouseTracking(True)
        self.auction_history_list.setWordWrap(True)
        self.auction_history_list.setSpacing(4)
        self.auction_history_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.auction_history_list.itemEntered.connect(
            self._history_event_hovered
        )
        self.auction_history_list.hoverCleared.connect(
            self._clear_history_hover_highlight
        )
        history_layout.addWidget(self.auction_history_list, 1)
        history_index = self.auction_activity_tabs.addTab(history_page, "История")
        self.auction_activity_tabs.setCurrentIndex(history_index)
        conduct_content_layout.addWidget(self.auction_activity_tabs, 2)

        self.wheel_panel = QWidget()
        wheel_panel_layout = QVBoxLayout(self.wheel_panel)
        wheel_panel_layout.setContentsMargins(8, 8, 8, 8)
        wheel_panel_layout.setSpacing(8)

        wheel_heading_row = QHBoxLayout()
        wheel_heading = QLabel("Колесо")
        wheel_heading.setStyleSheet("font-size: 11pt; font-weight: 650;")
        wheel_heading_row.addWidget(wheel_heading)
        wheel_heading_row.addStretch()
        wheel_panel_layout.addLayout(wheel_heading_row)

        self.wheel_soundtrack_widget = self._build_wheel_soundtrack_controls()
        wheel_panel_layout.addWidget(self.wheel_soundtrack_widget)

        self.wheel_widget = AuctionWheelWidget()
        self.wheel_widget.spinFinished.connect(
            self._handle_local_wheel_spin_finished
        )
        self.wheel_widget.centerClicked.connect(
            self._open_wheel_center_picker
        )
        self.wheel_widget.setToolTip(
            "Нажмите на центр колеса, чтобы быстро выбрать изображение или смайлик."
        )
        wheel_panel_layout.addWidget(self.wheel_widget, 1)

        self.wheel_panel.setMinimumWidth(300)
        self.wheel_panel.setVisible(False)
        conduct_content_layout.addWidget(self.wheel_panel, 2)

        # R1.0.7 geometry stability: dynamic operator panes may need more
        # horizontal space than the current restored window provides. Put this
        # row behind its own horizontal scroll boundary so showing the Wheel
        # cannot squeeze critical fields/columns or resize MainWindow.
        self.conduct_content_scroll = QScrollArea()
        self.conduct_content_scroll.setFrameShape(QFrame.NoFrame)
        self.conduct_content_scroll.setWidgetResizable(True)
        self.conduct_content_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.conduct_content_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.conduct_content_scroll.setMinimumHeight(260)
        self.conduct_content_scroll.setWidget(self.conduct_content)
        conduct_layout.addWidget(self.conduct_content_scroll, 1)

        self.auction_tabs.addTab(self.conduct_page, "Проведение")
        self.refresh_integration_status()

        # ==========================================================
        # LEGACY COMPATIBLE EXPORT
        # ==========================================================
        self.legacy_export_page = QWidget()
        legacy_export_layout = QVBoxLayout(self.legacy_export_page)
        legacy_export_layout.setContentsMargins(10, 10, 10, 10)
        legacy_export_layout.setSpacing(10)

        export_rules_row = QHBoxLayout()
        self.export_rules_btn = QPushButton("Правила вкладки")
        self.export_rules_btn.clicked.connect(
            lambda: self._toggle_rules(
                self.export_rules_label,
                self.export_rules_btn,
            )
        )
        export_rules_row.addWidget(self.export_rules_btn)
        export_rules_row.addStretch()
        legacy_export_layout.addLayout(export_rules_row)

        self.export_rules_label = QLabel(
            "Для совместимого экспорта используется текущий список ДЛЯ АУКА: только активные "
            "игры ИГРАЛ + НЕ ИГРАЛ. Экспорт и копирование выполняются в формате "
            "Название|Баллы. ПРОХОДИТСЯ, ПРОЙДЕНО, ЗАБРОШЕНО и архив исключаются."
        )
        self.export_rules_label.setWordWrap(True)
        self.export_rules_label.setProperty("muted", True)
        self.export_rules_label.setVisible(False)
        legacy_export_layout.addWidget(self.export_rules_label)

        buttons = QHBoxLayout()
        export_btn = QPushButton("Экспорт CSV")
        export_btn.clicked.connect(self.export_auction_csv)
        copy_btn = QPushButton("Копировать список")
        copy_btn.clicked.connect(self.copy_auction_list)
        buttons.addWidget(export_btn)
        buttons.addWidget(copy_btn)
        buttons.addStretch()
        legacy_export_layout.addLayout(buttons)

        shared_separator = QFrame()
        shared_separator.setFrameShape(QFrame.HLine)
        shared_separator.setFrameShadow(QFrame.Sunken)
        legacy_export_layout.addWidget(shared_separator)

        shared_title = QLabel("Совместная таблица")
        shared_title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        legacy_export_layout.addWidget(shared_title)

        shared_description = QLabel(
            "Обычный XLSX с основным списком игр. Файл можно хранить в папке "
            "Google Drive Desktop и редактировать через Google Таблицы. Все "
            "подключённые экземпляры In one line равноправны; применяется "
            "последняя полученная версия файла."
        )
        shared_description.setWordWrap(True)
        shared_description.setProperty("muted", True)
        legacy_export_layout.addWidget(shared_description)

        shared_buttons = QHBoxLayout()
        self.shared_xlsx_create_btn = QPushButton("Создать таблицу")
        self.shared_xlsx_connect_btn = QPushButton("Подключить таблицу")
        self.shared_xlsx_disconnect_btn = QPushButton("Отключить")
        self.shared_xlsx_create_btn.clicked.connect(self._shared_xlsx_create)
        self.shared_xlsx_connect_btn.clicked.connect(self._shared_xlsx_connect)
        self.shared_xlsx_disconnect_btn.clicked.connect(self._shared_xlsx_disconnect)
        shared_buttons.addWidget(self.shared_xlsx_create_btn)
        shared_buttons.addWidget(self.shared_xlsx_connect_btn)
        shared_buttons.addWidget(self.shared_xlsx_disconnect_btn)
        shared_buttons.addStretch()
        legacy_export_layout.addLayout(shared_buttons)

        shared_form = QFormLayout()
        self.shared_xlsx_path_label = QLabel("Не подключена")
        self.shared_xlsx_path_label.setWordWrap(True)
        self.shared_xlsx_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.shared_xlsx_status_label = QLabel("Выключено")
        self.shared_xlsx_status_label.setWordWrap(True)
        self.shared_xlsx_modified_label = QLabel("—")
        shared_form.addRow("Таблица:", self.shared_xlsx_path_label)
        shared_form.addRow("Состояние:", self.shared_xlsx_status_label)
        shared_form.addRow("Последнее изменение:", self.shared_xlsx_modified_label)
        legacy_export_layout.addLayout(shared_form)
        legacy_export_layout.addStretch()

        self._init_shared_xlsx_sync()

        # R1.0.9: the former Auction -> Export page is no longer exposed as an
        # auction subtab. Compatible export actions live in Settings -> Export,
        # while the proven shared-XLSX synchronization controls are re-hosted
        # on the main Games page by MainWindow. The sync engine remains here so
        # no accepted synchronization semantics/timers are rewritten.

        # Подключаем currentChanged только после создания всех внутренних страниц.
        # QTabWidget испускает currentChanged уже при добавлении первой вкладки;
        # раннее подключение обращалось к ещё не созданному conduct_page.
        self.auction_tabs.currentChanged.connect(
            self._handle_inner_tab_changed
        )

        # Полная синхронизация состояния остаётся редкой и не пишет время в БД:
        # остаток вычисляется из deadline_at. Отдельный точный UI-таймер лишь
        # перерисовывает миллисекунды из кэшированного deadline и не трогает SQLite.
        self._timer_display_session_id = None
        self._timer_display_status = ""
        self._timer_display_kind = ""
        self._timer_display_deadline = None
        self._timer_display_wheel_start = None
        self._timer_display_wheel_duration_ms = 0
        self._timer_display_paused_ms = 0
        self._timer_expiry_handled_id = None

        self.auction_timer = QTimer(self)
        self.auction_timer.setInterval(500)
        self.auction_timer.timeout.connect(self._tick_auction)

        self.timer_display_timer = QTimer(self)
        self.timer_display_timer.setTimerType(Qt.PreciseTimer)
        self.timer_display_timer.setInterval(25)
        self.timer_display_timer.timeout.connect(self._tick_timer_display)

        # Один таймер обслуживает оба локальных списка лотов. Две кнопки
        # показывают и меняют одно session-only состояние (default OFF).
        # OBS/list-overlay имеют собственную независимую прокрутку.
        self.conduct_scroll_timer = QTimer(self)
        self.conduct_scroll_timer.setInterval(40)
        self.conduct_scroll_timer.timeout.connect(
            self._auto_scroll_conduct_lots
        )

        self.auction_history_timer = QTimer(self)
        self.auction_history_timer.setInterval(750)
        self.auction_history_timer.timeout.connect(self._poll_auction_history)

        # Runtime websocket failures must remain visible even while the status
        # dialog is closed. This timer performs only local state reads.
        self.integration_status_timer = QTimer(self)
        self.integration_status_timer.setInterval(1500)
        self.integration_status_timer.timeout.connect(self.refresh_integration_status)
        self.integration_status_timer.start()

        self.mode_combo.currentIndexChanged.connect(
            self._handle_prestart_mode_changed
        )


        self.refresh_rng_availability()
        self.refresh()
        self._handle_prestart_mode_changed()

        # Если программа была закрыта во время аукциона, база сохраняет сессию.
        # При следующем запуске сразу возвращаем пользователя на «Проведение»
        # для running / paused / tie-break / wheel / winner_selected состояний.
        if self._current_session() is not None:
            self.auction_tabs.setCurrentWidget(self.conduct_page)
            QTimer.singleShot(0, self._reset_conduct_auto_scroll)



    def _persist_manual_bid_points(self) -> None:
        """Persist the shared manual amount without changing any auction lot."""
        try:
            self.db.set_auction_manual_bid_points(int(self.bid_amount.value()))
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Аукцион",
                f"Не удалось сохранить значение поля баллов:\n{exc}",
            )

    def _set_wheel_chance_visible(self, visible: bool) -> None:
        """Persist A6.1 visibility and update only the presentation column."""
        normalized = bool(visible)
        self._wheel_chance_visible = normalized
        try:
            self.db.set_auction_wheel_chance_visible(normalized)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Аукцион",
                f"Не удалось сохранить показ шанса в колесе:\n{exc}",
            )
            return
        self._sync_wheel_chance_visibility(self._current_session())

    @staticmethod
    def _format_wheel_probability(probability: float) -> str:
        percent = max(0.0, float(probability)) * 100.0
        return f"{percent:.2f}".replace(".", ",") + " %"

    def _saved_max_amount_default_duration_ms(self) -> int:
        raw = self.db.get_setting(
            "auction_max_amount_default_duration_ms",
            "600000",
        )
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = 10 * 60_000
        if not (AUCTION_MIN_DURATION_MS <= value <= AUCTION_MAX_DURATION_MS):
            return 10 * 60_000
        return value

    def _saved_wheel_default_duration_ms(self) -> int:
        raw = self.db.get_setting("auction_wheel_default_duration_ms", "8000")
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = 8_000
        if not (
            self.db.WHEEL_MIN_DURATION_MS
            <= value
            <= self.db.WHEEL_MAX_DURATION_MS
        ):
            return 8_000
        return value

    def _init_shared_xlsx_sync(self) -> None:
        self._shared_xlsx_path: Path | None = None
        self._shared_xlsx_worker: FunctionWorker | None = None
        self._shared_xlsx_worker_kind = ""
        self._shared_xlsx_last_signature: tuple[int, int] | None = None
        self._shared_xlsx_observed_signature: tuple[int, int] | None = None
        self._shared_xlsx_failed_signature: tuple[int, int] | None = None
        self._shared_xlsx_last_hash = ""
        self._shared_xlsx_write_pending = False
        self._shared_xlsx_write_retry = False
        self._shared_xlsx_applying_external = False
        self._shared_xlsx_shutdown = False

        self._shared_xlsx_poll_timer = QTimer(self)
        self._shared_xlsx_poll_timer.setInterval(SHARED_XLSX_POLL_INTERVAL_MS)
        self._shared_xlsx_poll_timer.timeout.connect(self._shared_xlsx_poll)

        self._shared_xlsx_write_timer = QTimer(self)
        self._shared_xlsx_write_timer.setSingleShot(True)
        self._shared_xlsx_write_timer.setInterval(SHARED_XLSX_LOCAL_WRITE_DEBOUNCE_MS)
        self._shared_xlsx_write_timer.timeout.connect(self._shared_xlsx_start_local_write)

        settings = self.db.get_settings((SHARED_XLSX_ENABLED_KEY, SHARED_XLSX_PATH_KEY))
        enabled = str(settings.get(SHARED_XLSX_ENABLED_KEY, "0")).strip() == "1"
        saved_path = str(settings.get(SHARED_XLSX_PATH_KEY, "")).strip()
        if enabled and saved_path:
            self._shared_xlsx_activate(Path(saved_path), persist=False, import_now=True)
        else:
            self._shared_xlsx_update_controls()

    @staticmethod
    def _shared_xlsx_signature(path: Path) -> tuple[int, int] | None:
        try:
            stat = path.stat()
        except OSError:
            return None
        return int(stat.st_mtime_ns), int(stat.st_size)

    def _shared_xlsx_set_status(self, text: str, *, mtime: float | None = None) -> None:
        self.shared_xlsx_status_label.setText(str(text))
        if mtime is not None:
            self.shared_xlsx_modified_label.setText(
                datetime.fromtimestamp(float(mtime)).strftime("%d.%m.%Y %H:%M:%S")
            )

    def _shared_xlsx_update_controls(self) -> None:
        connected = self._shared_xlsx_path is not None
        busy = self._shared_xlsx_worker is not None
        self.shared_xlsx_path_label.setText(
            str(self._shared_xlsx_path) if connected else "Не подключена"
        )
        self.shared_xlsx_disconnect_btn.setEnabled(connected and not busy)
        self.shared_xlsx_create_btn.setEnabled(not busy)
        self.shared_xlsx_connect_btn.setEnabled(not busy)
        if not connected:
            self.shared_xlsx_modified_label.setText("—")

    def _shared_xlsx_create(self) -> None:
        initial = "Список игр.xlsx"
        if self._shared_xlsx_path is not None:
            initial = str(self._shared_xlsx_path.parent / initial)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Создать совместную таблицу",
            initial,
            "Excel (*.xlsx)",
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() != ".xlsx":
            target = target.with_suffix(".xlsx")
        if target.exists():
            answer = QMessageBox.question(
                self,
                "Заменить таблицу?",
                f"Файл уже существует:\n{target}\n\nЗаменить его текущим основным списком игр?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
        self._shared_xlsx_start_write(target, connect_after=True)

    def _shared_xlsx_connect(self) -> None:
        initial = str(self._shared_xlsx_path.parent) if self._shared_xlsx_path else ""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Подключить совместную таблицу",
            initial,
            "Excel (*.xlsx)",
        )
        if not path:
            return
        self._shared_xlsx_activate(Path(path), persist=True, import_now=True)

    def _shared_xlsx_activate(
        self,
        path: Path,
        *,
        persist: bool,
        import_now: bool,
        initial_hash: str = "",
        initial_signature: tuple[int, int] | None = None,
        initial_mtime: float | None = None,
    ) -> None:
        self._shared_xlsx_path = Path(path)
        self._shared_xlsx_last_hash = str(initial_hash or "")
        self._shared_xlsx_last_signature = initial_signature
        self._shared_xlsx_observed_signature = initial_signature
        self._shared_xlsx_failed_signature = None
        if persist:
            self.db.set_settings_bulk(
                {
                    SHARED_XLSX_ENABLED_KEY: "1",
                    SHARED_XLSX_PATH_KEY: str(self._shared_xlsx_path),
                }
            )
        self._shared_xlsx_poll_timer.start()
        self._shared_xlsx_update_controls()
        if initial_mtime is not None:
            self._shared_xlsx_set_status("Синхронизировано", mtime=initial_mtime)
        elif self._shared_xlsx_path.exists():
            self._shared_xlsx_set_status("Подключено. Проверка таблицы…")
        else:
            self._shared_xlsx_set_status("Файл не найден. Ожидание Google Drive…")
        if import_now:
            QTimer.singleShot(0, self._shared_xlsx_force_import)

    def _shared_xlsx_disconnect(self) -> None:
        if self._shared_xlsx_worker is not None:
            return
        self._shared_xlsx_poll_timer.stop()
        self._shared_xlsx_write_timer.stop()
        self._shared_xlsx_path = None
        self._shared_xlsx_last_hash = ""
        self._shared_xlsx_last_signature = None
        self._shared_xlsx_observed_signature = None
        self._shared_xlsx_failed_signature = None
        self._shared_xlsx_write_pending = False
        self.db.set_settings_bulk(
            {SHARED_XLSX_ENABLED_KEY: "0", SHARED_XLSX_PATH_KEY: ""}
        )
        self._shared_xlsx_update_controls()
        self._shared_xlsx_set_status("Выключено")

    def shared_xlsx_local_data_changed(self) -> None:
        """Schedule a complete XLSX rewrite after a real main-list mutation."""
        if (
            self._shared_xlsx_shutdown
            or self._shared_xlsx_path is None
            or self._shared_xlsx_applying_external
        ):
            return
        self._shared_xlsx_write_pending = True
        self._shared_xlsx_write_retry = False
        self._shared_xlsx_write_timer.start(SHARED_XLSX_LOCAL_WRITE_DEBOUNCE_MS)

    def _shared_xlsx_start_local_write(self) -> None:
        if self._shared_xlsx_path is None or self._shared_xlsx_shutdown:
            return
        if self._shared_xlsx_worker is not None:
            self._shared_xlsx_write_pending = True
            return
        self._shared_xlsx_write_pending = False
        self._shared_xlsx_start_write(self._shared_xlsx_path, connect_after=False)

    def _shared_xlsx_start_write(self, path: Path, *, connect_after: bool) -> None:
        if self._shared_xlsx_worker is not None or self._shared_xlsx_shutdown:
            self._shared_xlsx_write_pending = True
            return
        self._shared_xlsx_set_status("Запись таблицы…")
        previous_hash = self._shared_xlsx_last_hash

        def write_task():
            if not connect_after and path.exists():
                rows = main_games_rows(self.db)
                logical_hash = state_hash(rows)
                if logical_hash == previous_hash:
                    stat = path.stat()
                    return {
                        "path": str(path),
                        "hash": logical_hash,
                        "rows": len(rows),
                        "signature": (int(stat.st_mtime_ns), int(stat.st_size)),
                        "mtime": float(stat.st_mtime),
                        "written": False,
                    }
            result = write_shared_xlsx(self.db, path)
            result["written"] = True
            return result

        worker = FunctionWorker(write_task)
        self._shared_xlsx_worker = worker
        self._shared_xlsx_worker_kind = "write"
        self._shared_xlsx_update_controls()
        worker.signals.result.connect(
            lambda result: self._shared_xlsx_write_succeeded(result, connect_after=connect_after)
        )
        worker.signals.error.connect(self._shared_xlsx_worker_failed)
        worker.signals.finished.connect(self._shared_xlsx_worker_finished)
        self.thread_pool.start(worker)

    def _shared_xlsx_write_succeeded(self, result: dict, *, connect_after: bool) -> None:
        self._shared_xlsx_write_retry = False
        signature = tuple(result.get("signature") or ())
        signature = signature if len(signature) == 2 else None
        if connect_after:
            self._shared_xlsx_activate(
                Path(result["path"]),
                persist=True,
                import_now=False,
                initial_hash=str(result.get("hash") or ""),
                initial_signature=signature,
                initial_mtime=result.get("mtime"),
            )
        else:
            self._shared_xlsx_last_hash = str(result.get("hash") or "")
            self._shared_xlsx_last_signature = signature
            self._shared_xlsx_observed_signature = signature
            self._shared_xlsx_failed_signature = None
            self._shared_xlsx_set_status("Синхронизировано", mtime=result.get("mtime"))

    def _shared_xlsx_force_import(self) -> None:
        if self._shared_xlsx_path is None or self._shared_xlsx_worker is not None:
            return
        signature = self._shared_xlsx_signature(self._shared_xlsx_path)
        if signature is None:
            self._shared_xlsx_set_status("Файл не найден. Ожидание Google Drive…")
            return
        self._shared_xlsx_start_import(signature)

    def _shared_xlsx_poll(self) -> None:
        if self._shared_xlsx_shutdown or self._shared_xlsx_path is None:
            return
        if self._shared_xlsx_worker is not None or self._shared_xlsx_write_timer.isActive():
            return
        signature = self._shared_xlsx_signature(self._shared_xlsx_path)
        if signature is None:
            self._shared_xlsx_observed_signature = None
            self._shared_xlsx_set_status("Файл не найден. Ожидание Google Drive…")
            return
        if signature == self._shared_xlsx_last_signature:
            self._shared_xlsx_observed_signature = signature
            return
        if signature == self._shared_xlsx_failed_signature:
            return
        # Require the cloud-delivered file to remain unchanged for a complete
        # poll interval before opening it. Atomic local writes pass on the next
        # tick; streamed/replaced cloud updates are never consumed halfway.
        if signature != self._shared_xlsx_observed_signature:
            self._shared_xlsx_observed_signature = signature
            self._shared_xlsx_set_status("Обнаружено изменение. Ожидание завершения записи…")
            return
        self._shared_xlsx_start_import(signature)

    def _shared_xlsx_start_import(self, signature: tuple[int, int]) -> None:
        if self._shared_xlsx_path is None or self._shared_xlsx_worker is not None:
            return
        path = self._shared_xlsx_path
        expected_hash = self._shared_xlsx_last_hash
        backup_dir = AppPaths.from_database_path(self.db.path).backups_dir
        self._shared_xlsx_set_status("Чтение таблицы…")

        def import_task():
            payload = read_shared_xlsx(path)
            if tuple(payload["signature"]) != tuple(signature):
                raise SharedXlsxTransientError(
                    "Таблица изменилась до завершения чтения; повторная попытка."
                )
            incoming_hash = str(payload["hash"])
            if incoming_hash == expected_hash:
                return {**payload, "changed": False, "result": None, "backup_path": ""}
            local_hash = state_hash(main_games_rows(self.db))
            if incoming_hash == local_hash:
                return {**payload, "changed": False, "result": None, "backup_path": ""}

            backup_path = self.db.backup_isolated(backup_dir)
            try:
                self.db.prune_backups(backup_dir, 30)
            except Exception:
                # The safety snapshot already exists. Failure to prune old
                # backups must not convert a valid shared-table update into a
                # data-loss situation or leave the three clients divergent.
                pass
            result = self.db.sync_main_games_state(payload["rows"])
            return {
                **payload,
                "changed": bool(result["created"] or result["updated"] or result["deleted"]),
                "result": result,
                "backup_path": str(backup_path),
            }

        worker = FunctionWorker(import_task)
        self._shared_xlsx_worker = worker
        self._shared_xlsx_worker_kind = "import"
        self._shared_xlsx_update_controls()
        worker.signals.result.connect(self._shared_xlsx_import_succeeded)
        worker.signals.error.connect(self._shared_xlsx_worker_failed)
        worker.signals.finished.connect(self._shared_xlsx_worker_finished)
        self.thread_pool.start(worker)

    def _shared_xlsx_import_succeeded(self, payload: dict) -> None:
        signature = tuple(payload.get("signature") or ())
        self._shared_xlsx_last_signature = signature if len(signature) == 2 else None
        self._shared_xlsx_observed_signature = self._shared_xlsx_last_signature
        self._shared_xlsx_failed_signature = None
        self._shared_xlsx_last_hash = str(payload.get("hash") or "")
        self._shared_xlsx_set_status("Синхронизировано", mtime=payload.get("mtime"))
        if payload.get("changed"):
            self._shared_xlsx_applying_external = True
            try:
                self.changed()
            finally:
                self._shared_xlsx_applying_external = False

    def _shared_xlsx_worker_failed(self, exc: Exception) -> None:
        if isinstance(exc, SharedXlsxTransientError):
            self._shared_xlsx_set_status(str(exc))
            if self._shared_xlsx_worker_kind == "write":
                self._shared_xlsx_write_pending = True
                self._shared_xlsx_write_retry = True
            return
        if self._shared_xlsx_worker_kind == "import" and self._shared_xlsx_path is not None:
            self._shared_xlsx_failed_signature = self._shared_xlsx_signature(self._shared_xlsx_path)
        self._shared_xlsx_set_status(f"Ошибка синхронизации: {exc}")

    def _shared_xlsx_worker_finished(self) -> None:
        self._shared_xlsx_worker = None
        self._shared_xlsx_worker_kind = ""
        self._shared_xlsx_update_controls()
        if self._shared_xlsx_write_pending and self._shared_xlsx_path is not None:
            delay = 1500 if self._shared_xlsx_write_retry else SHARED_XLSX_LOCAL_WRITE_DEBOUNCE_MS
            self._shared_xlsx_write_timer.start(delay)

    def shutdown_shared_xlsx(self) -> None:
        self._shared_xlsx_shutdown = True
        self._shared_xlsx_poll_timer.stop()
        self._shared_xlsx_write_timer.stop()

    def _wheel_center_local_picker_items(self) -> list[dict]:
        items: list[dict] = []
        try:
            assets = self.db.sync_managed_media_category(
                MEDIA_CATEGORY_WHEEL_CENTER_ICONS
            )
        except Exception:
            assets = []
        for asset in assets:
            if not media_asset_available(self.db.path.parent, asset):
                continue
            try:
                path = resolve_media_asset_path(self.db.path.parent, asset)
            except (OSError, ValueError):
                continue
            items.append(
                {
                    "asset_id": int(asset.id),
                    "name": str(asset.display_name or path.name),
                    "path": str(path),
                }
            )
        return items

    def _open_wheel_center_picker(self) -> None:
        if self._wheel_center_picker is not None:
            try:
                self._wheel_center_picker.close()
            except RuntimeError:
                pass

        dialog = WheelCenterPickerDialog(self)
        self._wheel_center_picker = dialog
        dialog.set_local_items(self._wheel_center_local_picker_items())
        dialog.uploadRequested.connect(self._wheel_center_picker_upload)
        dialog.localAssetSelected.connect(
            self._wheel_center_picker_local_selected
        )
        dialog.remoteEmoteSelected.connect(
            self._wheel_center_picker_remote_selected
        )

        if self._wheel_center_catalog_cache is not None:
            dialog.set_remote_items(self._wheel_center_catalog_cache)
        else:
            dialog.set_loading_message("Загрузка смайликов…")
            self._start_wheel_center_catalog_load()

        center_global = self.wheel_widget.mapToGlobal(
            self.wheel_widget.rect().center()
        )
        dialog.adjustSize()
        dialog.move(
            int(center_global.x() - dialog.width() / 2),
            int(center_global.y() - dialog.height() / 2),
        )
        dialog.show()

    def _start_wheel_center_catalog_load(self) -> None:
        if self._wheel_center_catalog_worker is not None:
            return
        worker = FunctionWorker(self._load_wheel_center_catalog)
        self._wheel_center_catalog_worker = worker
        worker.signals.result.connect(self._wheel_center_catalog_ready)
        worker.signals.error.connect(self._wheel_center_catalog_failed)
        worker.signals.finished.connect(self._wheel_center_catalog_finished)
        self.thread_pool.start(worker)

    def _load_wheel_center_catalog(self) -> list[EmoteCatalogItem]:
        row = self.db.get_integration_connection("twitch") or {}
        if (
            not bool(row.get("enabled"))
            or str(row.get("status") or "") != "connected"
        ):
            return []

        twitch = self.integration_manager.call_adapter(
            "twitch",
            "list_center_emotes",
        )
        twitch_id = str((twitch or {}).get("twitch_user_id") or "")
        items: list[EmoteCatalogItem] = []
        for raw in (twitch or {}).get("items", []):
            if not isinstance(raw, dict):
                continue
            image_url = str(raw.get("image_url") or "").strip()
            emote_id = str(raw.get("emote_id") or "").strip()
            if not image_url or not emote_id:
                continue
            items.append(
                EmoteCatalogItem(
                    source=str(raw.get("source") or "Twitch"),
                    emote_id=emote_id,
                    name=str(raw.get("name") or emote_id),
                    image_url=image_url,
                    preview_url=str(raw.get("preview_url") or image_url),
                    animated=bool(raw.get("animated")),
                )
            )

        items.extend(fetch_third_party_channel_emotes(twitch_id))
        seen: set[tuple[str, str]] = set()
        unique: list[EmoteCatalogItem] = []
        for item in items:
            if item.dedupe_key in seen:
                continue
            seen.add(item.dedupe_key)
            unique.append(item)
        return hydrate_emote_thumbnails(unique)

    def _wheel_center_catalog_ready(self, items) -> None:
        self._wheel_center_catalog_cache = list(items or [])
        dialog = self._wheel_center_picker
        if dialog is not None:
            try:
                dialog.set_remote_items(self._wheel_center_catalog_cache)
            except RuntimeError:
                pass

    def _wheel_center_catalog_failed(self, _exc) -> None:
        dialog = self._wheel_center_picker
        if dialog is not None:
            try:
                dialog.set_remote_items([])
            except RuntimeError:
                pass

    def _wheel_center_catalog_finished(self) -> None:
        self._wheel_center_catalog_worker = None

    def _apply_wheel_center_asset(self, asset_id: int) -> None:
        asset = self.db.get_media_asset(int(asset_id))
        if (
            asset is None
            or asset.category != MEDIA_CATEGORY_WHEEL_CENTER_ICONS
            or not media_asset_available(self.db.path.parent, asset)
        ):
            QMessageBox.warning(
                self,
                "Изображение центра",
                "Выбранное изображение недоступно.",
            )
            return
        self.db.set_setting(
            WHEEL_CENTER_IMAGE_MEDIA_ID_KEY,
            str(int(asset.id)),
        )
        self._update_wheel_panel(self._current_session())
        self.centerImageChanged.emit(int(asset.id))
        dialog = self._wheel_center_picker
        if dialog is not None:
            dialog.close()

    def _wheel_center_picker_local_selected(self, asset_id: int) -> None:
        self._apply_wheel_center_asset(int(asset_id))

    def _wheel_center_picker_upload(self) -> None:
        if self._wheel_center_import_worker is not None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение центра колеса",
            "",
            "Изображения (*.png *.jpg *.jpeg *.webp *.gif);;Все файлы (*.*)",
        )
        if not path:
            return
        self._start_wheel_center_picker_import(
            prepare_local_center_image,
            path,
        )

    def _wheel_center_picker_remote_selected(self, item) -> None:
        if self._wheel_center_import_worker is not None:
            return
        image_url = str(getattr(item, "image_url", "") or "").strip()
        if not image_url:
            return

        def prepare():
            result = prepare_remote_center_image(image_url)
            label = str(getattr(item, "name", "") or "").strip()
            source = str(getattr(item, "source", "") or "").strip()
            if label:
                result["label"] = (
                    f"{label} ({source})" if source else label
                )
            return result

        self._start_wheel_center_picker_import(prepare)

    def _start_wheel_center_picker_import(self, fn, *args) -> None:
        dialog = self._wheel_center_picker
        if dialog is not None:
            dialog.set_busy(True)
        worker = FunctionWorker(fn, *args)
        self._wheel_center_import_worker = worker
        worker.signals.result.connect(
            self._wheel_center_picker_import_ready
        )
        worker.signals.error.connect(
            self._wheel_center_picker_import_failed
        )
        worker.signals.finished.connect(
            self._wheel_center_picker_import_finished
        )
        self.thread_pool.start(worker)

    def _wheel_center_picker_import_ready(self, prepared: dict) -> None:
        try:
            asset = store_prepared_center_image(self.db, prepared)
        except Exception as exc:
            self._wheel_center_picker_import_failed(exc)
            return
        self._apply_wheel_center_asset(int(asset.id))

    def _wheel_center_picker_import_failed(self, exc) -> None:
        dialog = self._wheel_center_picker
        if dialog is not None:
            try:
                dialog.set_busy(False)
                dialog.set_loading_message("")
            except RuntimeError:
                pass
        QMessageBox.critical(
            self,
            "Изображение центра",
            f"Не удалось добавить изображение:\n{str(exc)}",
        )

    def _wheel_center_picker_import_finished(self) -> None:
        self._wheel_center_import_worker = None

    def refresh_auction_settings(self) -> None:
        """Reload persisted auction defaults without changing a live session."""
        self._default_auction_duration_ms = (
            self._saved_max_amount_default_duration_ms()
        )
        self._default_wheel_duration_ms = self._saved_wheel_default_duration_ms()
        session = self._current_session()
        # Presentation-only D19 setting may change while a session exists; it
        # must refresh local wheel immediately without touching session state.
        if self._wheel_context_relevant(session):
            self._update_wheel_panel(session)
        if session is not None:
            return
        self._prestart_auction_duration_ms = self._default_auction_duration_ms
        self._prestart_wheel_duration_ms = self._default_wheel_duration_ms
        if self._timer_context == "wheel":
            self._set_wheel_timer_ms(self._default_wheel_duration_ms)
        else:
            self._set_prestart_timer_ms(self._default_auction_duration_ms)

    def _prepare_next_max_amount_timer(self) -> None:
        """Restore the saved max-amount default after a session is closed."""
        default_ms = self._saved_max_amount_default_duration_ms()
        self._default_auction_duration_ms = default_ms
        self._prestart_auction_duration_ms = default_ms
        if (
            self._current_session() is None
            and str(self.mode_combo.currentData() or "max_amount") == "max_amount"
        ):
            self._timer_context = "auction"
            self._set_prestart_timer_ms(default_ms)

    def _active_integration_views(self, views=None):
        source = self.integration_manager.views() if views is None else views
        return [
            view
            for view in source
            if view.enabled and view.status != "not_configured"
        ]

    def _runtime_health_snapshot(self) -> dict[str, dict]:
        try:
            snapshot = self.integration_runtime_health()
        except Exception:
            return {}
        return dict(snapshot or {}) if isinstance(snapshot, dict) else {}

    def _integration_status_text(self) -> str:
        base = self.integration_manager.operational_status_text()
        runtime = self._runtime_health_snapshot()
        active_keys = {view.service_key for view in self._active_integration_views()}
        for service_key, state in runtime.items():
            if service_key not in active_keys or not isinstance(state, dict):
                continue
            if str(state.get("error") or "").strip():
                return "Интеграции: ошибка"
        return base

    def refresh_integration_status(self) -> None:
        # A reconnect/account change may alter Twitch/7TV/BTTV/FFZ emotes.
        self._wheel_center_catalog_cache = None
        button = getattr(self, "integration_status_btn", None)
        if button is None:
            return
        # One UI poll should take one provider-state DB snapshot and one runtime
        # health snapshot.  Previously this path rebuilt both twice.
        views = self.integration_manager.views()
        runtime = self._runtime_health_snapshot()
        active_views = self._active_integration_views(views)
        text = self.integration_manager.operational_status_text(views)
        active_keys = {view.service_key for view in active_views}
        if any(
            service_key in active_keys
            and isinstance(state, dict)
            and str(state.get("error") or "").strip()
            for service_key, state in runtime.items()
        ):
            text = "Интеграции: ошибка"
        button.setText(text)
        danger = text == "Интеграции: ошибка"
        if bool(button.property("danger")) != danger:
            button.setProperty("danger", danger)
            button.style().unpolish(button)
            button.style().polish(button)
        errors = []
        for view in active_views:
            state = runtime.get(view.service_key) or {}
            error = str(state.get("error") or "").strip() if isinstance(state, dict) else ""
            if view.message:
                errors.append(f"{view.display_name}: {view.message}")
            elif error:
                errors.append(f"{view.display_name}: {error}")
        if errors:
            button.setToolTip(
                "Сбой интеграции:\n"
                + "\n".join(errors)
                + "\n\nНажмите для подробностей."
            )
        else:
            button.setToolTip(
                "Открыть состояние подключённых сервисов. Подключённые источники пополнений "
                "работают постоянно — отдельного включения для текущего аукциона нет."
            )

    def _show_integration_status_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Интеграции")
        dialog.setMinimumWidth(660)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        note = QLabel(
            "Здесь показаны только подключённые или ранее подключённые активные сервисы. "
            "Источники пополнений работают постоянно: во время аукциона событие относится "
            "к соответствующей сессии, вне аукциона — к постоянному списку игр."
        )
        note.setWordWrap(True)
        note.setProperty("muted", True)
        layout.addWidget(note)

        views = self._active_integration_views()
        runtime = self._runtime_health_snapshot()
        if not views:
            empty = QLabel("Подключённых сервисов нет.")
            empty.setProperty("muted", True)
            layout.addWidget(empty)
        else:
            table = QTableWidget(len(views), 3)
            table.setHorizontalHeaderLabels(["Сервис", "Подключение", "Realtime / события"])
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setSelectionMode(QAbstractItemView.NoSelection)
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            for row, view in enumerate(views):
                table.setItem(row, 0, QTableWidgetItem(view.display_name))
                connection_text = view.status_label
                if view.message:
                    connection_text += f" — {view.message}"
                table.setItem(row, 1, QTableWidgetItem(connection_text))

                state = runtime.get(view.service_key) or {}
                realtime_text = "—"
                if isinstance(state, dict) and state:
                    error = str(state.get("error") or "").strip()
                    expected = bool(state.get("expected", False))
                    connected = bool(state.get("connected", False))
                    detail = str(state.get("detail") or "").strip()
                    if error:
                        realtime_text = "Ошибка: " + error
                    elif connected:
                        realtime_text = detail or "Подключено"
                    elif expected:
                        realtime_text = detail or "Подключение…"
                    else:
                        realtime_text = detail or "Не требуется"
                table.setItem(row, 2, QTableWidgetItem(realtime_text))
            table.resizeRowsToContents()
            layout.addWidget(table)

        buttons = QDialogButtonBox()
        settings_btn = buttons.addButton("Настройки интеграций", QDialogButtonBox.ActionRole)
        close_btn = buttons.addButton(QDialogButtonBox.Close)
        settings_btn.clicked.connect(lambda: (dialog.accept(), self.open_integrations()))
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(buttons)
        self._integration_status_dialog = dialog
        dialog.exec()
        self._integration_status_dialog = None
        self.refresh_integration_status()

    def refresh_rng_availability(self):
        """Show remote RNG choice only after a non-empty saved API key."""
        has_random_org_key = bool(
            self.db.get_random_org_api_key().strip()
        )

        if not has_random_org_key:
            local_index = self.rng_combo.findData("local")
            if local_index >= 0 and self.rng_combo.currentIndex() != local_index:
                self.rng_combo.setCurrentIndex(local_index)

        self._set_visible_state(
            self.rng_selector_label,
            has_random_org_key,
        )
        self._set_visible_state(
            self.rng_combo,
            has_random_org_key,
        )

    def _handle_prestart_mode_changed(self, _index: int = -1):
        if self._current_session() is not None:
            return

        next_context = (
            "wheel"
            if str(self.mode_combo.currentData() or "") == "weighted_wheel"
            else "auction"
        )
        if self._timer_context != next_context:
            try:
                if self._timer_context == "wheel":
                    self._prestart_wheel_duration_ms = self._wheel_timer_ms()
                else:
                    self._prestart_auction_duration_ms = self._prestart_timer_ms()
            except ValueError:
                pass
            self._timer_context = next_context
            value = (
                self._prestart_wheel_duration_ms
                if next_context == "wheel"
                else self._prestart_auction_duration_ms
            )
            self.timer_edit.setText(self._format_milliseconds(value))

        self._update_session_controls(None)
        self._refresh_conduct_wheel_chances_in_place(None)

    def _handle_wheel_format_changed(self, _index: int = -1) -> None:
        combo = getattr(self, "wheel_format_combo", None)
        if combo is None:
            return
        wheel_format = str(combo.currentData() or AUCTION_WHEEL_FORMAT_DEFAULT)
        if wheel_format not in self.WHEEL_FORMAT_LABELS:
            wheel_format = AUCTION_WHEEL_FORMAT_DEFAULT

        session = self._current_session()
        if session is None:
            self._prestart_wheel_format = wheel_format
            self.db.set_setting(AUCTION_WHEEL_FORMAT_KEY, wheel_format)
            self._update_session_controls(None)
            self._refresh_conduct_wheel_chances_in_place(None)
            return

        if str(session.get("mode") or "") != "weighted_wheel":
            return
        try:
            self.db.set_auction_wheel_format(int(session["id"]), wheel_format)
        except Exception as exc:
            # Restore the persisted active-session value if a race crossed a
            # spin/result boundary between UI enablement and this signal.
            current = self._current_session() or session
            persisted = str(
                current.get("wheel_format") or AUCTION_WHEEL_FORMAT_DEFAULT
            )
            index = combo.findData(persisted)
            combo.blockSignals(True)
            combo.setCurrentIndex(max(0, index))
            combo.blockSignals(False)
            QMessageBox.warning(self, "Формат колеса", str(exc))
            return

        self._prestart_wheel_format = wheel_format
        self.db.set_setting(AUCTION_WHEEL_FORMAT_KEY, wheel_format)
        self.refresh()

    def auction_lots_overlay_state(self) -> dict[str, object]:
        """Expose existing Auction-owned transient state without duplicating it."""
        return {
            "mode": (
                "weighted_wheel"
                if self._timer_context == "wheel"
                else "max_amount"
            ),
            "wheel_format": str(
                self.wheel_format_combo.currentData()
                if hasattr(self, "wheel_format_combo")
                else self._prestart_wheel_format
            ),
            "auto_scroll": bool(self._desktop_lot_auto_scroll_enabled),
            "audio": self.auction_browser_audio_state(),
        }

    def set_main_tab_visible(
        self, visible: bool, *, refresh_pending: bool = False
    ) -> bool:
        """Pause hidden visual work while preserving functional auction checks."""
        visible = bool(visible)
        was_visible = bool(self._main_tab_visible)
        self._main_tab_visible = visible

        if not visible:
            self.timer_display_timer.stop()
            self.conduct_scroll_timer.stop()
            self.auction_history_timer.stop()
            self.integration_status_timer.stop()
            self._clear_history_hover_highlight()
            return False

        # A clean tab return does not rebuild both lot tables.  Hidden data
        # mutations still set _refresh_pending and receive one catch-up rebuild;
        # otherwise only session/timer controls are synchronized.
        refreshed = bool(self._refresh_pending or refresh_pending)
        if refreshed:
            self.refresh()
        elif not was_visible:
            self._sync_session_state_without_table_rebuild()

        self._sync_timer_display_activity()
        self._set_timer_running(
            self.conduct_scroll_timer,
            bool(self._desktop_lot_auto_scroll_enabled),
        )
        self._set_timer_running(
            self.auction_history_timer,
            self.auction_tabs.currentWidget() is self.conduct_page,
        )
        self._set_timer_running(self.integration_status_timer, True)
        self.refresh_integration_status()
        return refreshed

    def _handle_inner_tab_changed(self, _index: int):
        # Не отдаём фокус первому QLineEdit новой страницы автоматически.
        # Это важно для «Проведение»: автопрокрутка должна останавливаться
        # только после реального действия пользователя.
        QTimer.singleShot(
            0,
            lambda: self.auction_tabs.setFocus(Qt.OtherFocusReason),
        )
        conduct_page = getattr(self, "conduct_page", None)
        conduct_visible = bool(
            conduct_page is not None
            and self.auction_tabs.currentWidget() is conduct_page
            and getattr(self, "_main_tab_visible", True)
        )
        timer = getattr(self, "auction_history_timer", None)
        if timer is not None:
            self._set_timer_running(timer, conduct_visible)
        if conduct_visible:
            QTimer.singleShot(0, self._poll_auction_history)
        else:
            self._clear_history_hover_highlight()

    def _rules_overlay_url(self) -> str:
        raw_port = self.db.get_setting("api_port", "8765")
        try:
            port = int(raw_port)
        except (TypeError, ValueError):
            port = 8765
        if not (1 <= port <= 65535):
            port = 8765
        return f"http://{DEFAULT_API_HOST}:{port}/rules-overlay"

    def open_auction_rules_editor(self) -> None:
        initial_template_id = None
        session = self._current_session()
        if session is not None:
            snapshot = self.db.get_auction_rules_snapshot(int(session["id"]))
            if snapshot is not None and snapshot.get("template_id") is not None:
                initial_template_id = int(snapshot["template_id"])
        dialog = AuctionRulesEditorDialog(
            self.db,
            self,
            initial_template_id=initial_template_id,
        )
        dialog.exec()

    def show_auction_rules_preview(self) -> None:
        session = None
        if self._active_auction_id is not None:
            session = self.db.get_auction_session(self._active_auction_id)
        if session is None:
            session = self.db.get_open_auction_session()

        if session is not None:
            snapshot = self.db.get_auction_rules_snapshot(int(session["id"]))
            if snapshot is None:
                template = self.db.get_active_rule_template()
                template_name = str(template["name"])
                content_html = str(template["content_html"] or "")
            else:
                template_name = str(snapshot["template_name"] or "")
                content_html = str(snapshot["content_html"] or "")
            title = f"Правила аукциона #{int(session['id'])}"
        else:
            template = self.db.get_active_rule_template()
            template_name = str(template["name"])
            content_html = str(template["content_html"] or "")
            title = "Правила аукциона — активный шаблон"

        dialog = AuctionRulesPreviewDialog(
            title=title,
            template_name=template_name,
            content_html=content_html,
            parent=self,
        )
        dialog.exec()

    @staticmethod
    def _toggle_rules(label: QLabel, button: QPushButton):
        visible = not label.isVisible()
        label.setVisible(visible)
        button.setText("Скрыть правила" if visible else "Правила вкладки")

    def _current_session(self) -> dict | None:
        if self._active_auction_id is not None:
            session = self.db.get_auction_session(self._active_auction_id)
            if session and session.get("status") in self.db.AUCTION_OPEN_STATUSES:
                return session

        session = self.db.get_open_auction_session()
        self._active_auction_id = int(session["id"]) if session else None
        return session

    def _entries_for_table(self, session: dict | None):
        if session is None:
            return [
                {
                    "game_id": int(g.id),
                    "title": g.title,
                    "review": g.review,
                    "total_sm_points": int(g.sm_points),
                    "start_position": position,
                    "current_position": position,
                }
                for position, g in enumerate(self.db.auction_eligible_games(), start=1)
            ]
        return self.db.list_auction_entries(int(session["id"]))

    @staticmethod
    def _format_milliseconds(milliseconds: int) -> str:
        milliseconds = max(0, int(milliseconds))
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        seconds, millis = divmod(remainder, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"

    @classmethod
    def _format_seconds(cls, seconds: int) -> str:
        return cls._format_milliseconds(max(0, int(seconds)) * 1000)

    @staticmethod
    def _parse_timer_text(text: str) -> int:
        return parse_duration_input(text, example="00:10:00.000")

    def _normalize_timer_editor_text(self) -> int:
        total_ms = self._parse_timer_text(self.timer_edit.text())
        self.timer_edit.setText(self._format_milliseconds(total_ms))
        return total_ms

    def _timer_editing_finished(self) -> None:
        """Normalize shorthand on Enter/focus loss and persist wheel edits."""
        try:
            self._normalize_timer_editor_text()
        except ValueError as exc:
            QMessageBox.warning(self, "Время", str(exc))
            self.timer_edit.setFocus()
            return
        self._save_wheel_duration_from_editor()

    def _prestart_timer_ms(self) -> int:
        total_ms = self._parse_timer_text(self.timer_edit.text())
        self.timer_edit.setText(self._format_milliseconds(total_ms))
        if total_ms < AUCTION_MIN_DURATION_MS or total_ms > AUCTION_MAX_DURATION_MS:
            raise ValueError(
                "Длительность аукциона должна быть от 00:00:01.000 до 24:00:00.000."
            )
        return total_ms

    def _wheel_timer_ms(self) -> int:
        total_ms = self._parse_timer_text(self.timer_edit.text())
        self.timer_edit.setText(self._format_milliseconds(total_ms))
        if not (
            self.db.WHEEL_MIN_DURATION_MS
            <= total_ms
            <= self.db.WHEEL_MAX_DURATION_MS
        ):
            raise ValueError(
                "Время вращения колеса должно быть от 00:00:03.000 "
                "до 24:00:00.000."
            )
        return total_ms

    def _set_prestart_timer_ms(self, milliseconds: int) -> None:
        milliseconds = max(AUCTION_MIN_DURATION_MS, min(AUCTION_MAX_DURATION_MS, int(milliseconds)))
        self.timer_edit.setText(self._format_milliseconds(milliseconds))

    def _set_wheel_timer_ms(self, milliseconds: int) -> None:
        milliseconds = max(
            self.db.WHEEL_MIN_DURATION_MS,
            min(self.db.WHEEL_MAX_DURATION_MS, int(milliseconds)),
        )
        self.timer_edit.setText(self._format_milliseconds(milliseconds))

    def _save_wheel_duration_from_editor(self) -> None:
        """Persist edited wheel time before refresh can restore the old value."""
        session = self._current_session()
        if session is None or str(session.get("status") or "") != "awaiting_wheel":
            return

        try:
            wheel_duration_ms = self._wheel_timer_ms()
            self.db.set_auction_wheel_duration_ms(
                int(session["id"]),
                wheel_duration_ms,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Время вращения", str(exc))
            saved_ms = int(session.get("wheel_duration_ms") or 8_000)
            self._set_wheel_timer_ms(saved_ms)
            self.timer_edit.setFocus()
            return
        except Exception as exc:
            QMessageBox.critical(self, "Колесо", str(exc))
            return

        self._timer_context = "wheel"
        self._prestart_wheel_duration_ms = wheel_duration_ms
        self.time_label.setText(
            f"Вращение: {self._format_milliseconds(wheel_duration_ms)}"
        )

    def _populate_lot_table(
        self,
        table: QTableWidget,
        rows,
        selected_id: int | None,
        wheel_probabilities: dict[int, float] | None = None,
    ) -> dict[str, float]:
        is_conduct = table is self.conduct_table
        if is_conduct:
            self._clear_history_hover_highlight()
        compact_columns = (
            self._CONDUCT_COMPACT_COLUMNS
            if is_conduct
            else self._LOT_COMPACT_COLUMNS
        )
        previous_blocked = table.blockSignals(True)
        suspend_live_content_resize(table, compact_columns)
        table.setUpdatesEnabled(False)
        fill_started = time.perf_counter()
        fill_seconds = 0.0
        autosize_seconds = 0.0
        reactivate_seconds = 0.0
        try:
            table.setRowCount(len(rows))
            selected_row = -1

            for r, row in enumerate(rows):
                if is_conduct:
                    probability = (wheel_probabilities or {}).get(
                        int(row["game_id"]),
                        0.0,
                    )
                    values = (
                        row.get("start_position") or "",
                        row.get("current_position") or "",
                        row["title"],
                        self._format_wheel_probability(probability),
                        format_points(int(row["total_sm_points"])),
                    )
                    points_column = 4
                else:
                    values = (
                        row.get("start_position") or "",
                        row.get("current_position") or "",
                        row["title"],
                        format_points(int(row["total_sm_points"])),
                    )
                    points_column = 3

                for c, value in enumerate(values):
                    text = str(value)
                    item = table.item(r, c)
                    if item is None:
                        item = QTableWidgetItem()
                        table.setItem(r, c, item)
                    if item.text() != text:
                        item.setText(text)
                    if c == 0:
                        item.setData(Qt.UserRole, int(row["game_id"]))
                        item.setData(Qt.UserRole + 1, bool(row.get("auction_only")))
                    item.setToolTip(str(row.get("review") or "") if c == 2 else "")
                    if c in (0, 1, 3, points_column):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                if int(row["game_id"]) == selected_id:
                    selected_row = r

            if selected_row >= 0:
                table.selectRow(selected_row)
            fill_seconds = time.perf_counter() - fill_started

            autosize_started = time.perf_counter()
            autosize_compact_columns_once(table, compact_columns)
            autosize_seconds = time.perf_counter() - autosize_started

            reactivate_started = time.perf_counter()
            table.setUpdatesEnabled(True)
            reactivate_seconds = time.perf_counter() - reactivate_started
        finally:
            if not table.updatesEnabled():
                table.setUpdatesEnabled(True)
            table.blockSignals(previous_blocked)

        return {
            "fill": fill_seconds,
            "autosize": autosize_seconds,
            "reactivate": reactivate_seconds,
        }

    def _integration_source_label(self, source: str) -> str:
        adapter = self.integration_manager.registry.get(str(source or ""))
        if adapter is not None and str(adapter.display_name or "").strip():
            return str(adapter.display_name).strip()
        value = str(source or "").strip()
        return value or "Интеграция"

    def _integration_unit_label(
        self,
        source_unit: str,
        stored_label: str = "",
    ) -> str:
        unit = str(source_unit or "").strip()
        for descriptor in self.integration_manager.conversion_units():
            if descriptor.normalized_unit() == unit.upper():
                return str(descriptor.label or stored_label or unit)
        return str(stored_label or unit)

    def _reset_auction_bets(self, auction_id: int | None) -> None:
        self.auction_bets_list.clear()
        self._bets_auction_id = int(auction_id) if auction_id is not None else None
        self._bets_last_log_id = 0
        if auction_id is None:
            self.auction_bets_status.setText(
                "Ставки появятся после запуска аукциона."
            )
        else:
            self.auction_bets_status.setText(
                f"Сессия #{int(auction_id)} · принятые интеграционные ставки появляются автоматически."
            )

    def _sync_auction_bets(self, session: dict | None) -> None:
        """Load only unseen accepted integration bets for current/just-closed session."""
        if session is not None:
            auction_id = int(session["id"])
            if self._bets_auction_id != auction_id:
                self._reset_auction_bets(auction_id)
        elif self._bets_auction_id is None:
            self._reset_auction_bets(None)
            return

        auction_id = self._bets_auction_id
        if auction_id is None:
            return

        try:
            batch = self.db.list_auction_integration_bets(
                auction_id,
                after_id=self._bets_last_log_id,
            )
        except Exception:
            return

        next_cursor = int(batch.get("last_log_id") or self._bets_last_log_id)
        events = list(batch.get("events") or [])
        if next_cursor > self._bets_last_log_id:
            self._bets_last_log_id = next_cursor
        if not events:
            return

        self.auction_bets_list.setUpdatesEnabled(False)
        try:
            for event in events:
                presentation = format_integration_bet_event(
                    event,
                    source_label=self._integration_source_label(event.get("source")),
                    source_unit_label=self._integration_unit_label(
                        event.get("source_unit"),
                        event.get("source_unit_label"),
                    ),
                )
                item = QListWidgetItem(presentation["text"])
                item.setData(Qt.UserRole, presentation.get("game_id"))
                item.setData(Qt.UserRole + 1, presentation.get("event_id"))
                exact_time = presentation.get("exact_time") or "—"
                external_event_id = presentation.get("external_event_id") or "—"
                item.setToolTip(
                    f"Точное время: {exact_time}\n"
                    f"Событие change_log #{presentation.get('event_id') or '—'}\n"
                    f"Внешнее событие: {external_event_id}"
                )
                self.auction_bets_list.insertItem(0, item)
        finally:
            self.auction_bets_list.setUpdatesEnabled(True)

    def _reset_auction_history(self, auction_id: int | None) -> None:
        self._clear_history_hover_highlight()
        self.auction_history_list.clear()
        self._history_auction_id = int(auction_id) if auction_id is not None else None
        self._history_last_log_id = 0
        if auction_id is None:
            self.auction_history_status.setText(
                "История появится после запуска аукциона."
            )
        else:
            self.auction_history_status.setText(
                f"Сессия #{int(auction_id)} · новые события появляются автоматически."
            )

    def _sync_auction_history(self, session: dict | None) -> None:
        """Load only unseen change_log rows for the current/just-closed session."""
        if session is not None:
            auction_id = int(session["id"])
            if self._history_auction_id != auction_id:
                self._reset_auction_history(auction_id)
        elif self._history_auction_id is None:
            self._reset_auction_history(None)
            return

        auction_id = self._history_auction_id
        if auction_id is None:
            return

        try:
            batch = self.db.list_auction_history_events(
                auction_id,
                after_id=self._history_last_log_id,
            )
        except Exception:
            # History is auxiliary operator UI; an audit-read problem must not
            # interrupt auction controls or mutate the underlying session.
            return

        next_cursor = int(batch.get("last_log_id") or self._history_last_log_id)
        events = list(batch.get("events") or [])
        if next_cursor > self._history_last_log_id:
            self._history_last_log_id = next_cursor
        if not events:
            return

        self.auction_history_list.setUpdatesEnabled(False)
        try:
            for event in events:
                presentation = format_auction_history_event(event)
                item = QListWidgetItem(presentation["text"])
                item.setData(Qt.UserRole, presentation.get("game_id"))
                item.setData(Qt.UserRole + 1, presentation.get("event_id"))
                exact_time = presentation.get("exact_time") or "—"
                item.setToolTip(
                    f"Точное время: {exact_time}\n"
                    f"Событие change_log #{presentation.get('event_id') or '—'}"
                )
                # Existing Journal is newest-first; keep the compact history
                # consistent while still reading DB rows oldest-first.
                self.auction_history_list.insertItem(0, item)
        finally:
            self.auction_history_list.setUpdatesEnabled(True)

    def _poll_auction_history(self) -> None:
        if not getattr(self, "_main_tab_visible", True):
            return
        if self.auction_tabs.currentWidget() is not self.conduct_page:
            return
        session = self._current_session()
        self._sync_auction_bets(session)
        self._sync_auction_history(session)

    def _history_event_hovered(self, item: QListWidgetItem) -> None:
        value = item.data(Qt.UserRole)
        try:
            game_id = int(value) if value is not None else None
        except (TypeError, ValueError):
            game_id = None
        self._highlight_conduct_game_from_history(game_id)

    def _highlight_conduct_game_from_history(self, game_id: int | None) -> None:
        self._clear_history_hover_highlight()
        if game_id is None:
            return

        target_row = -1
        target_item = None
        for row in range(self.conduct_table.rowCount()):
            item = self.conduct_table.item(row, 0)
            if item is None:
                continue
            try:
                if int(item.data(Qt.UserRole)) == int(game_id):
                    target_row = row
                    target_item = item
                    break
            except (TypeError, ValueError):
                continue
        if target_row < 0 or target_item is None:
            return

        # A7 manual correction: a linked visible lot must become immediately
        # visible and stay put for as long as the history card is hovered.
        # scrollToItem changes only the viewport; it does not change selection.
        self._history_hover_pauses_auto_scroll = True
        self.conduct_table.scrollToItem(
            target_item,
            QAbstractItemView.ScrollHint.PositionAtCenter,
        )

        hover_brush = QBrush(QColor(255, 214, 64, 90))
        for column in range(self.conduct_table.columnCount()):
            item = self.conduct_table.item(target_row, column)
            if item is None:
                continue
            self._history_hover_brushes.append((item, item.background()))
            item.setBackground(hover_brush)

    def _clear_history_hover_highlight(self) -> None:
        for item, brush in self._history_hover_brushes:
            try:
                item.setBackground(brush)
            except RuntimeError:
                pass
        self._history_hover_brushes.clear()
        # Do not reset scroll direction or position: the normal timer resumes
        # from the revealed row after the pointer leaves the history card.
        self._history_hover_pauses_auto_scroll = False

    def _selected_conduct_is_temporary_lot(self) -> bool:
        row = self.conduct_table.currentRow()
        if row < 0:
            return False
        item = self.conduct_table.item(row, 0)
        if item is None:
            return False
        return bool(item.data(Qt.UserRole + 1))

    def _update_delete_lot_action_state(self, *args, running: bool | None = None):
        if running is None:
            session = self._current_session()
            running = bool(session and session.get("status") == "running")
        enabled = bool(running and self._selected_conduct_is_temporary_lot())
        self._set_visible_state(self.delete_lot_btn, bool(running))
        self._set_enabled_state(self.delete_lot_btn, enabled)

    @staticmethod
    def _set_visible_state(widget: QWidget, visible: bool):
        # isHidden() reflects the widget's own hidden state, independent of
        # whether the parent tab is currently visible.
        if widget.isHidden() == bool(visible):
            widget.setVisible(bool(visible))

    @staticmethod
    def _set_enabled_state(widget: QWidget, enabled: bool):
        if widget.isEnabled() != bool(enabled):
            widget.setEnabled(bool(enabled))

    def copy_wheel_overlay_url(self):
        url = f"{self.window().api.base_url}/wheel-overlay"
        QApplication.clipboard().setText(url)

    def open_wheel_preview(self):
        QDesktopServices.openUrl(
            QUrl(f"{self.window().api.base_url}/wheel-overlay?preview=1")
        )
