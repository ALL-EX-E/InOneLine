"""Read-only presentation policy shared by the existing OBS widgets."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
import re
from typing import Any

from .constants import (
    MUSIC_PLAYER_OVERLAY_SHOW_MODE_KEY,
    RULES_OVERLAY_VISIBLE_DEFAULT,
    RULES_OVERLAY_VISIBLE_KEY,
    WHEEL_GLOW_ENABLED_KEY,
    WHEEL_GLOW_ENABLED_DEFAULT,
    WHEEL_GLOW_COLOR_KEY,
    WHEEL_GLOW_COLOR_DEFAULT,
    WHEEL_POINTER_LABEL_ENABLED_KEY,
    WHEEL_POINTER_LABEL_ENABLED_DEFAULT,
)


@dataclass(frozen=True)
class WidgetVisibility:
    key: str
    default: str
    options: tuple[tuple[str, str], ...]


_HIDDEN = ("hidden", "Не показывать")
_ALWAYS = ("always", "Показывать постоянно")
_SIMPLE = (_HIDDEN, _ALWAYS)

AUCTION_WIDGET_BINDINGS = {
    "timer": (
        "timer_overlay_follow_auction_tab",
        "timer_overlay_slide_direction",
        "timer_overlay_slide_seconds",
    ),
    "auction_lots": (
        "auction_lots_overlay_follow_auction_tab",
        "auction_lots_overlay_slide_direction",
        "auction_lots_overlay_slide_seconds",
    ),
    "rules": (
        "rules_overlay_follow_auction_tab",
        "rules_overlay_slide_direction",
        "rules_overlay_slide_seconds",
    ),
}
AUCTION_WIDGET_SLIDE_MODE = ("slide", "Выезд")
AUCTION_WIDGET_SLIDE_DIRECTIONS = (
    ("Слева", "left"), ("Справа", "right"),
    ("Сверху", "top"), ("Снизу", "bottom"),
)
AUCTION_WIDGET_SLIDE_DEFAULT_SECONDS = 0.65
AUCTION_WIDGET_SLIDE_MIN_SECONDS = 0.10
AUCTION_WIDGET_SLIDE_MAX_SECONDS = 10.00

# Keep the main-overlay visibility mechanism for future use, but the
# operator's primary canvas is currently always rendered. Re-enable the
# existing mode UI and remove this override only when explicitly requested.
MAIN_OVERLAY_SHOW_MODE_CONTROL_ENABLED = False

WIDGETS = {
    "overlay": WidgetVisibility("overlay_show_mode", "always", _SIMPLE),
    "list": WidgetVisibility("list_overlay_show_mode", "always", (_HIDDEN, _ALWAYS, ("slide", "Выезд"))),
    "timer": WidgetVisibility("timer_overlay_show_mode", "always", (*_SIMPLE, AUCTION_WIDGET_SLIDE_MODE)),
    "music_player": WidgetVisibility(
        MUSIC_PLAYER_OVERLAY_SHOW_MODE_KEY, "track_change",
        (_HIDDEN, ("track_change", "При смене трека"), _ALWAYS),
    ),
    "auction_lots": WidgetVisibility(
        "auction_lots_overlay_show_mode", "always", (*_SIMPLE, AUCTION_WIDGET_SLIDE_MODE),
    ),
    "rules": WidgetVisibility("rules_overlay_show_mode", "always", (*_SIMPLE, AUCTION_WIDGET_SLIDE_MODE)),
    "wheel": WidgetVisibility(
        "wheel_overlay_show_mode", "context",
        (_HIDDEN, ("context", "Когда колесо используется"), _ALWAYS),
    ),
}


def auction_widget_linked(settings: Mapping[str, Any], widget: str) -> bool:
    link_key, _, _ = AUCTION_WIDGET_BINDINGS[widget]
    return settings.get(link_key) == "1"


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
    if (
        widget in AUCTION_WIDGET_BINDINGS
        and mode == AUCTION_WIDGET_SLIDE_MODE[0]
        and not auction_widget_linked(settings, widget)
    ):
        return spec.default
    return mode if any(mode == value for value, _label in spec.options) else spec.default


def auction_widget_motion(
    settings: Mapping[str, Any], widget: str, *, auction_widgets_visible: bool = False,
) -> dict[str, Any]:
    _, direction_key, seconds_key = AUCTION_WIDGET_BINDINGS[widget]
    direction = settings.get(direction_key)
    if not any(direction == value for _label, value in AUCTION_WIDGET_SLIDE_DIRECTIONS):
        direction = AUCTION_WIDGET_SLIDE_DIRECTIONS[0][1]
    try:
        seconds = float(settings.get(seconds_key, AUCTION_WIDGET_SLIDE_DEFAULT_SECONDS))
    except (TypeError, ValueError):
        seconds = AUCTION_WIDGET_SLIDE_DEFAULT_SECONDS
    if not math.isfinite(seconds):
        seconds = AUCTION_WIDGET_SLIDE_DEFAULT_SECONDS
    return {
        "follow_auction_tab": auction_widget_linked(settings, widget),
        "auction_widgets_visible": auction_widgets_visible,
        "direction": direction,
        "duration_seconds": max(
            AUCTION_WIDGET_SLIDE_MIN_SECONDS, min(AUCTION_WIDGET_SLIDE_MAX_SECONDS, seconds),
        ),
    }


def wheel_glow_appearance(settings: Mapping[str, Any]) -> dict[str, Any]:
    """One validated, read-only local+OBS wheel appearance contract."""
    raw_color = str(settings.get(WHEEL_GLOW_COLOR_KEY) or WHEEL_GLOW_COLOR_DEFAULT).strip()
    color = raw_color.upper() if re.fullmatch(r"#[0-9a-fA-F]{6}", raw_color) else WHEEL_GLOW_COLOR_DEFAULT
    return {
        "glow_enabled": str(settings.get(WHEEL_GLOW_ENABLED_KEY,
                                      "1" if WHEEL_GLOW_ENABLED_DEFAULT else "0")) == "1",
        "glow_color": color,
        "pointer_label_enabled": str(settings.get(
            WHEEL_POINTER_LABEL_ENABLED_KEY,
            "1" if WHEEL_POINTER_LABEL_ENABLED_DEFAULT else "0",
        )) == "1",
    }


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
