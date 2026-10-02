from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streaming_manager.single_instance import acquire_instance_lock


def probe(data_dir: Path) -> int:
    lock = acquire_instance_lock(data_dir)
    if lock is None:
        return 23
    lock.unlock()
    return 0


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--probe":
        raise SystemExit(probe(Path(sys.argv[2])))

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        data_dir = Path(tmp) / "data"
        first = acquire_instance_lock(data_dir)
        assert first is not None

        blocked = subprocess.run(
            [sys.executable, __file__, "--probe", str(data_dir)],
            cwd=PROJECT_ROOT,
            check=False,
        )
        assert blocked.returncode == 23, blocked.returncode

        first.unlock()

        allowed = subprocess.run(
            [sys.executable, __file__, "--probe", str(data_dir)],
            cwd=PROJECT_ROOT,
            check=False,
        )
        assert allowed.returncode == 0, allowed.returncode

    print("SINGLE_INSTANCE_LOCK=PASS")


if __name__ == "__main__":
    main()
