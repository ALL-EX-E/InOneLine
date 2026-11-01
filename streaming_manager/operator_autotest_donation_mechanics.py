"""DonationAlerts B3 credit-routing regression matrix. No provider traffic.

Called only from --autotest-sandbox: each case creates its own temporary
SQLite database and synthetic DonationAlerts service connection.
"""
from __future__ import annotations

import tempfile
import time
from datetime import datetime, timedelta, timezone

from .app_paths import AppPaths
from .database import Database, Game
from .donationalerts import DonationAlertsAdapter
from .donationalerts_runtime import DonationAlertsDonationService
from .integrations import IntegrationManager, IntegrationRegistry


def run_donation_mechanic_checks(check):
    def execute(fn):
        def isolated():
            with tempfile.TemporaryDirectory(prefix="InOneLine_DA_Mechanics_") as folder:
                paths = AppPaths.from_root(folder)
                paths.ensure_runtime_dirs()
                db = Database(paths.database_path)
                db.upsert_integration_connection(
                    "donationalerts", enabled=True, status="connected"
                )
                db.set_conversion_rate("RUB", "2")
                db.set_conversion_rate("EUR", "3")
                registry = IntegrationRegistry()
                registry.register(DonationAlertsAdapter())
                manager = IntegrationManager(db, registry, retry_delays=())
                service = DonationAlertsDonationService(db, manager)
                fn(db, service)
        return isolated

    def create_game(db, title, points=0):
        return db.add_game(Game(None, title, None, points, 0, "not_played", ""))

    def raw(identifier, title, *, amount="5", currency="RUB", created_at=None):
        return {
            "id": identifier, "amount": amount, "currency": currency,
            "username": "Synthetic", "message": title,
            "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        }

    def count(db, table):
        assert table in {"games", "contributions", "external_events", "pending_conversions"}
        with db.connect() as conn:
            return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def new_auction(db):
        ids = [create_game(db, "DA EXISTING A", 12), create_game(db, "DA EXISTING B", 8)]
        auction_id = db.create_auction_session("max_amount", duration_seconds=180)
        assert db.get_auction_session(auction_id)["status"] == "running"
        return auction_id, ids

    def existing_title_and_multiple_new_ids(db, service):
        title = "Donation existing target"
        game_id = create_game(db, title, 15)
        first = service.process_donation(raw(98000101, title, amount="4"))
        second = service.process_donation(raw(98000102, "  DONATION EXISTING TARGET  ", amount="7"))
        assert first["status"] == second["status"] == "processed"
        assert first["game_id"] == second["game_id"] == game_id
        assert first["credited_sm_points"] == 8
        assert second["credited_sm_points"] == 14
        assert db.get_game(game_id).sm_points == 37
        assert count(db, "games") == 1
        assert count(db, "external_events") == count(db, "contributions") == 2
        with db.connect() as conn:
            rows = conn.execute(
                "SELECT game_id,credited_sm_points,external_event_id FROM contributions "
                "ORDER BY id"
            ).fetchall()
            assert [(r["game_id"], r["credited_sm_points"]) for r in rows] == [
                (game_id, 8), (game_id, 14)
            ]
        duplicate = service.process_donation(raw(98000102, title, amount="700"))
        assert duplicate["status"] == "duplicate_cursor"
        assert db.get_game(game_id).sm_points == 37
        assert count(db, "contributions") == 2

    check("sandbox_da_existing_title_increment_no_duplicate", execute(existing_title_and_multiple_new_ids))

    def new_title_and_repeated_credit(db, service):
        title = "DA New Target"
        first = service.process_donation(raw(98000201, title, amount="6"))
        assert first["status"] == "processed"
        new_id = first["game_id"]
        row = db.get_game(new_id)
        assert row.title == title and row.sm_points == 12 and row.auction_only == 0
        second = service.process_donation(raw(98000202, title, amount="2"))
        assert second["status"] == "processed" and second["game_id"] == new_id
        assert db.get_game(new_id).sm_points == 16
        assert count(db, "games") == 1
        assert count(db, "external_events") == count(db, "contributions") == 2

    check("sandbox_da_new_title_create_then_increment", execute(new_title_and_repeated_credit))

    def archived_title_not_reused(db, service):
        title = "DA Archived"
        game_id = create_game(db, title, 40)
        db.archive_game(game_id, True)
        result = service.process_donation(raw(98000301, title))
        assert result["status"] == "inapplicable"
        assert result["reason"] == "target_game_archived"
        assert db.get_game(game_id).sm_points == 40
        assert count(db, "games") == 1
        assert count(db, "contributions") == 0
        assert count(db, "external_events") == 1

    check("sandbox_da_archived_target_rejected", execute(archived_title_not_reused))

    def blank_outside_auction(db, service):
        result = service.process_donation(raw(98000401, ""))
        assert result["status"] == "inapplicable"
        assert result["reason"] == "missing_target"
        assert count(db, "games") == count(db, "contributions") == 0
        assert count(db, "external_events") == 1

    check("sandbox_da_blank_message_outside_auction", execute(blank_outside_auction))

    def zero_amount_no_credit(db, service):
        game_id = create_game(db, "DA Zero", 25)
        result = service.process_donation(raw(98000501, "DA Zero", amount="0"))
        assert result["status"] == "inapplicable"
        assert result["reason"] == "non_positive_credit"
        assert db.get_game(game_id).sm_points == 25
        assert count(db, "contributions") == 0
        assert count(db, "external_events") == 1

    check("sandbox_da_zero_amount_no_credit", execute(zero_amount_no_credit))

    def unknown_rate_deferred(db, service):
        result = service.process_donation(raw(98000601, "DA Waiting", currency="ZZZ"))
        assert result["status"] == "awaiting_rate"
        assert result["pending_id"] is not None
        assert result["credited_sm_points"] is None
        assert count(db, "games") == 0
        assert count(db, "contributions") == 0
        assert count(db, "pending_conversions") == count(db, "external_events") == 1
        with db.connect() as conn:
            row = conn.execute(
                "SELECT status,source_unit FROM pending_conversions LIMIT 1"
            ).fetchone()
            assert row["status"] == "awaiting_rate" and row["source_unit"] == "ZZZ"

    check("sandbox_da_unknown_currency_queued_not_credited", execute(unknown_rate_deferred))
