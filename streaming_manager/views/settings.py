from __future__ import annotations

import hashlib
import os
import json
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QSettings, Qt, QThreadPool, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QDesktopServices, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QCheckBox, QComboBox, QColorDialog, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFontComboBox, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit,
    QLayout, QMainWindow, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QSpinBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from ..api_server import LocalApiServer
from ..app_paths import AppPaths
from ..backup_restore import (
    create_full_backup_archive,
    launch_full_restore_helper,
    launch_restore_helper,
    stage_full_restore_candidate,
    stage_restore_candidate,
    validate_full_backup_destination,
)
from ..constants import (
    APP_NAME, APP_VERSION,
    AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_DEFAULT,
    AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_KEY,
    AUCTION_AUTO_EXTEND_EXTERNAL_SERVICE_UNITS_ENABLED_DEFAULT,
    AUCTION_AUTO_EXTEND_EXTERNAL_SERVICE_UNITS_ENABLED_KEY,
    AUCTION_AUTO_EXTEND_EXTERNAL_MS_DEFAULT,
    AUCTION_AUTO_EXTEND_EXTERNAL_MS_KEY,
    AUCTION_AUTO_EXTEND_LEADER_ENABLED_DEFAULT,
    AUCTION_AUTO_EXTEND_LEADER_ENABLED_KEY,
    AUCTION_AUTO_EXTEND_LEADER_MS_DEFAULT,
    AUCTION_AUTO_EXTEND_LEADER_MS_KEY,
    AUCTION_AUTO_EXTEND_MAX_MS,
    AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_DEFAULT,
    AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_KEY,
    AUCTION_AUTO_EXTEND_NEW_LOT_MS_DEFAULT,
    AUCTION_AUTO_EXTEND_NEW_LOT_MS_KEY,
    AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_DEFAULT,
    AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_KEY,
    AUCTION_AUTO_EXTEND_THRESHOLD_MS_DEFAULT,
    AUCTION_AUTO_EXTEND_THRESHOLD_MS_KEY,
    AUCTION_MIN_DURATION_MS, AUCTION_MAX_DURATION_MS,
    WHEEL_CENTER_IMAGE_MEDIA_ID_KEY,
    COOP_LABELS, DEFAULT_API_HOST, STATUS_ABANDONED, STATUS_COMPLETED,
    STATUS_LABELS, STATUS_NOT_PLAYED, STATUS_PLAYED, STATUS_PLAYING, STREAM_FORMATS,
)
from ..conversion import ConversionUnit
from ..diagnostic_logs import sanitize_diagnostic_text
from ..integrations import IntegrationManager
from ..twitch import TwitchAdapter, TwitchDeviceCode
from ..donationalerts import (
    DONATIONALERTS_REDIRECT_URI,
    DonationAlertsAdapter,
    DonationAlertsOAuthRequest,
)
from ..donationalerts_runtime import DonationAlertsDonationService
from ..twitch_b4 import (
    TWITCH_DEFAULT_REWARD_COLOR,
    TwitchChannelPointsService,
    TwitchRewardDefinition,
)
from ..database import (
    Database, DuplicateGameError, Game, display_date, display_datetime_local,
    format_points, normalize_date_text, normalize_text_key, parse_date,
)
from ..exporters import (
    export_pointauc_csv, export_public_csv, export_public_json, export_public_xlsx,
    pointauc_text,
)
from ..random_sources import RandomDraw, RandomOrgClient
from ..media import (
    MEDIA_CATEGORY_WHEEL_CENTER_ICONS,
    media_asset_available,
    managed_media_directory,
    resolve_media_asset_path,
)
from ..wheel_center_media import (
    prepare_local_center_image,
    prepare_remote_center_image,
    store_prepared_center_image,
)
from ..workers import FunctionWorker
from ..time_input import parse_duration_input
from .common import (
    APP_STYLE, FocusClearingWidget, ScrollSafeComboBox, ScrollSafeFontComboBox,
    ScrollSafeSpinBox, _center, _selected_id, make_wide_step_control, pick_screen_color,
)

class SettingsTab(QWidget):
    twitch_device_code_ready = Signal(object)
    donationalerts_oauth_ready = Signal(object)

    def __init__(
        self,
        db: Database,
        paths: AppPaths,
        api: LocalApiServer,
        random_org_key_changed: Callable[[], None] | None = None,
        auction_settings_changed: Callable[[], None] | None = None,
        conversion_units_provider: Callable[[], list[ConversionUnit]] | None = None,
        external_points_applied: Callable[[], None] | None = None,
        integration_manager: IntegrationManager | None = None,
        integration_status_changed: Callable[[], None] | None = None,
        twitch_channel_points_service: TwitchChannelPointsService | None = None,
        twitch_runtime_wake: Callable[[], None] | None = None,
        donationalerts_service: DonationAlertsDonationService | None = None,
        donationalerts_runtime_wake: Callable[[], None] | None = None,
    ):
        super().__init__()
        self.db = db
        self.paths = paths
        self.project_dir = paths.root_dir
        self.api = api
        self.random_org_key_changed = random_org_key_changed or (lambda: None)
        self.auction_settings_changed = auction_settings_changed or (lambda: None)
        # B1 integration center is the authority for connection state. It
        # supplies conversion units only for enabled connected adapters; Settings
        # does not persist a parallel provider-specific connected flag.
        self.conversion_units_provider = conversion_units_provider or (lambda: [])
        self.external_points_applied = external_points_applied or (lambda: None)
        self.integration_manager = integration_manager or IntegrationManager(db)
        self.integration_status_changed = integration_status_changed or (lambda: None)
        self.twitch_channel_points_service = twitch_channel_points_service
        self.twitch_runtime_wake = twitch_runtime_wake or (lambda: None)
        self.donationalerts_service = donationalerts_service
        self.donationalerts_runtime_wake = donationalerts_runtime_wake or (lambda: None)
        self.thread_pool = QThreadPool.globalInstance()
        self._rng_worker = None
        self._backup_worker = None
        self._restore_worker = None
        self._full_backup_worker = None
        self._full_restore_worker = None
        self._integration_worker = None
        self._wheel_center_image_worker = None
        self.wheel_center_icons_dir = managed_media_directory(
            self.db.path.parent, MEDIA_CATEGORY_WHEEL_CENTER_ICONS
        )
        self.wheel_center_icons_dir.mkdir(parents=True, exist_ok=True)
        self._integration_buttons: list[QPushButton] = []
        self._integration_config_editors: dict[str, QLineEdit] = {}
        self._twitch_auth_dialog: QDialog | None = None
        self._twitch_auth_timer: QTimer | None = None
        self._donationalerts_auth_dialog: QDialog | None = None
        self._donationalerts_auth_timer: QTimer | None = None
        self._twitch_reward_table: QTableWidget | None = None
        self._twitch_common_title: QLineEdit | None = None
        self.twitch_device_code_ready.connect(self._show_twitch_device_code)
        self.donationalerts_oauth_ready.connect(self._show_donationalerts_oauth)
        twitch_adapter = self.integration_manager.registry.get("twitch")
        if isinstance(twitch_adapter, TwitchAdapter):
            twitch_adapter.set_device_code_callback(self.twitch_device_code_ready.emit)
        donationalerts_adapter = self.integration_manager.registry.get("donationalerts")
        if isinstance(donationalerts_adapter, DonationAlertsAdapter):
            donationalerts_adapter.set_oauth_ready_callback(self.donationalerts_oauth_ready.emit)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)
        outer_layout.setSpacing(9)

        self.settings_tabs = QTabWidget()
        outer_layout.addWidget(self.settings_tabs, 1)

        self.general_page = QWidget()
        layout = QVBoxLayout(self.general_page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel("Локальные данные")
        heading.setStyleSheet("font-size: 15pt; font-weight: 700;")
        layout.addWidget(heading)

        db_label = QLabel(f"База данных:\n{db.path}")
        db_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        db_label.setProperty("muted", True)
        layout.addWidget(db_label)

        btns = QHBoxLayout()
        self.backup_btn = QPushButton("Создать резервную копию")
        self.backup_btn.setProperty("primary", True)
        self.backup_btn.clicked.connect(self.backup)
        self.restore_btn = QPushButton("Восстановить из резервной копии…")
        self.restore_btn.clicked.connect(self.restore_backup)
        self.restore_btn.setToolTip(
            "Проверить выбранную .db, сохранить текущее состояние и безопасно восстановить backup."
        )
        open_data = QPushButton("Открыть папку data")
        open_data.clicked.connect(lambda: self._open_folder(self.db.path.parent))
        open_backups = QPushButton("Открыть папку backups")
        open_backups.clicked.connect(lambda: self._open_folder(self.paths.backups_dir))
        btns.addWidget(self.backup_btn)
        btns.addWidget(self.restore_btn)
        btns.addWidget(open_data)
        btns.addWidget(open_backups)
        btns.addStretch()
        layout.addLayout(btns)

        full_backup_note = QLabel(
            "Полная резервная копия предназначена для сохранения данных вне папки InOneLine "
            "перед полным удалением программы. Она включает БД, защищённые credentials и "
            "managed-media; внутренние logs/backups и внешние связанные файлы не копируются."
        )
        full_backup_note.setWordWrap(True)
        full_backup_note.setProperty("muted", True)
        layout.addWidget(full_backup_note)

        full_btns = QHBoxLayout()
        self.full_backup_btn = QPushButton(
            "Создать полную резервную копию в случае полного удаления программы"
        )
        self.full_backup_btn.clicked.connect(self.create_full_backup)
        self.full_restore_btn = QPushButton(
            "Восстановить полную резервную копию после полного удаления программы…"
        )
        self.full_restore_btn.clicked.connect(self.restore_full_backup)
        self.full_restore_btn.setToolTip(
            "Проверить .iolbackup, создать полную safety-копию текущих данных и восстановить "
            "БД, protected credentials и managed-media с автоматическим перезапуском."
        )
        full_btns.addWidget(self.full_backup_btn)
        full_btns.addWidget(self.full_restore_btn)
        full_btns.addStretch()
        layout.addLayout(full_btns)

        line = QFrame()
        line.setProperty("line", True)
        layout.addWidget(line)

        integrations_hint = QLabel("Интеграции")
        integrations_hint.setStyleSheet("font-size: 13pt; font-weight: 650;")
        layout.addWidget(integrations_hint)
        info = QLabel(
            "Подключения внешних сервисов и RANDOM.ORG находятся на отдельной "
            "внутренней вкладке «Интеграции»."
        )
        info.setWordWrap(True)
        info.setProperty("muted", True)
        layout.addWidget(info)
        layout.addStretch()
        self.general_scroll = self._wrap_settings_page(self.general_page, layout)
        self.settings_tabs.addTab(self.general_scroll, "Общие")

        self.auction_page = QWidget()
        auction_layout = QVBoxLayout(self.auction_page)
        auction_layout.setContentsMargins(18, 18, 18, 18)
        auction_layout.setSpacing(12)

        auction_heading = QLabel("Аукцион")
        auction_heading.setStyleSheet("font-size: 15pt; font-weight: 700;")
        auction_layout.addWidget(auction_heading)

        auction_note = QLabel(
            "Здесь задаются значения времени по умолчанию для новых аукционов. "
            "Перед конкретным запуском их по-прежнему можно изменить вручную."
        )
        auction_note.setWordWrap(True)
        auction_note.setProperty("muted", True)
        auction_layout.addWidget(auction_note)

        max_amount_row = QHBoxLayout()
        max_amount_row.addWidget(
            QLabel("Длительность аукциона «Максимальная сумма» по умолчанию:")
        )
        self.auction_max_amount_duration = QLineEdit()
        self.auction_max_amount_duration.setPlaceholderText("001000")
        self.auction_max_amount_duration.setMinimumWidth(190)
        self.auction_max_amount_duration.setMaximumWidth(220)
        self.auction_max_amount_duration.setMinimumHeight(34)
        self.auction_max_amount_duration.setText(
            self._format_duration_ms(self._saved_auction_max_amount_duration_ms())
        )
        self.auction_max_amount_duration.editingFinished.connect(
            self._normalize_auction_max_amount_duration_editor
        )
        max_amount_row.addWidget(self.auction_max_amount_duration)
        max_amount_row.addStretch()
        auction_layout.addLayout(max_amount_row)

        max_amount_range = QLabel(
            "Ввод: 6 цифр ЧЧММСС (например 003000 → 00:30:00.000) или полный "
            "формат ЧЧ:ММ:СС.мс. Диапазон: от 00:00:01.000 до 24:00:00.000."
        )
        max_amount_range.setProperty("muted", True)
        auction_layout.addWidget(max_amount_range)

        wheel_row = QHBoxLayout()
        wheel_row.addWidget(QLabel("Длительность вращения колеса по умолчанию:"))
        self.auction_wheel_duration = QLineEdit()
        self.auction_wheel_duration.setPlaceholderText("000008")
        self.auction_wheel_duration.setMinimumWidth(190)
        self.auction_wheel_duration.setMaximumWidth(220)
        self.auction_wheel_duration.setMinimumHeight(34)
        self.auction_wheel_duration.setText(
            self._format_duration_ms(self._saved_auction_wheel_duration_ms())
        )
        self.auction_wheel_duration.editingFinished.connect(
            self._normalize_auction_wheel_duration_editor
        )
        wheel_row.addWidget(self.auction_wheel_duration)
        wheel_row.addStretch()
        auction_layout.addLayout(wheel_row)

        wheel_range = QLabel(
            "Ввод: 6 цифр ЧЧММСС (например 001530 → 00:15:30.000) или полный "
            "формат ЧЧ:ММ:СС.мс. Диапазон: от 00:00:03.000 до 24:00:00.000."
        )
        wheel_range.setProperty("muted", True)
        auction_layout.addWidget(wheel_range)

        wheel_center_line = QFrame()
        wheel_center_line.setProperty("line", True)
        auction_layout.addWidget(wheel_center_line)

        wheel_center_heading = QLabel("Изображение в центре колеса")
        wheel_center_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        auction_layout.addWidget(wheel_center_heading)

        wheel_center_note = QLabel(
            "Одно изображение используется одновременно в локальном колесе и OBS. "
            "Оно остаётся неподвижным при вращении. Внешние изображения сначала "
            "проверяются и сохраняются как локальная PNG-копия, поэтому во время "
            "стрима колесо не зависит от доступности внешнего сервиса. "
            "Анимированные GIF/WebP сохраняют анимацию, если формат поддерживается Qt."
        )
        wheel_center_note.setWordWrap(True)
        wheel_center_note.setProperty("muted", True)
        auction_layout.addWidget(wheel_center_note)

        wheel_center_select_row = QHBoxLayout()
        wheel_center_select_row.addWidget(QLabel("Изображение:"))
        self.wheel_center_image_combo = ScrollSafeComboBox()
        self.wheel_center_image_combo.setMinimumWidth(260)
        self.wheel_center_image_combo.currentIndexChanged.connect(
            self._update_wheel_center_image_status
        )
        wheel_center_select_row.addWidget(self.wheel_center_image_combo, 1)
        self.add_wheel_center_file_btn = QPushButton("Добавить файл…")
        self.add_wheel_center_file_btn.clicked.connect(
            self._import_wheel_center_image_file
        )
        wheel_center_select_row.addWidget(self.add_wheel_center_file_btn)
        auction_layout.addLayout(wheel_center_select_row)

        wheel_center_external_row = QHBoxLayout()
        wheel_center_external_row.addWidget(QLabel("Внешний источник:"))
        self.wheel_center_image_source = QLineEdit()
        self.wheel_center_image_source.setPlaceholderText(
            "URL изображения, Twitch/7TV/BetterTTV/FrankerFaceZ ссылка или 7tv:ID / bttv:ID / ffz:ID / twitch:канал"
        )
        wheel_center_external_row.addWidget(self.wheel_center_image_source, 1)
        self.add_wheel_center_url_btn = QPushButton("Загрузить")
        self.add_wheel_center_url_btn.clicked.connect(
            self._import_wheel_center_image_url
        )
        wheel_center_external_row.addWidget(self.add_wheel_center_url_btn)
        auction_layout.addLayout(wheel_center_external_row)

        wheel_center_source_note = QLabel(
            "Примеры: twitch:канал — аватар Twitch; 7tv:ID / bttv:ID / ffz:ID — "
            "emote; также можно вставить страницу emote или прямой URL изображения. "
            "Поддерживаемые анимированные GIF/WebP сохраняются как анимация и работают "
            "одинаково в local и OBS."
        )
        wheel_center_source_note.setWordWrap(True)
        wheel_center_source_note.setProperty("muted", True)
        auction_layout.addWidget(wheel_center_source_note)

        self.wheel_center_image_status = QLabel("")
        self.wheel_center_image_status.setProperty("muted", True)
        self.wheel_center_image_status.setWordWrap(True)
        auction_layout.addWidget(self.wheel_center_image_status)
        self._refresh_wheel_center_image_library()

        auto_extend_line = QFrame()
        auto_extend_line.setProperty("line", True)
        auction_layout.addWidget(auto_extend_line)

        auto_extend_heading = QLabel("Автопродление таймера")
        auto_extend_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        auction_layout.addWidget(auto_extend_heading)

        auto_extend_note = QLabel(
            "Продление прибавляется к текущему остатку времени только во время "
            "активного приёма ставок. Одна операция даёт максимум одно продление; "
            "если совпало несколько включённых причин, применяется самое большое."
        )
        auto_extend_note.setWordWrap(True)
        auto_extend_note.setProperty("muted", True)
        auction_layout.addWidget(auto_extend_note)

        auto_grid = QGridLayout()
        auto_grid.setHorizontalSpacing(10)
        auto_grid.setVerticalSpacing(7)
        auto_grid.addWidget(QLabel("Причина"), 0, 0)
        auto_grid.addWidget(QLabel("Продление"), 0, 1)

        self.auto_extend_leader_enabled = QCheckBox("Смена лидера")
        self.auto_extend_leader_enabled.setChecked(
            self._saved_bool_setting(
                AUCTION_AUTO_EXTEND_LEADER_ENABLED_KEY,
                AUCTION_AUTO_EXTEND_LEADER_ENABLED_DEFAULT,
            )
        )
        self.auto_extend_leader_duration = self._make_auto_extend_duration_editor(
            AUCTION_AUTO_EXTEND_LEADER_MS_KEY,
            AUCTION_AUTO_EXTEND_LEADER_MS_DEFAULT,
        )
        self.auto_extend_leader_enabled.toggled.connect(
            self.auto_extend_leader_duration.setEnabled
        )
        self.auto_extend_leader_duration.setEnabled(
            self.auto_extend_leader_enabled.isChecked()
        )
        auto_grid.addWidget(self.auto_extend_leader_enabled, 1, 0)
        auto_grid.addWidget(self.auto_extend_leader_duration, 1, 1)

        self.auto_extend_new_lot_enabled = QCheckBox("Новый временный лот")
        self.auto_extend_new_lot_enabled.setChecked(
            self._saved_bool_setting(
                AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_KEY,
                AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_DEFAULT,
            )
        )
        self.auto_extend_new_lot_duration = self._make_auto_extend_duration_editor(
            AUCTION_AUTO_EXTEND_NEW_LOT_MS_KEY,
            AUCTION_AUTO_EXTEND_NEW_LOT_MS_DEFAULT,
        )
        self.auto_extend_new_lot_enabled.toggled.connect(
            self.auto_extend_new_lot_duration.setEnabled
        )
        self.auto_extend_new_lot_duration.setEnabled(
            self.auto_extend_new_lot_enabled.isChecked()
        )
        auto_grid.addWidget(self.auto_extend_new_lot_enabled, 2, 0)
        auto_grid.addWidget(self.auto_extend_new_lot_duration, 2, 1)

        self.auto_extend_external_enabled = QCheckBox("Внешнее пожертвование")
        self.auto_extend_external_enabled.setChecked(
            self._saved_bool_setting(
                AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_KEY,
                AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_DEFAULT,
            )
        )
        self.auto_extend_external_duration = self._make_auto_extend_duration_editor(
            AUCTION_AUTO_EXTEND_EXTERNAL_MS_KEY,
            AUCTION_AUTO_EXTEND_EXTERNAL_MS_DEFAULT,
        )
        self.auto_extend_external_service_units_enabled = QCheckBox(
            "Также учитывать неденежные единицы интеграций"
        )
        self.auto_extend_external_service_units_enabled.setChecked(
            self._saved_bool_setting(
                AUCTION_AUTO_EXTEND_EXTERNAL_SERVICE_UNITS_ENABLED_KEY,
                AUCTION_AUTO_EXTEND_EXTERNAL_SERVICE_UNITS_ENABLED_DEFAULT,
            )
        )
        self.auto_extend_external_service_units_enabled.setToolTip(
            "Например: Twitch Channel Points, баллы/очки VK и аналогичные "
            "неденежные единицы других интеграций."
        )
        self.auto_extend_external_service_units_enabled.setStyleSheet(
            "margin-left: 20px;"
        )
        self.auto_extend_external_enabled.toggled.connect(
            self.auto_extend_external_duration.setEnabled
        )
        self.auto_extend_external_enabled.toggled.connect(
            self.auto_extend_external_service_units_enabled.setEnabled
        )
        self.auto_extend_external_duration.setEnabled(
            self.auto_extend_external_enabled.isChecked()
        )
        self.auto_extend_external_service_units_enabled.setEnabled(
            self.auto_extend_external_enabled.isChecked()
        )
        auto_grid.addWidget(self.auto_extend_external_enabled, 3, 0)
        auto_grid.addWidget(self.auto_extend_external_duration, 3, 1)
        auto_grid.addWidget(self.auto_extend_external_service_units_enabled, 4, 0, 1, 2)
        auto_grid.setColumnStretch(2, 1)
        auction_layout.addLayout(auto_grid)

        self.auto_extend_threshold_enabled = QCheckBox(
            "Продлевать только если осталось не больше:"
        )
        self.auto_extend_threshold_enabled.setChecked(
            self._saved_bool_setting(
                AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_KEY,
                AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_DEFAULT,
            )
        )
        self.auto_extend_threshold_duration = self._make_auto_extend_duration_editor(
            AUCTION_AUTO_EXTEND_THRESHOLD_MS_KEY,
            AUCTION_AUTO_EXTEND_THRESHOLD_MS_DEFAULT,
        )
        self.auto_extend_threshold_enabled.toggled.connect(
            self.auto_extend_threshold_duration.setEnabled
        )
        self.auto_extend_threshold_duration.setEnabled(
            self.auto_extend_threshold_enabled.isChecked()
        )
        threshold_row = QHBoxLayout()
        threshold_row.addWidget(self.auto_extend_threshold_enabled)
        threshold_row.addWidget(self.auto_extend_threshold_duration)
        threshold_row.addStretch()
        auction_layout.addLayout(threshold_row)

        auto_extend_range = QLabel(
            "Формат времени: ЧЧ:ММ:СС.мс. Значения продления и порога — от "
            "00:00:00.001 до 24:00:00.000. По умолчанию причины выключены; "
            "порог включён и равен 00:02:00.000."
        )
        auto_extend_range.setWordWrap(True)
        auto_extend_range.setProperty("muted", True)
        auction_layout.addWidget(auto_extend_range)

        save_auction = QPushButton("Сохранить настройки аукциона")
        save_auction.setProperty("primary", True)
        save_auction.clicked.connect(self.save_auction_settings)
        auction_layout.addWidget(save_auction, 0, Qt.AlignLeft)
        auction_layout.addStretch()

        self.auction_scroll = self._wrap_settings_page(self.auction_page, auction_layout)
        self.settings_tabs.addTab(self.auction_scroll, "Аукцион")

        # B1 — единый центр реальных поддерживаемых сервисных адаптеров.
        # Registry пуст до B2, поэтому никаких фальшивых карточек будущих
        # карточек неподключённых или будущих сервисов здесь не создаётся.
        self.integration_page = QWidget()
        integration_layout = QVBoxLayout(self.integration_page)
        integration_layout.setContentsMargins(18, 18, 18, 18)
        integration_layout.setSpacing(12)

        integration_heading = QLabel("Подключить сервисы")
        integration_heading.setStyleSheet("font-size: 15pt; font-weight: 700;")
        integration_layout.addWidget(integration_heading)

        integration_note = QLabel(
            "Подключения, авторизация и состояние поддерживаемых сервисов находятся здесь. "
            "Секреты хранятся отдельно от SQLite в защищённом CredentialStore."
        )
        integration_note.setWordWrap(True)
        integration_note.setProperty("muted", True)
        integration_layout.addWidget(integration_note)

        random_card = QFrame()
        random_card.setFrameShape(QFrame.StyledPanel)
        random_layout = QVBoxLayout(random_card)
        random_layout.setContentsMargins(10, 10, 10, 10)
        random_layout.setSpacing(6)
        rng_heading = QLabel("RANDOM.ORG")
        rng_heading.setStyleSheet("font-size: 12pt; font-weight: 650;")
        random_layout.addWidget(rng_heading)
        rng_note = QLabel(
            "Внешний генератор случайных чисел для Random.org / Random.org+. "
            "API key хранится в защищённом CredentialStore, а не в SQLite."
        )
        rng_note.setWordWrap(True)
        rng_note.setProperty("muted", True)
        random_layout.addWidget(rng_note)
        rng_row = QHBoxLayout()
        rng_row.addWidget(QLabel("API key:"))
        self.random_org_key = QLineEdit()
        self.random_org_key.setEchoMode(QLineEdit.Password)
        self.random_org_key.setText(self.db.get_random_org_api_key())
        self.random_org_key.setPlaceholderText("RANDOM.ORG API key")
        rng_row.addWidget(self.random_org_key, 1)
        save_rng = QPushButton("Сохранить ключ")
        save_rng.clicked.connect(self.save_random_org_key)
        self.check_rng_btn = QPushButton("Проверить API")
        self.check_rng_btn.clicked.connect(self.check_random_org_api)
        rng_row.addWidget(save_rng)
        rng_row.addWidget(self.check_rng_btn)
        random_layout.addLayout(rng_row)
        self.random_org_status = QLabel("Статус: не проверялся")
        self.random_org_status.setProperty("muted", True)
        random_layout.addWidget(self.random_org_status)
        integration_layout.addWidget(random_card)

        self.integration_empty_label = QLabel("Подключённых сервисов пока нет.")
        self.integration_empty_label.setWordWrap(True)
        self.integration_empty_label.setProperty("muted", True)
        integration_layout.addWidget(self.integration_empty_label)

        self.integration_cards_host = QWidget()
        self.integration_cards_layout = QVBoxLayout(self.integration_cards_host)
        self.integration_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.integration_cards_layout.setSpacing(10)
        integration_layout.addWidget(self.integration_cards_host)
        integration_layout.addStretch()
        self.integration_scroll = self._wrap_settings_page(self.integration_page, integration_layout)
        self.settings_tabs.addTab(self.integration_scroll, "Интеграции")
        self._refresh_integrations()

        self.conversion_page = QWidget()
        conversion_layout = QVBoxLayout(self.conversion_page)
        conversion_layout.setContentsMargins(18, 18, 18, 18)
        conversion_layout.setSpacing(12)

        conversion_heading = QLabel("Конвертация в баллы")
        conversion_heading.setStyleSheet("font-size: 15pt; font-weight: 700;")
        conversion_layout.addWidget(conversion_heading)

        conversion_note = QLabel(
            "Баллы всегда целые. Любая внешняя валюта или неденежная единица "
            "сначала умножается на свой настроенный курс, после чего любое "
            "положительное дробное значение округляется вверх до следующего "
            "целого балла. Обратная конвертация баллов во внешние единицы не "
            "используется."
        )
        conversion_note.setWordWrap(True)
        conversion_note.setProperty("muted", True)
        conversion_layout.addWidget(conversion_note)

        currencies_heading = QLabel("Валюты")
        currencies_heading.setStyleSheet("font-size: 12pt; font-weight: 650;")
        conversion_layout.addWidget(currencies_heading)

        self.conversion_rates_widget = QWidget()
        self.conversion_rates_layout = QVBoxLayout(self.conversion_rates_widget)
        self.conversion_rates_layout.setContentsMargins(0, 0, 0, 0)
        self.conversion_rates_layout.setSpacing(8)
        conversion_layout.addWidget(self.conversion_rates_widget)
        self.conversion_rate_edits: dict[str, QLineEdit] = {}
        self.conversion_unit_descriptors: dict[str, ConversionUnit] = {}
        self._conversion_units_signature: tuple[tuple[str, str, str, str], ...] = ()

        conversion_visibility_note = QLabel(
            "RUB остаётся базовой валютой программы. Другие валюты появляются, "
            "когда их сообщает подключённый донат-сервис, когда такая валюта "
            "впервые встречается во внешнем событии или когда для неё уже "
            "сохранён курс. Неденежные единицы конкретного сервиса видны только "
            "пока этот сервис подключён; сохранённый курс при отключении не удаляется."
        )
        conversion_visibility_note.setWordWrap(True)
        conversion_visibility_note.setProperty("muted", True)
        conversion_layout.addWidget(conversion_visibility_note)

        conversion_example = QLabel(
            "Пример: 100,85 RUB при курсе 1 RUB = 1 балл → 101 балл. "
            "Если придёт 250 PLN и курс PLN ещё не задан, событие сохраняется "
            "без начисления. После задания курса оператор увидит рассчитанный "
            "результат и применит событие вручную."
        )
        conversion_example.setProperty("muted", True)
        conversion_example.setWordWrap(True)
        conversion_layout.addWidget(conversion_example)

        pending_heading = QLabel("Ожидают применения")
        pending_heading.setStyleSheet("font-size: 12pt; font-weight: 650;")
        conversion_layout.addWidget(pending_heading)

        pending_note = QLabel(
            "Неизвестная валюта не зачисляется автоматически. Исходное событие "
            "сохраняется здесь. После задания курса проверьте расчёт и нажмите "
            "«Применить». Изменение курса позднее не пересчитывает уже применённое событие."
        )
        pending_note.setWordWrap(True)
        pending_note.setProperty("muted", True)
        conversion_layout.addWidget(pending_note)

        self.pending_conversion_table = QTableWidget(0, 6)
        self.pending_conversion_table.setHorizontalHeaderLabels(
            ["Источник", "Событие", "Игра", "Исходное значение", "К зачислению", "Действие"]
        )
        self.pending_conversion_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.pending_conversion_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pending_conversion_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.pending_conversion_table.verticalHeader().setVisible(False)
        pending_header = self.pending_conversion_table.horizontalHeader()
        pending_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        pending_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        pending_header.setSectionResizeMode(2, QHeaderView.Stretch)
        pending_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        pending_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        pending_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.pending_conversion_table.setMinimumHeight(170)
        conversion_layout.addWidget(self.pending_conversion_table)

        save_conversion = QPushButton("Сохранить курсы")
        save_conversion.setProperty("primary", True)
        save_conversion.clicked.connect(self.save_conversion_settings)
        conversion_layout.addWidget(save_conversion, 0, Qt.AlignLeft)
        conversion_layout.addStretch()

        self.conversion_scroll = self._wrap_settings_page(self.conversion_page, conversion_layout)
        self.settings_tabs.addTab(self.conversion_scroll, "Конвертация")

        # R1.0.9 — all file/list export actions are centralized here.
        self.export_page = QWidget()
        export_layout = QVBoxLayout(self.export_page)
        export_layout.setContentsMargins(18, 18, 18, 18)
        export_layout.setSpacing(12)

        export_heading = QLabel("Экспорт")
        export_heading.setStyleSheet("font-size: 15pt; font-weight: 700;")
        export_layout.addWidget(export_heading)

        public_heading = QLabel("Публичный список")
        public_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        export_layout.addWidget(public_heading)
        public_note = QLabel(
            "Экспорт текущего публичного списка в отдельный файл. "
            "Управление подключённой публичной XLSX-таблицей остаётся на вкладке «Публичный список»."
        )
        public_note.setWordWrap(True)
        public_note.setProperty("muted", True)
        export_layout.addWidget(public_note)

        public_buttons = QHBoxLayout()
        self.export_public_csv_btn = QPushButton("Экспорт CSV")
        self.export_public_json_btn = QPushButton("Экспорт JSON")
        self.export_public_xlsx_btn = QPushButton("Экспорт Excel")
        self.export_public_csv_btn.clicked.connect(self.export_public_csv)
        self.export_public_json_btn.clicked.connect(self.export_public_json)
        self.export_public_xlsx_btn.clicked.connect(self.export_public_xlsx)
        public_buttons.addWidget(self.export_public_csv_btn)
        public_buttons.addWidget(self.export_public_json_btn)
        public_buttons.addWidget(self.export_public_xlsx_btn)
        public_buttons.addStretch()
        export_layout.addLayout(public_buttons)

        export_separator = QFrame()
        export_separator.setProperty("line", True)
        export_layout.addWidget(export_separator)

        pointauc_heading = QLabel("Pointauc")
        pointauc_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        export_layout.addWidget(pointauc_heading)
        pointauc_note = QLabel(
            "Для Pointauc используется текущий список ДЛЯ АУКА: только активные "
            "игры ИГРАЛ + НЕ ИГРАЛ. Экспорт и копирование выполняются в формате "
            "Название|Баллы. ПРОХОДИТСЯ, ПРОЙДЕНО, ЗАБРОШЕНО и архив исключаются."
        )
        pointauc_note.setWordWrap(True)
        pointauc_note.setProperty("muted", True)
        export_layout.addWidget(pointauc_note)

        pointauc_buttons = QHBoxLayout()
        self.export_pointauc_btn = QPushButton("Экспорт CSV для Pointauc")
        self.copy_pointauc_btn = QPushButton("Копировать список")
        self.export_pointauc_btn.clicked.connect(self.export_pointauc)
        self.copy_pointauc_btn.clicked.connect(self.copy_pointauc)
        pointauc_buttons.addWidget(self.export_pointauc_btn)
        pointauc_buttons.addWidget(self.copy_pointauc_btn)
        pointauc_buttons.addStretch()
        export_layout.addLayout(pointauc_buttons)
        export_layout.addStretch()

        self.export_scroll = self._wrap_settings_page(self.export_page, export_layout)
        self.settings_tabs.addTab(self.export_scroll, "Экспорт")
        self.settings_tabs.currentChanged.connect(self._handle_settings_page_changed)
        self._refresh_conversion_rate_rows(force=True)
        self._refresh_pending_conversion_rows()

    @staticmethod
    def _wrap_settings_page(page: QWidget, page_layout: QLayout) -> QScrollArea:
        """Keep long settings pages readable instead of vertically compressing them."""
        # Force the page's minimum height to follow the layout's real minimum
        # whenever dynamic integration/conversion controls are rebuilt. The
        # enclosing scroll area then absorbs height pressure at the 1100x700
        # main-window minimum instead of letting Qt collapse child widgets.
        page_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(page)
        return scroll

    @staticmethod
    def _format_duration_ms(milliseconds: int) -> str:
        milliseconds = max(0, int(milliseconds))
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        seconds, millis = divmod(remainder, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"

    @staticmethod
    def _parse_duration_text(text: str, *, example: str = "00:00:08.000") -> int:
        return parse_duration_input(text, example=example)

    def _normalize_auction_wheel_duration_editor(self) -> None:
        try:
            duration_ms = self._parse_duration_text(
                self.auction_wheel_duration.text()
            )
            self.auction_wheel_duration.setText(
                self._format_duration_ms(duration_ms)
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Настройки аукциона", str(exc))
            self.auction_wheel_duration.setFocus()
            return
        self.auction_wheel_duration.setText(
            self._format_duration_ms(duration_ms)
        )

    def _normalize_auction_max_amount_duration_editor(self) -> None:
        try:
            duration_ms = self._parse_duration_text(
                self.auction_max_amount_duration.text(),
                example="00:10:00.000",
            )
            self.auction_max_amount_duration.setText(
                self._format_duration_ms(duration_ms)
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Настройки аукциона", str(exc))
            self.auction_max_amount_duration.setFocus()

    @staticmethod
    def _setting_bool(raw: object, default: bool) -> bool:
        if raw is None:
            return bool(default)
        normalized = str(raw).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", ""}:
            return False
        return bool(default)

    def _saved_bool_setting(self, key: str, default: bool) -> bool:
        return self._setting_bool(
            self.db.get_setting(key, "1" if default else "0"),
            default,
        )

    def _saved_auto_extend_duration_ms(self, key: str, default: int) -> int:
        raw = self.db.get_setting(key, str(int(default)))
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return int(default)
        if not 1 <= value <= AUCTION_AUTO_EXTEND_MAX_MS:
            return int(default)
        return value

    def _save_export_file(self, title: str, default_name: str, suffix: str, fn) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            default_name,
            f"*{suffix}",
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() != suffix.lower():
            target = target.with_suffix(suffix)
        try:
            fn(self.db, target)
            QMessageBox.information(self, "Экспорт", f"Файл сохранён:\n{target}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка экспорта", str(exc))

    def export_public_csv(self) -> None:
        self._save_export_file("Экспорт CSV", "public_games.csv", ".csv", export_public_csv)

    def export_public_json(self) -> None:
        self._save_export_file("Экспорт JSON", "public_games.json", ".json", export_public_json)

    def export_public_xlsx(self) -> None:
        self._save_export_file("Экспорт Excel", "public_games.xlsx", ".xlsx", export_public_xlsx)

    def export_pointauc(self) -> None:
        self._save_export_file("Экспорт Pointauc", "pointauc.csv", ".csv", export_pointauc_csv)

    def copy_pointauc(self) -> None:
        QApplication.clipboard().setText(pointauc_text(self.db))
        QMessageBox.information(
            self,
            "Pointauc",
            "Список скопирован в буфер обмена.",
        )

    def _make_auto_extend_duration_editor(self, key: str, default: int) -> QLineEdit:
        editor = QLineEdit()
        editor.setMinimumWidth(190)
        editor.setMaximumWidth(220)
        # R1.0.10: disabled QLineEdits inside the auto-extend QGridLayout can
        # receive a transient undersized row on the first layout pass when the
        # saved MainWindow geometry is already at 1100x700. An explicit height
        # floor makes the cold-start layout deterministic; subsequent resizes
        # no longer need to "repair" these fields.
        editor.setMinimumHeight(34)
        editor.setPlaceholderText("000030")
        editor.setText(
            self._format_duration_ms(
                self._saved_auto_extend_duration_ms(key, default)
            )
        )
        editor.editingFinished.connect(
            lambda edit=editor: self._normalize_auto_extend_duration_editor(edit)
        )
        return editor

    def _normalize_auto_extend_duration_editor(self, editor: QLineEdit) -> None:
        try:
            duration_ms = self._parse_duration_text(
                editor.text(),
                example="00:00:30.000",
            )
            if not 1 <= duration_ms <= AUCTION_AUTO_EXTEND_MAX_MS:
                raise ValueError(
                    "Значение автопродления должно быть от "
                    "00:00:00.001 до 24:00:00.000."
                )
        except ValueError as exc:
            QMessageBox.warning(self, "Настройки аукциона", str(exc))
            editor.setFocus()
            return
        editor.setText(self._format_duration_ms(duration_ms))

    def _saved_auction_max_amount_duration_ms(self) -> int:
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

    def _saved_auction_wheel_duration_ms(self) -> int:
        raw = self.db.get_setting("auction_wheel_default_duration_ms", "8000")
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = 8_000
        if not (3_000 <= value <= 24 * 3_600_000):
            return 8_000
        return value

    def save_auction_settings(self):
        try:
            max_amount_duration_ms = self._parse_duration_text(
                self.auction_max_amount_duration.text(),
                example="00:10:00.000",
            )
            if not (AUCTION_MIN_DURATION_MS <= max_amount_duration_ms <= AUCTION_MAX_DURATION_MS):
                raise ValueError(
                    "Длительность аукциона «Максимальная сумма» должна быть от "
                    "00:00:01.000 до 24:00:00.000."
                )

            wheel_duration_ms = self._parse_duration_text(
                self.auction_wheel_duration.text()
            )
            if not (3_000 <= wheel_duration_ms <= 24 * 3_600_000):
                raise ValueError(
                    "Длительность вращения колеса должна быть от "
                    "00:00:03.000 до 24:00:00.000."
                )

            leader_extend_ms = self._parse_duration_text(
                self.auto_extend_leader_duration.text(),
                example="00:00:30.000",
            )
            new_lot_extend_ms = self._parse_duration_text(
                self.auto_extend_new_lot_duration.text(),
                example="00:01:00.000",
            )
            external_extend_ms = self._parse_duration_text(
                self.auto_extend_external_duration.text(),
                example="00:01:00.000",
            )
            threshold_ms = self._parse_duration_text(
                self.auto_extend_threshold_duration.text(),
                example="00:02:00.000",
            )
            for value in (
                leader_extend_ms, new_lot_extend_ms, external_extend_ms, threshold_ms
            ):
                if not 1 <= value <= AUCTION_AUTO_EXTEND_MAX_MS:
                    raise ValueError(
                        "Значения автопродления и порога должны быть от "
                        "00:00:00.001 до 24:00:00.000."
                    )
        except ValueError as exc:
            QMessageBox.warning(self, "Настройки аукциона", str(exc))
            return

        wheel_center_asset = self._selected_wheel_center_image_asset()
        self.db.set_settings_bulk(
            {
                "auction_max_amount_default_duration_ms": str(max_amount_duration_ms),
                "auction_wheel_default_duration_ms": str(wheel_duration_ms),
                WHEEL_CENTER_IMAGE_MEDIA_ID_KEY: (
                    str(wheel_center_asset.id) if wheel_center_asset is not None else ""
                ),
                AUCTION_AUTO_EXTEND_LEADER_ENABLED_KEY: (
                    "1" if self.auto_extend_leader_enabled.isChecked() else "0"
                ),
                AUCTION_AUTO_EXTEND_LEADER_MS_KEY: str(leader_extend_ms),
                AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_KEY: (
                    "1" if self.auto_extend_new_lot_enabled.isChecked() else "0"
                ),
                AUCTION_AUTO_EXTEND_NEW_LOT_MS_KEY: str(new_lot_extend_ms),
                AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_KEY: (
                    "1" if self.auto_extend_external_enabled.isChecked() else "0"
                ),
                AUCTION_AUTO_EXTEND_EXTERNAL_SERVICE_UNITS_ENABLED_KEY: (
                    "1"
                    if self.auto_extend_external_service_units_enabled.isChecked()
                    else "0"
                ),
                AUCTION_AUTO_EXTEND_EXTERNAL_MS_KEY: str(external_extend_ms),
                AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_KEY: (
                    "1" if self.auto_extend_threshold_enabled.isChecked() else "0"
                ),
                AUCTION_AUTO_EXTEND_THRESHOLD_MS_KEY: str(threshold_ms),
            }
        )
        self.auction_max_amount_duration.setText(
            self._format_duration_ms(max_amount_duration_ms)
        )
        self.auction_wheel_duration.setText(
            self._format_duration_ms(wheel_duration_ms)
        )
        self.auto_extend_leader_duration.setText(
            self._format_duration_ms(leader_extend_ms)
        )
        self.auto_extend_new_lot_duration.setText(
            self._format_duration_ms(new_lot_extend_ms)
        )
        self.auto_extend_external_duration.setText(
            self._format_duration_ms(external_extend_ms)
        )
        self.auto_extend_threshold_duration.setText(
            self._format_duration_ms(threshold_ms)
        )
        self.auction_settings_changed()
        QMessageBox.information(
            self,
            "Настройки аукциона",
            "Настройки аукциона сохранены.",
        )

    def _wheel_center_image_assets(self):
        return self.db.sync_managed_media_category(MEDIA_CATEGORY_WHEEL_CENTER_ICONS)

    def _selected_wheel_center_image_asset(self):
        raw = self.wheel_center_image_combo.currentData()
        if not str(raw or "").isdigit():
            return None
        asset = self.db.get_media_asset(int(raw))
        if asset is None or asset.category != MEDIA_CATEGORY_WHEEL_CENTER_ICONS:
            return None
        return asset

    def _refresh_wheel_center_image_library(self, selected_asset_id=None) -> None:
        if selected_asset_id is None:
            selected_asset_id = self.db.get_setting(WHEEL_CENTER_IMAGE_MEDIA_ID_KEY, "")
        try:
            selected_id = int(selected_asset_id) if str(selected_asset_id or "").isdigit() else None
        except (TypeError, ValueError):
            selected_id = None
        combo = self.wheel_center_image_combo
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("— стандартный центр —", "")
        for asset in self._wheel_center_image_assets():
            available = media_asset_available(self.db.path.parent, asset)
            label = asset.display_name if available else f"⚠ файл недоступен: {asset.display_name}"
            combo.addItem(label, asset.id)
        index = combo.findData(selected_id) if selected_id is not None else 0
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)
        self._update_wheel_center_image_status()

    def _update_wheel_center_image_status(self, _index: int = -1) -> None:
        asset = self._selected_wheel_center_image_asset()
        if asset is None:
            self.wheel_center_image_status.setText(
                "Используется стандартный центр колеса без пользовательского изображения."
            )
            self.wheel_center_image_status.setToolTip("")
            return
        available = media_asset_available(self.db.path.parent, asset)
        try:
            path = resolve_media_asset_path(self.db.path.parent, asset)
            self.wheel_center_image_status.setToolTip(str(path))
        except (OSError, ValueError):
            self.wheel_center_image_status.setToolTip("")
        self.wheel_center_image_status.setText(
            "Локальная копия готова. Нажмите «Сохранить настройки аукциона»."
            if available
            else "Файл локальной копии недоступен — добавьте изображение заново."
        )

    def _set_wheel_center_import_busy(self, busy: bool) -> None:
        self.add_wheel_center_file_btn.setEnabled(not busy)
        self.add_wheel_center_url_btn.setEnabled(not busy)
        self.wheel_center_image_source.setEnabled(not busy)
        self.add_wheel_center_url_btn.setText("Загрузка…" if busy else "Загрузить")

    def _twitch_profile_image_url(self, login: str) -> str:
        return str(
            self.integration_manager.call_adapter(
                "twitch", "resolve_profile_image", str(login)
            )
        )

    def _prepare_wheel_center_local(self, source_path: str) -> dict:
        return prepare_local_center_image(source_path)

    def _prepare_wheel_center_remote(self, source: str) -> dict:
        return prepare_remote_center_image(
            source,
            twitch_profile_resolver=self._twitch_profile_image_url,
        )

    def _start_wheel_center_import(self, fn, *args) -> None:
        if self._wheel_center_image_worker is not None:
            return
        self._set_wheel_center_import_busy(True)
        worker = FunctionWorker(fn, *args)
        self._wheel_center_image_worker = worker
        worker.signals.result.connect(self._wheel_center_image_import_ready)
        worker.signals.error.connect(self._wheel_center_image_import_failed)
        worker.signals.finished.connect(self._wheel_center_image_import_finished)
        self.thread_pool.start(worker)

    def _import_wheel_center_image_file(self) -> None:
        if self._wheel_center_image_worker is not None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение центра колеса",
            "",
            "Изображения (*.png *.jpg *.jpeg *.webp *.gif);;Все файлы (*.*)",
        )
        if not path:
            return
        self._start_wheel_center_import(self._prepare_wheel_center_local, path)

    def _import_wheel_center_image_url(self) -> None:
        source = self.wheel_center_image_source.text().strip()
        if not source:
            QMessageBox.warning(
                self, "Изображение центра", "Укажите URL или внешний источник изображения."
            )
            return
        self._start_wheel_center_import(self._prepare_wheel_center_remote, source)

    def _wheel_center_image_import_ready(self, result: dict) -> None:
        try:
            asset = store_prepared_center_image(self.db, result)
            self._refresh_wheel_center_image_library(asset.id)
            self.wheel_center_image_source.clear()
        except Exception as exc:
            self._wheel_center_image_import_failed(exc)

    def _wheel_center_image_import_failed(self, exc) -> None:
        QMessageBox.critical(
            self,
            "Изображение центра",
            f"Не удалось добавить изображение:\n{sanitize_diagnostic_text(str(exc))}",
        )

    def _wheel_center_image_import_finished(self) -> None:
        self._wheel_center_image_worker = None
        self._set_wheel_center_import_busy(False)

    def _connected_conversion_units(self) -> list[ConversionUnit]:
        try:
            units = self.conversion_units_provider() or []
        except Exception:
            # Connection/status UI must not break Settings if an external
            # adapter is temporarily unavailable. The adapter can report its
            # error in the integration center; its conversion rows stay hidden.
            return []
        return [unit for unit in units if isinstance(unit, ConversionUnit)]

    def _visible_conversion_units(self) -> list[ConversionUnit]:
        return self.db.visible_conversion_units(self._connected_conversion_units())

    def _refresh_conversion_rate_rows(self, *, force: bool = False) -> None:
        units = self._visible_conversion_units()
        signature = tuple(
            (item.normalized_unit(), item.label, item.service, item.normalized_kind())
            for item in units
        )
        if not force and signature == self._conversion_units_signature:
            return

        while self.conversion_rates_layout.count():
            item = self.conversion_rates_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.conversion_rate_edits = {}
        self.conversion_unit_descriptors = {}
        for descriptor in units:
            unit = descriptor.normalized_unit()
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            source_label = descriptor.label
            if descriptor.normalized_kind() != "currency" and descriptor.service:
                source_label = f"{descriptor.service} — {descriptor.label}"
            row.addWidget(QLabel(f"1 {source_label} ="))
            editor = QLineEdit()
            editor.setMaximumWidth(180)
            editor.setPlaceholderText("не настроено")
            saved = self.db.get_conversion_rate(unit)
            editor.setText(saved.replace(".", ",") if saved else "")
            row.addWidget(editor)
            row.addWidget(QLabel("баллов"))
            row.addStretch()
            self.conversion_rates_layout.addWidget(row_widget)
            self.conversion_rate_edits[unit] = editor
            self.conversion_unit_descriptors[unit] = descriptor

        self._conversion_units_signature = signature

    def _handle_settings_page_changed(self, _index: int) -> None:
        if self.settings_tabs.currentWidget() is self.integration_scroll:
            self._refresh_integrations()
        if self.settings_tabs.currentWidget() is self.conversion_scroll:
            # Rebuild only if the connected-adapter capability set changed, so
            # ordinary tab switching does not discard unsaved editor text.
            self._refresh_conversion_rate_rows()
            self._refresh_pending_conversion_rows()

    def _refresh_pending_conversion_rows(self) -> None:
        events = self.db.list_pending_conversion_events()
        self.pending_conversion_table.setRowCount(len(events))
        for row_index, event in enumerate(events):
            source = event["source"]
            if event.get("contributor"):
                source = f"{source} — {event['contributor']}"
            values = [
                source,
                event["external_event_id"],
                event.get("game_title") or "Игра недоступна",
                f"{event['source_amount_text']} {event['source_unit_label']}",
            ]
            preview = event.get("preview_sm_points")
            rate = event.get("conversion_rate")
            if rate:
                result_text = f"{preview} баллов (× {rate.replace('.', ',')})"
            else:
                result_text = "Курс не задан"
            values.append(result_text)
            for column, text in enumerate(values):
                self.pending_conversion_table.setItem(
                    row_index, column, QTableWidgetItem(str(text))
                )

            apply_btn = QPushButton("Применить")
            apply_btn.setEnabled(bool(rate) and bool(event.get("game_title")))
            apply_btn.clicked.connect(
                lambda _checked=False, pending_id=event["id"]: 
                    self._apply_pending_conversion(pending_id)
            )
            self.pending_conversion_table.setCellWidget(row_index, 5, apply_btn)

    def _apply_pending_conversion(self, pending_id: int) -> None:
        try:
            event = self.db.get_pending_conversion_event(pending_id)
        except (KeyError, ValueError) as exc:
            QMessageBox.warning(self, "Конвертация", str(exc))
            self._refresh_pending_conversion_rows()
            return
        if not event.get("conversion_rate"):
            QMessageBox.warning(
                self,
                "Конвертация",
                f"Для {event['source_unit']} сначала задайте и сохраните курс.",
            )
            return
        answer = QMessageBox.question(
            self,
            "Применить внешнее событие?",
            f"Игра: {event.get('game_title') or 'недоступна'}\n"
            f"Источник: {event['source']}\n"
            f"Исходное значение: {event['source_amount_text']} {event['source_unit_label']}\n"
            f"Курс: 1 {event['source_unit_label']} = "
            f"{event['conversion_rate'].replace('.', ',')} баллов\n"
            f"Будет начислено: {event['preview_sm_points']} баллов\n\n"
            "Начислить эти баллы?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            result = self.db.apply_pending_conversion_event(pending_id)
        except (KeyError, RuntimeError, ValueError, sqlite3.IntegrityError) as exc:
            QMessageBox.warning(self, "Конвертация", str(exc))
            self._refresh_pending_conversion_rows()
            return
        self.external_points_applied()
        self._refresh_conversion_rate_rows()
        self._refresh_pending_conversion_rows()
        QMessageBox.information(
            self,
            "Конвертация",
            f"Начислено {result['credited_sm_points']} баллов.",
        )

    def save_conversion_settings(self):
        try:
            for unit, editor in self.conversion_rate_edits.items():
                text = editor.text().strip()
                if not text:
                    self.db.clear_conversion_rate(unit)
                    if unit == "RUB":
                        editor.setText("1")
                    continue
                descriptor = self.conversion_unit_descriptors[unit]
                normalized = self.db.set_conversion_rate(
                    unit,
                    text,
                    label=descriptor.label,
                    kind=descriptor.normalized_kind(),
                    service=descriptor.service,
                )
                editor.setText(normalized.replace(".", ","))
        except (TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Конвертация", str(exc))
            return
        self._refresh_conversion_rate_rows(force=True)
        self._refresh_pending_conversion_rows()
        QMessageBox.information(
            self,
            "Конвертация",
            "Курсы конвертации в баллы сохранены.",
        )

    def _clear_integration_cards(self) -> None:
        while self.integration_cards_layout.count():
            item = self.integration_cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._integration_buttons = []
        self._integration_config_editors = {}

    def _refresh_integrations(self) -> None:
        if not hasattr(self, "integration_cards_layout"):
            return
        self._clear_integration_cards()
        views = self.integration_manager.views()
        self.integration_empty_label.setVisible(not views)
        self.integration_cards_host.setVisible(bool(views))
        for view in views:
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 10, 10, 10)
            card_layout.setSpacing(6)

            title = QLabel(view.display_name)
            title.setStyleSheet("font-size: 12pt; font-weight: 650;")
            card_layout.addWidget(title)
            status_text = f"Статус: {view.status_label}"
            if not view.enabled:
                status_text += " · использование отключено"
            status = QLabel(status_text)
            status.setProperty("badge", True)
            card_layout.addWidget(status)

            if view.service_key == "twitch":
                public_note = QLabel(
                    "OAuth: Device Code Grant Flow · Public client · приложение уже настроено; "
                    "Client Secret не требуется и не хранится."
                )
                public_note.setWordWrap(True)
                public_note.setProperty("muted", True)
                card_layout.addWidget(public_note)

            if view.service_key == "donationalerts":
                self._build_donationalerts_connection_controls(card_layout, view)

            for detail_text in view.details:
                detail = QLabel(str(detail_text))
                detail.setWordWrap(True)
                detail.setProperty("muted", True)
                card_layout.addWidget(detail)

            if view.capabilities:
                capabilities = QLabel("Возможности: " + ", ".join(view.capabilities))
                capabilities.setWordWrap(True)
                capabilities.setProperty("muted", True)
                card_layout.addWidget(capabilities)
            if view.message:
                error = QLabel(view.message)
                error.setWordWrap(True)
                error.setProperty("muted", True)
                card_layout.addWidget(error)
            if view.last_check_at:
                checked = QLabel("Последняя проверка: " + str(view.last_check_at))
                checked.setProperty("muted", True)
                card_layout.addWidget(checked)
            if view.last_event_at:
                event = QLabel("Последняя принятая активность: " + str(view.last_event_at))
                event.setProperty("muted", True)
                card_layout.addWidget(event)

            if view.service_key == "twitch" and self.twitch_channel_points_service is not None:
                self._build_twitch_b4_controls(card_layout, view)

            actions = QHBoxLayout()
            specs = (
                ("Подключить", "connect"),
                ("Проверить соединение", "check_connection"),
                ("Переподключить", "reconnect"),
                ("Отключить", "disconnect"),
            )
            for label, action in specs:
                if action == "connect" and view.service_key == "twitch":
                    display_label = "Подключить Twitch"
                elif action == "connect" and view.service_key == "donationalerts":
                    display_label = "Подключить DonationAlerts"
                else:
                    display_label = label
                button = QPushButton(display_label)
                button.clicked.connect(
                    lambda _checked=False, key=view.service_key, op=action: self._run_integration_action(key, op)
                )
                actions.addWidget(button)
                self._integration_buttons.append(button)
            remove = QPushButton("Удалить подключение")
            remove.clicked.connect(
                lambda _checked=False, key=view.service_key: self._confirm_remove_integration(key)
            )
            actions.addWidget(remove)
            self._integration_buttons.append(remove)
            actions.addStretch()
            card_layout.addLayout(actions)
            self.integration_cards_layout.addWidget(card)

    def _build_donationalerts_connection_controls(self, card_layout: QVBoxLayout, view) -> None:
        adapter = self.integration_manager.registry.get("donationalerts")
        if not isinstance(adapter, DonationAlertsAdapter):
            return

        note = QLabel(
            "OAuth: DonationAlerts Public/Implicit Flow. После нажатия «Подключить DonationAlerts» "
            "страница входа и подтверждения открывается в обычном браузере. Client Secret "
            "приложение не запрашивает и не хранит; access token хранится через общий защищённый "
            "CredentialStore (DPAPI в Windows)."
        )
        note.setWordWrap(True)
        note.setProperty("muted", True)
        card_layout.addWidget(note)

        if adapter.has_built_in_client_id():
            configured = QLabel("OAuth Client ID: встроен в сборку (public client).")
            configured.setProperty("muted", True)
            card_layout.addWidget(configured)
            return

        config = self.db.get_integration_connection("donationalerts") or {}
        provider_config = dict(config.get("provider_config") or {})
        current_client_id = adapter.configured_client_id_from_row(provider_config)

        info = QLabel(
            "Для DonationAlerts требуется зарегистрированное OAuth-приложение. Пока у In one line "
            "нет собственного публичного Client ID, можно указать Client ID вашего приложения. "
            "Это не секрет и может храниться в настройках программы."
        )
        info.setWordWrap(True)
        info.setProperty("muted", True)
        card_layout.addWidget(info)

        client_row = QHBoxLayout()
        client_row.addWidget(QLabel("DonationAlerts Client ID:"))
        editor = QLineEdit(current_client_id)
        editor.setPlaceholderText("Только цифры")
        editor.setMaxLength(64)
        editor.setToolTip("Публичный numeric Client ID OAuth-приложения DonationAlerts; Client Secret не нужен.")
        client_row.addWidget(editor, 1)
        save = QPushButton("Сохранить Client ID")
        save.clicked.connect(self._save_donationalerts_client_id)
        client_row.addWidget(save)
        self._integration_config_editors["donationalerts_client_id"] = editor
        self._integration_buttons.append(save)
        card_layout.addLayout(client_row)

        redirect_row = QHBoxLayout()
        redirect_row.addWidget(QLabel("Redirect URI:"))
        redirect = QLineEdit(DONATIONALERTS_REDIRECT_URI)
        redirect.setReadOnly(True)
        redirect.setToolTip("Укажите этот URI при регистрации OAuth-приложения в DonationAlerts без изменений.")
        redirect_row.addWidget(redirect, 1)
        copy_redirect = QPushButton("Копировать")
        copy_redirect.clicked.connect(
            lambda: QApplication.clipboard().setText(DONATIONALERTS_REDIRECT_URI)
        )
        redirect_row.addWidget(copy_redirect)
        self._integration_buttons.append(copy_redirect)
        card_layout.addLayout(redirect_row)

    def _save_donationalerts_client_id(self) -> None:
        if self._integration_worker is not None:
            return
        editor = self._integration_config_editors.get("donationalerts_client_id")
        if editor is None:
            return
        client_id = editor.text().strip()
        try:
            adapter = self.integration_manager.registry.get("donationalerts")
            if not isinstance(adapter, DonationAlertsAdapter):
                raise RuntimeError("DonationAlerts adapter недоступен.")
            # Validate synchronously so a typo is reported next to the form and no
            # worker changes connection state for invalid input.
            adapter._normalize_client_id(client_id)
        except Exception as exc:
            QMessageBox.warning(self, "DonationAlerts", str(exc))
            return

        self._set_integration_actions_enabled(False)
        worker = FunctionWorker(
            lambda: self.integration_manager.call_adapter(
                "donationalerts",
                "set_public_client_id",
                client_id,
            )
        )
        self._integration_worker = worker
        worker.signals.result.connect(lambda _result: self._donationalerts_client_id_saved())
        worker.signals.error.connect(self._integration_action_failed)
        worker.signals.finished.connect(self._integration_action_finished)
        self.thread_pool.start(worker)

    def _donationalerts_client_id_saved(self) -> None:
        self.donationalerts_runtime_wake()
        self._refresh_integrations()
        self._refresh_conversion_rate_rows()
        self.integration_status_changed()
        QMessageBox.information(
            self,
            "DonationAlerts",
            "Client ID сохранён. Теперь нажмите «Подключить DonationAlerts»."
        )

    def _build_twitch_b4_controls(self, card_layout: QVBoxLayout, view) -> None:
        service = self.twitch_channel_points_service
        if service is None:
            return
        config = service.configuration()

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        card_layout.addWidget(divider)

        heading = QLabel("Channel Points — пополнение игр")
        heading.setStyleSheet("font-size: 11pt; font-weight: 650;")
        card_layout.addWidget(heading)

        note = QLabel(
            "Отдельного переключателя «учитывать ставки» больше нет. Пока Twitch подключён "
            "и созданные In one line награды включены, каждое допустимое погашение автоматически "
            "пополняет указанную игру. Во время аукциона оно относится к лоту соответствующей "
            "сессии; вне аукциона — к постоянному списку игр."
        )
        note.setWordWrap(True)
        note.setProperty("muted", True)
        card_layout.addWidget(note)

        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("Общее название:"))
        common_title = QLineEdit(str(config["common_title"]))
        common_title.setMaxLength(45)
        common_title.setPlaceholderText("Ставка")
        title_row.addWidget(common_title, 1)
        self._twitch_common_title = common_title
        card_layout.addLayout(title_row)

        rewards = list(config["rewards"])
        table = QTableWidget(len(rewards), 4)
        table.setHorizontalHeaderLabels(["Стоимость", "Цвет", "Twitch Reward ID", ""])
        table.verticalHeader().setVisible(False)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setMinimumHeight(120)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self._twitch_reward_table = table
        for row_index, definition in enumerate(rewards):
            self._populate_twitch_reward_row(row_index, definition)
        card_layout.addWidget(table)

        reward_actions = QHBoxLayout()
        add_reward = QPushButton("Добавить награду")
        add_reward.clicked.connect(self._add_twitch_reward_row)
        reward_actions.addWidget(add_reward)

        sync_rewards = QPushButton("Сохранить и синхронизировать награды")
        sync_rewards.setEnabled(view.status == "connected" and view.enabled)
        sync_rewards.clicked.connect(self._sync_twitch_rewards_from_form)
        reward_actions.addWidget(sync_rewards)
        self._integration_buttons.extend([add_reward, sync_rewards])
        reward_actions.addStretch()
        card_layout.addLayout(reward_actions)

        availability_actions = QHBoxLayout()
        enable_rewards = QPushButton("Включить награды")
        disable_rewards = QPushButton("Отключить награды")
        manual_allowed = view.status == "connected" and view.enabled
        enable_rewards.setEnabled(manual_allowed)
        disable_rewards.setEnabled(manual_allowed)
        enable_rewards.clicked.connect(lambda: self._set_twitch_rewards_manual(True))
        disable_rewards.clicked.connect(lambda: self._set_twitch_rewards_manual(False))
        availability_actions.addWidget(enable_rewards)
        availability_actions.addWidget(disable_rewards)

        delete_rewards = QPushButton("Удалить награды")
        delete_rewards.setEnabled(view.status == "connected" and view.enabled)
        delete_rewards.clicked.connect(self._confirm_delete_twitch_rewards)
        availability_actions.addWidget(delete_rewards)
        availability_actions.addStretch()
        card_layout.addLayout(availability_actions)
        self._integration_buttons.extend([enable_rewards, disable_rewards, delete_rewards])

        state = QLabel(
            "Награды сейчас: "
            + ("включены" if config["manual_rewards_enabled"] else "выключены")
            + ". Их доступность больше не привязана к старту/паузе/завершению аукциона. "
            "Формат Twitch-названия: «<Общее название> - <Стоимость>»."
        )
        state.setWordWrap(True)
        state.setProperty("muted", True)
        card_layout.addWidget(state)

    def _populate_twitch_reward_row(
        self,
        row_index: int,
        definition: TwitchRewardDefinition | None = None,
    ) -> None:
        table = self._twitch_reward_table
        if table is None:
            return
        definition = definition or TwitchRewardDefinition(100, TWITCH_DEFAULT_REWARD_COLOR, "")
        cost = QSpinBox()
        cost.setRange(1, 2_147_483_647)
        cost.setValue(int(definition.cost))
        cost.setGroupSeparatorShown(True)
        table.setCellWidget(row_index, 0, cost)

        color = QLineEdit(str(definition.color or TWITCH_DEFAULT_REWARD_COLOR).upper())
        color.setMaxLength(7)
        color.setFixedWidth(90)
        color_pick = QPushButton("⌖")
        color_pick.setToolTip(
            "Пипетка: выбрать цвет с экрана. Левый клик — принять, Escape — отмена."
        )
        color_pick.setFixedWidth(max(34, color_pick.sizeHint().height()))
        color_pick.clicked.connect(
            lambda _checked=False, edit=color: self._pick_twitch_reward_color(edit)
        )
        color_cell = QWidget()
        color_cell.setProperty("twitchRewardColorCell", True)
        color_layout = QHBoxLayout(color_cell)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(5)
        color_layout.addWidget(color)
        color_layout.addWidget(color_pick)
        table.setCellWidget(row_index, 1, color_cell)

        reward_id_item = QTableWidgetItem(str(definition.reward_id or "—"))
        reward_id_item.setFlags(reward_id_item.flags() & ~Qt.ItemIsEditable)
        reward_id_item.setData(Qt.UserRole, str(definition.reward_id or ""))
        table.setItem(row_index, 2, reward_id_item)

        remove = QPushButton("Убрать")
        remove.clicked.connect(lambda _checked=False, button=remove: self._remove_twitch_reward_button_row(button))
        table.setCellWidget(row_index, 3, remove)
        self._resize_twitch_reward_action_column()

    def _pick_twitch_reward_color(self, color_edit: QLineEdit) -> None:
        selected = pick_screen_color(self)
        if selected is not None and selected.isValid():
            color_edit.setText(selected.name().upper())

    @staticmethod
    def _twitch_reward_color_edit(widget: QWidget | None) -> QLineEdit | None:
        if isinstance(widget, QLineEdit):
            return widget
        if isinstance(widget, QWidget):
            child = widget.findChild(QLineEdit)
            if isinstance(child, QLineEdit):
                return child
        return None

    def _resize_twitch_reward_action_column(self) -> None:
        table = self._twitch_reward_table
        if table is None:
            return
        required_width = 0
        for row in range(table.rowCount()):
            button = table.cellWidget(row, 3)
            if isinstance(button, QPushButton):
                # A small margin prevents style/DPI rounding from clipping the
                # label even when the row was inserted before the first layout.
                required_width = max(required_width, button.sizeHint().width() + 12)
        if required_width:
            table.setColumnWidth(3, required_width)

    def _add_twitch_reward_row(self) -> None:
        table = self._twitch_reward_table
        if table is None:
            return
        row = table.rowCount()
        table.insertRow(row)
        self._populate_twitch_reward_row(row)
        # Run once more after the insert call returns so the new cell widget has
        # participated in layout even on styles that defer its first size hint.
        QTimer.singleShot(0, self._resize_twitch_reward_action_column)

    def _remove_twitch_reward_button_row(self, button: QPushButton) -> None:
        table = self._twitch_reward_table
        if table is None:
            return
        for row in range(table.rowCount()):
            if table.cellWidget(row, 3) is button:
                table.removeRow(row)
                self._resize_twitch_reward_action_column()
                return

    def _collect_twitch_reward_form(self) -> tuple[str, list[TwitchRewardDefinition]]:
        table = self._twitch_reward_table
        title = self._twitch_common_title
        if table is None or title is None:
            raise RuntimeError("Twitch Channel Points UI ещё не готов.")
        rewards: list[TwitchRewardDefinition] = []
        for row in range(table.rowCount()):
            cost_widget = table.cellWidget(row, 0)
            color_widget = table.cellWidget(row, 1)
            color_edit = self._twitch_reward_color_edit(color_widget)
            reward_item = table.item(row, 2)
            if not isinstance(cost_widget, QSpinBox) or color_edit is None:
                continue
            rewards.append(
                TwitchRewardDefinition(
                    cost=cost_widget.value(),
                    color=color_edit.text().strip(),
                    reward_id=str(reward_item.data(Qt.UserRole) or "") if reward_item is not None else "",
                )
            )
        return title.text().strip(), rewards

    def _run_twitch_b4_action(self, fn: Callable[[], object], *, success_message: str = "") -> None:
        if self._integration_worker is not None:
            return
        self._set_integration_actions_enabled(False)
        worker = FunctionWorker(fn)
        self._integration_worker = worker

        def done(_result):
            self._close_twitch_auth_dialog(success=True)
            self.twitch_runtime_wake()
            self._refresh_integrations()
            self._refresh_conversion_rate_rows()
            self.integration_status_changed()
            if success_message:
                QMessageBox.information(self, "Twitch", success_message)

        worker.signals.result.connect(done)
        worker.signals.error.connect(self._integration_action_failed)
        worker.signals.finished.connect(self._integration_action_finished)
        self.thread_pool.start(worker)

    def _sync_twitch_rewards_from_form(self) -> None:
        service = self.twitch_channel_points_service
        if service is None:
            return
        try:
            common_title, rewards = self._collect_twitch_reward_form()
        except Exception as exc:
            QMessageBox.warning(self, "Twitch", str(exc))
            return

        def action():
            service.save_configuration(
                common_title=common_title,
                rewards=rewards,
            )
            return service.sync_rewards()

        self._run_twitch_b4_action(action, success_message="Twitch-награды синхронизированы.")

    def _set_twitch_rewards_manual(self, enabled: bool) -> None:
        service = self.twitch_channel_points_service
        if service is None:
            return
        self._run_twitch_b4_action(
            lambda: service.set_manual_rewards_enabled(bool(enabled)),
            success_message="Twitch-награды включены." if enabled else "Twitch-награды выключены.",
        )

    def _confirm_delete_twitch_rewards(self) -> None:
        service = self.twitch_channel_points_service
        if service is None or self._integration_worker is not None:
            return
        answer = QMessageBox.warning(
            self,
            "Удалить Twitch-награды?",
            "Удалить все Twitch Custom Rewards, созданные и зарегистрированные In one line для ставок?\n\n"
            "Это отдельное действие: подключение Twitch и история событий останутся. "
            "Удалённые награды придётся создать заново.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self._run_twitch_b4_action(
            service.delete_managed_rewards,
            success_message="Зарегистрированные Twitch-награды удалены.",
        )

    def _show_twitch_device_code(self, info: TwitchDeviceCode) -> None:
        self._close_twitch_auth_dialog(success=True)
        dialog = QDialog(self)
        dialog.setWindowTitle("Подключение Twitch")
        dialog.setModal(False)
        dialog.setMinimumWidth(560)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        heading = QLabel("Авторизация Twitch")
        heading.setStyleSheet("font-size: 14pt; font-weight: 700;")
        layout.addWidget(heading)
        note = QLabel(
            "Откройте страницу Twitch, войдите в нужный аккаунт и подтвердите доступ. "
            f"{APP_NAME} ожидает подтверждение в фоновом режиме."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        code_title = QLabel("Код подтверждения:")
        layout.addWidget(code_title)
        code = QLabel(info.user_code)
        code.setTextInteractionFlags(Qt.TextSelectableByMouse)
        code.setStyleSheet("font-size: 18pt; font-weight: 700;")
        layout.addWidget(code)

        uri = QLabel(info.verification_uri)
        uri.setTextInteractionFlags(Qt.TextSelectableByMouse)
        uri.setWordWrap(True)
        uri.setProperty("muted", True)
        layout.addWidget(uri)

        expires = QLabel()
        expires.setProperty("muted", True)
        layout.addWidget(expires)

        buttons = QHBoxLayout()
        open_btn = QPushButton("Открыть Twitch")
        open_btn.setProperty("primary", True)
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(info.verification_uri)))
        buttons.addWidget(open_btn)
        copy_btn = QPushButton("Копировать код")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(info.user_code))
        buttons.addWidget(copy_btn)
        buttons.addStretch()
        cancel_btn = QPushButton("Отмена")
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        def cancel_authorization() -> None:
            adapter = self.integration_manager.registry.get("twitch")
            if isinstance(adapter, TwitchAdapter):
                adapter.cancel_authorization()
            if dialog.isVisible():
                dialog.reject()

        cancel_btn.clicked.connect(cancel_authorization)
        dialog.rejected.connect(
            lambda: (
                self.integration_manager.registry.get("twitch").cancel_authorization()
                if isinstance(self.integration_manager.registry.get("twitch"), TwitchAdapter)
                else None
            )
        )

        timer = QTimer(dialog)
        def update_countdown() -> None:
            remaining = max(0, int(info.expires_at - datetime.now(timezone.utc).timestamp()))
            minutes, seconds = divmod(remaining, 60)
            expires.setText(f"Код действует ещё: {minutes:02d}:{seconds:02d}")
            if remaining <= 0:
                timer.stop()
        timer.timeout.connect(update_countdown)
        timer.start(1000)
        update_countdown()

        self._twitch_auth_dialog = dialog
        self._twitch_auth_timer = timer
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _show_donationalerts_oauth(self, info: DonationAlertsOAuthRequest) -> None:
        self._close_donationalerts_auth_dialog(success=True)
        dialog = QDialog(self)
        dialog.setWindowTitle("Подключение DonationAlerts")
        dialog.setModal(False)
        dialog.setMinimumWidth(620)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        heading = QLabel("Авторизация DonationAlerts")
        heading.setStyleSheet("font-size: 14pt; font-weight: 700;")
        layout.addWidget(heading)
        note = QLabel(
            "Открываю официальную страницу DonationAlerts в браузере. Войдите в нужный аккаунт "
            "и подтвердите доступ. После подтверждения браузер вернёт результат в локальный "
            "callback In one line, а это окно закроется автоматически."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        uri_title = QLabel("Страница авторизации:")
        layout.addWidget(uri_title)
        uri = QLabel(info.authorization_url)
        uri.setTextInteractionFlags(Qt.TextSelectableByMouse)
        uri.setWordWrap(True)
        uri.setProperty("muted", True)
        layout.addWidget(uri)

        redirect = QLabel("Redirect URI: " + info.redirect_uri)
        redirect.setTextInteractionFlags(Qt.TextSelectableByMouse)
        redirect.setWordWrap(True)
        redirect.setProperty("muted", True)
        layout.addWidget(redirect)

        expires = QLabel()
        expires.setProperty("muted", True)
        layout.addWidget(expires)

        buttons = QHBoxLayout()
        open_btn = QPushButton("Открыть DonationAlerts")
        open_btn.setProperty("primary", True)
        open_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(info.authorization_url))
        )
        buttons.addWidget(open_btn)
        copy_btn = QPushButton("Копировать ссылку")
        copy_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(info.authorization_url)
        )
        buttons.addWidget(copy_btn)
        buttons.addStretch()
        cancel_btn = QPushButton("Отмена")
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        def cancel_authorization() -> None:
            adapter = self.integration_manager.registry.get("donationalerts")
            if isinstance(adapter, DonationAlertsAdapter):
                adapter.cancel_authorization()
            if dialog.isVisible():
                dialog.reject()

        cancel_btn.clicked.connect(cancel_authorization)
        dialog.rejected.connect(
            lambda: (
                self.integration_manager.registry.get("donationalerts").cancel_authorization()
                if isinstance(
                    self.integration_manager.registry.get("donationalerts"),
                    DonationAlertsAdapter,
                )
                else None
            )
        )

        timer = QTimer(dialog)

        def update_countdown() -> None:
            remaining = max(0, int(info.expires_at - datetime.now(timezone.utc).timestamp()))
            minutes, seconds = divmod(remaining, 60)
            expires.setText(f"Ожидание авторизации: {minutes:02d}:{seconds:02d}")
            if remaining <= 0:
                timer.stop()

        timer.timeout.connect(update_countdown)
        timer.start(1000)
        update_countdown()

        self._donationalerts_auth_dialog = dialog
        self._donationalerts_auth_timer = timer
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        # Match the requested Pointauc-style flow: a click in the app immediately
        # opens DonationAlerts in the user's normal browser.
        QDesktopServices.openUrl(QUrl(info.authorization_url))

    def _close_donationalerts_auth_dialog(self, *, success: bool = True) -> None:
        timer = self._donationalerts_auth_timer
        self._donationalerts_auth_timer = None
        if timer is not None:
            timer.stop()
        dialog = self._donationalerts_auth_dialog
        self._donationalerts_auth_dialog = None
        if dialog is not None:
            if success:
                dialog.accept()
            else:
                dialog.reject()
            dialog.deleteLater()

    def _close_twitch_auth_dialog(self, *, success: bool = True) -> None:
        timer = self._twitch_auth_timer
        self._twitch_auth_timer = None
        if timer is not None:
            timer.stop()
        dialog = self._twitch_auth_dialog
        self._twitch_auth_dialog = None
        if dialog is not None:
            if success:
                dialog.accept()
            else:
                dialog.reject()
            dialog.deleteLater()

    def _set_integration_actions_enabled(self, enabled: bool) -> None:
        for button in self._integration_buttons:
            button.setEnabled(bool(enabled))

    def _run_integration_action(self, service_key: str, action: str) -> None:
        if self._integration_worker is not None:
            return
        operation = getattr(self.integration_manager, action)

        def perform_operation():
            twitch_service = self.twitch_channel_points_service if service_key == "twitch" else None
            da_service = self.donationalerts_service if service_key == "donationalerts" else None
            if twitch_service is not None and action in {"disconnect", "remove_connection"}:
                twitch_service.prepare_disconnect()
            if da_service is not None and action in {"disconnect", "remove_connection"}:
                # Intentional disconnect/removal starts the next DonationAlerts
                # connection from a fresh provider high-water baseline.
                da_service.on_connection_removed()
            if twitch_service is not None and action == "reconnect" and twitch_service.managed_reward_ids():
                result = self.integration_manager.call_adapter(
                    "twitch",
                    "reconnect_for_channel_points",
                )
            else:
                result = operation(service_key)
            if twitch_service is not None and action == "remove_connection":
                twitch_service.on_connection_removed()
            return result

        self._set_integration_actions_enabled(False)
        worker = FunctionWorker(perform_operation)
        self._integration_worker = worker
        worker.signals.result.connect(lambda _result: self._integration_action_done())
        worker.signals.error.connect(self._integration_action_failed)
        worker.signals.finished.connect(self._integration_action_finished)
        self.thread_pool.start(worker)

    def _integration_action_done(self) -> None:
        self._close_twitch_auth_dialog(success=True)
        self._close_donationalerts_auth_dialog(success=True)
        self.twitch_runtime_wake()
        self.donationalerts_runtime_wake()
        self._refresh_integrations()
        self._refresh_conversion_rate_rows()
        self.integration_status_changed()

    def _integration_action_failed(self, exc) -> None:
        self._close_twitch_auth_dialog(success=True)
        self._close_donationalerts_auth_dialog(success=True)
        self.twitch_runtime_wake()
        self.donationalerts_runtime_wake()
        self._refresh_integrations()
        self._refresh_conversion_rate_rows()
        self.integration_status_changed()
        QMessageBox.critical(self, "Интеграции", sanitize_diagnostic_text(str(exc)))

    def _integration_action_finished(self) -> None:
        self._integration_worker = None
        self._set_integration_actions_enabled(True)

    def _confirm_remove_integration(self, service_key: str) -> None:
        if self._integration_worker is not None:
            return
        answer = QMessageBox.question(
            self,
            "Удалить подключение",
            "Удалить локальную конфигурацию подключения и credentials?\n\n"
            "История donations/events/contributions/аукционов не удаляется.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self._run_integration_action(service_key, "remove_connection")

    def save_random_org_key(self):
        key = self.random_org_key.text().strip()
        self.db.set_random_org_api_key(key)
        self.random_org_status.setText(
            "Статус: ключ сохранён локально" if key else "Статус: ключ очищен"
        )
        self.random_org_key_changed()

    def check_random_org_api(self):
        key = self.random_org_key.text().strip()
        if not key:
            QMessageBox.information(self, "RANDOM.ORG", "Введите API key.")
            return
        if self._rng_worker is not None:
            return

        self.check_rng_btn.setEnabled(False)
        self.random_org_status.setText("Статус: проверка…")
        worker = FunctionWorker(RandomOrgClient(key).get_usage)
        self._rng_worker = worker
        worker.signals.result.connect(self._random_org_usage_ready)
        worker.signals.error.connect(self._random_org_usage_failed)
        worker.signals.finished.connect(self._random_org_usage_finished)
        self.thread_pool.start(worker)

    def _random_org_usage_ready(self, usage):
        requests_left = usage.get("requestsLeft", "—")
        bits_left = usage.get("bitsLeft", "—")
        text = (
            f"API работает. Запросов осталось: {requests_left}; "
            f"битов осталось: {bits_left}."
        )
        self.random_org_status.setText("Статус: " + text)
        QMessageBox.information(self, "RANDOM.ORG", text)

    def _random_org_usage_failed(self, exc):
        self.random_org_status.setText("Статус: ошибка")
        QMessageBox.critical(self, "RANDOM.ORG", sanitize_diagnostic_text(str(exc)))

    def _random_org_usage_finished(self):
        self.check_rng_btn.setEnabled(True)
        self._rng_worker = None

    def _open_folder(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def _backup_restore_busy(self) -> bool:
        return any(
            worker is not None
            for worker in (
                self._backup_worker,
                self._restore_worker,
                self._full_backup_worker,
                self._full_restore_worker,
            )
        )

    def _set_backup_controls_enabled(self, enabled: bool) -> None:
        self.backup_btn.setEnabled(enabled)
        self.restore_btn.setEnabled(enabled)
        self.full_backup_btn.setEnabled(enabled)
        self.full_restore_btn.setEnabled(enabled)

    def backup(self):
        if self._backup_restore_busy():
            return

        def create_backup():
            path = self.db.backup_isolated(self.paths.backups_dir)
            self.db.prune_backups(self.paths.backups_dir, 30)
            return path

        self._set_backup_controls_enabled(False)
        self.backup_btn.setText("Создание копии…")
        worker = FunctionWorker(create_backup)
        self._backup_worker = worker
        worker.signals.result.connect(
            lambda path: QMessageBox.information(
                self, "Резервная копия", f"Создано:\n{path}"
            )
        )
        worker.signals.error.connect(
            lambda exc: QMessageBox.critical(
                self, "Ошибка резервного копирования", str(exc)
            )
        )
        worker.signals.finished.connect(self._backup_finished)
        self.thread_pool.start(worker)

    def restore_backup(self):
        if self._backup_restore_busy():
            return

        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите резервную копию In one line",
            str((self.paths.backups_dir).resolve()),
            "База In one line (*.db);;Все файлы (*)",
        )
        if not selected:
            return

        source = Path(selected).resolve()
        current = self.db.path.resolve()
        if source == current:
            QMessageBox.information(
                self,
                "Восстановление",
                "Выбран текущий рабочий файл базы данных. Выберите резервную копию из папки backups.",
            )
            return

        answer = QMessageBox.warning(
            self,
            "Восстановить резервную копию?",
            "Текущая база будет заменена данными из выбранной резервной копии.\n\n"
            "Перед заменой программа автоматически сохранит текущее состояние в отдельный safety-backup. "
            "Выбранный файл сначала пройдёт quick_check, integrity_check, foreign_key_check и проверку совместимости схемы.\n\n"
            "После подготовки In one line автоматически перезапустится.\n\n"
            f"Файл:\n{source}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        top_window = self.window()
        top_window.setEnabled(False)
        self._set_backup_controls_enabled(False)
        self.restore_btn.setText("Проверка backup…")

        worker = FunctionWorker(
            lambda: stage_restore_candidate(source, self.db.path.parent)
        )
        self._restore_worker = worker
        worker.signals.result.connect(self._restore_candidate_ready)
        worker.signals.error.connect(self._restore_candidate_failed)
        worker.signals.finished.connect(self._restore_stage_finished)
        self.thread_pool.start(worker)

    def create_full_backup(self):
        if self._backup_restore_busy():
            return

        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"InOneLine_Backup_{stamp}.iolbackup"
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "Сохраните полную резервную копию вне папки InOneLine",
            str((Path.home() / default_name).resolve()),
            "Полная резервная копия In one line (*.iolbackup)",
        )
        if not selected:
            return
        destination = Path(selected).resolve()
        if destination.suffix.lower() != ".iolbackup":
            destination = destination.with_name(destination.name + ".iolbackup")
        try:
            destination = validate_full_backup_destination(destination, self.paths.root_dir)
        except ValueError as exc:
            QMessageBox.warning(self, "Полная резервная копия", str(exc))
            return

        def create_backup():
            work = self.paths.data_dir / (
                f".full_backup_create_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            )
            work.mkdir(parents=True, exist_ok=False)
            try:
                snapshot = self.db.backup_isolated(work)
                return create_full_backup_archive(
                    snapshot,
                    self.paths.data_dir,
                    destination,
                    app_version=APP_VERSION,
                    installation_root=self.paths.root_dir,
                )
            finally:
                shutil.rmtree(work, ignore_errors=True)

        self._set_backup_controls_enabled(False)
        self.full_backup_btn.setText("Создание полной копии…")
        worker = FunctionWorker(create_backup)
        self._full_backup_worker = worker
        worker.signals.result.connect(self._full_backup_created)
        worker.signals.error.connect(self._full_backup_failed)
        worker.signals.finished.connect(self._full_backup_finished)
        self.thread_pool.start(worker)

    def _full_backup_created(self, result):
        credential_note = (
            "\n\nЗащищённые credentials включены. Они используют Windows DPAPI и "
            "предназначены для восстановления под тем же Windows-пользователем."
            if result.get("credentials_present")
            else ""
        )
        QMessageBox.information(
            self,
            "Полная резервная копия",
            "Полная резервная копия создана.\n\n"
            f"Файл:\n{result.get('path')}\n\n"
            f"Файлов данных: {result.get('file_count')}\n"
            f"Размер данных: {result.get('payload_bytes')} байт"
            + credential_note,
        )

    def _full_backup_failed(self, exc):
        QMessageBox.critical(
            self,
            "Ошибка полной резервной копии",
            str(exc),
        )

    def _full_backup_finished(self):
        self._full_backup_worker = None
        self.full_backup_btn.setText(
            "Создать полную резервную копию в случае полного удаления программы"
        )
        if not self._backup_restore_busy():
            self._set_backup_controls_enabled(True)

    def restore_full_backup(self):
        if self._backup_restore_busy():
            return
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите полную резервную копию In one line",
            str(Path.home().resolve()),
            "Полная резервная копия In one line (*.iolbackup);;Все файлы (*)",
        )
        if not selected:
            return
        source = Path(selected).resolve()
        answer = QMessageBox.warning(
            self,
            "Восстановить полную резервную копию?",
            "Будут заменены рабочая база In one line, protected credentials и все managed-media "
            "из папок data\\overlay_backgrounds, data\\music, data\\wheel_jingles и "
            "data\\wheel_center_icons.\n\n"
            "Внешние файлы, на которые In one line только ссылается, изменяться не будут. "
            "Перед заменой программа создаст полную safety-копию текущих данных в backups.\n\n"
            "После проверки In one line закроется, выполнит восстановление и автоматически запустится снова.\n\n"
            f"Файл:\n{source}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.window().setEnabled(False)
        self._set_backup_controls_enabled(False)
        self.full_restore_btn.setText("Проверка полной копии…")
        worker = FunctionWorker(
            lambda: stage_full_restore_candidate(source, self.paths.data_dir)
        )
        self._full_restore_worker = worker
        worker.signals.result.connect(self._full_restore_candidate_ready)
        worker.signals.error.connect(self._full_restore_candidate_failed)
        worker.signals.finished.connect(self._full_restore_stage_finished)
        self.thread_pool.start(worker)

    def _full_restore_candidate_ready(self, result):
        try:
            launch_full_restore_helper(
                self.paths.root_dir,
                result["staged_dir"],
                os.getpid(),
            )
        except Exception as exc:
            shutil.rmtree(Path(result.get("staged_dir", "")), ignore_errors=True)
            self.window().setEnabled(True)
            self._set_backup_controls_enabled(True)
            self.full_restore_btn.setText(
                "Восстановить полную резервную копию после полного удаления программы…"
            )
            QMessageBox.critical(
                self,
                "Ошибка полного восстановления",
                "Не удалось запустить безопасный процесс полного восстановления. Данные не изменены.\n\n"
                + str(exc),
            )
            return
        self.window().close()

    def _full_restore_candidate_failed(self, exc):
        self.window().setEnabled(True)
        self._set_backup_controls_enabled(True)
        self.full_restore_btn.setText(
            "Восстановить полную резервную копию после полного удаления программы…"
        )
        QMessageBox.critical(
            self,
            "Полная резервная копия не подходит",
            "Восстановление не выполнялось. Текущие данные не изменены.\n\n" + str(exc),
        )

    def _full_restore_stage_finished(self):
        self._full_restore_worker = None

    def _restore_candidate_ready(self, result):
        try:
            launch_restore_helper(
                self.paths.root_dir,
                result["staged_path"],
                self.db.path,
                os.getpid(),
            )
        except Exception as exc:
            Path(result.get("staged_path", "")).unlink(missing_ok=True)
            self.window().setEnabled(True)
            self._set_backup_controls_enabled(True)
            self.restore_btn.setText("Восстановить из резервной копии…")
            QMessageBox.critical(
                self,
                "Ошибка восстановления",
                "Не удалось запустить безопасный процесс восстановления. База не изменена.\n\n"
                + str(exc),
            )
            return

        # Helper waits until this process is completely closed, then creates the
        # final safety-backup, replaces the DB atomically and relaunches the app.
        self.window().close()

    def _restore_candidate_failed(self, exc):
        self.window().setEnabled(True)
        self._set_backup_controls_enabled(True)
        self.restore_btn.setText("Восстановить из резервной копии…")
        QMessageBox.critical(
            self,
            "Резервная копия не подходит",
            "Восстановление не выполнялось. Текущая база не изменена.\n\n" + str(exc),
        )

    def _restore_stage_finished(self):
        self._restore_worker = None

    def _backup_finished(self):
        self._backup_worker = None
        self.backup_btn.setText("Создать резервную копию")
        if not self._backup_restore_busy():
            self._set_backup_controls_enabled(True)

