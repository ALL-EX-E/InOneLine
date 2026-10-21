from __future__ import annotations

from typing import Any

from ..database import display_datetime_local


MODE_LABELS = {
    "max_amount": "Максимальная сумма",
    "weighted_wheel": "Взвешенное колесо",
}


def format_completed_auction_mode(
    session: dict[str, Any],
    evidence: dict[str, Any] | None = None,
) -> str:
    """Render executed winner-selection stages from existing audit and snapshots."""
    mode = str(session.get("mode") or "")
    if mode not in {"max_amount", "weighted_wheel"}:
        return MODE_LABELS.get(mode, mode or "—")

    evidence = evidence if isinstance(evidence, dict) else {}
    events = evidence.get("events") or []
    snapshots = evidence.get("spins") or []
    allowed = {"standard", "elimination"}
    selected = str(session.get("wheel_format") or "standard")
    selected = selected if selected in allowed else "standard"

    by_run = {
        str(spin.get("run_id") or ""): spin
        for spin in snapshots if isinstance(spin, dict) and spin.get("run_id")
    }
    by_index = {
        int(spin.get("spin_index") or 1): spin
        for spin in snapshots if isinstance(spin, dict)
    }

    def snapshot_format(spin: dict[str, Any] | None) -> str | None:
        if not isinstance(spin, dict):
            return None
        result_kind = str(spin.get("result_kind") or "")
        if result_kind == "eliminated":
            return "elimination"
        if result_kind == "winner":
            return "standard"
        return None

    current_format = selected
    tie_wheel_chosen = False
    recorded_spins: list[tuple[int, str]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        action = str(event.get("action") or "")
        after = event.get("after")
        after = after if isinstance(after, dict) else {}
        new_format = str(after.get("wheel_format") or "")
        if action in {"create", "wheel_format"} and new_format in allowed:
            current_format = new_format
        elif action == "tie_wheel":
            tie_wheel_chosen = True
        elif action == "wheel":
            try:
                index = int(after.get("spin_index") or len(recorded_spins) + 1)
            except (TypeError, ValueError):
                index = len(recorded_spins) + 1
            snapshot = by_run.get(str(after.get("verification_run_id") or ""))
            if snapshot is None:
                snapshot = by_index.get(index)
            actual = (
                new_format if new_format in allowed
                else snapshot_format(snapshot) or current_format
            )
            recorded_spins.append((index, actual))
            current_format = actual

    seen_indices = {index for index, _fmt in recorded_spins}
    for spin in snapshots:
        if not isinstance(spin, dict):
            continue
        index = int(spin.get("spin_index") or 1)
        if index not in seen_indices:
            actual = snapshot_format(spin)
            if actual is not None:
                recorded_spins.append((index, actual))
    recorded_spins.sort(key=lambda item: item[0])

    labels = {"standard": "Обычное колесо", "elimination": "Выбывание"}
    actual_path: list[str] = []
    for _index, wheel_format in recorded_spins:
        name = labels[wheel_format]
        if not actual_path or actual_path[-1] != name:
            actual_path.append(name)

    if mode == "max_amount":
        if not actual_path:
            return "Максимальная сумма"
        if tie_wheel_chosen:
            return "Максимальная сумма → Колесо при ничьей"
        return "Максимальная сумма → " + " → ".join(actual_path)

    if not actual_path:
        return labels[selected]
    return " → ".join(actual_path)


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
        elif action == "post_expiry_add":
            icon = "+"
            kind = "БАЛЛЫ ПОСЛЕ 00:00"
            details = (
                f"+{_points(after.get('added_sm_points'))} баллов; "
                f"итог: {_points(after.get('sm_points'))}; "
                "таймер не перезапущен"
            )
        elif action == "post_expiry_decrease":
            icon = "−"
            kind = "УМЕНЬШЕНИЕ ПОСЛЕ 00:00"
            details = (
                f"−{_points(after.get('decreased_sm_points'))} баллов; "
                f"итог: {_points(after.get('sm_points'))}; "
                "таймер не перезапущен"
            )

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
        elif action in {"post_expiry_create", "post_expiry_merge"}:
            icon = "+" if action == "post_expiry_create" else "⇄"
            kind = (
                "НОВЫЙ ЛОТ ПОСЛЕ 00:00"
                if action == "post_expiry_create"
                else "ЛОТ ОБЪЕДИНЁН ПОСЛЕ 00:00"
            )
            details = (
                f"Добавлено: +{_points(after.get('added_sm_points'))} баллов; "
                "таймер не перезапущен"
            )
            if action == "post_expiry_merge":
                details += "; объединено с существующим лотом"
        elif action == "post_expiry_title_lot":
            icon = "+"
            kind = "ЛОТ ИЗ ОЖИДАЮЩЕГО ПОСТУПЛЕНИЯ"
            details = (
                "Создан временный лот"
                if after.get("temporary")
                else "Использован существующий лот"
            )
        elif action == "post_expiry_temporary_rename":
            icon = "⇄"
            kind = "ЛОТ ПЕРЕИМЕНОВАН"
            old_title = str(before.get("old_title") or "—")
            new_title = str(after.get("new_title") or "—")
            object_text = new_title
            details = (
                f"«{old_title}» → «{new_title}»; "
                f"баллы сохранены: {_points(after.get('sm_points'))}; "
                "таймер не перезапущен"
            )
        elif action == "post_expiry_permanent_exclude":
            icon = "×"
            kind = "ПОСТОЯННЫЙ ЛОТ ИСКЛЮЧЁН"
            object_text = str(before.get("title") or title or "Лот")
            details = (
                f"Итог на момент исключения: "
                f"{_points(before.get('sm_points'))} баллов; "
                "игра и её баллы сохранены"
            )
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
            if str(after.get("wheel_format") or "") == "elimination":
                kind = "ВЫБЫВАНИЕ: ЛОТ ВЫБРАН"
                details = (
                    f"Раунд {int(after.get('spin_index') or 1)}; "
                    "ожидает действия «В архив»"
                )
            else:
                kind = "ПОБЕДИТЕЛЬ КОЛЕСА"
                details = (
                    f"Раунд {int(after.get('spin_index') or 1)}; "
                    "победитель выбран"
                )
        elif action == "wheel_spin_stopped":
            icon = "■"
            kind = "ВРАЩЕНИЕ ОСТАНОВЛЕНО"
            details = (
                "Текущая анимация остановлена; "
                "сохранённый результат не подтверждён"
            )
        elif action == "wheel_spin_replayed":
            icon = "↺"
            kind = "ВРАЩЕНИЕ ПОВТОРЕНО"
            details = (
                "Повтор анимации сохранённого результата "
                "без нового определения победителя"
            )
        elif action == "wheel_format":
            icon = "⇄"
            kind = "ФОРМАТ КОЛЕСА"
            label = {
                "standard": "Обычное",
                "elimination": "Выбывание",
            }.get(str(after.get("wheel_format") or ""), str(after.get("wheel_format") or ""))
            details = f"Выбран формат: {label}"
        elif action == "elimination_archive":
            icon = "→"
            kind = "ЛОТ ВЫБЫЛ"
            remaining = int(after.get("remaining_lots") or 0)
            details = (
                "Отправлен в архив; осталось активных лотов: "
                f"{remaining}"
            )
            if remaining == 0:
                details += "; аукцион завершён без победителя"
        elif action in {
            "post_expiry_manual_bid",
            "post_expiry_manual_decrease",
            "post_expiry_manual_lot",
            "post_expiry_pending_correction",
            "post_expiry_permanent_lot_exclude",
            "post_expiry_temporary_lot_delete",
        }:
            icon = "±"
            labels = {
                "post_expiry_manual_bid": "ПЕРЕСЧЁТ ПОСЛЕ ДОБАВЛЕНИЯ БАЛЛОВ",
                "post_expiry_manual_decrease": "ПЕРЕСЧЁТ ПОСЛЕ УМЕНЬШЕНИЯ БАЛЛОВ",
                "post_expiry_manual_lot": "ПЕРЕСЧЁТ ПОСЛЕ ИЗМЕНЕНИЯ ЛОТА",
                "post_expiry_pending_correction": "УЧТЕНО ОЖИДАВШЕЕ ПОСТУПЛЕНИЕ",
                "post_expiry_permanent_lot_exclude": "ПЕРЕСЧЁТ ПОСЛЕ ИСКЛЮЧЕНИЯ ЛОТА",
                "post_expiry_temporary_lot_delete": "ПЕРЕСЧЁТ ПОСЛЕ УДАЛЕНИЯ ЛОТА",
            }
            kind = labels[action]
            status_names = {
                "winner_selected": "определён лидер",
                "tie_break_required": "ничья",
                "awaiting_wheel": "ожидается колесо",
                "finished_no_winner": "без победителя",
                "confirmed": "результат подтверждён",
            }
            status = str(after.get("status") or "")
            parts = []
            if status:
                parts.append(status_names.get(status, status))
            target = after.get("target_game_id")
            if target is None:
                target = after.get("excluded_game_id", after.get("removed_game_id"))
            if target is not None:
                parts.append(f"ID лота: {target}")
            credited = after.get("credited_sm_points")
            if credited is not None:
                amount = int(credited)
                sign = "−" if amount < 0 else "+"
                parts.append(f"изменение: {sign}{abs(amount)} баллов")
            parts.append("без перезапуска таймера")
            details = "; ".join(parts)
        elif action == "confirm_winner":
            icon = "✓"
            kind = "ПОБЕДИТЕЛЬ ПОДТВЕРЖДЁН"
            details = "Результат аукциона подтверждён"
        elif action == "cancel":
            icon = "×"
            kind = "АУКЦИОН ОТМЕНЁН"
            details = "Сессия завершена без подтверждённого победителя"
            promoted = after.get("promoted_temporary_lots")
            if isinstance(promoted, list) and promoted:
                details += f"; временных лотов сохранено: {len(promoted)}"

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
