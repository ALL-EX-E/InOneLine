from __future__ import annotations

"""D41-04 native Qt feed with bounded, off-GUI media loading.

The operator and OBS consume the same RAM snapshot.  Qt uses its existing
QTextEdit/QTextDocument (not a second browser process) and QMovie for motion.
No remote HTML, JavaScript or user-provided local paths are interpreted.
"""

import base64
import hashlib
import html
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QImage, QMovie, QPainter, QTextCursor, QTextDocument
from PySide6.QtWidgets import QTextEdit

from ..chat_graphics import safe_image_url
from ..remote_image import download_external_image

_GLITCH = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
<circle cx="512" cy="512" r="512" fill="#9146ff"/>
<path fill="#fff" d="M692.9 535 617 607h-76l-66.5 63v-63H389V337.2h303.9V535zM370 301.2l-95 89.9v323.8h114v89.9l95-89.9h76L730.9 553V301.2H370zM636 403h-38v107.9h38V403zm-142.5-.5h38v107.9h-38V402.5z"/>
</svg>"""
_MAX_CACHE_ITEMS = 96
_MAX_CACHE_BYTES = 14 * 1024 * 1024
_MAX_LOADED_IMAGE = 2 * 1024 * 1024
_MAX_ACTIVE_MOVIES = 16


def _escape(value) -> str:
    return html.escape(str(value or ""), quote=True)


def _resource_url(url: str) -> str:
    return "iol-chat-media:" + hashlib.sha256(url.encode("utf-8")).hexdigest()


def _fetch_chat_image(url: str):
    result = download_external_image(url)
    if len(result.image_bytes) > _MAX_LOADED_IMAGE:
        return None
    # Decode static media in the background, not the GUI event loop.
    # Read first frame of both static and animated images OFF the GUI thread.
    # Keep its dimensions so inline content preserves the provider aspect ratio.
    image = QImage.fromData(result.image_bytes)
    if image.isNull():
        return None
    image = image.scaled(48,48,Qt.KeepAspectRatio,Qt.SmoothTransformation)
    return result, image


class ChatRichFeed(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setPlaceholderText("Ожидание сообщений Twitch")
        self._pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="TwitchChatImage")
        self._jobs: dict[str, object] = {}
        # Value: (raw bytes, decoded small QImage, QMovie, QBuffer, animated)
        self._cache: OrderedDict[str, tuple] = OrderedDict()
        self._failed: set[str] = set()
        self._cache_bytes = 0
        self._active_urls: set[str] = set()
        self._wanted_urls: set[str] = set()
        self._preload_candidates: tuple[str, ...] = ()
        self._visible_movie_count = 0
        self._rows: list[dict] = []
        self._show_time = True
        self._show_icons = True
        self._signature = None
        self._platform_image = None
        self._make_platform_image()
        self._poll = QTimer(self)
        # 75 ms responsiveness while loading, without an EventSub/GUI network wait.
        self._poll.setInterval(75)
        self._poll.timeout.connect(self._finish_downloads)
        self._poll.start()

    def _make_platform_image(self):
        # QtSvg is supplied by the existing PySide6 install. Avoid a network
        # download of the official Twitch Glitch platform-identification icon.
        from PySide6.QtSvg import QSvgRenderer
        svg = QSvgRenderer(QByteArray(_GLITCH))
        if not svg.isValid():
            return
        image = QImage(44, 44, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        svg.render(painter)
        painter.end()
        self._platform_image = image

    def prefetch_media(self, urls) -> None:
        """Warm a few common assets while the chat is idle.

        Never occupy all three image workers: a new viewer/emote needs one
        immediately available worker even during background preloading.
        """
        choices = tuple(dict.fromkeys(
            url for raw in list(urls)[:24]
            if (url := safe_image_url(raw))
        ))
        if choices != self._preload_candidates:
            self._preload_candidates = choices
        self._maybe_prefetch()

    def _maybe_prefetch(self):
        inflight = sum(1 for url in self._jobs if url in self._preload_candidates)
        for url in self._preload_candidates:
            if inflight >= 2 or len(self._jobs) >= 8:
                break
            if url not in self._jobs and url not in self._cache and url not in self._failed:
                self._enqueue(url)
                if url in self._jobs:
                    inflight += 1

    def _enqueue(self, url: str):
        if (
            not safe_image_url(url)
            or url in self._cache or url in self._jobs or url in self._failed
            or len(self._jobs) >= 24
        ):
            return
        self._jobs[url] = self._pool.submit(_fetch_chat_image, url)
        if self._poll.interval() != 75:
            self._poll.setInterval(75)

    def _finish_downloads(self):
        changed = False
        for url, future in list(self._jobs.items()):
            if not future.done():
                continue
            del self._jobs[url]
            try:
                payload = future.result()
            except Exception:
                payload = None
            if payload is None:
                if len(self._failed) < 1024:
                    self._failed.add(url)
                continue
            asset, image = payload
            self._cache[url] = (asset.image_bytes, image, None, None, bool(asset.animated))
            self._cache.move_to_end(url)
            self._cache_bytes += len(asset.image_bytes)
            changed = changed or url in self._wanted_urls
        while (len(self._cache) > _MAX_CACHE_ITEMS or
               self._cache_bytes > _MAX_CACHE_BYTES):
            url, (raw, _image, movie, buffer, _animated) = self._cache.popitem(last=False)
            self._cache_bytes -= len(raw)
            if movie is not None:
                movie.stop()
                movie.deleteLater()
            if buffer is not None:
                buffer.deleteLater()
        if changed:
            self._draw()
        self._maybe_prefetch()
        if not self._jobs and self._poll.interval() != 300:
            self._poll.setInterval(300)

    def _image_tag(self, url: str, fallback: str, *, size: int, is_content: bool):
        url = safe_image_url(url)
        if not url:
            return _escape(fallback) if is_content else ""
        self._wanted_urls.add(url)
        if url not in self._cache:
            self._enqueue(url)
            return _escape(fallback) if is_content else ""
        if self._cache[url][4]:
            if self._visible_movie_count >= _MAX_ACTIVE_MOVIES:
                return _escape(fallback) if is_content else ""
            self._visible_movie_count += 1
        self._active_urls.add(url)
        res = _resource_url(url)
        preview = self._cache[url][1]
        width = (max(1, round(size * preview.width() / preview.height()))
                 if preview is not None and preview.height() > 0 else size)
        return f'<img src="{res}" height="{size}" width="{width}" />'

    def display(self, rows: list[dict], *, show_time: bool, show_icons: bool):
        signature = (
            bool(show_time), bool(show_icons),
            repr(rows),  # bounded snapshot; no persistence or extra state
        )
        if signature == self._signature:
            return
        self._signature = signature
        self._rows = list(rows)
        self._show_time = bool(show_time)
        self._show_icons = bool(show_icons)
        self._draw()

    def _draw(self):
        self._active_urls = set()
        self._wanted_urls = set()
        self._visible_movie_count = 0
        paragraphs = []
        for row in self._rows:
            header = []
            if self._show_icons and self._platform_image is not None:
                header.append('<img src="iol-chat-twitch-logo:" height="18" width="18" />')
            avatar = self._image_tag(row.get("avatar_url",""),"",size=24,is_content=False)
            if avatar:
                header.append(avatar)
            badges = row.get("badges")
            if isinstance(badges, (tuple,list)):
                for badge in badges[:16]:
                    if isinstance(badge, dict):
                        icon = self._image_tag(badge.get("url",""),"",size=18,is_content=False)
                        if icon:
                            header.append(icon)
            color = str(row.get("color") or "")
            if (len(color) != 7 or color[0] != "#" or
                    any(c not in "0123456789abcdefABCDEF" for c in color[1:])):
                color = "#FFFFFF"
            header.append(f'<b><span style="color:{color}">{_escape(row.get("author"))}</span></b>')
            if self._show_time:
                value = row.get("sent_at")
                if value is None:
                    value = row.get("received_at")
                try:
                    stamp = datetime.fromtimestamp(float(value)).strftime("%H:%M")
                except (ValueError, OverflowError, TypeError, OSError):
                    stamp = ""
                if stamp:
                    header.append(f'<span style="color:#cccccc">{stamp}</span>')
            body = []
            fragments = row.get("fragments") or []
            if isinstance(fragments, (list,tuple)) and fragments:
                for frag in fragments[:256]:
                    if not isinstance(frag,dict):
                        continue
                    if frag.get("kind") == "image":
                        body.append(self._image_tag(
                            frag.get("url",""),frag.get("text",""),
                            size=28,is_content=True,
                        ))
                    else:
                        body.append(_escape(frag.get("text","")))
            else:
                body.append(_escape(row.get("text")))
            paragraphs.append(
                '<p style="background-color:#303030;color:white;'
                'margin:3px 0;padding:5px;">' +
                " ".join(header) + "<br/>" +
                "".join(body) + "</p>"
            )

        html_body = (
            '<html><body style="background-color:transparent;color:white;'
            'font-family:sans-serif;font-size:14px;">' +
            "".join(paragraphs) + "</body></html>"
        )
        self.setHtml(html_body)
        if self._platform_image is not None:
            self.document().addResource(
                QTextDocument.ImageResource,
                QUrl("iol-chat-twitch-logo:"), self._platform_image,
            )
        for url, (raw, image, movie, buffer, animated) in list(self._cache.items()):
            if url not in self._active_urls:
                if movie is not None:
                    movie.stop()
                continue
            target = QUrl(_resource_url(url))
            if animated and movie is None:
                buffer = QBuffer(self)
                buffer.setData(QByteArray(raw))
                if buffer.open(QIODevice.ReadOnly):
                    movie = QMovie(buffer, parent=self)
                    movie.setCacheMode(QMovie.CacheNone)
                    width = max(1, round(28 * image.width() / image.height())) if (
                        image is not None and image.height() > 0
                    ) else 28
                    movie.setScaledSize(QSize(width, 28))
                    movie.frameChanged.connect(
                        lambda _frame, key=url: self._on_movie_frame(key)
                    )
                self._cache[url] = (raw, image, movie, buffer, animated)
            if movie is not None:
                if movie.state() != QMovie.Running:
                    movie.start()
                frame = movie.currentImage()
                if not frame.isNull():
                    self.document().addResource(QTextDocument.ImageResource, target, frame)
            elif image is not None and not image.isNull():
                self.document().addResource(QTextDocument.ImageResource, target, image)
        self.document().markContentsDirty(0, self.document().characterCount())
        self.moveCursor(QTextCursor.End)

    def _on_movie_frame(self, url: str):
        item = self._cache.get(url)
        if item is None or url not in self._active_urls:
            return
        movie = item[2]
        if movie is None:
            return
        frame = movie.currentImage()
        if not frame.isNull():
            self.document().addResource(
                QTextDocument.ImageResource, QUrl(_resource_url(url)), frame,
            )
            self.document().markContentsDirty(0, self.document().characterCount())
            self.viewport().update()

    def wheelEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event):
        event.ignore()

    def closeEvent(self, event):
        self._poll.stop()
        for _raw, _image, movie, _buffer, _animated in self._cache.values():
            if movie is not None:
                movie.stop()
        self._pool.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)
