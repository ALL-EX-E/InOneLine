"""Read-only presentation policy shared by the existing OBS widgets."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .constants import (
    MUSIC_PLAYER_OVERLAY_SHOW_MODE_KEY,
    RULES_OVERLAY_VISIBLE_DEFAULT,
    RULES_OVERLAY_VISIBLE_KEY,
)


@dataclass(frozen=True)
class WidgetVisibility:
    key: str
    default: str
    options: tuple[tuple[str, str], ...]


_HIDDEN = ("hidden", "Не показывать")
_ALWAYS = ("always", "Показывать постоянно")
_SIMPLE = (_HIDDEN, _ALWAYS)

# Keep the main-overlay visibility mechanism for future use, but the
# operator's primary canvas is currently always rendered. Re-enable the
# existing mode UI and remove this override only when explicitly requested.
MAIN_OVERLAY_SHOW_MODE_CONTROL_ENABLED = False

WIDGETS = {
    "overlay": WidgetVisibility("overlay_show_mode", "always", _SIMPLE),
    "list": WidgetVisibility("list_overlay_show_mode", "always", _SIMPLE),
    "timer": WidgetVisibility("timer_overlay_show_mode", "always", _SIMPLE),
    "music_player": WidgetVisibility(
        MUSIC_PLAYER_OVERLAY_SHOW_MODE_KEY, "track_change",
        (_HIDDEN, ("track_change", "При смене трека"), _ALWAYS),
    ),
    "auction_lots": WidgetVisibility("auction_lots_overlay_show_mode", "always", _SIMPLE),
    "rules": WidgetVisibility("rules_overlay_show_mode", "always", _SIMPLE),
    "wheel": WidgetVisibility(
        "wheel_overlay_show_mode", "context",
        (_HIDDEN, ("context", "Когда колесо используется"), _ALWAYS),
    ),
}


def show_mode(settings: Mapping[str, Any], widget: str) -> str:
    spec = WIDGETS[widget]
    if widget == "overlay" and not MAIN_OVERLAY_SHOW_MODE_CONTROL_ENABLED:
        return "always"
    # Consolidated List mode also owns the list embedded in the main overlay.
    # Until its first Save, preserve an older embedded-list hide choice.
    if widget == "list" and spec.key not in settings:
        return "hidden" if settings.get("overlay_list_enabled", "1") == "0" else "always"
    # Old Rules databases keep their choice until an explicit new-mode Save.
    # Once present, the new key alone is authoritative, even if malformed.
    if widget == "rules" and spec.key not in settings:
        legacy = settings.get(
            RULES_OVERLAY_VISIBLE_KEY, "1" if RULES_OVERLAY_VISIBLE_DEFAULT else "0",
        )
        return "always" if legacy == "1" else "hidden"
    mode = str(settings.get(spec.key) or "").strip().casefold()
    return mode if any(mode == value for value, _label in spec.options) else spec.default


def visibility_payload(
    settings: Mapping[str, Any], widget: str, context_visible: bool = True,
) -> dict[str, Any]:
    return {
        "show_mode": show_mode(settings, widget),
        "context_visible": bool(context_visible),
    }


def wheel_context_relevant(
    session: Mapping[str, Any] | None, selected_mode: str = "max_amount",
) -> bool:
    """The existing local wheel relevance predicate, without Qt or writes."""
    if session is None:
        return str(selected_mode or "") == "weighted_wheel"
    return (
        str(session.get("mode") or "") == "weighted_wheel"
        or str(session.get("status") or "") == "awaiting_wheel"
        or bool(session.get("wheel_spin_id"))
    )
