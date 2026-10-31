from __future__ import annotations

"""Common background of the existing Qt chat feed: registered media, no new importer."""

from pathlib import Path

from PySide6.QtCore import QEvent, QSize, Qt, QUrl
from PySide6.QtGui import QColor, QPalette, QPixmap, QMovie
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QLabel, QStackedLayout, QSizePolicy,
)

from ..chat_appearance import normalize_common
from ..media import (
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, media_asset_available,
    resolve_media_asset_path,
)


class _BackdropLabel(QLabel):
    """A pixmap must NEVER become the preferred size of its own canvas.

    QStackedLayout consults both child size hints even in StackAll mode.
    QLabel's default pixmap-sized hint produced an expanding feedback loop:
    scale background -> grow label hint -> grow frame -> scale again.
    """

    def sizeHint(self):
        return QSize(0, 0)

    def minimumSizeHint(self):
        return QSize(0, 0)


class ChatBackgroundFrame(QFrame):
    def __init__(self, db, feed, parent=None):
        super().__init__(parent)
        self.db = db
        self.feed = feed
        self._appearance = normalize_common({})
        self._source_key = None
        self._paint_key = None
        self._last_style = None
        self._original = QPixmap()
        self._movie: QMovie | None = None
        self._player: QMediaPlayer | None = None
        self._sink: QVideoSink | None = None
        self._movie_kind = ""
        stack = QStackedLayout(self)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.setStackingMode(QStackedLayout.StackAll)
        self.media = _BackdropLabel(self)
        self.media.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.media.setMinimumSize(0, 0)
        self.media.setAlignment(Qt.AlignCenter)
        self.media.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.media.hide()
        stack.addWidget(self.media)
        stack.addWidget(feed)
        # StackAll raises its *current* page above its siblings. The media
        # layer was added first, so without selecting the feed it can cover
        # every message and the local test sample in the operator preview.
        stack.setCurrentWidget(feed)
        feed.setStyleSheet("QTextEdit{background:transparent;border:none;}")
        feed.viewport().setAutoFillBackground(False)
        feed.setAttribute(Qt.WA_TranslucentBackground, True)
        feed.viewport().setAttribute(Qt.WA_TranslucentBackground, True)
        palette = QPalette(feed.palette())
        palette.setColor(QPalette.Base, QColor(0, 0, 0, 0))
        feed.setPalette(palette)
        feed.viewport().setPalette(palette)
        self.effect = QGraphicsDropShadowEffect(self)
        self.effect.setOffset(0, 0)
        self.effect.setBlurRadius(20)
        self.effect.setEnabled(False)
        self.setGraphicsEffect(self.effect)
        self.apply({}, has_content=False)

    def _stop_media(self):
        if self._movie is not None:
            self._movie.stop()
            self._movie.deleteLater()
            self._movie = None
        if self._player is not None:
            self._player.stop()
            self._player.setVideoOutput(None)
            self._player.deleteLater()
            self._player = None
        if self._sink is not None:
            self._sink.deleteLater()
            self._sink = None
        self._movie_kind = ""
        self._source_key = None
        self._paint_key = None
        self._original = QPixmap()
        self.media.hide()
        self.media.clear()

    def _load_media(self, path: Path, key):
        self._stop_media()
        suffix = path.suffix.lower()
        if suffix == ".gif":
            self._movie = QMovie(str(path), parent=self)
            if not self._movie.isValid():
                self._stop_media()
                return
            self._movie_kind = "gif"
            movie = self._movie
            movie.frameChanged.connect(
                lambda _frame, target=movie: self._update_movie(target)
            )
            self._source_key = key
            movie.start()
        elif suffix in {".mp4", ".webm"}:
            self._movie_kind = "video"
            sink = QVideoSink(self)
            player = QMediaPlayer(self)
            self._sink = sink
            self._player = player
            sink.videoFrameChanged.connect(self._update_video)
            player.setVideoOutput(sink)
            player.setLoops(QMediaPlayer.Infinite)
            # No QAudioOutput: never play audio from a decorative video.
            self._source_key = key
            player.setSource(QUrl.fromLocalFile(str(path)))
            player.play()
        else:
            self._original = QPixmap(str(path))
            if self._original.isNull():
                self._stop_media()
                return
            self._movie_kind = "image"
            self._source_key = key
            self._paint_media()

    def _update_movie(self, target):
        if self._movie is target:
            pixmap = target.currentPixmap()
            if not pixmap.isNull():
                self._original = pixmap
                self._paint_media()

    def _update_video(self, frame):
        if self._movie_kind == "video" and frame.isValid():
            image = frame.toImage()
            if not image.isNull():
                self._original = QPixmap.fromImage(image)
                self._paint_media()

    def _paint_media(self):
        """Render once per new frame, size or fit. Never restack on each timer tick.

        The operator refreshes every 250 ms. Rebuilding a full-size pixmap
        and changing QStackedLayout z-order on each refresh caused unbounded
        Qt repaints with media backgrounds, even for static PNG/JPG.
        """
        if self._original.isNull() or self._source_key is None:
            return
        size = self.size()
        width, height = max(1, size.width()), max(1, size.height())
        fit = self._appearance["background_fit"]
        key = (self._source_key, self._original.cacheKey(), width, height, fit)
        if key == self._paint_key:
            return
        aspect = Qt.KeepAspectRatio if fit == "contain" else Qt.KeepAspectRatioByExpanding
        scaled = self._original.scaled(width, height, aspect, Qt.SmoothTransformation)
        if fit == "cover":
            x = max(0, (scaled.width() - width) // 2)
            y = max(0, (scaled.height() - height) // 2)
            scaled = scaled.copy(x, y, width, height)
        self.media.setPixmap(scaled)
        self._paint_key = key
        if self.media.isHidden():
            self.media.show()
            # StackAll may raise a newly shown QLabel over the QTextEdit.
            # Select the one existing operator feed once; never lower/raise
            # per animation frame or per 250 ms refresh.
            stack = self.layout()
            if isinstance(stack, QStackedLayout) and stack.currentWidget() is not self.feed:
                stack.setCurrentWidget(self.feed)
            self.feed.raise_()

    def apply(self, values, *, has_content):
        common = normalize_common(values)
        self._appearance = common
        show_shell = has_content or common["visibility"] == "always"
        self.setProperty("chatHasContent", bool(has_content))
        if common["background"] == "color" and show_shell:
            color = QColor(common["background_color"])
            alpha = round(255 * common["background_opacity"] / 100)
            background = "rgba({},{},{},{})".format(
                color.red(),color.green(),color.blue(),alpha
            )
        else:
            background = "transparent"
        if common["glow"] and show_shell:
            c = QColor(common["glow_color"])
            stroke = "rgba({},{},{},160)".format(c.red(),c.green(),c.blue())
            glow_color = QColor(c.red(), c.green(), c.blue(), 148)
            if self.effect.color() != glow_color:
                self.effect.setColor(glow_color)
            if not self.effect.isEnabled():
                self.effect.setEnabled(True)
        else:
            stroke = "rgba(255,255,255,0)"
            if self.effect.isEnabled():
                self.effect.setEnabled(False)
        style = (
            "ChatBackgroundFrame {background-color:" + background +
            ";border:1px solid " + stroke + ";border-radius:8px;}"
        )
        if style != self._last_style:
            self._last_style = style
            self.setStyleSheet(style)
        path = None
        if common["background"] == "media" and show_shell and common["background_media_id"]:
            asset = self.db.get_media_asset(common["background_media_id"])
            if (asset is not None
                    and asset.category == MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
                    and media_asset_available(self.db.path.parent, asset)):
                path = resolve_media_asset_path(self.db.path.parent, asset)
        if path is None:
            if self._source_key is not None:
                self._stop_media()
            return
        try:
            key = (str(path),path.stat().st_mtime_ns)
        except OSError:
            key = None
        if key is None:
            self._stop_media()
            return
        if key != self._source_key:
            self._load_media(path,key)
        else:
            self._paint_media()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self._source_key is not None:
            self._paint_media()

    def shutdown(self):
        # The parent QWidget close does not deliver ChatRichFeed.closeEvent.
        # Stop the feed and all of its network helpers explicitly, after the
        # unsaved-appearance confirmation has accepted application exit.
        self.feed.shutdown()
        self._stop_media()
