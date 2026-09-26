from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import re
from typing import Any, Iterable


class ConversionRateError(ValueError):
    pass


class ConversionUnitError(ValueError):
    pass


UNIT_KIND_CURRENCY = "currency"
UNIT_KIND_SERVICE = "service"
_VALID_UNIT_KEY = re.compile(r"^[A-Z0-9][A-Z0-9_.:-]{0,63}$")
_CURRENCY_CODE = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True)
class ConversionUnit:
    """One source unit that may be converted into whole program points.

    ``unit`` is a stable storage/API key. ``label`` is operator-facing text.
    ``service`` is optional presentation metadata. ``kind`` is either
    ``currency`` or ``service``; when omitted it is inferred conservatively:
    three-letter alphabetic codes are currencies, everything else is a
    service-specific/non-monetary unit.
    """

    unit: str
    label: str
    service: str = ""
    kind: str = ""

    def normalized_unit(self) -> str:
        return normalize_unit_key(self.unit)

    def normalized_kind(self) -> str:
        kind = str(self.kind or "").strip().lower()
        if kind:
            if kind not in {UNIT_KIND_CURRENCY, UNIT_KIND_SERVICE}:
                raise ConversionUnitError(f"Неизвестный тип единицы: {self.kind!r}")
            return kind
        return (
            UNIT_KIND_CURRENCY
            if _CURRENCY_CODE.fullmatch(self.normalized_unit())
            else UNIT_KIND_SERVICE
        )


# RUB remains the only permanently seeded currency because it is the explicit
# schema-12 legacy migration/default unit. Other currencies are shown when a
# connected adapter reports them, when an event actually uses them, or after a
# user saves a rate for them.
BASE_CURRENCY_CONVERSION_UNITS: tuple[ConversionUnit, ...] = (
    ConversionUnit("RUB", "RUB", kind=UNIT_KIND_CURRENCY),
)


def normalize_unit_key(value: Any) -> str:
    unit = str(value or "").strip().upper()
    if not unit:
        raise ConversionUnitError("Не указана исходная единица конвертации.")
    if not _VALID_UNIT_KEY.fullmatch(unit):
        raise ConversionUnitError(
            "Код единицы может содержать только латинские буквы, цифры, "
            "точку, подчёркивание, двоеточие и дефис (до 64 символов)."
        )
    return unit


def infer_unit_kind(unit: Any) -> str:
    normalized = normalize_unit_key(unit)
    return (
        UNIT_KIND_CURRENCY
        if _CURRENCY_CODE.fullmatch(normalized)
        else UNIT_KIND_SERVICE
    )


def merge_conversion_units(*unit_groups: Iterable[ConversionUnit]) -> list[ConversionUnit]:
    """Merge visible conversion rows without inventing connection state.

    Duplicate canonical unit keys are collapsed. Later groups may improve the
    presentation metadata (label/service/kind) for an already known unit while
    preserving one logical row.
    """
    result: list[ConversionUnit] = []
    positions: dict[str, int] = {}
    for group in unit_groups:
        for item in group:
            unit = item.normalized_unit()
            descriptor = ConversionUnit(
                unit,
                str(item.label or unit),
                str(item.service or ""),
                item.normalized_kind(),
            )
            if unit not in positions:
                positions[unit] = len(result)
                result.append(descriptor)
                continue
            index = positions[unit]
            previous = result[index]
            # Connected/provider metadata is normally supplied later and is
            # more informative than a registry fallback such as label=unit.
            result[index] = ConversionUnit(
                unit,
                descriptor.label or previous.label,
                descriptor.service or previous.service,
                descriptor.kind or previous.kind,
            )
    return result


def parse_decimal(value: Any) -> Decimal:
    """Parse user/source numeric text without binary floating-point arithmetic."""
    if value is None:
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    text = str(value).strip().replace(" ", "").replace("\u00a0", "").replace(",", ".")
    if not text:
        return Decimal(0)
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Некорректное числовое значение: {value!r}") from exc


def decimal_to_storage_text(value: Any) -> str:
    number = parse_decimal(value)
    if not number.is_finite():
        raise ValueError("Числовое значение должно быть конечным.")
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def parse_positive_rate(value: Any) -> Decimal:
    rate = parse_decimal(value)
    if not rate.is_finite() or rate <= 0:
        raise ConversionRateError("Курс должен быть положительным числом больше нуля.")
    return rate


def convert_source_to_sm_points(amount: Any, points_per_unit: Any) -> int:
    """Convert any non-negative source value to whole program points.

    The rounding rule is source-neutral: currency, channel points, rewards and
    any other external unit all use the same calculation. First apply the
    configured rate, then round every positive fractional result upward to the
    next whole point. Exact integers and zero remain unchanged.
    """
    source = parse_decimal(amount)
    if not source.is_finite() or source < 0:
        raise ValueError("Исходное значение не может быть отрицательным.")
    rate = parse_positive_rate(points_per_unit)
    converted = source * rate
    if converted == 0:
        return 0
    return int(converted.to_integral_value(rounding=ROUND_CEILING))


def parse_sm_points(value: Any) -> int:
    """Parse a direct points value, rounding a positive fraction upward."""
    return convert_source_to_sm_points(value, Decimal(1))


def format_rate(value: Any) -> str:
    rate = parse_positive_rate(value)
    text = format(rate.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",")
