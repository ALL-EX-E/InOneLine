"""P18-G / UI-084: never show an impossible empty-provider placeholder."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.donationalerts import DonationAlertsAdapter
from streaming_manager.integrations import IntegrationManager, IntegrationRegistry
from streaming_manager.twitch import TwitchAdapter
from streaming_manager.views.settings import SettingsTab


class IntegrationEmptyNoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.temp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        registry = IntegrationRegistry()
        registry.register(TwitchAdapter())
        registry.register(DonationAlertsAdapter())
        self.manager = IntegrationManager(self.db, registry, retry_delays=())
        self.tab = SettingsTab(
            self.db, self.paths, LocalApiServer(self.db),
            integration_manager=self.manager,
        )

    def tearDown(self):
        self.tab.thread_pool.waitForDone(5000)
        self.tab.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def provider_cards(self):
        cards = []
        for i in range(self.tab.integration_cards_layout.count()):
            item = self.tab.integration_cards_layout.itemAt(i)
            card = item.widget()
            if card is not None:
                cards.append(card)
        return cards

    def all_labels(self):
        return "\n".join(
            label.text() for label in self.tab.integration_page.findChildren(QLabel)
        )

    def assert_card_names(self):
        cards = self.provider_cards()
        self.assertEqual(len(cards), 2)
        for provider in ("Twitch", "DonationAlerts"):
            self.assertTrue(
                any(provider == label.text()
                    for card in cards
                    for label in card.findChildren(QLabel)),
                provider,
            )

    def test_no_connections_still_show_supported_provider_cards(self):
        self.assertIsNone(self.db.get_integration_connection("twitch"))
        self.assertIsNone(self.db.get_integration_connection("donationalerts"))
        self.assert_card_names()
        self.assertNotIn("Подключённых сервисов пока нет.", self.all_labels())
        self.assertFalse(hasattr(self.tab, "integration_empty_label"))
        button_names = [
            button.text() for card in self.provider_cards()
            for button in card.findChildren(QPushButton)
        ]
        self.assertIn("Подключить Twitch", button_names)
        self.assertIn("Подключить DonationAlerts", button_names)

    def test_disabled_or_connected_states_do_not_create_empty_note(self):
        self.db.upsert_integration_connection(
            "twitch", status="connected", enabled=False,
            provider_config={"login": "test_channel"},
        )
        self.db.upsert_integration_connection(
            "donationalerts", status="requires_login", enabled=True,
            provider_config={"code": "test_channel"},
        )
        before = [self.db.get_integration_connection(key)
                  for key in ("twitch", "donationalerts")]
        self.tab._refresh_integrations()
        self.assert_card_names()
        self.assertNotIn("Подключённых сервисов пока нет.", self.all_labels())
        self.assertIn("Включить", [
            b.text() for card in self.provider_cards()
            for b in card.findChildren(QPushButton)
        ])
        after = [self.db.get_integration_connection(key)
                 for key in ("twitch", "donationalerts")]
        self.assertEqual(before, after)

    def test_navigation_and_refresh_keep_cards_and_no_empty_note(self):
        self.tab.settings_tabs.setCurrentWidget(self.tab.integration_page)
        self.tab.settings_tabs.setCurrentWidget(self.tab.conversion_page)
        self.tab.settings_tabs.setCurrentWidget(self.tab.integration_page)
        self.tab._refresh_integrations()
        self.assert_card_names()
        self.assertNotIn("Подключённых сервисов пока нет.", self.all_labels())


if __name__ == "__main__":
    unittest.main()
