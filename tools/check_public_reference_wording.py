from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".html", ".css", ".js", ".ts", ".json",
    ".yml", ".yaml", ".toml", ".ini", ".cfg", ".iss", ".bat", ".cmd", ".ps1",
}

PATTERNS = (
    ("comparison_like_in", re.compile(r"\bкак\s+в\s+[«\"'“]?[A-ZА-ЯЁ][A-Za-zА-Яа-яЁё0-9_.+-]*", re.IGNORECASE)),
    ("comparison_by_analogy", re.compile(r"\bпо\s+аналогии\s+с\b", re.IGNORECASE)),
    ("comparison_after_example", re.compile(r"\bпо\s+образцу\b", re.IGNORECASE)),
    ("comparison_in_style", re.compile(r"\bв\s+стиле\s+[«\"'“]?[A-ZА-ЯЁ][A-Za-zА-Яа-яЁё0-9_.+-]*", re.IGNORECASE)),
    ("comparison_like_suffix_ru", re.compile(r"[A-Za-zА-Яа-яЁё0-9_.+]+[-‑–—]подобн\w*", re.IGNORECASE)),
    ("comparison_like_suffix_en", re.compile(r"[A-Za-z0-9_.+]+[-‑–—]style\b", re.IGNORECASE)),
    ("comparison_english", re.compile(r"\b(?:inspired\s+by|model(?:l)?ed\s+after|like\s+in)\b", re.IGNORECASE)),
)


def tracked_files() -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z"])
    return [Path(p.decode("utf-8")) for p in raw.split(b"\0") if p]


def main() -> int:
    violations: list[str] = []
    for path in tracked_files():
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for rule, pattern in PATTERNS:
                if pattern.search(line):
                    violations.append(f"{path}:{line_no}: {rule}: {line.strip()}")

    if violations:
        print("Public reference-wording check failed:")
        print("\n".join(violations))
        return 1

    print("Public reference-wording check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
