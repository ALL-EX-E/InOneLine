"""P20-B fix1: late source credit must leave deleted-lot history inactive."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streaming_manager.app_paths import AppPaths
from streaming_manager.credentials import MemoryCredentialStore
from streaming_manager.database import Database, Game


class RemovedLotPendingCorrectionTests(unittest.TestCase):
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
        self.earlier = "2026-10-19T09:00:00+00:00"

    def _entry(self, entry_id):
        with self.db.connect() as conn:
            return dict(conn.execute(
                "SELECT * FROM auction_entries WHERE id=?", (entry_id,),
            ).fetchone())

    def _seed_running_source(self, removed_points):
        self.games = {}
        for title, points in (("Alpha", 100), ("Beta", 90), ("Mistake", removed_points)):
            self.games[title] = self.db.add_game(
                Game(None, title, None, points, 0, "not_played", ""),
            )
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE games SET auction_only=1 WHERE id=?", (self.games["Mistake"],),
            )
            sid = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,remaining_ms,remaining_seconds,deadline_at"
                ") VALUES(?,?,?,?,?,?,?,?)",
                ("Removed-lot regression", "max_amount", "local", self.earlier,
                 "running", 0, 0, self.earlier),
            ).lastrowid)
            self.entries = {}
            for position, (title, starting, bid) in enumerate(
                (("Alpha", 100, 0), ("Beta", 90, 0), ("Mistake", 0, removed_points)), 1,
            ):
                self.entries[title] = int(conn.execute(
                    "INSERT INTO auction_entries("
                    "auction_id,game_id,starting_sm_points,bid_sm_points,weight,active,"
                    "snapshot_title,snapshot_release_date,snapshot_coop,snapshot_status,"
                    "snapshot_review,start_position"
                    ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (sid, self.games[title], starting, bid, starting + bid, 1,
                     title, "2026-01-02", 0, "not_played", "Retained source snapshot", position),
                ).lastrowid)
            conn.execute(
                "INSERT INTO contributions(game_id,source,external_event_id,points,unit,created_at) "
                "VALUES(?,?,?,?,?,?)",
                (self.games["Mistake"], "removed-lot-fixture", "deleted-bid",
                 removed_points, "SM", self.earlier),
            )
        return sid

    def _exercise_correction(
        self, *, removed_points, credited, expected_status, expected_winner,
        expected_beta_points, expected_results, legacy_tombstone_active=False,
    ):
        sid = self._seed_running_source(removed_points)
        pending_request = {
            "source": "removed-lot-regression",
            "external_event_id": self.id(),
            "game_id": self.games["Beta"],
            "amount": str(credited),
            "source_unit": "PLN",
            "auction_id": sid,
            "payload": {"normalized": {"lot_title": "Beta"}},
        }
        pending = self.db.queue_external_conversion_event(**pending_request)
        pending_id = pending["id"]

        removed = self.db.delete_temporary_auction_lot(sid, self.games["Mistake"])
        self.assertEqual(removed["removed_contributions"], 1)
        deleted_entry = self._entry(self.entries["Mistake"])
        self.assertIsNone(deleted_entry["game_id"])
        self.assertEqual((deleted_entry["active"], deleted_entry["result"]), (0, "removed"))

        self.db.finish_auction(sid)
        before = self.db.get_auction_session(sid)
        self.assertEqual(before["status"], "winner_selected")
        self.assertEqual(before["winner_game_id"], self.games["Alpha"])
        tombstone = self._entry(self.entries["Mistake"])
        # Existing finish_auction behavior rewrites result='removed'. Fix1
        # preserves the post-finish history exactly; it does not repair that.
        self.assertEqual((tombstone["active"], tombstone["result"]), (0, "not_winner"))
        if legacy_tombstone_active:
            # A prior buggy correction could persist this state when the
            # deleted lot's retained score was below the surviving leaders.
            with self.db.connect() as conn:
                conn.execute(
                    "UPDATE auction_entries SET active=1 WHERE id=?",
                    (self.entries["Mistake"],),
                )
            tombstone = self._entry(self.entries["Mistake"])
            self.assertEqual(tombstone["active"], 1)
        self.assertTrue(self.db.get_pending_conversion_event(pending_id)["can_apply"])
        self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 1)

        result = self.db.apply_pending_conversion_event(pending_id)
        self.assertEqual(result["auction_id"], sid)
        self.assertEqual(result["game_id"], self.games["Beta"])
        self.assertEqual(result["credited_sm_points"], credited)
        after = self.db.get_auction_session(sid)
        self.assertEqual(after["status"], expected_status)
        self.assertEqual(
            after["winner_game_id"],
            self.games[expected_winner] if expected_winner is not None else None,
        )
        for column in (
            "started_at", "finished_at", "deadline_at", "remaining_ms",
            "remaining_seconds", "duration_ms", "duration_seconds",
            "timer_phase_starts_at", "wheel_spin_id",
        ):
            self.assertEqual(after[column], before[column], column)
        self.assertEqual(after["remaining_ms"], 0)
        self.assertIsNone(after["deadline_at"])
        self.assertEqual(self.db.get_game(self.games["Alpha"]).sm_points, 100)
        self.assertEqual(self.db.get_game(self.games["Beta"]).sm_points, expected_beta_points)
        for title, expected_result in zip(("Alpha", "Beta"), expected_results):
            entry = self._entry(self.entries[title])
            self.assertEqual(entry["active"], 1)
            self.assertEqual(entry["result"], expected_result)
        beta_entry = self._entry(self.entries["Beta"])
        self.assertEqual(beta_entry["bid_sm_points"], credited)
        self.assertEqual(beta_entry["weight"], expected_beta_points)

        applied = self.db.get_pending_conversion_event(pending_id)
        self.assertEqual(applied["status"], "applied")
        self.assertEqual(applied["auction_id"], sid)
        self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 0)
        with self.db.connect() as conn:
            contribution = conn.execute("SELECT * FROM contributions").fetchall()
            self.assertEqual(len(contribution), 1)
            self.assertEqual(contribution[0]["game_id"], self.games["Beta"])
            self.assertEqual(contribution[0]["external_event_id"], self.id())
            self.assertEqual(contribution[0]["credited_sm_points"], credited)
            event = conn.execute("SELECT * FROM external_events").fetchone()
            self.assertEqual(event["processing_status"], "processed")
            self.assertTrue(event["processed_at"])
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM games").fetchone()[0], 2)
            self.assertIsNone(conn.execute(
                "SELECT id FROM games WHERE id=? OR title='Mistake'", (self.games["Mistake"],),
            ).fetchone())
            audit = conn.execute(
                "SELECT after_json FROM change_log WHERE entity_type='auction_session' "
                "AND entity_id=? AND action='post_expiry_pending_correction'", (sid,),
            ).fetchall()
            self.assertEqual(len(audit), 1)
            self.assertEqual(json.loads(audit[0]["after_json"])["source_auction_id"], sid)

        replay = self.db.queue_external_conversion_event(**pending_request)
        self.assertEqual(replay["id"], pending_id)
        self.assertEqual(replay["status"], "applied")
        with self.assertRaises(RuntimeError):
            self.db.apply_pending_conversion_event(pending_id)
        with self.db.connect() as conn:
            for table in ("contributions", "external_events", "pending_conversions"):
                self.assertEqual(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 1)
        self.assertEqual(self.db.get_game(self.games["Beta"]).sm_points, expected_beta_points)
        self.assertEqual(self.db.get_auction_session(sid), after)
        self.assertEqual(self._entry(self.entries["Mistake"]), {**tombstone, "active": 0})

    def test_high_deleted_score_does_not_block_late_winner(self):
        self._exercise_correction(
            removed_points=200, credited=15, expected_status="winner_selected",
            expected_winner="Beta", expected_beta_points=105,
            expected_results=("not_winner", "winner"),
        )

    def test_high_deleted_score_does_not_block_late_tie(self):
        self._exercise_correction(
            removed_points=200, credited=10, expected_status="tie_break_required",
            expected_winner=None, expected_beta_points=100,
            expected_results=("tie", "tie"),
        )

    def test_low_deleted_score_stays_inactive_after_late_winner(self):
        self._exercise_correction(
            removed_points=50, credited=15, expected_status="winner_selected",
            expected_winner="Beta", expected_beta_points=105,
            expected_results=("not_winner", "winner"),
        )

    def test_low_deleted_score_stays_inactive_after_late_tie(self):
        self._exercise_correction(
            removed_points=50, credited=10, expected_status="tie_break_required",
            expected_winner=None, expected_beta_points=100,
            expected_results=("tie", "tie"),
        )

    def test_legacy_reactivated_deleted_lot_is_made_inactive_again(self):
        self._exercise_correction(
            removed_points=50, credited=15, expected_status="winner_selected",
            expected_winner="Beta", expected_beta_points=105,
            expected_results=("not_winner", "winner"), legacy_tombstone_active=True,
        )


if __name__ == "__main__":
    unittest.main()
