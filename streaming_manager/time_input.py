from __future__ import annotations


def parse_duration_input(text: str, *, example: str) -> int:
    """Parse auction duration input.

    Accepted forms:
    - HHMMSS: six digits; milliseconds are always normalized to .000.
    - HH:MM:SS.mmm: legacy/full form kept for compatibility.
    """
    raw = str(text or "").strip()
    if not raw:
        raise ValueError(
            "Поле времени пустое. Введите 6 цифр в формате ЧЧММСС "
            f"(например {example.replace(':', '').split('.', 1)[0]}) или полное время "
            f"в формате ЧЧ:ММ:СС.мс, например {example}"
        )

    if raw.isdigit():
        if len(raw) != 6:
            raise ValueError(
                "Для сокращённого ввода используйте ровно 6 цифр в формате "
                "ЧЧММСС, например 001530."
            )
        hours = int(raw[0:2])
        minutes = int(raw[2:4])
        seconds = int(raw[4:6])
        millis = 0
    else:
        try:
            hhmmss, millis_text = raw.split(".", 1)
            hours_text, minutes_text, seconds_text = hhmmss.split(":", 2)
            if not (
                hours_text.isdigit()
                and minutes_text.isdigit()
                and seconds_text.isdigit()
                and millis_text.isdigit()
            ):
                raise ValueError
            if len(millis_text) > 3:
                raise ValueError
            hours = int(hours_text)
            minutes = int(minutes_text)
            seconds = int(seconds_text)
            millis = int(millis_text.ljust(3, "0"))
        except (ValueError, AttributeError):
            raise ValueError(
                "Введите 6 цифр в формате ЧЧММСС, например 001530, "
                f"или полное время ЧЧ:ММ:СС.мс, например {example}."
            ) from None

    if minutes > 59 or seconds > 59 or millis > 999:
        raise ValueError(
            "Минуты и секунды должны быть от 00 до 59, миллисекунды — от 000 до 999."
        )

    return (
        hours * 3_600_000
        + minutes * 60_000
        + seconds * 1000
        + millis
    )
