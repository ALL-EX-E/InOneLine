"""Auction finish observes a credited bid whose transaction is already in flight."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, Game


class AuctionFinishConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        paths = AppPaths.from_root(self.temp.name)
        paths.ensure_runtime_dirs()
        self.db = Database(paths.database_path)
        self.db.add_game(Game(None, "Leader", None, 100, 0, "not_played", ""))
        self.db.add_game(Game(None, "Challenger", None, 90, 0, "not_played", ""))
        self.sid = self.db.create_auction_session("max_amount", 300)
        self.challenger = next(
            row["game_id"] for row in self.db.list_auction_entries(self.sid)
            if row["title"] == "Challenger"
        )

    def tearDown(self):
        self.temp.cleanup()

    def during_bid(
        self, points, action=None, before_action=None, *,
        release_on_update=False, writer_action=None,
    ):
        staged = threading.Event()
        release = threading.Event()
        committed = threading.Event()
        failures = []
        original_connect = self.db.connect
        original_leaders = self.db._max_leaders_conn
        original_session = self.db._get_auction_session_conn
        main_thread = threading.get_ident()

        class UpdateBoundary:
            def __init__(self, conn):
                self.conn = conn

            def execute(self, sql, *args):
                if sql.lstrip().upper().startswith("UPDATE "):
                    release.set()
                    if not committed.wait(5):
                        raise AssertionError("concurrent bid did not commit")
                return self.conn.execute(sql, *args)

            def __getattr__(self, name):
                return getattr(self.conn, name)

        @contextmanager
        def controlled_connect():
            writer = threading.get_ident() != main_thread
            with original_connect() as conn:
                if not writer:
                    # Wake the existing writer as soon as finish requests its
                    # write lock. The fixed reader must wait for that commit.
                    conn.set_trace_callback(
                        lambda sql: release.set()
                        if sql.strip().upper() == "BEGIN IMMEDIATE" else None
                    )
                yield UpdateBoundary(conn) if not writer and release_on_update else conn
                if writer:
                    staged.set()
                    if not release.wait(5):
                        raise AssertionError("finish did not reach its read/write boundary")
            if writer:
                committed.set()

        def controlled_leaders(conn, auction_id):
            result = original_leaders(conn, auction_id)
            if threading.get_ident() == main_thread and not release_on_update:
                # On the old code, let the bid commit immediately after the
                # stale leader read and before finish's first UPDATE.
                release.set()
                if not committed.wait(5):
                    raise AssertionError("concurrent bid did not commit")
            return result

        def controlled_session(conn, auction_id):
            result = original_session(conn, auction_id)
            if threading.get_ident() == main_thread and not release_on_update:
                release.set()
                if not committed.wait(5):
                    raise AssertionError("concurrent bid did not commit")
            return result

        def credit_bid():
            try:
                if writer_action:
                    writer_action()
                else:
                    self.db.add_auction_bid(self.sid, self.challenger, points)
            except BaseException as exc:
                failures.append(exc)
                staged.set()

        with (
            patch.object(self.db, "connect", controlled_connect),
            patch.object(self.db, "_max_leaders_conn", controlled_leaders),
            patch.object(self.db, "_get_auction_session_conn", controlled_session),
        ):
            worker = threading.Thread(target=credit_bid)
            worker.start()
            try:
                self.assertTrue(staged.wait(5), "bid did not reach commit")
                self.assertFalse(failures)
                if before_action:
                    before_action()
                result = action() if action else self.db.finish_auction(self.sid)
            finally:
                release.set()
                worker.join(5)
            self.assertFalse(worker.is_alive())
            self.assertFalse(failures)
        return result

    def test_in_flight_bid_selects_actual_new_leader(self):
        result = self.during_bid(20)
        self.assertEqual(result["status"], "winner_selected")
        self.assertEqual(result["winner_game_id"], self.challenger)
        self.assertEqual(self.db.list_auction_entries(self.sid)[0]["total_sm_points"], 110)

    def test_in_flight_bid_creates_tie_instead_of_stale_winner(self):
        result = self.during_bid(10)
        self.assertEqual(result["status"], "tie_break_required")
        self.assertIsNone(result["winner_game_id"])
        self.assertEqual(
            {row["result"] for row in self.db.list_auction_entries(self.sid)}, {"tie"}
        )

    def enable_leader_extension(self):
        self.db.set_settings_bulk({
            "auction_auto_extend_leader_enabled": "1",
            "auction_auto_extend_leader_ms": "7000",
            "auction_auto_extend_threshold_enabled": "0",
        })

    def test_pause_preserves_in_flight_bid_extension(self):
        self.enable_leader_extension()
        self.during_bid(20, lambda: self.db.pause_auction(self.sid))
        session = self.db.get_auction_session(self.sid)
        self.assertEqual(session["status"], "paused")
        self.assertEqual(session["remaining_ms"], 307000)

    def test_time_adjustment_preserves_in_flight_bid_extension(self):
        self.enable_leader_extension()
        remaining = self.during_bid(
            20, lambda: self.db.adjust_auction_time_ms(self.sid, 1000)
        )
        self.assertEqual(remaining, 308000)

    def test_automatic_expiry_waits_for_in_flight_extension(self):
        class Clock(datetime):
            instant = datetime.now(timezone.utc)

            @classmethod
            def now(cls, tz=None):
                return cls.instant if tz is not None else cls.instant.replace(tzinfo=None)

        self.enable_leader_extension()
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET timer_phase_starts_at=NULL, deadline_at=? WHERE id=?",
                ((Clock.instant + timedelta(milliseconds=500)).isoformat(), self.sid),
            )

        def expire_old_deadline():
            Clock.instant += timedelta(milliseconds=1000)

        with patch("streaming_manager.db.auction_session.datetime", Clock):
            result = self.during_bid(
                20, lambda: self.db.finish_auction(self.sid, automatic=True),
                before_action=expire_old_deadline,
            )
        self.assertEqual(result["status"], "running")
        self.assertIsNone(result["winner_game_id"])
        self.assertEqual(self.db.list_auction_entries(self.sid)[0]["total_sm_points"], 110)

    def test_automatic_finish_keeps_pause_and_explicit_finish_still_works(self):
        self.db.pause_auction(self.sid)
        self.assertEqual(self.db.finish_auction(self.sid, automatic=True)["status"], "paused")
        self.assertEqual(self.db.finish_auction(self.sid)["status"], "winner_selected")
        self.assertEqual(self.db.finish_auction(self.sid)["status"], "winner_selected")

    def test_automatic_finish_does_not_release_audio_after_stale_expiry(self):
        from streaming_manager.views.auction_parts.actions import AuctionActionMixin

        tab = MagicMock()
        tab._current_session.return_value = {"id": self.sid, "status": "running"}
        tab.db = self.db
        AuctionActionMixin.finish_auction(tab, automatic=True)
        tab._finish_auction_soundtrack_phase.assert_not_called()
        tab.refresh.assert_called_once_with()
        self.assertEqual(self.db.get_auction_session(self.sid)["status"], "running")

    def test_manual_lot_merge_keeps_in_flight_credited_points(self):
        self.during_bid(
            20,
            lambda: self.db.add_or_increment_auction_lot(self.sid, "Challenger", 5),
            release_on_update=True,
        )
        row = next(
            row for row in self.db.list_auction_entries(self.sid)
            if row["game_id"] == self.challenger
        )
        self.assertEqual(row["total_sm_points"], 115)
        self.assertEqual(self.db.get_game(self.challenger).sm_points, 115)

    def test_manual_bid_cannot_mutate_in_flight_finished_result(self):
        with self.assertRaises(RuntimeError):
            self.during_bid(
                0, lambda: self.db.add_auction_bid(self.sid, self.challenger, 20),
                writer_action=lambda: self.db.finish_auction(self.sid),
                release_on_update=True,
            )
        self.assertEqual(self.db.get_game(self.challenger).sm_points, 90)
        self.assertEqual(self.db.get_auction_session(self.sid)["status"], "winner_selected")

    def test_manual_decrease_cannot_mutate_in_flight_finished_result(self):
        self.db.add_auction_bid(self.sid, self.challenger, 5)
        with self.assertRaises(RuntimeError):
            self.during_bid(
                0, lambda: self.db.decrease_auction_bid(self.sid, self.challenger, 1),
                writer_action=lambda: self.db.finish_auction(self.sid),
                release_on_update=True,
            )
        self.assertEqual(self.db.get_game(self.challenger).sm_points, 95)
        self.assertEqual(self.db.get_auction_session(self.sid)["status"], "winner_selected")

    def test_pending_apply_recalculates_result_when_finish_commits_first(self):
        self.db.set_conversion_rate("PLN", "1")
        now = datetime.now(timezone.utc).isoformat()
        with self.db.connect() as conn:
            event_id = int(conn.execute(
                "INSERT INTO external_events("
                "source,external_event_id,event_type,payload_json,processing_status,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("test", "concurrent-pending", "donation",
                 json.dumps({"normalized": {"lot_title": "Challenger"}}),
                 "awaiting_manual_apply", now),
            ).lastrowid)
            pending_id = int(conn.execute(
                "INSERT INTO pending_conversions("
                "external_event_row_id,game_id,auction_id,source_amount_text,"
                "source_unit,source_unit_label,unit_kind,status,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,?)",
                (event_id, self.challenger, self.sid, "20", "PLN", "PLN",
                 "currency", "awaiting_manual_apply", now),
            ).lastrowid)

        result = self.during_bid(
            0, lambda: self.db.apply_pending_conversion_event(pending_id),
            writer_action=lambda: self.db.finish_auction(self.sid),
            release_on_update=True,
        )
        session = self.db.get_auction_session(self.sid)
        self.assertEqual(result["auction_id"], self.sid)
        self.assertEqual(session["status"], "winner_selected")
        self.assertEqual(session["winner_game_id"], self.challenger)
        self.assertEqual(session["remaining_ms"], 0)
        self.assertIsNone(session["deadline_at"])
        self.assertEqual(self.db.get_game(self.challenger).sm_points, 110)
        self.assertEqual(self.db.get_pending_conversion_event(pending_id)["status"], "applied")
        with self.db.connect() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM contributions").fetchone()[0], 1)

    def correction_cannot_reopen_confirmed_result(self, correction, *, initial_bid=0):
        if initial_bid:
            self.db.add_auction_bid(self.sid, self.challenger, initial_bid)
        self.db.finish_auction(self.sid)
        with self.assertRaises(RuntimeError):
            self.during_bid(
                0, correction,
                writer_action=lambda: self.db.confirm_auction_winner(self.sid),
                release_on_update=True,
            )
        self.assertEqual(self.db.get_auction_session(self.sid)["status"], "confirmed")
        self.assertEqual(self.db.get_game(self.challenger).sm_points, 90 + initial_bid)

    def test_late_lot_cannot_reopen_in_flight_confirmed_result(self):
        self.correction_cannot_reopen_confirmed_result(
            lambda: self.db.add_post_expiry_manual_lot(self.sid, "Challenger", 20)
        )

    def test_late_bid_cannot_reopen_in_flight_confirmed_result(self):
        self.correction_cannot_reopen_confirmed_result(
            lambda: self.db.add_post_expiry_manual_bid(self.sid, self.challenger, 20)
        )

    def test_late_decrease_cannot_reopen_in_flight_confirmed_result(self):
        self.correction_cannot_reopen_confirmed_result(
            lambda: self.db.decrease_post_expiry_manual_bid(self.sid, self.challenger, 1),
            initial_bid=5,
        )

    def test_confirmation_uses_winner_from_in_flight_late_correction(self):
        previous = self.db.finish_auction(self.sid)["winner_game_id"]
        winner = self.during_bid(
            0, lambda: self.db.confirm_auction_winner(self.sid),
            writer_action=lambda: self.db.add_post_expiry_manual_bid(
                self.sid, self.challenger, 20
            ),
            release_on_update=True,
        )
        self.assertEqual(winner, self.challenger)
        session = self.db.get_auction_session(self.sid)
        self.assertEqual(session["status"], "confirmed")
        self.assertEqual(session["winner_game_id"], self.challenger)
        self.assertEqual(self.db.get_game(self.challenger).status, "playing")
        self.assertEqual(self.db.get_game(previous).status, "not_played")

    def test_late_exclusion_cannot_change_in_flight_confirmed_history(self):
        self.correction_cannot_reopen_confirmed_result(
            lambda: self.db.exclude_post_expiry_permanent_auction_lot(self.sid, self.challenger)
        )
        self.assertEqual(len(self.db.list_auction_entries(self.sid)), 2)

    def test_temporary_rename_cannot_change_in_flight_confirmed_history(self):
        temporary = self.db.add_or_increment_auction_lot(self.sid, "Temporary", 5)["game_id"]
        self.correction_cannot_reopen_confirmed_result(
            lambda: self.db.rename_post_expiry_temporary_lot(self.sid, temporary, "Renamed")
        )
        self.assertEqual(self.db.get_game(temporary).title, "Temporary")

    def test_temporary_delete_cannot_change_in_flight_confirmed_history(self):
        temporary = self.db.add_or_increment_auction_lot(self.sid, "Temporary", 5)["game_id"]
        self.correction_cannot_reopen_confirmed_result(
            lambda: self.db.delete_temporary_auction_lot(self.sid, temporary)
        )
        self.assertIsNotNone(self.db.get_game(temporary))


if __name__ == "__main__":
    unittest.main()
