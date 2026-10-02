from __future__ import annotations

import tempfile
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streaming_manager.database import Database
from streaming_manager.random_sources import RandomOrgClient
from streaming_manager.views.auction_parts.rng import AuctionRngMixin


def expect_value_error(fn, message: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


def main() -> None:
    # Rule-template create/rename both pass through the normalized duplicate-name
    # guard. This catches missing normalize_text_key runtime dependencies.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "streaming.db")
        first = db.create_rule_template("Первый", make_active=True)
        second = db.create_rule_template("Второй", make_active=False)

        db.rename_rule_template(second, "Переименованный")
        row = db.get_rule_template(second)
        assert row is not None
        assert row["name"] == "Переименованный"

        expect_value_error(
            lambda: db.create_rule_template("  первый  ", make_active=False),
            "normalized duplicate create must fail",
        )
        expect_value_error(
            lambda: db.rename_rule_template(second, " ПЕРВЫЙ "),
            "normalized duplicate rename must fail",
        )

        first_row = db.get_rule_template(first)
        assert first_row is not None
        assert first_row["name"] == "Первый"

    # run_wheel() creates RandomOrgClient directly in its non-local RNG path.
    # Assert the method's runtime globals still resolve the class even if a
    # private wrapper helper is removed.
    assert AuctionRngMixin.run_wheel.__globals__.get("RandomOrgClient") is RandomOrgClient

    print("RULE_TEMPLATE_CREATE_RENAME=PASS")
    print("RANDOM_ORG_RUNTIME_DEPENDENCY=PASS")


if __name__ == "__main__":
    main()
