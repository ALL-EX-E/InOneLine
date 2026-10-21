"""UI-080 #4: readable auction audit presentation; immutable change_log untouched."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.views.auction_history import format_auction_history_event


class ReadableCompletedAuctionEventsTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        paths = AppPaths.from_root(self.temp.name)
        paths.ensure_runtime_dirs()
        self.db = Database(paths.database_path)
        self.now = "2026-10-21T07:00:00+00:00"

    def tearDown(self):
        self.temp.cleanup()

    def event(self, entity, action, before=None, after=None, title="Лот 1"):
        return {
            "id": 117,
            "entity_type": entity,
            "action": action,
            "title": title,
            "created_at": self.now,
            "before": before or {},
            "after": after or {},
        }

    def render(self, entity, action, before=None, after=None, title="Лот 1"):
        result = format_auction_history_event(
            self.event(entity, action, before, after, title)
        )
        self.assertEqual(result["event_id"], 117)
        self.assertIn("Лот", result["text"])
        self.assertRegex(result["exact_time"], r"^\\d{2}\\.\\d{2}\\.\\d{4} \\d{2}:\\d{2}:\\d{2}$")
        self.assertTrue(result["kind"])
        return result["text"]

    def test_late_manual_bid_and_decrease_show_exact_delta_and_total(self):
        added = self.render(
            "auction_bid", "post_expiry_add", {"sm_points": 70},
            {"added_sm_points": 20, "sm_points": 90},
        )
        self.assertIn("БАЛЛЫ ПОСЛЕ 00:00", added)
        self.assertIn("+20 баллов", added)
        self.assertIn("итог: 90", added)
        reduced = self.render(
            "auction_bid", "post_expiry_decrease", {"sm_points": 90},
            {"decreased_sm_points": 10, "sm_points": 80},
        )
        self.assertIn("УМЕНЬШЕНИЕ ПОСЛЕ 00:00", reduced)
        self.assertIn("−10 баллов", reduced)
        self.assertIn("итог: 80", reduced)

    def test_existing_auction_bid_labels_are_preserved(self):
        self.assertIn("ДОБАВЛЕНИЕ", self.render(
            "auction_bid", "add", None,
            {"added_sm_points": 50, "sm_points": 70}))
        self.assertIn("УМЕНЬШЕНИЕ", self.render(
            "auction_bid", "decrease", None,
            {"decreased_sm_points": 20, "sm_points": 50}))

    def test_late_created_and_normalized_merged_lots(self):
        new = self.render(
            "auction_lot", "post_expiry_create", None,
            {"title": "Лот 1", "added_sm_points": 15, "merged": False})
        self.assertIn("НОВЫЙ ЛОТ ПОСЛЕ 00:00", new)
        self.assertIn("+15 баллов", new)
        merged = self.render(
            "auction_lot", "post_expiry_merge", None,
            {"title": "Лот 1", "added_sm_points": 20, "merged": True})
        self.assertIn("ЛОТ ОБЪЕДИНЁН ПОСЛЕ 00:00", merged)
        self.assertIn("+20 баллов", merged)
        self.assertIn("существующим лотом", merged)

    def test_rename_uses_recorded_titles_and_preserved_amount(self):
        text = self.render(
            "auction_lot", "post_expiry_temporary_rename",
            {"old_title": "Раннее", "sm_points": 120},
            {"new_title": "Позднее", "sm_points": 120},
            title="Позднее",
        )
        self.assertIn("ЛОТ ПЕРЕИМЕНОВАН", text)
        self.assertIn("«Раннее» → «Позднее»", text)
        self.assertIn("баллы сохранены: 120", text)

    def test_permanent_exclusion_explains_data_preservation(self):
        text = self.render(
            "auction_lot", "post_expiry_permanent_exclude",
            {"title": "Лот 1", "sm_points": 99},
            {"result": "removed", "game_preserved": True},
        )
        self.assertIn("ПОСТОЯННЫЙ ЛОТ ИСКЛЮЧЁН", text)
        self.assertIn("99 баллов", text)
        self.assertIn("игра и её баллы сохранены", text)

    def test_pending_source_materialization_includes_correct_auction(self):
        with self.db.connect() as conn:
            sid = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,finished_at,status"
                ") VALUES(?,?,?,?,?,?)",
                ("Аукцион #1", "max_amount", "local", self.now, self.now,
                 "confirmed"),
            ).lastrowid)
            other = int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,finished_at,status"
                ") VALUES(?,?,?,?,?,?)",
                ("Аукцион #2", "max_amount", "local", self.now, self.now,
                 "confirmed"),
            ).lastrowid)
            conn.execute(
                "INSERT INTO change_log("
                "entity_type,entity_id,action,before_json,after_json,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("auction_session", sid, "create", None,
                 json.dumps({"id": sid, "name": "Аукцион #1"}), self.now))
            conn.execute(
                "INSERT INTO change_log("
                "entity_type,entity_id,action,before_json,after_json,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("auction_lot", 123, "post_expiry_title_lot", None,
                 json.dumps({"source_auction_id": sid, "title": "Лот из поступления",
                             "temporary": True}), self.now))
            conn.execute(
                "INSERT INTO change_log("
                "entity_type,entity_id,action,before_json,after_json,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("auction_lot", 124, "post_expiry_title_lot", None,
                 json.dumps({"source_auction_id": other, "title": "Чужой лот",
                             "temporary": False}), self.now))
        rows = self.db.list_auction_history_events(sid)["events"]
        self.assertEqual([row["action"] for row in rows],
                         ["create", "post_expiry_title_lot"])
        self.assertIn(
            "ЛОТ ИЗ ОЖИДАЮЩЕГО ПОСТУПЛЕНИЯ",
            format_auction_history_event(rows[-1])["text"],
        )
        self.assertIn("Лот из поступления",
                      format_auction_history_event(rows[-1])["text"])

    def test_wheel_archive_replay_and_late_recalculation(self):
        archive = self.render(
            "auction_session", "elimination_archive", None,
            {"title": "Лот 1", "remaining_lots": 0})
        self.assertIn("аукцион завершён без победителя", archive)
        for action, wanted in (
            ("wheel_spin_stopped", "ВРАЩЕНИЕ ОСТАНОВЛЕНО"),
            ("wheel_spin_replayed", "ВРАЩЕНИЕ ПОВТОРЕНО"),
        ):
            self.assertIn(wanted, self.render("auction_session", action))
        recalculated = self.render(
            "auction_session", "post_expiry_manual_decrease", None,
            {"status": "winner_selected", "target_game_id": 33,
             "credited_sm_points": -5})
        self.assertIn("ПЕРЕСЧЁТ ПОСЛЕ УМЕНЬШЕНИЯ", recalculated)
        self.assertIn("определён лидер", recalculated)
        self.assertIn("−5 баллов", recalculated)

    def test_existing_history_actions_and_unknown_fallback(self):
        scenarios = (
            ("auction_session", "pause", {"remaining_ms": 1000}, "ПАУЗА"),
            ("auction_session", "tie_wheel", {"wheel_duration_ms": 2000},
             "ТАЙ-БРЕЙК: КОЛЕСО"),
            ("auction_session", "wheel", {"spin_index": 3}, "Раунд 3"),
            ("auction_session", "confirm_winner", {}, "ПОБЕДИТЕЛЬ ПОДТВЕРЖДЁН"),
            ("auction_session", "cancel", {}, "АУКЦИОН ОТМЕНЁН"),
            ("auction_lot", "delete", {}, "ЛОТ УДАЛЁН"),
        )
        for entity, action, after, expected in scenarios:
            with self.subTest(action=action):
                text = self.render(entity, action, None, after)
                self.assertIn(expected, text)
        fallback = self.render(
            "auction_session", "new_future_action", None, {"value": 1})
        self.assertIn("NEW_FUTURE_ACTION", fallback)


if __name__ == "__main__":
    unittest.main()
