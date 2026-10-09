"""Exercise P07 presentation through the real elimination lifecycle."""
from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streaming_manager.constants import STATUS_NOT_PLAYED
from streaming_manager.database import Database, Game
from streaming_manager.position_policy import (
    POSITION_COLUMNS_SINGLE,
    POSITION_COLUMNS_START_CURRENT,
)


def assert_elimination_lifecycle(db: Database, check_local_tables=None) -> None:
    """Use real selection/archive/format APIs; an optional GUI check shares phases."""
    for index in range(4):
        db.add_game(Game(
            None, f"P07 Lifecycle {index}", None, 1_000_000 - index,
            0, STATUS_NOT_PLAYED, "",
        ))

    def check(phase: str, expected: str) -> None:
        payload = db.current_auction_lots_payload()
        actual = payload["position_columns"]
        if actual != expected:
            raise AssertionError(
                f"P07 {phase}: overlay position columns {actual!r} != {expected!r}"
            )
        session = db.get_open_auction_session()
        if session is not None:
            entries = db.list_auction_entries(int(session["id"]))
            expected_ids = [int(row["game_id"]) for row in entries]
            actual_ids = [int(row["game_id"]) for row in payload["rows"]]
            if actual_ids != expected_ids:
                raise AssertionError(f"P07 {phase}: active lot order/scope changed")
        if check_local_tables is not None:
            check_local_tables(phase, expected)

    auction_id = db.create_auction_session(
        "weighted_wheel", 0, start_in_wheel_mode=True,
        wheel_format="elimination",
    )
    check("before selection", POSITION_COLUMNS_SINGLE)
    first_selected = db.run_weighted_wheel(auction_id, pick=0)
    check("first selection", POSITION_COLUMNS_START_CURRENT)
    db.archive_elimination_result(auction_id)
    check("between rounds", POSITION_COLUMNS_START_CURRENT)
    if first_selected in {
        int(row["game_id"]) for row in db.list_auction_entries(auction_id)
    }:
        raise AssertionError("P07 archived elimination lot reappeared in active rows")

    db.run_weighted_wheel(auction_id, pick=0)
    check("next selection", POSITION_COLUMNS_START_CURRENT)
    db.archive_elimination_result(auction_id)
    check("next archive", POSITION_COLUMNS_START_CURRENT)
    db.set_auction_wheel_format(auction_id, "standard")
    check("format switch", POSITION_COLUMNS_START_CURRENT)
    db.run_weighted_wheel(auction_id, pick=0)
    check("standard after elimination", POSITION_COLUMNS_START_CURRENT)
    db.cancel_auction(auction_id)
    check("closed session", POSITION_COLUMNS_SINGLE)

    standard_id = db.create_auction_session(
        "weighted_wheel", 0, start_in_wheel_mode=True,
        wheel_format="standard",
    )
    check("fresh standard session", POSITION_COLUMNS_SINGLE)
    db.run_weighted_wheel(standard_id, pick=0)
    check("standard selection", POSITION_COLUMNS_SINGLE)
    db.cancel_auction(standard_id)
    fresh_id = db.create_auction_session(
        "weighted_wheel", 0, start_in_wheel_mode=True,
        wheel_format="elimination",
    )
    check("fresh elimination session", POSITION_COLUMNS_SINGLE)
    db.cancel_auction(fresh_id)


def main() -> int:
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "data" / "streaming.db")
        assert_elimination_lifecycle(db)
    print("P07_ELIMINATION_POSITION_LIFECYCLE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
