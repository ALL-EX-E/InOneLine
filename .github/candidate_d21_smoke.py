from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())

from PySide6.QtWidgets import QApplication, QMessageBox

from streaming_manager.app_paths import AppPaths
from streaming_manager.constants import (
    APP_VERSION,
    AUCTION_WHEEL_FORMAT_ELIMINATION,
    AUCTION_WHEEL_FORMAT_STANDARD,
    SCHEMA_VERSION,
    STATUS_NOT_PLAYED,
    STATUS_PLAYING,
)
from streaming_manager.database import Database, Game
from streaming_manager.views.main_window import MainWindow


assert APP_VERSION == "1.0.6", APP_VERSION
assert SCHEMA_VERSION == 19, SCHEMA_VERSION


def game(title: str, points: int) -> Game:
    return Game(
        id=None,
        title=title,
        release_date=None,
        sm_points=points,
        coop=0,
        status=STATUS_NOT_PLAYED,
        review="",
        archived=0,
    )


def force_spin_complete(db: Database, auction_id: int) -> None:
    past = (datetime.now(timezone.utc) - timedelta(seconds=20)).isoformat(
        timespec="milliseconds"
    )
    with db.connect() as conn:
        conn.execute(
            "UPDATE auction_sessions SET wheel_started_at=? WHERE id=?",
            (past, int(auction_id)),
        )


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def migration_count(db: Database) -> int:
    with db.connect() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0])


def active_game_ids(db: Database, auction_id: int) -> list[int]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT game_id FROM auction_entries "
            "WHERE auction_id=? AND active=1 ORDER BY game_id",
            (int(auction_id),),
        ).fetchall()
    return [int(row["game_id"]) for row in rows]


def rebuild_snapshot_tables_as_schema15(db: Database, auction_id: int) -> None:
    """Make one existing v19 snapshot look like the accepted schema-15 layout."""
    snapshots = db.list_wheel_verification_snapshots(auction_id)
    assert len(snapshots) == 1
    snap = snapshots[0]
    participants = list(snap["participants"])

    with db.connect() as conn:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("DROP TABLE wheel_verification_participants")
        conn.execute("DROP TABLE wheel_verification_snapshots")
        conn.executescript(
            """
            CREATE TABLE wheel_verification_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                auction_id INTEGER NOT NULL UNIQUE
                    REFERENCES auction_sessions(id) ON DELETE CASCADE,
                algorithm_version TEXT NOT NULL,
                mode TEXT NOT NULL,
                rng_method TEXT NOT NULL,
                rng_value INTEGER NOT NULL,
                draw_upper INTEGER NOT NULL CHECK(draw_upper > 0),
                total_weight INTEGER NOT NULL CHECK(total_weight >= 0),
                equal_fallback INTEGER NOT NULL DEFAULT 0
                    CHECK(equal_fallback IN (0,1)),
                winner_game_id INTEGER NOT NULL,
                winner_title TEXT NOT NULL,
                rng_ticket_id TEXT,
                rng_serial_number INTEGER,
                rng_random_json TEXT,
                rng_signature TEXT,
                rng_verified INTEGER CHECK(rng_verified IN (0,1) OR rng_verified IS NULL),
                created_at TEXT NOT NULL
            );
            CREATE TABLE wheel_verification_participants (
                snapshot_id INTEGER NOT NULL
                    REFERENCES wheel_verification_snapshots(id) ON DELETE CASCADE,
                position INTEGER NOT NULL CHECK(position >= 1),
                game_id INTEGER NOT NULL,
                snapshot_title TEXT NOT NULL,
                source_weight INTEGER NOT NULL CHECK(source_weight >= 0),
                effective_weight INTEGER NOT NULL CHECK(effective_weight >= 0),
                interval_start INTEGER NOT NULL CHECK(interval_start >= 0),
                interval_end INTEGER NOT NULL CHECK(interval_end >= interval_start),
                PRIMARY KEY(snapshot_id, position),
                UNIQUE(snapshot_id, game_id)
            );
            CREATE INDEX idx_wheel_verification_auction
                ON wheel_verification_snapshots(auction_id);
            CREATE INDEX idx_wheel_verification_participants_game
                ON wheel_verification_participants(snapshot_id, game_id);
            """
        )
        cursor = conn.execute(
            """
            INSERT INTO wheel_verification_snapshots(
                id, run_id, auction_id, algorithm_version, mode, rng_method,
                rng_value, draw_upper, total_weight, equal_fallback,
                winner_game_id, winner_title, rng_ticket_id, rng_serial_number,
                rng_random_json, rng_signature, rng_verified, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                int(snap["id"]),
                str(snap["run_id"]),
                int(snap["auction_id"]),
                str(snap["algorithm_version"]),
                str(snap["mode"]),
                str(snap["rng_method"]),
                int(snap["rng_value"]),
                int(snap["draw_upper"]),
                int(snap["total_weight"]),
                int(snap["equal_fallback"]),
                int(snap["winner_game_id"]),
                str(snap["winner_title"]),
                snap.get("rng_ticket_id"),
                snap.get("rng_serial_number"),
                snap.get("rng_random_json"),
                snap.get("rng_signature"),
                snap.get("rng_verified"),
                str(snap["created_at"]),
            ),
        )
        snapshot_id = int(cursor.lastrowid)
        for row in participants:
            conn.execute(
                """
                INSERT INTO wheel_verification_participants(
                    snapshot_id, position, game_id, snapshot_title,
                    source_weight, effective_weight, interval_start, interval_end
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    snapshot_id,
                    int(row["position"]),
                    int(row["game_id"]),
                    str(row["snapshot_title"]),
                    int(row["source_weight"]),
                    int(row["effective_weight"]),
                    int(row["interval_start"]),
                    int(row["interval_end"]),
                ),
            )
        conn.execute(
            "DELETE FROM schema_migrations "
            "WHERE name='weighted_wheel_multi_spin_elimination'"
        )
        conn.execute(
            "UPDATE schema_meta SET value='18' WHERE key='schema_version'"
        )
        conn.execute("PRAGMA foreign_keys=ON")


def db_regression(root: Path) -> None:
    db = Database(root / "d21.sqlite")
    assert migration_count(db) == 15

    ids = {}
    for title, points in (("A", 10), ("B", 20), ("C", 30), ("D", 40)):
        ids[title] = db.add_game(game(title, points))

    auction_id = db.create_auction_session(
        "weighted_wheel",
        0,
        rng_method="local",
        wheel_duration_ms=3000,
        duration_ms=0,
        start_in_wheel_mode=True,
        wheel_format=AUCTION_WHEEL_FORMAT_ELIMINATION,
    )
    session = db.get_auction_session(auction_id)
    assert session["status"] == "awaiting_wheel"
    assert session["wheel_format"] == AUCTION_WHEEL_FORMAT_ELIMINATION

    # Normal archive remains guarded while the game is part of an open auction.
    try:
        db.archive_game(ids["A"], True)
    except RuntimeError:
        pass
    else:
        raise AssertionError("normal archive guard did not protect open auction")

    # Round 1: A is selected deterministically and is not archived until explicit action.
    selected = db.run_weighted_wheel(auction_id, pick=0)
    assert selected == ids["A"]
    assert db.get_game(ids["A"]).archived == 0
    payload = db.prepare_wheel_animation(auction_id)
    assert payload["wheel_format"] == AUCTION_WHEEL_FORMAT_ELIMINATION
    assert payload["winner"] is None  # reveal waits for authoritative timer completion
    force_spin_complete(db, auction_id)
    payload = db.wheel_payload(auction_id)
    assert payload["winner"]["game_id"] == ids["A"]
    assert payload["winner"]["chance"]["available"] is True

    result = db.archive_elimination_result(auction_id)
    assert result["game_id"] == ids["A"]
    assert result["remaining_lots"] == 3
    assert db.get_game(ids["A"]).archived == 1
    assert active_game_ids(db, auction_id) == [ids["B"], ids["C"], ids["D"]]
    session = db.get_auction_session(auction_id)
    assert session["status"] == "awaiting_wheel"
    assert session["winner_game_id"] is None
    assert session["wheel_spin_id"] is None

    timer = db.current_timer_payload({"mode": "weighted_wheel"})
    assert timer["timer_kind"] == "wheel"
    assert timer["remaining_ms"] == 3000
    assert timer["status"] == "awaiting_wheel"

    next_payload = db.wheel_payload(auction_id)
    assert [s["game_id"] for s in next_payload["sectors"]] == [
        ids["B"], ids["C"], ids["D"]
    ]
    probs = {s["game_id"]: s["probability"] for s in next_payload["sectors"]}
    assert abs(probs[ids["B"]] - (20 / 90)) < 1e-9
    assert abs(probs[ids["C"]] - (30 / 90)) < 1e-9
    assert abs(probs[ids["D"]] - (40 / 90)) < 1e-9

    # Round 2.
    assert db.run_weighted_wheel(auction_id, pick=0) == ids["B"]
    db.prepare_wheel_animation(auction_id)
    force_spin_complete(db, auction_id)
    db.archive_elimination_result(auction_id)
    snapshots = db.list_wheel_verification_snapshots(auction_id)
    assert [int(s["spin_index"]) for s in snapshots] == [1, 2]
    assert [s["result_kind"] for s in snapshots] == ["eliminated", "eliminated"]

    # User may leave elimination after any completed round and use ordinary weighted wheel.
    db.set_auction_wheel_format(auction_id, AUCTION_WHEEL_FORMAT_STANDARD)
    session = db.get_auction_session(auction_id)
    assert session["wheel_format"] == AUCTION_WHEEL_FORMAT_STANDARD
    assert db.run_weighted_wheel(auction_id, pick=0) == ids["C"]
    db.prepare_wheel_animation(auction_id)
    force_spin_complete(db, auction_id)
    db.confirm_auction_winner(auction_id)
    assert db.get_game(ids["C"]).status == STATUS_PLAYING
    assert db.get_auction_session(auction_id)["status"] == "confirmed"
    snapshots = db.list_wheel_verification_snapshots(auction_id)
    assert [int(s["spin_index"]) for s in snapshots] == [1, 2, 3]
    assert snapshots[-1]["result_kind"] == "winner"

    # A separate D21 session can continue through the last remaining lot to zero.
    ids["E"] = db.add_game(game("E", 50))
    zero_id = db.create_auction_session(
        "weighted_wheel",
        0,
        rng_method="local",
        wheel_duration_ms=3000,
        duration_ms=0,
        start_in_wheel_mode=True,
        wheel_format=AUCTION_WHEEL_FORMAT_ELIMINATION,
    )
    assert active_game_ids(db, zero_id) == [ids["D"], ids["E"]]
    assert db.run_weighted_wheel(zero_id, pick=0) == ids["D"]
    db.prepare_wheel_animation(zero_id)
    force_spin_complete(db, zero_id)
    db.archive_elimination_result(zero_id)
    assert db.get_auction_session(zero_id)["status"] == "awaiting_wheel"
    assert active_game_ids(db, zero_id) == [ids["E"]]

    # One participant is still a real spin; only after explicit archive does it end.
    assert db.run_weighted_wheel(zero_id, pick=0) == ids["E"]
    db.prepare_wheel_animation(zero_id)
    force_spin_complete(db, zero_id)
    assert db.get_game(ids["E"]).archived == 0
    final_result = db.archive_elimination_result(zero_id)
    assert final_result["remaining_lots"] == 0
    assert final_result["status"] == "finished_no_winner"
    assert db.get_game(ids["E"]).archived == 1
    assert db.get_open_auction_session() is None

    # Stop Auction after a revealed result does not implicitly archive that result.
    for title, points in (("F", 60), ("G", 70), ("H", 80)):
        ids[title] = db.add_game(game(title, points))
    stop_id = db.create_auction_session(
        "weighted_wheel",
        0,
        rng_method="local",
        wheel_duration_ms=3000,
        duration_ms=0,
        start_in_wheel_mode=True,
        wheel_format=AUCTION_WHEEL_FORMAT_ELIMINATION,
    )
    assert db.run_weighted_wheel(stop_id, pick=0) == ids["F"]
    db.prepare_wheel_animation(stop_id)
    force_spin_complete(db, stop_id)
    db.archive_elimination_result(stop_id)
    assert db.get_game(ids["F"]).archived == 1

    assert db.run_weighted_wheel(stop_id, pick=0) == ids["G"]
    db.prepare_wheel_animation(stop_id)
    force_spin_complete(db, stop_id)
    assert db.get_game(ids["G"]).archived == 0
    db.cancel_auction(stop_id)
    assert db.get_auction_session(stop_id)["status"] == "cancelled"
    assert db.get_game(ids["F"]).archived == 1
    assert db.get_game(ids["G"]).archived == 0
    assert db.get_game(ids["H"]).archived == 0


def migration_regression(root: Path) -> None:
    path = root / "migration.sqlite"
    db = Database(path)
    a = db.add_game(game("Legacy A", 10))
    db.add_game(game("Legacy B", 20))
    auction_id = db.create_auction_session(
        "weighted_wheel",
        0,
        rng_method="local",
        wheel_duration_ms=3000,
        duration_ms=0,
        start_in_wheel_mode=True,
        wheel_format=AUCTION_WHEEL_FORMAT_STANDARD,
    )
    assert db.run_weighted_wheel(auction_id, pick=0) == a
    rebuild_snapshot_tables_as_schema15(db, auction_id)

    reopened = Database(path)
    assert migration_count(reopened) == 15
    with reopened.connect() as conn:
        schema_version = conn.execute(
            "SELECT value FROM schema_meta WHERE key='schema_version'"
        ).fetchone()[0]
        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert str(schema_version) == "19"
    assert fk_errors == [], fk_errors
    snapshots = reopened.list_wheel_verification_snapshots(auction_id)
    assert len(snapshots) == 1
    assert int(snapshots[0]["spin_index"]) == 1
    assert snapshots[0]["result_kind"] == "winner"
    assert len(snapshots[0]["participants"]) == 2


def ui_api_regression(root: Path, app: QApplication) -> None:
    paths = AppPaths.from_root(root / "ui")
    paths.ensure_runtime_dirs()
    db = Database(paths.database_path)
    db.set_setting("api_port", "18772")
    ids = [
        db.add_game(game("UI A", 10)),
        db.add_game(game("UI B", 20)),
        db.add_game(game("UI C", 30)),
    ]
    auction_id = db.create_auction_session(
        "weighted_wheel",
        0,
        rng_method="local",
        wheel_duration_ms=3000,
        duration_ms=0,
        start_in_wheel_mode=True,
        wheel_format=AUCTION_WHEEL_FORMAT_ELIMINATION,
    )

    window = MainWindow(db, paths)
    try:
        auction = window.auction_tab
        auction.refresh_force()
        app.processEvents()

        assert auction.wheel_format_combo.currentData() == AUCTION_WHEEL_FORMAT_ELIMINATION
        assert auction.start_btn.text() == "Крутить"
        assert window.audio_coordinator.owner == "idle"

        # Use the real UI action path without modal confirmation.
        auction.run_wheel(confirm=False)
        for _ in range(5):
            app.processEvents()
            time.sleep(0.03)
        session = db.get_auction_session(auction_id)
        assert session["status"] == "winner_selected"
        assert window.audio_coordinator.owner == "auction"

        force_spin_complete(db, auction_id)
        auction._handle_local_wheel_spin_finished()
        auction.refresh_force()
        app.processEvents()

        assert auction.confirm_btn.text() == "В архив"
        assert auction.confirm_btn.isEnabled()
        assert "Выбывает:" in auction.leader_label.text()
        assert window.audio_coordinator.owner == "idle"

        wheel_api = get_json(window.api.base_url + "/api/wheel")
        assert wheel_api["wheel_format"] == "elimination"
        assert wheel_api["winner"]["game_id"] == ids[0]

        timer_api = get_json(window.api.base_url + "/api/timer")
        assert timer_api["timer_kind"] == "wheel"
        assert timer_api["remaining_ms"] == 0
        assert "audio" in timer_api

        html = urllib.request.urlopen(
            window.api.base_url + "/wheel-overlay", timeout=5
        ).read().decode("utf-8")
        assert 's?.wheel_format==="elimination"?"Выбывает":"Победитель"' in html
        assert "Шанс в этом вращении:" in html

        # Explicit archive removes exactly one lot from both wheel and lots overlay.
        auction.archive_elimination_result()
        app.processEvents()
        session = db.get_auction_session(auction_id)
        assert session["status"] == "awaiting_wheel"
        assert db.get_game(ids[0]).archived == 1
        assert auction.start_btn.text() == "Крутить"
        assert not auction.confirm_btn.isVisible()
        assert auction.timer_edit.text() == "00:00:03.000"
        assert window.audio_coordinator.owner == "idle"

        wheel_api = get_json(window.api.base_url + "/api/wheel")
        assert [s["game_id"] for s in wheel_api["sectors"]] == ids[1:]
        lots_api = get_json(window.api.base_url + "/api/auction-lots")
        assert [row["game_id"] for row in lots_api["rows"]] == ids[1:]
        timer_api = get_json(window.api.base_url + "/api/timer")
        assert timer_api["remaining_ms"] == 3000
        assert timer_api["status"] == "awaiting_wheel"

        # Between rounds the format can change and immediately uses the same live lots.
        standard_index = auction.wheel_format_combo.findData(
            AUCTION_WHEEL_FORMAT_STANDARD
        )
        auction.wheel_format_combo.setCurrentIndex(standard_index)
        app.processEvents()
        assert db.get_auction_session(auction_id)["wheel_format"] == "standard"

        elimination_index = auction.wheel_format_combo.findData(
            AUCTION_WHEEL_FORMAT_ELIMINATION
        )
        auction.wheel_format_combo.setCurrentIndex(elimination_index)
        app.processEvents()
        assert db.get_auction_session(auction_id)["wheel_format"] == "elimination"

        # Hiding the Auction tab defers visual work without closing the session.
        auction.set_main_tab_visible(False)
        auction.refresh()
        assert db.get_open_auction_session()["id"] == auction_id
        auction.set_main_tab_visible(True, refresh_pending=True)
        app.processEvents()

        # Stop Auction after completed D21 round preserves archive state.
        db.cancel_auction(auction_id)
        auction.refresh_force()
        app.processEvents()
        assert db.get_game(ids[0]).archived == 1
        assert db.get_game(ids[1]).archived == 0
    finally:
        window.api.stop()
        window.close()
        app.processEvents()


def main() -> None:
    app = QApplication.instance() or QApplication([])
    old_info = QMessageBox.information
    old_warn = QMessageBox.warning
    old_critical = QMessageBox.critical
    old_question = QMessageBox.question
    QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.Ok)
    QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)
    QMessageBox.critical = staticmethod(lambda *a, **k: QMessageBox.Ok)
    QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
    try:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_regression(root)
            migration_regression(root)
            ui_api_regression(root, app)
    finally:
        QMessageBox.information = old_info
        QMessageBox.warning = old_warn
        QMessageBox.critical = old_critical
        QMessageBox.question = old_question

    print("D21 MULTI-SPIN ELIMINATION SMOKE: PASS")


if __name__ == "__main__":
    main()
