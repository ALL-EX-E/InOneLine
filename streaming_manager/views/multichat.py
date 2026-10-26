from __future__ import annotations

"""D41 operator Twitch chat view; shared state retained for future platforms."""

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


from .chat_rich_feed import ChatRichFeed as _ChatFeed

class MultichatTab(QWidget):
    def __init__(self, db, state, api, *, twitch_status_provider=None):
        super().__init__()
        self.db, self.state, self.api = db, state, api
        self.twitch_status_provider = twitch_status_provider
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
        self.show_platform_icons = QCheckBox("Показывать значки платформ")
        self.show_platform_icons.setChecked(
            db.get_setting("multichat_show_platform_icons", "1") == "1"
        )
        self.show_platform_icons.toggled.connect(self._on_platform_icons)
        form.addRow(self.show_platform_icons)
        settings.addWidget(general)
        connections = QGroupBox("Подключения и OBS")
        connections_layout = QVBoxLayout(connections)
        self.connection_status = QLabel("Twitch: ожидание подключения чата через EventSub")
        self.connection_status.setWordWrap(True)
        connections_layout.addWidget(self.connection_status)
        self.twitch_obs = QCheckBox("Отображать чат Twitch в OBS")
        self.twitch_obs.setChecked(db.get_setting("multichat_twitch_obs", "1") == "1")
        self.state.set_obs_enabled("twitch", self.twitch_obs.isChecked())
        self.twitch_obs.toggled.connect(self._on_twitch_obs)
        connections_layout.addWidget(self.twitch_obs)
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
        self.state.configure(
            limit=self.limit.value(), show_time=self.show_time.isChecked(),
            show_platform_icons=self.show_platform_icons.isChecked(),
        )
        self._applied_delay = 0.0
        self._on_delay()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(250)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()
        self.refresh()

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

    def _on_platform_icons(self, enabled):
        self.state.configure(show_platform_icons=enabled)
        self.db.set_setting("multichat_show_platform_icons", "1" if enabled else "0")
        self.refresh()

    def refresh(self):
        if self.twitch_status_provider is not None:
            try:
                status = str(self.twitch_status_provider())
            except Exception:
                status = "Twitch: не удалось получить состояние подключения."
            info = status
            if self.connection_status.text() != info:
                self.connection_status.setText(info)
        snapshot = self.state.snapshot()
        # Preload platform media as soon as Twitch connects, before any text
        # messages appear; the Qt image pool retains free slots for live chat.
        self.feed.prefetch_media(snapshot.get("media_preload", {}).get("twitch", ()))
        overflow = snapshot["overflow_count"]
        warning = ("Буфер задержки переполнен: для сохранения сообщений "
                   "часть сообщений показана раньше установленного времени "
                   f"({overflow})." if overflow else "")
        if self.buffer_warning.text() != warning:
            self.buffer_warning.setText(warning)
            self.buffer_warning.setVisible(bool(warning))
        # Keep multi-provider RAM/API contracts intact, but the current UI is Twitch-only.
        messages = [m for m in snapshot["messages"] if m["platform"] == "twitch"]
        key = (
            snapshot["show_time"], snapshot["show_platform_icons"],
            repr(messages),
        )
        if key == self._last_render:
            return
        self._last_render = key
        self.feed.display(
            messages,
            show_time=snapshot["show_time"],
            show_icons=snapshot["show_platform_icons"],
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        direction = QBoxLayout.LeftToRight if self.width() >= 800 else QBoxLayout.TopToBottom
        if self.columns.direction() != direction:
            self.columns.setDirection(direction)
