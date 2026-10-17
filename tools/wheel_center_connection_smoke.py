"""P15-G: real persisted center selection and built-in icon perimeter regression."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from streaming_manager.api_server import LocalApiServer
from streaming_manager.app_paths import AppPaths
from streaming_manager.constants import WHEEL_CENTER_IMAGE_MEDIA_ID_KEY as CENTER_KEY
from streaming_manager.database import Database
from streaming_manager.default_wheel_icon import (
    bundled_icon_path, default_wheel_icon_png, fill_default_icon_corners,
)
from streaming_manager.integrations import (
    IntegrationAdapter, IntegrationManager, IntegrationOperationResult, IntegrationRegistry,
)
from streaming_manager.remote_image import RemoteImageResult
from streaming_manager.twitch import TwitchAdapter, TwitchCredential
from streaming_manager.views.settings import SettingsTab
from streaming_manager.wheel_center_media import prepare_local_center_image, store_prepared_center_image


class ProviderFixture(IntegrationAdapter):
    service_key = "twitch"
    display_name = "Twitch"
    user_id = "100"
    image_url = "https://static-cdn.jtvnw.net/avatar.png"

    def connect(self, context):
        return IntegrationOperationResult(provider_config={
            "twitch_user_id": self.user_id, "login": "fixture_channel",
            "profile_image_url": self.image_url,
        })

    check_connection = connect


class CenterConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        paths = AppPaths.from_root(self.temp.name)
        paths.ensure_runtime_dirs()
        self.db = Database(paths.database_path)
        self.provider = ProviderFixture()
        registry = IntegrationRegistry()
        registry.register(self.provider)
        self.manager = IntegrationManager(self.db, registry, retry_delays=())
        self.tab = SettingsTab(self.db, paths, LocalApiServer(self.db), integration_manager=self.manager)
        self.notices = []
        self.notice_patch = patch.object(QMessageBox, "information", side_effect=lambda *a: self.notices.append(a))
        self.notice_patch.start()
        self.addCleanup(self.notice_patch.stop)
        self.selected_signals = []
        self.tab.wheelCenterChanged.connect(self.selected_signals.append)

    def tearDown(self):
        self.tab.thread_pool.waitForDone(5000)
        self.tab.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def action(self, name):
        self.tab._run_integration_action("twitch", name)
        self.finish_action()

    def finish_action(self):
        for _ in range(500):
            self.app.processEvents()
            if self.tab._integration_worker is None:
                return
            QTest.qWait(10)
        self.fail("Integration worker did not finish")

    def download(self, source, **kwargs):
        return RemoteImageResult(default_wheel_icon_png(), ".png", False, "Twitch avatar", source)

    def select_manual(self):
        image = QImage(16, 16, QImage.Format.Format_ARGB32)
        image.fill(QColor("#1234FF"))
        path = str(Path(self.temp.name) / "manual.png")
        image.save(path)
        asset = store_prepared_center_image(self.db, prepare_local_center_image(path))
        self.db.set_setting(CENTER_KEY, str(asset.id))
        self.tab._refresh_wheel_center_image_library()
        return str(asset.id)

    def test_new_connection_selects_avatar_status_check_and_disconnect_preserve_manual(self):
        with patch("streaming_manager.wheel_center_media.download_external_image", side_effect=self.download):
            self.action("connect")
        chosen = self.db.get_setting(CENTER_KEY, "")
        self.assertTrue(chosen, "New Twitch connection did not persist its avatar")
        self.assertTrue(self.db.get_media_asset(int(chosen)))
        self.assertEqual(self.selected_signals, [int(chosen)])
        self.assertEqual(self.db.current_wheel_payload()["center_image"]["asset_id"], int(chosen))
        manual = self.select_manual()
        with patch("streaming_manager.wheel_center_media.download_external_image", side_effect=AssertionError("unexpected download")) as download:
            self.action("check_connection")
            self.action("connect")
            self.action("reconnect")
            self.action("disconnect")
        download.assert_not_called()
        self.assertEqual(self.db.get_setting(CENTER_KEY, ""), manual)
        self.assertTrue(self.db.get_media_asset(int(manual)))
        self.assertEqual(Database(self.db.path).get_setting(CENTER_KEY, ""), manual)

    def test_same_account_recovery_does_not_overwrite_manual_image(self):
        self.manager.connect("twitch")
        manual = self.select_manual()
        for status in ("error", "requires_login"):
            self.db.upsert_integration_connection("twitch", status=status)
            with patch("streaming_manager.wheel_center_media.download_external_image", side_effect=self.download):
                self.action("reconnect")
            self.assertEqual(self.db.get_setting(CENTER_KEY, ""), manual, status)

    def test_manual_choice_returning_to_original_value_wins_slow_download(self):
        manual = self.select_manual()
        self.db.set_setting(CENTER_KEY, "")
        self.tab._refresh_wheel_center_image_library()
        entered, release = Event(), Event()

        def download(source, **kwargs):
            entered.set()
            if not release.wait(5):
                raise TimeoutError("fixture did not release avatar download")
            return self.download(source, **kwargs)

        with patch("streaming_manager.wheel_center_media.download_external_image", side_effect=download):
            self.tab._run_integration_action("twitch", "connect")
            try:
                for _ in range(100):
                    if entered.is_set():
                        break
                    QTest.qWait(10)
                self.assertTrue(entered.is_set())
                self.tab.wheel_center_image_combo.setCurrentIndex(
                    self.tab.wheel_center_image_combo.findData(int(manual))
                )
                self.tab.wheel_center_image_combo.setCurrentIndex(0)
                self.assertEqual(self.db.get_setting(CENTER_KEY, ""), "")
            finally:
                release.set()
            self.finish_action()
        self.assertEqual(self.db.get_setting(CENTER_KEY, ""), "", "Slow avatar replaced explicit return to default")

    def test_account_change_and_reenable_select_avatar(self):
        self.manager.connect("twitch")
        self.provider.user_id = "200"
        with patch("streaming_manager.wheel_center_media.download_external_image", side_effect=self.download):
            self.action("reconnect")
        self.assertTrue(self.db.get_setting(CENTER_KEY, ""), "Account change did not select avatar")
        self.action("disconnect")
        self.db.set_setting(CENTER_KEY, "")
        with patch("streaming_manager.wheel_center_media.download_external_image", side_effect=self.download):
            self.action("connect")
        self.assertTrue(self.db.get_setting(CENTER_KEY, ""), "Reenabled connection did not select avatar")

    def test_avatar_failure_does_not_fail_connection_or_replace_manual_choice(self):
        manual = self.select_manual()
        with patch("streaming_manager.wheel_center_media.download_external_image", side_effect=ValueError("download unavailable")):
            self.action("connect")
        self.assertEqual(self.db.get_integration_connection("twitch")["status"], "connected")
        self.assertEqual(self.db.get_setting(CENTER_KEY, ""), manual)
        self.assertTrue(self.notices, "Avatar failure must have a nonblocking explanation")

    def test_manual_choice_during_download_wins(self):
        def download(source, **kwargs):
            # A manual picker may save while the network worker is active.
            self.db.set_setting(CENTER_KEY, "12345")
            return self.download(source, **kwargs)
        with patch("streaming_manager.wheel_center_media.download_external_image", side_effect=download):
            self.action("connect")
        self.assertEqual(self.db.get_setting(CENTER_KEY, ""), "12345")
        self.assertEqual(self.selected_signals, [])

    def test_authorized_profile_payload_retains_avatar_even_without_channel_points(self):
        class Client:
            def get_current_user(self, client_id, access):
                return {"data": [{"id": "100", "login": "fixture", "profile_image_url": "https://static-cdn.jtvnw.net/avatar.png"}]}

            def get_custom_rewards(self, *args):
                from streaming_manager.twitch import TwitchHttpError
                raise TwitchHttpError(403, "not eligible")

        result = TwitchAdapter(client=Client())._profile_and_capability(
            self.manager._context("twitch"), "public-client",
            TwitchCredential("fixture-access", "fixture-refresh", 0, ()), {},
        )
        self.assertEqual(result.status, "connected")
        self.assertEqual(result.provider_config.get("profile_image_url"), "https://static-cdn.jtvnw.net/avatar.png")

    def test_icon_removes_horizontal_and_vertical_fringe_without_changing_symbol(self):
        image = QImage(100, 100, QImage.Format.Format_ARGB32)
        image.fill(QColor("black"))
        for y in range(15, 85):
            for x in range(15, 85):
                image.setPixelColor(x, y, QColor("#34E415"))
        # Dark fringe embedded between green pixels defeats a row-only scan.
        for x in range(30, 70):
            image.setPixelColor(x, 15, QColor("#1f710e"))
        for y in range(30, 70):
            image.setPixelColor(15, y, QColor("#1f710e"))
        image.setPixelColor(50, 50, QColor("black"))
        fixed = fill_default_icon_corners(image)
        self.assertEqual(fixed.size(), image.size())
        for x, y in [(15, 50), (50, 15), (0, 0)]:
            self.assertEqual(fixed.pixelColor(x, y).name().upper(), "#34E415", f"Fringe left at {x},{y}")
        self.assertEqual(fixed.pixelColor(50, 50).name(), "#000000")
        source = QImage(str(bundled_icon_path()))
        real = fill_default_icon_corners(source)
        self.assertGreater(real.pixelColor(627, 1156).green(), 200, "Bundled bottom seam remains")
        self.assertGreater(real.pixelColor(98, 627).green(), 200, "Bundled left seam remains")
        self.assertEqual(real.pixelColor(627, 600), source.pixelColor(627, 600), "Inner symbol changed")
        self.assertEqual(
            real.copy(280, 135, 694, 995),
            source.convertToFormat(real.format()).copy(280, 135, 694, 995),
            "Interior symbol region changed",
        )


if __name__ == "__main__":
    unittest.main()
