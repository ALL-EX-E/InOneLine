from __future__ import annotations

from PySide6.QtCore import QEventLoop, QPoint, QRect, Qt
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractSpinBox, QBoxLayout, QComboBox, QFontComboBox, QFormLayout,
    QHeaderView, QHBoxLayout, QPushButton, QScrollArea, QSpinBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QWidget,
)


APP_STYLE = """
QMainWindow, QWidget {
    background: #1d1f21;
    color: #e8e8e8;
    font-size: 10pt;
}
QMenuBar, QMenu { background: #1d1f21; color: #e8e8e8; }
QMenuBar::item {
    padding: 6px 12px;
}
QMenuBar::item:selected, QMenu::item:selected { background: #2d5f86; }
QMenu::item {
    padding: 8px 42px 8px 14px;
    min-width: 220px;
}
QMenu::separator {
    height: 1px;
    background: #3a3f44;
    margin: 5px 8px;
}
QTabWidget::pane { border: 1px solid #34383d; top: -1px; }
QTabBar::tab {
    background: #24272a; color: #cfd3d6; padding: 8px 15px;
    border: 1px solid #34383d; border-bottom: none;
}
QTabBar::tab:selected { background: #2f3337; color: white; }
QLineEdit, QComboBox, QFontComboBox, QDoubleSpinBox, QSpinBox, QTextEdit {
    background: #26292c; color: #f0f0f0; border: 1px solid #444a50;
    border-radius: 4px; padding: 6px;
}
QLineEdit:focus, QComboBox:focus, QFontComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus, QTextEdit:focus {
    border: 1px solid #328ac4;
}
QPushButton {
    background: #303438; color: #eeeeee; border: 1px solid #4b5157;
    border-radius: 4px; padding: 6px 12px;
}
QPushButton:hover { background: #3a4045; }
QPushButton:pressed { background: #25292d; }
QPushButton:disabled { color: #777; background: #252729; border-color: #333; }
QPushButton[primary="true"] { background: #176da5; border-color: #238dce; font-weight: 600; }
QPushButton[danger="true"] { border-color: #8a4b4b; }
QTableWidget {
    background: #202326; alternate-background-color: #24282b; color: #ededed;
    border: 1px solid #393e43; selection-background-color: #295e83;
    selection-color: white; gridline-color: #32373b;
}
QHeaderView::section {
    background: #2b2f33; color: #e8e8e8; border: none;
    border-right: 1px solid #3b4045; border-bottom: 1px solid #3b4045;
    padding: 7px 6px; font-weight: 600;
}
QCheckBox { spacing: 7px; }
QLabel[muted="true"] { color: #a7adb3; }
QLabel[badge="true"] {
    background: #2b2f33; border: 1px solid #3d444a; border-radius: 5px;
    padding: 5px 9px;
}
QPushButton[statFilter="true"] {
    background: #2b2f33;
    color: #eeeeee;
    border: 1px solid #3d444a;
    border-radius: 5px;
    padding: 5px 9px;
    font-weight: normal;
}
QPushButton[statFilter="true"]:hover {
    background: #343a3f;
    border-color: #59636b;
}
QPushButton[statFilter="true"]:checked {
    background: #176da5;
    border-color: #238dce;
    color: white;
    font-weight: 600;
}
QFrame[line="true"] { background: #383d42; max-height: 1px; }
QStatusBar { background: #181a1c; color: #bfc5ca; }
"""



def reflow_narrow_rows(
    root: QWidget,
    available_width: int,
    *,
    compact: bool,
    button_gap: int = 8,
) -> None:
    """Stack only overflowing horizontal groups in compact workspaces.

    Original directions and spacing are restored when the workspace grows.
    Expanding horizontal spacers are temporarily removed from stacked rows so
    they cannot turn into large vertical gaps. Explicitly hidden widgets are
    excluded from width measurement; Qt's layouts also omit them from geometry.
    """
    if root.layout() is None:
        return

    box_states = getattr(root, "_responsive_box_layout_states", None)
    if box_states is None:
        box_states = {}
        root._responsive_box_layout_states = box_states
    form_states = getattr(root, "_responsive_form_layout_states", None)
    if form_states is None:
        form_states = {}
        root._responsive_form_layout_states = form_states

    layouts = []
    seen_layouts = set()
    seen_widgets = set()

    def collect_widget(widget: QWidget) -> None:
        if widget is None or id(widget) in seen_widgets:
            return
        seen_widgets.add(id(widget))
        if (
            widget.inherits("QAbstractItemView")
            or widget.inherits("QAbstractButton")
            or widget.inherits("QComboBox")
            or widget.inherits("QAbstractSpinBox")
        ):
            return
        if isinstance(widget, QTabWidget):
            for index in range(widget.count()):
                collect_widget(widget.widget(index))
            return
        if isinstance(widget, QScrollArea):
            if widget.widget() is not None:
                collect_widget(widget.widget())
            return
        child_layout = widget.layout()
        if child_layout is not None:
            collect_layout(child_layout)
        for child_widget in widget.children():
            if isinstance(child_widget, QWidget):
                collect_widget(child_widget)

    def collect_layout(layout) -> None:
        if layout is None or id(layout) in seen_layouts:
            return
        seen_layouts.add(id(layout))
        layouts.append(layout)
        for index in range(layout.count()):
            item = layout.itemAt(index)
            child_layout = item.layout()
            if child_layout is not None:
                collect_layout(child_layout)
            child_widget = item.widget()
            if child_widget is not None:
                collect_widget(child_widget)

    collect_layout(root.layout())

    for layout in layouts:
        if not isinstance(layout, QFormLayout):
            continue
        if layout not in form_states:
            form_states[layout] = layout.rowWrapPolicy()
        original_policy = form_states[layout]
        target = original_policy
        if compact and original_policy != QFormLayout.WrapAllRows:
            target = QFormLayout.WrapLongRows
        if layout.rowWrapPolicy() != target:
            layout.setRowWrapPolicy(target)

    def spacing_for_width(layout) -> int:
        spacing = layout.spacing()
        return spacing if spacing >= 0 else 6

    def item_width(item) -> int:
        widget = item.widget()
        if widget is not None:
            if widget.isHidden():
                return 0
            return max(
                widget.minimumWidth(),
                widget.minimumSizeHint().width(),
                widget.sizeHint().width(),
            )
        child = item.layout()
        if child is not None:
            child_parent = child.parentWidget()
            if child_parent is not None and child_parent.isHidden():
                return 0
            return preferred_width(child)
        spacer = item.spacerItem()
        if spacer is not None:
            if item.expandingDirections() & Qt.Orientation.Horizontal:
                return 0
            return max(0, item.sizeHint().width())
        return 0

    def preferred_width(layout) -> int:
        margins = layout.contentsMargins()
        widths = [
            item_width(layout.itemAt(index))
            for index in range(layout.count())
        ]
        widths = [width for width in widths if width > 0]
        if not widths:
            return margins.left() + margins.right()
        if isinstance(layout, QBoxLayout):
            state = box_states.get(layout)
            direction = state["direction"] if state else layout.direction()
            if direction in (QBoxLayout.LeftToRight, QBoxLayout.RightToLeft):
                width = sum(widths) + spacing_for_width(layout) * (len(widths) - 1)
            else:
                width = max(widths)
        else:
            width = layout.sizeHint().width() - margins.left() - margins.right()
        return max(0, width) + margins.left() + margins.right()

    for layout in reversed(layouts):
        if not isinstance(layout, QBoxLayout):
            continue
        state = box_states.get(layout)
        if state is None:
            state = {
                "direction": layout.direction(),
                "spacing": layout.spacing(),
                "removed_spacers": [],
            }
            box_states[layout] = state

        original = state["direction"]
        originally_horizontal = original in (
            QBoxLayout.LeftToRight,
            QBoxLayout.RightToLeft,
        )
        parent = layout.parentWidget()
        if parent is not None and parent.isHidden():
            continue

        if originally_horizontal:
            parent_width = (
                parent.contentsRect().width()
                if parent is not None
                else available_width
            )
            if parent_width <= 0:
                parent_width = available_width
            needs_stack = bool(
                compact
                and parent_width > 0
                and preferred_width(layout) > max(0, parent_width - 2)
            )
            target_direction = QBoxLayout.TopToBottom if needs_stack else original
            if needs_stack and layout.direction() != QBoxLayout.TopToBottom:
                for index in range(layout.count() - 1, -1, -1):
                    item = layout.itemAt(index)
                    if (
                        item.spacerItem() is not None
                        and item.expandingDirections()
                        & Qt.Orientation.Horizontal
                    ):
                        removed = layout.takeAt(index)
                        state["removed_spacers"].append((index, removed))
                state["removed_spacers"].sort(key=lambda entry: entry[0])
            elif not needs_stack and state["removed_spacers"]:
                for index, item in state["removed_spacers"]:
                    layout.insertItem(index, item)
                state["removed_spacers"].clear()

            if layout.direction() != target_direction:
                layout.setDirection(target_direction)
            target_spacing = (
                max(button_gap, state["spacing"])
                if needs_stack and state["spacing"] >= 0
                else button_gap if needs_stack else state["spacing"]
            )
            if layout.spacing() != target_spacing:
                layout.setSpacing(target_spacing)
        else:
            visible_button_count = sum(
                1
                for index in range(layout.count())
                if (widget := layout.itemAt(index).widget()) is not None
                and not widget.isHidden()
                and widget.inherits("QPushButton")
            )
            target_spacing = (
                max(button_gap, state["spacing"])
                if compact and visible_button_count > 1 and state["spacing"] >= 0
                else button_gap
                if compact and visible_button_count > 1
                else state["spacing"]
            )
            if layout.spacing() != target_spacing:
                layout.setSpacing(target_spacing)

    root.layout().activate()


def suspend_live_content_resize(
    table: QTableWidget,
    columns: tuple[int, ...],
) -> None:
    """Freeze compact columns before bulk QTableWidget population.

    ResizeToContents reacts to every content mutation while a visible table is
    being rebuilt. Switching the compact sections to Interactive preserves the
    current widths while preventing that repeated synchronous geometry work.
    """
    # QSS/system font metrics can be finalized only when the widget is polished.
    # Make every sizing pass use the current real style metrics. A second,
    # post-show pass is scheduled by MainWindow for the initial tables.
    table.ensurePolished()
    header = table.horizontalHeader()
    header.ensurePolished()
    for column in columns:
        if header.sectionResizeMode(column) != QHeaderView.Interactive:
            header.setSectionResizeMode(column, QHeaderView.Interactive)


def autosize_compact_columns_once(
    table: QTableWidget,
    columns: tuple[int, ...],
) -> None:
    """Run one explicit content-size pass per visible compact column.

    The header remains Interactive afterwards. Combined with
    resizeContentsPrecision(0), this keeps widths content-aware without leaving
    a live ResizeToContents scan attached to every subsequent setItem().
    """
    header = table.horizontalHeader()
    for column in columns:
        if table.isColumnHidden(column):
            continue
        table.resizeColumnToContents(column)
        # An empty/short table can make resizeColumnToContents() narrower than
        # the styled header text (especially after the section was switched to
        # Interactive). QHeaderView.sectionSizeHint() does not reliably include
        # stylesheet padding on Windows, which clipped the first/last glyphs.
        # Measure the actual label and add a DPI-scaled visual safety margin.
        header_item = table.horizontalHeaderItem(column)
        header_text = header_item.text() if header_item is not None else ""
        header_text_width = header.fontMetrics().horizontalAdvance(header_text)
        # Keep a deliberately larger reserve than the visible header padding.
        # On native Windows the header can be polished after the first table
        # population and the final Segoe UI metrics may grow by a few pixels.
        # 0.3.70 still clipped "ТЕКУЩАЯ" by 1 px on the user's Windows PC.
        # Four M glyphs make the reserve DPI-aware while 44 px is a safe floor.
        header_padding = max(
            44,
            header.fontMetrics().horizontalAdvance("MMMM"),
        )
        header_floor = max(
            header.minimumSectionSize(),
            header.sectionSizeHint(column),
            header_text_width + header_padding,
        )
        if table.columnWidth(column) < header_floor:
            table.setColumnWidth(column, header_floor)



class _ScreenEyedropperSession:
    """One-shot multi-monitor screen color picker used by style controls."""

    def __init__(self, parent: QWidget | None = None):
        self.loop = QEventLoop()
        self.color: QColor | None = None
        self.parent = parent
        self.overlays: list[_ScreenEyedropperOverlay] = []
        self._grabber: _ScreenEyedropperOverlay | None = None
        self._finishing = False
        if parent is not None:
            parent.destroyed.connect(self.cancel)

    def run(self) -> QColor | None:
        screens = list(QGuiApplication.screens())
        if not screens:
            return None

        # Capture every monitor before any overlay is shown so the eyedropper
        # never samples its own reticle/magnifier. Each overlay uses the cached
        # pixels for both the preview and the final selected color.
        for screen in screens:
            snapshot = screen.grabWindow(0)
            overlay = _ScreenEyedropperOverlay(screen, snapshot, self, self.parent)
            self.overlays.append(overlay)

        for overlay in self.overlays:
            overlay.show()
            overlay.raise_()

        cursor_pos = QCursor.pos()
        active = self._overlay_at(cursor_pos) or self.overlays[0]
        active.activateWindow()
        active.setFocus(Qt.ActiveWindowFocusReason)

        # A fully transparent layered window is not a reliable Windows input
        # surface: transparent pixels can be skipped by native hit testing.
        # Explicit Qt mouse/keyboard grabs make the picker independent from
        # alpha hit testing and keep left/right click + Escape reliable.
        self._grabber = active
        try:
            active.grabMouse()
            active.grabKeyboard()
            self.update_cursor(cursor_pos)
            self.loop.exec()
            return self.color
        finally:
            # Never leave a native input grab behind. This is especially
            # important when the picker is launched from QDialog.exec(): the
            # editor owns a nested modal event loop, so any abnormal picker
            # exit must still restore mouse/keyboard input to the application.
            self._cleanup()

    def _overlay_at(self, global_pos: QPoint) -> _ScreenEyedropperOverlay | None:
        for overlay in self.overlays:
            if overlay.screen.geometry().contains(global_pos):
                return overlay
        return None

    def update_cursor(self, global_pos: QPoint) -> None:
        target = self._overlay_at(global_pos)
        for overlay in self.overlays:
            if overlay is target:
                overlay.set_cursor_position(overlay.mapFromGlobal(global_pos))
            else:
                overlay.clear_cursor_position()

    def sample_global(self, global_pos: QPoint) -> QColor:
        target = self._overlay_at(global_pos)
        if target is None:
            return QColor()
        return target.sample_local(target.mapFromGlobal(global_pos))

    def accept_at(self, global_pos: QPoint) -> None:
        sampled = self.sample_global(global_pos)
        if sampled.isValid():
            self.accept(sampled)

    def accept(self, color: QColor) -> None:
        self.color = QColor(color)
        self._finish()

    def cancel(self) -> None:
        self.color = None
        self._finish()

    def _cleanup(self) -> None:
        if self._finishing:
            return
        self._finishing = True
        try:
            grabber = self._grabber
            self._grabber = None
            if grabber is not None:
                # release*() is safe only while this widget owns the grab.
                if QWidget.mouseGrabber() is grabber:
                    grabber.releaseMouse()
                if QWidget.keyboardGrabber() is grabber:
                    grabber.releaseKeyboard()
            for overlay in list(self.overlays):
                overlay.close()
            self.overlays.clear()
        finally:
            self._finishing = False

    def _finish(self) -> None:
        self._cleanup()
        if self.loop.isRunning():
            self.loop.quit()


class _ScreenEyedropperOverlay(QWidget):
    """Per-screen visual layer driven by one explicit native input grab."""

    _MAGNIFIER_SIZE = 150
    _SAMPLE_RADIUS = 7

    def __init__(
        self,
        screen,
        snapshot,
        session: _ScreenEyedropperSession,
        parent: QWidget | None = None,
    ):
        # Keep the overlay in the modal parent's window hierarchy. A top-level
        # unparented Tool can be blocked by QDialog.exec() on Windows, which
        # previously left the picker grab active and made the app impossible
        # to close normally from the auction-rules editor.
        super().__init__(
            parent,
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint,
        )
        self.screen = screen
        self.snapshot = snapshot
        self.session = session
        self._cursor: QPoint | None = None
        self._current_color = QColor("#000000")
        self.setGeometry(screen.geometry())
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.CrossCursor)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def _snapshot_point(self, local: QPoint) -> QPoint:
        logical_width = max(1, self.width())
        logical_height = max(1, self.height())
        scale_x = self.snapshot.width() / logical_width
        scale_y = self.snapshot.height() / logical_height
        x = max(0, min(self.snapshot.width() - 1, round(local.x() * scale_x)))
        y = max(0, min(self.snapshot.height() - 1, round(local.y() * scale_y)))
        return QPoint(x, y)

    def sample_local(self, local: QPoint) -> QColor:
        if self.snapshot.isNull():
            return QColor()
        point = self._snapshot_point(local)
        return self.snapshot.toImage().pixelColor(point)

    def set_cursor_position(self, local: QPoint) -> None:
        self._cursor = local
        sampled = self.sample_local(local)
        if sampled.isValid():
            self._current_color = sampled
        self.update()

    def clear_cursor_position(self) -> None:
        if self._cursor is not None:
            self._cursor = None
            self.update()

    def mouseMoveEvent(self, event):
        self.session.update_cursor(event.globalPosition().toPoint())
        event.accept()

    def mousePressEvent(self, event):
        global_pos = event.globalPosition().toPoint()
        if event.button() == Qt.LeftButton:
            self.session.accept_at(global_pos)
            event.accept()
            return
        if event.button() == Qt.RightButton:
            self.session.cancel()
            event.accept()
            return
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.session.cancel()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        # Alt+F4 / native close must terminate the nested picker loop too.
        if not self.session._finishing and self.session.loop.isRunning():
            self.session.cancel()
        event.accept()

    def paintEvent(self, event):
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Keep one almost-invisible alpha value across the whole layered
        # surface. This is visually transparent, but avoids Windows treating
        # untouched pixels as a zero-alpha click-through region. The explicit
        # mouse grab above is still the authoritative input mechanism.
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        if self._cursor is None:
            painter.end()
            return

        # Small crosshair around the exact sample point without materially
        # dimming the underlying desktop. The sampled pixels come from the
        # pre-overlay snapshot, never from this paint layer.
        cross_pen = QPen(QColor("#FFFFFF"), 1)
        painter.setPen(cross_pen)
        x, y = self._cursor.x(), self._cursor.y()
        painter.drawLine(x - 14, y, x - 4, y)
        painter.drawLine(x + 4, y, x + 14, y)
        painter.drawLine(x, y - 14, x, y - 4)
        painter.drawLine(x, y + 4, x, y + 14)

        size = self._MAGNIFIER_SIZE
        margin = 22
        left = x + margin
        top = y + margin
        if left + size > self.width():
            left = x - margin - size
        if top + size + 28 > self.height():
            top = y - margin - size - 28
        left = max(0, left)
        top = max(0, top)

        center = self._snapshot_point(self._cursor)
        radius = self._SAMPLE_RADIUS
        source = QRect(
            max(0, center.x() - radius),
            max(0, center.y() - radius),
            min(self.snapshot.width(), radius * 2 + 1),
            min(self.snapshot.height(), radius * 2 + 1),
        )
        target = QRect(left, top, size, size)
        painter.fillRect(target.adjusted(-3, -3, 3, 27), QColor(20, 20, 20, 235))
        painter.drawPixmap(target, self.snapshot, source)

        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.drawRect(target)
        center_x = target.center().x()
        center_y = target.center().y()
        painter.drawRect(center_x - 5, center_y - 5, 10, 10)

        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(
            QRect(left, top + size + 4, size, 20),
            Qt.AlignCenter,
            self._current_color.name().upper(),
        )
        painter.end()


def pick_screen_color(parent: QWidget | None = None) -> QColor | None:
    """Pick one desktop pixel. Left click confirms; Esc/right click cancels."""
    # A Qt.Tool remains a top-level native window even when it has a QWidget
    # parent, so it can still span monitors. Parenting is essential for calls
    # made from modal QDialog.exec() windows: it keeps picker overlays enabled
    # in the same modal hierarchy instead of having Qt block their input.
    return _ScreenEyedropperSession(parent).run()


def make_screen_color_picker_button(tooltip: str = "") -> QPushButton:
    """Create a square, compact eyedropper button for screen color picking."""
    button = QPushButton("⌖")
    size = max(34, button.sizeHint().height())
    button.setFixedSize(size, size)
    button.setProperty("screenColorPicker", True)
    button.setAccessibleName("Выбрать цвет с экрана")
    if tooltip:
        button.setToolTip(tooltip)
    return button


def _center(item: QTableWidgetItem) -> QTableWidgetItem:
    item.setTextAlignment(Qt.AlignCenter)
    return item

class FocusClearingWidget(QWidget):
    """Клик по пустой области страницы снимает фокус с поля ввода."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.ClickFocus)

    def mousePressEvent(self, event):
        self.setFocus(Qt.MouseFocusReason)
        super().mousePressEvent(event)

class ScrollSafeComboBox(QComboBox):
    """Не меняет выбранное значение от колеса мыши над закрытым combo."""

    def wheelEvent(self, event):
        # Игнорируем событие, чтобы QScrollArea-родитель продолжил прокрутку.
        event.ignore()

class ScrollSafeFontComboBox(QFontComboBox):
    """QFontComboBox, который не перехватывает прокрутку страницы колесом."""

    def wheelEvent(self, event):
        event.ignore()

class ScrollSafeSpinBox(QSpinBox):
    """Не меняет число колесом; размер меняется кнопками ▲/▼ или вводом."""

    def wheelEvent(self, event):
        event.ignore()

def make_wide_step_control(
    spin: QSpinBox,
    *,
    up_tooltip: str,
    down_tooltip: str,
) -> QWidget:
    """Оборачивает spinbox крупными внешними ▲/▼ с нормальным hitbox.

    Нативные стрелки QSpinBox на некоторых темах Windows визуально крупнее
    своей фактической кликабельной области. Поэтому используем тот же подход,
    который уже применяется в настройках шрифтов OBS.
    """
    spin.setButtonSymbols(
        QAbstractSpinBox.ButtonSymbols.NoButtons
    )

    wrapper = QWidget()
    layout = QHBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)

    up_btn = QPushButton("▲")
    down_btn = QPushButton("▼")
    button_size = max(36, spin.sizeHint().height())
    for button in (up_btn, down_btn):
        button.setFixedSize(button_size, button_size)
        button.setAutoRepeat(True)
        button.setAutoRepeatDelay(350)
        button.setAutoRepeatInterval(80)

    up_btn.setToolTip(up_tooltip)
    down_btn.setToolTip(down_tooltip)
    up_btn.clicked.connect(spin.stepUp)
    down_btn.clicked.connect(spin.stepDown)

    layout.addWidget(spin)
    layout.addWidget(up_btn)
    layout.addWidget(down_btn)
    return wrapper

def _selected_id(table: QTableWidget) -> int | None:
    row = table.currentRow()
    if row < 0:
        return None
    item = table.item(row, 0)
    if not item:
        return None
    try:
        return int(item.text())
    except ValueError:
        return None

