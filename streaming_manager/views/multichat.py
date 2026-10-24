from __future__ import annotations

"""D41 first-stage operator view; platform connections and themes follow later."""

from datetime import datetime
from math import isfinite

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QBoxLayout, QCheckBox, QFormLayout, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QSpinBox,
    QTextEdit, QVBoxLayout, QWidget,
)


class _ChatFeed(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setPlaceholderText("Ожидание сообщений")

    def wheelEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event):
        event.ignore()


class MultichatTab(QWidget):
    def __init__(self, db, state, api):
        super().__init__()
        self.db, self.state, self.api = db, state, api
        self._last_render = None
        self.columns = QBoxLayout(QBoxLayout.LeftToRight, self)
        self.columns.setContentsMargins(8, 8, 8, 8)
        self.feed = _ChatFeed()
        self.columns.addWidget(self.feed, 3)
        options_scroll = QScrollArea()
        options_scroll.setFrameShape(QFrame.NoFrame)
        options_scroll.setWidgetResizable(True)
        options_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        options_scroll.setMinimumSize(0, 0)
        settings_widget = QWidget()
        settings = QVBoxLayout(settings_widget)
        options_scroll.setWidget(settings_widget)
        self.columns.addWidget(options_scroll, 2)
        general = QGroupBox("Общие настройки")
        form = QFormLayout(general)
        self.delay = QLineEdit(db.get_setting("multichat_delay", "0"))
        self.delay.editingFinished.connect(self._on_delay)
        self.limit = QSpinBox()
        self.limit.setRange(10, 1000)
        try:
            stored_limit = int(db.get_setting("multichat_limit", "100"))
        except (ValueError, TypeError):
            stored_limit = 100
        self.limit.setValue(max(10, min(1000, stored_limit)))
        self.limit.valueChanged.connect(self._on_limit)
        self.show_time = QCheckBox("Показывать время")
        self.show_time.setChecked(db.get_setting("multichat_show_time", "1") == "1")
        self.show_time.toggled.connect(self._on_time)
        form.addRow("Задержка (сек.)", self.delay)
        form.addRow("Лимит сообщений", self.limit)
        form.addRow(self.show_time)
        settings.addWidget(general)
        connections = QGroupBox("Подключения и OBS")
        connections_layout = QVBoxLayout(connections)
        status = QLabel("Twitch и YouTube: ожидание подключения чата")
        status.setWordWrap(True)
        connections_layout.addWidget(status)
        url = f"{api.base_url}/multichat-overlay"
        self.url_edit = QLineEdit(url)
        self.url_edit.setReadOnly(True)
        connections_layout.addWidget(self.url_edit)
        actions = QHBoxLayout()
        copy = QPushButton("Копировать URL")
        copy.clicked.connect(lambda: QApplication.clipboard().setText(url))
        preview = QPushButton("Проверить в браузере")
        preview.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        actions.addWidget(copy)
        actions.addWidget(preview)
        connections_layout.addLayout(actions)
        settings.addWidget(connections)
        settings.addStretch()
        # Platform-specific appearance controls remain hidden until adapters
        # can confirm that their channels are actually connected.
        self.state.configure(limit=self.limit.value(), show_time=self.show_time.isChecked())
        self._on_delay()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(250)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()
        self.refresh()

    def _on_delay(self):
        try:
            seconds = float(self.delay.text().strip().replace(",", "."))
            if not isfinite(seconds):
                raise ValueError("nonfinite")
            self.state.configure(delay=seconds)
        except (ValueError, TypeError):
            self.delay.setToolTip("Введите неотрицательное число секунд")
            return
        self.delay.setToolTip("")
        self.db.set_setting("multichat_delay", str(seconds))

    def _on_limit(self, limit):
        self.state.configure(limit=limit)
        self.db.set_setting("multichat_limit", str(limit))
        self.refresh()

    def _on_time(self, enabled):
        self.state.configure(show_time=enabled)
        self.db.set_setting("multichat_show_time", "1" if enabled else "0")
        self.refresh()

    def refresh(self):
        snapshot = self.state.snapshot()
        messages = snapshot["messages"]
        key = (snapshot["show_time"], tuple(
            (m["platform"], m["source_id"], m["external_id"], m["author"], m["text"])
            for m in messages
        ))
        if key == self._last_render:
            return
        self._last_render = key
        lines = []
        for m in messages:
            value = m["sent_at"] if m["sent_at"] is not None else m["received_at"]
            stamp = datetime.fromtimestamp(value).strftime("%H:%M") if snapshot["show_time"] and value is not None else ""
            lines.append(f"{m['platform']}  {m['author']} {stamp}  {m['text']}")
        self.feed.setPlainText("\n".join(lines))
        self.feed.moveCursor(QTextCursor.End)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        direction = QBoxLayout.LeftToRight if self.width() >= 800 else QBoxLayout.TopToBottom
        if self.columns.direction() != direction:
            self.columns.setDirection(direction)
