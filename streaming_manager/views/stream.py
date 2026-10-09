from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QColorDialog,
    QFileDialog,
    QFontComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..api_server import LocalApiServer
from ..constants import (
    AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_DEFAULT,
    AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_KEY,
    AUCTION_LOTS_OVERLAY_BACKGROUND_DEFAULT,
    AUCTION_LOTS_OVERLAY_BACKGROUND_KEY,
    AUCTION_LOTS_OVERLAY_BACKGROUND_MEDIA_ID_KEY,
    AUCTION_LOTS_OVERLAY_FONT_COLOR_DEFAULT,
    AUCTION_LOTS_OVERLAY_FONT_COLOR_KEY,
    AUCTION_LOTS_OVERLAY_FONT_FAMILY_DEFAULT,
    AUCTION_LOTS_OVERLAY_FONT_FAMILY_KEY,
    AUCTION_LOTS_OVERLAY_FONT_SIZE_DEFAULT,
    AUCTION_LOTS_OVERLAY_FONT_SIZE_KEY,
    RULES_OVERLAY_AUTOSCROLL_DEFAULT,
    RULES_OVERLAY_AUTOSCROLL_KEY,
    RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT,
    RULES_OVERLAY_BACKGROUND_COLOR_KEY,
    RULES_OVERLAY_BACKGROUND_DEFAULT,
    RULES_OVERLAY_BACKGROUND_KEY,
    RULES_OVERLAY_BACKGROUND_OPACITY_DEFAULT,
    RULES_OVERLAY_BACKGROUND_OPACITY_KEY,
    RULES_OVERLAY_PADDING_DEFAULT,
    RULES_OVERLAY_PADDING_KEY,
    RULES_OVERLAY_VISIBLE_DEFAULT,
    RULES_OVERLAY_VISIBLE_KEY,
    TIMER_OVERLAY_BACKGROUND_COLOR_DEFAULT,
    TIMER_OVERLAY_BACKGROUND_COLOR_KEY,
    TIMER_OVERLAY_BACKGROUND_DEFAULT,
    TIMER_OVERLAY_BACKGROUND_KEY,
    TIMER_OVERLAY_FONT_COLOR_DEFAULT,
    TIMER_OVERLAY_FONT_COLOR_KEY,
    TIMER_OVERLAY_FONT_FAMILY_DEFAULT,
    TIMER_OVERLAY_FONT_FAMILY_KEY,
    TIMER_OVERLAY_FONT_SIZE_DEFAULT,
    TIMER_OVERLAY_FONT_SIZE_KEY,
    MUSIC_PLAYER_OVERLAY_ANIMATION_DEFAULT,
    MUSIC_PLAYER_OVERLAY_ANIMATION_FADE,
    MUSIC_PLAYER_OVERLAY_ANIMATION_KEY,
    MUSIC_PLAYER_OVERLAY_ANIMATION_SLIDE,
    MUSIC_PLAYER_OVERLAY_AUTO_COLORS_DEFAULT,
    MUSIC_PLAYER_OVERLAY_AUTO_COLORS_KEY,
    MUSIC_PLAYER_OVERLAY_BACKGROUND_COLOR_DEFAULT,
    MUSIC_PLAYER_OVERLAY_BACKGROUND_COLOR_KEY,
    MUSIC_PLAYER_OVERLAY_BACKGROUND_DEFAULT,
    MUSIC_PLAYER_OVERLAY_BACKGROUND_KEY,
    MUSIC_PLAYER_OVERLAY_DIRECTION_DEFAULT,
    MUSIC_PLAYER_OVERLAY_DIRECTION_KEY,
    MUSIC_PLAYER_OVERLAY_DURATION_SECONDS_DEFAULT,
    MUSIC_PLAYER_OVERLAY_DURATION_SECONDS_KEY,
    MUSIC_PLAYER_OVERLAY_FONT_FAMILY_DEFAULT,
    MUSIC_PLAYER_OVERLAY_FONT_FAMILY_KEY,
    MUSIC_PLAYER_OVERLAY_FONT_SIZE_DEFAULT,
    MUSIC_PLAYER_OVERLAY_FONT_SIZE_KEY,
    MUSIC_PLAYER_OVERLAY_FRAME_COLOR_DEFAULT,
    MUSIC_PLAYER_OVERLAY_FRAME_COLOR_KEY,
    MUSIC_PLAYER_OVERLAY_SHOW_ALWAYS,
    MUSIC_PLAYER_OVERLAY_SHOW_HIDDEN,
    MUSIC_PLAYER_OVERLAY_SHOW_MODE_DEFAULT,
    MUSIC_PLAYER_OVERLAY_SHOW_MODE_KEY,
    MUSIC_PLAYER_OVERLAY_SHOW_TRACK_CHANGE,
    MUSIC_PLAYER_OVERLAY_SPECTRUM_COLOR_DEFAULT,
    MUSIC_PLAYER_OVERLAY_SPECTRUM_COLOR_KEY,
    MUSIC_PLAYER_OVERLAY_TEXT_COLOR_DEFAULT,
    MUSIC_PLAYER_OVERLAY_TEXT_COLOR_KEY,
    STREAM_FORMATS,
)
from ..database import Database
from ..media import (
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
    MEDIA_STORAGE_EXTERNAL,
    MEDIA_STORAGE_MANAGED,
    media_asset_available,
    managed_media_directory,
    resolve_media_asset_path,
    supported_media_extensions,
)
from ..workers import FunctionWorker
from .common import (
    ScrollSafeComboBox,
    ScrollSafeFontComboBox,
    ScrollSafeSpinBox,
    make_wide_step_control,
    make_screen_color_picker_button,
    pick_screen_color,
)

class StreamTab(QWidget):
    def __init__(self, db: Database, api: LocalApiServer):
        super().__init__()
        self.db = db
        self.api = api
        self.thread_pool = QThreadPool.globalInstance()
        self._background_copy_worker: FunctionWorker | None = None
        self._background_copy_target = "main"
        self.background_dir = managed_media_directory(
            self.db.path.parent, MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
        )
        self.background_dir.mkdir(parents=True, exist_ok=True)

        # The active main-tab scroll host owns page overflow and keeps its
        # vertical scrollbar at the visible right edge of the workspace.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel("Данные для OBS")
        heading.setStyleSheet("font-size: 15pt; font-weight: 700;")
        layout.addWidget(heading)

        obs_help_actions = QHBoxLayout()
        obs_help_actions.setSpacing(8)
        obs_help = QPushButton("Как добавить виджет в OBS")
        obs_help.clicked.connect(self._show_obs_widget_help)
        obs_help_actions.addWidget(obs_help)
        obs_help_actions.addStretch()
        layout.addLayout(obs_help_actions)

        form = QFormLayout()
        form.setVerticalSpacing(10)
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.game_combo = ScrollSafeComboBox()
        self.game_combo.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.info_field = QLineEdit()
        self.info_field.setPlaceholderText("Введите текст информационного блока…")
        self.info_field.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.info_enabled = QCheckBox("Показывать")
        self.info_enabled.setToolTip(
            "Если выключено, информационный блок полностью скрывается, "
            "а остальные элементы занимают освободившееся место."
        )
        self.info_enabled.toggled.connect(self._update_info_enabled_state)

        info_row = QWidget()
        info_layout = QHBoxLayout(info_row)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)
        info_layout.addWidget(self.info_field, 1)
        info_layout.addWidget(self.info_enabled)
        info_layout.addStretch()

        self.format_combo = ScrollSafeComboBox()
        self.format_combo.addItems(STREAM_FORMATS)
        self.format_combo.setMaximumWidth(180)

        form.addRow("Текущая игра:", self.game_combo)
        form.addRow("Текст информационного блока:", info_row)
        form.addRow("Формат:", self.format_combo)
        layout.addLayout(form)

        background_heading = QLabel("Фон оверлея")
        background_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        layout.addWidget(background_heading)

        background_form = QFormLayout()
        background_form.setVerticalSpacing(10)
        background_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        background_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.background_combo = ScrollSafeComboBox()
        self.background_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.background_combo.currentIndexChanged.connect(
            self._update_background_path_field
        )

        self.choose_background_btn = QPushButton("Добавить фон…")
        self.choose_background_btn.setToolTip(
            "Добавить новый фон и решить: скопировать его в программу или использовать исходный файл"
        )
        self.choose_background_btn.clicked.connect(self._import_background_media)

        background_row = QWidget()
        background_row_layout = QHBoxLayout(background_row)
        background_row_layout.setContentsMargins(0, 0, 0, 0)
        background_row_layout.setSpacing(8)
        background_row_layout.addWidget(self.background_combo, 1)
        background_row_layout.addWidget(self.choose_background_btn)
        background_form.addRow("Фон:", background_row)

        self.background_path = QLineEdit()
        self.background_path.setReadOnly(True)
        self.background_path.setPlaceholderText(
            "Фон не выбран — используется стандартная подложка оверлея"
        )
        background_form.addRow("Источник:", self.background_path)

        self.background_status = QLabel("Фон не выбран")
        self.background_status.setProperty("muted", True)
        background_form.addRow("Состояние:", self.background_status)

        self.background_mode = ScrollSafeComboBox()
        self.background_mode.addItem("Растянуть", "stretch")
        self.background_mode.addItem("Вписать", "contain")
        self.background_mode.addItem("Заполнить", "cover")
        self.background_mode.addItem("По центру", "center")
        self.background_mode.setMaximumWidth(220)
        background_form.addRow("Режим отображения:", self.background_mode)

        background_help = QLabel(
            "После выбора файла можно «Копировать в программу» или «Использовать исходный файл». "
            "Копия хранится только в отдельной папке data\\overlay_backgrounds; оригинал программа "
            "никогда не изменяет и не удаляет. Ссылки на исходные файлы обслуживаются OBS через "
            "защищённый локальный media-route без раскрытия произвольного доступа к файловой системе. "
            "Если файл недоступен, он автоматически исключается из выбора; "
            "отсутствующая управляемая копия удаляется из библиотеки, а выбранный фон сбрасывается. "
            "Поддерживаются PNG, JPG, JPEG, WEBP, GIF, MP4 и WEBM. GIF воспроизводится как анимация, "
            "видео — без звука и по кругу. Фон применяется после «Сохранить параметры стрима»."
        )
        background_help.setWordWrap(True)
        background_help.setProperty("muted", True)
        background_form.addRow("", background_help)
        layout.addLayout(background_form)

        overlay_heading = QLabel("Внешний вид оверлея")
        overlay_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        layout.addWidget(overlay_heading)

        overlay_form = QFormLayout()
        self.overlay_form = overlay_form
        overlay_form.setVerticalSpacing(10)
        overlay_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        overlay_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.webcam_enabled = QCheckBox("Показывать")
        self.webcam_position = ScrollSafeComboBox()
        self.webcam_position.addItem("Справа сверху", "top_right")
        self.webcam_position.addItem("Справа снизу", "bottom_right")
        self.webcam_position.addItem("Слева сверху", "top_left")
        self.webcam_position.addItem("Слева снизу", "bottom_left")
        self.webcam_position.setMinimumWidth(190)
        self.webcam_enabled.toggled.connect(
            self._update_main_overlay_conditional_visibility
        )

        webcam_row = QWidget()
        webcam_layout = QHBoxLayout(webcam_row)
        webcam_layout.setContentsMargins(0, 0, 0, 0)
        webcam_layout.setSpacing(8)
        webcam_layout.addWidget(self.webcam_enabled)
        webcam_layout.addWidget(self.webcam_position)
        webcam_layout.addStretch()
        overlay_form.addRow("Область веб-камеры:", webcam_row)

        self.overlay_list_enabled = QCheckBox("Показывать")
        self.overlay_list_side = ScrollSafeComboBox()
        self.overlay_list_side.addItem("Авто — за веб-камерой", "auto")
        self.overlay_list_side.addItem("Справа", "right")
        self.overlay_list_side.addItem("Слева", "left")
        self.overlay_list_side.setMinimumWidth(190)
        self.overlay_list_enabled.toggled.connect(
            self._update_main_overlay_conditional_visibility
        )

        list_row = QWidget()
        list_layout = QHBoxLayout(list_row)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(8)
        list_layout.addWidget(self.overlay_list_enabled)
        list_layout.addWidget(self.overlay_list_side)
        list_layout.addStretch()
        overlay_form.addRow("Список игр:", list_row)

        self.info_position = ScrollSafeComboBox()
        self.info_position.addItem("Авто — за веб-камерой", "auto")
        self.info_position.addItem("Справа сверху", "top_right")
        self.info_position.addItem("Справа снизу", "bottom_right")
        self.info_position.addItem("Слева сверху", "top_left")
        self.info_position.addItem("Слева снизу", "bottom_left")
        self.info_position.setMinimumWidth(190)
        self.info_position.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        overlay_form.addRow("Положение информации:", self.info_position)

        glow_heading = QLabel("Цвета светящегося контура")
        glow_heading.setStyleSheet("font-weight: 600;")
        overlay_form.addRow("", glow_heading)

        self.frame_color_buttons: dict[str, QPushButton] = {}
        self.frame_color_row_widgets: dict[str, QWidget] = {}
        frame_color_rows = (
            ("game", "Игровая рамка:"),
            ("webcam", "Рамка веб-камеры:"),
            ("list", "Рамка списка:"),
            ("info", "Рамка доп. информации:"),
        )
        for color_key, color_label in frame_color_rows:
            color_btn = QPushButton()
            color_btn.setToolTip(
                f"Выбрать цвет светящегося контура: {color_label.rstrip(':').lower()}"
            )
            frame_color_text_width = color_btn.fontMetrics().horizontalAdvance(
                "#FFFFFF"
            )
            color_btn.setMinimumWidth(
                max(112, frame_color_text_width + 38)
            )
            color_btn.setMaximumWidth(
                max(160, frame_color_text_width + 58)
            )
            self._set_color_button(color_btn, "#FFFFFF")
            color_btn.clicked.connect(
                lambda checked=False, key=color_key: self._choose_frame_color(key)
            )
            pipette_btn = make_screen_color_picker_button()
            pipette_btn.setToolTip(
                "Выбрать цвет непосредственно с экрана. Левый клик — принять, Escape — отмена."
            )
            pipette_btn.clicked.connect(
                lambda checked=False, button=color_btn: self._pick_color_from_screen(button)
            )
            color_row = QWidget()
            color_row_layout = QHBoxLayout(color_row)
            color_row_layout.setContentsMargins(0, 0, 0, 0)
            color_row_layout.setSpacing(8)
            color_row_layout.addWidget(color_btn)
            color_row_layout.addWidget(pipette_btn)
            color_row_layout.addStretch()
            self.frame_color_buttons[color_key] = color_btn
            self.frame_color_row_widgets[color_key] = color_row
            overlay_form.addRow(color_label, color_row)

        overlay_help = QLabel(
            "Авто: список и информационный блок следуют за веб-камерой. "
            "Если камера снизу — список и информация находятся над ней. "
            "Если камера переносится влево — автоматические блоки тоже переходят влево.\n"
            "Только внутренние области игровой рамки и рамки веб-камеры прозрачны; "
            "остальной фон оверлея непрозрачный. В OBS разместите Browser Source "
            "с этим оверлеем выше источника игры и веб-камеры."
        )
        overlay_help.setWordWrap(True)
        overlay_help.setProperty("muted", True)
        overlay_form.addRow("", overlay_help)

        layout.addLayout(overlay_form)

        typography_heading = QLabel("Шрифты оверлея")
        typography_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        layout.addWidget(typography_heading)

        typography_help = QLabel(
            "Для каждого элемента можно отдельно выбрать семейство шрифта, "
            "размер и цвет. Настройки применяются после сохранения параметров."
        )
        typography_help.setWordWrap(True)
        typography_help.setProperty("muted", True)
        layout.addWidget(typography_help)

        self.typography_controls: dict[str, tuple[QFontComboBox, QSpinBox, QPushButton]] = {}
        self.typography_row_widgets: dict[str, tuple[QLabel, QWidget]] = {}
        self.typography_control_groups: dict[str, tuple[QWidget, QWidget]] = {}
        typography_layout = QVBoxLayout()
        typography_layout.setSpacing(10)

        self._add_typography_row(
            typography_layout, "title", "Название текущей игры", 30, "#FFFFFF"
        )
        self._add_typography_row(
            typography_layout, "top1", "Top-1", 17, "#FFFFFF"
        )
        self._add_typography_row(
            typography_layout, "top2", "Top-2", 17, "#FFFFFF"
        )
        self._add_typography_row(
            typography_layout, "top3", "Top-3", 17, "#FFFFFF"
        )
        self._add_typography_row(
            typography_layout, "list", "Прокручиваемый список", 17, "#FFFFFF"
        )
        self._add_typography_row(
            typography_layout, "info", "Доп. информация", 17, "#FFFFFF"
        )
        layout.addLayout(typography_layout)

        save = QPushButton("Сохранить параметры стрима")
        save.setProperty("primary", True)
        save.clicked.connect(self.save)
        layout.addWidget(save, 0, Qt.AlignLeft)

        line = QFrame()
        line.setProperty("line", True)
        layout.addWidget(line)

        api_heading = QLabel("Локальный API")
        api_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        layout.addWidget(api_heading)

        self.api_label = QLabel()
        self.api_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.api_label.setProperty("muted", True)
        layout.addWidget(self.api_label)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        copy = QPushButton("Копировать URL оверлея")
        copy.setToolTip(
            "Скопировать адрес, который нужно добавить в OBS как источник «Браузер»"
        )
        copy.clicked.connect(
            lambda: QApplication.clipboard().setText(
                f"{self.api.base_url}/overlay"
            )
        )

        overlay_btn = QPushButton("Открыть предпросмотр оверлея")
        overlay_btn.setToolTip(
            "Открыть предварительный просмотр оверлея в браузере"
        )
        overlay_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl(f"{self.api.base_url}/overlay?preview=1")
            )
        )

        health = QPushButton("Проверить API")
        health.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f"{self.api.base_url}/health")))
        data_btn = QPushButton("Открыть JSON OBS")
        data_btn.setToolTip(
            "Открыть диагностические данные OBS в читаемом виде. "
            "Это не графический оверлей."
        )
        data_btn.clicked.connect(self._open_obs_json)
        btns.addWidget(copy)
        btns.addWidget(overlay_btn)
        btns.addWidget(health)
        btns.addWidget(data_btn)
        btns.addStretch()
        layout.addLayout(btns)

        # Browser applications may reuse an already-open diagnostics tab when
        # asked to navigate to the exact same URL.  A unique query value makes
        # every operator click perform a fresh /api/data request, while the
        # server itself remains no-store and recalculates media availability.
        self._obs_json_open_counter = 0

        list_btns = QHBoxLayout()
        list_btns.setSpacing(8)
        copy_list = QPushButton("Копировать URL списка")
        copy_list.setToolTip(
            "Скопировать отдельный URL списка игр для второго источника «Браузер» в OBS"
        )
        copy_list.clicked.connect(self.copy_list_overlay_url)
        open_list = QPushButton("Открыть предпросмотр списка")
        open_list.setToolTip(
            "Открыть отдельный OBS-оверлей, содержащий только Top-3 и прокручиваемый список"
        )
        open_list.clicked.connect(self.open_list_overlay_preview)
        list_btns.addWidget(copy_list)
        list_btns.addWidget(open_list)
        list_btns.addStretch()
        layout.addLayout(list_btns)

        timer_line = QFrame()
        timer_line.setProperty("line", True)
        layout.addWidget(timer_line)
        timer_heading = QLabel("Виджет таймера аукциона")
        timer_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        layout.addWidget(timer_heading)

        timer_form = QFormLayout()
        self.timer_overlay_form = timer_form
        timer_form.setVerticalSpacing(10)
        timer_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        timer_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.timer_overlay_font = ScrollSafeFontComboBox()
        self.timer_overlay_font.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        timer_form.addRow("Шрифт:", self.timer_overlay_font)

        self.timer_overlay_font_size = ScrollSafeSpinBox()
        self.timer_overlay_font_size.setRange(8, 300)
        self.timer_overlay_font_size.setSuffix(" px")
        self.timer_overlay_font_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.timer_overlay_font_size_control = make_wide_step_control(
            self.timer_overlay_font_size,
            up_tooltip="Увеличить размер таймера",
            down_tooltip="Уменьшить размер таймера",
        )
        timer_form.addRow("Размер:", self.timer_overlay_font_size_control)

        timer_text_color_row = QWidget()
        timer_text_color_layout = QHBoxLayout(timer_text_color_row)
        timer_text_color_layout.setContentsMargins(0, 0, 0, 0)
        timer_text_color_layout.setSpacing(8)
        self.timer_overlay_font_color_btn = QPushButton()
        self.timer_overlay_font_color_btn.clicked.connect(self._choose_timer_font_color)
        self.timer_overlay_font_color_pick_btn = make_screen_color_picker_button()
        self.timer_overlay_font_color_pick_btn.setToolTip("Выбрать цвет таймера с экрана")
        self.timer_overlay_font_color_pick_btn.clicked.connect(
            lambda: self._pick_color_from_screen(self.timer_overlay_font_color_btn)
        )
        timer_text_color_layout.addWidget(self.timer_overlay_font_color_btn)
        timer_text_color_layout.addWidget(self.timer_overlay_font_color_pick_btn)
        timer_text_color_layout.addStretch()
        timer_form.addRow("Цвет текста:", timer_text_color_row)

        timer_background_row = QWidget()
        timer_background_layout = QHBoxLayout(timer_background_row)
        timer_background_layout.setContentsMargins(0, 0, 0, 0)
        timer_background_layout.setSpacing(12)
        self.timer_background_transparent = QRadioButton("Прозрачный")
        self.timer_background_color_mode = QRadioButton("Цвет")
        self.timer_background_transparent.toggled.connect(self._update_timer_background_enabled_state)
        self.timer_background_color_mode.toggled.connect(self._update_timer_background_enabled_state)
        timer_background_layout.addWidget(self.timer_background_transparent)
        timer_background_layout.addWidget(self.timer_background_color_mode)
        timer_background_layout.addStretch()
        timer_form.addRow("Фон:", timer_background_row)

        timer_bg_color_row = QWidget()
        timer_bg_color_layout = QHBoxLayout(timer_bg_color_row)
        timer_bg_color_layout.setContentsMargins(0, 0, 0, 0)
        timer_bg_color_layout.setSpacing(8)
        self.timer_background_color_btn = QPushButton()
        self.timer_background_color_btn.clicked.connect(self._choose_timer_background_color)
        self.timer_background_color_pick_btn = make_screen_color_picker_button()
        self.timer_background_color_pick_btn.setToolTip("Выбрать цвет фона таймера с экрана")
        self.timer_background_color_pick_btn.clicked.connect(
            lambda: self._pick_color_from_screen(self.timer_background_color_btn)
        )
        timer_bg_color_layout.addWidget(self.timer_background_color_btn)
        timer_bg_color_layout.addWidget(self.timer_background_color_pick_btn)
        timer_bg_color_layout.addStretch()
        self.timer_background_color_row = timer_bg_color_row
        timer_form.addRow("Цвет фона:", self.timer_background_color_row)
        layout.addLayout(timer_form)

        timer_actions = QHBoxLayout()
        timer_actions.setSpacing(8)
        save_timer = QPushButton("Сохранить виджет таймера")
        save_timer.setProperty("primary", True)
        save_timer.clicked.connect(self._save_timer_overlay_settings)
        copy_timer = QPushButton("Копировать URL таймера")
        copy_timer.clicked.connect(
            lambda: QApplication.clipboard().setText(f"{self.api.base_url}/timer-overlay")
        )
        open_timer = QPushButton("Открыть предпросмотр таймера")
        open_timer.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(f"{self.api.base_url}/timer-overlay?preview=1"))
        )
        timer_actions.addWidget(save_timer)
        timer_actions.addWidget(copy_timer)
        timer_actions.addWidget(open_timer)
        timer_actions.addStretch()
        layout.addLayout(timer_actions)

        music_line = QFrame()
        music_line.setProperty("line", True)
        layout.addWidget(music_line)
        music_heading = QLabel("Виджет музыкального плеера")
        music_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        layout.addWidget(music_heading)

        music_form = QFormLayout()
        music_form.setVerticalSpacing(10)
        music_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        music_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.music_player_overlay_form = music_form

        self.music_player_overlay_font = ScrollSafeFontComboBox()
        self.music_player_overlay_font.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        music_form.addRow("Шрифт:", self.music_player_overlay_font)

        self.music_player_overlay_font_size = ScrollSafeSpinBox()
        self.music_player_overlay_font_size.setRange(8, 200)
        self.music_player_overlay_font_size.setSuffix(" px")
        self.music_player_overlay_font_size_control = make_wide_step_control(
            self.music_player_overlay_font_size,
            up_tooltip="Увеличить размер текста плеера",
            down_tooltip="Уменьшить размер текста плеера",
        )
        music_form.addRow("Размер:", self.music_player_overlay_font_size_control)

        def music_color_row(button_attr: str, picker_attr: str, tooltip: str):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            button = QPushButton()
            picker = make_screen_color_picker_button()
            picker.setToolTip(tooltip)
            setattr(self, button_attr, button)
            setattr(self, picker_attr, picker)
            row_layout.addWidget(button)
            row_layout.addWidget(picker)
            row_layout.addStretch()
            return row, button, picker

        row, self.music_player_overlay_text_color_btn, self.music_player_overlay_text_color_pick_btn = music_color_row(
            "music_player_overlay_text_color_btn",
            "music_player_overlay_text_color_pick_btn",
            "Выбрать цвет текста плеера с экрана",
        )
        self.music_player_overlay_text_color_btn.clicked.connect(
            lambda: self._choose_music_overlay_color(
                self.music_player_overlay_text_color_btn,
                "Выберите цвет текста плеера",
                MUSIC_PLAYER_OVERLAY_TEXT_COLOR_DEFAULT,
            )
        )
        self.music_player_overlay_text_color_pick_btn.clicked.connect(
            lambda: self._pick_color_from_screen(self.music_player_overlay_text_color_btn)
        )
        music_form.addRow("Цвет текста:", row)

        bg_mode_row = QWidget()
        bg_mode_layout = QHBoxLayout(bg_mode_row)
        bg_mode_layout.setContentsMargins(0, 0, 0, 0)
        bg_mode_layout.setSpacing(12)
        self.music_player_background_transparent = QRadioButton("Прозрачный")
        self.music_player_background_color_mode = QRadioButton("Цвет")
        self.music_player_background_transparent.toggled.connect(
            self._update_music_player_overlay_enabled_state
        )
        self.music_player_background_color_mode.toggled.connect(
            self._update_music_player_overlay_enabled_state
        )
        bg_mode_layout.addWidget(self.music_player_background_transparent)
        bg_mode_layout.addWidget(self.music_player_background_color_mode)
        bg_mode_layout.addStretch()
        music_form.addRow("Фон:", bg_mode_row)

        row, self.music_player_background_color_btn, self.music_player_background_color_pick_btn = music_color_row(
            "music_player_background_color_btn",
            "music_player_background_color_pick_btn",
            "Выбрать цвет фона плеера с экрана",
        )
        self.music_player_background_color_btn.clicked.connect(
            lambda: self._choose_music_overlay_color(
                self.music_player_background_color_btn,
                "Выберите цвет фона плеера",
                MUSIC_PLAYER_OVERLAY_BACKGROUND_COLOR_DEFAULT,
            )
        )
        self.music_player_background_color_pick_btn.clicked.connect(
            lambda: self._pick_color_from_screen(self.music_player_background_color_btn)
        )
        self.music_player_background_color_row = row
        music_form.addRow("Цвет фона:", self.music_player_background_color_row)

        row, self.music_player_frame_color_btn, self.music_player_frame_color_pick_btn = music_color_row(
            "music_player_frame_color_btn",
            "music_player_frame_color_pick_btn",
            "Выбрать цвет рамок плеера с экрана",
        )
        self.music_player_frame_color_btn.clicked.connect(
            lambda: self._choose_music_overlay_color(
                self.music_player_frame_color_btn,
                "Выберите цвет рамок плеера",
                MUSIC_PLAYER_OVERLAY_FRAME_COLOR_DEFAULT,
            )
        )
        self.music_player_frame_color_pick_btn.clicked.connect(
            lambda: self._pick_color_from_screen(self.music_player_frame_color_btn)
        )
        self.music_player_frame_color_row = row
        music_form.addRow("Цвет рамки:", self.music_player_frame_color_row)

        row, self.music_player_spectrum_color_btn, self.music_player_spectrum_color_pick_btn = music_color_row(
            "music_player_spectrum_color_btn",
            "music_player_spectrum_color_pick_btn",
            "Выбрать цвет спектра с экрана",
        )
        self.music_player_spectrum_color_btn.clicked.connect(
            lambda: self._choose_music_overlay_color(
                self.music_player_spectrum_color_btn,
                "Выберите цвет спектра",
                MUSIC_PLAYER_OVERLAY_SPECTRUM_COLOR_DEFAULT,
            )
        )
        self.music_player_spectrum_color_pick_btn.clicked.connect(
            lambda: self._pick_color_from_screen(self.music_player_spectrum_color_btn)
        )
        self.music_player_spectrum_color_row = row
        music_form.addRow("Цвет спектра:", self.music_player_spectrum_color_row)

        self.music_player_auto_colors = QCheckBox("Подбирать цвета по обложке")
        self.music_player_auto_colors.toggled.connect(
            self._update_music_player_overlay_enabled_state
        )
        music_form.addRow("", self.music_player_auto_colors)

        self.music_player_show_mode = ScrollSafeComboBox()
        self.music_player_show_mode.addItem("Не показывать", MUSIC_PLAYER_OVERLAY_SHOW_HIDDEN)
        self.music_player_show_mode.addItem("При смене трека", MUSIC_PLAYER_OVERLAY_SHOW_TRACK_CHANGE)
        self.music_player_show_mode.addItem("Показывать постоянно", MUSIC_PLAYER_OVERLAY_SHOW_ALWAYS)
        self.music_player_show_mode.currentIndexChanged.connect(
            self._update_music_player_overlay_enabled_state
        )
        music_form.addRow("Показ плашки:", self.music_player_show_mode)

        self.music_player_duration_seconds = ScrollSafeSpinBox()
        self.music_player_duration_seconds.setRange(1, 120)
        self.music_player_duration_seconds.setSuffix(" сек.")
        self.music_player_duration_seconds_control = make_wide_step_control(
            self.music_player_duration_seconds,
            up_tooltip="Увеличить время показа",
            down_tooltip="Уменьшить время показа",
        )
        music_form.addRow("Время показа:", self.music_player_duration_seconds_control)

        self.music_player_animation = ScrollSafeComboBox()
        self.music_player_animation.addItem("Проявление", MUSIC_PLAYER_OVERLAY_ANIMATION_FADE)
        self.music_player_animation.addItem("Выезд", MUSIC_PLAYER_OVERLAY_ANIMATION_SLIDE)
        self.music_player_animation.currentIndexChanged.connect(
            self._update_music_player_overlay_enabled_state
        )
        music_form.addRow("Анимация:", self.music_player_animation)

        self.music_player_direction = ScrollSafeComboBox()
        self.music_player_direction.addItem("Слева", "left")
        self.music_player_direction.addItem("Справа", "right")
        self.music_player_direction.addItem("Сверху", "top")
        self.music_player_direction.addItem("Снизу", "bottom")
        music_form.addRow("Направление:", self.music_player_direction)

        layout.addLayout(music_form)

        music_actions = QHBoxLayout()
        music_actions.setSpacing(8)
        save_music = QPushButton("Сохранить виджет плеера")
        save_music.setProperty("primary", True)
        save_music.clicked.connect(self._save_music_player_overlay_settings)
        copy_music = QPushButton("Копировать URL плеера")
        copy_music.clicked.connect(self.copy_music_player_overlay_url)
        open_music = QPushButton("Открыть предпросмотр")
        open_music.clicked.connect(self.open_music_player_overlay_preview)
        music_actions.addWidget(save_music)
        music_actions.addWidget(copy_music)
        music_actions.addWidget(open_music)
        music_actions.addStretch()
        layout.addLayout(music_actions)

        auction_lots_line = QFrame()
        auction_lots_line.setProperty("line", True)
        layout.addWidget(auction_lots_line)
        auction_lots_heading = QLabel("Виджет списка лотов аукциона")
        auction_lots_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        layout.addWidget(auction_lots_heading)

        auction_lots_form = QFormLayout()
        self.auction_lots_overlay_form = auction_lots_form
        auction_lots_form.setVerticalSpacing(10)
        auction_lots_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        auction_lots_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.auction_lots_overlay_font = ScrollSafeFontComboBox()
        self.auction_lots_overlay_font.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        auction_lots_form.addRow("Шрифт:", self.auction_lots_overlay_font)

        self.auction_lots_overlay_font_size = ScrollSafeSpinBox()
        self.auction_lots_overlay_font_size.setRange(8, 160)
        self.auction_lots_overlay_font_size.setSuffix(" px")
        self.auction_lots_overlay_font_size_control = make_wide_step_control(
            self.auction_lots_overlay_font_size,
            up_tooltip="Увеличить размер текста списка лотов",
            down_tooltip="Уменьшить размер текста списка лотов",
        )
        auction_lots_form.addRow("Размер:", self.auction_lots_overlay_font_size_control)

        color_row = QWidget()
        color_layout = QHBoxLayout(color_row)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(8)
        self.auction_lots_overlay_font_color_btn = QPushButton()
        self.auction_lots_overlay_font_color_btn.clicked.connect(self._choose_auction_lots_font_color)
        self.auction_lots_overlay_font_color_pick_btn = make_screen_color_picker_button()
        self.auction_lots_overlay_font_color_pick_btn.clicked.connect(
            lambda: self._pick_color_from_screen(self.auction_lots_overlay_font_color_btn)
        )
        color_layout.addWidget(self.auction_lots_overlay_font_color_btn)
        color_layout.addWidget(self.auction_lots_overlay_font_color_pick_btn)
        color_layout.addStretch()
        auction_lots_form.addRow("Цвет текста:", color_row)

        bg_mode_row = QWidget()
        bg_mode_layout = QHBoxLayout(bg_mode_row)
        bg_mode_layout.setContentsMargins(0, 0, 0, 0)
        bg_mode_layout.setSpacing(12)
        self.auction_lots_background_transparent = QRadioButton("Прозрачный")
        self.auction_lots_background_color_mode = QRadioButton("Цвет")
        self.auction_lots_background_media_mode = QRadioButton("Свой")
        for control in (
            self.auction_lots_background_transparent,
            self.auction_lots_background_color_mode,
            self.auction_lots_background_media_mode,
        ):
            control.toggled.connect(self._update_auction_lots_background_enabled_state)
            bg_mode_layout.addWidget(control)
        bg_mode_layout.addStretch()
        auction_lots_form.addRow("Фон:", bg_mode_row)

        bg_color_row = QWidget()
        bg_color_layout = QHBoxLayout(bg_color_row)
        bg_color_layout.setContentsMargins(0, 0, 0, 0)
        bg_color_layout.setSpacing(8)
        self.auction_lots_background_color_btn = QPushButton()
        self.auction_lots_background_color_btn.clicked.connect(self._choose_auction_lots_background_color)
        self.auction_lots_background_color_pick_btn = make_screen_color_picker_button()
        self.auction_lots_background_color_pick_btn.clicked.connect(
            lambda: self._pick_color_from_screen(self.auction_lots_background_color_btn)
        )
        bg_color_layout.addWidget(self.auction_lots_background_color_btn)
        bg_color_layout.addWidget(self.auction_lots_background_color_pick_btn)
        bg_color_layout.addStretch()
        self.auction_lots_background_color_row = bg_color_row
        auction_lots_form.addRow("Цвет фона:", self.auction_lots_background_color_row)

        media_row = QWidget()
        media_layout = QHBoxLayout(media_row)
        media_layout.setContentsMargins(0, 0, 0, 0)
        media_layout.setSpacing(8)
        self.auction_lots_background_combo = ScrollSafeComboBox()
        self.auction_lots_background_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.auction_lots_choose_background_btn = QPushButton("Добавить фон…")
        self.auction_lots_choose_background_btn.clicked.connect(self._import_auction_lots_background_media)
        media_layout.addWidget(self.auction_lots_background_combo, 1)
        media_layout.addWidget(self.auction_lots_choose_background_btn)
        self.auction_lots_background_media_row = media_row
        auction_lots_form.addRow("Свой фон:", self.auction_lots_background_media_row)
        layout.addLayout(auction_lots_form)

        auction_lots_actions = QHBoxLayout()
        auction_lots_actions.setSpacing(8)
        save_auction_lots = QPushButton("Сохранить виджет списка лотов")
        save_auction_lots.setProperty("primary", True)
        save_auction_lots.clicked.connect(self._save_auction_lots_overlay_settings)
        copy_auction_lots = QPushButton("Копировать URL списка лотов")
        copy_auction_lots.clicked.connect(self.copy_auction_lots_overlay_url)
        open_auction_lots = QPushButton("Открыть предпросмотр списка лотов")
        open_auction_lots.clicked.connect(self.open_auction_lots_overlay_preview)
        auction_lots_actions.addWidget(save_auction_lots)
        auction_lots_actions.addWidget(copy_auction_lots)
        auction_lots_actions.addWidget(open_auction_lots)
        auction_lots_actions.addStretch()
        layout.addLayout(auction_lots_actions)

        rules_line = QFrame()
        rules_line.setProperty("line", True)
        layout.addWidget(rules_line)
        rules_heading = QLabel("Виджет правил аукциона")
        rules_heading.setStyleSheet("font-size: 13pt; font-weight: 650;")
        layout.addWidget(rules_heading)

        rules_form = QFormLayout()
        self.rules_overlay_form = rules_form
        rules_form.setVerticalSpacing(10)
        rules_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        rules_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.rules_overlay_visible = QCheckBox("Показывать правила в OBS")
        rules_form.addRow("Видимость:", self.rules_overlay_visible)
        self.rules_overlay_autoscroll = QCheckBox("Автопрокрутка")
        rules_form.addRow("Прокрутка:", self.rules_overlay_autoscroll)

        background_row = QWidget()
        background_layout = QHBoxLayout(background_row)
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_layout.setSpacing(12)
        self.rules_background_transparent = QRadioButton("Прозрачный")
        self.rules_background_color_mode = QRadioButton("Цвет")
        self.rules_background_transparent.toggled.connect(
            self._update_rules_background_enabled_state
        )
        self.rules_background_color_mode.toggled.connect(
            self._update_rules_background_enabled_state
        )
        background_layout.addWidget(self.rules_background_transparent)
        background_layout.addWidget(self.rules_background_color_mode)
        background_layout.addStretch()
        rules_form.addRow("Фон:", background_row)

        rules_color_row = QWidget()
        rules_color_layout = QHBoxLayout(rules_color_row)
        rules_color_layout.setContentsMargins(0, 0, 0, 0)
        rules_color_layout.setSpacing(8)
        self.rules_background_color_btn = QPushButton()
        self.rules_background_color_btn.clicked.connect(self._choose_rules_background_color)
        self.rules_background_color_pick_btn = make_screen_color_picker_button()
        self.rules_background_color_pick_btn.setToolTip(
            "Выбрать цвет фона непосредственно с экрана"
        )
        self.rules_background_color_pick_btn.clicked.connect(
            lambda: self._pick_color_from_screen(self.rules_background_color_btn)
        )
        rules_color_layout.addWidget(self.rules_background_color_btn)
        rules_color_layout.addWidget(self.rules_background_color_pick_btn)
        rules_color_layout.addStretch()
        self.rules_background_color_row = rules_color_row
        rules_form.addRow("Цвет фона:", self.rules_background_color_row)

        self.rules_background_opacity = ScrollSafeSpinBox()
        self.rules_background_opacity.setRange(0, 100)
        self.rules_background_opacity.setSuffix(" %")
        self.rules_background_opacity.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.rules_background_opacity_control = make_wide_step_control(
            self.rules_background_opacity,
            up_tooltip="Увеличить непрозрачность",
            down_tooltip="Уменьшить непрозрачность",
        )
        rules_form.addRow("Непрозрачность:", self.rules_background_opacity_control)

        self.rules_overlay_padding = ScrollSafeSpinBox()
        self.rules_overlay_padding.setRange(0, 200)
        self.rules_overlay_padding.setSuffix(" px")
        self.rules_overlay_padding.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.rules_overlay_padding_control = make_wide_step_control(
            self.rules_overlay_padding,
            up_tooltip="Увеличить внутренний отступ",
            down_tooltip="Уменьшить внутренний отступ",
        )
        rules_form.addRow("Внутренний отступ:", self.rules_overlay_padding_control)
        layout.addLayout(rules_form)

        rules_actions = QHBoxLayout()
        rules_actions.setSpacing(8)
        save_rules = QPushButton("Сохранить виджет правил")
        save_rules.setProperty("primary", True)
        save_rules.clicked.connect(self._save_rules_overlay_settings)
        copy_rules = QPushButton("Копировать URL правил")
        copy_rules.clicked.connect(
            lambda: QApplication.clipboard().setText(f"{self.api.base_url}/rules-overlay")
        )
        open_rules = QPushButton("Открыть предпросмотр правил")
        open_rules.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl(f"{self.api.base_url}/rules-overlay?preview=1")
            )
        )
        rules_actions.addWidget(save_rules)
        rules_actions.addWidget(copy_rules)
        rules_actions.addWidget(open_rules)
        rules_actions.addStretch()
        layout.addLayout(rules_actions)

        layout.addStretch()
        self.refresh()

    @staticmethod
    def _set_form_row_visible(
        form: QFormLayout,
        field_widget: QWidget,
        visible: bool,
    ) -> None:
        field_widget.setVisible(bool(visible))
        label = form.labelForField(field_widget)
        if label is not None:
            label.setVisible(bool(visible))

    def _update_timer_background_enabled_state(self) -> None:
        self._set_form_row_visible(
            self.timer_overlay_form,
            self.timer_background_color_row,
            self.timer_background_color_mode.isChecked(),
        )

    def _choose_timer_font_color(self) -> None:
        current = QColor(str(self.timer_overlay_font_color_btn.property("fontColor") or TIMER_OVERLAY_FONT_COLOR_DEFAULT))
        selected = QColorDialog.getColor(current, self, "Выберите цвет таймера")
        if selected.isValid():
            self._set_color_button(self.timer_overlay_font_color_btn, selected.name())

    def _choose_timer_background_color(self) -> None:
        current = QColor(str(self.timer_background_color_btn.property("fontColor") or TIMER_OVERLAY_BACKGROUND_COLOR_DEFAULT))
        selected = QColorDialog.getColor(current, self, "Выберите цвет фона таймера")
        if selected.isValid():
            self._set_color_button(self.timer_background_color_btn, selected.name())

    def _save_timer_overlay_settings(self) -> None:
        background = "color" if self.timer_background_color_mode.isChecked() else "transparent"
        self.db.set_settings_bulk({
            TIMER_OVERLAY_FONT_FAMILY_KEY: self.timer_overlay_font.currentFont().family(),
            TIMER_OVERLAY_FONT_SIZE_KEY: str(self.timer_overlay_font_size.value()),
            TIMER_OVERLAY_FONT_COLOR_KEY: str(
                self.timer_overlay_font_color_btn.property("fontColor") or TIMER_OVERLAY_FONT_COLOR_DEFAULT
            ),
            TIMER_OVERLAY_BACKGROUND_KEY: background,
            TIMER_OVERLAY_BACKGROUND_COLOR_KEY: str(
                self.timer_background_color_btn.property("fontColor") or TIMER_OVERLAY_BACKGROUND_COLOR_DEFAULT
            ),
        })
        QMessageBox.information(
            self,
            "OBS Timer",
            "Настройки виджета таймера сохранены. Открытый Browser Source обновится автоматически.",
        )

    def _choose_music_overlay_color(
        self,
        button: QPushButton,
        title: str,
        default: str,
    ) -> None:
        current = QColor(str(button.property("fontColor") or default))
        selected = QColorDialog.getColor(current, self, title)
        if selected.isValid():
            self._set_color_button(button, selected.name())

    def _set_music_player_form_row_visible(
        self,
        field_widget: QWidget,
        visible: bool,
    ) -> None:
        """Show/hide both parts of one Music Player QFormLayout row."""
        self._set_form_row_visible(
            self.music_player_overlay_form,
            field_widget,
            visible,
        )

    def _update_music_player_overlay_enabled_state(self) -> None:
        show_mode = str(self.music_player_show_mode.currentData() or "")
        animation = str(self.music_player_animation.currentData() or "")
        auto_colors = self.music_player_auto_colors.isChecked()
        background_is_color = self.music_player_background_color_mode.isChecked()

        # Manual colors that are actually overridden by artwork automation are
        # hidden, not merely disabled. Text and Spectrum stay visible because
        # D26 deliberately keeps those two colors user-controlled.
        self._set_music_player_form_row_visible(
            self.music_player_background_color_row,
            background_is_color and not auto_colors,
        )
        self._set_music_player_form_row_visible(
            self.music_player_frame_color_row,
            not auto_colors,
        )

        visual_is_enabled = show_mode != MUSIC_PLAYER_OVERLAY_SHOW_HIDDEN
        self._set_music_player_form_row_visible(
            self.music_player_duration_seconds_control,
            show_mode == MUSIC_PLAYER_OVERLAY_SHOW_TRACK_CHANGE,
        )
        self._set_music_player_form_row_visible(
            self.music_player_animation,
            visual_is_enabled,
        )
        self._set_music_player_form_row_visible(
            self.music_player_direction,
            visual_is_enabled
            and animation == MUSIC_PLAYER_OVERLAY_ANIMATION_SLIDE,
        )

    def _save_music_player_overlay_settings(self) -> None:
        background = (
            "color"
            if self.music_player_background_color_mode.isChecked()
            else "transparent"
        )
        self.db.set_settings_bulk({
            MUSIC_PLAYER_OVERLAY_FONT_FAMILY_KEY: self.music_player_overlay_font.currentFont().family(),
            MUSIC_PLAYER_OVERLAY_FONT_SIZE_KEY: str(self.music_player_overlay_font_size.value()),
            MUSIC_PLAYER_OVERLAY_TEXT_COLOR_KEY: str(
                self.music_player_overlay_text_color_btn.property("fontColor")
                or MUSIC_PLAYER_OVERLAY_TEXT_COLOR_DEFAULT
            ),
            MUSIC_PLAYER_OVERLAY_BACKGROUND_KEY: background,
            MUSIC_PLAYER_OVERLAY_BACKGROUND_COLOR_KEY: str(
                self.music_player_background_color_btn.property("fontColor")
                or MUSIC_PLAYER_OVERLAY_BACKGROUND_COLOR_DEFAULT
            ),
            MUSIC_PLAYER_OVERLAY_FRAME_COLOR_KEY: str(
                self.music_player_frame_color_btn.property("fontColor")
                or MUSIC_PLAYER_OVERLAY_FRAME_COLOR_DEFAULT
            ),
            MUSIC_PLAYER_OVERLAY_SPECTRUM_COLOR_KEY: str(
                self.music_player_spectrum_color_btn.property("fontColor")
                or MUSIC_PLAYER_OVERLAY_SPECTRUM_COLOR_DEFAULT
            ),
            MUSIC_PLAYER_OVERLAY_AUTO_COLORS_KEY: "1" if self.music_player_auto_colors.isChecked() else "0",
            MUSIC_PLAYER_OVERLAY_SHOW_MODE_KEY: str(
                self.music_player_show_mode.currentData()
                or MUSIC_PLAYER_OVERLAY_SHOW_MODE_DEFAULT
            ),
            MUSIC_PLAYER_OVERLAY_DURATION_SECONDS_KEY: str(
                self.music_player_duration_seconds.value()
            ),
            MUSIC_PLAYER_OVERLAY_ANIMATION_KEY: str(
                self.music_player_animation.currentData()
                or MUSIC_PLAYER_OVERLAY_ANIMATION_DEFAULT
            ),
            MUSIC_PLAYER_OVERLAY_DIRECTION_KEY: str(
                self.music_player_direction.currentData()
                or MUSIC_PLAYER_OVERLAY_DIRECTION_DEFAULT
            ),
        })
        QMessageBox.information(
            self,
            "OBS Music Player",
            "Настройки виджета музыкального плеера сохранены. "
            "Открытый Browser Source обновится автоматически.",
        )

    def copy_music_player_overlay_url(self) -> None:
        QApplication.clipboard().setText(
            f"{self.api.base_url}/music-player-overlay"
        )

    def open_music_player_overlay_preview(self) -> None:
        QDesktopServices.openUrl(
            QUrl(f"{self.api.base_url}/music-player-overlay?preview=1")
        )

    def _show_obs_widget_help(self) -> None:
        QMessageBox.information(
            self,
            "Как добавить виджет в OBS",
            "1. У нужного виджета нажмите «Копировать URL…».\n"
            "2. OBS → Источники → + → Браузер.\n"
            "3. Создайте новый источник «Браузер».\n"
            "4. Вставьте скопированный URL.\n"
            "5. Задайте Width / Height под нужный размер виджета.\n"
            "6. Разместите источник на сцене.\n"
            "7. При необходимости измените настройки виджета в InOneLine и сохраните их. "
            "Поддерживаемые настройки открытого Browser Source обновляются автоматически.\n\n"
            "Параметры ‘Shutdown source when not visible’ и ‘Refresh browser when scene becomes active’ "
            "не обязательны.",
        )

    def _update_auction_lots_background_enabled_state(self) -> None:
        color_enabled = self.auction_lots_background_color_mode.isChecked()
        media_enabled = self.auction_lots_background_media_mode.isChecked()
        self._set_form_row_visible(
            self.auction_lots_overlay_form,
            self.auction_lots_background_color_row,
            color_enabled,
        )
        self._set_form_row_visible(
            self.auction_lots_overlay_form,
            self.auction_lots_background_media_row,
            media_enabled,
        )
        self.auction_lots_choose_background_btn.setEnabled(
            self._background_copy_worker is None
        )

    def _choose_auction_lots_font_color(self) -> None:
        current = str(
            self.auction_lots_overlay_font_color_btn.property("fontColor")
            or AUCTION_LOTS_OVERLAY_FONT_COLOR_DEFAULT
        )
        color = QColorDialog.getColor(
            QColor(current), self, "Цвет текста списка лотов"
        )
        if color.isValid():
            self._set_color_button(
                self.auction_lots_overlay_font_color_btn,
                color.name().upper(),
            )

    def _choose_auction_lots_background_color(self) -> None:
        current = str(
            self.auction_lots_background_color_btn.property("fontColor")
            or AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_DEFAULT
        )
        color = QColorDialog.getColor(
            QColor(current), self, "Цвет фона списка лотов"
        )
        if color.isValid():
            self._set_color_button(
                self.auction_lots_background_color_btn,
                color.name().upper(),
            )

    def _save_auction_lots_overlay_settings(self) -> None:
        if self.auction_lots_background_media_mode.isChecked():
            background = "media"
        elif self.auction_lots_background_color_mode.isChecked():
            background = "color"
        else:
            background = "transparent"

        media_value = self.auction_lots_background_combo.currentData()
        media_id = (
            str(media_value)
            if str(media_value or "").isdigit()
            else ""
        )
        self.db.set_settings_bulk({
            AUCTION_LOTS_OVERLAY_FONT_FAMILY_KEY:
                self.auction_lots_overlay_font.currentFont().family(),
            AUCTION_LOTS_OVERLAY_FONT_SIZE_KEY:
                str(self.auction_lots_overlay_font_size.value()),
            AUCTION_LOTS_OVERLAY_FONT_COLOR_KEY: str(
                self.auction_lots_overlay_font_color_btn.property("fontColor")
                or AUCTION_LOTS_OVERLAY_FONT_COLOR_DEFAULT
            ),
            AUCTION_LOTS_OVERLAY_BACKGROUND_KEY: background,
            AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_KEY: str(
                self.auction_lots_background_color_btn.property("fontColor")
                or AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_DEFAULT
            ),
            AUCTION_LOTS_OVERLAY_BACKGROUND_MEDIA_ID_KEY: media_id,
        })
        QMessageBox.information(
            self,
            "OBS Auction Lots",
            "Настройки списка лотов сохранены. Открытый Browser Source обновится автоматически.",
        )

    def _update_rules_background_enabled_state(self) -> None:
        enabled = self.rules_background_color_mode.isChecked()
        self._set_form_row_visible(
            self.rules_overlay_form,
            self.rules_background_color_row,
            enabled,
        )
        self._set_form_row_visible(
            self.rules_overlay_form,
            self.rules_background_opacity_control,
            enabled,
        )

    def _choose_rules_background_color(self) -> None:
        current = QColor(str(self.rules_background_color_btn.property("fontColor") or "#000000"))
        selected = QColorDialog.getColor(current, self, "Выберите цвет фона правил")
        if selected.isValid():
            self._set_color_button(self.rules_background_color_btn, selected.name())

    def _save_rules_overlay_settings(self) -> None:
        background = "color" if self.rules_background_color_mode.isChecked() else "transparent"
        self.db.set_settings_bulk({
            RULES_OVERLAY_VISIBLE_KEY: "1" if self.rules_overlay_visible.isChecked() else "0",
            RULES_OVERLAY_AUTOSCROLL_KEY: "1" if self.rules_overlay_autoscroll.isChecked() else "0",
            RULES_OVERLAY_BACKGROUND_KEY: background,
            RULES_OVERLAY_BACKGROUND_COLOR_KEY: str(
                self.rules_background_color_btn.property("fontColor") or RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT
            ),
            RULES_OVERLAY_BACKGROUND_OPACITY_KEY: str(self.rules_background_opacity.value()),
            RULES_OVERLAY_PADDING_KEY: str(self.rules_overlay_padding.value()),
        })
        QMessageBox.information(
            self,
            "OBS Rules",
            "Настройки виджета правил сохранены. Открытый Browser Source обновится автоматически.",
        )

    def copy_list_overlay_url(self) -> None:
        QApplication.clipboard().setText(f"{self.api.base_url}/list-overlay")

    def open_list_overlay_preview(self) -> None:
        QDesktopServices.openUrl(QUrl(f"{self.api.base_url}/list-overlay"))

    def copy_auction_lots_overlay_url(self) -> None:
        QApplication.clipboard().setText(
            f"{self.api.base_url}/auction-lots-overlay"
        )

    def open_auction_lots_overlay_preview(self) -> None:
        QDesktopServices.openUrl(
            QUrl(f"{self.api.base_url}/auction-lots-overlay?preview=1")
        )

    def _open_obs_json(self):
        self._refresh_selected_background_availability()
        self._obs_json_open_counter += 1
        QDesktopServices.openUrl(
            QUrl(
                f"{self.api.base_url}/api/data?pretty=1&refresh={self._obs_json_open_counter}"
            )
        )

    @staticmethod
    def _supported_background_extensions() -> set[str]:
        return set(supported_media_extensions(MEDIA_CATEGORY_OVERLAY_BACKGROUNDS))

    def _background_assets(self):
        # One available-only category view for both overlay selectors.
        return [
            asset
            for asset in self.db.sync_managed_media_category(
                MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
            )
            if media_asset_available(self.db.path.parent, asset)
        ]

    @staticmethod
    def _background_asset_label(asset, available: bool) -> str:
        if asset.storage_mode == MEDIA_STORAGE_EXTERNAL:
            label = f"{asset.display_name} — исходный файл"
        else:
            label = asset.display_name
        return label if available else f"⚠ файл недоступен: {label}"

    def _refresh_selected_background_availability(self):
        # This category is shared by the main overlay and Auction Lots.
        self._refresh_background_library()
        self._refresh_auction_lots_background_library()

    def _refresh_background_library(self, selected_asset_id: int | str | None = None):
        if selected_asset_id is None:
            selected_asset_id = self.background_combo.currentData()
        try:
            selected_id = int(selected_asset_id) if str(selected_asset_id or "").isdigit() else None
        except (TypeError, ValueError):
            selected_id = None

        assets = self._background_assets()
        self.background_combo.blockSignals(True)
        self.background_combo.clear()
        self.background_combo.addItem("— без фоновой картинки —", "")
        for asset in assets:
            available = media_asset_available(self.db.path.parent, asset)
            self.background_combo.addItem(
                self._background_asset_label(asset, available),
                asset.id,
            )

        idx = self.background_combo.findData(selected_id) if selected_id is not None else 0
        self.background_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.background_combo.blockSignals(False)
        self._update_background_path_field()

    def _refresh_auction_lots_background_library(
        self,
        selected_asset_id: int | str | None = None,
    ) -> None:
        if selected_asset_id is None:
            selected_asset_id = self.auction_lots_background_combo.currentData()
        try:
            selected_id = (
                int(selected_asset_id)
                if str(selected_asset_id or "").isdigit()
                else None
            )
        except (TypeError, ValueError):
            selected_id = None

        assets = self._background_assets()
        self.auction_lots_background_combo.blockSignals(True)
        self.auction_lots_background_combo.clear()
        self.auction_lots_background_combo.addItem("— без фонового файла —", "")
        for asset in assets:
            available = media_asset_available(self.db.path.parent, asset)
            self.auction_lots_background_combo.addItem(
                self._background_asset_label(asset, available),
                asset.id,
            )
        idx = (
            self.auction_lots_background_combo.findData(selected_id)
            if selected_id is not None
            else 0
        )
        self.auction_lots_background_combo.setCurrentIndex(
            idx if idx >= 0 else 0
        )
        self.auction_lots_background_combo.blockSignals(False)

    def _select_imported_background(self, target: str, asset_id: int) -> None:
        if target == "auction_lots":
            self._refresh_auction_lots_background_library(asset_id)
            self._refresh_background_library()
        else:
            self._refresh_background_library(asset_id)
            self._refresh_auction_lots_background_library()

    def _selected_background_asset(self):
        raw = self.background_combo.currentData()
        if not str(raw or "").isdigit():
            return None
        asset = self.db.get_media_asset(int(raw))
        if asset is None or asset.category != MEDIA_CATEGORY_OVERLAY_BACKGROUNDS:
            return None
        return asset

    def _update_background_path_field(self, *args):
        asset = self._selected_background_asset()
        if asset is None:
            self.background_path.clear()
            self.background_status.setText("Фон не выбран")
            self.repair_background_btn.setEnabled(False)
            self.repair_background_btn.setVisible(False)
            return

        try:
            path = resolve_media_asset_path(self.db.path.parent, asset)
        except (OSError, ValueError):
            path = Path(asset.external_path or asset.managed_name)
        available = media_asset_available(self.db.path.parent, asset)
        self.background_path.setText(str(path))

        self.background_status.setText(
            "Доступен" if available else "Файл недоступен — выберите другой фон"
        )

    def _unique_background_target(self, source_name: str) -> Path:
        source_path = Path(source_name)
        stem = source_path.stem
        suffix = source_path.suffix
        existing = {p.name.casefold() for p in self.background_dir.iterdir() if p.is_file()}
        candidate = self.background_dir / source_path.name
        number = 2
        while candidate.name.casefold() in existing:
            candidate = self.background_dir / f"{stem} ({number}){suffix}"
            number += 1
        return candidate

    @staticmethod
    def _copy_background_video(source: Path, target: Path) -> Path:
        try:
            shutil.copy2(source, target)
        except Exception:
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return target

    def _background_video_copy_ready(self, target: Path):
        asset = self.db.ensure_managed_media_asset(
            MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
            target.name,
            target.name,
        )
        self._select_imported_background(
            self._background_copy_target,
            asset.id,
        )

    def _background_video_copy_failed(self, exc):
        QMessageBox.critical(
            self,
            "Ошибка копирования фона",
            f"Не удалось скопировать видео во внутреннюю библиотеку:\n{exc}",
        )

    def _background_video_copy_finished(self):
        self._background_copy_worker = None
        self.choose_background_btn.setEnabled(True)
        self.choose_background_btn.setText("Добавить фон…")
        self.auction_lots_choose_background_btn.setText("Добавить фон…")
        self._update_auction_lots_background_enabled_state()

    def _start_background_video_copy(
        self,
        source: Path,
        target: Path,
        selection_target: str = "main",
    ):
        if self._background_copy_worker is not None:
            return
        self._background_copy_target = selection_target
        self.choose_background_btn.setEnabled(False)
        self.auction_lots_choose_background_btn.setEnabled(False)
        active_button = (
            self.auction_lots_choose_background_btn
            if selection_target == "auction_lots"
            else self.choose_background_btn
        )
        active_button.setText("Копирование…")
        worker = FunctionWorker(self._copy_background_video, source, target)
        self._background_copy_worker = worker
        worker.signals.result.connect(self._background_video_copy_ready)
        worker.signals.error.connect(self._background_video_copy_failed)
        worker.signals.finished.connect(self._background_video_copy_finished)
        self.thread_pool.start(worker)

    def _choose_background_storage_mode(self, source: Path) -> str | None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Как использовать фон?")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setText(f"Выбран файл:\n{source}\n\nКак In one line должен его использовать?")
        dialog.setInformativeText(
            "«Копировать в программу» создаст управляемую копию в отдельной папке "
            "data\\overlay_backgrounds. «Использовать исходный файл» сохранит ссылку "
            "на оригинал; сам оригинал программа не изменяет и не удаляет."
        )
        copy_button = dialog.addButton(
            "Копировать в программу", QMessageBox.ButtonRole.AcceptRole
        )
        external_button = dialog.addButton(
            "Использовать исходный файл", QMessageBox.ButtonRole.ActionRole
        )
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        clicked = dialog.clickedButton()
        if clicked is copy_button:
            return MEDIA_STORAGE_MANAGED
        if clicked is external_button:
            return MEDIA_STORAGE_EXTERNAL
        return None

    def _import_background_media(self):
        self._import_background_media_for("main")

    def _import_auction_lots_background_media(self):
        self._import_background_media_for("auction_lots")

    def _import_background_media_for(self, selection_target: str):
        if self._background_copy_worker is not None:
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите фон оверлея",
            "",
            "Поддерживаемые фоны (*.png *.jpg *.jpeg *.webp *.gif *.mp4 *.webm);;"
            "Изображения (*.png *.jpg *.jpeg *.webp);;"
            "GIF (*.gif);;Видео (*.mp4 *.webm);;Все файлы (*.*)",
        )
        if not path:
            return

        source = Path(path)
        if source.suffix.lower() not in self._supported_background_extensions():
            QMessageBox.warning(
                self,
                "Неподдерживаемый формат",
                "Поддерживаются PNG, JPG, JPEG, WEBP, GIF, MP4 и WEBM.",
            )
            return
        if not source.is_file():
            QMessageBox.critical(self, "Ошибка", "Выбранный файл не найден.")
            return

        try:
            self.background_dir.mkdir(parents=True, exist_ok=True)
            # Every file chosen through the operator picker uses the same W2
            # storage decision, including video and files that already happen
            # to be inside the managed background directory.
            storage_mode = self._choose_background_storage_mode(source)
            if storage_mode is None:
                return
            if storage_mode == MEDIA_STORAGE_EXTERNAL:
                asset = self.db.register_external_media_asset(
                    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
                    source,
                )
                self._select_imported_background(selection_target, asset.id)
                return

            # Copy mode for a file already in the dedicated managed category
            # means "use this existing managed copy"; never copy a file onto
            # itself.
            if source.resolve().parent == self.background_dir.resolve():
                asset = self.db.ensure_managed_media_asset(
                    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
                    source.name,
                    source.name,
                )
                self._select_imported_background(selection_target, asset.id)
                return

            if source.suffix.lower() in {".mp4", ".webm"}:
                existing_video = next(
                    (
                        item
                        for item in self.background_dir.iterdir()
                        if item.is_file() and item.name.casefold() == source.name.casefold()
                    ),
                    None,
                )
                if existing_video is not None:
                    QMessageBox.information(
                        self,
                        "Фон уже есть",
                        f'Файл «{source.name}» уже есть в библиотеке фонов.\n'
                        "Будет выбран существующий файл.",
                    )
                    asset = self.db.ensure_managed_media_asset(
                        MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
                        existing_video.name,
                        existing_video.name,
                    )
                    self._select_imported_background(selection_target, asset.id)
                    return
                target = self.background_dir / source.name
                self._start_background_video_copy(source, target, selection_target)
                return

            target = self._unique_background_target(source.name)
            shutil.copy2(source, target)
            asset = self.db.ensure_managed_media_asset(
                MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
                target.name,
                source.name,
            )
        except (OSError, ValueError) as exc:
            QMessageBox.critical(
                self,
                "Ошибка выбора фона",
                f"Не удалось подготовить выбранный фон:\n{exc}",
            )
            return

        self._select_imported_background(selection_target, asset.id)

    def _repair_background_reference(self):
        asset = self._selected_background_asset()
        if asset is None or asset.storage_mode != MEDIA_STORAGE_EXTERNAL:
            return
        current = Path(asset.external_path) if asset.external_path else Path.home()
        start_dir = str(current.parent if current.parent.exists() else Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Переукажите исходный файл фона",
            start_dir,
            "Поддерживаемые фоны (*.png *.jpg *.jpeg *.webp *.gif *.mp4 *.webm);;"
            "Все файлы (*.*)",
        )
        if not path:
            return
        source = Path(path)
        if not source.is_file():
            QMessageBox.warning(self, "Файл недоступен", "Выбранный файл не найден.")
            return
        if source.suffix.lower() not in self._supported_background_extensions():
            QMessageBox.warning(
                self,
                "Неподдерживаемый формат",
                "Поддерживаются PNG, JPG, JPEG, WEBP, GIF, MP4 и WEBM.",
            )
            return
        try:
            repaired = self.db.update_external_media_asset(asset.id, source)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(
                self,
                "Ошибка переуказания",
                f"Не удалось обновить ссылку на файл:\n{exc}",
            )
            return
        self._refresh_background_library(repaired.id)

    def _add_typography_row(
        self,
        parent_layout: QVBoxLayout,
        key: str,
        label: str,
        default_size: int,
        default_color: str,
    ):
        # Название элемента вынесено на отдельную строку. Благодаря этому
        # настройки остаются читаемыми даже в узком окне / split-screen режиме.
        item_label = QLabel(label)
        item_label.setStyleSheet("font-weight: 600;")
        item_label.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed,
        )
        parent_layout.addWidget(item_label)

        font_combo = ScrollSafeFontComboBox()
        font_combo.setMinimumWidth(190)
        font_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        size_spin = ScrollSafeSpinBox()
        size_spin.setRange(8, 96)
        size_spin.setValue(default_size)
        size_spin.setSuffix(" px")

        # Нативные стрелки QSpinBox на некоторых темах Windows имеют маленькую
        # реальную область нажатия. Поэтому отключаем их и используем две
        # отдельные крупные кнопки с гарантированным hitbox.
        size_spin.setButtonSymbols(
            QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        size_text_width = size_spin.fontMetrics().horizontalAdvance("96 px")
        size_spin.setFixedWidth(max(140, size_text_width + 54))

        step_up_btn = QPushButton("▲")
        step_down_btn = QPushButton("▼")
        step_button_size = max(38, size_spin.sizeHint().height())
        for step_btn in (step_up_btn, step_down_btn):
            step_btn.setFixedSize(step_button_size, step_button_size)
            step_btn.setAutoRepeat(True)
            step_btn.setAutoRepeatDelay(350)
            step_btn.setAutoRepeatInterval(80)

        step_up_btn.setToolTip("Увеличить размер шрифта")
        step_down_btn.setToolTip("Уменьшить размер шрифта")
        step_up_btn.clicked.connect(size_spin.stepUp)
        step_down_btn.clicked.connect(size_spin.stepDown)

        def preferred_control_width(widget: QWidget) -> int:
            minimum_width = widget.minimumWidth()
            maximum_width = widget.maximumWidth()
            if minimum_width == maximum_width:
                return max(0, minimum_width)
            return max(
                minimum_width,
                widget.minimumSizeHint().width(),
                widget.sizeHint().width(),
            )

        def preferred_control_height(widget: QWidget) -> int:
            minimum_height = widget.minimumHeight()
            maximum_height = widget.maximumHeight()
            if minimum_height == maximum_height:
                return max(0, minimum_height)
            return max(
                minimum_height,
                widget.minimumSizeHint().height(),
                widget.sizeHint().height(),
            )

        size_label = QLabel("Размер:")
        size_label.setFixedWidth(size_label.sizeHint().width())
        size_controls_group = QWidget()
        size_controls_layout = QHBoxLayout(size_controls_group)
        size_controls_layout.setContentsMargins(0, 0, 0, 0)
        size_controls_layout.setSpacing(6)
        size_controls_layout.addWidget(size_label)
        size_controls_layout.addWidget(size_spin)
        size_controls_layout.addWidget(step_up_btn)
        size_controls_layout.addWidget(step_down_btn)
        size_controls_width = sum(
            preferred_control_width(widget)
            for widget in (size_label, size_spin, step_up_btn, step_down_btn)
        ) + size_controls_layout.spacing() * 3
        size_controls_group.setFixedSize(
            max(size_controls_layout.sizeHint().width(), size_controls_width) + 4,
            max(size_label.sizeHint().height(), size_spin.sizeHint().height(), step_button_size),
        )

        color_btn = QPushButton()
        color_text_width = color_btn.fontMetrics().horizontalAdvance("#FFFFFF")
        color_btn.setFixedWidth(max(220, color_text_width + 54))
        color_btn.setToolTip("Выбрать цвет шрифта")
        self._set_color_button(color_btn, default_color)
        color_btn.clicked.connect(
            lambda checked=False, row_key=key: self._choose_typography_color(row_key)
        )
        pipette_btn = make_screen_color_picker_button()
        pipette_btn.setToolTip(
            "Выбрать цвет непосредственно с экрана. Левый клик — принять, Escape — отмена."
        )
        pipette_btn.clicked.connect(
            lambda checked=False, button=color_btn: self._pick_color_from_screen(button)
        )

        color_label = QLabel("Цвет:")
        color_label.setFixedWidth(color_label.sizeHint().width())
        color_picker_group = QWidget()
        color_picker_layout = QHBoxLayout(color_picker_group)
        color_picker_layout.setContentsMargins(0, 0, 0, 0)
        color_picker_layout.setSpacing(6)
        color_picker_layout.addWidget(color_label)
        color_picker_layout.addWidget(color_btn)
        color_picker_layout.addWidget(pipette_btn)
        color_picker_width = sum(
            preferred_control_width(widget)
            for widget in (color_label, color_btn, pipette_btn)
        ) + color_picker_layout.spacing() * 2
        color_picker_group.setFixedSize(
            max(color_picker_layout.sizeHint().width(), color_picker_width) + 4,
            max(
                preferred_control_height(color_label),
                preferred_control_height(color_btn),
                preferred_control_height(pipette_btn),
            ),
        )

        # При переносе строки в узком окне размер и цвет переходят компактными
        # горизонтальными группами: стрелки остаются у поля, цвет не сжимается.
        row = QWidget()
        row.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        row_layout.addWidget(font_combo, 1)
        row_layout.addWidget(size_controls_group)
        row_layout.addWidget(color_picker_group)

        row.setMinimumHeight(
            max(
                font_combo.sizeHint().height(),
                size_controls_group.sizeHint().height(),
                color_picker_group.sizeHint().height(),
            )
        )

        self.typography_controls[key] = (font_combo, size_spin, color_btn)
        self.typography_row_widgets[key] = (item_label, row)
        self.typography_control_groups[key] = (
            size_controls_group,
            color_picker_group,
        )
        parent_layout.addWidget(row)

    @staticmethod
    def _set_color_button(button: QPushButton, color_text: str):
        color = QColor(color_text)
        if not color.isValid():
            color = QColor("#FFFFFF")
        value = color.name().upper()
        button.setProperty("fontColor", value)
        button.setText(value)

        # Контрастная подпись на самой кнопке выбора цвета.
        luminance = (
            0.299 * color.red()
            + 0.587 * color.green()
            + 0.114 * color.blue()
        )
        text_color = "#111111" if luminance > 165 else "#FFFFFF"
        button.setStyleSheet(
            f"background: {value}; color: {text_color}; "
            "border: 1px solid #60666c; font-weight: 600;"
        )

    def _pick_color_from_screen(self, button: QPushButton):
        selected = pick_screen_color(self)
        if selected is not None and selected.isValid():
            self._set_color_button(button, selected.name())

    def _choose_frame_color(self, key: str):
        button = self.frame_color_buttons.get(key)
        if button is None:
            return
        current = QColor(
            str(button.property("fontColor") or "#FFFFFF")
        )
        selected = QColorDialog.getColor(
            current,
            self,
            "Выберите цвет светящегося контура",
        )
        if selected.isValid():
            self._set_color_button(button, selected.name())

    def _choose_typography_color(self, key: str):
        controls = self.typography_controls.get(key)
        if not controls:
            return
        button = controls[2]
        current = QColor(str(button.property("fontColor") or "#FFFFFF"))
        selected = QColorDialog.getColor(
            current,
            self,
            "Выберите цвет шрифта",
        )
        if selected.isValid():
            self._set_color_button(button, selected.name())

    def _load_typography_settings(self, settings: dict[str, str] | None = None):
        settings = settings if settings is not None else self.db.get_settings()
        defaults = {
            "title": ("Segoe UI", 30, "#FFFFFF"),
            "top1": ("Segoe UI", 17, "#FFFFFF"),
            "top2": ("Segoe UI", 17, "#FFFFFF"),
            "top3": ("Segoe UI", 17, "#FFFFFF"),
            "list": ("Segoe UI", 17, "#FFFFFF"),
            "info": ("Segoe UI", 17, "#FFFFFF"),
        }
        for key, (default_family, default_size, default_color) in defaults.items():
            font_combo, size_spin, color_btn = self.typography_controls[key]
            family = settings.get(
                f"overlay_font_{key}_family", default_family
            )
            font_combo.setCurrentFont(QFont(family))

            try:
                size = int(settings.get(
                    f"overlay_font_{key}_size", str(default_size)
                ))
            except (TypeError, ValueError):
                size = default_size
            size_spin.setValue(max(size_spin.minimum(), min(size_spin.maximum(), size)))

            color = settings.get(
                f"overlay_font_{key}_color", default_color
            )
            self._set_color_button(color_btn, color)

    def _collect_typography_settings(self) -> dict[str, str]:
        values: dict[str, str] = {}
        for key, (font_combo, size_spin, color_btn) in self.typography_controls.items():
            values[f"overlay_font_{key}_family"] = font_combo.currentFont().family()
            values[f"overlay_font_{key}_size"] = str(size_spin.value())
            values[f"overlay_font_{key}_color"] = str(
                color_btn.property("fontColor") or "#FFFFFF"
            )
        return values

    def _update_info_enabled_state(self):
        enabled = self.info_enabled.isChecked()
        self.info_field.setEnabled(enabled)
        self.info_field.setToolTip(
            ""
            if enabled
            else "Информационный блок отключён. Сохранённый текст не удаляется."
        )
        self._update_main_overlay_conditional_visibility()

    def _update_main_overlay_conditional_visibility(self, *_args) -> None:
        if not hasattr(self, "overlay_form"):
            return
        webcam_enabled = bool(self.webcam_enabled.isChecked())
        list_enabled = bool(self.overlay_list_enabled.isChecked())
        info_enabled = bool(self.info_enabled.isChecked())

        # Keep the enable/disable switch itself visible. Only controls that
        # have no meaning while that block is disabled disappear.
        if hasattr(self, "webcam_position"):
            self.webcam_position.setVisible(webcam_enabled)
        if hasattr(self, "overlay_list_side"):
            self.overlay_list_side.setVisible(list_enabled)
        if hasattr(self, "info_position"):
            self._set_form_row_visible(
                self.overlay_form,
                self.info_position,
                info_enabled,
            )

        if hasattr(self, "frame_color_row_widgets"):
            for key, visible in (
                ("webcam", webcam_enabled),
                ("list", list_enabled),
                ("info", info_enabled),
            ):
                row = self.frame_color_row_widgets.get(key)
                if row is not None:
                    self._set_form_row_visible(self.overlay_form, row, visible)

        if hasattr(self, "typography_row_widgets"):
            for key in ("top1", "top2", "top3", "list"):
                pair = self.typography_row_widgets.get(key)
                if pair is not None:
                    pair[0].setVisible(list_enabled)
                    pair[1].setVisible(list_enabled)
            pair = self.typography_row_widgets.get("info")
            if pair is not None:
                pair[0].setVisible(info_enabled)
                pair[1].setVisible(info_enabled)

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, value: str, fallback: int = 0):
        idx = combo.findData(value)
        combo.setCurrentIndex(idx if idx >= 0 else fallback)

    def refresh(self):
        # All stream/overlay settings are read in one transaction. This keeps
        # tab switches and OBS configuration refreshes cheap even as the number
        # of appearance options grows.
        settings = self.db.get_settings()
        setting = settings.get

        current = setting("stream_current_game_id", "")
        self.game_combo.blockSignals(True)
        self.game_combo.clear()
        self.game_combo.addItem("— автоматически: первая ПРОХОДИТСЯ —", "")
        for game in self.db.list_games():
            self.game_combo.addItem(game.title, str(game.id))
        idx = self.game_combo.findData(current)
        self.game_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.game_combo.blockSignals(False)

        self.info_field.setText(setting("stream_info", ""))

        info_enabled = setting("stream_info_enabled", "1") == "1"
        self.info_enabled.blockSignals(True)
        self.info_enabled.setChecked(info_enabled)
        self.info_enabled.blockSignals(False)
        self._update_info_enabled_state()

        fmt = setting("stream_format", "16:9")
        idx = self.format_combo.findText(fmt)
        self.format_combo.setCurrentIndex(idx if idx >= 0 else 0)

        background_media_id = setting("overlay_background_media_id", "")
        if not background_media_id:
            # Migration 16 normally populates this.  Keep a defensive legacy
            # adoption path for partially upgraded/copied settings databases.
            legacy_file = setting("overlay_background_file", "")
            if (
                legacy_file
                and Path(legacy_file).name == legacy_file
                and (self.background_dir / legacy_file).is_file()
            ):
                try:
                    legacy_asset = self.db.ensure_managed_media_asset(
                        MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
                        legacy_file,
                        legacy_file,
                    )
                except ValueError:
                    legacy_asset = None
                if legacy_asset is not None:
                    background_media_id = str(legacy_asset.id)
        self._refresh_background_library(background_media_id)
        if background_media_id and not self.background_combo.currentData():
            self.db.set_settings_bulk({
                "overlay_background_media_id": "",
                "overlay_background_file": "",
            })
        self._set_combo_by_data(
            self.background_mode,
            setting("overlay_background_mode", "stretch"),
        )

        webcam_enabled = setting("overlay_webcam_enabled", "1") == "1"
        self.webcam_enabled.setChecked(webcam_enabled)
        self._set_combo_by_data(
            self.webcam_position,
            setting("overlay_webcam_position", "top_right"),
        )

        list_enabled = setting("overlay_list_enabled", "1") == "1"
        self.overlay_list_enabled.setChecked(list_enabled)
        self._set_combo_by_data(
            self.overlay_list_side,
            setting("overlay_list_side", "auto"),
        )
        self._set_combo_by_data(
            self.info_position,
            setting("overlay_info_position", "auto"),
        )

        legacy_frame_color = setting("overlay_frame_color", "#FFFFFF")
        for color_key, color_btn in self.frame_color_buttons.items():
            self._set_color_button(
                color_btn,
                setting(
                    f"overlay_frame_{color_key}_color",
                    legacy_frame_color,
                ),
            )
        self._update_info_enabled_state()
        self._load_typography_settings(settings)
        self._update_main_overlay_conditional_visibility()

        self.timer_overlay_font.setCurrentFont(QFont(
            setting(TIMER_OVERLAY_FONT_FAMILY_KEY, TIMER_OVERLAY_FONT_FAMILY_DEFAULT)
        ))
        try:
            timer_font_size = int(setting(
                TIMER_OVERLAY_FONT_SIZE_KEY, str(TIMER_OVERLAY_FONT_SIZE_DEFAULT)
            ))
        except ValueError:
            timer_font_size = TIMER_OVERLAY_FONT_SIZE_DEFAULT
        self.timer_overlay_font_size.setValue(max(8, min(300, timer_font_size)))
        self._set_color_button(
            self.timer_overlay_font_color_btn,
            setting(TIMER_OVERLAY_FONT_COLOR_KEY, TIMER_OVERLAY_FONT_COLOR_DEFAULT),
        )
        timer_background = setting(TIMER_OVERLAY_BACKGROUND_KEY, TIMER_OVERLAY_BACKGROUND_DEFAULT)
        self.timer_background_color_mode.setChecked(timer_background == "color")
        self.timer_background_transparent.setChecked(timer_background != "color")
        self._set_color_button(
            self.timer_background_color_btn,
            setting(TIMER_OVERLAY_BACKGROUND_COLOR_KEY, TIMER_OVERLAY_BACKGROUND_COLOR_DEFAULT),
        )
        self._update_timer_background_enabled_state()

        self.music_player_overlay_font.setCurrentFont(QFont(
            setting(
                MUSIC_PLAYER_OVERLAY_FONT_FAMILY_KEY,
                MUSIC_PLAYER_OVERLAY_FONT_FAMILY_DEFAULT,
            )
        ))
        try:
            music_font_size = int(setting(
                MUSIC_PLAYER_OVERLAY_FONT_SIZE_KEY,
                str(MUSIC_PLAYER_OVERLAY_FONT_SIZE_DEFAULT),
            ))
        except ValueError:
            music_font_size = MUSIC_PLAYER_OVERLAY_FONT_SIZE_DEFAULT
        self.music_player_overlay_font_size.setValue(
            max(8, min(200, music_font_size))
        )
        self._set_color_button(
            self.music_player_overlay_text_color_btn,
            setting(
                MUSIC_PLAYER_OVERLAY_TEXT_COLOR_KEY,
                MUSIC_PLAYER_OVERLAY_TEXT_COLOR_DEFAULT,
            ),
        )
        music_background = setting(
            MUSIC_PLAYER_OVERLAY_BACKGROUND_KEY,
            MUSIC_PLAYER_OVERLAY_BACKGROUND_DEFAULT,
        )
        self.music_player_background_color_mode.setChecked(
            music_background == "color"
        )
        self.music_player_background_transparent.setChecked(
            music_background != "color"
        )
        self._set_color_button(
            self.music_player_background_color_btn,
            setting(
                MUSIC_PLAYER_OVERLAY_BACKGROUND_COLOR_KEY,
                MUSIC_PLAYER_OVERLAY_BACKGROUND_COLOR_DEFAULT,
            ),
        )
        self._set_color_button(
            self.music_player_frame_color_btn,
            setting(
                MUSIC_PLAYER_OVERLAY_FRAME_COLOR_KEY,
                MUSIC_PLAYER_OVERLAY_FRAME_COLOR_DEFAULT,
            ),
        )
        self._set_color_button(
            self.music_player_spectrum_color_btn,
            setting(
                MUSIC_PLAYER_OVERLAY_SPECTRUM_COLOR_KEY,
                MUSIC_PLAYER_OVERLAY_SPECTRUM_COLOR_DEFAULT,
            ),
        )
        self.music_player_auto_colors.setChecked(
            setting(
                MUSIC_PLAYER_OVERLAY_AUTO_COLORS_KEY,
                "1" if MUSIC_PLAYER_OVERLAY_AUTO_COLORS_DEFAULT else "0",
            ) == "1"
        )
        self._set_combo_by_data(
            self.music_player_show_mode,
            setting(
                MUSIC_PLAYER_OVERLAY_SHOW_MODE_KEY,
                MUSIC_PLAYER_OVERLAY_SHOW_MODE_DEFAULT,
            ),
        )
        try:
            music_duration = int(setting(
                MUSIC_PLAYER_OVERLAY_DURATION_SECONDS_KEY,
                str(MUSIC_PLAYER_OVERLAY_DURATION_SECONDS_DEFAULT),
            ))
        except ValueError:
            music_duration = MUSIC_PLAYER_OVERLAY_DURATION_SECONDS_DEFAULT
        self.music_player_duration_seconds.setValue(
            max(1, min(120, music_duration))
        )
        self._set_combo_by_data(
            self.music_player_animation,
            setting(
                MUSIC_PLAYER_OVERLAY_ANIMATION_KEY,
                MUSIC_PLAYER_OVERLAY_ANIMATION_DEFAULT,
            ),
        )
        self._set_combo_by_data(
            self.music_player_direction,
            setting(
                MUSIC_PLAYER_OVERLAY_DIRECTION_KEY,
                MUSIC_PLAYER_OVERLAY_DIRECTION_DEFAULT,
            ),
        )
        self._update_music_player_overlay_enabled_state()

        self.auction_lots_overlay_font.setCurrentFont(QFont(
            setting(
                AUCTION_LOTS_OVERLAY_FONT_FAMILY_KEY,
                AUCTION_LOTS_OVERLAY_FONT_FAMILY_DEFAULT,
            )
        ))
        try:
            auction_lots_font_size = int(setting(
                AUCTION_LOTS_OVERLAY_FONT_SIZE_KEY,
                str(AUCTION_LOTS_OVERLAY_FONT_SIZE_DEFAULT),
            ))
        except ValueError:
            auction_lots_font_size = AUCTION_LOTS_OVERLAY_FONT_SIZE_DEFAULT
        self.auction_lots_overlay_font_size.setValue(
            max(8, min(160, auction_lots_font_size))
        )
        self._set_color_button(
            self.auction_lots_overlay_font_color_btn,
            setting(
                AUCTION_LOTS_OVERLAY_FONT_COLOR_KEY,
                AUCTION_LOTS_OVERLAY_FONT_COLOR_DEFAULT,
            ),
        )
        auction_lots_background = setting(
            AUCTION_LOTS_OVERLAY_BACKGROUND_KEY,
            AUCTION_LOTS_OVERLAY_BACKGROUND_DEFAULT,
        )
        self.auction_lots_background_media_mode.setChecked(
            auction_lots_background == "media"
        )
        self.auction_lots_background_color_mode.setChecked(
            auction_lots_background == "color"
        )
        self.auction_lots_background_transparent.setChecked(
            auction_lots_background not in {"color", "media"}
        )
        self._set_color_button(
            self.auction_lots_background_color_btn,
            setting(
                AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_KEY,
                AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_DEFAULT,
            ),
        )
        saved_lots_background = setting(
            AUCTION_LOTS_OVERLAY_BACKGROUND_MEDIA_ID_KEY, ""
        )
        self._refresh_auction_lots_background_library(saved_lots_background)
        if saved_lots_background and not self.auction_lots_background_combo.currentData():
            self.db.set_settings_bulk({
                AUCTION_LOTS_OVERLAY_BACKGROUND_MEDIA_ID_KEY: "",
            })
        self._update_auction_lots_background_enabled_state()

        self.rules_overlay_visible.setChecked(
            setting(RULES_OVERLAY_VISIBLE_KEY, "1" if RULES_OVERLAY_VISIBLE_DEFAULT else "0") == "1"
        )
        self.rules_overlay_autoscroll.setChecked(
            setting(RULES_OVERLAY_AUTOSCROLL_KEY, "1" if RULES_OVERLAY_AUTOSCROLL_DEFAULT else "0") == "1"
        )
        rules_background = setting(RULES_OVERLAY_BACKGROUND_KEY, RULES_OVERLAY_BACKGROUND_DEFAULT)
        self.rules_background_color_mode.setChecked(rules_background == "color")
        self.rules_background_transparent.setChecked(rules_background != "color")
        self._set_color_button(
            self.rules_background_color_btn,
            setting(RULES_OVERLAY_BACKGROUND_COLOR_KEY, RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT),
        )
        try:
            opacity = int(setting(
                RULES_OVERLAY_BACKGROUND_OPACITY_KEY,
                str(RULES_OVERLAY_BACKGROUND_OPACITY_DEFAULT),
            ))
        except ValueError:
            opacity = RULES_OVERLAY_BACKGROUND_OPACITY_DEFAULT
        self.rules_background_opacity.setValue(max(0, min(100, opacity)))
        try:
            padding = int(setting(RULES_OVERLAY_PADDING_KEY, str(RULES_OVERLAY_PADDING_DEFAULT)))
        except ValueError:
            padding = RULES_OVERLAY_PADDING_DEFAULT
        self.rules_overlay_padding.setValue(max(0, min(200, padding)))
        self._update_rules_background_enabled_state()

        state = "РАБОТАЕТ" if self.api.running else f"НЕ ЗАПУЩЕН: {self.api.last_error or 'неизвестная ошибка'}"
        self.api_label.setText(
            f"Состояние: {state}\n"
            f"Оверлей OBS: {self.api.base_url}/overlay\n"
            f"Отдельный список OBS: {self.api.base_url}/list-overlay\n"
            f"Таймер OBS: {self.api.base_url}/timer-overlay\n"
            f"Музыкальный плеер OBS: {self.api.base_url}/music-player-overlay\n"
            f"Список лотов OBS: {self.api.base_url}/auction-lots-overlay\n"
            f"Правила OBS: {self.api.base_url}/rules-overlay\n"
            f"OBS JSON: {self.api.base_url}/api/data\n"
            f"Публичный JSON: {self.api.base_url}/api/public"
        )

    def save(self):
        background_asset = self._selected_background_asset()
        legacy_background_file = (
            background_asset.managed_name
            if background_asset is not None
            and background_asset.storage_mode == MEDIA_STORAGE_MANAGED
            else ""
        )
        values = {
            "stream_current_game_id": str(self.game_combo.currentData() or ""),
            # Текст сохраняем даже при отключённом блоке, чтобы он не потерялся.
            "stream_info": self.info_field.text().strip(),
            "stream_info_enabled": "1" if self.info_enabled.isChecked() else "0",
            "stream_format": self.format_combo.currentText(),
            "overlay_background_media_id": (
                str(background_asset.id) if background_asset is not None else ""
            ),
            # Kept only for compatibility with pre-W2 versions.  External
            # absolute paths are never written into the legacy filename key.
            "overlay_background_file": legacy_background_file,
            "overlay_background_mode": str(self.background_mode.currentData() or "stretch"),
            "overlay_webcam_enabled": "1" if self.webcam_enabled.isChecked() else "0",
            "overlay_webcam_position": str(self.webcam_position.currentData() or "top_right"),
            "overlay_list_enabled": "1" if self.overlay_list_enabled.isChecked() else "0",
            "overlay_list_side": str(self.overlay_list_side.currentData() or "auto"),
            "overlay_info_position": str(self.info_position.currentData() or "auto"),
        }
        for color_key, color_btn in self.frame_color_buttons.items():
            values[f"overlay_frame_{color_key}_color"] = str(
                color_btn.property("fontColor") or "#FFFFFF"
            )
        values.update(self._collect_typography_settings())

        self.db.set_settings_bulk(values)
        QMessageBox.information(self, "Стрим", "Параметры сохранены. OBS API обновлён.")

