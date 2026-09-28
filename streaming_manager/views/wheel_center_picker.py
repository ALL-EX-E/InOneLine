from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class WheelCenterPickerDialog(QDialog):
    uploadRequested = Signal()
    localAssetSelected = Signal(int)
    remoteEmoteSelected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("wheelCenterPicker")
        self.setMinimumWidth(430)
        self.setMaximumWidth(540)
        self.resize(470, 390)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.upload_btn = QPushButton("Загрузить своё изображение")
        self.upload_btn.clicked.connect(self.uploadRequested.emit)
        layout.addWidget(self.upload_btn)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setMinimumHeight(280)

        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(4, 4, 4, 4)
        self.grid.setHorizontalSpacing(5)
        self.grid.setVerticalSpacing(5)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.grid_host)
        layout.addWidget(self.scroll, 1)

        self.status = QLabel("Загрузка смайликов…")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setProperty("muted", True)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self._local_items: list[dict] = []
        self._remote_items: list[object] = []
        self._buttons: list[QToolButton] = []

    @staticmethod
    def _icon_from_path(path: str) -> QIcon:
        pixmap = QPixmap(str(path or ""))
        if pixmap.isNull():
            return QIcon()
        return QIcon(pixmap)

    @staticmethod
    def _icon_from_bytes(raw: bytes) -> QIcon:
        pixmap = QPixmap()
        if not raw or not pixmap.loadFromData(bytes(raw)):
            return QIcon()
        return QIcon(pixmap)

    def set_local_items(self, items: list[dict]) -> None:
        self._local_items = list(items or [])
        self._rebuild()

    def set_remote_items(self, items: list[object]) -> None:
        self._remote_items = list(items or [])
        self.status.setText("")
        self.status.setVisible(False)
        self._rebuild()

    def set_loading_message(self, text: str) -> None:
        self.status.setText(str(text or ""))
        self.status.setVisible(bool(text))

    def set_busy(self, busy: bool) -> None:
        self.upload_btn.setEnabled(not busy)
        self.grid_host.setEnabled(not busy)
        if busy:
            self.set_loading_message("Загрузка изображения…")

    def _clear_grid(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._buttons.clear()

    def _button(self, icon: QIcon, tooltip: str, callback) -> QToolButton:
        button = QToolButton()
        button.setIcon(icon)
        button.setIconSize(QSize(50, 50))
        button.setFixedSize(62, 62)
        button.setToolTip(str(tooltip or ""))
        button.setAutoRaise(False)
        button.clicked.connect(callback)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._buttons.append(button)
        return button

    def _rebuild(self) -> None:
        self._clear_grid()
        cells: list[QToolButton] = []

        for item in self._local_items:
            try:
                asset_id = int(item.get("asset_id"))
            except (TypeError, ValueError):
                continue
            path = str(item.get("path") or "")
            if not path or not Path(path).exists():
                continue
            icon = self._icon_from_path(path)
            if icon.isNull():
                continue
            name = str(item.get("name") or Path(path).name)
            cells.append(
                self._button(
                    icon,
                    name,
                    lambda _checked=False, value=asset_id: self.localAssetSelected.emit(value),
                )
            )

        for item in self._remote_items:
            raw = bytes(getattr(item, "thumbnail_bytes", b"") or b"")
            icon = self._icon_from_bytes(raw)
            if icon.isNull():
                continue
            name = str(getattr(item, "name", "") or "")
            source = str(getattr(item, "source", "") or "")
            tooltip = name if not source else f"{name} · {source}"
            cells.append(
                self._button(
                    icon,
                    tooltip,
                    lambda _checked=False, value=item: self.remoteEmoteSelected.emit(value),
                )
            )

        columns = 6
        for index, button in enumerate(cells):
            self.grid.addWidget(button, index // columns, index % columns)

        if not cells and not self.status.isVisible():
            self.set_loading_message("Нет доступных изображений.")
