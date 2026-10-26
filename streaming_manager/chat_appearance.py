from __future__ import annotations

"""D41-06 Twitch chat presentation: persisted appearance, never chat content.

The existing Database.settings table remains the sole durable owner.  Runtime
operator messages and OBS messages continue to live only in MultichatState.
"""

import json
import re

from .media import MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, media_asset_available
from .media import resolve_media_asset_path

TWITCH_KEY = "multichat_appearance_twitch"
COMMON_KEY = "multichat_appearance_common"

TWITCH_DEFAULTS = {
    "mode": "original",
    "text_font": "Segoe UI", "text_size": 18, "text_color": "#FFFFFF",
    "name_font": "Segoe UI", "name_size": 18, "name_color": "#FFFFFF",
    "card_color": "#000000", "card_opacity": 50,
    "card_border_color": "#FFFFFF", "card_border_width": 0,
    "card_radius": 0, "avatar_size": 24, "badge_size": 18,
}
COMMON_DEFAULTS = {
    "background": "transparent", "background_color": "#000000",
    "background_opacity": 65, "background_media_id": None,
    "background_fit": "cover", "glow": False,
    "glow_color": "#FFFFFF", "visibility": "hide_empty",
}
_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_FONT = re.compile(r"^[\w \-+,.()]{1,80}$", re.UNICODE)


def _integer(value, default: int, lo: int, hi: int) -> int:
    try:
        if isinstance(value, bool):
            return default
        v = int(value)
        return max(lo, min(hi, v))
    except (TypeError, ValueError, OverflowError):
        return default


def _color(value, default: str) -> str:
    return str(value).upper() if _COLOR.fullmatch(str(value or "")) else default


def _font(value, default: str) -> str:
    value = str(value or "").strip()
    return value if _FONT.fullmatch(value) else default


def normalize_twitch(raw) -> dict:
    d = TWITCH_DEFAULTS.copy()
    if not isinstance(raw, dict):
        return d
    if raw.get("mode") in {"original", "custom"}:
        d["mode"] = raw["mode"]
    for key in ("text_font", "name_font"):
        d[key] = _font(raw.get(key), d[key])
    for key in ("text_color", "name_color", "card_color", "card_border_color"):
        d[key] = _color(raw.get(key), d[key])
    for key, low, high in (
        ("text_size", 6, 96), ("name_size", 6, 96),
        ("card_opacity", 0, 100), ("card_border_width", 0, 12),
        ("card_radius", 0, 64), ("avatar_size", 8, 96),
        ("badge_size", 8, 64),
    ):
        d[key] = _integer(raw.get(key), d[key], low, high)
    return d


def normalize_common(raw) -> dict:
    d = COMMON_DEFAULTS.copy()
    if not isinstance(raw, dict):
        return d
    if raw.get("background") in {"transparent", "color", "media"}:
        d["background"] = raw["background"]
    d["background_color"] = _color(raw.get("background_color"), d["background_color"])
    d["glow_color"] = _color(raw.get("glow_color"), d["glow_color"])
    d["background_opacity"] = _integer(raw.get("background_opacity"), 65, 0, 100)
    d["background_media_id"] = _integer(raw.get("background_media_id"), 0, 0, 2147483647) or None
    d["background_fit"] = "contain" if raw.get("background_fit") == "contain" else "cover"
    d["glow"] = raw.get("glow") is True
    d["visibility"] = "always" if raw.get("visibility") == "always" else "hide_empty"
    return d


def _load(db, key: str) -> dict:
    try:
        data = json.loads(db.get_setting(key, "{}"))
        return data if isinstance(data, dict) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def saved_appearance(db) -> dict:
    return {
        "twitch": normalize_twitch(_load(db, TWITCH_KEY)),
        "common": normalize_common(_load(db, COMMON_KEY)),
    }


def save_appearance(db, twitch: dict, common: dict) -> dict:
    result = {"twitch": normalize_twitch(twitch), "common": normalize_common(common)}
    # Existing settings persistence, no table, migration, account or message history.
    db.set_setting(TWITCH_KEY, json.dumps(result["twitch"], ensure_ascii=False, sort_keys=True))
    db.set_setting(COMMON_KEY, json.dumps(result["common"], ensure_ascii=False, sort_keys=True))
    return result


def public_appearance(db) -> dict:
    """OBS receives only saved appearance and a validated registered media URL."""
    result = saved_appearance(db)
    common = result["common"]
    common["media_url"] = ""
    common["media_kind"] = ""
    if common["background"] == "media" and common["background_media_id"]:
        asset = db.get_media_asset(common["background_media_id"])
        if (asset is not None
                and asset.category == MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
                and media_asset_available(db.path.parent, asset)):
            ext = resolve_media_asset_path(db.path.parent, asset).suffix.lower()
            if ext in {".mp4", ".webm"}:
                common["media_kind"] = "video"
            elif ext in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                common["media_kind"] = "image"
            if common["media_kind"]:
                common["media_url"] = f"/media/{asset.id}"
    return result
