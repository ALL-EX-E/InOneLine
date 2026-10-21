"""P22-B UI-080 #2: executed completed-auction path, not only initial mode."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.views.auction_history import format_completed_auction_mode
from streaming_manager.views.completed_auction_history import CompletedAuctionHistoryTab


class CompletedHistoryModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.when = "2026-10-21T00:00:00+00:00"

    def tearDown(self):
        self.tmp.cleanup()

    def session(self, mode, wheel_format="standard"):
        with self.db.connect() as conn:
            return int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,finished_at,status,wheel_format"
                ") VALUES(?,?,?,?,?,?,?)",
                ("Режим", mode, "local", self.when, self.when,
                 "confirmed", wheel_format),
            ).lastrowid)

    def event(self, sid, action, **after):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO change_log("
                "entity_type,entity_id,action,before_json,after_json,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("auction_session", sid, action, None,
                 json.dumps(after, ensure_ascii=False), self.when),
            )

    def snapshot(self, sid, index, kind):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO wheel_verification_snapshots("
                "run_id,auction_id,spin_index,result_kind,algorithm_version,"
                "mode,rng_method,rng_value,draw_upper,total_weight,"
                "equal_fallback,winner_game_id,winner_title,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"mock-{sid}-{index}", sid, index, kind, "old-fixture",
                 "weighted_wheel", "local", 0, 1, 1, 0, 1, "Проверка", self.when),
            )

    def mode_label(self, sid):
        rows = self.db.list_completed_auction_sessions()
        row = next(r for r in rows if int(r["id"]) == sid)
        details = self.db.completed_auction_details(sid)
        self.assertIsNotNone(details)
        from_list = format_completed_auction_mode(row, row["mode_evidence"])
        from_details = format_completed_auction_mode(
            details["session"], details["mode_evidence"]
        )
        self.assertEqual(from_list, from_details)
        return from_list

    def test_max_without_actual_wheel_spin(self):
        sid = self.session("max_amount")
        self.assertEqual(self.mode_label(sid), "Максимальная сумма")
        self.event(sid, "tie_wheel")
        self.assertEqual(self.mode_label(sid), "Максимальная сумма")

    def test_max_tie_wheel_actual_spin(self):
        sid = self.session("max_amount")
        self.event(sid, "create", wheel_format="standard")
        self.event(sid, "tie_wheel")
        self.event(sid, "wheel", wheel_format="standard", spin_index=1)
        self.assertEqual(
            self.mode_label(sid), "Максимальная сумма → Колесо при ничьей"
        )

    def test_standard_and_elimination_direct(self):
        standard = self.session("weighted_wheel", "standard")
        elimination = self.session("weighted_wheel", "elimination")
        self.event(standard, "wheel", wheel_format="standard", spin_index=1)
        self.event(elimination, "wheel", wheel_format="elimination", spin_index=1)
        self.assertEqual(self.mode_label(standard), "Обычное колесо")
        self.assertEqual(self.mode_label(elimination), "Выбывание")

    def test_actual_format_transitions_between_spins(self):
        sid = self.session("weighted_wheel", "elimination")
        self.event(sid, "create", wheel_format="elimination")
        self.event(sid, "wheel", wheel_format="elimination", spin_index=1)
        self.event(sid, "wheel", wheel_format="elimination", spin_index=2)
        self.event(sid, "wheel_format", wheel_format="standard")
        self.event(sid, "wheel", wheel_format="standard", spin_index=3)
        self.event(sid, "wheel_format", wheel_format="elimination")
        self.event(sid, "wheel", wheel_format="elimination", spin_index=4)
        self.assertEqual(
            self.mode_label(sid),
            "Выбывание → Обычное колесо → Выбывание",
        )

    def test_unspun_format_switch_not_called_actual(self):
        sid = self.session("weighted_wheel", "standard")
        self.event(sid, "create", wheel_format="elimination")
        self.event(sid, "wheel", wheel_format="elimination", spin_index=1)
        self.event(sid, "wheel_format", wheel_format="standard")
        self.assertEqual(self.mode_label(sid), "Выбывание")

    def test_legacy_snapshot_without_wheel_log(self):
        sid = self.session("weighted_wheel")
        self.snapshot(sid, 1, "eliminated")
        self.assertEqual(self.mode_label(sid), "Выбывание")

    def test_max_to_regular_and_elimination_wheel_audit(self):
        std = self.session("max_amount")
        eli = self.session("max_amount")
        self.event(std, "wheel", wheel_format="standard", spin_index=1)
        self.event(eli, "wheel", wheel_format="elimination", spin_index=1)
        self.assertEqual(
            self.mode_label(std), "Максимальная сумма → Обычное колесо"
        )
        self.assertEqual(
            self.mode_label(eli), "Максимальная сумма → Выбывание"
        )

    def test_qt_table_and_general_show_same_path(self):
        sid = self.session("max_amount")
        self.event(sid, "tie_wheel")
        self.event(sid, "wheel", wheel_format="standard", spin_index=1)
        with patch.object(CompletedAuctionHistoryTab, "_load_verification_details"):
            tab = CompletedAuctionHistoryTab(self.db)
            try:
                mode = tab.table.item(0, 2).text()
                tab._load_details(sid)
                self.assertEqual(
                    mode, "Максимальная сумма → Колесо при ничьей"
                )
                self.assertEqual(mode, tab.general_labels["mode"].text())
                self.assertEqual(tab.sort.count(), 2)
            finally:
                tab.close()
                tab.deleteLater()
                self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
