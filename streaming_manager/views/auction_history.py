from __future__ import annotations

from typing import Any

from ..database import display_datetime_local


MODE_LABELS = {
    "max_amount": "Максимальная сумма",
    "weighted_wheel": "Взвешенное колесо",
}


def _points(value: Any) -> str:
    try:
        number = max(0, int(value or 0))
    except (TypeError, ValueError):
        number = 0
    return f"{number:,}".replace(",", " ")


def _duration(milliseconds: Any) -> str:
    try:
        value = max(0, int(milliseconds or 0))
    except (TypeError, ValueError):
        value = 0
    hours, remainder = divmod(value, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def _signed_duration(milliseconds: Any) -> str:
    try:
        value = int(milliseconds or 0)
    except (TypeError, ValueError):
        value = 0
    sign = "+" if value >= 0 else "−"
    return f"{sign}{_duration(abs(value))}"


def format_auction_history_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return compact, human-readable A7 presentation for one audit event.

    The authoritative timestamp and raw before/after payload stay in
    ``change_log``; this helper only derives operator-facing text.
    """
    entity_type = str(event.get("entity_type") or "")
    action = str(event.get("action") or "")
    before = event.get("before") if isinstance(event.get("before"), dict) else {}
    after = event.get("after") if isinstance(event.get("after"), dict) else {}
    title = str(event.get("title") or after.get("title") or before.get("title") or "").strip()
    game_id = event.get("game_id")

    exact_time = display_datetime_local(event.get("created_at"))
    short_time = exact_time.rsplit(" ", 1)[-1] if exact_time else "—"

    icon = "•"
    kind = action.upper() or "СОБЫТИЕ"
    object_text = title or "Аукцион"
    details = ""

    if entity_type == "auction_bid":
        if action == "add":
            icon = "+"
            kind = "ДОБАВЛЕНИЕ"
            added = after.get("added_sm_points")
            total = after.get("sm_points")
            details = f"+{_points(added)} баллов → {_points(total)}"
        elif action == "decrease":
            icon = "−"
            kind = "УМЕНЬШЕНИЕ"
            decreased = after.get("decreased_sm_points")
            total = after.get("sm_points")
            details = f"−{_points(decreased)} баллов → {_points(total)}"

    elif entity_type == "auction_lot":
        if action == "create":
            icon = "+"
            kind = "НОВЫЙ ЛОТ"
            added = after.get("added_sm_points")
            starting = after.get("starting_sm_points")
            details = (
                f"Старт: {_points(starting)}; добавлено: +{_points(added)}"
            )
        elif action == "increment":
            icon = "+"
            kind = "ЛОТ ДОПОЛНЕН"
            details = f"+{_points(after.get('added_sm_points'))} баллов"
        elif action == "reuse":
            icon = "•"
            kind = "ЛОТ ВЫБРАН"
            details = "Существующий лот использован без изменения суммы"
        elif action == "delete":
            icon = "×"
            kind = "ЛОТ УДАЛЁН"
            details = "Удалён из текущего аукциона"

    elif entity_type == "auction_session":
        object_text = title or "Аукцион"
        if action == "create":
            icon = "▶"
            kind = "СТАРТ СЕССИИ"
            mode = MODE_LABELS.get(str(after.get("mode") or ""), str(after.get("mode") or ""))
            duration_ms = after.get("duration_ms")
            lots = after.get("lots")
            parts = []
            if mode:
                parts.append(mode)
            if lots is not None:
                parts.append(f"лотов: {lots}")
            if duration_ms is not None:
                parts.append(f"таймер: {_duration(duration_ms)}")
            details = "; ".join(parts)
        elif action == "pause":
            icon = "Ⅱ"
            kind = "ПАУЗА"
            details = f"Осталось: {_duration(after.get('remaining_ms'))}"
        elif action == "resume":
            icon = "▶"
            kind = "ПРОДОЛЖЕНИЕ"
            details = f"Осталось: {_duration(after.get('remaining_ms'))}"
        elif action == "adjust_time":
            icon = "±"
            kind = "ИЗМЕНЕНИЕ ВРЕМЕНИ"
            details = (
                f"{_signed_duration(after.get('delta_ms'))}; "
                f"осталось: {_duration(after.get('remaining_ms'))}"
            )
        elif action == "reset_timer":
            icon = "↺"
            kind = "СБРОС ТАЙМЕРА"
            details = f"Установлено: {_duration(after.get('remaining_ms'))}"
        elif action == "auto_extend":
            icon = "⏱"
            kind = "АВТОПРОДЛЕНИЕ"
            reason_labels = {
                "leader_change": "смена лидера",
                "new_lot": "новый временный лот",
                "external_donation": "внешнее пожертвование",
            }
            reason_codes = after.get("matched_reasons") or []
            labels = [
                reason_labels.get(str(code), str(code))
                for code in reason_codes
            ]
            details = (
                f"+{_duration(after.get('delta_ms'))}; "
                f"осталось: {_duration(after.get('remaining_ms'))}"
            )
            if labels:
                details += "; " + ", ".join(labels)
        elif action == "finish":
            icon = "■"
            kind = "ПРИЁМ СТАВОК ЗАВЕРШЁН"
            winner_game_id = after.get("winner_game_id")
            tie_game_ids = after.get("tie_game_ids") or []
            if winner_game_id:
                details = "Определён лидер по максимальной сумме"
            elif tie_game_ids:
                details = f"Ничья: {len(tie_game_ids)} лота(ов)"
            else:
                details = "Победитель не определён"
        elif action == "wheel_duration":
            icon = "⏱"
            kind = "ВРЕМЯ КОЛЕСА"
            details = f"Установлено: {_duration(after.get('wheel_duration_ms'))}"
        elif action == "tie_overtime":
            icon = "+"
            kind = "ДОП. ВРЕМЯ"
            details = f"Таймер: {_duration(after.get('duration_ms'))}"
        elif action == "tie_wheel":
            icon = "◉"
            kind = "ТАЙ-БРЕЙК: КОЛЕСО"
            details = f"Вращение: {_duration(after.get('wheel_duration_ms'))}"
        elif action == "wheel_animation":
            icon = "◉"
            kind = "КОЛЕСО ЗАПУЩЕНО"
            details = f"Вращение: {_duration(after.get('wheel_duration_ms'))}"
        elif action == "wheel":
            icon = "★"
            kind = "ПОБЕДИТЕЛЬ КОЛЕСА"
            details = "Победитель выбран"
        elif action == "confirm_winner":
            icon = "✓"
            kind = "ПОБЕДИТЕЛЬ ПОДТВЕРЖДЁН"
            details = "Результат аукциона подтверждён"
        elif action == "cancel":
            icon = "×"
            kind = "АУКЦИОН ОТМЕНЁН"
            details = "Сессия завершена без подтверждённого победителя"

    first_line = f"{icon}  {kind}  ·  {short_time}"
    second_parts = [part for part in (object_text, details) if part]
    text = first_line
    if second_parts:
        text += "\n" + " — ".join(second_parts)

    return {
        "text": text,
        "exact_time": exact_time,
        "game_id": game_id,
        "event_id": event.get("id"),
        "kind": kind,
    }
