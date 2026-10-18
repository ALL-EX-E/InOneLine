"""P18-A/UI-084: checking provider health never activates a disabled source."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.integrations import (
    IntegrationAdapter,
    IntegrationAuthRequired,
    IntegrationError,
    IntegrationManager,
    IntegrationOperationResult,
    IntegrationRegistry,
    IntegrationTemporaryError,
    NormalizedIntegrationEvent,
    STATUS_CONNECTED,
    STATUS_ERROR,
    STATUS_REQUIRES_LOGIN,
)


class FixtureProvider(IntegrationAdapter):
    service_key = "p18_fixture"
    display_name = "P18 fixture"
    accepted_event_types = frozenset({"fixture_bid"})

    def __init__(self):
        self.next_error = None
        self.calls = []

    def connect(self, context):
        self.calls.append("connect")
        return IntegrationOperationResult(status=STATUS_CONNECTED)

    def reconnect(self, context):
        self.calls.append("reconnect")
        return IntegrationOperationResult(status=STATUS_CONNECTED)

    def check_connection(self, context):
        self.calls.append("check_connection")
        if self.next_error is not None:
            raise self.next_error
        return IntegrationOperationResult(status=STATUS_CONNECTED)


class DiagnosticEnabledTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(ignore_cleanup_errors=True)
        paths = AppPaths.from_root(self.temp.name)
        paths.ensure_runtime_dirs()
        self.db = Database(paths.database_path)
        self.adapter = FixtureProvider()
        registry = IntegrationRegistry()
        registry.register(self.adapter)
        self.manager = IntegrationManager(self.db, registry, retry_delays=())
        self.key = self.adapter.service_key

    def tearDown(self):
        self.temp.cleanup()

    def seed(self, *, enabled=False, status=STATUS_CONNECTED):
        return self.db.upsert_integration_connection(
            self.key,
            enabled=enabled,
            status=status,
            provider_config={"account": "fixture", "capability": "incoming"},
        )

    def assert_disabled_and_intact(self, status):
        row = self.db.get_integration_connection(self.key)
        self.assertFalse(row["enabled"], row)
        self.assertEqual(row["status"], status)
        self.assertEqual(row["provider_config"], {
            "account": "fixture", "capability": "incoming",
        })
        # A diagnostic can update status/time, but never event intake gating.
        self.assertEqual(self.manager.views()[0].enabled, False)
        with self.assertRaises(IntegrationError):
            self.manager.accept_normalized_event(NormalizedIntegrationEvent(
                service_key=self.key, external_event_id="do-not-intake",
                event_type="fixture_bid", source_amount="1", source_unit="RUB",
                contributor="tester",
            ))
        self.assertFalse(self.db.get_integration_connection(self.key)["enabled"])

    def test_successful_check_does_not_reenable_disabled_source(self):
        before = self.seed()
        checked = self.manager.check_connection(self.key)
        self.assertEqual(checked["last_event_at"], before["last_event_at"])
        self.assertTrue(checked["last_check_at"])
        self.assert_disabled_and_intact(STATUS_CONNECTED)
        self.assertEqual(self.adapter.calls, ["check_connection"])

    def test_auth_failure_does_not_reenable_disabled_source(self):
        self.seed()
        self.adapter.next_error = IntegrationAuthRequired("login needed")
        checked = self.manager.check_connection(self.key)
        self.assertEqual(checked["status"], STATUS_REQUIRES_LOGIN)
        self.assert_disabled_and_intact(STATUS_REQUIRES_LOGIN)
        # Enabling needs an explicit Connect or Reconnect operation.
        self.adapter.next_error = None
        activated = self.manager.reconnect(self.key)
        self.assertTrue(activated["enabled"])
        self.assertEqual(activated["status"], STATUS_CONNECTED)

    def test_temporary_and_other_errors_do_not_reenable_disabled_source(self):
        for error in (IntegrationTemporaryError("network error"), ValueError("bad reply")):
            self.seed()
            self.adapter.next_error = error
            checked = self.manager.check_connection(self.key)
            self.assertEqual(checked["status"], STATUS_ERROR)
            self.assert_disabled_and_intact(STATUS_ERROR)
            self.assertTrue(checked["last_error"])

    def test_active_source_stays_enabled_through_diagnostics(self):
        self.seed(enabled=True)
        self.assertTrue(self.manager.check_connection(self.key)["enabled"])
        self.adapter.next_error = IntegrationTemporaryError("network error")
        checked = self.manager.check_connection(self.key)
        self.assertTrue(checked["enabled"])
        self.assertEqual(checked["status"], STATUS_ERROR)

    def test_check_without_config_does_not_silently_activate_source(self):
        self.assertIsNone(self.db.get_integration_connection(self.key))
        checked = self.manager.check_connection(self.key)
        self.assertFalse(checked["enabled"])
        self.assertEqual(checked["status"], STATUS_CONNECTED)
        self.assertEqual(self.adapter.calls, ["check_connection"])
        # User explicit Connect can activate the provider later.
        self.assertTrue(self.manager.connect(self.key)["enabled"])

    def test_explicit_connect_still_enables_disabled_source(self):
        self.seed(enabled=False)
        activated = self.manager.connect(self.key)
        self.assertTrue(activated["enabled"])
        self.assertEqual(activated["status"], STATUS_CONNECTED)


if __name__ == "__main__":
    unittest.main()
