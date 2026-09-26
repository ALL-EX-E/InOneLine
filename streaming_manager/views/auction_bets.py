from __future__ import annotations

from typing import Any

from ..database import display_datetime_local


def _points(value: Any) -> str:
    try:
        number = max(0, int(value or 0))
    except (TypeError, ValueError):
        number = 0
    return f"{number:,}".replace(",", " ")


def _amount(value: Any) -> str:
    text = str(value or "").strip()
    return text or "0"


def format_integration_bet_event(
    event: dict[str, Any],
    *,
    source_label: str | None = None,
    source_unit_label: str | None = None,
) -> dict[str, Any]:
    """Return compact B5 presentation for one accepted integration bet.

    B5 is read-only operator presentation.  The authoritative source remains
    ``external_events`` + ``contributions`` + the successful
    ``integration_event`` audit row; this helper does not mutate or reinterpret
    provider events.
    """
    exact_time = display_datetime_local(event.get("created_at"))
    short_time = exact_time.rsplit(" ", 1)[-1] if exact_time else "—"

    source = str(source_label or event.get("source") or "Интеграция").strip()
    contributor = str(event.get("contributor") or "—").strip() or "—"
    title = str(event.get("title") or "—").strip() or "—"
    source_unit = str(
        source_unit_label
        or event.get("source_unit_label")
        or event.get("source_unit")
        or ""
    ).strip()
    amount = _amount(event.get("source_amount_text"))
    original = f"{amount} {source_unit}".strip()
    credited = _points(event.get("credited_sm_points"))

    return {
        "text": (
            f"{short_time} · {source} · {contributor}\n"
            f"{title} · {original} → {credited} баллов"
        ),
        "exact_time": exact_time,
        "event_id": event.get("id"),
        "external_event_id": str(event.get("external_event_id") or ""),
        "game_id": event.get("game_id"),
        "source": str(event.get("source") or ""),
    }
