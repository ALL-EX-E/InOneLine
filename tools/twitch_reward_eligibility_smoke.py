"""P18-C: Twitch Channel Points action eligibility and contextual controls."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.integrations import IntegrationAdapter, IntegrationManager, IntegrationRegistry
from streaming_manager.twitch import TWITCH_MANAGE_SCOPE
from streaming_manager.twitch_b4 import (
    TwitchChannelPointsService,
    TWITCH_REWARD_DEFINITIONS_KEY,
    TWITCH_RETIRED_REWARD_IDS_KEY,
    TWITCH_REWARDS_MANUAL_ENABLED_KEY,
)
from streaming_manager.views.settings import SettingsTab


class TwitchFixture(IntegrationAdapter):
    service_key = "twitch"
    display_name = "Twitch"


class TwitchRewardActionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.temp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        registry = IntegrationRegistry()
        registry.register(TwitchFixture())
        self.manager = IntegrationManager(self.db, registry, retry_delays=())
        self.service = TwitchChannelPointsService(self.db, self.manager)
        self.tab = SettingsTab(
            self.db, self.paths, LocalApiServer(self.db),
            integration_manager=self.manager,
            twitch_channel_points_service=self.service,
        )

    def tearDown(self):
        self.tab.thread_pool.waitForDone(5000)
        self.tab.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def setup_provider(
        self, *, available=True, has_manage_scope=True,
        enabled=True, status="connected", reward_ids=(),
        retired_ids=(), manual=False,
    ):
        self.db.set_settings_bulk({
            TWITCH_REWARD_DEFINITIONS_KEY: json.dumps([
                {"cost": (i + 1) * 100, "color": "#9146FF", "reward_id": rid}
                for i, rid in enumerate(reward_ids)
            ]),
            TWITCH_RETIRED_REWARD_IDS_KEY: json.dumps(list(retired_ids)),
            TWITCH_REWARDS_MANUAL_ENABLED_KEY: "1" if manual else "0",
        })
        self.db.upsert_integration_connection(
            "twitch", status=status, enabled=enabled,
            provider_config={
                "channel_points_custom_rewards_available": available,
                "channel_points_custom_rewards_reason": "Недоступны для этого канала",
                "granted_scopes": [TWITCH_MANAGE_SCOPE] if has_manage_scope else ["channel:read:redemptions"],
                "twitch_user_id": "fixture_1",
            },
        )
        self.tab._refresh_integrations()

    def controls(self):
        card = self.tab.integration_cards_layout.itemAt(0).widget()
        return {b.text(): b for b in card.findChildren(QPushButton)}

    def labels(self):
        card = self.tab.integration_cards_layout.itemAt(0).widget()
        return "\n".join(label.text() for label in card.findChildren(QLabel))

    def test_ready_without_ids_can_sync_but_cannot_toggle_or_delete(self):
        self.setup_provider()
        controls = self.controls()
        self.assertTrue(controls["Добавить награду"].isEnabled())
        self.assertTrue(controls["Сохранить и синхронизировать награды"].isEnabled())
        self.assertFalse(controls["Включить награды"].isEnabled())
        self.assertNotIn("Отключить награды", controls)
        self.assertNotIn("Удалить награды", controls)

    def test_ready_registered_ids_only_correct_manual_action_visible(self):
        self.setup_provider(reward_ids=("reward-1",), manual=False)
        controls = self.controls()
        self.assertTrue(controls["Включить награды"].isEnabled())
        self.assertNotIn("Отключить награды", controls)
        self.assertTrue(controls["Удалить награды"].isEnabled())
        self.setup_provider(reward_ids=("reward-1",), manual=True)
        controls = self.controls()
        self.assertNotIn("Включить награды", controls)
        self.assertTrue(controls["Отключить награды"].isEnabled())
        self.assertTrue(controls["Удалить награды"].isEnabled())

    def test_retired_ids_offer_explicit_delete_but_no_remote_toggle(self):
        self.setup_provider(retired_ids=("retired-1",))
        controls = self.controls()
        self.assertTrue(controls["Удалить награды"].isEnabled())
        self.assertFalse(controls["Включить награды"].isEnabled())

    def test_not_eligible_blocks_remote_actions_even_after_worker_finish(self):
        self.setup_provider(available=False, reward_ids=("reward-1",))
        controls = self.controls()
        self.assertFalse(controls["Сохранить и синхронизировать награды"].isEnabled())
        self.assertFalse(controls["Включить награды"].isEnabled())
        self.assertFalse(controls["Удалить награды"].isEnabled())
        self.assertIn("Недоступны для этого канала", self.labels())
        self.tab._set_integration_actions_enabled(False)
        self.tab._set_integration_actions_enabled(True)
        controls = self.controls()
        for name in ("Сохранить и синхронизировать награды", "Включить награды", "Удалить награды"):
            self.assertFalse(controls[name].isEnabled(), name)

    def test_missing_manage_scope_has_explicit_consent_path(self):
        self.setup_provider(has_manage_scope=False, reward_ids=("reward-1",))
        controls = self.controls()
        self.assertFalse(controls["Сохранить и синхронизировать награды"].isEnabled())
        self.assertFalse(controls["Включить награды"].isEnabled())
        self.assertFalse(controls["Удалить награды"].isEnabled())
        self.assertTrue(controls["Подтвердить права на награды"].isEnabled())
        with patch.object(self.tab, "_run_twitch_b4_action") as run:
            controls["Подтвердить права на награды"].click()
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0], self.service.ensure_manage_scope)

    def test_disconnected_or_disabled_twitch_never_mutates_rewards(self):
        for enabled, status in ((False, "connected"), (True, "error"), (True, "requires_login")):
            with self.subTest(enabled=enabled, status=status):
                self.setup_provider(enabled=enabled, status=status, reward_ids=("reward-1",))
                controls = self.controls()
                self.assertFalse(controls["Сохранить и синхронизировать награды"].isEnabled())
                self.assertFalse(controls["Включить награды"].isEnabled())
                self.assertFalse(controls["Удалить награды"].isEnabled())
                self.assertNotIn("Подтвердить права на награды", controls)
                self.assertTrue(controls["Добавить награду"].isEnabled())


if __name__ == "__main__":
    unittest.main()
