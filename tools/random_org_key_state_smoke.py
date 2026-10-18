"""P18-E: Random.org API key editor distinguishes stored vs unsaved candidate."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.views.settings import SettingsTab


class RandomOrgKeyStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.paths = AppPaths.from_root(self.temp.name)
        self.paths.ensure_runtime_dirs()
        self.db = Database(self.paths.database_path)
        self.key_change_notices = []
        self.tab = SettingsTab(
            self.db, self.paths, LocalApiServer(self.db),
            random_org_key_changed=lambda: self.key_change_notices.append("changed"),
        )
        self.notices = []
        self.patch_info = patch.object(
            QMessageBox, "information",
            side_effect=lambda *args: self.notices.append(("information", str(args[2]))),
        )
        self.patch_error = patch.object(
            QMessageBox, "critical",
            side_effect=lambda *args: self.notices.append(("critical", str(args[2]))),
        )
        self.patch_info.start()
        self.patch_error.start()

    def tearDown(self):
        self.tab.thread_pool.waitForDone(5000)
        self.patch_error.stop()
        self.patch_info.stop()
        self.tab.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def finish(self):
        for _ in range(500):
            self.app.processEvents()
            if self.tab._rng_worker is None:
                return
            QTest.qWait(10)
        self.fail("Random.org API test worker did not finish")

    def verify(self, usage=None):
        with patch("streaming_manager.views.settings.RandomOrgClient") as client:
            client.return_value.get_usage.return_value = usage or {
                "requestsLeft": 19, "bitsLeft": 580
            }
            self.tab.check_random_org_api()
            self.finish()
            client.assert_called_once()

    def test_unsaved_key_is_tested_without_persisting_or_notifying_auction(self):
        self.tab.random_org_key.setText("candidate-not-saved")
        self.assertIn("не сохранён", self.tab.random_org_status.text())
        self.verify()
        self.assertEqual(self.db.get_random_org_api_key(), "")
        self.assertEqual(self.key_change_notices, [])
        self.assertIn("Ключ ещё не сохранён", self.tab.random_org_status.text())
        self.assertIn("Запросов осталось: 19", self.tab.random_org_status.text())
        self.assertIn("битов осталось: 580", self.tab.random_org_status.text())
        self.assertNotIn("candidate-not-saved", self.tab.random_org_status.text())

    def test_explicit_save_then_test_recognizes_saved_key(self):
        self.tab.random_org_key.setText("saved-candidate")
        self.tab.save_random_org_key()
        self.assertEqual(self.db.get_random_org_api_key(), "saved-candidate")
        self.assertEqual(self.key_change_notices, ["changed"])
        self.verify()
        self.assertIn("Ключ сохранён", self.tab.random_org_status.text())
        self.assertNotIn("Ключ ещё не сохранён", self.tab.random_org_status.text())
        self.assertEqual(self.key_change_notices, ["changed"])

    def test_testing_different_key_does_not_replace_saved_credential(self):
        self.db.set_random_org_api_key("real-saved")
        self.tab.random_org_key.setText("new-unsaved")
        self.verify({"requestsLeft": 7, "bitsLeft": 31})
        self.assertEqual(self.db.get_random_org_api_key(), "real-saved")
        self.assertIn("Ключ ещё не сохранён", self.tab.random_org_status.text())
        self.assertEqual(self.key_change_notices, [])

    def test_edit_during_inflight_check_does_not_claim_current_key_was_tested(self):
        release = Event()
        entered = Event()

        def slow_usage():
            entered.set()
            if not release.wait(5):
                raise RuntimeError("fixture not released")
            return {"requestsLeft": 2, "bitsLeft": 16}

        self.db.set_random_org_api_key("saved-before")
        self.tab.random_org_key.setText("saved-before")
        with patch("streaming_manager.views.settings.RandomOrgClient") as client:
            client.return_value.get_usage.side_effect = slow_usage
            self.tab.check_random_org_api()
            self.assertTrue(entered.wait(5))
            self.tab.random_org_key.setText("changed-during-check")
            release.set()
            self.finish()
        self.assertEqual(self.db.get_random_org_api_key(), "saved-before")
        self.assertIn("поле изменилось", self.tab.random_org_status.text())
        self.assertIn("Проверьте текущий ключ отдельно", self.tab.random_org_status.text())
        self.assertNotIn("changed-during-check", self.tab.random_org_status.text())

    def test_error_does_not_persist_key(self):
        self.tab.random_org_key.setText("unsaved-error")
        with patch("streaming_manager.views.settings.RandomOrgClient") as client:
            client.return_value.get_usage.side_effect = RuntimeError("API temporarily unavailable")
            self.tab.check_random_org_api()
            self.finish()
        self.assertIn("ошибка проверки", self.tab.random_org_status.text())
        self.assertEqual(self.db.get_random_org_api_key(), "")
        self.assertEqual(self.key_change_notices, [])
        self.assertTrue(any(k == "critical" for k, _ in self.notices))

    def test_clear_requires_explicit_save_to_delete_credential(self):
        self.db.set_random_org_api_key("original")
        self.tab.random_org_key.setText("original")
        self.tab.random_org_key.clear()
        self.assertEqual(self.db.get_random_org_api_key(), "original")
        self.assertIn("не сохранён", self.tab.random_org_status.text())
        self.tab.save_random_org_key()
        self.assertEqual(self.db.get_random_org_api_key(), "")
        self.assertEqual(self.key_change_notices, ["changed"])
        self.assertIn("ключ очищен", self.tab.random_org_status.text())


if __name__ == "__main__":
    unittest.main()
