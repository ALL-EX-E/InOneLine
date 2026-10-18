"""P18-F / UI-084: clear integration copy and shared local-time rendering."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database, display_datetime_local
from streaming_manager.donationalerts import DonationAlertsAdapter
from streaming_manager.integrations import IntegrationManager, IntegrationRegistry
from streaming_manager.twitch import TWITCH_MANAGE_SCOPE, TwitchAdapter
from streaming_manager.views.settings import SettingsTab


TIMESTAMP = "2026-10-06T08:18:36+00:00"
ACTIVITY = "2026-10-06T08:19:42.123456+00:00"


class IntegrationCopyLocalTimeTests(unittest.TestCase):
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
        self.db.upsert_integration_connection(
            "twitch", status="connected", enabled=True,
            last_check_at=TIMESTAMP, last_event_at=ACTIVITY,
            provider_config={
                "display_name": "Test channel", "login": "testchannel",
                "broadcaster_type": "affiliate", "twitch_user_id": "1234",
                "channel_points_custom_rewards_available": True,
                "granted_scopes": [TWITCH_MANAGE_SCOPE],
            },
        )
        self.db.upsert_integration_connection(
            "donationalerts", status="connected", enabled=False,
            last_check_at=TIMESTAMP, last_event_at=ACTIVITY,
            provider_config={"display_name": "Test account", "code": "test",
                             "donationalerts_user_id": "12345"},
        )
        self.tab = SettingsTab(
            self.db, self.paths, LocalApiServer(self.db),
            integration_manager=self.manager,
        )

    def tearDown(self):
        self.tab.thread_pool.waitForDone(5000)
        self.tab.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def card(self, name):
        for i in range(self.tab.integration_cards_layout.count()):
            card = self.tab.integration_cards_layout.itemAt(i).widget()
            if card is None:
                continue
            if any(label.text() == name for label in card.findChildren(QLabel)):
                return card
        self.fail(f"Missing provider card {name}")

    def text(self, name):
        return "\n".join(label.text() for label in self.card(name).findChildren(QLabel))

    def test_twitch_text_is_readable_without_changing_provider_capabilities(self):
        shown = self.text("Twitch")
        self.assertIn("Авторизация через официальный вход Twitch", shown)
        self.assertIn("защищённом хранилище", shown)
        self.assertIn("Права на управление наградами:", shown)
        self.assertIn("Баллы канала и награды Twitch", shown)
        self.assertIn("События Twitch в реальном времени", shown)
        self.assertIn("Тип канала: компаньон", shown)
        for jargon in ("Device Code Grant Flow", "Public client", "Права B4",
                       "OAuth Device Code (Public)", "EventSub WebSocket"):
            self.assertNotIn(jargon, shown)
        self.assertIn("Channel Points / Custom Rewards",
                      TwitchAdapter.capabilities)
        buttons = {button.text() for button in self.card("Twitch").findChildren(QPushButton)}
        self.assertIn("Проверить соединение", buttons)
        self.assertNotIn("Подключить Twitch", buttons)

    def test_donationalerts_uses_protected_storage_explanation_and_local_labels(self):
        shown = self.text("DonationAlerts")
        self.assertIn("официальный вход", shown)
        self.assertIn("защищённом хранилище Windows", shown)
        self.assertIn("ID пользователя DonationAlerts: 12345", shown)
        self.assertIn("События DonationAlerts в реальном времени", shown)
        self.assertIn("История пожертвований", shown)
        self.assertIn("вводить ID вручную не нужно", shown)
        for jargon in ("Centrifugo WebSocket", "DonationAlerts User ID",
                       "CredentialStore", "OAuth Implicit (Public desktop)"):
            self.assertNotIn(jargon, shown)
        self.assertIn("Centrifugo WebSocket", DonationAlertsAdapter.capabilities)
        self.assertIn("Включить", {
            button.text() for button in self.card("DonationAlerts").findChildren(QPushButton)
        })
        self.assertFalse(self.db.get_integration_connection("donationalerts")["enabled"])

    def test_existing_shared_local_formatter_preserves_raw_utc_db(self):
        local_check = display_datetime_local(TIMESTAMP)
        local_event = display_datetime_local(ACTIVITY)
        self.assertEqual(len(local_check), 19)
        for provider in ("Twitch", "DonationAlerts"):
            shown = self.text(provider)
            self.assertIn("Последняя проверка: " + local_check, shown)
            self.assertIn("Последняя принятая активность: " + local_event, shown)
            self.assertNotIn("2026-10-06T", shown)
            row = self.db.get_integration_connection(provider.lower())
            self.assertEqual(row["last_check_at"], TIMESTAMP)
            self.assertEqual(row["last_event_at"], ACTIVITY)

    def test_refresh_changes_no_provider_state_or_timestamp(self):
        before = {key: self.db.get_integration_connection(key)
                  for key in ("twitch", "donationalerts")}
        self.tab._refresh_integrations()
        self.app.processEvents()
        for key, name in (("twitch", "Twitch"), ("donationalerts", "DonationAlerts")):
            self.assertIn("Последняя проверка: ", self.text(name))
            self.assertEqual(before[key], self.db.get_integration_connection(key))


if __name__ == "__main__":
    unittest.main()
