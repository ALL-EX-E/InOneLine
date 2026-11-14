"""Regression: automatic clean-install defaults must not look like user actions."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication

from streaming_manager.api_server import LocalApiServer
from streaming_manager.credentials import MemoryCredentialStore
from streaming_manager.database import Database
from streaming_manager.multichat import MultichatState
from streaming_manager.music_player import MusicPlayerController
from streaming_manager.views.multichat import MultichatTab


class SilentSettingsInitializationSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_missing_defaults_are_silent_and_later_changes_are_audited(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db = Database(
                Path(tmp) / "streaming.db",
                credential_store=MemoryCredentialStore(),
            )

            self.assertEqual(
                db.initialize_settings({"first": "default", "second": "value"}),
                2,
            )
            self.assertEqual(db.get_setting("first"), "default")
            self.assertEqual(db.get_setting("second"), "value")
            self.assertEqual(db.list_log(limit=None), [])

            db.set_setting("first", "changed")
            db.set_setting("first", "changed")
            self.assertEqual(len(db.list_log(limit=None)), 1)

            self.assertEqual(
                db.initialize_settings({"first": "must-not-overwrite", "third": "new"}),
                1,
            )
            self.assertEqual(db.get_setting("first"), "changed")
            self.assertEqual(db.get_setting("third"), "new")
            self.assertEqual(len(db.list_log(limit=None)), 1)

    def test_clean_music_player_construction_is_silent_but_user_change_is_audited(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db = Database(
                Path(tmp) / "streaming.db",
                credential_store=MemoryCredentialStore(),
            )
            player = MusicPlayerController(db, None)
            try:
                self.assertEqual(db.list_log(limit=None), [])
                player.set_volume_percent(75)
                rows = db.list_log(limit=None)
                self.assertEqual(len(rows), 1)
                self.assertIn("music_player_volume", rows[0]["after_json"])
            finally:
                player.shutdown()

    def test_clean_multichat_construction_is_silent_but_user_change_is_audited(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            db = Database(
                Path(tmp) / "streaming.db",
                credential_store=MemoryCredentialStore(),
            )
            tab = MultichatTab(
                db,
                MultichatState(),
                LocalApiServer(db, "127.0.0.1", 0),
            )
            try:
                self.assertEqual(db.list_log(limit=None), [])
                tab.delay.setText("2")
                tab._on_delay()
                rows = db.list_log(limit=None)
                self.assertEqual(len(rows), 1)
                self.assertIn("multichat_delay", rows[0]["after_json"])
            finally:
                tab.refresh_timer.stop()
                tab.close()


if __name__ == "__main__":
    unittest.main()
