from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QMovie, QPixmap
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


class _PickerImageButton(QToolButton):
    """62px picker cell with optional QMovie-backed live preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(50, 50))
        self.setFixedSize(62, 62)
        self.setAutoRaise(False)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._movie: QMovie | None = None
        self._movie_buffer: QBuffer | None = None
        self._movie_bytes: QByteArray | None = None

    @property
    def is_animated_preview(self) -> bool:
        return self._movie is not None

    def _stop_movie(self) -> None:
        movie = self._movie
        self._movie = None
        if movie is not None:
            movie.stop()
            movie.deleteLater()
        buffer = self._movie_buffer
        self._movie_buffer = None
        if buffer is not None:
            buffer.close()
            buffer.deleteLater()
        self._movie_bytes = None

    def set_static_icon(self, icon: QIcon) -> None:
        self._stop_movie()
        self.setIcon(icon)

    def set_movie_file(self, path: str) -> bool:
        self._stop_movie()
        movie = QMovie(str(path or ""), parent=self)
        if not movie.isValid() or movie.frameCount() == 1:
            movie.deleteLater()
            return False
        movie.frameChanged.connect(self._movie_frame_changed)
        self._movie = movie
        movie.start()
        return True

    def set_movie_bytes(self, raw: bytes) -> bool:
        self._stop_movie()
        if not raw:
            return False
        payload = QByteArray(bytes(raw))
        buffer = QBuffer(self)
        buffer.setData(payload)
        if not buffer.open(QIODevice.ReadOnly):
            buffer.deleteLater()
            return False
        movie = QMovie(buffer, parent=self)
        if not movie.isValid() or movie.frameCount() == 1:
            movie.deleteLater()
            buffer.close()
            buffer.deleteLater()
            return False
        self._movie_bytes = payload
        self._movie_buffer = buffer
        self._movie = movie
        movie.frameChanged.connect(self._movie_frame_changed)
        movie.start()
        return True

    def _movie_frame_changed(self, _frame: int) -> None:
        movie = self._movie
        if movie is None:
            return
        pixmap = movie.currentPixmap()
        if not pixmap.isNull():
            self.setIcon(QIcon(pixmap))

    def stop_preview(self) -> None:
        self._stop_movie()


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
        self._buttons: list[_PickerImageButton] = []

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
                if isinstance(widget, _PickerImageButton):
                    widget.stop_preview()
                widget.deleteLater()
        self._buttons.clear()

    def _button(self, tooltip: str, callback) -> _PickerImageButton:
        button = _PickerImageButton()
        button.setToolTip(str(tooltip or ""))
        button.clicked.connect(callback)
        self._buttons.append(button)
        return button

    def _rebuild(self) -> None:
        self._clear_grid()
        cells: list[_PickerImageButton] = []

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
            button = self._button(
                name,
                lambda _checked=False, value=asset_id: self.localAssetSelected.emit(value),
            )
            suffix = Path(path).suffix.casefold()
            if suffix not in {".gif", ".webp"} or not button.set_movie_file(path):
                button.set_static_icon(icon)
            cells.append(button)

        for item in self._remote_items:
            raw = bytes(getattr(item, "thumbnail_bytes", b"") or b"")
            icon = self._icon_from_bytes(raw)
            if icon.isNull():
                continue
            name = str(getattr(item, "name", "") or "")
            source = str(getattr(item, "source", "") or "")
            tooltip = name if not source else f"{name} · {source}"
            button = self._button(
                tooltip,
                lambda _checked=False, value=item: self.remoteEmoteSelected.emit(value),
            )
            animated = bool(getattr(item, "animated", False))
            if not animated or not button.set_movie_bytes(raw):
                button.set_static_icon(icon)
            cells.append(button)

        columns = 6
        for index, button in enumerate(cells):
            self.grid.addWidget(button, index // columns, index % columns)

        if not cells and not self.status.isVisible():
            self.set_loading_message("Нет доступных изображений.")


    def closeEvent(self, event) -> None:
        self._clear_grid()
        super().closeEvent(event)
