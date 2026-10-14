from __future__ import annotations

from typing import Callable
from secrets import token_urlsafe

from PySide6.QtCore import QEvent, QSignalBlocker, Qt, QUrl
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDesktopServices,
    QFont,
    QPalette,
    QPixmap,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextListFormat,
)
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QCheckBox,
    QDialog,
    QFormLayout,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QFrame,
    QScrollArea,
    QSplitter,
    QStackedLayout,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..constants import (
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
)
from ..database import Database
from ..media import MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, media_asset_available, resolve_media_asset_path
from .common import (
    ScrollSafeComboBox,
    ScrollSafeFontComboBox,
    ScrollSafeSpinBox,
    make_wide_step_control,
    make_screen_color_picker_button,
    pick_screen_color,
)


_UNSET_MEDIA = object()


class AuctionRulesEditorDialog(QDialog):
    """WYSIWYG editor for reusable auction-rule templates.

    The same editor is used before, during and after an auction.  While a local
    auction is open, saving its source template also synchronizes the session
    rules copy in the database, so there is no separate "current rules" editor.
    """

    def __init__(
        self,
        db: Database,
        parent: QWidget | None = None,
        *,
        initial_template_id: int | None = None,
        rules_overlay_url: Callable[[], str] | None = None,
        import_background: Callable[[Callable[[int], None], QWidget], None] | None = None,
    ):
        super().__init__(parent)
        self.db = db
        self._rules_overlay_url = rules_overlay_url
        self._import_background = import_background
        # One ephemeral link per editor: changing the selected template updates
        # its browser preview without altering active/on-air Rules.
        self._rules_preview_token = token_urlsafe(24) if rules_overlay_url else None
        self._initial_template_id = (
            int(initial_template_id) if initial_template_id is not None else None
        )
        self._loaded_template_id: int | None = None
        self._loaded_html = ""
        self._loaded_obs_presentation: dict[str, object] = {}
        self._loaded_obs_explicit = False
        self._loading = False
        # New templates created in this editor can be saved directly once.
        self._new_template_ids: set[int] = set()
        self.setWindowTitle("Правила аукциона")
        self.resize(1050, 760)
        self.setMinimumSize(760, 560)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        template_row = QHBoxLayout()
        template_row.addWidget(QLabel("Шаблон:"))
        self.template_combo = ScrollSafeComboBox()
        self.template_combo.setMinimumWidth(280)
        self.template_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.template_combo.currentIndexChanged.connect(self._template_index_changed)
        template_row.addWidget(self.template_combo, 1)
        root.addLayout(template_row)

        # Keep the template selector and the template actions on separate
        # rows. At the dialog's minimum width they cannot fit side by side:
        # the old expanding combo overlapped the active badge and Create.
        template_actions_row = QHBoxLayout()
        template_actions_row.addStretch(1)
        for title, handler in (
            ("Создать", self._create_template),
            ("Переименовать", self._rename_template),
            ("Удалить", self._delete_template),
            ("Сделать активным", self._make_active),
        ):
            button = QPushButton(title)
            button.clicked.connect(handler)
            if title == "Сделать активным":
                self.activate_template_btn = button
            elif title == "Удалить":
                self.delete_template_btn = button
            template_actions_row.addWidget(button)
        root.addLayout(template_actions_row)

        # UI-060 / P11-I: surface the existing session-to-template relationship
        # before the user changes any rules. No new session state or settings.
        self.rules_session_notice_label = QLabel()
        self.rules_session_notice_label.setWordWrap(True)
        self.rules_session_notice_label.setStyleSheet("font-weight: 600;")
        self.rules_session_notice_label.hide()
        root.addWidget(self.rules_session_notice_label)

        # P11-K5 FIX1: text and appearance must remain visible together.
        # Reparent the SAME existing editable QTextEdit and OBS controls,
        # never copy text into a secondary preview or create a second model.
        self.rules_editor_splitter = QSplitter(Qt.Horizontal)
        self.rules_editor_splitter.setChildrenCollapsible(False)
        self.rules_text_page = QWidget()
        text_layout = QVBoxLayout(self.rules_text_page)
        text_layout.setContentsMargins(0, 8, 0, 0)
        text_layout.setSpacing(8)
        text_layout.addWidget(QLabel("Текст правил"))
        self.rules_obs_page = QWidget()
        obs_layout = QVBoxLayout(self.rules_obs_page)
        obs_layout.setContentsMargins(6, 8, 6, 0)
        obs_layout.setSpacing(8)
        obs_layout.addWidget(QLabel("Оформление OBS"))
        self.rules_obs_scroll = QScrollArea()
        self.rules_obs_scroll.setFrameShape(QFrame.NoFrame)
        self.rules_obs_scroll.setWidgetResizable(True)
        self.rules_obs_scroll.setMinimumWidth(200)
        self.rules_obs_scroll.setMinimumHeight(130)
        self.rules_obs_scroll.setWidget(self.rules_obs_page)
        self.rules_editor_splitter.addWidget(self.rules_text_page)
        self.rules_editor_splitter.addWidget(self.rules_obs_scroll)
        self.rules_editor_splitter.setStretchFactor(0, 2)
        self.rules_editor_splitter.setStretchFactor(1, 1)
        self.rules_editor_splitter.setSizes([680, 340])
        root.addWidget(self.rules_editor_splitter, 1)

        # P11-B: reuse AuctionTab's existing URL provider; neither duplicate
        # its port resolution nor introduce another OBS route or preview mode.
        if rules_overlay_url is not None:
            obs_layout.addWidget(QLabel("URL рабочего виджета правил (текущий аукцион):"))
            self.rules_overlay_url_label = QLabel(str(rules_overlay_url()))
            self.rules_overlay_url_label.setWordWrap(True)
            self.rules_overlay_url_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.rules_overlay_url_label.setSizePolicy(
                QSizePolicy.Ignored, QSizePolicy.Preferred
            )
            obs_layout.addWidget(self.rules_overlay_url_label)
            rules_access = QVBoxLayout()

            self.copy_rules_url_btn = QPushButton("Копировать URL")
            self.copy_rules_url_btn.clicked.connect(
                lambda _checked=False: QApplication.clipboard().setText(
                    str(rules_overlay_url())
                )
            )
            rules_access.addWidget(self.copy_rules_url_btn)

            self.preview_rules_obs_btn = QPushButton("Проверить в браузере")
            self.preview_rules_obs_btn.setToolTip(
                "Показать сохранённый вариант выбранного шаблона правил. "
                "Несохранённые изменения появятся после нажатия «Сохранить»."
            )
            self.preview_rules_obs_btn.clicked.connect(
                self._open_selected_template_preview
            )
            rules_access.addWidget(self.preview_rules_obs_btn)
            obs_layout.addLayout(rules_access)
            self.rules_preview_target_label = QLabel()
            self.rules_preview_target_label.setWordWrap(True)
            obs_layout.addWidget(self.rules_preview_target_label)

        # P11-K3: the five existing Rules appearance settings now belong
        # to the selected template, not to a second save in Stream / OBS.
        obs_form = QFormLayout()
        obs_form.setVerticalSpacing(10)
        obs_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        obs_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.rules_obs_autoscroll = QCheckBox("Автопрокрутка")
        self.rules_obs_autoscroll.toggled.connect(self._editor_changed)
        obs_form.addRow("Прокрутка:", self.rules_obs_autoscroll)

        background_row = QWidget()
        background_row_layout = QHBoxLayout(background_row)
        background_row_layout.setContentsMargins(0, 0, 0, 0)
        self.rules_obs_transparent = QRadioButton("Прозрачный")
        self.rules_obs_color_mode = QRadioButton("Цвет")
        self.rules_obs_media_mode = QRadioButton("Свой")
        self.rules_obs_transparent.toggled.connect(self._obs_background_changed)
        self.rules_obs_color_mode.toggled.connect(self._obs_background_changed)
        self.rules_obs_media_mode.toggled.connect(self._obs_background_changed)
        background_row_layout.addWidget(self.rules_obs_transparent)
        background_row_layout.addWidget(self.rules_obs_color_mode)
        background_row_layout.addWidget(self.rules_obs_media_mode)
        background_row_layout.addStretch()
        obs_form.addRow("Фон:", background_row)

        # K8A reads the existing shared background category. File import stays
        # with the original Stream/OBS importer until its separate UI step.
        self.rules_obs_media_combo = ScrollSafeComboBox()
        self.rules_obs_media_combo.setMinimumWidth(175)
        self.rules_obs_media_combo.currentIndexChanged.connect(self._editor_changed)
        self.rules_obs_media_refresh = QPushButton("Обновить")
        self.rules_obs_media_refresh.clicked.connect(lambda: self._refresh_rules_media_library())
        media_row = QWidget()
        media_row_layout = QHBoxLayout(media_row)
        media_row_layout.setContentsMargins(0, 0, 0, 0)
        media_row_layout.addWidget(self.rules_obs_media_combo, 1)
        media_row_layout.addWidget(self.rules_obs_media_refresh)
        obs_form.addRow("Из библиотеки:", media_row)
        self.rules_obs_media_add = QPushButton("Добавить фон…")
        self.rules_obs_media_add.setEnabled(import_background is not None)
        self.rules_obs_media_add.setToolTip(
            "Добавить PNG, JPG или WEBP через общую библиотеку фонов."
            if import_background is not None else
            "Добавление фонов доступно из редактора в главном окне."
        )
        self.rules_obs_media_add.clicked.connect(self._import_rules_media_file)
        obs_form.addRow("", self.rules_obs_media_add)
        self.rules_obs_media_hint = QLabel(
            "Общая библиотека фонов: копия в программу или ссылка на исходник. "
            "GIF и видео будут доступны на следующем этапе."
        )
        self.rules_obs_media_hint.setWordWrap(True)
        obs_form.addRow(self.rules_obs_media_hint)
        self._refresh_rules_media_library()

        color_row = QWidget()
        color_row_layout = QHBoxLayout(color_row)
        color_row_layout.setContentsMargins(0, 0, 0, 0)
        self.rules_obs_color_btn = QPushButton()
        self.rules_obs_color_btn.clicked.connect(
            lambda: self._choose_obs_color(False)
        )
        self.rules_obs_color_pick_btn = make_screen_color_picker_button(
            "Выбрать цвет фона с экрана. Левый клик — принять, Escape — отмена."
        )
        self.rules_obs_color_pick_btn.clicked.connect(
            lambda: self._choose_obs_color(True)
        )
        color_row_layout.addWidget(self.rules_obs_color_btn)
        color_row_layout.addWidget(self.rules_obs_color_pick_btn)
        color_row_layout.addStretch()
        obs_form.addRow("Цвет фона:", color_row)

        self.rules_obs_opacity = ScrollSafeSpinBox()
        self.rules_obs_opacity.setRange(0, 100)
        self.rules_obs_opacity.setSuffix(" %")
        self.rules_obs_opacity.valueChanged.connect(self._editor_changed)
        self.rules_obs_opacity_control = make_wide_step_control(
            self.rules_obs_opacity,
            up_tooltip="Увеличить непрозрачность",
            down_tooltip="Уменьшить непрозрачность",
        )
        obs_form.addRow("Непрозрачность:", self.rules_obs_opacity_control)

        # Reuse the common 8px rounded edge and standard soft/inner glow.
        # Only glow on/off and its color are template settings: no extra
        # blur, radius, thickness or second presentation model.
        self.rules_obs_glow = QCheckBox("Светящийся контур")
        self.rules_obs_glow.toggled.connect(self._obs_glow_changed)
        obs_form.addRow("Контур:", self.rules_obs_glow)
        glow_row = QWidget()
        glow_layout = QHBoxLayout(glow_row)
        glow_layout.setContentsMargins(0, 0, 0, 0)
        self.rules_obs_glow_color_btn = QPushButton()
        self.rules_obs_glow_color_btn.clicked.connect(
            lambda: self._choose_obs_glow_color(False)
        )
        self.rules_obs_glow_color_pick_btn = make_screen_color_picker_button(
            "Выбрать цвет подсветки с экрана. Левый клик — принять, Escape — отмена."
        )
        self.rules_obs_glow_color_pick_btn.clicked.connect(
            lambda: self._choose_obs_glow_color(True)
        )
        glow_layout.addWidget(self.rules_obs_glow_color_btn)
        glow_layout.addWidget(self.rules_obs_glow_color_pick_btn)
        glow_layout.addStretch()
        obs_form.addRow("Цвет контура:", glow_row)

        obs_layout.addLayout(obs_form)
        obs_layout.addStretch(1)

        tools1 = QHBoxLayout()
        self.style_combo = ScrollSafeComboBox()
        self.style_combo.addItem("Обычный текст", "normal")
        self.style_combo.addItem("Заголовок", "heading")
        self.style_combo.addItem("Подзаголовок", "subheading")
        self.style_combo.currentIndexChanged.connect(self._apply_paragraph_style)
        tools1.addWidget(self.style_combo)

        self.font_combo = ScrollSafeFontComboBox()
        self.font_combo.setMinimumWidth(190)
        self.font_combo.currentFontChanged.connect(self._apply_font_family)
        tools1.addWidget(self.font_combo)

        self.size_spin = ScrollSafeSpinBox()
        self.size_spin.setRange(6, 96)
        self.size_spin.setValue(14)
        self.size_spin.setSuffix(" pt")
        self.size_spin.valueChanged.connect(self._apply_font_size)
        self.size_spin_control = make_wide_step_control(
            self.size_spin,
            up_tooltip="Увеличить размер шрифта",
            down_tooltip="Уменьшить размер шрифта",
        )
        tools1.addWidget(self.size_spin_control)

        self.bold_btn = QPushButton("Ж")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setToolTip("Жирный")
        self.bold_btn.clicked.connect(self._apply_bold)
        self.italic_btn = QPushButton("К")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setToolTip("Курсив")
        self.italic_btn.clicked.connect(self._apply_italic)
        self.underline_btn = QPushButton("Ч")
        self.underline_btn.setCheckable(True)
        self.underline_btn.setToolTip("Подчёркивание")
        self.underline_btn.clicked.connect(self._apply_underline)
        tools1.addWidget(self.bold_btn)
        tools1.addWidget(self.italic_btn)
        tools1.addWidget(self.underline_btn)
        tools1.addStretch()
        self.rules_format_toolbars = []
        self._add_scrollable_toolbar(text_layout, tools1)

        tools2 = QHBoxLayout()
        self.text_color_btn = QPushButton("Цвет текста")
        self.text_color_btn.clicked.connect(lambda: self._choose_color(False))
        self.text_color_pick_btn = make_screen_color_picker_button(
            "Выбрать цвет текста с экрана. Левый клик — принять, Escape — отмена."
        )
        self.text_color_pick_btn.clicked.connect(lambda: self._choose_color(True))
        tools2.addWidget(self.text_color_btn)
        tools2.addWidget(self.text_color_pick_btn)
        tools2.addSpacing(14)

        for title, alignment in (
            ("Слева", Qt.AlignLeft),
            ("Центр", Qt.AlignHCenter),
            ("Справа", Qt.AlignRight),
            ("По ширине", Qt.AlignJustify),
        ):
            button = QPushButton(title)
            button.clicked.connect(
                lambda _checked=False, align=alignment: self.editor.setAlignment(align)
            )
            tools2.addWidget(button)

        bullet_btn = QPushButton("• Список")
        bullet_btn.clicked.connect(lambda: self._make_list(QTextListFormat.Style.ListDisc))
        number_btn = QPushButton("1. Список")
        number_btn.clicked.connect(lambda: self._make_list(QTextListFormat.Style.ListDecimal))
        tools2.addWidget(bullet_btn)
        tools2.addWidget(number_btn)
        tools2.addStretch()
        self._add_scrollable_toolbar(text_layout, tools2)

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.setPlaceholderText("Введите правила аукциона…")
        self._rules_default_editor_palette = QPalette(self.editor.palette())
        self._rules_default_viewport_palette = QPalette(self.editor.viewport().palette())
        self._rules_media_source_key = None
        self._rules_media_original = QPixmap()
        self._rules_media_brush_key = None
        self._rules_media_label = QLabel()
        self._rules_media_label.setScaledContents(True)
        self._rules_media_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._rules_media_label.hide()
        self._rules_glow_effect = QGraphicsDropShadowEffect(self.editor)
        self._rules_glow_effect.setOffset(0, 0)
        self._rules_glow_effect.setBlurRadius(20)
        self._rules_glow_effect.setEnabled(False)
        self.editor.setGraphicsEffect(self._rules_glow_effect)
        self.editor.textChanged.connect(self._editor_changed)
        self.editor.cursorPositionChanged.connect(self._sync_format_controls)
        self.editor.viewport().installEventFilter(self)
        self.rules_text_canvas = QWidget()
        self.rules_text_canvas_layout = QStackedLayout(self.rules_text_canvas)
        self.rules_text_canvas_layout.setContentsMargins(0, 0, 0, 0)
        self.rules_text_canvas_layout.setStackingMode(QStackedLayout.StackAll)
        self.rules_text_canvas_layout.addWidget(self._rules_media_label)
        self.rules_text_canvas_layout.addWidget(self.editor)
        self.rules_text_canvas_layout.setCurrentWidget(self.editor)
        text_layout.addWidget(self.rules_text_canvas, 1)

        bottom = QHBoxLayout()
        self.dirty_label = QLabel()
        self.dirty_label.setProperty("muted", True)
        bottom.addWidget(self.dirty_label)
        bottom.addStretch()
        save_btn = QPushButton("Сохранить")
        # P11-F: saving must not close the composite Rules editor.
        # Reuse the existing persistence/dirty-status path unchanged.
        save_btn.clicked.connect(lambda _checked=False: self._save_with_choice())
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        bottom.addWidget(save_btn)
        bottom.addWidget(close_btn)
        root.addLayout(bottom)

        self._reload_templates(
            selected_id=self._initial_template_id,
            select_active=self._initial_template_id is None,
        )
        self._set_color_button(self.text_color_btn, QColor("#FFFFFF"), "Цвет текста")



    def _add_scrollable_toolbar(self, layout: QVBoxLayout, buttons: QHBoxLayout) -> None:
        """Keep the original formatting controls reachable at narrow widths."""
        wrapper = QWidget()
        wrapper.setLayout(buttons)
        wrapper.adjustSize()
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(wrapper)
        scroll.setFixedHeight(wrapper.sizeHint().height() + 22)
        layout.addWidget(scroll)
        self.rules_format_toolbars.append(scroll)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if not hasattr(self, "rules_editor_splitter"):
            return
        # At small sizes both sections remain accessible without compressing
        # the editable text to an unusable narrow column.
        orientation = Qt.Vertical if self.width() < 950 else Qt.Horizontal
        splitter = self.rules_editor_splitter
        if splitter.orientation() != orientation:
            splitter.setOrientation(orientation)
            splitter.setSizes(
                [max(180, self.height() * 3 // 5), max(130, self.height() * 2 // 5)]
                if orientation == Qt.Vertical else [max(420, self.width() * 2 // 3), 320]
            )

    def _open_selected_template_preview(self) -> None:
        """Preview the selected saved template, never switch live OBS source."""
        if self._rules_overlay_url is None:
            return
        selected = self.template_combo.currentData()
        if selected is None or self._loaded_template_id is None:
            return
        selected_id = int(selected)
        if selected_id != self._loaded_template_id:
            QMessageBox.warning(
                self, "Предпросмотр правил",
                "Выбранный шаблон ещё не загружен в редактор. "
                "Повторно выберите шаблон и откройте предпросмотр."
            )
            return
        QDesktopServices.openUrl(
            QUrl(self._selected_template_preview_url(selected_id))
        )

    def _selected_template_preview_url(self, template_id: int) -> str:
        assert self._rules_overlay_url is not None
        assert self._rules_preview_token is not None
        # URL stays the same while the editor changes its selected template.
        # The selected ID is resolved from the process-only preview registry.
        return (
            str(self._rules_overlay_url())
            + f"?preview=1&follow_token={self._rules_preview_token}"
        )

    def _reload_templates(
        self,
        *,
        selected_id: int | None = None,
        select_active: bool = False,
    ) -> None:
        templates = self.db.list_rule_templates()
        active_id = next((int(row["id"]) for row in templates if row["is_active"]), None)
        target_id = active_id if select_active or selected_id is None else int(selected_id)
        with QSignalBlocker(self.template_combo):
            self.template_combo.clear()
            target_index = 0
            for index, row in enumerate(templates):
                row_id = int(row["id"])
                self.template_combo.addItem(str(row["name"]), row_id)
                if int(row["is_active"]):
                    self.template_combo.setItemData(
                        index, QBrush(QColor("#256849")), Qt.BackgroundRole
                    )
                    self.template_combo.setItemData(
                        index, QBrush(QColor("#F3FFF7")), Qt.ForegroundRole
                    )
                    self.template_combo.setItemData(index, "Активный шаблон", Qt.ToolTipRole)
                if row_id == target_id:
                    target_index = index
            if self.template_combo.count():
                self.template_combo.setCurrentIndex(target_index)
        if self.template_combo.count():
            self._load_template(int(self.template_combo.currentData()))

    def _legacy_rules_presentation(self) -> dict[str, object]:
        """Resolve the user's original global Rules values for legacy templates."""
        settings = self.db.get_settings()
        background = str(settings.get(
            RULES_OVERLAY_BACKGROUND_KEY, RULES_OVERLAY_BACKGROUND_DEFAULT
        ) or RULES_OVERLAY_BACKGROUND_DEFAULT).strip().casefold()
        if background not in ("color", "transparent"):
            background = RULES_OVERLAY_BACKGROUND_DEFAULT
        color = QColor(str(settings.get(
            RULES_OVERLAY_BACKGROUND_COLOR_KEY, RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT
        ) or RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT))
        if not color.isValid():
            color = QColor(RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT)
        return {
            "autoscroll": settings.get(
                RULES_OVERLAY_AUTOSCROLL_KEY,
                "1" if RULES_OVERLAY_AUTOSCROLL_DEFAULT else "0",
            ) == "1",
            "background": background,
            "background_color": color.name().upper(),
            "background_opacity": self.db._bounded_int_setting(
                settings.get(RULES_OVERLAY_BACKGROUND_OPACITY_KEY),
                RULES_OVERLAY_BACKGROUND_OPACITY_DEFAULT, 0, 100,
            ),
            "padding": self.db._bounded_int_setting(
                settings.get(RULES_OVERLAY_PADDING_KEY),
                RULES_OVERLAY_PADDING_DEFAULT, 0, 200,
            ),
        }

    @staticmethod
    def _with_glow_defaults(presentation: dict[str, object]) -> dict[str, object]:
        # Old five-key template JSON remains valid and clean on first load.
        return {
            **presentation,
            "glow": bool(presentation.get("glow", False)),
            "glow_color": str(presentation.get("glow_color", "#FFFFFF")).upper(),
            "background_media_id": presentation.get("background_media_id"),
        }

    def _obs_presentation_values(self) -> dict[str, object]:
        return {
            "autoscroll": self.rules_obs_autoscroll.isChecked(),
            "background": (
                "media" if self.rules_obs_media_mode.isChecked()
                else "color" if self.rules_obs_color_mode.isChecked()
                else "transparent"
            ),
            "background_media_id": (
                int(self.rules_obs_media_combo.currentData())
                if str(self.rules_obs_media_combo.currentData() or "").isdigit()
                else None
            ),
            "background_color": str(
                self.rules_obs_color_btn.property("selectedColor")
                or RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT
            ).upper(),
            "background_opacity": self.rules_obs_opacity.value(),
            "glow": self.rules_obs_glow.isChecked(),
            "glow_color": str(
                self.rules_obs_glow_color_btn.property("selectedColor")
                or "#FFFFFF"
            ).upper(),
            # Retain the legacy saved field for schema/backup compatibility,
            # but no longer expose it or let it control display geometry.
            "padding": int(self._loaded_obs_presentation.get(
                "padding", RULES_OVERLAY_PADDING_DEFAULT
            )),
        }

    def _apply_obs_presentation(self, values: dict[str, object]) -> None:
        self.rules_obs_autoscroll.setChecked(bool(values["autoscroll"]))
        self.rules_obs_color_mode.setChecked(values["background"] == "color")
        self.rules_obs_media_mode.setChecked(values["background"] == "media")
        self.rules_obs_transparent.setChecked(values["background"] == "transparent")
        self._refresh_rules_media_library(values.get("background_media_id"))
        self._set_color_button(
            self.rules_obs_color_btn,
            QColor(str(values["background_color"])),
            "Цвет фона",
        )
        self.rules_obs_opacity.setValue(int(values["background_opacity"]))
        self.rules_obs_glow.setChecked(bool(values.get("glow", False)))
        self._set_color_button(
            self.rules_obs_glow_color_btn,
            QColor(str(values.get("glow_color", "#FFFFFF"))),
            "Цвет контура",
        )
        self._obs_glow_changed()
        self._obs_background_changed()

    def _obs_background_changed(self, _checked: bool = False) -> None:
        color_mode = self.rules_obs_color_mode.isChecked()
        self.rules_obs_color_btn.setEnabled(color_mode)
        self.rules_obs_color_pick_btn.setEnabled(color_mode)
        self.rules_obs_opacity_control.setEnabled(color_mode)
        self.rules_obs_media_combo.setEnabled(self.rules_obs_media_mode.isChecked())
        self.rules_obs_media_refresh.setEnabled(self.rules_obs_media_mode.isChecked())
        self.rules_obs_media_add.setEnabled(
            self.rules_obs_media_mode.isChecked()
            and self._import_background is not None
        )
        self._editor_changed()

    def _refresh_rules_media_library(self, selected_id=_UNSET_MEDIA) -> None:
        """Use registered shared overlay assets; never create a new library."""
        if selected_id is _UNSET_MEDIA:
            selected_id = self.rules_obs_media_combo.currentData()
        self.db.sync_managed_media_category(MEDIA_CATEGORY_OVERLAY_BACKGROUNDS)
        existing = []
        for asset in self.db.list_media_assets(MEDIA_CATEGORY_OVERLAY_BACKGROUNDS):
            if not media_asset_available(self.db.path.parent, asset):
                continue
            try:
                extension = resolve_media_asset_path(self.db.path.parent, asset).suffix.lower()
            except (OSError, ValueError):
                continue
            if extension in {".png", ".jpg", ".jpeg", ".webp"}:
                existing.append(asset)
        with QSignalBlocker(self.rules_obs_media_combo):
            self.rules_obs_media_combo.clear()
            self.rules_obs_media_combo.addItem("— выберите изображение —", None)
            for asset in existing:
                self.rules_obs_media_combo.addItem(asset.display_name, asset.id)
            idx = self.rules_obs_media_combo.findData(selected_id)
            self.rules_obs_media_combo.setCurrentIndex(idx if idx >= 0 else 0)
        if not self._loading and hasattr(self, "editor"):
            self._editor_changed()

    def _import_rules_media_file(self) -> None:
        """Invoke the one pre-existing shared managed/external importer."""
        if self._import_background is not None:
            self._import_background(self._rules_media_imported, self)

    def _rules_media_imported(self, asset_id: int) -> None:
        """Select newly imported media in this template, not other widgets."""
        self._refresh_rules_media_library(asset_id)
        if self.rules_obs_media_combo.currentData() != asset_id:
            QMessageBox.warning(
                self, "Фон недоступен",
                "Не удалось выбрать добавленный фон в общей библиотеке."
            )
            return
        self.rules_obs_media_mode.setChecked(True)
        self._editor_changed()

    def _obs_glow_changed(self, _checked: bool = False) -> None:
        enabled = self.rules_obs_glow.isChecked()
        self.rules_obs_glow_color_btn.setEnabled(enabled)
        self.rules_obs_glow_color_pick_btn.setEnabled(enabled)
        self._editor_changed()

    def _choose_obs_glow_color(self, pipette: bool) -> None:
        current = QColor(str(
            self.rules_obs_glow_color_btn.property("selectedColor") or "#FFFFFF"
        ))
        selected = (
            pick_screen_color(self) if pipette
            else QColorDialog.getColor(current, self, "Цвет подсветки правил")
        )
        if selected is None or not selected.isValid():
            return
        self._set_color_button(
            self.rules_obs_glow_color_btn, selected, "Цвет контура"
        )
        self._editor_changed()

    def _choose_obs_color(self, pipette: bool) -> None:
        current = QColor(str(
            self.rules_obs_color_btn.property("selectedColor")
            or RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT
        ))
        selected = (
            pick_screen_color(self) if pipette
            else QColorDialog.getColor(current, self, "Цвет фона правил")
        )
        if selected is None or not selected.isValid():
            return
        self._set_color_button(self.rules_obs_color_btn, selected, "Цвет фона")
        self._editor_changed()

    def _template_index_changed(self, index: int) -> None:
        if self._loading or index < 0:
            return
        new_id = self.template_combo.itemData(index)
        if new_id is None or int(new_id) == self._loaded_template_id:
            return
        if not self._confirm_discard_or_save():
            with QSignalBlocker(self.template_combo):
                old_index = self.template_combo.findData(self._loaded_template_id)
                if old_index >= 0:
                    self.template_combo.setCurrentIndex(old_index)
            return
        self._load_template(int(new_id))

    def _load_template(self, template_id: int) -> None:
        template = self.db.get_rule_template(template_id)
        if template is None:
            self._reload_templates(select_active=True)
            return
        self._loading = True
        try:
            self._loaded_template_id = int(template["id"])
            self._loaded_html = str(template["content_html"] or "")
            explicit = self.db.get_rule_template_presentation(template_id)
            self._loaded_obs_explicit = explicit is not None
            self._loaded_obs_presentation = self._with_glow_defaults(
                explicit if explicit is not None else self._legacy_rules_presentation()
            )
            self._apply_obs_presentation(self._loaded_obs_presentation)
            self.editor.setHtml(self._loaded_html) if self._loaded_html else self.editor.clear()
        finally:
            self._loading = False
        self._refresh_local_rules_preview()
        if self._rules_preview_token is not None:
            self.db.set_rules_preview_selection(
                self._rules_preview_token, self._loaded_template_id
            )
            self._publish_unsaved_preview()
        self._update_status()
        self._update_rules_session_notice()
        self._sync_format_controls()

    def _update_rules_session_notice(self) -> None:
        """Read current auction ownership only on template selection/reload.

        This intentionally does not poll SQLite on each QTextEdit keystroke.
        A source-template Save already mirrors into matching open local
        sessions through the existing Database API.
        """
        session = self.db.get_open_auction_session()
        source_id = session.get("rules_template_id") if session else None
        if session is None:
            self.rules_session_notice_label.clear()
            self.rules_session_notice_label.hide()
            return
        if source_id is not None and int(source_id) == self._loaded_template_id:
            self.rules_session_notice_label.setText(
                "Этот шаблон используется текущим аукционом. "
                "После сохранения изменения обновят правила текущего аукциона "
                "и виджет правил, если он показан в OBS."
            )
        else:
            self.rules_session_notice_label.setText(
                "Текущий аукцион использует другой шаблон. "
                "Сохранение здесь не изменит правила текущего аукциона."
            )
        self.rules_session_notice_label.show()

    def _is_dirty(self) -> bool:
        if self._loaded_template_id is None:
            return False
        current = self.editor.toHtml() if self.editor.toPlainText() or self.editor.document().blockCount() else ""
        presentation_dirty = (
            self._obs_presentation_values() != self._loaded_obs_presentation
        )
        if not self._loaded_html and not self.editor.toPlainText().strip():
            return presentation_dirty
        return current != self._loaded_html or presentation_dirty

    def _refresh_local_rules_preview(self) -> None:
        """Mirror OBS color/opacity and automatic inset in the editable area.

        This is a *view-only* treatment of the SAME QTextEdit/document. No HTML
        rewrite, second rendering backend or template write occurs on preview.
        Other OBS appearance features are separate future UI-060 increments.
        """
        values = self._obs_presentation_values()
        if values["background"] == "color":
            color = QColor(str(values["background_color"]))
            alpha = round(int(values["background_opacity"]) * 255 / 100)
            background = (
                f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"
            )
        else:
            background = "transparent"

        # Style the viewport, not the QTextEdit frame: retain the application's
        # focus border and keep all text editing, selection and shortcuts intact.
        glow = bool(values["glow"])
        edge = QColor(str(values["glow_color"]))
        edge_alpha = 160 if glow else 42
        stroke = (
            f"rgba({edge.red()}, {edge.green()}, {edge.blue()}, {edge_alpha})"
            if glow else "rgba(255, 255, 255, 42)"
        )
        # A border-image stylesheet on QTextEdit.viewport is swallowed by
        # the native QTextEdit painting. Use a real QPalette.Base pixmap brush:
        # it paints *behind* editable text and never rewrites HTML.
        media_selected = (
            values["background"] == "media"
            and values["background_media_id"] is not None
        )
        color_css = (
            "background-color: transparent;" if media_selected
            else f"background-color: {background};"
        )
        style = (
            f"{color_css}"
            f"border-radius: 8px; border: 1px solid {stroke};"
        )
        viewport = self.editor.viewport()
        if viewport.styleSheet() != style:
            viewport.setStyleSheet(style)
        # The image is displayed under the one transparent editable surface.
        self._update_rules_media_layer(values)
        self._rules_glow_effect.setColor(QColor(
            edge.red(), edge.green(), edge.blue(), 148
        ))
        self._rules_glow_effect.setEnabled(glow)

        self._update_local_rules_padding()

    def _update_rules_media_layer(self, values: dict[str, object]) -> bool:
        """Paint the cached image *under* one transparent native QTextEdit.

        A QTextEdit viewport repaints its own base color, so a QSS border-image
        or a QPalette texture on its viewport is not a reliable actual preview.
        Using a QWidget stack leaves text, cursor, scrolling and QTextDocument
        untouched and avoids duplicating the HTML renderer or editor model.
        """
        viewport = self.editor.viewport()
        asset = None
        if (values["background"] == "media"
                and values.get("background_media_id") is not None):
            asset = self.db.get_media_asset(int(values["background_media_id"]))
        path = None
        if (asset is not None
                and asset.category == MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
                and media_asset_available(self.db.path.parent, asset)):
            try:
                path = resolve_media_asset_path(self.db.path.parent, asset)
            except (ValueError, OSError):
                path = None

        valid = False
        if path is not None and path.suffix.lower() in {
            ".png", ".jpg", ".jpeg", ".webp",
        }:
            try:
                source_key = (str(path), path.stat().st_mtime_ns)
            except OSError:
                source_key = None
            if source_key is not None:
                if self._rules_media_source_key != source_key:
                    self._rules_media_source_key = source_key
                    self._rules_media_original = QPixmap(str(path))
                    self._rules_media_brush_key = None
                if not self._rules_media_original.isNull():
                    valid = True
                    size = self.rules_text_canvas.size()
                    width, height = max(1, size.width()), max(1, size.height())
                    brush_key = (source_key, width, height)
                    if self._rules_media_brush_key != brush_key:
                        scaled = self._rules_media_original.scaled(
                            width, height, Qt.KeepAspectRatioByExpanding,
                            Qt.SmoothTransformation,
                        )
                        x = max(0, (scaled.width() - width) // 2)
                        y = max(0, (scaled.height() - height) // 2)
                        self._rules_media_label.setPixmap(
                            scaled.copy(x, y, width, height)
                        )
                        self._rules_media_brush_key = brush_key

        if valid:
            # Make the actual QTextEdit surface see-through; the media
            # is a non-interactive sibling painted beneath the text.
            transparent = QPalette(self._rules_default_editor_palette)
            transparent.setColor(QPalette.Base, QColor(0, 0, 0, 0))
            self.editor.setPalette(transparent)
            viewport.setPalette(transparent)
            self.editor.setAttribute(Qt.WA_TranslucentBackground, True)
            viewport.setAttribute(Qt.WA_TranslucentBackground, True)
            viewport.setAutoFillBackground(False)
            self.editor.setStyleSheet("QTextEdit { background: transparent; }")
            self._rules_media_label.show()
            self._rules_media_label.lower()
        else:
            self._rules_media_label.hide()
            self._rules_media_source_key = None
            self._rules_media_original = QPixmap()
            self._rules_media_brush_key = None
            self.editor.setStyleSheet("")
            self.editor.setPalette(self._rules_default_editor_palette)
            viewport.setPalette(self._rules_default_viewport_palette)
            self.editor.setAttribute(Qt.WA_TranslucentBackground, False)
            viewport.setAttribute(Qt.WA_TranslucentBackground, False)
        viewport.update()
        return valid

    @staticmethod
    def _responsive_rules_padding(width: int, height: int) -> float:
        """Same clamp(8px, 2.2vmin, 24px) used by the OBS Browser Source."""
        dimension = min(max(1, int(width)), max(1, int(height)))
        return float(max(8, min(24, int(dimension * 0.022 + 0.5))))

    def _update_local_rules_padding(self) -> None:
        viewport = self.editor.viewport()
        margin = self._responsive_rules_padding(viewport.width(), viewport.height())
        document = self.editor.document()
        if document.documentMargin() != margin:
            document.setDocumentMargin(margin)

    def eventFilter(self, watched, event) -> bool:
        # Moving the responsive splitter can resize the editor viewport
        # without a QDialog resize event. The document itself is unchanged.
        if (hasattr(self, "editor") and watched is self.editor.viewport()
                and event.type() == QEvent.Resize):
            self._update_local_rules_padding()
            if (hasattr(self, "rules_obs_media_mode")
                    and self.rules_obs_media_mode.isChecked()):
                self._refresh_local_rules_preview()
        return super().eventFilter(watched, event)

    def _publish_unsaved_preview(self) -> None:
        """Live browser draft for this editor token only, never normal OBS.

        Reuses the existing read-only preview registry and the same validated
        Rules media payload resolver as saved templates.
        """
        if self._rules_preview_token is None or self._loaded_template_id is None:
            return
        if not self._is_dirty():
            self.db.clear_rules_preview_draft(
                self._rules_preview_token, self._loaded_template_id,
            )
            return
        presentation = self._obs_presentation_values()
        if (presentation["background"] == "media"
                and presentation.get("background_media_id") is None):
            # Allow choosing "Свой" before choosing a library file.
            presentation["background"] = "transparent"
        html = (
            self.editor.toHtml() if self.editor.toPlainText().strip() else ""
        )
        self.db.set_rules_preview_draft(
            self._rules_preview_token, self._loaded_template_id,
            html, presentation,
        )

    def _editor_changed(self) -> None:
        if not self._loading:
            self._refresh_local_rules_preview()
            self._publish_unsaved_preview()
            self._update_status()

    def _update_status(self) -> None:
        current = self.db.get_rule_template(self._loaded_template_id) if self._loaded_template_id else None
        is_active = bool(current is not None and int(current["is_active"]))
        self.template_combo.setProperty("ruleTemplateActive", is_active)
        active_style = (
            "QComboBox { background: #256849; color: #F3FFF7; "
            "border: 1px solid #44AE7D; }"
            if is_active else ""
        )
        if self.template_combo.styleSheet() != active_style:
            self.template_combo.setStyleSheet(active_style)
        self.activate_template_btn.setHidden(is_active)
        self.delete_template_btn.setHidden(self.template_combo.count() <= 1)
        if self._rules_overlay_url is not None:
            name = str(current["name"]) if current is not None else ""
            kind = "активный" if is_active else "неактивный"
            self.rules_preview_target_label.setText(
                f"Предпросмотр: «{name}» ({kind} шаблон). "
                "Рабочий оверлей OBS останется без изменений."
                if current is not None else ""
            )
            if current is not None and self._loaded_template_id is not None:
                self.preview_rules_obs_btn.setToolTip(
                    "Откроется сохранённый вариант выбранного шаблона. "
                    "Несохранённые изменения видны после «Сохранить». "
                    "Ссылка: " + self._selected_template_preview_url(
                        self._loaded_template_id
                    )
                )
        self.dirty_label.setText(
            ("Есть несохранённые изменения" if self._is_dirty() else "Сохранено")
            if current is not None else ""
        )

    def _save_current(self) -> bool:
        if self._loaded_template_id is None:
            return True
        html = self.editor.toHtml() if self.editor.toPlainText().strip() else ""
        presentation = self._obs_presentation_values()
        presentation_dirty = presentation != self._loaded_obs_presentation
        try:
            if presentation_dirty:
                self.db.save_rule_template_presentation(
                    self._loaded_template_id, presentation
                )
            self.db.save_rule_template(self._loaded_template_id, html)
        except Exception as exc:
            QMessageBox.critical(self, "Правила аукциона", str(exc))
            return False
        self._new_template_ids.discard(self._loaded_template_id)
        self._loaded_html = html
        self._loaded_obs_presentation = presentation
        if presentation_dirty:
            self._loaded_obs_explicit = True
        self._publish_unsaved_preview()
        self._update_status()
        return True

    def _choose_save_action(self) -> str:
        """Prompt only for explicitly saving edits to an existing template."""
        box = QMessageBox(self)
        box.setWindowTitle("Сохранение шаблона правил")
        box.setText("Как сохранить изменения в шаблоне правил?")
        replace_btn = box.addButton("Заменить текущий", QMessageBox.AcceptRole)
        new_btn = box.addButton("Сохранить как новый", QMessageBox.ActionRole)
        cancel_btn = box.addButton("Отмена", QMessageBox.RejectRole)
        box.setDefaultButton(cancel_btn)
        box.exec()
        clicked = box.clickedButton()
        if clicked is replace_btn:
            return "replace"
        if clicked is new_btn:
            return "new"
        return "cancel"

    def _save_with_choice(self) -> bool:
        """P11-G: reuse existing DB save/create paths; no second persistence."""
        if (self._loaded_template_id is None or not self._is_dirty()
                or self._loaded_template_id in self._new_template_ids):
            return self._save_current()

        action = self._choose_save_action()
        if action == "replace":
            return self._save_current()
        if action != "new":
            return False

        template = self.db.get_rule_template(self._loaded_template_id)
        if template is None:
            QMessageBox.warning(self, "Шаблоны правил", "Шаблон правил не найден.")
            return False
        name, ok = QInputDialog.getText(
            self, "Сохранить как новый", "Название нового шаблона:",
            text=f"{template['name']} (копия)",
        )
        if not ok:
            return False
        html = self.editor.toHtml() if self.editor.toPlainText().strip() else ""
        try:
            new_id = self.db.create_rule_template(
                name, content_html=html, make_active=False
            )
            if (
                self._loaded_obs_explicit
                or self._obs_presentation_values() != self._loaded_obs_presentation
            ):
                self.db.save_rule_template_presentation(
                    new_id, self._obs_presentation_values()
                )
        except Exception as exc:
            QMessageBox.warning(self, "Шаблоны правил", str(exc))
            return False
        # Source template and active/on-air Rules remain unchanged.
        self._reload_templates(selected_id=new_id)
        return True

    def _confirm_discard_or_save(self) -> bool:
        if not self._is_dirty():
            return True
        box = QMessageBox(self)
        box.setWindowTitle("Несохранённые изменения")
        box.setText("В текущем шаблоне есть несохранённые изменения.")
        save = box.addButton("Сохранить", QMessageBox.AcceptRole)
        discard = box.addButton("Не сохранять", QMessageBox.DestructiveRole)
        cancel = box.addButton("Отмена", QMessageBox.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is save:
            return self._save_current()
        if clicked is discard:
            return True
        assert clicked is cancel or clicked is None
        return False

    def _create_template(self) -> None:
        if not self._confirm_discard_or_save():
            return
        name, ok = QInputDialog.getText(self, "Новый шаблон", "Название шаблона:")
        if not ok:
            return
        try:
            template_id = self.db.create_rule_template(name, make_active=False)
        except Exception as exc:
            QMessageBox.warning(self, "Шаблоны правил", str(exc))
            return
        self._new_template_ids.add(template_id)
        self._reload_templates(selected_id=template_id)

    def _rename_template(self) -> None:
        if self._loaded_template_id is None or not self._confirm_discard_or_save():
            return
        template = self.db.get_rule_template(self._loaded_template_id)
        if template is None:
            return
        name, ok = QInputDialog.getText(
            self,
            "Переименовать шаблон",
            "Название шаблона:",
            text=str(template["name"]),
        )
        if not ok:
            return
        try:
            self.db.rename_rule_template(self._loaded_template_id, name)
        except Exception as exc:
            QMessageBox.warning(self, "Шаблоны правил", str(exc))
            return
        self._reload_templates(selected_id=self._loaded_template_id)

    def _delete_template(self) -> None:
        if self._loaded_template_id is None or not self._confirm_discard_or_save():
            return
        templates = self.db.list_rule_templates()
        if len(templates) <= 1:
            QMessageBox.information(self, "Шаблоны правил", "Последний шаблон правил удалить нельзя.")
            return
        template = self.db.get_rule_template(self._loaded_template_id)
        if template is None:
            return
        answer = QMessageBox.question(
            self,
            "Удаление шаблона",
            f"Удалить шаблон «{template['name']}»?\n\n"
            "Уже созданные снимки правил в аукционах не изменятся.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            active_id = self.db.delete_rule_template(self._loaded_template_id)
        except Exception as exc:
            QMessageBox.warning(self, "Шаблоны правил", str(exc))
            return
        self._reload_templates(selected_id=active_id)

    def _confirm_save_before_activation(self) -> bool:
        """Do not silently persist a dirty template when the user activates it."""
        box = QMessageBox(self)
        box.setWindowTitle("Несохранённые изменения")
        box.setText(
            "В выбранном шаблоне есть несохранённые изменения. "
            "Сохранить их и сделать шаблон активным?"
        )
        save = box.addButton("Сохранить и активировать", QMessageBox.AcceptRole)
        cancel = box.addButton("Отмена", QMessageBox.RejectRole)
        box.setDefaultButton(cancel)
        box.exec()
        return box.clickedButton() is save

    def _make_active(self) -> None:
        if self._loaded_template_id is None:
            return
        if self._is_dirty():
            if not self._confirm_save_before_activation():
                return
            if not self._save_current():
                return
        try:
            self.db.set_active_rule_template(self._loaded_template_id)
        except Exception as exc:
            QMessageBox.warning(self, "Шаблоны правил", str(exc))
            return
        self._reload_templates(selected_id=self._loaded_template_id)

    @staticmethod
    def _set_color_button(button: QPushButton, color: QColor, label: str) -> None:
        if not color.isValid():
            return
        value = color.name().upper()
        luminance = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()
        text = "#111111" if luminance > 165 else "#FFFFFF"
        button.setText(f"{label}: {value}")
        button.setProperty("selectedColor", value)
        button.setStyleSheet(
            f"background: {value}; color: {text}; border: 1px solid #60666c; font-weight: 600;"
        )

    def _choose_color(self, pipette: bool) -> None:
        # Only foreground color remains editable in the toolbar. Existing
        # rich-text background highlights are preserved in saved template HTML.
        button = self.text_color_btn
        current = QColor(str(button.property("selectedColor") or "#FFFFFF"))
        selected = pick_screen_color(self) if pipette else QColorDialog.getColor(
            current,
            self,
            "Цвет текста",
        )
        if selected is None or not selected.isValid():
            return
        fmt = QTextCharFormat()
        fmt.setForeground(selected)
        self._set_color_button(button, selected, "Цвет текста")
        self._merge_char_format(fmt)

    def _merge_char_format(self, fmt: QTextCharFormat) -> None:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            self.editor.mergeCurrentCharFormat(fmt)
        else:
            cursor.mergeCharFormat(fmt)
            self.editor.setTextCursor(cursor)
        self.editor.setFocus(Qt.OtherFocusReason)

    def _apply_font_family(self, font: QFont) -> None:
        if self._loading:
            return
        fmt = QTextCharFormat()
        fmt.setFontFamilies([font.family()])
        self._merge_char_format(fmt)

    def _apply_font_size(self, value: int) -> None:
        if self._loading:
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(value))
        self._merge_char_format(fmt)

    def _apply_bold(self, enabled: bool) -> None:
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if enabled else QFont.Weight.Normal)
        self._merge_char_format(fmt)

    def _apply_italic(self, enabled: bool) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(bool(enabled))
        self._merge_char_format(fmt)

    def _apply_underline(self, enabled: bool) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(bool(enabled))
        self._merge_char_format(fmt)

    def _apply_paragraph_style(self, _index: int) -> None:
        if self._loading:
            return
        style = self.style_combo.currentData()
        fmt = QTextCharFormat()
        if style == "heading":
            fmt.setFontPointSize(24.0)
            fmt.setFontWeight(QFont.Weight.Bold)
        elif style == "subheading":
            fmt.setFontPointSize(18.0)
            fmt.setFontWeight(QFont.Weight.Bold)
        else:
            fmt.setFontPointSize(float(self.size_spin.value()))
            fmt.setFontWeight(QFont.Weight.Normal)
        self._merge_char_format(fmt)

    def _make_list(self, style: QTextListFormat.Style) -> None:
        cursor = self.editor.textCursor()
        list_format = QTextListFormat()
        list_format.setStyle(style)
        list_format.setIndent(max(1, cursor.blockFormat().indent() + 1))
        cursor.createList(list_format)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus(Qt.OtherFocusReason)

    def _sync_format_controls(self) -> None:
        if self._loading:
            return
        fmt = self.editor.currentCharFormat()
        with QSignalBlocker(self.bold_btn):
            self.bold_btn.setChecked(fmt.fontWeight() >= int(QFont.Weight.Bold))
        with QSignalBlocker(self.italic_btn):
            self.italic_btn.setChecked(fmt.fontItalic())
        with QSignalBlocker(self.underline_btn):
            self.underline_btn.setChecked(fmt.fontUnderline())
        families = fmt.fontFamilies()
        family = (families[0] if families else "") or self.editor.currentFont().family()
        if family:
            with QSignalBlocker(self.font_combo):
                self.font_combo.setCurrentFont(QFont(family))
        size = fmt.fontPointSize()
        if size > 0:
            with QSignalBlocker(self.size_spin):
                self.size_spin.setValue(max(6, min(96, int(round(size)))))

    def closeEvent(self, event) -> None:
        if self._confirm_discard_or_save():
            if self._rules_preview_token is not None:
                self.db.clear_rules_preview_selection(self._rules_preview_token)
            event.accept()
        else:
            event.ignore()
