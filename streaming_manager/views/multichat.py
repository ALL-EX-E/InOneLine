from __future__ import annotations

"""D41 operator view; independent Twitch/YouTube status and shared OBS feed."""

from datetime import datetime
from math import isfinite

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QTextCursor
from .common import make_wide_step_control

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
    def __init__(self, db, state, api, *, twitch_status_provider=None,
                 youtube_status_provider=None, youtube_channel_provider=None,
                 youtube_choice_provider=None, youtube_reopen=None):
        super().__init__()
        self.db, self.state, self.api = db, state, api
        self.twitch_status_provider = twitch_status_provider
        self.youtube_status_provider = youtube_status_provider
        self.youtube_channel_provider = youtube_channel_provider
        self.youtube_choice_provider = youtube_choice_provider
        self.youtube_reopen = youtube_reopen
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
        self.delay.setAccessibleName("Задержка сообщений, секунд")
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
        form.addRow("Лимит сообщений", make_wide_step_control(
            self.limit,
            up_tooltip="Увеличить лимит сообщений",
            down_tooltip="Уменьшить лимит сообщений",
        ))
        form.addRow(self.show_time)
        settings.addWidget(general)
        connections = QGroupBox("Подключения и OBS")
        connections_layout = QVBoxLayout(connections)
        self.connection_status = QLabel("Twitch и YouTube: ожидание подключения чата")
        self.connection_status.setWordWrap(True)
        connections_layout.addWidget(self.connection_status)
        self.twitch_obs = QCheckBox("Отображать чат Twitch в OBS")
        self.twitch_obs.setChecked(db.get_setting("multichat_twitch_obs", "1") == "1")
        self.state.set_obs_enabled("twitch", self.twitch_obs.isChecked())
        self.twitch_obs.toggled.connect(self._on_twitch_obs)
        connections_layout.addWidget(self.twitch_obs)
        self.youtube_obs = QCheckBox("Отображать чат YouTube в OBS")
        self.youtube_obs.setChecked(db.get_setting("multichat_youtube_obs", "1") == "1")
        self.state.set_obs_enabled("youtube", self.youtube_obs.isChecked())
        self.youtube_obs.toggled.connect(self._on_youtube_obs)
        connections_layout.addWidget(self.youtube_obs)
        self.youtube_select = QPushButton("Выбрать трансляцию YouTube")
        if youtube_reopen:
            self.youtube_select.clicked.connect(youtube_reopen)
        self.youtube_select.hide()
        connections_layout.addWidget(self.youtube_select)
        self.buffer_warning = QLabel("")
        self.buffer_warning.setWordWrap(True)
        self.buffer_warning.hide()
        connections_layout.addWidget(self.buffer_warning)
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
        self._applied_delay = 0.0
        self._on_delay()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(250)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()
        self.refresh()

    def _on_youtube_obs(self, enabled):
        self.state.set_obs_enabled("youtube", enabled)
        self.db.set_setting("multichat_youtube_obs", "1" if enabled else "0")

    def _on_twitch_obs(self, enabled):
        self.state.set_obs_enabled("twitch", enabled)
        self.db.set_setting("multichat_twitch_obs", "1" if enabled else "0")

    def _on_delay(self):
        try:
            seconds = float(self.delay.text().strip().replace(",", "."))
            if not isfinite(seconds):
                raise ValueError("nonfinite")
            self.state.configure(delay=seconds)
        except (ValueError, TypeError):
            # The previous saved value remains active; do not persist a bad
            # draft or silently leave it looking like the current setting.
            self.delay.setText(str(self._applied_delay))
            self.delay.setToolTip("Исправлено: требуется неотрицательное число секунд")
            return
        self._applied_delay = seconds
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
        if self.twitch_status_provider is not None:
            try:
                status = str(self.twitch_status_provider())
            except Exception:
                status = "Twitch: не удалось получить состояние подключения."
            if self.youtube_status_provider is not None:
                try:
                    yt_status = str(self.youtube_status_provider())
                    yt_channel = str(self.youtube_channel_provider() or "") if self.youtube_channel_provider else ""
                    if yt_channel:
                        yt_status += f" Авторизованный канал: {yt_channel}."
                except Exception:
                    yt_status = "YouTube: состояние временно недоступно."
            else:
                yt_status = "YouTube: не подключён."
            info = status + "\n" + yt_status
            if self.connection_status.text() != info:
                self.connection_status.setText(info)
            choose = bool(self.youtube_choice_provider()) if self.youtube_choice_provider else False
            self.youtube_select.setVisible(choose)
        snapshot = self.state.snapshot()
        overflow = snapshot["overflow_count"]
        warning = ("Буфер задержки переполнен: для сохранения сообщений "
                   "часть сообщений показана раньше установленного времени "
                   f"({overflow})." if overflow else "")
        if self.buffer_warning.text() != warning:
            self.buffer_warning.setText(warning)
            self.buffer_warning.setVisible(bool(warning))
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
