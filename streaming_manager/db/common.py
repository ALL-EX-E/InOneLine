from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..constants import STATUS_LABELS
from ..conversion import parse_sm_points


@dataclass(slots=True, init=False)
class Game:
    id: int | None
    title: str
    release_date: str | None
    sm_points: int
    coop: int
    status: str
    review: str
    archived: int = 0
    created_at: str | None = None
    updated_at: str | None = None

    def __init__(
        self,
        id: int | None,
        title: str,
        release_date: str | None,
        sm_points: int | None = None,
        coop: int = 0,
        status: str = "not_played",
        review: str = "",
        archived: int = 0,
        created_at: str | None = None,
        updated_at: str | None = None,
        *,
        amount_kopecks: int | None = None,
    ):
        # Legacy constructor compatibility is intentionally one-way. Old callers
        # may still provide kopecks; schema-12 business state is always whole
        # SM points and therefore uses the same 1 RUB = 1 SM ceiling migration.
        if sm_points is None:
            if amount_kopecks is None:
                sm_points = 0
            else:
                legacy = max(0, int(amount_kopecks))
                sm_points = 0 if legacy == 0 else (legacy + 99) // 100
        self.id = id
        self.title = title
        self.release_date = release_date
        self.sm_points = max(0, int(sm_points))
        self.coop = int(coop)
        self.status = status
        self.review = review
        self.archived = int(archived)
        self.created_at = created_at
        self.updated_at = updated_at

    @property
    def amount(self) -> int:
        """Compatibility alias for older API payload builders."""
        return int(self.sm_points)

    @property
    def amount_kopecks(self) -> int:
        """Legacy read-only compatibility view; not authoritative storage."""
        return int(self.sm_points) * 100

    @property
    def status_label(self) -> str:
        return STATUS_LABELS[self.status]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def normalize_text_key(value: str | None) -> str:
    """Unicode-ключ для поиска: регистр не важен, пробелы нормализованы."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    return " ".join(text.split()).casefold()


def normalize_title_key(value: str | None) -> str:
    """Ключ сравнения названий игр."""
    return normalize_text_key(value)


class DuplicateGameError(ValueError):
    """Попытка создать/переименовать игру в уже существующее название."""

    def __init__(self, existing_id: int, existing_title: str):
        self.existing_id = existing_id
        self.existing_title = existing_title
        super().__init__(f"Запись «{existing_title}» уже существует в списке.")


RUSSIAN_MONTHS = {
    "январь": 1, "января": 1, "янв": 1,
    "февраль": 2, "февраля": 2, "фев": 2,
    "март": 3, "марта": 3, "мар": 3,
    "апрель": 4, "апреля": 4, "апр": 4,
    "май": 5, "мая": 5,
    "июнь": 6, "июня": 6, "июн": 6,
    "июль": 7, "июля": 7, "июл": 7,
    "август": 8, "августа": 8, "авг": 8,
    "сентябрь": 9, "сентября": 9, "сен": 9, "сент": 9,
    "октябрь": 10, "октября": 10, "окт": 10,
    "ноябрь": 11, "ноября": 11, "ноя": 11, "нояб": 11,
    "декабрь": 12, "декабря": 12, "дек": 12,
}


def normalize_date_text(value: str | None) -> str:
    """Преобразует пользовательский ввод даты в формат ДД.ММ.ГГГГ."""
    if value is None:
        return ""

    text = str(value).strip()
    if not text:
        return ""

    # Восемь цифр подряд: 26012010.
    if re.fullmatch(r"\d{8}", text):
        try:
            return datetime.strptime(text, "%d%m%Y").strftime("%d.%m.%Y")
        except ValueError as exc:
            raise ValueError("Некорректная дата.") from exc

    # Числовые форматы.
    for fmt in (
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d %m %Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
    ):
        try:
            return datetime.strptime(text, fmt).strftime("%d.%m.%Y")
        except ValueError:
            pass

    # Русское название месяца: 26 января 2010 / 26 январь 2010 / 26 янв 2010.
    match = re.fullmatch(
        r"\s*(\d{1,2})\s+([А-Яа-яЁё.]+)\s+(\d{4})\s*",
        text,
    )
    if match:
        day = int(match.group(1))
        month_word = match.group(2).lower().replace("ё", "е").rstrip(".")
        year = int(match.group(3))
        month = RUSSIAN_MONTHS.get(month_word)

        if month is None:
            raise ValueError(f"Неизвестное название месяца: {match.group(2)!r}.")

        try:
            return datetime(year, month, day).strftime("%d.%m.%Y")
        except ValueError as exc:
            raise ValueError("Некорректная дата.") from exc

    raise ValueError(
        f"Неверный формат даты: {value!r}. "
        "Введите, например, 26.01.2010, 26012010 или «26 января 2010»."
    )


def parse_date(value: str | None) -> str | None:
    normalized = normalize_date_text(value)
    if not normalized:
        return None
    return datetime.strptime(normalized, "%d.%m.%Y").date().isoformat()


def display_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return value


def display_datetime_local(value: str | None) -> str:
    """Показывает ISO-время базы в локальном часовом поясе Windows."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%d.%m.%Y %H:%M:%S")
    except (ValueError, TypeError):
        return str(value).replace("T", " ")[:19]


def points_from_text(value: Any) -> int:
    """Compatibility parser for whole Streaming Manager points."""
    return parse_sm_points(value)


def format_points(points: int) -> str:
    return str(max(0, int(points)))

