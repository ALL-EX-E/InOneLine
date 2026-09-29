from __future__ import annotations

import math
import time
from datetime import datetime, timezone

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush, QColor, QFontMetricsF, QMovie, QPainter, QPainterPath, QPen, QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..wheel_motion import wheel_motion_progress

try:
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
except ImportError:  # pragma: no cover
    QOpenGLWidget = QWidget


class AuctionWheelWidget(QOpenGLWidget):
    """GPU-backed локальное изображение того же колеса, которое получает OBS."""

    spinFinished = Signal()
    centerClicked = Signal()

    PALETTE = (
        "#4FC3F7",
        "#FF8A65",
        "#BA68C8",
        "#81C784",
        "#FFD54F",
        "#64B5F6",
        "#F06292",
        "#4DB6AC",
        "#A1887F",
        "#90A4AE",
        "#9575CD",
        "#DCE775",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self._payload: dict = {}
        self._wheel_cache: QPixmap | None = None
        self._wheel_cache_key = None
        self._center_image_path = ""
        self._center_image_pixmap: QPixmap | None = None
        self._center_image_movie: QMovie | None = None
        self._spin_id = None
        self._spin_start_monotonic: float | None = None
        self._finished_emitted_for_spin = None

        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # QOpenGLWidget может сохранять содержимое framebuffer между кадрами.
        # Во время вращения нужен полный кадр каждый раз, иначе текст внизу
        # способен визуально наслаиваться. В idle постоянный repaint не нужен.
        try:
            self.setUpdateBehavior(
                QOpenGLWidget.UpdateBehavior.NoPartialUpdate
            )
        except (AttributeError, TypeError):
            pass

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.setInterval(8)
        self._timer.timeout.connect(self._advance_frame)

    def mousePressEvent(self, event):
        rect = self.rect().adjusted(10, 10, -10, -68)
        side = max(2, min(rect.width(), rect.height()))
        center = rect.center()
        center_radius = (side / 2.0) * 0.12
        pos = event.position()
        dx = float(pos.x()) - float(center.x())
        dy = float(pos.y()) - float(center.y())
        if dx * dx + dy * dy <= center_radius * center_radius:
            self.centerClicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def set_center_image_path(self, path: str | None) -> None:
        normalized = str(path or "")
        if normalized == self._center_image_path:
            return

        previous_movie = self._center_image_movie
        self._center_image_movie = None
        if previous_movie is not None:
            previous_movie.stop()
            # QMovie can keep the GIF/WebP file handle open on Windows until
            # its source is cleared. Release it immediately when the selected
            # center changes instead of waiting for deferred QObject deletion.
            previous_movie.setFileName("")
            previous_movie.deleteLater()

        self._center_image_path = normalized
        pixmap = QPixmap(normalized) if normalized else QPixmap()
        self._center_image_pixmap = None if pixmap.isNull() else pixmap

        suffix = normalized.lower().rsplit(".", 1)[-1] if "." in normalized else ""
        if normalized and suffix in {"gif", "webp"}:
            movie = QMovie(normalized)
            if movie.isValid() and movie.frameCount() != 1:
                movie.setParent(self)
                movie.frameChanged.connect(lambda _frame: self.update())
                self._center_image_movie = movie
                movie.start()
            else:
                movie.deleteLater()
        self.update()

    def set_payload(self, payload: dict | None):
        payload = dict(payload or {})
        animation = payload.get("animation") or {}
        spin_id = animation.get("spin_id")

        # Сопоставляем серверное UTC-время старта с monotonic clock ровно один
        # раз на spin_id. Повторный refresh payload не перезапускает локальную
        # временную шкалу и больше не создаёт микрорывки каждые 0,5 секунды.
        if spin_id != self._spin_id:
            self._spin_id = spin_id
            self._spin_start_monotonic = None
            self._finished_emitted_for_spin = None
            started_at = animation.get("started_at")
            if spin_id and started_at:
                try:
                    start_dt = datetime.fromisoformat(str(started_at))
                    delay = (
                        start_dt - datetime.now(timezone.utc)
                    ).total_seconds()
                    self._spin_start_monotonic = time.perf_counter() + delay
                except (TypeError, ValueError):
                    self._spin_start_monotonic = time.perf_counter()

        old_sectors = self._payload.get("sectors") or []
        new_sectors = payload.get("sectors") or []
        if old_sectors != new_sectors:
            self._wheel_cache = None
            self._wheel_cache_key = None

        self._payload = payload
        self.update()
        self._sync_frame_timer()

    def _sync_frame_timer(self) -> None:
        animation = self._payload.get("animation") or {}
        spin_id = animation.get("spin_id")
        if not spin_id:
            if self._timer.isActive():
                self._timer.stop()
            return

        _progress, complete = self._animation_progress()
        if complete:
            if self._timer.isActive():
                self._timer.stop()
            return

        if not self._timer.isActive():
            self._timer.start()

    def showEvent(self, event):
        super().showEvent(event)
        # Не ограничиваем локальное колесо фиксированными ~60 FPS.
        # Таймер подстраивается под реальную частоту экрана (до 240 Гц).
        try:
            refresh_rate = float(self.screen().refreshRate())
        except Exception:
            refresh_rate = 60.0
        if refresh_rate <= 1.0:
            refresh_rate = 60.0
        refresh_rate = min(240.0, max(60.0, refresh_rate))
        self._timer.setInterval(
            max(4, int(round(1000.0 / refresh_rate)))
        )

    def is_spinning(self) -> bool:
        animation = self._payload.get("animation") or {}
        if not animation.get("spin_id"):
            return False
        _progress, complete = self._animation_progress()
        return not complete

    def _advance_frame(self):
        animation = self._payload.get("animation") or {}
        spin_id = animation.get("spin_id")
        if not spin_id:
            self._timer.stop()
            return

        _progress, complete = self._animation_progress()
        if complete:
            self._timer.stop()
            # Сначала дорисовываем последний кадр, потом разрешаем
            # AuctionTab обновить таблицы/кнопки.
            self.update()
            if self._finished_emitted_for_spin != spin_id:
                self._finished_emitted_for_spin = spin_id
                QTimer.singleShot(0, self.spinFinished.emit)
            return

        self.update()

    def _animation_progress(self) -> tuple[float, bool]:
        animation = self._payload.get("animation") or {}
        duration_ms = max(1, int(animation.get("duration_ms") or 8000))
        if not animation.get("spin_id"):
            return 0.0, True
        if self._spin_start_monotonic is None:
            return 0.0, False

        elapsed_ms = (
            time.perf_counter() - self._spin_start_monotonic
        ) * 1000.0
        if elapsed_ms <= 0:
            return 0.0, False
        progress = min(1.0, elapsed_ms / duration_ms)
        return progress, progress >= 1.0

    def _rotation(self) -> tuple[float, bool]:
        animation = self._payload.get("animation") or {}
        target = float(animation.get("target_rotation") or 0.0)
        if not animation.get("spin_id"):
            return 0.0, True
        progress, complete = self._animation_progress()
        duration_ms = max(1, int(animation.get("duration_ms") or 8000))
        visual_progress = wheel_motion_progress(progress, duration_ms)
        return target * visual_progress, complete

    @staticmethod
    def _short_title(text: str, limit: int = 22) -> str:
        text = str(text or "").strip()
        if len(text) <= limit:
            return text
        return text[: max(1, limit - 1)].rstrip() + "…"

    @staticmethod
    def _fit_sector_font(
        painter: QPainter,
        title: str,
        max_width: float,
        max_height: float,
        preferred_size: float,
    ):
        """Подбирает шрифт для полного названия с переносом слов."""
        title = str(title or "").strip()
        base = painter.font()
        base.setBold(True)
        flags = Qt.AlignCenter | Qt.TextWordWrap
        size = max(6.0, float(preferred_size))
        while size >= 6.0:
            base.setPointSizeF(size)
            metrics = QFontMetricsF(base)
            bounds = metrics.boundingRect(
                QRectF(0, 0, max(8.0, max_width), 2000),
                flags,
                title,
            )
            if bounds.height() <= max_height + 0.5:
                return base, flags
            size -= 0.5
        base.setPointSizeF(6.0)
        return base, flags

    def _cache_key(self, side: int, sectors: list[dict]):
        return (
            int(side),
            tuple(
                (
                    int(s.get("game_id") or 0),
                    str(s.get("title") or ""),
                    int(s.get("weight") or 0),
                )
                for s in sectors
            ),
        )

    def _build_wheel_cache(self, side: int, sectors: list[dict]) -> QPixmap:
        side = max(2, int(side))
        pixmap = QPixmap(side, side)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)

        radius = side / 2.0 - 3.0
        center = QPointF(side / 2.0, side / 2.0)
        local_rect = QRectF(
            center.x() - radius,
            center.y() - radius,
            radius * 2,
            radius * 2,
        )

        painter.setPen(QPen(QColor("#D9E1E8"), 3))
        painter.setBrush(QColor("#15181B"))
        painter.drawEllipse(local_rect.adjusted(-1, -1, 1, 1))

        if not sectors:
            painter.setPen(QPen(QColor("#4A5258"), 2))
            painter.setBrush(QColor("#25292D"))
            painter.drawEllipse(local_rect.adjusted(3, 3, -3, -3))
            painter.setPen(QColor("#AEB8C0"))
            font = painter.font()
            font.setPointSizeF(11)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                QRectF(0, 0, side, side),
                Qt.AlignCenter,
                "НЕТ ЛОТОВ",
            )
            painter.end()
            return pixmap

        effective_total = sum(
            max(0, int(s.get("weight") or 0))
            for s in sectors
        )
        if effective_total <= 0:
            effective_total = len(sectors)
            sectors = [
                {**sector, "weight": 1}
                for sector in sectors
            ]

        start_deg = 90.0
        for index, sector in enumerate(sectors):
            weight = max(0, int(sector.get("weight") or 0))
            span = (
                (weight / effective_total) * 360.0
                if effective_total
                else 0.0
            )
            color = QColor(self.PALETTE[index % len(self.PALETTE)])

            path = QPainterPath()
            path.moveTo(center)
            path.arcTo(local_rect, start_deg, -span)
            path.closeSubpath()
            painter.setPen(QPen(QColor("#15181B"), 1.0))
            painter.setBrush(QBrush(color))
            painter.drawPath(path)

            if span >= 4.0:
                # Подпись идёт вдоль радиуса сектора. Длинные названия
                # переносятся по словам и получают динамический размер шрифта.
                mid_deg = start_deg - span / 2.0
                theta = math.radians(-mid_deg)
                tx = center.x() + math.cos(theta) * radius * 0.56
                ty = center.y() + math.sin(theta) * radius * 0.56
                painter.save()
                painter.translate(tx, ty)

                text_rotation = -mid_deg
                if 90.0 < (text_rotation % 360.0) < 270.0:
                    text_rotation += 180.0
                painter.rotate(text_rotation)

                text_width = radius * 0.70
                arc_height = radius * 0.56 * math.radians(max(4.0, span))
                text_height = max(18.0, min(radius * 0.34, arc_height * 0.86))
                preferred = max(7.0, min(11.5, 7.0 + span / 11.0))
                title = str(sector.get("title") or "")
                font, flags = self._fit_sector_font(
                    painter,
                    title,
                    text_width,
                    text_height,
                    preferred,
                )
                painter.setFont(font)
                painter.setPen(QColor("#111315"))
                painter.drawText(
                    QRectF(
                        -text_width / 2.0,
                        -text_height / 2.0,
                        text_width,
                        text_height,
                    ),
                    flags,
                    title,
                )
                painter.restore()

            start_deg -= span

        painter.end()
        return pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Полностью очищаем framebuffer перед каждым новым кадром.
        # Это устраняет следы/дубли текста у QOpenGLWidget.
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor("#000000"))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # Внизу всегда резервируется отдельная зона для читаемой подписи.
        rect = self.rect().adjusted(10, 10, -10, -68)
        side = max(2, min(rect.width(), rect.height()))
        center = rect.center()
        wheel_rect = QRectF(
            center.x() - side / 2,
            center.y() - side / 2,
            side,
            side,
        )
        radius = side / 2.0

        sectors = list(self._payload.get("sectors") or [])
        key = self._cache_key(side, sectors)
        if self._wheel_cache is None or key != self._wheel_cache_key:
            self._wheel_cache = self._build_wheel_cache(side, sectors)
            self._wheel_cache_key = key

        rotation, complete = self._rotation()

        # Само сложное колесо (сотни секторов + текст) рисуется только при
        # изменении состава/размера. Каждый кадр вращает уже готовый QPixmap.
        painter.save()
        painter.translate(center)
        painter.rotate(rotation)
        painter.drawPixmap(
            QRectF(-side / 2, -side / 2, side, side),
            self._wheel_cache,
            QRectF(self._wheel_cache.rect()),
        )
        painter.restore()

        # D19: center is painted after the rotating sector layer, so it remains
        # physically stationary while the wheel spins.
        center_radius = radius * 0.12
        center_rect = QRectF(
            center.x() - center_radius,
            center.y() - center_radius,
            center_radius * 2.0,
            center_radius * 2.0,
        )
        painter.setPen(QPen(QColor("#E8EDF2"), 2))
        painter.setBrush(QColor("#25292D"))
        painter.drawEllipse(center_rect)
        center_pixmap = self._center_image_pixmap
        center_movie = self._center_image_movie
        if center_movie is not None:
            current = center_movie.currentPixmap()
            if not current.isNull():
                center_pixmap = current
        if center_pixmap is not None and not center_pixmap.isNull():
            source = QRectF(center_pixmap.rect())
            target_ratio = center_rect.width() / max(1.0, center_rect.height())
            source_ratio = source.width() / max(1.0, source.height())
            if source_ratio > target_ratio:
                new_width = source.height() * target_ratio
                source.setLeft(source.left() + (source.width() - new_width) / 2.0)
                source.setWidth(new_width)
            elif source_ratio < target_ratio:
                new_height = source.width() / target_ratio
                source.setTop(source.top() + (source.height() - new_height) / 2.0)
                source.setHeight(new_height)
            clip = QPainterPath()
            clip.addEllipse(center_rect.adjusted(1, 1, -1, -1))
            painter.save()
            painter.setClipPath(clip)
            painter.drawPixmap(center_rect, center_pixmap, source)
            painter.restore()
            painter.setPen(QPen(QColor("#E8EDF2"), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center_rect)

        pointer_y = wheel_rect.top() - 2
        pointer = QPolygonF(
            [
                QPointF(center.x() - 18, pointer_y - 22),
                QPointF(center.x() + 18, pointer_y - 22),
                QPointF(center.x(), pointer_y + 16),
            ]
        )
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.setBrush(QColor("#E53935"))
        painter.drawPolygon(pointer)

        animation = self._payload.get("animation") or {}
        winner = self._payload.get("winner")
        if animation.get("spin_id") and not complete:
            caption = "Колесо вращается…"
        elif winner:
            prefix = (
                "Выбывает"
                if str(self._payload.get("wheel_format") or "") == "elimination"
                else "Победитель"
            )
            caption = f"{prefix}: {winner.get('title', '')}"
        elif sectors:
            caption = (
                "Готово к вращению"
                if self._payload.get("ready")
                else ""
            )
        else:
            caption = "Нет лотов"

        if caption:
            caption_rect = QRectF(
                12,
                self.height() - 54,
                max(10, self.width() - 24),
                40,
            )

            # Одна непрозрачная плашка каждый кадр: текст не смешивается
            # с колесом и остаётся читаемым даже во время быстрого вращения.
            painter.setPen(QPen(QColor("#59636B"), 1))
            painter.setBrush(QColor("#15191D"))
            painter.drawRoundedRect(caption_rect, 8, 8)

            font = painter.font()
            font.setPointSizeF(12.5)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(
                caption_rect.adjusted(12, 0, -12, 0),
                Qt.AlignCenter | Qt.TextSingleLine,
                caption,
            )

