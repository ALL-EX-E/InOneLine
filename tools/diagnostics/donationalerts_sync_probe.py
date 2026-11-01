"""Reproduce DonationAlerts -> SQLite -> Qt view propagation in a disposable DB.

No network calls to DonationAlerts, no credentials, no real money and no
read/write of any user data. Prints a synthetic-only JSON diagnostic.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
import threading
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
            # Exercise a real Python background thread, as Centrifugo does.
            started = time.monotonic()
            outcome = {}
            def apply_in_background():
                try:
                    outcome["result"] = window.donationalerts_service.process_donation(payload)
                    outcome["committed"] = time.monotonic()
                except Exception as exc:
                    outcome["error"] = exc
            thread = threading.Thread(target=apply_in_background, name="SyntheticDonationPush")
            thread.start()
            thread.join(timeout=8)
            assert not thread.is_alive(), "Donation service blocked background thread"
            if "error" in outcome:
                raise outcome["error"]
            result, committed = outcome["result"], outcome["committed"]
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
            # In the corrected implementation, all hidden tabs are marked
            # dirty; opening them must catch up without F5.
            window._set_current_main_page(window.games_tab)
            app.processEvents()
            games_after_switch = window.games_tab.table.rowCount()
            window._set_current_main_page(window.log_tab)
            end_log = time.monotonic() + 5.0
            log_found = False
            while time.monotonic() < end_log:
                app.processEvents()
                log_found = any(
                    "Интеграция" in str(item)
                    for row in window.log_tab.model._rows for item in row
                )
                if log_found:
                    break
                time.sleep(0.02)
            window._set_current_main_page(window.completed_history_tab)
            app.processEvents()
            completed_history_rows = window.completed_history_tab.table.rowCount()
            assert completed_history_rows == 0, (
                "outside-auction donation incorrectly created completed auction history"
            )
            after_f5_count = None
            if before_f5_count != 1:
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
                "visible_public_rows_after_F5": after_f5_count,
                "hidden_list_rows_after_open": int(games_after_switch),
                "log_event_visible_after_open": log_found,
                "completed_history_rows_outside_auction": completed_history_rows,
                "ui_auto_refresh": (
                    "PASS" if seen_after_ms is not None and games_after_switch == 1 and log_found
                    else "FAIL"
                ),
            }
            print(json.dumps(report, ensure_ascii=False, sort_keys=True))
            return 0 if report["ui_auto_refresh"] == "PASS" else 2
        finally:
            window.close()
            app.processEvents()
            window.thread_pool.waitForDone(15000)


if __name__ == "__main__":
    raise SystemExit(main())
