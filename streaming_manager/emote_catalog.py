from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib import error as urlerror
from urllib import request as urlrequest

from .integrations import IntegrationTemporaryError


USER_AGENT = "InOneLine/1.0.6 emote-catalog"
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

    def load_7tv() -> list[EmoteCatalogItem]:
        try:
            # api.7tv.app is the 2026 service-status endpoint; retain the
            # older 7tv.io origin as compatibility fallback.
            user_payload = {}
            seven_root = "https://api.7tv.app/v3"
            for root in ("https://api.7tv.app/v3", "https://7tv.io/v3"):
                try:
                    user_payload = _fetch_json(f"{root}/users/twitch/{twitch_id}")
                except Exception:
                    continue
                if user_payload:
                    seven_root = root
                    break
            emote_set = user_payload.get("emote_set")
            set_id = str(
                user_payload.get("emote_set_id")
                or (
                    emote_set.get("id")
                    if isinstance(emote_set, dict)
                    else ""
                )
                or ""
            ).strip()
            if not (
                isinstance(emote_set, dict)
                and isinstance(emote_set.get("emotes"), list)
            ):
                user_payload = (
                    _fetch_json(f"{seven_root}/emote-sets/{set_id}")
                    if set_id
                    else {}
                )
            return _parse_7tv_emotes(user_payload)
        except Exception:
            return []

    def load_bttv() -> list[EmoteCatalogItem]:
        try:
            return _parse_bttv_emotes(
                _fetch_json(
                    f"https://api.betterttv.net/3/cached/users/twitch/{twitch_id}"
                )
            )
        except Exception:
            return []

    def load_ffz() -> list[EmoteCatalogItem]:
        try:
            return _parse_ffz_emotes(
                _fetch_json(
                    f"https://api.frankerfacez.com/v1/room/id/{twitch_id}"
                )
            )
        except Exception:
            return []

    result: list[EmoteCatalogItem] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(load_7tv),
            pool.submit(load_bttv),
            pool.submit(load_ffz),
        ]
        for future in futures:
            try:
                result.extend(future.result())
            except Exception:
                continue

    seen: set[tuple[str, str]] = set()
    unique: list[EmoteCatalogItem] = []
    for item in result:
        if item.dedupe_key in seen:
            continue
        seen.add(item.dedupe_key)
        unique.append(item)
    return unique



def _fetch_list(url: str) -> list:
    """BTTV global endpoint is a JSON array; channel endpoints are mappings."""
    request = urlrequest.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with urlrequest.urlopen(request, timeout=12.0) as response:
            raw = _read_limited(response, JSON_LIMIT)
        payload = json.loads(raw.decode("utf-8"))
        return payload if isinstance(payload, list) else []
    except (urlerror.HTTPError, urlerror.URLError, TimeoutError, OSError,
            ValueError, UnicodeError, json.JSONDecodeError):
        return []


def fetch_third_party_chat_emotes(twitch_user_id: str) -> list[EmoteCatalogItem]:
    """Fetch all *publicly applicable* channel/global sets for one Twitch room.

    Global FFZ user-scoped sets are intentionally excluded unless user-specific
    eligibility can be authenticated per sender. Only default_sets apply to
    every viewer in the Twitch channel. Independent provider failures never
    block EventSub and never invent images.
    """
    channel = str(twitch_user_id or "").strip()
    if not channel.isdigit():
        return []

    def global_7tv():
        for root in ("https://api.7tv.app/v3", "https://7tv.io/v3"):
            try:
                payload = _fetch_json(f"{root}/emote-sets/global")
                if payload:
                    return _parse_7tv_emotes(payload)
            except Exception:
                continue
        return []

    def global_bttv():
        return _parse_bttv_emotes({
            "channelEmotes": _fetch_list(
                "https://api.betterttv.net/3/cached/emotes/global"
            ),
        })

    def global_ffz():
        try:
            payload = _fetch_json("https://api.frankerfacez.com/v1/set/global")
            defaults = {str(x) for x in (payload.get("default_sets") or [])}
            sets = payload.get("sets") or {}
            if not isinstance(sets, dict):
                return []
            # Do not accidentally expose user-gated global sets to everyone.
            return _parse_ffz_emotes({
                "sets": {key: value for key, value in sets.items()
                         if str(key) in defaults}
            })
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = [pool.submit(global_7tv), pool.submit(global_bttv),
                pool.submit(global_ffz),
                pool.submit(fetch_third_party_channel_emotes, channel)]
        result = []
        for job in jobs:
            try:
                result.extend(job.result())
            except Exception:
                continue
    # A channel/global code may legitimately repeat, including collisions.
    # Do not deduplicate by code here: the chat resolver decides ambiguity.
    seen = set()
    catalog = []
    for item in result[:4500]:
        key = (item.source, item.emote_id, item.name, item.image_url)
        if key in seen:
            continue
        seen.add(key)
        catalog.append(item)
        if len(catalog) >= 3000:
            break
    return catalog


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
