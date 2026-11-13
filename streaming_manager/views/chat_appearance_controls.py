from __future__ import annotations

"""D41-06 controls. Same in-tab draft for live Qt; OBS reads saved values only."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QSpinBox,
    QVBoxLayout, QWidget,
)

from ..chat_appearance import (
    normalize_common, normalize_twitch, saved_appearance, save_appearance,
    save_common_appearance, save_twitch_appearance, save_youtube_appearance,
)
from ..media import MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
from ..media import media_asset_available
from .common import (
    ScrollSafeComboBox, ScrollSafeFontComboBox, ScrollSafeSpinBox,
    make_screen_color_picker_button, make_wide_step_control, pick_screen_color,
)


class ChatAppearanceEditor(QWidget):
    changed = Signal(object, object, bool)  # Twitch style, common style, test-visible
    saved_changed = Signal(object)  # Emitted only after the Save succeeded

    def __init__(self, db, *, import_background=None, visibility_control=None,
                 parent=None, platform="twitch", section="all"):
        super().__init__(parent)
        if section not in {"all", "platform", "common"}:
            raise ValueError("Unknown appearance editor section: " + str(section))
        self.db = db
        self.platform = platform
        self.section = section
        self._has_platform = section in {"all", "platform"}
        # The legacy YouTube editor never exposed shared multichat controls.
        self._has_common = section == "common" or (
            section == "all" and platform != "youtube"
        )
        self._import_background = import_background
        self._loading = True
        appearance = saved_appearance(db)
        self.saved = {platform: appearance[platform], "common": appearance["common"]}
        self.test_visible = False
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(7)

        self.custom_widgets = []
        if self._has_platform:
            _platform_box, platform_form = self._group(
                root, "Оформление " + ("YouTube" if platform == "youtube" else "Twitch")
            )
            self.mode = ScrollSafeComboBox()
            self.mode.addItem("Оригинальное оформление", "original")
            self.mode.addItem("Настраиваемое оформление", "custom")
            platform_form.addRow("Режим:", self.mode)
            self.mode.currentIndexChanged.connect(self._changed)
            self.text_font = self._font(platform_form, "Шрифт сообщения:")
            self.text_size = self._number(platform_form, "Размер сообщения:", 6, 96, " px")
            self.text_color = self._color(platform_form, "Цвет текста:")
            self.name_font = self._font(platform_form, "Шрифт никнейма:")
            self.name_size = self._number(platform_form, "Размер никнейма:", 6, 96, " px")
            self.name_color = self._color(platform_form, "Цвет никнейма:")
            self.card_color = self._color(platform_form, "Цвет карточки:")
            self.card_opacity = self._number(platform_form, "Непрозрачность карточки:", 0, 100, " %")
            self.card_border_color = self._color(platform_form, "Цвет рамки:")
            self.card_border_width = self._number(platform_form, "Толщина рамки:", 0, 12, " px")
            self.card_radius = self._number(platform_form, "Скругление:", 0, 64, " px")
            self.avatar_size = self._number(platform_form, "Размер аватара:", 8, 96, " px")
            self.badge_size = self._number(platform_form, "Размер значков ролей:", 8, 64, " px")
            self.test = QPushButton("Показать тестовое сообщение")
            self.test.clicked.connect(self._toggle_test)
            platform_form.addRow(self.test)

        if self._has_common:
            _common_box, common_form = self._group(root, "Общий фон и контур")
            self.background = ScrollSafeComboBox()
            self.background.addItem("Прозрачный", "transparent")
            self.background.addItem("Цвет", "color")
            self.background.addItem("Свой (изображение / GIF / видео)", "media")
            self.background.currentIndexChanged.connect(self._changed)
            common_form.addRow("Фон:", self.background)
            self.background_color = self._color(common_form, "Цвет фона:")
            self.background_opacity = self._number(common_form, "Непрозрачность:", 0, 100, " %")
            self.bg_color_control = self.background_color.parentWidget()
            self.bg_color_label = common_form.labelForField(self.bg_color_control)
            self.bg_opacity_control = self.background_opacity.parentWidget()
            self.bg_opacity_label = common_form.labelForField(self.bg_opacity_control)
            self.media_combo = ScrollSafeComboBox()
            self.media_combo.currentIndexChanged.connect(self._changed)
            common_form.addRow("Из библиотеки:", self.media_combo)
            self.media_label = common_form.labelForField(self.media_combo)
            self.media_import = QPushButton("Добавить фон…")
            self.media_import.setEnabled(import_background is not None)
            self.media_import.clicked.connect(self._import_media)
            common_form.addRow(self.media_import)
            self.background_fit = ScrollSafeComboBox()
            self.background_fit.addItem("Вписать целиком", "contain")
            self.background_fit.addItem("Заполнить область", "cover")
            self.background_fit.currentIndexChanged.connect(self._changed)
            common_form.addRow("Масштабирование:", self.background_fit)
            self.fit_label = common_form.labelForField(self.background_fit)
            self.glow = QCheckBox("Светящийся контур")
            self.glow.toggled.connect(self._changed)
            common_form.addRow(self.glow)
            self.glow_color = self._color(common_form, "Цвет контура:")
            self.glow_color_control = self.glow_color.parentWidget()
            self.glow_color_label = common_form.labelForField(self.glow_color_control)
            self.visibility = visibility_control or ScrollSafeComboBox()
            self.visibility.addItem("Не показывать", "hidden")
            self.visibility.addItem("Скрывать, когда чат пуст", "hide_empty")
            self.visibility.addItem("Показывать постоянно", "always")
            self.visibility.currentIndexChanged.connect(self._changed)
            if visibility_control is None:
                common_form.addRow("Видимость OBS:", self.visibility)

        # Keep the long Reset label from squeezing Save at narrow widths.
        foot = QVBoxLayout()
        self.status = QLabel("Сохранено")
        foot.addWidget(self.status)
        buttons = QHBoxLayout()
        self.reset_button = QPushButton("Сбросить по умолчанию")
        self.reset_button.setToolTip(
            "Вернуть исходный вид чата в локальный "
            "предпросмотр. Для OBS нажмите «Сохранить»."
        )
        self.reset_button.clicked.connect(self.reset_to_defaults)
        buttons.addWidget(self.reset_button, 1)
        self.save_button = QPushButton("Сохранить")
        self.save_button.setProperty("primary", True)
        self.save_button.clicked.connect(self.save)
        buttons.addWidget(self.save_button)
        foot.addLayout(buttons)
        root.addLayout(foot)
        self._apply_values(self.saved)
        self._loading = False
        self._changed()

    def _group(self, parent, title):
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        toggle = QCheckBox("Показывать настройки")
        toggle.setChecked(True)
        layout.addWidget(toggle)
        area = QWidget()
        form = QFormLayout(area)
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.addWidget(area)
        toggle.toggled.connect(area.setVisible)
        parent.addWidget(box)
        return box, form

    def _number(self, form, title, lo, hi, suffix):
        spin = ScrollSafeSpinBox()
        spin.setRange(lo, hi)
        spin.setSuffix(suffix)
        spin.valueChanged.connect(self._changed)
        widget = make_wide_step_control(
            spin, up_tooltip='Увеличить: ' + title,
            down_tooltip='Уменьшить: ' + title,
        )
        form.addRow(title, widget)
        if hasattr(self, "custom_widgets") and title != "Непрозрачность:":
            if title not in ("",):
                self.custom_widgets.append(widget)
                self.custom_widgets.append(form.labelForField(widget))
        return spin

    def _font(self, form, title):
        font = ScrollSafeFontComboBox()
        font.currentFontChanged.connect(self._font_changed)
        form.addRow(title, font)
        self.custom_widgets.extend([font, form.labelForField(font)])
        return font

    def _font_changed(self, _font):
        # A missing system font must not silently rewrite a saved preference.
        # Clear the original requested family only after a real user edit.
        if not self._loading:
            sender = self.sender()
            if sender is not None:
                sender.setProperty("requestedFamily", None)
            self._changed()

    def _color(self, form, title):
        controls = QWidget()
        layout = QHBoxLayout(controls)
        layout.setContentsMargins(0, 0, 0, 0)
        choose = QPushButton()
        choose.setMinimumWidth(70)
        pipette = make_screen_color_picker_button(
            "Выбрать цвет с экрана (левый клик — принять, Escape — отмена)"
        )
        layout.addWidget(choose)
        layout.addWidget(pipette)
        layout.addStretch()
        form.addRow(title, controls)
        choose.clicked.connect(lambda _=False, btn=choose, name=title: self._pick(btn, name, False))
        pipette.clicked.connect(lambda _=False, btn=choose, name=title: self._pick(btn, name, True))
        if hasattr(self, "custom_widgets") and title not in ("Цвет фона:", "Цвет контура:"):
            self.custom_widgets.extend([controls, form.labelForField(controls)])
        return choose

    def _set_color(self, button, value):
        button.setProperty("selectedColor", value)
        button.setText(value)
        button.setStyleSheet("background-color:" + value + ";color:" +
                             ("#000000" if QColor(value).lightness() > 150 else "#FFFFFF") + ";")

    def _pick(self, button, title, pipette):
        initial = QColor(button.property("selectedColor") or "#FFFFFF")
        color = pick_screen_color(self) if pipette else QColorDialog.getColor(initial, self, title)
        if color is not None and color.isValid():
            self._set_color(button, color.name().upper())
            self._changed()

    @staticmethod
    def _set_combo(combo, value):
        index = combo.findData(value)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _refresh_media(self, selected):
        self.db.sync_managed_media_category(MEDIA_CATEGORY_OVERLAY_BACKGROUNDS)
        self.media_combo.blockSignals(True)
        self.media_combo.clear()
        self.media_combo.addItem("— выберите фон —", None)
        for asset in self.db.list_media_assets(MEDIA_CATEGORY_OVERLAY_BACKGROUNDS):
            available = media_asset_available(self.db.path.parent, asset)
            self.media_combo.addItem(
                asset.display_name if available else "Недоступен: " + asset.display_name,
                asset.id,
            )
        if selected is not None and self.media_combo.findData(selected) < 0:
            self.media_combo.addItem("Недоступный фон #" + str(selected), selected)
        self._set_combo(self.media_combo, selected)
        self.media_combo.blockSignals(False)

    def _import_media(self):
        if self._import_background is not None:
            self._import_background(self._media_imported, self)

    def _media_imported(self, asset_id):
        self._refresh_media(int(asset_id))
        self._set_combo(self.background, "media")
        self._changed()

    def _apply_values(self, data):
        self._loading = True
        t, c = data[self.platform], data["common"]
        if self._has_platform:
            self._set_combo(self.mode, t["mode"])
            for widget, key in ((self.text_font,"text_font"),(self.name_font,"name_font")):
                widget.setCurrentFont(QFont(t[key]))
                widget.setProperty("requestedFamily", t[key])
            for widget,key in (
                (self.text_size,"text_size"),(self.name_size,"name_size"),
                (self.card_opacity,"card_opacity"),(self.card_border_width,"card_border_width"),
                (self.card_radius,"card_radius"),(self.avatar_size,"avatar_size"),
                (self.badge_size,"badge_size"),
            ):
                widget.setValue(t[key])
            for widget,key in (
                (self.text_color,"text_color"),(self.name_color,"name_color"),
                (self.card_color,"card_color"),(self.card_border_color,"card_border_color"),
            ):
                self._set_color(widget,t[key])
        if self._has_common:
            self._set_combo(self.background, c["background"])
            self._set_combo(self.background_fit, c["background_fit"])
            self._set_combo(self.visibility, c["visibility"])
            self.background_opacity.setValue(c["background_opacity"])
            self._set_color(self.background_color,c["background_color"])
            self._set_color(self.glow_color,c["glow_color"])
            self.glow.setChecked(c["glow"])
            self._refresh_media(c["background_media_id"])
        self._loading = False

    def values(self):
        t = self.saved[self.platform]
        if self._has_platform:
            t = {
            "mode":self.mode.currentData(), "text_font":(
                self.text_font.property("requestedFamily") or self.text_font.currentFont().family()
            ),
            "text_size":self.text_size.value(), "text_color":self.text_color.property("selectedColor"),
            "name_font":(
                self.name_font.property("requestedFamily") or self.name_font.currentFont().family()
            ),
            "name_size":self.name_size.value(), "name_color":self.name_color.property("selectedColor"),
            "card_color":self.card_color.property("selectedColor"),
            "card_opacity":self.card_opacity.value(),
            "card_border_color":self.card_border_color.property("selectedColor"),
            "card_border_width":self.card_border_width.value(),
            "card_radius":self.card_radius.value(),
            "avatar_size":self.avatar_size.value(), "badge_size":self.badge_size.value(),
            }
        c = self.saved["common"]
        if self._has_common:
            c = {
            "background":self.background.currentData(),
            "background_color":self.background_color.property("selectedColor"),
            "background_opacity":self.background_opacity.value(),
            "background_media_id":self.media_combo.currentData(),
            "background_fit":self.background_fit.currentData(),
            "glow":self.glow.isChecked(),
            "glow_color":self.glow_color.property("selectedColor"),
            "visibility":self.visibility.currentData(),
            }
        return {self.platform:t,"common":c}

    def is_dirty(self):
        return self.values() != self.saved

    def _changed(self, *_args):
        if self._loading:
            return
        data = self.values()
        if self._has_platform:
            custom = data[self.platform]["mode"] == "custom"
            for widget in self.custom_widgets:
                if widget is not None:
                    widget.setVisible(custom)
        if self._has_common:
            bg = data["common"]["background"]
            for widget in (
                self.bg_color_control, self.bg_color_label,
                self.bg_opacity_control, self.bg_opacity_label,
            ):
                if widget is not None:
                    widget.setVisible(bg == "color")
            for widget in (self.media_combo,self.media_label,self.media_import,
                           self.background_fit,self.fit_label):
                if widget is not None:
                    widget.setVisible(bg == "media")
            for widget in (self.glow_color_control, self.glow_color_label):
                if widget is not None:
                    widget.setVisible(data["common"]["glow"])
        self.status.setText("Есть несохранённые изменения" if self.is_dirty() else "Сохранено")
        self.changed.emit(data[self.platform], data["common"], self.test_visible)

    def _toggle_test(self):
        self.test_visible = not self.test_visible
        self.test.setText("Закрыть предпросмотр" if self.test_visible else
                          "Показать тестовое сообщение")
        self._changed()

    def reset_to_defaults(self):
        """Only replace appearance draft; OBS reads saved settings until Save."""
        target = (
            "общего фона и контура мультичата"
            if self.section == "common"
            else ("YouTube" if self.platform == "youtube" else "Twitch") + "-чата"
        )
        choice = QMessageBox.question(
            self,
            "Сбросить оформление чата",
            "Вернуть настройки внешнего вида " + target + " к значениям "
            "по умолчанию?\n\n"
            "Сначала изменится только предпросмотр в программе. "
            "Чтобы применить оформление в OBS, нажмите «Сохранить».\n"
            "Сообщения и фоны из библиотеки не удаляются.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        self._apply_values({
            self.platform: (
                normalize_twitch({}) if self._has_platform else self.saved[self.platform]
            ),
            "common": normalize_common({}) if self._has_common else self.saved["common"],
        })
        self._changed()

    def save(self):
        data = self.values()
        try:
            if self.section == "common":
                self.saved = {
                    self.platform: data[self.platform],
                    "common": save_common_appearance(self.db, data["common"]),
                }
            elif self.section == "platform" and self.platform == "twitch":
                self.saved = {
                    "twitch": save_twitch_appearance(self.db, data["twitch"]),
                    "common": data["common"],
                }
            elif self.platform == "youtube":
                self.saved = {"youtube": save_youtube_appearance(self.db, data["youtube"]),
                              "common": data["common"]}
            else:
                self.saved = save_appearance(self.db,data["twitch"],data["common"])
        except Exception as exc:
            QMessageBox.warning(self,"Не удалось сохранить оформление",str(exc))
            return False
        self._changed()
        self.saved_changed.emit(self.saved)
        return True

    def discard(self):
        self._apply_values(self.saved)
        self._changed()
