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
        assert row.title == title and row.sm_points == 12
        with db.connect() as conn:
            assert conn.execute("SELECT auction_only FROM games WHERE id=?", (new_id,)).fetchone()[0] == 0
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

    def running_existing_lot(db, service):
        auction_id, (game_id, _) = new_auction(db)
        current = datetime.now(timezone.utc).isoformat()
        result = service.process_donation(raw(98000701, "DA EXISTING A", created_at=current))
        assert result["status"] == "processed", result
        assert result["auction_id"] == auction_id
        assert result["game_id"] == game_id
        assert result["credited_sm_points"] == 10
        assert db.get_game(game_id).sm_points == 22
        entry = next(row for row in db.list_auction_entries(auction_id)
                     if row["game_id"] == game_id)
        assert entry["bid_sm_points"] == 10
        assert entry["total_sm_points"] == 22
        assert count(db, "contributions") == 1
        with db.connect() as conn:
            record = conn.execute("SELECT game_id,credited_sm_points FROM contributions LIMIT 1").fetchone()
            assert record["game_id"] == game_id and record["credited_sm_points"] == 10

    check("sandbox_da_running_existing_lot_auction_bid", execute(running_existing_lot))

    def running_new_lot(db, service):
        auction_id, originals = new_auction(db)
        result = service.process_donation(raw(98000801, "DA New Auction Lot"))
        assert result["status"] == "processed", result
        assert result["auction_id"] == auction_id
        new_id = result["game_id"]
        assert new_id not in originals
        assert db.get_game(new_id).sm_points == 10
        with db.connect() as conn:
            row = conn.execute("SELECT auction_only FROM games WHERE id=?", (new_id,)).fetchone()
            assert row and row["auction_only"] == 1, "new lot not auction-scoped"
        entries = db.list_auction_entries(auction_id)
        entry = next(e for e in entries if e["game_id"] == new_id)
        # Newly created auction-only lots store their first credit as
        # starting_sm_points; only subsequent credit increments bid_sm_points.
        assert entry["starting_sm_points"] == 10
        assert entry["bid_sm_points"] == 0
        assert entry["total_sm_points"] == 10
        assert len(entries) == 3
        assert count(db, "contributions") == 1

    check("sandbox_da_running_new_lot_auction_scoped", execute(running_new_lot))

    def blank_text_running_unique_ordinals(db, service):
        auction_id, _ = new_auction(db)
        first = service.process_donation(raw(98000901, ""))
        assert first["status"] == "processed", first
        g1 = db.get_game(first["game_id"])
        assert g1.title == "Без текста 1", g1.title
        duplicate = service.process_donation(raw(98000901, ""))
        assert duplicate["status"] == "duplicate_cursor"
        second = service.process_donation(raw(98000902, ""))
        assert second["status"] == "processed", second
        g2 = db.get_game(second["game_id"])
        assert g2.title == "Без текста 2" and g2.id != g1.id
        assert first["auction_id"] == second["auction_id"] == auction_id
        assert g1.sm_points == g2.sm_points == 10
        assert count(db, "external_events") == count(db, "contributions") == 2
        assert len(db.list_auction_entries(auction_id)) == 4

    check("sandbox_da_running_blank_text_ordinal_and_dedup", execute(blank_text_running_unique_ordinals))

    def delayed_outside_timestamp_cannot_enter_new_auction(db, service):
        game_id = create_game(db, "DA Outside Historical", 17)
        original_timestamp = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        auction_id, _ = new_auction(db)
        entries_before = db.list_auction_entries(auction_id)
        result = service.process_donation(raw(
            98001001, "DA Outside Historical", created_at=original_timestamp
        ))
        assert result["status"] == "processed"
        assert result["auction_id"] is None, "past outside event entered new auction"
        assert result["game_id"] == game_id
        assert db.get_game(game_id).sm_points == 27
        assert count(db, "contributions") == 1
        assert db.list_auction_entries(auction_id) == entries_before

    check("sandbox_da_delayed_outside_donation_not_new_auction", execute(delayed_outside_timestamp_cannot_enter_new_auction))

    def cancelled_source_auction_not_retargeted(db, service):
        auction_id, (game_id, _) = new_auction(db)
        time.sleep(0.018)  # source timestamp falls *inside* running phase
        source_timestamp = datetime.now(timezone.utc).isoformat()
        assert db.find_running_auction_at(source_timestamp) == auction_id
        time.sleep(0.018)
        db.cancel_auction(auction_id)
        assert db.get_auction_session(auction_id)["status"] == "cancelled"
        old_points = db.get_game(game_id).sm_points
        result = service.process_donation(raw(
            98001101, "DA EXISTING A", created_at=source_timestamp
        ))
        assert result["status"] == "inapplicable", result
        assert result["reason"] == "source_auction_not_running"
        assert result["credited_sm_points"] is None
        assert db.get_game(game_id).sm_points == old_points
        assert count(db, "external_events") == 1
        assert count(db, "contributions") == 0

    check("sandbox_da_cancelled_historical_source_not_retargeted", execute(cancelled_source_auction_not_retargeted))
