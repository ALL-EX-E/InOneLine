"""UI-086 P20-B: post-00:00 source-session corrections for existing Max Amount lots."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, Game
from streaming_manager.api_server import LocalApiServer
from streaming_manager.views.settings import SettingsTab


class ExpiredSourceCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.db.set_conversion_rate("PLN", "1")
        for title, points in [("Альфа", 100), ("Бета", 90), ("Гамма", 80)]:
            self.db.add_game(Game(None, title, None, points, 0, "not_played", ""))
        with self.db.connect() as conn:
            self.games = {str(r["title"]): int(r["id"]) for r in
                          conn.execute("SELECT id,title FROM games").fetchall()}
        self.earlier = "2026-10-19T09:00:00+00:00"

    def tearDown(self):
        self.tmp.cleanup()

    def session(self, scores=None, *, status="winner_selected", active=None):
        scores = scores or {"Альфа": 100, "Бета": 90}
        active = active or list(scores)
        winner = max(scores, key=scores.get) if status == "winner_selected" else None
        with self.db.connect() as conn:
            sid = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,status,winner_game_id,"
                "remaining_ms,remaining_seconds,finished_at"
                ") VALUES(?,?,?,?,?,?,?,?,?)",
                ("Испытание", "max_amount", "local", self.earlier, status,
                 self.games[winner] if winner else None, 0, 0, self.earlier),
            ).lastrowid)
            for title, points in scores.items():
                conn.execute(
                    "INSERT INTO auction_entries("
                    "auction_id,game_id,starting_sm_points,bid_sm_points,weight,"
                    "active,result,snapshot_title"
                    ") VALUES(?,?,?,?,?,?,?,?)",
                    (sid, self.games[title], points, 0, points,
                     int(title in active),
                     "winner" if title == winner else (
                         "tie" if status == "tie_break_required" and title in active
                         else "not_winner"),
                     title),
                )
        return sid

    def pending(self, sid, title, amount, *, event_id="late", link_by_id=True):
        with self.db.connect() as conn:
            raw_id = int(conn.execute(
                "INSERT INTO external_events("
                "source,external_event_id,event_type,payload_json,"
                "processing_status,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("test", event_id, "donation",
                 json.dumps({"normalized": {"lot_title": title}}, ensure_ascii=False),
                 "awaiting_manual_apply", self.earlier),
            ).lastrowid)
            pid = int(conn.execute(
                "INSERT INTO pending_conversions("
                "external_event_row_id,game_id,auction_id,source_amount_text,"
                "source_unit,source_unit_label,unit_kind,status,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,?)",
                (raw_id, self.games[title] if link_by_id and title in self.games else None,
                 sid, str(amount), "PLN", "PLN", "currency",
                 "awaiting_manual_apply", self.earlier),
            ).lastrowid)
        return pid

    def entries(self, sid):
        with self.db.connect() as conn:
            return {int(r["game_id"]): dict(r) for r in conn.execute(
                "SELECT game_id,starting_sm_points,bid_sm_points,weight,active,result "
                "FROM auction_entries WHERE auction_id=?", (sid,),
            ).fetchall()}

    def contribution_count(self):
        with self.db.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM contributions").fetchone()[0])

    def test_existing_lot_after_expiry_changes_winner_and_keeps_timer_finished(self):
        sid = self.session()
        pid = self.pending(sid, "Бета", 15)
        self.assertTrue(self.db.get_pending_conversion_event(pid)["can_apply"])
        before = self.db.get_auction_session(sid)
        result = self.db.apply_pending_conversion_event(pid)
        self.assertEqual(result["auction_id"], sid)
        self.assertEqual(result["game_id"], self.games["Бета"])
        after = self.db.get_auction_session(sid)
        self.assertEqual(after["status"], "winner_selected")
        self.assertEqual(after["winner_game_id"], self.games["Бета"])
        for column in ("finished_at", "remaining_ms", "deadline_at"):
            self.assertEqual(before[column], after[column])
        self.assertEqual(self.entries(sid)[self.games["Бета"]]["bid_sm_points"], 15)
        self.assertEqual(self.db.get_game(self.games["Бета"]).sm_points, 105)
        self.assertEqual(self.contribution_count(), 1)
        with self.assertRaises(RuntimeError):
            self.db.apply_pending_conversion_event(pid)
        self.assertEqual(self.contribution_count(), 1)

    def test_tie_recalculates_all_lots_including_previously_inactive(self):
        sid = self.session(
            {"Альфа": 100, "Бета": 100, "Гамма": 90},
            status="tie_break_required", active=["Альфа", "Бета"],
        )
        pid = self.pending(sid, "Гамма", 15, link_by_id=False)
        self.assertTrue(self.db.get_pending_conversion_event(pid)["can_apply"])
        self.db.apply_pending_conversion_event(pid)
        session = self.db.get_auction_session(sid)
        self.assertEqual(session["status"], "winner_selected")
        self.assertEqual(session["winner_game_id"], self.games["Гамма"])
        entries = self.entries(sid)
        self.assertTrue(all(e["active"] for e in entries.values()))
        self.assertEqual(entries[self.games["Гамма"]]["result"], "winner")

    def test_late_apply_can_create_new_tie_and_source_gate_stays_until_resolved(self):
        sid = self.session()
        p1 = self.pending(sid, "Бета", 10, event_id="source-1")
        p2 = self.pending(sid, "Альфа", 1, event_id="source-2")
        self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 2)
        self.db.apply_pending_conversion_event(p1)
        self.assertEqual(self.db.get_auction_session(sid)["status"], "tie_break_required")
        self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 1)
        with self.assertRaisesRegex(RuntimeError, "необработанные поступления"):
            self.db.start_auction_tie_wheel(sid)
        self.db.reject_pending_conversion_event(p2)
        self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 0)

    def test_closed_history_remains_immutable_and_no_new_auction_capture(self):
        old = self.session(status="confirmed")
        newer = self.session()
        pid = self.pending(old, "Бета", 15)
        # Existing S1 legacy compatibility: a direct backend Apply to a
        # persistent game may still credit that game outside a closed auction.
        # It must NEVER rewrite the old auction or capture the newer one.
        self.assertFalse(self.db.get_pending_conversion_event(pid)["can_apply"])
        before_newer = self.entries(newer)
        before_old = self.entries(old)
        old_session = self.db.get_auction_session(old)
        result = self.db.apply_pending_conversion_event(pid)
        self.assertIsNone(result["auction_id"])
        self.assertEqual(self.entries(newer), before_newer)
        self.assertEqual(self.entries(old), before_old)
        self.assertEqual(self.db.get_auction_session(old), old_session)
        self.assertEqual(self.contribution_count(), 1)
        self.assertEqual(self.db.get_pending_conversion_event(pid)["status"], "applied")
        with self.assertRaises(RuntimeError):
            self.db.apply_pending_conversion_event(pid)
        self.assertEqual(self.contribution_count(), 1)

    def test_missing_source_lot_is_now_allowed_only_in_source_session_p20c(self):
        # P20-C changes exactly this P20-B blocked-case expectation; all
        # four pre-existing source-locked correction tests stay unchanged.
        sid = self.session()
        pid = self.pending(sid, "Неизвестный лот", 15, link_by_id=False)
        before = self.db.get_auction_session(sid)
        self.assertTrue(self.db.get_pending_conversion_event(pid)["can_apply"])
        with self.db.connect() as conn:
            games_before = int(conn.execute("SELECT COUNT(*) FROM games").fetchone()[0])
        result = self.db.apply_pending_conversion_event(pid)
        self.assertEqual(result["auction_id"], sid)
        self.assertEqual(self.db.get_game(result["game_id"]).title, "Неизвестный лот")
        self.assertEqual(self.db.get_game(result["game_id"]).sm_points, 15)
        with self.db.connect() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM games").fetchone()[0],
                             games_before + 1)
            self.assertEqual(conn.execute(
                "SELECT auction_only FROM games WHERE id=?", (result["game_id"],)
            ).fetchone()[0], 1)
        after = self.db.get_auction_session(sid)
        for key in ("remaining_ms", "deadline_at", "finished_at"):
            self.assertEqual(before[key], after[key])
        self.assertEqual(self.db.count_unresolved_auction_conversions(sid), 0)
        self.assertEqual(self.contribution_count(), 1)


if __name__ == "__main__":
    unittest.main()
