"""Reproduce DonationAlerts -> SQLite -> Qt view propagation in a disposable DB.

No network calls to DonationAlerts, no credentials, no real money and no
read/write of any user data. Prints a synthetic-only JSON diagnostic.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.views.main_window import MainWindow


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(prefix="InOneLine_DA_Sync_") as folder:
        paths = AppPaths.from_root(folder)
        paths.ensure_runtime_dirs()
        db = Database(paths.database_path)
        db.set_setting("api_port", "0")
        window = MainWindow(db, paths)
        try:
            # Never let the fake connected flag cause any external provider call.
            window.donationalerts_runtime.stop()
            window.twitch_eventsub_runtime.stop()
            window.show()
            window._set_current_main_page(window.public_tab)
            app.processEvents()
            before = window.public_tab.table.rowCount()
            assert before == 0, "expected isolated empty public table"
            db.upsert_integration_connection(
                "donationalerts", enabled=True, status="connected"
            )
            db.set_conversion_rate("RUB", "1")
            title = "IOL DA synthetic UI probe"
            payload = {
                "id": 750000001,
                "amount": "5",
                "currency": "RUB",
                "username": "Synthetic",
                "message": title,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            started = time.monotonic()
            result = window.donationalerts_service.process_donation(payload)
            committed = time.monotonic()
            assert result["status"] == "processed", result["status"]
            row = db.find_game_by_title(title)
            assert row and row.sm_points == 5
            with db.connect() as conn:
                event_count = conn.execute(
                    "SELECT COUNT(*) FROM external_events WHERE source=?",
                    ("donationalerts",)
                ).fetchone()[0]
                contribution_count = conn.execute(
                    "SELECT COUNT(*) FROM contributions WHERE source=?",
                    ("donationalerts",)
                ).fetchone()[0]
            assert event_count == contribution_count == 1
            duplicate = window.donationalerts_service.process_donation(payload)
            assert duplicate["status"] == "duplicate_cursor"
            assert db.get_game(row.id).sm_points == 5

            deadline = time.monotonic() + 1.0
            seen_after_ms = None
            while time.monotonic() < deadline:
                app.processEvents()
                if window.public_tab.table.rowCount() != before:
                    seen_after_ms = round((time.monotonic() - committed) * 1000)
                    break
                time.sleep(0.025)
            before_f5_count = window.public_tab.table.rowCount()
            window.refresh_all()
            app.processEvents()
            after_f5_count = window.public_tab.table.rowCount()
            assert after_f5_count == 1, "F5 failed to refresh synthetic donation"
            report = {
                "schema": "inone-da-synthetic-ui-probe-v1",
                "scope": "isolated_temporary_sqlite_no_provider_network",
                "provider_to_desktop_delivery": "NOT_TESTED",
                "db_transaction": "PASS",
                "db_commit_ms": round((committed-started) * 1000),
                "event_rows": int(event_count),
                "contribution_rows": int(contribution_count),
                "duplicate_credit_prevented": True,
                "visible_public_rows_before": int(before),
                "visible_public_rows_after_1000ms": int(before_f5_count),
                "auto_refresh_ms": seen_after_ms,
                "visible_public_rows_after_F5": int(after_f5_count),
                "ui_auto_refresh": "PASS" if seen_after_ms is not None else "FAIL",
            }
            print(json.dumps(report, ensure_ascii=False, sort_keys=True))
            return 0 if seen_after_ms is not None else 2
        finally:
            window.close()
            app.processEvents()
            window.thread_pool.waitForDone(15000)


if __name__ == "__main__":
    raise SystemExit(main())
