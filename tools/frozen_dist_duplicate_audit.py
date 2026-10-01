from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    files = sorted(
        (p for p in root.rglob("*") if p.is_file()),
        key=lambda p: p.as_posix().casefold(),
    )

    by_size: dict[int, list[Path]] = defaultdict(list)
    for path in files:
        by_size[path.stat().st_size].append(path)

    groups = []
    for size, candidates in sorted(by_size.items()):
        if size <= 0 or len(candidates) < 2:
            continue
        by_hash: dict[str, list[Path]] = defaultdict(list)
        for path in candidates:
            by_hash[sha256(path)].append(path)
        for digest, members in by_hash.items():
            if len(members) > 1:
                groups.append((size, digest, members))

    print(f"FROZEN_FILES={len(files)}")
    print(f"FROZEN_BYTES={sum(p.stat().st_size for p in files)}")
    print(f"EXACT_DUPLICATE_GROUPS={len(groups)}")
    duplicate_bytes = 0
    for size, digest, members in groups:
        duplicate_bytes += size * (len(members) - 1)
        print(f"DUP size={size} sha256={digest}")
        for member in members:
            print(f"  {member.relative_to(root).as_posix()}")
    print(f"EXACT_DUPLICATE_EXTRA_BYTES={duplicate_bytes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
