from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = PROJECT_ROOT / ".github" / "workflows"

REQUIRED_MAJOR = {
    "actions/checkout": "v7",
    "actions/setup-python": "v7",
    "actions/upload-artifact": "v7",
}

USE_RE = re.compile(r"\buses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)")


def check_native_failure_guards() -> None:
    workflow = (WORKFLOWS / "regression-foundation-1.0.8.yml").read_text(encoding="utf-8")
    blocks = re.findall(r"(?m)^        run: \|\n((?:          [^\n]*\n|\n)+)", workflow)
    batches = []
    for block in blocks:
        lines = [line[10:] if line.startswith("          ") else line for line in block.splitlines()]
        commands = [i for i, line in enumerate(lines) if line.startswith("python ")]
        if len(commands) < 2:
            continue
        for i in commands:
            assert i + 1 < len(lines) and lines[i + 1].startswith("if ($LASTEXITCODE -ne 0)"), (
                f"Native command failure can be masked: {lines[i]}"
            )
        batches.append((lines, commands))
    assert len(batches) == 3, "Dependency/UI/database regression batches changed; review failure coverage"
    print("WORKFLOW_NATIVE_FAILURE_GUARDS=PASS")

    pwsh = shutil.which("pwsh")
    if pwsh is None:
        print("WORKFLOW_NATIVE_FAILURE_EXECUTION=SKIP (pwsh unavailable)")
        return
    probes = 0
    marker = "NATIVE_SEQUENCE_COMPLETED"
    for lines, commands in batches:
        for failure in [None, *commands]:
            probe = list(lines)
            for i in commands:
                probe[i] = f'python -c "raise SystemExit({23 if i == failure else 0})"'
            script = "$ErrorActionPreference = 'Stop'\n" + "\n".join(probe) + f"\nWrite-Output '{marker}'"
            result = subprocess.run(
                [pwsh, "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True, text=True, timeout=30,
            )
            if failure is None:
                assert result.returncode == 0 and marker in result.stdout, result.stderr
            else:
                assert result.returncode != 0 and marker not in result.stdout, (
                    f"Failure at {lines[failure]} did not stop the batch: {result.stdout} {result.stderr}"
                )
                probes += 1
    print(f"WORKFLOW_NATIVE_FAILURE_EXECUTION=PASS ({probes} failure probes)")


def main() -> None:
    check_native_failure_guards()
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
