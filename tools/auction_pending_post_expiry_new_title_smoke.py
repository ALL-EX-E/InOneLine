"""P20-C: title-only pending conversion joins only its original expired auction."""
from __future__ import annotations

import json
import sqlite3
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streaming_manager.app_paths import AppPaths
from streaming_manager.credentials import MemoryCredentialStore
from streaming_manager.database import Database, Game


class ExpiredTitleOnlySourceLotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(
            self.paths.database_path,
            credential_store=MemoryCredentialStore(self.tmp.name),
        )
        self.db.set_conversion_rate("PLN", "1")
        self.alpha = self.db.add_game(Game(None, "Alpha", None, 100, 0, "not_played", ""))
        self.beta = self.db.add_game(Game(None, "Beta", None, 90, 0, "not_played", ""))
        self.earlier = "2026-10-19T09:00:00+00:00"

    def source(self, *, tie=False):
        with self.db.connect() as conn:
            sid = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,remaining_ms,remaining_seconds,deadline_at"
                ") VALUES(?,?,?,?,?,?,?,?)",
                ("P20-C", "max_amount", "local", self.earlier, "running", 0, 0, self.earlier),
            ).lastrowid)
            scores = ((self.alpha, 100), (self.beta, 100 if tie else 90))
            for game_id, score in scores:
                conn.execute(
                    "INSERT INTO auction_entries("
                    "auction_id,game_id,weight,active,starting_sm_points,bid_sm_points,"
                    "snapshot_title,snapshot_status) "
                    "SELECT ?,?,?,1,?,0,title,status FROM games WHERE id=?",
                    (sid, game_id, score, score, game_id),
                )
        return sid

    def pending(self, sid, title, amount=15, *, event_id="new"):
        # The provider's accepted title-only event is stored with game_id=NULL.
        # queue_external_conversion_event intentionally accepts known IDs only;
        # use the real persisted schema the integration processor produces.
        with self.db.connect() as conn:
            event_row = int(conn.execute(
                "INSERT INTO external_events("
                "source,external_event_id,event_type,payload_json,"
                "processing_status,created_at) VALUES(?,?,?,?,?,?)",
                ("p20c-regression", event_id, "donation",
                 json.dumps({"normalized": {"lot_title": title}}),
                 "awaiting_manual_apply", self.earlier),
            ).lastrowid)
            return int(conn.execute(
                "INSERT INTO pending_conversions("
                "external_event_row_id,game_id,auction_id,source_amount_text,"
                "source_unit,source_unit_label,unit_kind,status,created_at)"
                " VALUES(?,?,?,?,?,?,?,?,?)",
                (event_row, None, sid, str(amount), "PLN", "PLN", "currency",
                 "awaiting_manual_apply", self.earlier),
            ).lastrowid)

    def snapshot(self, sid):
        with self.db.connect() as conn:
            session = dict(conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?", (sid,)
            ).fetchone())
            entries = [dict(r) for r in conn.execute(
                "SELECT * FROM auction_entries WHERE auction_id=? ORDER BY id", (sid,)
            ).fetchall()]
            return session, entries

    def test_missing_title_creates_temporary_source_lot_and_changes_winner(self):
        sid = self.source()
        pending = self.pending(sid, "Late arrival", amount=110)
        self.db.finish_auction(sid)
        before, entries_before = self.snapshot(sid)
        self.assertTrue(self.db.get_pending_conversion_event(pending)["can_apply"])
        applied = self.db.apply_pending_conversion_event(pending)
        after, entries_after = self.snapshot(sid)
        self.assertEqual(applied["auction_id"], sid)
        self.assertEqual(after["status"], "winner_selected")
        self.assertEqual(after["winner_game_id"], applied["game_id"])
        for field in ("finished_at", "remaining_ms", "deadline_at", "wheel_spin_id"):
            self.assertEqual(before[field], after[field])
        self.assertEqual(len(entries_after), len(entries_before) + 1)
        target = self.db.get_game(applied["game_id"])
        self.assertEqual((target.title, target.sm_points), ("Late arrival", 110))
        with self.db.connect() as conn:
            self.assertEqual(conn.execute(
                "SELECT auction_only FROM games WHERE id=?", (applied["game_id"],)
            ).fetchone()[0], 1)
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM contributions"
            ).fetchone()[0], 1)
        with self.assertRaises(RuntimeError):
            self.db.apply_pending_conversion_event(pending)

    def test_existing_permanent_title_not_in_snapshot_is_reused_without_duplication(self):
        game = self.db.add_game(Game(None, "Known outside", None, 35, 0, "not_played", ""))
        sid = self.source()
        pending = self.pending(sid, "Known outside", amount=65)
        self.db.finish_auction(sid)
        count_before = self._game_count()
        applied = self.db.apply_pending_conversion_event(pending)
        self.assertEqual(applied["game_id"], game)
        self.assertEqual(self._game_count(), count_before)
        self.assertEqual(self.db.get_game(game).sm_points, 100)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "tie_break_required")
        with self.db.connect() as conn:
            r = conn.execute(
                "SELECT starting_sm_points,bid_sm_points,weight FROM auction_entries "
                "WHERE auction_id=? AND game_id=?", (sid, game),
            ).fetchone()
            self.assertEqual(tuple(r), (35, 65, 100))

    def test_removed_title_tombstone_stays_deleted_and_pending(self):
        sid = self.source()
        removed_id = self.db.add_game(Game(None, "Deleted name", None, 150, 0, "not_played", ""))
        with self.db.connect() as conn:
            conn.execute("UPDATE games SET auction_only=1 WHERE id=?", (removed_id,))
            conn.execute(
                "INSERT INTO auction_entries("
                "auction_id,game_id,weight,active,starting_sm_points,bid_sm_points,"
                "snapshot_title) VALUES(?,?,?,?,?,?,?)",
                (sid, removed_id, 150, 1, 150, 0, "Deleted name"),
            )
        pending = self.pending(sid, "Deleted name", amount=25)
        self.db.delete_temporary_auction_lot(sid, removed_id)
        self.db.finish_auction(sid)
        before = self.snapshot(sid)
        self.assertFalse(self.db.get_pending_conversion_event(pending)["can_apply"])
        with self.assertRaisesRegex(RuntimeError, "недоступен"):
            self.db.apply_pending_conversion_event(pending)
        self.assertEqual(self.snapshot(sid), before)
        self.assertEqual(self.db.get_pending_conversion_event(pending)["status"], "awaiting_manual_apply")
        self.assertEqual(self._game_count(), 2)

    def test_confirmed_source_never_creates_lot_or_captures_new_session(self):
        old = self.source()
        pid = self.pending(old, "A genuinely new title", amount=200)
        self.db.finish_auction(old)
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET status='confirmed' WHERE id=?", (old,)
            )
        newer = self.source()
        old_before, new_before = self.snapshot(old), self.snapshot(newer)
        self.assertFalse(self.db.get_pending_conversion_event(pid)["can_apply"])
        with self.assertRaises(RuntimeError):
            self.db.apply_pending_conversion_event(pid)
        self.assertEqual(self.snapshot(old), old_before)
        self.assertEqual(self.snapshot(newer), new_before)
        self.assertEqual(self._game_count(), 2)

    def test_new_title_creates_tie_without_restarting_timer_or_double_credit(self):
        sid = self.source(tie=False)
        pid = self.pending(sid, "Late tie", amount=100, event_id="tie")
        self.db.finish_auction(sid)
        self.db.apply_pending_conversion_event(pid)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "tie_break_required")
        self.assertEqual(self.db.get_auction_session(sid)["remaining_ms"], 0)
        self.assertIsNone(self.db.get_auction_session(sid)["deadline_at"])
        self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 0)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.connect() as conn:
                conn.execute(
                    "INSERT INTO external_events("
                    "source,external_event_id,event_type,payload_json,"
                    "processing_status,created_at) VALUES(?,?,?,?,?,?)",
                    ("p20c-regression", "tie", "donation", "{}",
                     "awaiting_manual_apply", self.earlier),
                )
        self.assertEqual(self.db.get_pending_conversion_event(pid)["status"], "applied")
        with self.assertRaises(RuntimeError):
            self.db.apply_pending_conversion_event(pid)
        with self.db.connect() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM contributions").fetchone()[0], 1)

    def _game_count(self):
        with self.db.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM games").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
