"""P18-B: state-aware provider buttons, explicit safe Enable, and recovery."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.integrations import (
    IntegrationAdapter,
    IntegrationAuthRequired,
    IntegrationManager,
    IntegrationOperationResult,
    IntegrationRegistry,
)
from streaming_manager.views.settings import SettingsTab


class ProviderFixture(IntegrationAdapter):
    service_key = "test_provider"
    display_name = "TestProvider"

    def __init__(self):
        self.failure = None
        self.calls = []

    def connect(self, context):
        self.calls.append("connect")
        return IntegrationOperationResult()

    def reconnect(self, context):
        self.calls.append("reconnect")
        return IntegrationOperationResult()

    def check_connection(self, context):
        self.calls.append("check_connection")
        if self.failure:
            raise self.failure
        return IntegrationOperationResult()


class StateAwareActionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.temp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.provider = ProviderFixture()
        registry = IntegrationRegistry()
        registry.register(self.provider)
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

    def state(self, status, enabled):
        self.db.upsert_integration_connection(
            "test_provider", status=status, enabled=enabled,
            provider_config={"account": "fixture"},
        )
        self.tab._refresh_integrations()

    def buttons(self):
        self.assertEqual(self.tab.integration_cards_layout.count(), 1)
        card = self.tab.integration_cards_layout.itemAt(0).widget()
        self.assertIsNotNone(card)
        return {button.text(): button for button in card.findChildren(QPushButton)}

    def finish_action(self):
        for _ in range(500):
            self.app.processEvents()
            if self.tab._integration_worker is None:
                return
            QTest.qWait(10)
        self.fail("Integration UI operation did not complete")

    def test_unconfigured_has_only_connect(self):
        self.assertEqual(
            set(self.buttons()), {"Подключить TestProvider"},
        )

    def test_connected_actions_hide_connect_and_enable(self):
        self.state("connected", True)
        self.assertEqual(set(self.buttons()), {
            "Проверить соединение", "Переподключить",
            "Отключить", "Удалить подключение",
        })

    def test_disabled_connected_actions_only_enable_and_remove(self):
        self.state("connected", False)
        self.assertEqual(
            set(self.buttons()), {"Включить", "Удалить подключение"},
        )

    def test_disabled_error_allows_enable_or_explicit_reauthorization(self):
        for status in ("error", "requires_login"):
            self.state(status, False)
            self.assertEqual(set(self.buttons()), {
                "Включить", "Переподключить", "Удалить подключение",
            })

    def test_active_error_shows_recovery_not_connect(self):
        for status in ("error", "requires_login"):
            self.state(status, True)
            self.assertEqual(set(self.buttons()), {
                "Проверить соединение", "Переподключить",
                "Отключить", "Удалить подключение",
            })

    def test_enable_uses_saved_health_check_and_preserves_config(self):
        self.state("connected", False)
        self.buttons()["Включить"].click()
        self.finish_action()
        self.assertEqual(self.provider.calls, ["check_connection"])
        row = self.db.get_integration_connection("test_provider")
        self.assertTrue(row["enabled"])
        self.assertEqual(row["provider_config"], {"account": "fixture"})
        self.assertIn("Отключить", self.buttons())
        self.assertNotIn("Включить", self.buttons())

    def test_invalid_credentials_keep_disabled_until_explicit_reconnect(self):
        self.state("connected", False)
        self.provider.failure = IntegrationAuthRequired("requires login")
        self.buttons()["Включить"].click()
        self.finish_action()
        row = self.db.get_integration_connection("test_provider")
        self.assertFalse(row["enabled"])
        self.assertEqual(row["status"], "requires_login")
        self.assertEqual(self.provider.calls, ["check_connection"])
        self.assertIn("Переподключить", self.buttons())
        self.provider.failure = None
        self.buttons()["Переподключить"].click()
        self.finish_action()
        self.assertTrue(self.db.get_integration_connection("test_provider")["enabled"])
        self.assertEqual(self.provider.calls, ["check_connection", "reconnect"])


if __name__ == "__main__":
    unittest.main()
