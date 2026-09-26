from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTextEdit, QVBoxLayout

from ..database import display_datetime_local, format_points


RNG_LABELS = {
    "local": "Стандартный (локальный)",
    "random_org": "Random.org",
    "random_org_plus": "Random.org+",
}
MODE_LABELS = {
    "weighted_wheel": "Взвешенное колесо",
    "max_amount": "Максимальная сумма / тай-брейк колесом",
}


def _percent(numerator: int, denominator: int) -> str:
    value = (100.0 * numerator / denominator) if denominator > 0 else 0.0
    return f"{value:.2f}".replace(".", ",") + "%"


def format_verification_snapshot(snapshot: dict[str, Any]) -> str:
    participants = list(snapshot.get("participants") or [])
    lines = [
        "IMMUTABLE VERIFICATION SNAPSHOT",
        "",
        f"Run ID: {snapshot.get('run_id') or '—'}",
        f"Алгоритм: {snapshot.get('algorithm_version') or '—'}",
        f"Режим: {MODE_LABELS.get(str(snapshot.get('mode') or ''), str(snapshot.get('mode') or '—'))}",
        f"RNG: {RNG_LABELS.get(str(snapshot.get('rng_method') or ''), str(snapshot.get('rng_method') or '—'))}",
        f"Время фиксации: {display_datetime_local(snapshot.get('created_at')) or '—'}",
        f"Точный timestamp: {snapshot.get('created_at') or '—'}",
        f"Случайное значение: {snapshot.get('rng_value')}",
        f"Диапазон RNG: 0..{max(0, int(snapshot.get('draw_upper') or 0) - 1)}",
        f"Суммарный исходный вес: {format_points(snapshot.get('total_weight') or 0)}",
        f"Equal fallback: {'ДА' if snapshot.get('equal_fallback') else 'НЕТ'}",
        f"Сохранённый победитель: ID {snapshot.get('winner_game_id')} — {snapshot.get('winner_title') or '—'}",
        f"Участников: {len(participants)}",
    ]
    if str(snapshot.get("rng_method") or "") == "random_org_plus":
        verified = snapshot.get("rng_verified")
        verified_text = "ДА" if verified == 1 else "НЕТ" if verified == 0 else "—"
        lines.extend(
            [
                "",
                "RANDOM.ORG+",
                f"Ticket ID: {snapshot.get('rng_ticket_id') or '—'}",
                f"Serial number: {snapshot.get('rng_serial_number') if snapshot.get('rng_serial_number') is not None else '—'}",
                f"Подпись была проверена при получении: {verified_text}",
                f"Signature: {snapshot.get('rng_signature') or '—'}",
                f"Random JSON: {snapshot.get('rng_random_json') or '—'}",
            ]
        )
    lines.extend(["", "УЧАСТНИКИ (математический порядок)"])
    draw_upper = int(snapshot.get("draw_upper") or 0)
    for row in participants:
        lines.append(
            f"{int(row['position'])}. ID {int(row['game_id'])} — {row.get('snapshot_title') or '—'} | "
            f"исходный вес {format_points(row.get('source_weight') or 0)} | "
            f"эффективный вес {format_points(row.get('effective_weight') or 0)} | "
            f"шанс {_percent(int(row.get('effective_weight') or 0), draw_upper)} | "
            f"диапазон [{int(row.get('interval_start') or 0)}; {int(row.get('interval_end') or 0)})"
        )
    return "\n".join(lines)


def format_verification_preview(preview: dict[str, Any]) -> str:
    participants = list(preview.get("participants") or [])
    exact = bool(preview.get("authoritative_input"))
    lines = [
        "ПРЕДВАРИТЕЛЬНЫЕ ДАННЫЕ ПРОВЕРКИ",
        "",
        "Окончательный immutable snapshot создаётся только при реальном вращении.",
        "Открытие этого окна не запускает RNG и ничего не записывает в базу данных.",
        "",
        f"Состав: {'зафиксированные участники текущей awaiting_wheel-сессии' if exact else 'текущий предварительный состав Conduct'}",
        f"Алгоритм: {preview.get('algorithm_version') or '—'}",
        f"Режим: {MODE_LABELS.get(str(preview.get('mode') or ''), str(preview.get('mode') or '—'))}",
        f"RNG: {RNG_LABELS.get(str(preview.get('rng_method') or ''), str(preview.get('rng_method') or '—'))}",
        f"Диапазон будущего RNG: 0..{max(0, int(preview.get('draw_upper') or 0) - 1)}",
        f"Суммарный исходный вес: {format_points(preview.get('total_weight') or 0)}",
        f"Equal fallback: {'ДА' if preview.get('equal_fallback') else 'НЕТ'}",
        f"Участников: {len(participants)}",
        "",
        "УЧАСТНИКИ (математический порядок)",
    ]
    draw_upper = int(preview.get("draw_upper") or 0)
    for row in participants:
        lines.append(
            f"{int(row['position'])}. ID {int(row['game_id'])} — {row.get('snapshot_title') or '—'} | "
            f"исходный вес {format_points(row.get('source_weight') or 0)} | "
            f"эффективный вес {format_points(row.get('effective_weight') or 0)} | "
            f"шанс {_percent(int(row.get('effective_weight') or 0), draw_upper)} | "
            f"диапазон [{int(row.get('interval_start') or 0)}; {int(row.get('interval_end') or 0)})"
        )
    return "\n".join(lines)


def show_readonly_text_dialog(parent, title: str, text: str) -> None:
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.resize(860, 620)
    layout = QVBoxLayout(dialog)
    editor = QTextEdit()
    editor.setReadOnly(True)
    editor.setPlainText(text)
    layout.addWidget(editor, 1)
    buttons = QDialogButtonBox(QDialogButtonBox.Close)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.exec()
