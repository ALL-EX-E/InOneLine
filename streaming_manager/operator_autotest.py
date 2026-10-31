"""Opt-in, frozen-safe, offline operator smoke tests.

This module never opens the installed AppPaths database. All mutations use a
new TemporaryDirectory. No Twitch/DonationAlerts request is performed.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def run_sandbox(output_file: str) -> int:
    """Run genuine provider-to-DB fixtures and Qt tab navigation in isolation."""
    from .app_paths import AppPaths
    from .database import Database, Game
    from .donationalerts import DonationAlertsAdapter
    from .donationalerts_runtime import DonationAlertsDonationService, DonationAlertsRuntime
    from .integrations import IntegrationManager, IntegrationRegistry

    results: list[dict] = []

    def check(name: str, fn) -> None:
        started = time.monotonic()
        try:
            fn()
            status, error_type = "PASS", ""
        except Exception as exc:
            status, error_type = "FAIL", type(exc).__name__
        results.append({
            "name": name, "status": status, "duration_ms": int((time.monotonic()-started)*1000),
            "error_type": error_type,
        })

    # Private test data only; no canonical installed program data paths.
    with tempfile.TemporaryDirectory(prefix="InOneLine_AutoTest_SANDBOX_") as folder:
        paths = AppPaths.from_root(folder)
        paths.ensure_runtime_dirs()
        db = Database(paths.database_path)
        registry = IntegrationRegistry()
        registry.register(DonationAlertsAdapter())
        manager = IntegrationManager(db, registry, retry_delays=())
        db.upsert_integration_connection("donationalerts", enabled=True, status="connected")
        db.set_conversion_rate("RUB", "2")
        db.set_conversion_rate("EUR", "3")
        title = "IOL AUTOTEST LOT"
        game_id = db.add_game(Game(None, title, None, 0, 0, "not_played", ""))
        service = DonationAlertsDonationService(db, manager)
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "id": 730000001, "amount": "10", "currency": "RUB",
            "username": "Synthetic", "message": title, "created_at": now,
        }

        def points() -> int:
            with db.connect() as conn:
                row = conn.execute("SELECT sm_points FROM games WHERE id=?", (game_id,)).fetchone()
            return int(row["sm_points"])

        def same_title_donation():
            event = DonationAlertsRuntime._extract_donation(
                {"result": {"data": {"data": dict(payload)}}}
            )
            assert event and event["id"] == payload["id"]
            result = service.process_donation(event)
            assert result["status"] == "processed", result["status"]
            assert result["credited_sm_points"] == 20, "10 RUB x 2"
            assert points() == 20, "existing lot points"
            assert service.last_seen_id() == payload["id"], "cursor advanced"

        check("sandbox_donationalerts_rub_and_websocket_payload", same_title_donation)

        def duplicate_event():
            before = points()
            result = service.process_donation(dict(payload))
            assert result["status"] == "duplicate_cursor"
            assert points() == before

        check("sandbox_donationalerts_duplicate_cursor", duplicate_event)

        def eur_conversion():
            event = dict(payload, id=730000002, amount="2", currency="EUR")
            result = service.process_donation(event)
            assert result["status"] == "processed"
            assert result["credited_sm_points"] == 6, "2 EUR x 3"
            assert points() == 26

        check("sandbox_donationalerts_eur_conversion", eur_conversion)

        def rejected_payloads():
            for change in (
                {"id": 0}, {"amount": "-1"}, {"amount": "Infinity"},
                {"currency": "INVALID"}, {"currency": "12"},
            ):
                invalid = dict(payload, **change)
                try:
                    service._normalize_donation(invalid)
                except ValueError:
                    pass
                else:
                    raise AssertionError("invalid donation accepted")
            assert points() == 26

        check("sandbox_donationalerts_invalid_fields_rejected", rejected_payloads)

        def audit_and_isolation():
            assert paths.database_path.is_file()
            assert paths.database_path.resolve().is_relative_to(Path(folder).resolve())
            with db.connect() as conn:
                count = conn.execute(
                    "SELECT COUNT(*) AS n FROM external_events WHERE source='donationalerts'"
                ).fetchone()["n"]
            assert int(count) == 2, "deduplicated event history"

        check("sandbox_donation_history_and_isolated_data", audit_and_isolation)

    # A second clean sandbox: instantiated MainWindow uses only its own temp
    # SQLite. Port 0 asks Windows to allocate a sandbox-only local HTTP port.
    def navigate_tabs():
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from .windows_long_path import prepare_frozen_qt_plugins_for_long_path
        prepare_frozen_qt_plugins_for_long_path()
        from PySide6.QtWidgets import QApplication
        from .views.main_window import MainWindow
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory(prefix="InOneLine_AutoTest_QT_") as folder:
            paths = AppPaths.from_root(folder)
            paths.ensure_runtime_dirs()
            db = Database(paths.database_path)
            db.set_setting("api_port", "0")
            window = MainWindow(db, paths)
            try:
                pages = dict(window._main_tab_pages)
                expected = {
                    "list", "public", "music", "auction",
                    "multichat", "auction_history", "log", "stream", "settings",
                }
                assert expected.issubset(pages), "missing main tabs"
                window.show()
                app.processEvents()
                for key in sorted(expected):
                    page = pages[key]
                    window._set_current_main_page(page)
                    app.processEvents()
                    assert window._current_main_page() is page, "tab navigation failed"
                # AUTO-TEST-002A: real GamesTab actions through the visible UI
                # and actual GameDialog validation, never the user's database.
                from PySide6.QtWidgets import QDialog, QMessageBox
                from .views.games import GameDialog

                tab = window.games_tab
                test_title = "IOL Test List A"
                edited_title = "IOL Test List Edited"
                record_id = None

                def use_dialog(**values):
                    # The QDialog.exec() modal event loop is replaced ONLY in
                    # this sandbox process. The original validator, payload,
                    # button callback and database code still run unmodified.
                    original_exec = GameDialog.exec

                    def automated_exec(dialog):
                        if "title" in values:
                            dialog.title_edit.setText(values["title"])
                        if "amount" in values:
                            dialog.amount_edit.setValue(values["amount"])
                        if "review" in values:
                            dialog.review_edit.setPlainText(values["review"])
                        if "date" in values:
                            dialog.date_edit.setText(values["date"])
                        dialog._ask_yes_no = lambda *args, **kwargs: True
                        dialog._validate_and_accept()
                        return dialog.result()

                    GameDialog.exec = automated_exec
                    return original_exec

                def create_list_record():
                    nonlocal record_id
                    window._set_current_main_page(tab)
                    original = use_dialog(
                        title=test_title, amount=123, date="26.01.2010"
                    )
                    try:
                        assert tab.add_btn.isEnabled(), "add button disabled"
                        tab.add_btn.click()
                    finally:
                        GameDialog.exec = original
                    saved = db.find_game_by_title(test_title)
                    assert saved is not None, "record absent after Add"
                    record_id = saved.id
                    assert saved.sm_points == 123
                    assert tab.table.rowCount() == 1
                    assert tab.table.item(0, 2).text() == test_title

                check("sandbox_list_add_dialog_and_persist", create_list_record)

                def list_search_and_selection():
                    assert record_id is not None, "Add test did not succeed"
                    window._set_current_main_page(tab)
                    tab.search.setText(test_title)
                    app.processEvents()
                    assert tab.table.rowCount() == 1, "exact search count"
                    tab.activate_search()
                    assert tab.selected_game_id() == record_id
                    tab.search.setText("IOL_NOT_FOUND_98765")
                    app.processEvents()
                    assert tab.table.rowCount() == 0, "not-found query leaked rows"
                    tab.search.clear()
                    app.processEvents()
                    assert tab.table.rowCount() == 1, "clear search did not restore rows"

                check("sandbox_list_search_select_and_not_found", list_search_and_selection)

                def edit_list_record():
                    assert record_id is not None, "Add test did not succeed"
                    window._set_current_main_page(tab)
                    tab.focus_game(record_id)
                    assert tab.selected_game_id() == record_id
                    original = use_dialog(
                        title=edited_title, amount=456, review="Synthetic review"
                    )
                    try:
                        assert tab.edit_btn.isEnabled(), "edit button disabled"
                        tab.edit_btn.click()
                    finally:
                        GameDialog.exec = original
                    saved = db.get_game(record_id)
                    assert saved.title == edited_title, "edit title not persisted"
                    assert saved.sm_points == 456, "edit amount not persisted"
                    assert saved.review == "Synthetic review"
                    assert db.find_game_by_title(test_title) is None
                    assert db.count_all_games() == 1

                check("sandbox_list_edit_dialog_and_persist", edit_list_record)

                def archive_restore_record():
                    assert record_id is not None, "Add test did not succeed"
                    window._set_current_main_page(tab)
                    tab.focus_game(record_id)
                    original_question = QMessageBox.question
                    try:
                        QMessageBox.question = staticmethod(
                            lambda *args, **kwargs: QMessageBox.Yes
                        )
                        tab.archive_selected(True)
                    finally:
                        QMessageBox.question = original_question
                    assert db.get_game(record_id).archived == 1
                    tab.apply_stat_filter("archive")
                    assert tab.table.rowCount() == 1
                    assert tab._select_game_row(record_id)
                    tab.archive_selected(False)
                    assert db.get_game(record_id).archived == 0
                    tab.apply_stat_filter("all")
                    assert tab.table.rowCount() == 1

                check("sandbox_list_archive_filter_and_restore", archive_restore_record)

                def duplicate_title_rejected():
                    assert record_id is not None, "Add test did not succeed"
                    window._set_current_main_page(tab)
                    original = use_dialog(title=edited_title, amount=999)
                    # The expected duplicate warning is a modal QMessageBox.
                    # Record that it was shown, without blocking headless CI.
                    original_warning = QMessageBox.warning
                    warnings = []
                    try:
                        QMessageBox.warning = staticmethod(
                            lambda *args, **kwargs: warnings.append(True) or QMessageBox.Ok
                        )
                        tab.add_btn.click()
                    finally:
                        QMessageBox.warning = original_warning
                        GameDialog.exec = original
                    assert len(warnings) == 1, "duplicate warning not shown"
                    assert db.count_all_games() == 1, "duplicate created"
                    assert tab.selected_game_id() == record_id
                    assert db.get_game(record_id).sm_points == 456

                check("sandbox_list_duplicate_title_guard", duplicate_title_rejected)

            finally:
                window.close()
                app.processEvents()
                window.thread_pool.waitForDone(15000)

    check("sandbox_qt_all_nine_main_tabs_navigation", navigate_tabs)
    report = {
        "schema": "inone-autotest-sandbox-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "tests": results,
        "summary": {
            "pass": sum(t["status"] == "PASS" for t in results),
            "fail": sum(t["status"] == "FAIL" for t in results),
        },
        "data_scope": "temporary_local_sandbox_only",
    }
    target = Path(output_file).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["summary"]["fail"] == 0 else 1
