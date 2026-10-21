"""P22-B / UI-080: only meaningful date ordering in completed-auction History."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.views.completed_auction_history import CompletedAuctionHistoryTab


class CompletedHistorySortingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.tmp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        # Names deliberately do not correspond to chronological order.
        sessions = (
            ("Аукцион #9", "2026-10-01T10:00:00+00:00", "confirmed"),
            ("Аукцион #10", "2026-10-03T10:00:00+00:00", "cancelled"),
            ("Аукцион #2", "2026-10-02T10:00:00+00:00", "finished_no_winner"),
        )
        with self.db.connect() as conn:
            for name, finished_at, status in sessions:
                conn.execute(
                    "INSERT INTO auction_sessions("
                    "name,mode,provider,created_at,finished_at,status"
                    ") VALUES(?,?,?,?,?,?)",
                    (name, "max_amount", "local", finished_at, finished_at, status),
                )
        # Isolate only the list/header/sorting behavior, not historical details.
        self.details_patch = patch.object(
            CompletedAuctionHistoryTab, "_load_details", return_value=None
        )
        self.details_patch.start()
        self.tab = CompletedAuctionHistoryTab(self.db)

    def tearDown(self):
        self.tab.close()
        self.tab.deleteLater()
        self.app.processEvents()
        self.details_patch.stop()
        self.tmp.cleanup()

    def names(self):
        return [
            self.tab.table.item(i, 1).text()
            for i in range(self.tab.table.rowCount())
        ]

    def test_ui_has_exactly_two_date_orders(self):
        self.assertEqual(
            [(self.tab.sort.itemText(i), self.tab.sort.itemData(i))
             for i in range(self.tab.sort.count())],
            [("Новые → старые", "newest"), ("Старые → новые", "oldest")],
        )
        self.assertEqual(
            self.names(), ["Аукцион #10", "Аукцион #2", "Аукцион #9"]
        )
        self.tab.sort.setCurrentIndex(1)
        self.assertEqual(
            self.names(), ["Аукцион #9", "Аукцион #2", "Аукцион #10"]
        )

    def test_database_chronology_pagination_and_search_remain(self):
        newest = self.db.list_completed_auction_sessions(sort_order="newest")
        oldest = self.db.list_completed_auction_sessions(sort_order="oldest")
        self.assertEqual([x["name"] for x in newest],
                         ["Аукцион #10", "Аукцион #2", "Аукцион #9"])
        self.assertEqual([x["name"] for x in oldest],
                         ["Аукцион #9", "Аукцион #2", "Аукцион #10"])
        first = self.db.list_completed_auction_sessions(limit=2, offset=0)
        last = self.db.list_completed_auction_sessions(limit=2, offset=2)
        self.assertEqual(len(first), 2)
        self.assertEqual([r["name"] for r in last], ["Аукцион #9"])
        filtered = self.db.list_completed_auction_sessions(search_text="#2")
        self.assertEqual([r["name"] for r in filtered], ["Аукцион #2"])

    def test_existing_period_and_summary_controls_survive(self):
        self.assertEqual(self.tab.period.currentData(), "all")
        self.assertEqual(self.tab.table.rowCount(), 3)
        self.tab.search.setText("#2")
        self.tab._search_timer.stop()
        self.tab.refresh()
        self.assertEqual(self.names(), ["Аукцион #2"])
        self.assertIn("1", self.tab.stat_total.text())
        self.assertEqual(self.tab.details_tabs.tabText(0), "Общие")
        self.assertEqual(self.tab.details_tabs.tabText(1), "Лоты")
        self.assertEqual(self.tab.details_tabs.tabText(2), "События")


if __name__ == "__main__":
    unittest.main()
