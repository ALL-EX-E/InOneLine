"""Presentation-only correction for the built-in InOneLine wheel-center icon.

The original square asset has dark corner padding around a green panel.  Fill
only the exterior bands of that *bundled* asset with its own dominant green;
leave every pixel between the first and last green pixel of a row untouched,
including the black symbol. This never transforms user-selected media/GIFs.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QColor, QImage


def _is_panel_green(color: QColor) -> bool:
    return (
        color.green() >= 110
        and color.green() > color.red() * 1.65
        and color.green() > color.blue() * 1.65
        and color.alpha() >= 200
    )


def fill_default_icon_corners(source: QImage) -> QImage:
    """Keep native dimensions, protect all inner black logo strokes."""
    if source.isNull():
        return QImage()
    result = source.convertToFormat(QImage.Format.Format_ARGB32)
    width, height = result.width(), result.height()

    # Sample the existing vivid green rather than adding a configurable color.
    # A central band avoids the dark border and the arrow-shaft drawing.
    swatches: list[tuple[int, int, int]] = []
    for y in range(height // 5, (height * 4) // 5, max(1, height // 40)):
        for x in range(width // 5, (width * 4) // 5, max(1, width // 40)):
            color = result.pixelColor(x, y)
            if _is_panel_green(color):
                swatches.append((color.red(), color.green(), color.blue()))
    if not swatches:
        return result
    swatches.sort()
    # Median by each channel resists edge anti-aliasing.
    fill = QColor(
        sorted(c[0] for c in swatches)[len(swatches) // 2],
        sorted(c[1] for c in swatches)[len(swatches) // 2],
        sorted(c[2] for c in swatches)[len(swatches) // 2],
    )

    # One scan per row. The dark arrows are INSIDE the green panel and are
    # never visited. If no green is present, the entire row is outer padding.
    for y in range(height):
        left = width
        right = -1
        for x in range(width):
            if _is_panel_green(result.pixelColor(x, y)):
                left = min(left, x)
                right = x
        for x in range(left):
            result.setPixelColor(x, y, fill)
        for x in range(right + 1, width):
            result.setPixelColor(x, y, fill)
    return result


def bundled_icon_path() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "InOneLine_icon_master.png"


@lru_cache(maxsize=1)
def default_wheel_icon_image() -> QImage:
    return fill_default_icon_corners(QImage(str(bundled_icon_path())))


@lru_cache(maxsize=1)
def default_wheel_icon_png() -> bytes:
    image = default_wheel_icon_image()
    if image.isNull():
        return b""
    buffer = QBuffer()
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        return b""
    if not image.save(buffer, "PNG"):
        return b""
    return bytes(buffer.data())
