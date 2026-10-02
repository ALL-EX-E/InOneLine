from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = PROJECT_ROOT / ".github" / "workflows"

REQUIRED_MAJOR = {
    "actions/checkout": "v7",
    "actions/setup-python": "v7",
    "actions/upload-artifact": "v7",
}

USE_RE = re.compile(r"\buses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)")


def main() -> None:
    found: dict[str, list[tuple[str, int, str]]] = {name: [] for name in REQUIRED_MAJOR}
    violations: list[str] = []

    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            match = USE_RE.search(line)
            if not match:
                continue
            action, version = match.groups()
            if action not in REQUIRED_MAJOR:
                continue
            found[action].append((path.name, line_no, version))
            expected = REQUIRED_MAJOR[action]
            if version != expected:
                violations.append(
                    f"{path.name}:{line_no}: {action}@{version}; expected {action}@{expected}"
                )

    missing = [action for action, refs in found.items() if not refs]
    if missing:
        violations.append("Required actions not referenced anywhere: " + ", ".join(sorted(missing)))

    if violations:
        raise AssertionError("\n".join(violations))

    for action in sorted(found):
        refs = ", ".join(f"{name}:{line}@{version}" for name, line, version in found[action])
        print(f"{action}={refs}")
    print("GITHUB_ACTIONS_MAJOR_REFRESH=PASS")


if __name__ == "__main__":
    main()
