"""P19-D / UI-085: local event time and source context in pending conversions."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QPushButton

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, display_datetime_local
from streaming_manager.views.settings import SettingsTab


class PendingEventTimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)

    def tearDown(self):
        self.tmp.cleanup()

    def add_pending(self, *, event_id="ext-event-1", event_time="2026-07-01T20:11:12+00:00",
                    queued_time="2026-10-19T00:00:00+00:00", with_auction=False):
        auction_id = None
        with self.db.connect() as conn:
            if with_auction:
                auction_id = int(conn.execute(
                    "INSERT INTO auction_sessions(name,mode,provider,created_at,status) "
                    "VALUES(?,?,?,?,?)",
                    ("Session", "max_amount", "local", queued_time, "running"),
                ).lastrowid)
            external = conn.execute(
                "INSERT INTO external_events("
                "source,external_event_id,event_type,payload_json,processing_status,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("test", event_id, "donation",
                 json.dumps({"normalized": {"lot_title": "Новая игра"}}, ensure_ascii=False),
                 "awaiting_rate", event_time),
            )
            pending = conn.execute(
                "INSERT INTO pending_conversions("
                "external_event_row_id,game_id,auction_id,source_amount_text,"
                "source_unit,source_unit_label,unit_kind,contributor,status,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,?,?)",
                (external.lastrowid, None, auction_id, "5", "PLN", "PLN",
                 "currency", "Проверочный автор", "awaiting_rate", queued_time),
            )
        return int(pending.lastrowid), auction_id

    def create_view(self):
        return SettingsTab(self.db, self.paths, LocalApiServer(self.db))

    def close_view(self, tab):
        tab.thread_pool.waitForDone(5000)
        tab.deleteLater()
        self.app.processEvents()

    def test_external_utc_event_time_displayed_in_local_timezone(self):
        event_time = "2026-07-01T20:11:12+00:00"
        queued_time = "2026-10-19T00:00:00+00:00"
        pid, _ = self.add_pending(event_time=event_time, queued_time=queued_time)
        event = self.db.get_pending_conversion_event(pid)
        self.assertEqual(event["event_created_at"], event_time)
        self.assertEqual(event["created_at"], queued_time)
        tab = self.create_view()
        try:
            table = tab.pending_conversion_table
            self.assertEqual(table.columnCount(), 8)
            self.assertEqual(
                [table.horizontalHeaderItem(i).text() for i in range(8)],
                ["Источник", "Время", "Событие", "Игра",
                 "Исходное значение", "К зачислению", "Применить", "Не применять"],
            )
            self.assertEqual(table.rowCount(), 1)
            self.assertEqual(table.item(0, 1).text(), display_datetime_local(event_time))
            self.assertNotEqual(table.item(0, 1).text(), display_datetime_local(queued_time))
            self.assertEqual(table.item(0, 3).text(), "Новая игра")
            self.assertIsInstance(table.cellWidget(0, 6), QPushButton)
            self.assertFalse(table.cellWidget(0, 6).isEnabled())
            self.assertIsInstance(table.cellWidget(0, 7), QPushButton)
            self.assertTrue(table.cellWidget(0, 7).isEnabled())
        finally:
            self.close_view(tab)
        with self.db.connect() as conn:
            raw = conn.execute(
                "SELECT created_at FROM external_events WHERE external_event_id=?",
                ("ext-event-1",),
            ).fetchone()
        self.assertEqual(raw["created_at"], event_time)

    def test_tooltips_preserve_source_contributor_id_target_and_auction_context(self):
        pid, auction_id = self.add_pending(event_id="with-auction", with_auction=True)
        self.assertIsNotNone(auction_id)
        tab = self.create_view()
        try:
            table = tab.pending_conversion_table
            for col in range(6):
                tip = table.item(0, col).toolTip()
                for expected in ("Источник: test", "Отправитель: Проверочный автор",
                                 "ID события: with-auction", "Игра: Новая игра",
                                 f"Аукцион-источник: №{auction_id}"):
                    self.assertIn(expected, tip)
            self.assertIn("ID события: with-auction", table.cellWidget(0, 6).toolTip())
            self.assertFalse(table.cellWidget(0, 6).isEnabled())
        finally:
            self.close_view(tab)
        self.assertEqual(self.db.get_pending_conversion_event(pid)["auction_id"], auction_id)

    def test_refresh_and_rate_keep_time_and_only_enable_existing_apply(self):
        pid, _ = self.add_pending()
        tab = self.create_view()
        try:
            original = tab.pending_conversion_table.item(0, 1).text()
            self.db.set_conversion_rate("PLN", "2")
            tab._refresh_pending_conversion_rows()
            table = tab.pending_conversion_table
            self.assertEqual(table.item(0, 1).text(), original)
            self.assertEqual(
                self.db.get_pending_conversion_event(pid)["event_created_at"],
                "2026-07-01T20:11:12+00:00",
            )
            self.assertEqual(table.item(0, 5).text(), "10 баллов (× 2)")
            self.assertTrue(table.cellWidget(0, 6).isEnabled())
            self.assertEqual(self.db.get_pending_conversion_event(pid)["status"], "awaiting_manual_apply")
            with self.db.connect() as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM contributions").fetchone()[0], 0)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM games").fetchone()[0], 0)
        finally:
            self.close_view(tab)


if __name__ == "__main__":
    unittest.main()
