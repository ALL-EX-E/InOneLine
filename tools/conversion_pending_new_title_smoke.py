"""P19-C / UI-085: show saved pending titles and allow safe explicit Apply."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.db.common import Game
from streaming_manager.views.settings import SettingsTab


class PendingNewTitleTests(unittest.TestCase):
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

    def add_pending(self, event_id, title, *, auction_id=None, game_id=None, amount="4", source_unit="PLN"):
        payload = (
            json.dumps({"normalized": {"lot_title": title}}, ensure_ascii=False)
            if title is not None else "{}"
        )
        with self.db.connect() as conn:
            ext = conn.execute(
                "INSERT INTO external_events("
                "source,external_event_id,event_type,payload_json,processing_status,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("test", event_id, "donation", payload, "awaiting_rate",
                 "2026-10-19T00:00:00+00:00"),
            )
            pending = conn.execute(
                "INSERT INTO pending_conversions("
                "external_event_row_id,game_id,auction_id,source_amount_text,"
                "source_unit,source_unit_label,unit_kind,status,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,?)",
                (ext.lastrowid, game_id, auction_id, amount, source_unit, source_unit,
                 "currency", "awaiting_rate", "2026-10-19T00:00:00+00:00"),
            )
            return int(pending.lastrowid)

    def counts(self):
        with self.db.connect() as conn:
            return (
                conn.execute("SELECT COUNT(*) FROM games").fetchone()[0],
                conn.execute("SELECT COUNT(*) FROM contributions").fetchone()[0],
            )

    def test_new_usable_title_visible_before_game_creation(self):
        pid = self.add_pending("new-1", "Новая игра")
        event = self.db.get_pending_conversion_event(pid)
        self.assertIsNone(event["game_id"])
        self.assertEqual(event["game_title"], "Новая игра")
        self.assertFalse(event["can_apply"])
        self.assertEqual(self.counts(), (0, 0))
        self.db.set_conversion_rate("PLN", "1,5")
        event = self.db.get_pending_conversion_event(pid)
        self.assertEqual(event["preview_sm_points"], 6)
        self.assertTrue(event["can_apply"])
        self.assertEqual(self.counts(), (0, 0))

    def test_user_interface_displays_new_title_and_enables_apply_after_rate(self):
        pid = self.add_pending("new-2", "Игра без предварительной записи")
        tab = SettingsTab(self.db, self.paths, LocalApiServer(self.db))
        try:
            self.assertEqual(tab.pending_conversion_table.rowCount(), 1)
            self.assertEqual(tab.pending_conversion_table.item(0, 2).text(), "Игра без предварительной записи")
            btn = tab.pending_conversion_table.cellWidget(0, 5)
            self.assertIsInstance(btn, QPushButton)
            self.assertFalse(btn.isEnabled())
            self.db.set_conversion_rate("PLN", "2")
            tab._refresh_pending_conversion_rows()
            self.assertTrue(tab.pending_conversion_table.cellWidget(0, 5).isEnabled())
            self.assertEqual(tab.pending_conversion_table.item(0, 2).text(), "Игра без предварительной записи")
            self.assertIsNone(self.db.get_pending_conversion_event(pid)["game_id"])
            with patch.object(QMessageBox, "question", return_value=QMessageBox.No) as confirm:
                tab._apply_pending_conversion(pid)
            self.assertIn("Игра без предварительной записи", confirm.call_args.args[2])
            self.assertEqual(self.counts(), (0, 0))
        finally:
            tab.thread_pool.waitForDone(5000)
            tab.deleteLater()
            self.app.processEvents()

    def test_manual_apply_creates_persistent_game_once_and_deduplicates(self):
        first = self.add_pending("new-3", "Игра Проверка")
        second = self.add_pending("new-4", "игра проверка")
        self.db.set_conversion_rate("PLN", "2")
        self.assertEqual(self.counts(), (0, 0))
        a = self.db.apply_pending_conversion_event(first)
        self.assertEqual(a["credited_sm_points"], 8)
        self.assertIsNone(a["auction_id"])
        self.assertEqual(self.db.get_pending_conversion_event(first)["status"], "applied")
        b = self.db.apply_pending_conversion_event(second)
        self.assertEqual(b["game_id"], a["game_id"])
        self.assertEqual(self.counts(), (1, 2))
        with self.db.connect() as conn:
            game = conn.execute(
                "SELECT title,sm_points,auction_only FROM games WHERE id=?",
                (a["game_id"],),
            ).fetchone()
            self.assertEqual(int(game["sm_points"]), 16)
            self.assertEqual(int(game["auction_only"]), 0)
        with self.assertRaises(RuntimeError):
            self.db.apply_pending_conversion_event(first)
        self.assertEqual(self.counts(), (1, 2))

    def test_existing_game_id_remains_applicable_without_payload_title(self):
        game_id = self.db.add_game(Game(
            None, "Уже существующая игра", None, 2, 0, "not_played", ""
        ))
        pid = self.add_pending("known-id", None, game_id=game_id)
        self.db.set_conversion_rate("PLN", "2")
        event = self.db.get_pending_conversion_event(pid)
        self.assertEqual(event["game_id"], game_id)
        self.assertEqual(event["game_title"], "Уже существующая игра")
        self.assertTrue(event["can_apply"])
        result = self.db.apply_pending_conversion_event(pid)
        self.assertEqual(result["game_id"], game_id)
        self.assertEqual(self.counts(), (1, 1))

    def test_missing_title_malformed_payload_and_zero_credit_are_not_enabled(self):
        missing = self.add_pending("missing", None)
        zero = self.add_pending("zero", "Нулевой перевод", amount="0")
        self.db.set_conversion_rate("PLN", "3")
        for pid in (missing, zero):
            self.assertFalse(self.db.get_pending_conversion_event(pid)["can_apply"])
        self.assertEqual(self.db.get_pending_conversion_event(missing)["game_title"], "")
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE external_events SET payload_json='bad-json' "
                "WHERE external_event_id='missing'"
            )
        self.assertFalse(self.db.get_pending_conversion_event(missing)["can_apply"])
        self.assertEqual(self.counts(), (0, 0))

    def test_closed_source_auction_never_reassigned_to_persistent_game(self):
        with self.db.connect() as conn:
            aid = conn.execute(
                "INSERT INTO auction_sessions(name,mode,provider,created_at,status) "
                "VALUES(?,?,?,?,?)",
                ("Old auction", "normal", "local",
                 "2026-10-19T00:00:00+00:00", "running"),
            ).lastrowid
        pid = self.add_pending("old-event", "Старая игра", auction_id=aid)
        self.db.set_conversion_rate("PLN", "1")
        event = self.db.get_pending_conversion_event(pid)
        self.assertEqual(event["game_title"], "Старая игра")
        self.assertTrue(event["can_apply"])
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE auction_sessions SET status='finished' WHERE id=?", (aid,)
            )
        self.assertFalse(self.db.get_pending_conversion_event(pid)["can_apply"])
        with self.assertRaises(RuntimeError):
            self.db.apply_pending_conversion_event(pid)
        self.assertEqual(self.counts(), (0, 0))


if __name__ == "__main__":
    unittest.main()
