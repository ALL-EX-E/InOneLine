from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib import error as urlerror
from urllib import request as urlrequest

from .integrations import IntegrationTemporaryError


USER_AGENT = "InOneLine/1.0.4 emote-catalog"
JSON_LIMIT = 2 * 1024 * 1024
THUMB_LIMIT = 1024 * 1024


@dataclass(frozen=True)
class EmoteCatalogItem:
    source: str
    emote_id: str
    name: str
    image_url: str
    preview_url: str
    animated: bool = False
    thumbnail_bytes: bytes = b""

    @property
    def dedupe_key(self) -> tuple[str, str]:
        return (str(self.source).casefold(), str(self.emote_id))


def _read_limited(response, maximum: int) -> bytes:
    data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("Ответ сервиса смайликов слишком большой.")
    return data


def _fetch_json(url: str) -> dict:
    request = urlrequest.Request(
        str(url),
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with urlrequest.urlopen(request, timeout=12.0) as response:
            raw = _read_limited(response, JSON_LIMIT)
    except urlerror.HTTPError as exc:
        if int(exc.code) == 404:
            return {}
        raise IntegrationTemporaryError(
            f"Сервис смайликов временно недоступен (HTTP {exc.code})."
        ) from exc
    except (urlerror.URLError, TimeoutError, OSError) as exc:
        raise IntegrationTemporaryError("Сервис смайликов временно недоступен.") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrationTemporaryError("Сервис смайликов вернул некорректный ответ.") from exc
    return payload if isinstance(payload, dict) else {}


def _fetch_thumbnail(url: str) -> bytes:
    request = urlrequest.Request(
        str(url),
        headers={"Accept": "image/*,*/*;q=0.2", "User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with urlrequest.urlopen(request, timeout=10.0) as response:
            return _read_limited(response, THUMB_LIMIT)
    except Exception:
        return b""


def _largest_url(mapping) -> tuple[str, str]:
    if not isinstance(mapping, dict):
        return "", ""
    rows: list[tuple[int, str, str]] = []
    for key, value in mapping.items():
        url = str(value or "").strip()
        if not url:
            continue
        if url.startswith("//"):
            url = "https:" + url
        try:
            rank = int(str(key))
        except ValueError:
            rank = 0
        rows.append((rank, str(key), url))
    if not rows:
        return "", ""
    rows.sort()
    largest = rows[-1][2]
    smallest = rows[0][2]
    return largest, smallest


def _parse_7tv_emotes(payload: dict) -> list[EmoteCatalogItem]:
    emote_set = payload.get("emote_set")
    emotes = []
    if isinstance(emote_set, dict) and isinstance(emote_set.get("emotes"), list):
        emotes = emote_set.get("emotes") or []
    elif isinstance(payload.get("emotes"), list):
        emotes = payload.get("emotes") or []
    result: list[EmoteCatalogItem] = []
    for row in emotes:
        if not isinstance(row, dict):
            continue
        data = row.get("data") if isinstance(row.get("data"), dict) else {}
        emote_id = str(row.get("id") or data.get("id") or "").strip()
        name = str(row.get("name") or data.get("name") or emote_id).strip()
        if not emote_id:
            continue
        result.append(
            EmoteCatalogItem(
                source="7TV",
                emote_id=emote_id,
                name=name or emote_id,
                image_url=f"https://cdn.7tv.app/emote/{emote_id}/4x.webp",
                preview_url=f"https://cdn.7tv.app/emote/{emote_id}/2x.webp",
                animated=bool(data.get("animated") or row.get("animated")),
            )
        )
    return result


def _parse_bttv_emotes(payload: dict) -> list[EmoteCatalogItem]:
    rows = []
    for key in ("channelEmotes", "sharedEmotes"):
        value = payload.get(key)
        if isinstance(value, list):
            rows.extend(value)
    result: list[EmoteCatalogItem] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        emote_id = str(row.get("id") or "").strip()
        name = str(row.get("code") or row.get("name") or emote_id).strip()
        if not emote_id:
            continue
        image_type = str(row.get("imageType") or "").casefold()
        result.append(
            EmoteCatalogItem(
                source="BTTV",
                emote_id=emote_id,
                name=name or emote_id,
                image_url=f"https://cdn.betterttv.net/emote/{emote_id}/3x",
                preview_url=f"https://cdn.betterttv.net/emote/{emote_id}/1x",
                animated=image_type in {"gif", "webp"},
            )
        )
    return result


def _parse_ffz_emotes(payload: dict) -> list[EmoteCatalogItem]:
    sets = payload.get("sets")
    if not isinstance(sets, dict):
        return []
    result: list[EmoteCatalogItem] = []
    for emote_set in sets.values():
        if not isinstance(emote_set, dict):
            continue
        rows = emote_set.get("emoticons")
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            emote_id = str(row.get("id") or "").strip()
            name = str(row.get("name") or emote_id).strip()
            image_url, preview_url = _largest_url(row.get("urls"))
            if not emote_id or not image_url:
                continue
            result.append(
                EmoteCatalogItem(
                    source="FFZ",
                    emote_id=emote_id,
                    name=name or emote_id,
                    image_url=image_url,
                    preview_url=preview_url or image_url,
                    animated=False,
                )
            )
    return result


def fetch_third_party_channel_emotes(twitch_user_id: str) -> list[EmoteCatalogItem]:
    twitch_id = str(twitch_user_id or "").strip()
    if not twitch_id.isdigit():
        return []

    result: list[EmoteCatalogItem] = []

    # 7TV v3: Twitch connection -> emote set. Some deployments include the
    # emote set inline; otherwise fetch the referenced set separately.
    try:
        user_payload = _fetch_json(f"https://7tv.io/v3/users/twitch/{twitch_id}")
        emote_set = user_payload.get("emote_set")
        set_id = str(
            user_payload.get("emote_set_id")
            or (emote_set.get("id") if isinstance(emote_set, dict) else "")
            or ""
        ).strip()
        if not (isinstance(emote_set, dict) and isinstance(emote_set.get("emotes"), list)):
            user_payload = (
                _fetch_json(f"https://7tv.io/v3/emote-sets/{set_id}")
                if set_id
                else {}
            )
        result.extend(_parse_7tv_emotes(user_payload))
    except Exception:
        pass

    try:
        result.extend(
            _parse_bttv_emotes(
                _fetch_json(
                    f"https://api.betterttv.net/3/cached/users/twitch/{twitch_id}"
                )
            )
        )
    except Exception:
        pass

    try:
        result.extend(
            _parse_ffz_emotes(
                _fetch_json(
                    f"https://api.frankerfacez.com/v1/room/id/{twitch_id}"
                )
            )
        )
    except Exception:
        pass

    seen: set[tuple[str, str]] = set()
    unique: list[EmoteCatalogItem] = []
    for item in result:
        if item.dedupe_key in seen:
            continue
        seen.add(item.dedupe_key)
        unique.append(item)
    return unique


def hydrate_emote_thumbnails(
    items: list[EmoteCatalogItem],
    *,
    max_workers: int = 8,
) -> list[EmoteCatalogItem]:
    if not items:
        return []
    workers = max(1, min(12, int(max_workers)))
    indexed: dict[int, bytes] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_fetch_thumbnail, item.preview_url or item.image_url): index
            for index, item in enumerate(items)
        }
        for future in as_completed(futures):
            index = futures[future]
            try:
                indexed[index] = bytes(future.result() or b"")
            except Exception:
                indexed[index] = b""
    return [
        EmoteCatalogItem(
            source=item.source,
            emote_id=item.emote_id,
            name=item.name,
            image_url=item.image_url,
            preview_url=item.preview_url,
            animated=item.animated,
            thumbnail_bytes=indexed.get(index, b""),
        )
        for index, item in enumerate(items)
    ]
