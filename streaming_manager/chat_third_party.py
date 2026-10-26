from __future__ import annotations

"""D41-05: resolve only verified, currently applicable third-party Twitch emotes.

Resolution happens on EventSub reception, never when a late catalog appears.
A third-party code with multiple different applicable images stays literal.
No HTML, provider scripts or OBS-side platform connections are permitted.
"""

import re
from dataclasses import dataclass

from .chat_graphics import safe_image_url

# Only stand-alone Twitch-style codes, preserving surrounding punctuation.
_TOKEN = re.compile(r"""^([("'\[{]*)([A-Za-z0-9_]{1,64})([.,!?;:)"'\]}]*)$""")
_MAX_EMOTES = 3000
_MAX_IMAGES_PER_MESSAGE = 32


def _text(out: list[dict], value: str) -> None:
    if not value:
        return
    if out and out[-1]["kind"] == "text":
        out[-1]["text"] += value
    else:
        out.append({"kind": "text", "text": value})


@dataclass(frozen=True)
class ChatEmote:
    provider: str
    code: str
    url: str
    animated: bool


def make_catalog(items) -> dict[str, ChatEmote | None]:
    """None marks an unresolved collision; insertion order never picks a winner."""
    catalog: dict[str, ChatEmote | None] = {}
    for item in list(items)[:_MAX_EMOTES]:
        provider = str(getattr(item, "source", "") or "").strip()
        name = str(getattr(item, "name", "") or "")
        url = safe_image_url(getattr(item, "image_url", ""))
        if provider not in {"BTTV", "FFZ", "7TV"} or not url:
            continue
        if not re.fullmatch(r"[A-Za-z0-9_]{1,64}", name):
            continue
        emote = ChatEmote(provider, name, url, bool(getattr(item, "animated", False)))
        if name not in catalog:
            catalog[name] = emote
        elif catalog[name] is not None and catalog[name].url != emote.url:
            catalog[name] = None
    return catalog


def resolve_text(text: str, catalog: dict[str, ChatEmote | None], *,
                 max_images: int = _MAX_IMAGES_PER_MESSAGE) -> tuple[dict, ...]:
    """Pure conversion of one EventSub text fragment, preserving every character."""
    if not text or not catalog:
        return ({"kind": "text", "text": text},) if text else ()
    pieces = re.split(r"(\s+)", text)
    result: list[dict] = []
    count = 0
    for piece in pieces:
        if not piece:
            continue
        match = _TOKEN.fullmatch(piece)
        emote = catalog.get(match.group(2)) if match else None
        if emote is None or count >= max_images:
            _text(result, piece)
            continue
        prefix, code, suffix = match.groups()
        if prefix:
            _text(result, prefix)
        result.append({"kind": "image", "text": code, "url": emote.url})
        if suffix:
            _text(result, suffix)
        count += 1
    return tuple(result)


def resolve_fragments(fragments: tuple[dict, ...], text: str,
                      catalog: dict[str, ChatEmote | None]) -> tuple[dict, ...]:
    """Convert text-only pieces without touching native Twitch emotes or GIFs."""
    if not catalog:
        return fragments  # byte-for-byte semantic preservation before catalog ready
    incoming = fragments or ({"kind": "text", "text": text},)
    result: list[dict] = []
    images = 0
    for fragment in incoming[:256]:
        if not isinstance(fragment, dict):
            continue
        if fragment.get("kind") == "image":
            result.append(fragment)
            images += 1
            continue
        # Never transform image URLs or a Twitch-native graphics fragment.
        for part in resolve_text(str(fragment.get("text") or ""), catalog,
                                 max_images=max(0, _MAX_IMAGES_PER_MESSAGE - images)):
            if part.get("kind") == "image":
                result.append(part)
                images += 1
            else:
                _text(result, part.get("text", ""))
    # Defensive: preserve the complete original message if a provider ever
    # sends enough fragments to exceed the bounded renderer limit.
    return tuple(result) if len(result) <= 256 else fragments
