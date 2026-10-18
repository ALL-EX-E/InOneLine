"""P18-D: retain unsaved Twitch reward drafts and report staged sync failures."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QMessageBox, QSpinBox

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.integrations import (
    IntegrationAdapter,
    IntegrationManager,
    IntegrationOperationResult,
    IntegrationRegistry,
)
from streaming_manager.twitch import TWITCH_MANAGE_SCOPE
from streaming_manager.twitch_b4 import (
    TWITCH_REWARD_COMMON_TITLE_KEY,
    TWITCH_REWARD_DEFINITIONS_KEY,
    TwitchChannelPointsService,
    TwitchRewardDefinition,
)
from streaming_manager.views.settings import SettingsTab


class TwitchFixture(IntegrationAdapter):
    service_key = "twitch"
    display_name = "Twitch"

    def reconnect(self, context):
        return IntegrationOperationResult(
            provider_config={
                **context.provider_config,
                "twitch_user_id": "",
            }
        )


class TwitchDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        paths = AppPaths.from_root(self.temp.name)
        paths.ensure_runtime_dirs()
        self.db = Database(paths.database_path)
        registry = IntegrationRegistry()
        registry.register(TwitchFixture())
        self.manager = IntegrationManager(self.db, registry, retry_delays=())
        self.service = TwitchChannelPointsService(self.db, self.manager)
        self.db.upsert_integration_connection(
            "twitch", enabled=True, status="connected",
            provider_config={
                "twitch_user_id": "",
                "channel_points_custom_rewards_available": True,
                "granted_scopes": [TWITCH_MANAGE_SCOPE],
            },
        )
        self.tab = SettingsTab(
            self.db, paths, LocalApiServer(self.db),
            integration_manager=self.manager,
            twitch_channel_points_service=self.service,
        )
        self.messages = []
        self.patches = [
            patch.object(QMessageBox, "critical", side_effect=lambda *a: self.messages.append(("critical", a[2]))),
            patch.object(QMessageBox, "information", side_effect=lambda *a: self.messages.append(("information", a[2]))),
        ]
        for handle in self.patches:
            handle.start()

    def tearDown(self):
        for handle in reversed(self.patches):
            handle.stop()
        self.tab.thread_pool.waitForDone(5000)
        self.tab.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def finish_action(self):
        for _ in range(500):
            self.app.processEvents()
            if self.tab._integration_worker is None:
                return
            QTest.qWait(10)
        self.fail("Twitch worker did not finish")

    def edit_draft(self):
        self.tab._twitch_common_title.setText("Черновик зрителей")
        self.tab._add_twitch_reward_row()
        table = self.tab._twitch_reward_table
        table.cellWidget(0, 0).setValue(375)
        editor = table.cellWidget(0, 1).findChild(QLineEdit)
        editor.setText("#12AB34")
        return self.tab._collect_twitch_reward_form()

    def test_switch_tabs_preserves_title_cost_color_and_new_row_without_db_write(self):
        expected = self.edit_draft()
        self.tab.settings_tabs.setCurrentWidget(self.tab.conversion_page)
        self.tab.settings_tabs.setCurrentWidget(self.tab.integration_page)
        self.assertEqual(self.tab._collect_twitch_reward_form(), expected)
        self.assertNotEqual(self.db.get_setting(TWITCH_REWARD_COMMON_TITLE_KEY, "Ставка"), expected[0])
        self.assertEqual(self.service.reward_definitions(), [])
        self.assertIsNotNone(self.tab._twitch_reward_unsaved_draft())

    def test_forced_rebuild_preserves_draft_and_revert_clears_dirty(self):
        expected = self.edit_draft()
        self.tab._refresh_integrations()
        self.assertEqual(self.tab._collect_twitch_reward_form(), expected)
        self.tab._twitch_common_title.setText(self.service.common_title())
        self.tab._twitch_reward_table.setRowCount(0)
        self.assertIsNone(self.tab._twitch_reward_unsaved_draft())
        self.tab._refresh_integrations()
        self.assertIsNone(self.tab._twitch_reward_unsaved_draft())

    def test_cancel_reconnect_keeps_unsaved_draft_and_avoids_provider_calls(self):
        expected = self.edit_draft()
        with patch.object(QMessageBox, "warning", return_value=QMessageBox.No) as warn, patch.object(self.manager, "reconnect") as reconnect:
            self.tab._run_integration_action("twitch", "reconnect")
            self.assertEqual(warn.call_count, 1)
            self.assertEqual(reconnect.call_count, 0)
        self.assertEqual(self.tab._collect_twitch_reward_form(), expected)

    def test_confirmed_reconnect_discard_is_explicit(self):
        self.edit_draft()
        with patch.object(QMessageBox, "warning", return_value=QMessageBox.Yes):
            self.tab._run_integration_action("twitch", "reconnect")
            self.finish_action()
        self.assertIsNone(self.tab._twitch_reward_unsaved_draft())
        self.assertEqual(self.tab._twitch_common_title.text(), self.service.common_title())

    def test_invalid_draft_does_not_persist_or_call_provider(self):
        self.tab._twitch_common_title.setText("")
        with patch.object(QMessageBox, "warning", return_value=QMessageBox.Ok) as warn, patch.object(self.service, "ensure_manage_scope") as ensure:
            self.tab._sync_twitch_rewards_from_form()
            self.assertEqual(warn.call_count, 1)
            ensure.assert_not_called()
        self.assertEqual(self.service.common_title(), "Ставка")

    def test_preflight_failure_does_not_stage_local_draft(self):
        expected = self.edit_draft()
        with patch.object(self.service, "ensure_manage_scope", side_effect=RuntimeError("No access")):
            self.tab._sync_twitch_rewards_from_form()
            self.finish_action()
        self.assertEqual(self.service.common_title(), "Ставка")
        self.assertEqual(self.service.reward_definitions(), [])
        self.assertEqual(self.tab._collect_twitch_reward_form(), expected)
        self.assertTrue(any("No access" in body for kind, body in self.messages if kind == "critical"))

    def test_partial_sync_reports_local_save_and_keeps_form_for_retry(self):
        expected = self.edit_draft()
        with patch.object(self.service, "ensure_manage_scope", return_value={}):
            with patch.object(self.service, "sync_rewards", side_effect=RuntimeError("Network interrupted")):
                self.tab._sync_twitch_rewards_from_form()
                self.finish_action()
        self.assertEqual(self.service.common_title(), expected[0])
        self.assertEqual(self.service.reward_definitions(), list(expected[1]))
        self.assertEqual(self.tab._collect_twitch_reward_form(), expected)
        self.assertTrue(any("Настройки наград сохранены в программе" in body and "не завершена" in body for kind, body in self.messages if kind == "critical"))

    def test_success_refreshes_authoritative_registered_reward_ids(self):
        self.edit_draft()
        def synced():
            self.service.save_configuration(
                common_title=self.service.common_title(),
                rewards=[TwitchRewardDefinition(375, "#12AB34", "remote-id-101")],
            )
            return self.service.reward_definitions()
        with patch.object(self.service, "ensure_manage_scope", return_value={}):
            with patch.object(self.service, "sync_rewards", side_effect=synced):
                self.tab._sync_twitch_rewards_from_form()
                self.finish_action()
        _, rewards = self.tab._collect_twitch_reward_form()
        self.assertEqual(len(rewards), 1)
        self.assertEqual(rewards[0].reward_id, "remote-id-101")
        self.assertIsNone(self.tab._twitch_reward_unsaved_draft())
        self.assertTrue(any(kind == "information" and "синхронизированы" in body for kind, body in self.messages))


if __name__ == "__main__":
    unittest.main()
