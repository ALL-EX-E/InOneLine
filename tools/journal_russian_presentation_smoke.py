"""P23-C/UI-081 #3: Journal readable events; audit and technical search stay intact."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from streaming_manager.views.log import LogTab


class JournalDb:
    path = "unused-for-rendering.db"

    def __init__(self, records):
        self.records = records
        self.limits = []

    def list_log(self, limit=500):
        self.limits.append(limit)
        return self.records if limit is None else self.records[:limit]


def event(entity, action, before=None, after=None, event_id=71, **extra):
    return {
        "id": event_id,
        "entity_type": entity,
        "entity_id": 9,
        "action": action,
        "before_json": json.dumps(before, ensure_ascii=False) if before is not None else None,
        "after_json": json.dumps(after, ensure_ascii=False) if after is not None else None,
        "created_at": "2026-10-21T11:00:00+00:00",
        **extra,
    }


class RussianJournalPresentationSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.db = JournalDb([
            event("auction_session", "pause", None, {"remaining_ms": 31000}),
            event("auction_lot", "post_expiry_temporary_rename",
                  {"old_title": "Старое", "sm_points": 70},
                  {"new_title": "Новое", "sm_points": 70}),
            event("auction_bid", "post_expiry_add",
                  {"game_id": 3, "sm_points": 70},
                  {"game_id": 3, "added_sm_points": 15, "sm_points": 85}),
            event("setting", "update", {"key": "test_volume", "value": "1"},
                  {"key": "test_volume", "value": "2"}),
            event("setting", "update", {"key": "test_api_key", "value": "legacy_secret"},
                  {"key": "test_api_key", "value": "new_secret"}),
            event("integration_event", "apply", None, {
                "source": "twitch", "lot_title": "Лот 1",
                "source_amount_text": "5", "source_unit": "SM",
                "credited_sm_points": 5, "auction_id": 1,
                "external_event_id": "test-123",
            }, external_payload_json=json.dumps({"normalized": {"contributor": "Зритель"}})),
            event("external_conversion", "queue", None, {
                "source": "DonationAlerts", "source_amount_text": "10",
                "source_unit": "RUB", "status": "awaiting_rate"}),
            event("game", "create", None, {"title": "Игровой лот"}),
            event("future_entity", "future_action", None, {"title": "Future"}),
        ])
        self.tab = LogTab(self.db)
        self.tab.thread_pool.waitForDone(10000)
        self.app.processEvents()

    def tearDown(self):
        self.tab.thread_pool.waitForDone(10000)
        self.tab.close()
        self.tab.deleteLater()
        self.app.processEvents()

    def test_readable_auction_labels_reuse_existing_formatter(self):
        rows = self.tab._load_rows()["rows"]
        self.assertEqual([x[1] for x in rows[:3]], ["Аукцион", "Лот аукциона", "Ставка"])
        self.assertEqual(rows[0][3], "ПАУЗА")
        self.assertIn("Осталось:", rows[0][4])
        self.assertEqual(rows[1][3], "ЛОТ ПЕРЕИМЕНОВАН")
        self.assertIn("«Старое» → «Новое»", rows[1][4])
        self.assertEqual(rows[2][3], "БАЛЛЫ ПОСЛЕ 00:00")
        self.assertIn("+15 баллов", rows[2][4])

    def test_settings_secret_redaction_and_readable_values(self):
        rows = self.tab._load_rows()["rows"]
        self.assertEqual(rows[3][1], "Настройка")
        self.assertIn("test_volume: 1 → 2", rows[3][4])
        self.assertIn("[СКРЫТО]", rows[4][4])
        self.assertNotIn("legacy_secret", rows[4][4])
        self.assertNotIn("new_secret", rows[4][4])

    def test_integration_conversion_game_fallback(self):
        rows = self.tab._load_rows()["rows"]
        self.assertEqual(rows[5][3], "НАЧИСЛЕНО")
        self.assertIn("Зритель", rows[5][4])
        self.assertIn("5 баллов", rows[5][4])
        self.assertEqual(rows[6][1:4:2], ("Конвертация", "ОЖИДАЕТ ПРИМЕНЕНИЯ"))
        self.assertIn("Источник: DonationAlerts", rows[6][4])
        self.assertEqual(rows[7][1:4:2], ("Игра", "СОЗДАНИЕ"))
        self.assertIn("Игровой лот", rows[7][4])
        self.assertEqual(rows[8][1:4:2], ("future_entity", "FUTURE_ACTION"))

    def test_raw_search_and_original_row_scope(self):
        self.assertEqual(len(self.tab._load_rows("post_expiry_add")["rows"]), 1)
        self.assertEqual(len(self.tab._load_rows("БАЛЛЫ ПОСЛЕ 00:00")["rows"]), 1)
        self.assertEqual(len(self.tab._load_rows("test_volume")["rows"]), 1)
        self.assertEqual(self.db.limits[-1], None)
        self.tab._load_rows("")
        self.assertEqual(self.db.limits[-1], 500)
        self.assertEqual(self.tab.model.HEADERS,
                         ("ВРЕМЯ", "ОБЪЕКТ", "ID", "ДЕЙСТВИЕ", "ПОДРОБНОСТИ"))
        self.assertEqual(self.tab._search_timer.interval(), 250)


if __name__ == "__main__":
    unittest.main()
