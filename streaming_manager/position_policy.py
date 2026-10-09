from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


POSITION_COLUMNS_SINGLE = "position"
POSITION_COLUMNS_START_CURRENT = "start_current"

_COMMON_LIST_SURFACES = {"main_list", "public_list"}
_AUCTION_SURFACES = {"auction", "auction_overlay"}
_ELIMINATION_PROGRESS_RESULTS = {"elimination_selected", "eliminated"}


def position_columns_for_surface(
    surface: str,
    session: Mapping[str, Any] | None,
    entries: Iterable[Mapping[str, Any]] | None = None,
    *,
    elimination_progress: bool = False,
) -> str:
    """Return the position-column presentation for a list surface.

    Common main/public lists always show one effective position. Auction
    surfaces show start/current only after a Max Amount session begins or
    after a direct elimination spin has produced a selected/eliminated lot.
    This is a read-only presentation decision; it never changes session data.
    """
    surface_key = str(surface or "").strip().casefold()
    if surface_key in _COMMON_LIST_SURFACES or surface_key not in _AUCTION_SURFACES:
        return POSITION_COLUMNS_SINGLE
    if not session:
        return POSITION_COLUMNS_SINGLE

    mode = str(session.get("mode") or "").strip().casefold()
    if mode == "max_amount":
        return POSITION_COLUMNS_START_CURRENT
    if mode != "weighted_wheel":
        return POSITION_COLUMNS_SINGLE

    # Archived elimination results are not in the active table rows. Callers
    # may supply read-only evidence from the complete existing session history.
    if elimination_progress:
        return POSITION_COLUMNS_START_CURRENT

    for entry in entries or ():
        result = str(entry.get("result") or "").strip().casefold()
        if result in _ELIMINATION_PROGRESS_RESULTS:
            return POSITION_COLUMNS_START_CURRENT
    return POSITION_COLUMNS_SINGLE
