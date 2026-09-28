from __future__ import annotations

import ipaddress
import json
import re
import socket
from dataclasses import dataclass
from typing import Callable
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImageReader


MAX_REMOTE_IMAGE_BYTES = 10 * 1024 * 1024
MAX_REMOTE_JSON_BYTES = 1024 * 1024
MAX_IMAGE_DIMENSION = 8192
MAX_IMAGE_PIXELS = 40_000_000
USER_AGENT = "InOneLine/1.0.4 wheel-center-image"


@dataclass(frozen=True)
class RemoteImageResult:
    png_bytes: bytes
    display_name: str
    resolved_url: str


def _forbidden_address(address: ipaddress._BaseAddress) -> bool:
    return bool(
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _validate_public_http_url(value: str) -> str:
    parsed = urlparse.urlparse(str(value or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Нужна ссылка http:// или https://.")
    host = parsed.hostname.casefold()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("Локальные адреса нельзя использовать как внешний источник изображения.")
    try:
        literal = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        literal = None
    if literal is not None and _forbidden_address(literal):
        raise ValueError("Локальные/служебные IP-адреса нельзя использовать как внешний источник.")
    if literal is None:
        try:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            addresses = {
                ipaddress.ip_address(item[4][0].split("%", 1)[0])
                for item in socket.getaddrinfo(
                    host,
                    port,
                    type=socket.SOCK_STREAM,
                )
            }
        except (OSError, ValueError) as exc:
            raise ValueError("Не удалось определить адрес внешнего источника.") from exc
        if not addresses or any(_forbidden_address(address) for address in addresses):
            raise ValueError("Источник изображения указывает на локальный/служебный адрес.")
    return parsed.geturl()


class _SafeRedirectHandler(urlrequest.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe = _validate_public_http_url(urlparse.urljoin(req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, safe)


_OPENER = urlrequest.build_opener(_SafeRedirectHandler())


def _read_limited(response, maximum: int) -> bytes:
    length = response.headers.get("Content-Length")
    if length:
        try:
            declared = int(length)
        except (TypeError, ValueError):
            declared = None
        if declared is not None and declared > maximum:
            raise ValueError("Файл изображения слишком большой.")
    data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("Файл изображения слишком большой.")
    return data


def _fetch_bytes(url: str, *, maximum: int, accept: str) -> tuple[bytes, str, str]:
    target = _validate_public_http_url(url)
    request = urlrequest.Request(
        target,
        headers={"User-Agent": USER_AGENT, "Accept": accept},
        method="GET",
    )
    try:
        with _OPENER.open(request, timeout=15.0) as response:
            final_url = _validate_public_http_url(response.geturl())
            raw = _read_limited(response, maximum)
            content_type = str(
                response.headers.get("Content-Type") or ""
            ).split(";", 1)[0].strip().casefold()
            return raw, final_url, content_type
    except urlerror.HTTPError as exc:
        raise ValueError(f"Источник изображения вернул HTTP {exc.code}.") from exc
    except (urlerror.URLError, TimeoutError, OSError) as exc:
        raise ValueError("Не удалось загрузить изображение по сети.") from exc


def _fetch_json(url: str) -> dict:
    raw, _final_url, _content_type = _fetch_bytes(
        url,
        maximum=MAX_REMOTE_JSON_BYTES,
        accept="application/json",
    )
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Сервис вернул некорректный ответ.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Сервис вернул некорректный ответ.")
    return payload


def _largest_mapping_url(mapping) -> str:
    if not isinstance(mapping, dict):
        return ""
    candidates: list[tuple[int, str]] = []
    for key, value in mapping.items():
        value = str(value or "").strip()
        if not value:
            continue
        try:
            rank = int(str(key))
        except ValueError:
            rank = 0
        if value.startswith("//"):
            value = "https:" + value
        candidates.append((rank, value))
    return max(candidates, default=(0, ""))[1]


def _url_display_name(url: str) -> str:
    parsed = urlparse.urlparse(url)
    name = parsed.path.rsplit("/", 1)[-1].strip()
    return urlparse.unquote(name) or (parsed.hostname or "image")


def resolve_external_image_source(
    source: str,
    *,
    twitch_profile_resolver: Callable[[str], str] | None = None,
) -> tuple[str, str]:
    """Resolve provider notation/page URL/direct URL to one concrete image URL."""
    raw = str(source or "").strip()
    if not raw:
        raise ValueError("Укажите URL или источник изображения.")

    prefix_match = re.fullmatch(r"(?i)(7tv|bttv|ffz|twitch)\s*:\s*(.+)", raw)
    if prefix_match:
        provider = prefix_match.group(1).casefold()
        token = prefix_match.group(2).strip()
        if provider == "7tv":
            if not re.fullmatch(r"[A-Za-z0-9]+", token):
                raise ValueError("Некорректный ID 7TV.")
            return f"https://cdn.7tv.app/emote/{token}/4x.webp", f"7TV {token}"
        if provider == "bttv":
            if not re.fullmatch(r"[A-Fa-f0-9]+", token):
                raise ValueError("Некорректный ID BetterTTV.")
            return f"https://cdn.betterttv.net/emote/{token}/3x", f"BetterTTV {token}"
        if provider == "ffz":
            if not token.isdigit():
                raise ValueError("Некорректный ID FrankerFaceZ.")
            payload = _fetch_json(f"https://api.frankerfacez.com/v1/emote/{token}")
            emote = payload.get("emote") or {}
            image_url = _largest_mapping_url(emote.get("urls"))
            if not image_url:
                raise ValueError("FrankerFaceZ не вернул изображение этого emote.")
            return image_url, f"FFZ {emote.get('name') or token}"
        login = token.lstrip("@").strip()
        if not login or twitch_profile_resolver is None:
            raise ValueError(
                "Для Twitch подключите Twitch в In one line или вставьте прямой URL изображения."
            )
        return twitch_profile_resolver(login), f"Twitch @{login}"

    parsed = urlparse.urlparse(_validate_public_http_url(raw))
    host = (parsed.hostname or "").casefold()
    path = parsed.path or ""

    if host in {"7tv.app", "www.7tv.app", "7tv.io", "www.7tv.io"}:
        match = re.search(r"/emotes?/([A-Za-z0-9]+)", path)
        if match:
            emote_id = match.group(1)
            return (
                f"https://cdn.7tv.app/emote/{emote_id}/4x.webp",
                f"7TV {emote_id}",
            )

    if host in {"betterttv.com", "www.betterttv.com"}:
        match = re.search(r"/emotes?/([A-Fa-f0-9]+)", path)
        if match:
            emote_id = match.group(1)
            return (
                f"https://cdn.betterttv.net/emote/{emote_id}/3x",
                f"BetterTTV {emote_id}",
            )

    if host.endswith("frankerfacez.com"):
        match = re.search(r"/(?:emoticon|emote)/(\d+)", path)
        if match:
            emote_id = match.group(1)
            payload = _fetch_json(
                f"https://api.frankerfacez.com/v1/emote/{emote_id}"
            )
            emote = payload.get("emote") or {}
            image_url = _largest_mapping_url(emote.get("urls"))
            if not image_url:
                raise ValueError(
                    "FrankerFaceZ не вернул изображение этого emote."
                )
            return image_url, f"FFZ {emote.get('name') or emote_id}"

    if host in {"twitch.tv", "www.twitch.tv"}:
        login = path.strip("/").split("/", 1)[0].lstrip("@").strip()
        if not login or twitch_profile_resolver is None:
            raise ValueError(
                "Для Twitch подключите Twitch в In one line или вставьте прямой URL изображения."
            )
        return twitch_profile_resolver(login), f"Twitch @{login}"

    return raw, _url_display_name(raw)


def normalize_image_bytes_to_png(raw: bytes) -> bytes:
    payload = QByteArray(raw)
    source = QBuffer()
    source.setData(payload)
    if not source.open(QIODevice.ReadOnly):
        raise ValueError("Не удалось прочитать изображение.")
    reader = QImageReader(source)
    size = reader.size()
    if not size.isValid() or size.width() <= 0 or size.height() <= 0:
        raise ValueError("Файл не распознан как поддерживаемое изображение.")
    if (
        size.width() > MAX_IMAGE_DIMENSION
        or size.height() > MAX_IMAGE_DIMENSION
        or size.width() * size.height() > MAX_IMAGE_PIXELS
    ):
        raise ValueError("Изображение имеет слишком большое разрешение.")
    image = reader.read()
    if image.isNull():
        raise ValueError("Файл не удалось декодировать как изображение.")

    output = QByteArray()
    buffer = QBuffer(output)
    if not buffer.open(QIODevice.WriteOnly) or not image.save(buffer, "PNG"):
        raise ValueError(
            "Не удалось подготовить локальную PNG-копию изображения."
        )
    # PySide6 may wrap/copy the QByteArray passed to QBuffer. Read the
    # buffer's actual backing data after QImage.save() instead of assuming the
    # original Python wrapper was updated in place.
    return bytes(buffer.data())


def load_local_image_as_png(path: str) -> bytes:
    try:
        with open(path, "rb") as file:
            raw = file.read(MAX_REMOTE_IMAGE_BYTES + 1)
    except OSError as exc:
        raise ValueError(
            "Не удалось прочитать выбранный файл изображения."
        ) from exc
    if len(raw) > MAX_REMOTE_IMAGE_BYTES:
        raise ValueError("Файл изображения слишком большой.")
    return normalize_image_bytes_to_png(raw)


def download_external_image_as_png(
    source: str,
    *,
    twitch_profile_resolver: Callable[[str], str] | None = None,
) -> RemoteImageResult:
    image_url, display_name = resolve_external_image_source(
        source,
        twitch_profile_resolver=twitch_profile_resolver,
    )
    raw, final_url, content_type = _fetch_bytes(
        image_url,
        maximum=MAX_REMOTE_IMAGE_BYTES,
        accept="image/*,*/*;q=0.2",
    )
    if content_type and not (
        content_type.startswith("image/")
        or content_type == "application/octet-stream"
    ):
        raise ValueError("По указанной ссылке получен не файл изображения.")
    return RemoteImageResult(
        png_bytes=normalize_image_bytes_to_png(raw),
        display_name=str(display_name or "remote image"),
        resolved_url=final_url,
    )
