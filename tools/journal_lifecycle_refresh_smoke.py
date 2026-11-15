"""Regression: Journal refreshes on visit and records explicit connections."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streaming_manager.credentials import MemoryCredentialStore
from streaming_manager.database import Database
from streaming_manager.integrations import (
    IntegrationAdapter,
    IntegrationManager,
    IntegrationOperationResult,
    IntegrationRegistry,
    STATUS_CONNECTED,
)
from streaming_manager.views.main_window import MainWindow


class _FixtureAdapter(IntegrationAdapter):
    service_key = "twitch"
    display_name = "Twitch"

    def connect(self, _context):
        return IntegrationOperationResult(
            status=STATUS_CONNECTED,
            provider_config={"display_name": "JournalTester", "login": "journal_tester"},
        )

    def check_connection(self, _context):
        return IntegrationOperationResult(status=STATUS_CONNECTED)


class _Page:
    def __init__(self):
        self.refresh_count = 0

    def refresh(self):
        self.refresh_count += 1


class _AuctionPage(_Page):
    def set_main_tab_visible(self, _visible, *, refresh_pending=False):
        return False


class _Tabs:
    def __init__(self, page):
        self.page = page

    def count(self):
        return 1

    def widget(self, _index):
        return self.page

    def setFocus(self, _reason):
        pass


class JournalLifecycleRefreshSmoke(unittest.TestCase):
    def test_journal_refreshes_every_time_it_is_opened(self):
        journal = _Page()
        window = SimpleNamespace(
            tabs=_Tabs(journal),
            _main_tab_page_by_scroll={journal: journal},
            _dirty_tabs=set(),
            auction_tab=_AuctionPage(),
            stream_tab=_Page(),
            music_tab=_Page(),
            log_tab=journal,
            _responsive_layout_settle_timer=SimpleNamespace(start=lambda: None),
            _queue_responsive_layout_update=lambda: None,
        )
        with patch("streaming_manager.views.main_window.QTimer.singleShot"):
            MainWindow._handle_tab_changed(window, 0)
        self.assertEqual(journal.refresh_count, 1)

    def test_explicit_twitch_connection_is_audited_without_credentials(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db = Database(
                Path(tmp) / "streaming.db",
                credential_store=MemoryCredentialStore(),
            )
            registry = IntegrationRegistry()
            registry.register(_FixtureAdapter())
            manager = IntegrationManager(db, registry, retry_delays=())

            connected = manager.connect("twitch")
            self.assertEqual(connected["status"], STATUS_CONNECTED)
            rows = db.list_log(limit=None)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["entity_type"], "integration_connection")
            self.assertEqual(rows[0]["action"], "connect")
            rendered = "\n".join(
                str(rows[0][field] or "") for field in ("before_json", "after_json")
            ).casefold()
            self.assertIn("journaltester", rendered.replace(" ", ""))
            for secret_word in ("credential", "token", "secret", "password"):
                self.assertNotIn(secret_word, rendered)


if __name__ == "__main__":
    unittest.main()
