"""Current-page focus/selection gestures, shared by the main workspace."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QApplication, QAbstractButton, QAbstractItemView, QAbstractSlider,
    QAbstractSpinBox, QFrame, QGroupBox, QLabel, QLineEdit, QPlainTextEdit,
    QComboBox, QScrollArea, QStackedWidget, QTabBar, QTextEdit, QWidget,
)


class PageFocusClearFilter(QObject):
    """Leave interactive controls and transient windows their ordinary events."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    @staticmethod
    def _contains(page, widget):
        return widget is not None and (widget is page or page.isAncestorOf(widget))

    @staticmethod
    def _editing_table(widget, page):
        while widget is not None and widget is not page:
            if isinstance(widget, QAbstractItemView):
                return widget.state() == QAbstractItemView.EditingState
            widget = widget.parentWidget()
        return False

    @staticmethod
    def _neutral_background(widget, page):
        # Only known passive containers qualify; custom drawing/input widgets
        # must keep their own mouse handling. A viewport can be a plain QWidget
        # too, so reject an interactive ancestor before accepting its type.
        ancestor = widget
        while ancestor is not None and ancestor is not page:
            if isinstance(ancestor, (
                QAbstractButton, QAbstractItemView, QAbstractSlider, QAbstractSpinBox,
                QComboBox, QLineEdit, QTextEdit, QPlainTextEdit, QTabBar,
            )):
                return False
            ancestor = ancestor.parentWidget()
        if isinstance(widget, QLabel):
            return widget.textInteractionFlags() == Qt.NoTextInteraction
        if isinstance(widget, QGroupBox):
            return not widget.isCheckable()
        return widget is page or type(widget) in (
            QWidget, QFrame, QScrollArea, QStackedWidget,
        )

    @staticmethod
    def _invalid_spinbox(widget, page):
        while widget is not None and widget is not page:
            if isinstance(widget, QAbstractSpinBox):
                return not widget.hasAcceptableInput()
            widget = widget.parentWidget()
        return False

    def _clear(self, page):
        focus = QApplication.focusWidget()
        if self._contains(page, focus) and not self._invalid_spinbox(focus, page):
            # Focus-out first lets an ordinary cell editor commit its text
            # before clearing its current index. Invalid numeric drafts retain
            # focus instead of being silently corrected by QAbstractSpinBox.
            page.setFocus(Qt.OtherFocusReason)
        for view in page.findChildren(QAbstractItemView):
            if view.isVisibleTo(page) and view.state() != QAbstractItemView.EditingState:
                selection = view.selectionModel()
                if selection is not None:
                    # Existing history/auction handlers read currentRow() from
                    # selectionChanged, so invalidate current first.
                    selection.clearCurrentIndex()
                    selection.clearSelection()

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind not in (QEvent.ShortcutOverride, QEvent.KeyPress, QEvent.MouseButtonPress):
            return False
        if not isinstance(watched, QWidget) or watched.window() is not self.window:
            return False
        app = QApplication.instance()
        if app.activePopupWidget() is not None or app.activeModalWidget() is not None:
            return False
        if app.activeWindow() not in (None, self.window):
            return False
        page = self.window._current_main_page()
        if page is None:
            return False
        if kind == QEvent.MouseButtonPress:
            if event.button() != Qt.LeftButton or event.modifiers() != Qt.NoModifier:
                return False
            scroll = self.window.tabs.currentWidget()
            workspace_background = isinstance(scroll, QScrollArea) and watched in (
                scroll, scroll.viewport(),
            )
            if not workspace_background and not (
                self._contains(page, watched) and self._neutral_background(watched, page)
            ):
                return False
            # QApplication runs filters in reverse installation order. The
            # existing native guard was installed before MainWindow, so honor
            # it before consuming a background press here.
            guard = getattr(app, "_streaming_input_guard", None)
            if guard is not None and guard.eventFilter(watched, event):
                return True
            self._clear(page)
            # Do not let a passive custom container handle the same click twice.
            event.accept()
            return True
        if event.key() != Qt.Key_Escape or event.modifiers() != Qt.NoModifier:
            return False
        focus = app.focusWidget()
        if self._editing_table(focus, page):
            return False
        if kind == QEvent.ShortcutOverride:
            event.accept()
            return True
        self._clear(page)
        event.accept()
        return True
