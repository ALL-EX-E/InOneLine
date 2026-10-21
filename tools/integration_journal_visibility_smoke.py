"""P22-A / UI-066: source-event audit remains globally visible in Journal.

Read-only presentation via existing change_log and external_events; no
provider-specific journal, no changes to integration credits or event dedup.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, Game
from streaming_manager.views.log import LogTab


class IntegrationJournalVisibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.game_id = self.db.add_game(
            Game(None, "Первый лот", None, 10, 0, "not_played", "")
        )
        self.db.add_game(
            Game(None, "Второй лот", None, 5, 0, "not_played", "")
        )
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO integration_connections("
                "service_key,enabled,status,created_at,updated_at) "
                "VALUES(?,?,?,?,?)",
                ("test", 1, "connected", "2026-10-21T00:00:00+00:00",
                 "2026-10-21T00:00:00+00:00"),
            )
        with patch.object(LogTab, "refresh"):
            self.tab = LogTab(self.db)

    def tearDown(self):
        self.tab.close()
        self.tab.deleteLater()
        self.app.processEvents()
        self.tmp.cleanup()

    def event(self, event_id, *, title="Первый лот", unit="RUB",
              amount="5", game_id=None, auction_id=None):
        return self.db.process_normalized_integration_event(
            service_key="test", external_event_id=event_id,
            event_type="donation", source_amount=amount, source_unit=unit,
            contributor="Автор пожертвования", lot_title=title,
            game_id=game_id, auction_id_hint=auction_id,
            force_outside_auction=auction_id is None,
            provider_metadata={"provider_time": "2026-10-21T03:30Z",
                               "access_token": "private-never-display"},
        )

    def entries(self, text=""):
        return [
            row for row in self.tab._load_rows(text)["rows"]
            if row[1] == "Интеграция"
        ]

    def test_known_external_credit_shows_source_sender_amount_target_destination(self):
        first = self.event("journal-known")
        self.assertEqual(first["status"], "processed")
        rows = self.entries()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row[3], "НАЧИСЛЕНО")
        self.assertIn("test", row[4])
        self.assertIn("Автор пожертвования", row[4])
        self.assertIn("5 RUB", row[4])
        self.assertIn("Первый лот", row[4])
        self.assertIn("НАЧИСЛЕНО: 5 баллов", row[4])
        self.assertIn("В основной список", row[4])
        self.assertIn("journal-known", row[4])
        self.assertNotIn("private-never-display", row[4])
        before = len(rows)
        duplicate = self.event("journal-known")
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(len(self.entries()), before)

    def test_archived_lot_stays_visible_as_no_credit_with_russian_reason_and_raw_search(self):
        with self.db.connect() as conn:
            conn.execute("UPDATE games SET archived=1 WHERE id=?", (self.game_id,))
        result = self.event("journal-archived", game_id=self.game_id)
        self.assertEqual(result["status"], "inapplicable")
        self.assertEqual(result["reason"], "target_game_archived")
        rows = self.entries("Лот находится в архиве")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][3], "НЕ НАЧИСЛЕНО")
        self.assertIn("Лот находится в архиве", rows[0][4])
        self.assertIn("journal-archived", rows[0][4])
        self.assertEqual(len(self.entries("target_game_archived")), 1)
        with self.db.connect() as conn:
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM contributions"
            ).fetchone()[0], 0)
        self.assertEqual(len(self.entries("no-such-provider-event")), 0)

    def test_unknown_rate_then_explicit_reject_both_visible_no_credits(self):
        incoming = self.event("journal-unknown", unit="XYZ")
        self.assertEqual(incoming["status"], "awaiting_rate")
        pending = self.entries("journal-unknown")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0][3], "ОЖИДАЕТ КУРСА")
        self.assertIn("ОЖИДАЕТ КОНВЕРТАЦИИ", pending[0][4])
        self.assertIn("Баллы не начислены", pending[0][4])
        self.db.reject_pending_conversion_event(incoming["pending_id"])
        rows = self.entries("journal-unknown")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][3], "НЕ ПРИМЕНЕНО")
        self.assertIn("Оператор отклонил начисление", rows[0][4])
        with self.db.connect() as conn:
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM contributions"
            ).fetchone()[0], 0)

    def test_auction_credit_shows_source_session_and_avoids_main_list_claim(self):
        auction_id = self.db.create_auction_session("max_amount", 300)
        result = self.event("journal-auction", auction_id=auction_id)
        self.assertEqual(result["status"], "processed")
        self.assertEqual(result["auction_id"], auction_id)
        rows = self.entries("journal-auction")
        self.assertEqual(len(rows), 1)
        self.assertIn(f"В аукцион #{auction_id}", rows[0][4])
        self.assertNotIn("В основной список", rows[0][4])


if __name__ == "__main__":
    unittest.main()
