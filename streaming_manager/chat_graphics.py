from __future__ import annotations

"""D41-04: strictly presentation-only Twitch EventSub graphics metadata.

Never put provider HTML into Qt or OBS; source messages contain text fragments,
limited provider image URLs and no executable markup.
"""

import re
from urllib.parse import urlsplit

_COLOR = re.compile(r"^#[a-fA-F0-9]{6}$")
_EMOTE_ID = re.compile(r"^[a-zA-Z0-9_-]{1,120}$")
_ALLOWED_IMAGE_DOMAINS = (
    "jtvnw.net", "twitchcdn.net", "ttvnw.net",
    "tenor.com", "giphy.com",
    "betterttv.net", "frankerfacez.com", "7tv.app", "7tv.io",
)


def safe_image_url(value: object) -> str:
    url = str(value or "").strip()
    if len(url) > 2048:
        return ""
    try:
        parts = urlsplit(url)
        hostname = str(parts.hostname or "").casefold()
        if (
            parts.scheme != "https" or parts.username or parts.password
            or parts.port not in (None, 443)
            or not hostname or not any(
                hostname == domain or hostname.endswith("." + domain)
                for domain in _ALLOWED_IMAGE_DOMAINS
            )
        ):
            return ""
    except ValueError:
        return ""
    return url


def parse_twitch_fragments(body: dict) -> tuple[dict, ...]:
    raw = body.get("fragments") if isinstance(body, dict) else None
    if not isinstance(raw, list) or not raw:
        return ()
    result: list[dict] = []
    pictures = 0
    for fragment in raw[:256]:
        if not isinstance(fragment, dict):
            continue
        label = str(fragment.get("text") or "")
        kind = str(fragment.get("type") or "").casefold()
        url = ""
        if kind == "emote":
            metadata = fragment.get("emote")
            if isinstance(metadata, dict):
                identifier = str(metadata.get("id") or "")
                formats = metadata.get("format") or []
                if _EMOTE_ID.fullmatch(identifier):
                    animated = "animated" in formats if isinstance(formats, list) else False
                    fmt = "animated" if animated else "static"
                    url = safe_image_url(
                        f"https://static-cdn.jtvnw.net/emoticons/v2/{identifier}/{fmt}/dark/2.0"
                    )
        elif kind == "gif":
            metadata = fragment.get("gif")
            if isinstance(metadata, dict):
                # A GIF EventSub url must be used verbatim, never reconstructed.
                url = safe_image_url(metadata.get("url"))
        if url and pictures < 32:
            result.append({"kind": "image", "text": label, "url": url})
            pictures += 1
        elif label:
            result.append({"kind": "text", "text": label})
    # Untrusted fragments should not be able to erase the authoritative text.
    return tuple(result) if result else ()


def parse_twitch_badges(event: dict) -> tuple[dict, ...]:
    raw = event.get("badges")
    if not isinstance(raw, list):
        return ()
    result = []
    for badge in raw[:16]:
        if not isinstance(badge, dict):
            continue
        set_id = str(badge.get("set_id") or "")[:100]
        version = str(badge.get("id") or "")[:100]
        if set_id and version:
            result.append({"set_id": set_id, "id": version, "url": ""})
    return tuple(result)


def twitch_name_color(value: object) -> str:
    color = str(value or "")
    return color if _COLOR.fullmatch(color) else ""


def validated_avatar(value: object) -> str:
    return safe_image_url(value)
