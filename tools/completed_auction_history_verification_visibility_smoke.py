"""P22-B UI-080 #3: verification tab exists only for actual saved wheel spins.

Pure presentation over already-existing change_log and immutable snapshots;
no mode-based approximation or storage changes.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.views.completed_auction_history import (
    CompletedAuctionHistoryTab,
)


class ConditionalWheelVerificationHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.temp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.at = "2026-10-21T00:00:00+00:00"
        self.tabs = []

    def tearDown(self):
        for tab in self.tabs:
            tab.close()
            tab.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def auction(self, mode="max_amount", wheel_format="standard"):
        with self.db.connect() as conn:
            return int(conn.execute(
                "INSERT INTO auction_sessions("
                "name,mode,provider,created_at,finished_at,status,wheel_format"
                ") VALUES(?,?,?,?,?,?,?)",
                ("Аукцион проверки", mode, "local", self.at, self.at,
                 "confirmed", wheel_format),
            ).lastrowid)

    def event(self, auction_id, action, **after):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO change_log("
                "entity_type,entity_id,action,before_json,after_json,created_at"
                ") VALUES(?,?,?,?,?,?)",
                ("auction_session", auction_id, action, None,
                 json.dumps(after, ensure_ascii=False), self.at),
            )

    def snapshot(self, auction_id, spin_index=1, result_kind="winner"):
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO wheel_verification_snapshots("
                "run_id,auction_id,spin_index,result_kind,algorithm_version,"
                "mode,rng_method,rng_value,draw_upper,total_weight,"
                "equal_fallback,winner_game_id,winner_title,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"history-tab-{auction_id}-{spin_index}", auction_id,
                 spin_index, result_kind, "fixture", "weighted_wheel",
                 "local", 0, 1, 1, 0, 1, "Тестовый лот", self.at),
            )

    def tab(self):
        tab = CompletedAuctionHistoryTab(self.db)
        self.tabs.append(tab)
        return tab

    @staticmethod
    def shown(tab):
        index = tab.details_tabs.indexOf(tab.verification_page)
        assert index == 3, "Verification tab position unexpectedly changed"
        return tab.details_tabs.isTabVisible(index)

    def test_pure_max_amount_has_no_verification_tab(self):
        sid = self.auction()
        tab = self.tab()
        tab._load_details(sid)
        self.assertFalse(self.shown(tab))
        self.assertEqual(tab.details_tabs.count(), 4)
        self.assertEqual(tab.details_tabs.tabText(0), "Общие")
        self.assertEqual(tab.details_tabs.tabText(1), "Лоты")
        self.assertEqual(tab.details_tabs.tabText(2), "События")

    def test_tie_wheel_selected_but_never_spun_is_hidden(self):
        sid = self.auction()
        self.event(sid, "tie_wheel", wheel_duration_ms=8000)
        tab = self.tab()
        tab._load_details(sid)
        self.assertFalse(self.shown(tab))

    def test_direct_wheel_without_actual_spin_is_hidden(self):
        sid = self.auction("weighted_wheel", "elimination")
        self.event(sid, "create", wheel_format="elimination")
        self.event(sid, "wheel_format", wheel_format="standard")
        tab = self.tab()
        tab._load_details(sid)
        self.assertFalse(self.shown(tab))

    def test_legacy_wheel_audit_without_snapshot_visible_with_notice(self):
        sid = self.auction("weighted_wheel")
        self.event(sid, "wheel", wheel_format="standard", spin_index=1)
        tab = self.tab()
        tab._load_details(sid)
        self.assertTrue(self.shown(tab))
        self.assertIn("Verification snapshot отсутствует",
                      tab.verification_notice.text())
        self.assertFalse(tab.verify_result_btn.isVisible())

    def test_snapshot_without_old_wheel_audit_is_visible(self):
        sid = self.auction("weighted_wheel")
        self.snapshot(sid)
        with patch.object(CompletedAuctionHistoryTab,
                          "_render_verification_snapshot"):
            tab = self.tab()
            tab._load_details(sid)
        self.assertTrue(self.shown(tab))
        self.assertEqual(tab.verification_spin_combo.count(), 1)

    def test_multi_round_verification_picker_retained(self):
        sid = self.auction("weighted_wheel", "elimination")
        self.snapshot(sid, 1, "eliminated")
        self.snapshot(sid, 2, "winner")
        with patch.object(CompletedAuctionHistoryTab,
                          "_render_verification_snapshot"):
            tab = self.tab()
            tab._load_details(sid)
        self.assertTrue(self.shown(tab))
        self.assertEqual(tab.verification_spin_combo.count(), 2)
        self.assertIn("Раунд 1", tab.verification_spin_combo.itemText(0))
        self.assertIn("Раунд 2", tab.verification_spin_combo.itemText(1))
        self.assertEqual(tab.verification_spin_combo.currentIndex(), 1)

    def test_switch_rows_and_refresh_hides_old_context(self):
        pure = self.auction()
        with_spin = self.auction("weighted_wheel")
        self.event(with_spin, "wheel", wheel_format="standard", spin_index=1)
        tab = self.tab()
        row_by_id = {
            int(tab.table.item(i, 0).data(Qt.UserRole)): i
            for i in range(tab.table.rowCount())
        }
        tab.table.selectRow(row_by_id[with_spin])
        self.assertTrue(self.shown(tab))
        tab.table.selectRow(row_by_id[pure])
        self.assertFalse(self.shown(tab))
        tab.refresh()
        self.assertTrue(self.shown(tab))
        tab.table.selectRow(row_by_id[pure])
        self.assertFalse(self.shown(tab))
        tab._clear_details()
        self.assertFalse(self.shown(tab))
        self.assertEqual(tab.verification_spin_combo.count(), 0)

    def test_unrelated_auction_spin_is_not_used(self):
        pure = self.auction()
        other = self.auction("weighted_wheel")
        self.event(other, "wheel", wheel_format="standard", spin_index=1)
        tab = self.tab()
        tab._load_details(pure)
        self.assertFalse(self.shown(tab))
        tab._load_details(other)
        self.assertTrue(self.shown(tab))


if __name__ == "__main__":
    unittest.main()
