"""Presentation-only correction for the built-in InOneLine wheel-center icon.

The original square asset has dark corner padding around a green panel.  Fill
only the exterior bands of that *bundled* asset with its own dominant green.
Scan both axes and cover the narrow antialiased panel fringe; the interior
black symbol stays untouched. This never transforms user-selected media/GIFs.
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
    """Recolor only exterior padding; avoid per-pixel Qt/Python QColor calls.

    RGBA8888 permits two short byte-level edge scans per row. This is
    considerably faster for the bundled high-resolution icon than repeated
    QImage.pixelColor/setPixelColor and leaves the interior logo untouched.
    """
    if source.isNull():
        return QImage()
    result = source.convertToFormat(QImage.Format.Format_RGBA8888)
    width, height = result.width(), result.height()
    stride = result.bytesPerLine()
    pixels = result.bits()
    original = bytes(pixels)

    def green(row: bytes, x: int, offset: int = 0) -> bool:
        p = offset + x * 4
        r, g, b, a = row[p], row[p + 1], row[p + 2], row[p + 3]
        return g >= 110 and g * 20 > r * 33 and g * 20 > b * 33 and a >= 200

    swatches: list[tuple[int, int, int]] = []
    for y in range(height // 5, (height * 4) // 5, max(1, height // 40)):
        row = original[y * stride: y * stride + width * 4]
        for x in range(width // 5, (width * 4) // 5, max(1, width // 40)):
            if green(row, x):
                p = x * 4
                swatches.append((row[p], row[p + 1], row[p + 2]))
    if not swatches:
        return result

    middle = len(swatches) // 2
    fill_pixel = bytes((
        sorted(c[0] for c in swatches)[middle],
        sorted(c[1] for c in swatches)[middle],
        sorted(c[2] for c in swatches)[middle],
        255,
    ))
    # The old panel has a thin dark/bright antialiased border, including
    # horizontal fragments that a row-only exterior scan cannot see.
    fringe = max(1, min(width, height) // 200)
    for y in range(height):
        source_row = original[y * stride: y * stride + width * 4]
        row = pixels[y * stride: y * stride + width * 4]
        left = 0
        while left < width and not green(source_row, left):
            left += 1
        right = width - 1
        while right >= left and not green(source_row, right):
            right -= 1
        left = min(width, left + fringe)
        right = max(-1, right - fringe)
        if left:
            row[:left * 4] = fill_pixel * left
        if right + 1 < width:
            row[(right + 1) * 4:] = fill_pixel * (width - right - 1)
    for x in range(width):
        top = 0
        while top < height and not green(original, x, top * stride):
            top += 1
        bottom = height - 1
        while bottom >= top and not green(original, x, bottom * stride):
            bottom -= 1
        for y in range(min(height, top + fringe)):
            offset = y * stride + x * 4
            pixels[offset:offset + 4] = fill_pixel
        for y in range(max(0, bottom + 1 - fringe), height):
            offset = y * stride + x * 4
            pixels[offset:offset + 4] = fill_pixel
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
