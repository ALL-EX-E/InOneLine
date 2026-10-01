from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streaming_manager.backup_restore as br
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database


with TemporaryDirectory() as td:
    base = Path(td)
    root = base / "InOneLine"
    paths = AppPaths.from_root(root)
    paths.ensure_runtime_dirs()
    Database(paths.database_path)

    with closing(sqlite3.connect(paths.database_path)) as conn, conn:
        conn.execute(
            "INSERT INTO games(title,release_date,sm_points,coop,status,review,archived,created_at,updated_at) "
            "VALUES('ORIG',NULL,1,0,'not_played','',0,datetime('now'),datetime('now'))"
        )

    (paths.data_dir / "music").mkdir(exist_ok=True)
    (paths.data_dir / "music/a.txt").write_text("ORIG")

    snap_dir = base / "snap"
    snap_dir.mkdir()
    snapshot = br.create_sqlite_backup(paths.database_path, snap_dir)
    archive = base / "full.iolbackup"
    br.create_full_backup_archive(
        snapshot,
        paths.data_dir,
        archive,
        app_version="1.0.8",
        installation_root=root,
    )

    with closing(sqlite3.connect(paths.database_path)) as conn, conn:
        conn.execute("UPDATE games SET title='LIVE' WHERE sm_points=1")
    (paths.data_dir / "music/a.txt").write_text("LIVE")

    staged = br.stage_full_restore_candidate(archive, paths.data_dir)
    real_move = br.shutil.move
    failed = {"done": False}
    staged_music = (Path(staged["staged_dir"]) / "data" / "music").resolve()

    def failing_move(src, dst, *args, **kwargs):
        if Path(src).resolve() == staged_music and not failed["done"]:
            failed["done"] = True
            raise OSError("injected restore failure")
        return real_move(src, dst, *args, **kwargs)

    br.shutil.move = failing_move
    try:
        try:
            br.apply_staged_full_restore(staged["staged_dir"], root)
        except RuntimeError as exc:
            assert "исходное состояние автоматически возвращено" in str(exc), exc
        else:
            raise AssertionError("failure not raised")
    finally:
        br.shutil.move = real_move

    with closing(sqlite3.connect(paths.database_path)) as conn, conn:
        assert conn.execute("SELECT title FROM games WHERE sm_points=1").fetchone()[0] == "LIVE"
    assert (paths.data_dir / "music/a.txt").read_text() == "LIVE"
    assert list(paths.backups_dir.glob("full_restore_safety_*.iolbackup"))

print("1.0.8 FULL RESTORE ROLLBACK REGRESSION SMOKE: OK")
