"""B1: real DonationAlerts/B3, conversion and auction tests, isolated temp SQLite.

Provider network and user's stored databases are never accessed.
"""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone

from .app_paths import AppPaths
from .database import Database, Game
from .donationalerts import DonationAlertsAdapter
from .donationalerts_runtime import (
    DONATIONALERTS_CURSOR_INITIALIZED_KEY,
    DONATIONALERTS_LAST_SEEN_ID_KEY,
    DonationAlertsDonationService,
)
from .integrations import IntegrationManager, IntegrationRegistry


def run_da_b1_checks(check):
    def isolated(fn):
        def test():
            with tempfile.TemporaryDirectory(prefix="InOneLine_DA_B1_") as root:
                paths = AppPaths.from_root(root)
                paths.ensure_runtime_dirs()
                db = Database(paths.database_path)
                db.upsert_integration_connection(
                    "donationalerts", enabled=True, status="connected"
                )
                db.set_conversion_rate("RUB", "2")
                registry = IntegrationRegistry()
                registry.register(DonationAlertsAdapter())
                manager = IntegrationManager(db, registry, retry_delays=())
                service = DonationAlertsDonationService(db, manager)
                fn(db, service, manager)
        return test

    def game(db, title, points=0):
        return db.add_game(Game(None, title, None, points, 0, "not_played", ""))

    def donation(event_id, title, *, amount="3", unit="ZZZ", when=None):
        return {
            "id": event_id, "message": title, "amount": amount,
            "currency": unit, "username": "Synthetic",
            "created_at": when or datetime.now(timezone.utc).isoformat(),
        }

    def count(db, table):
        assert table in {"games", "contributions", "external_events", "pending_conversions"}
        with db.connect() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def pending_new_apply(db, svc, mgr):
        title = "B1 New Pending"
        result = svc.process_donation(donation(98100001, title, amount="4"))
        assert result["status"] == "awaiting_rate" and result["game_id"] is None
        pending_id = result["pending_id"]
        assert count(db, "games") == count(db, "contributions") == 0
        assert db.get_pending_conversion_event(pending_id)["can_apply"] is False
        db.set_conversion_rate("ZZZ", "3")
        ready = db.get_pending_conversion_event(pending_id)
        assert ready["status"] == "awaiting_manual_apply" and ready["can_apply"]
        assert count(db, "games") == count(db, "contributions") == 0
        applied = db.apply_pending_conversion_event(pending_id)
        assert applied["status"] == "applied" and applied["credited_sm_points"] == 12
        assert applied["auction_id"] is None
        row = db.get_game(applied["game_id"])
        assert row.title == title and row.sm_points == 12
        assert count(db, "games") == count(db, "contributions") == 1
        assert db.get_pending_conversion_event(pending_id)["status"] == "applied"
        with db.connect() as conn:
            event = conn.execute("SELECT processing_status FROM external_events").fetchone()
            assert event["processing_status"] == "processed"
            contrib = conn.execute(
                "SELECT game_id,source_unit,credited_sm_points FROM contributions"
            ).fetchone()
            assert (contrib["game_id"], contrib["source_unit"], contrib["credited_sm_points"]) == (
                row.id, "ZZZ", 12
            )
        try:
            db.apply_pending_conversion_event(pending_id)
        except RuntimeError:
            pass
        else:
            raise AssertionError("applied event may not be applied twice")
        assert db.get_game(row.id).sm_points == 12

    check("sandbox_da_b1_pending_new_rate_manual_apply", isolated(pending_new_apply))

    def pending_existing_apply(db, svc, mgr):
        target = game(db, "B1 Existing Pending", 19)
        received = svc.process_donation(donation(98100002, "b1 existing pending", amount="5"))
        assert received["status"] == "awaiting_rate"
        assert received["game_id"] == target
        assert db.get_game(target).sm_points == 19
        assert count(db, "contributions") == 0
        db.set_conversion_rate("ZZZ", "4")
        result = db.apply_pending_conversion_event(received["pending_id"])
        assert result["game_id"] == target and result["credited_sm_points"] == 20
        assert db.get_game(target).sm_points == 39 and count(db, "games") == 1
        assert count(db, "contributions") == count(db, "external_events") == 1

    check("sandbox_da_b1_pending_existing_target_manual_apply", isolated(pending_existing_apply))

    def pending_reject_is_final(db, svc, mgr):
        item = svc.process_donation(donation(98100003, "B1 Rejected", amount="11"))
        assert item["status"] == "awaiting_rate"
        rejected = db.reject_pending_conversion_event(item["pending_id"])
        assert rejected["status"] == "cancelled"
        db.set_conversion_rate("ZZZ", "3")
        assert db.get_pending_conversion_event(item["pending_id"])["can_apply"] is False
        assert db.get_pending_conversion_event(item["pending_id"])["status"] == "cancelled"
        assert count(db, "games") == count(db, "contributions") == 0
        assert count(db, "external_events") == count(db, "pending_conversions") == 1
        for action in [db.reject_pending_conversion_event, db.apply_pending_conversion_event]:
            try:
                action(item["pending_id"])
            except RuntimeError:
                pass
            else:
                raise AssertionError("terminal cancelled event reprocessed")
        replay = svc.process_donation(donation(98100003, "B1 Rejected"))
        assert replay["status"] == "duplicate_cursor"
        assert count(db, "contributions") == 0

    check("sandbox_da_b1_reject_pending_final_no_credit", isolated(pending_reject_is_final))
