from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextListFormat,
)
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database import Database
from .common import (
    ScrollSafeComboBox,
    ScrollSafeFontComboBox,
    ScrollSafeSpinBox,
    make_wide_step_control,
    pick_screen_color,
)


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
    ):
        super().__init__(parent)
        self.db = db
        self._initial_template_id = (
            int(initial_template_id) if initial_template_id is not None else None
        )
        self._loaded_template_id: int | None = None
        self._loaded_html = ""
        self._loading = False
        self.setWindowTitle("Правила аукциона")
        self.resize(1050, 760)
        self.setMinimumSize(760, 560)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        self.active_label = QLabel()
        self.active_label.setProperty("badge", True)
        template_row = QHBoxLayout()
        template_row.addWidget(QLabel("Шаблон:"))
        self.template_combo = ScrollSafeComboBox()
        self.template_combo.setMinimumWidth(280)
        self.template_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.template_combo.currentIndexChanged.connect(self._template_index_changed)
        template_row.addWidget(self.template_combo, 1)
        template_row.addWidget(self.active_label)

        for title, handler in (
            ("Создать", self._create_template),
            ("Переименовать", self._rename_template),
            ("Удалить", self._delete_template),
            ("Сделать активным", self._make_active),
        ):
            button = QPushButton(title)
            button.clicked.connect(handler)
            template_row.addWidget(button)
        root.addLayout(template_row)

        tools1 = QHBoxLayout()
        self.undo_btn = QPushButton("Отменить")
        self.redo_btn = QPushButton("Повторить")
        self.undo_btn.clicked.connect(lambda: self.editor.undo())
        self.redo_btn.clicked.connect(lambda: self.editor.redo())
        tools1.addWidget(self.undo_btn)
        tools1.addWidget(self.redo_btn)

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
        root.addLayout(tools1)

        tools2 = QHBoxLayout()
        self.text_color_btn = QPushButton("Цвет текста")
        self.text_color_btn.clicked.connect(lambda: self._choose_color(False, False))
        self.text_color_pick_btn = QPushButton("Пипетка")
        self.text_color_pick_btn.clicked.connect(lambda: self._choose_color(False, True))
        self.highlight_color_btn = QPushButton("Выделение")
        self.highlight_color_btn.clicked.connect(lambda: self._choose_color(True, False))
        self.highlight_color_pick_btn = QPushButton("Пипетка")
        self.highlight_color_pick_btn.clicked.connect(lambda: self._choose_color(True, True))
        tools2.addWidget(self.text_color_btn)
        tools2.addWidget(self.text_color_pick_btn)
        tools2.addSpacing(8)
        tools2.addWidget(self.highlight_color_btn)
        tools2.addWidget(self.highlight_color_pick_btn)
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
        root.addLayout(tools2)

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.setPlaceholderText("Введите правила аукциона…")
        self.editor.textChanged.connect(self._editor_changed)
        self.editor.cursorPositionChanged.connect(self._sync_format_controls)
        root.addWidget(self.editor, 1)

        bottom = QHBoxLayout()
        self.dirty_label = QLabel()
        self.dirty_label.setProperty("muted", True)
        bottom.addWidget(self.dirty_label)
        bottom.addStretch()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self._save_and_close)
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
        self._set_color_button(self.highlight_color_btn, QColor("#000000"), "Выделение")


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
                prefix = "★ " if int(row["is_active"]) else ""
                self.template_combo.addItem(prefix + str(row["name"]), row_id)
                if row_id == target_id:
                    target_index = index
            if self.template_combo.count():
                self.template_combo.setCurrentIndex(target_index)
        if self.template_combo.count():
            self._load_template(int(self.template_combo.currentData()))

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
            self.editor.setHtml(self._loaded_html) if self._loaded_html else self.editor.clear()
        finally:
            self._loading = False
        self._update_status()
        self._sync_format_controls()

    def _is_dirty(self) -> bool:
        if self._loaded_template_id is None:
            return False
        current = self.editor.toHtml() if self.editor.toPlainText() or self.editor.document().blockCount() else ""
        if not self._loaded_html and not self.editor.toPlainText().strip():
            return False
        return current != self._loaded_html

    def _editor_changed(self) -> None:
        if not self._loading:
            self._update_status()

    def _update_status(self) -> None:
        current = self.db.get_rule_template(self._loaded_template_id) if self._loaded_template_id else None
        if current is None:
            self.active_label.setText("")
            self.dirty_label.setText("")
            return
        self.active_label.setText("Активный" if int(current["is_active"]) else "Неактивный")
        self.dirty_label.setText("Есть несохранённые изменения" if self._is_dirty() else "Сохранено")

    def _save_current(self) -> bool:
        if self._loaded_template_id is None:
            return True
        html = self.editor.toHtml() if self.editor.toPlainText().strip() else ""
        try:
            self.db.save_rule_template(self._loaded_template_id, html)
        except Exception as exc:
            QMessageBox.critical(self, "Правила аукциона", str(exc))
            return False
        self._loaded_html = html
        self._update_status()
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
            template_id = self.db.create_rule_template(name, make_active=True)
        except Exception as exc:
            QMessageBox.warning(self, "Шаблоны правил", str(exc))
            return
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

    def _make_active(self) -> None:
        if self._loaded_template_id is None:
            return
        if self._is_dirty() and not self._save_current():
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

    def _choose_color(self, highlight: bool, pipette: bool) -> None:
        button = self.highlight_color_btn if highlight else self.text_color_btn
        current = QColor(str(button.property("selectedColor") or ("#000000" if highlight else "#FFFFFF")))
        selected = pick_screen_color(self) if pipette else QColorDialog.getColor(
            current,
            self,
            "Цвет выделения" if highlight else "Цвет текста",
        )
        if selected is None or not selected.isValid():
            return
        fmt = QTextCharFormat()
        if highlight:
            fmt.setBackground(selected)
            self._set_color_button(button, selected, "Выделение")
        else:
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

    def _save_and_close(self) -> None:
        if self._save_current():
            self.accept()

    def closeEvent(self, event) -> None:
        if self._confirm_discard_or_save():
            event.accept()
        else:
            event.ignore()


class AuctionRulesPreviewDialog(QDialog):
    def __init__(
        self,
        *,
        title: str,
        template_name: str,
        content_html: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 620)
        self.setMinimumSize(520, 360)
        layout = QVBoxLayout(self)
        heading = QLabel(f"Шаблон: {template_name or '—'}")
        heading.setProperty("badge", True)
        layout.addWidget(heading)
        viewer = QTextEdit()
        viewer.setReadOnly(True)
        viewer.setAcceptRichText(True)
        if content_html:
            viewer.setHtml(content_html)
        else:
            viewer.setPlainText("Правила не заполнены.")
        layout.addWidget(viewer, 1)
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(close_btn)
        layout.addLayout(row)
