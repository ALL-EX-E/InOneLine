from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.create_source_snapshot import create_source_snapshot


def tracked_source_files() -> set[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {
        line.strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line.strip() and not line.strip().replace("\\", "/").startswith(".github/")
    }


fake_paths = (
    PROJECT_ROOT / "build" / "fake-build.bin",
    PROJECT_ROOT / "streaming_manager" / "__pycache__" / "fake.pyc",
    PROJECT_ROOT / "conditional_ui_smoke.py",
)
try:
    for path in fake_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"SHOULD-NOT-BE-IN-SOURCE")

    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        archive_path = Path(tmp) / "source.zip"
        create_source_snapshot(archive_path)
        with zipfile.ZipFile(archive_path, "r") as archive:
            names = set()
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = info.filename.replace("\\", "/")
                while name.startswith("./"):
                    name = name[2:]
                names.add(name)

        expected = tracked_source_files()
        assert names == expected, (
            f"snapshot mismatch: missing={sorted(expected - names)[:10]} "
            f"extra={sorted(names - expected)[:10]}"
        )
        assert not any("/__pycache__/" in f"/{name}" for name in names)
        assert not any(name.endswith(".pyc") for name in names)
        assert not any(name.startswith("build/") for name in names)
        assert not any(name.startswith("dist/") for name in names)
        assert "conditional_ui_smoke.py" not in names
        assert not any(name.startswith(".github/") for name in names)

        print(f"SOURCE_SNAPSHOT_FILES={len(names)}")
        print(f"SOURCE_SNAPSHOT_BYTES={archive_path.stat().st_size}")
finally:
    for path in reversed(fake_paths):
        path.unlink(missing_ok=True)
    for directory in (
        PROJECT_ROOT / "streaming_manager" / "__pycache__",
        PROJECT_ROOT / "build",
    ):
        try:
            directory.rmdir()
        except OSError:
            pass

print("CLEAN_SOURCE_SNAPSHOT=PASS")
