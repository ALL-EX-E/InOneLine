from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def create_source_snapshot(output: str | Path, *, ref: str = "HEAD") -> Path:
    """Create a clean source ZIP from Git-tracked bytes only.

    The old candidate workflows copied the already-built workspace and could
    therefore capture build/, __pycache__, *.pyc and generated smoke files.
    git archive makes ignored/untracked build output structurally impossible
    to include.
    """
    target = Path(output).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)

    command = [
        "git",
        "archive",
        "--format=zip",
        f"--output={target}",
        str(ref),
        "--",
        ".",
        ":(exclude).github",
        ":(exclude).github/**",
    ]
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    if not target.is_file() or target.stat().st_size <= 0:
        raise RuntimeError("Source snapshot was not created")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="Destination .zip")
    parser.add_argument("--ref", default="HEAD", help="Git ref/commit to archive")
    args = parser.parse_args()
    path = create_source_snapshot(args.output, ref=args.ref)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
