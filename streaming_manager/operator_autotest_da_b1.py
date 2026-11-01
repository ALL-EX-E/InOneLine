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

    def running_pending_credit(db, svc, mgr):
        a = game(db, "B1 Running A", 21)
        game(db, "B1 Running B", 8)
        auction_id = db.create_auction_session("max_amount", duration_seconds=300)
        seen = svc.process_donation(donation(98100004, "B1 Running B", amount="5"))
        assert seen["status"] == "awaiting_rate" and seen["auction_id"] == auction_id
        assert count(db, "contributions") == 0
        current = db.list_auction_entries(auction_id)
        b = next(row for row in current if row["title"] == "B1 Running B")
        assert b["bid_sm_points"] == 0
        db.set_conversion_rate("ZZZ", "2")
        applied = db.apply_pending_conversion_event(seen["pending_id"])
        assert applied["auction_id"] == auction_id and applied["credited_sm_points"] == 10
        after = db.list_auction_entries(auction_id)
        b2 = next(row for row in after if row["title"] == "B1 Running B")
        assert b2["bid_sm_points"] == 10
        assert b2["total_sm_points"] == 18
        assert db.get_game(a).sm_points == 21
        assert count(db, "games") == 2
        assert count(db, "contributions") == 1

    check("sandbox_da_b1_running_pending_credit_original_auction", isolated(running_pending_credit))

    def max_pending_provisional_reselect(db, svc, mgr):
        winner_initial = game(db, "B1 Max First", 17)
        winner_after = game(db, "B1 Max Second", 12)
        auction_id = db.create_auction_session("max_amount", duration_seconds=180)
        received = svc.process_donation(donation(98100005, "B1 Max Second", amount="4"))
        assert received["status"] == "awaiting_rate" and received["auction_id"] == auction_id
        before = db.finish_auction(auction_id)
        assert before["status"] == "winner_selected"
        assert before["winner_game_id"] == winner_initial
        try:
            db.confirm_auction_winner(auction_id)
        except RuntimeError:
            pass
        else:
            raise AssertionError("unprocessed source auction event did not block confirmation")
        assert db.get_auction_session(auction_id)["status"] == "winner_selected"
        db.set_conversion_rate("ZZZ", "2")
        pending = db.get_pending_conversion_event(received["pending_id"])
        assert pending["can_apply"], pending
        applied = db.apply_pending_conversion_event(received["pending_id"])
        assert applied["auction_id"] == auction_id and applied["credited_sm_points"] == 8
        after = db.get_auction_session(auction_id)
        assert after["status"] == "winner_selected"
        assert after["winner_game_id"] == winner_after
        assert after["deadline_at"] is None and int(after["remaining_ms"] or 0) == 0
        assert db.get_game(winner_initial).sm_points == 17
        assert db.get_game(winner_after).sm_points == 20
        entry = next(r for r in db.list_auction_entries(auction_id)
                     if r["game_id"] == winner_after)
        assert entry["total_sm_points"] == 20
        assert count(db, "contributions") == 1
        assert db.confirm_auction_winner(auction_id) == winner_after
        assert db.get_auction_session(auction_id)["status"] == "confirmed"

    check("sandbox_da_b1_post_expiry_max_correct_winner_no_restart", isolated(max_pending_provisional_reselect))

    def direct_wheel_donation_is_outside_auction(db, svc, mgr):
        a = game(db, "B1 Wheel A", 13)
        game(db, "B1 Wheel B", 7)
        auction_id = db.create_auction_session(
            "weighted_wheel", duration_seconds=0, start_in_wheel_mode=True
        )
        assert db.get_auction_session(auction_id)["status"] == "awaiting_wheel"
        entries = db.list_auction_entries(auction_id)
        received = svc.process_donation(donation(
            98100006, "B1 Wheel A", unit="RUB", amount="2"
        ))
        assert received["status"] == "processed" and received["auction_id"] is None
        assert received["game_id"] == a and received["credited_sm_points"] == 4
        assert db.get_game(a).sm_points == 17
        assert db.list_auction_entries(auction_id) == entries, (
            "wheel snapshot incorrectly altered by outside-auction message"
        )
        assert count(db, "games") == 2
        assert count(db, "contributions") == 1

    check("sandbox_da_b1_direct_weighted_wheel_not_running", isolated(direct_wheel_donation_is_outside_auction))

    def rest_catch_up_order_and_idempotence(db, svc, mgr):
        target = game(db, "B1 Catchup", 0)
        db.set_settings_bulk({
            DONATIONALERTS_LAST_SEEN_ID_KEY: "98100099",
            DONATIONALERTS_CURSOR_INITIALIZED_KEY: "1",
        })
        observed_calls = []
        originals = mgr.call_adapter

        def synthetic_api(key, method, page):
            assert key == "donationalerts" and method == "list_donations_page"
            observed_calls.append(page)
            assert page == 1
            return {
                "data": [
                    donation(98100103, "B1 Catchup", unit="RUB", amount="1"),
                    donation(98100102, "B1 Catchup", unit="RUB", amount="2"),
                    donation(98100101, "B1 Catchup", unit="RUB", amount="3"),
                    donation(98100099, "B1 Catchup", unit="RUB", amount="1"),
                ],
                "meta": {"last_page": 2},
            }
        mgr.call_adapter = synthetic_api
        try:
            assert svc.catch_up(max_pages=2) == 3
            assert svc.last_seen_id() == 98100103
            assert db.get_game(target).sm_points == 12
            assert count(db, "contributions") == count(db, "external_events") == 3
            with db.connect() as conn:
                ids = [str(row[0]) for row in conn.execute(
                    "SELECT external_event_id FROM contributions ORDER BY id"
                )]
                assert ids == ["98100101", "98100102", "98100103"], ids
            assert svc.catch_up(max_pages=2) == 0
            assert db.get_game(target).sm_points == 12
            assert count(db, "contributions") == 3
            assert observed_calls == [1, 1]
        finally:
            mgr.call_adapter = originals

    check("sandbox_da_b1_rest_catch_up_sorted_idempotent", isolated(rest_catch_up_order_and_idempotence))
