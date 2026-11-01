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
            # Only diagnostics from synthetic temporary fixtures, never live data.
            error_message = str(exc)[:350]
        results.append({
            "name": name, "status": status, "duration_ms": int((time.monotonic()-started)*1000),
            "error_type": error_type,
            "error_message": error_message if status == "FAIL" else "",
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

                # AUTO-TEST-002B: use the real CSV import button, worker,
                # isolated-process safety backup, strict parser, result/error
                # callbacks and table refresh, all inside the Qt temp root.
                import sqlite3
                from PySide6.QtWidgets import QFileDialog

                def csv_import_via_ui(csv_name, csv_content, expect_success):
                    csv_path = paths.root_dir / csv_name
                    csv_path.write_text(csv_content, encoding="utf-8")
                    info_messages = []
                    error_messages = []
                    original_picker = QFileDialog.getOpenFileName
                    original_info = QMessageBox.information
                    original_critical = QMessageBox.critical
                    try:
                        QFileDialog.getOpenFileName = staticmethod(
                            lambda *args, **kwargs: (str(csv_path), "CSV (*.csv)")
                        )
                        QMessageBox.information = staticmethod(
                            lambda *args, **kwargs:
                            info_messages.append(str(args[2]) if len(args) > 2 else "")
                            or QMessageBox.Ok
                        )
                        QMessageBox.critical = staticmethod(
                            lambda *args, **kwargs:
                            error_messages.append(str(args[2]) if len(args) > 2 else "")
                            or QMessageBox.Ok
                        )
                        window._set_current_main_page(tab)
                        app.processEvents()
                        assert tab._import_worker is None, "previous CSV worker is running"
                        assert tab.import_btn.isEnabled(), "CSV import button is disabled"
                        tab.import_btn.click()
                        assert tab._import_worker is not None, "no CSV worker was scheduled"
                        deadline = time.monotonic() + 105.0
                        while tab._import_worker is not None and time.monotonic() < deadline:
                            app.processEvents()
                            time.sleep(0.03)
                        app.processEvents()
                        assert tab._import_worker is None, "CSV import worker did not finish"
                        assert tab.import_btn.isEnabled(), "CSV import button stayed disabled"
                        if expect_success:
                            assert len(info_messages) == 1, "completion dialog missing"
                            assert not error_messages, "unexpected CSV error dialog"
                        else:
                            assert len(error_messages) == 1, "CSV error dialog missing"
                            assert not info_messages, "invalid CSV was reported as success"
                        return info_messages[0] if expect_success else error_messages[0]
                    finally:
                        QFileDialog.getOpenFileName = original_picker
                        QMessageBox.information = original_info
                        QMessageBox.critical = original_critical

                def safety_backup_files():
                    return tuple(sorted(paths.backups_dir.glob("streaming_*.db")))

                def assert_backup_is_valid(before):
                    after = safety_backup_files()
                    new_files = set(after) - set(before)
                    assert len(new_files) == 1, "safety backup not created"
                    backup_file = next(iter(new_files))
                    assert backup_file.stat().st_size > 0, "safety backup empty"
                    # sqlite3.Connection.__exit__ commits but does NOT close.
                    # Windows keeps the .db handle locked until explicit close.
                    from contextlib import closing
                    with closing(sqlite3.connect(str(backup_file))) as copied:
                        assert copied.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                    return backup_file

                def csv_normal_merge_with_backup():
                    assert record_id is not None, "list create failed earlier"
                    before = safety_backup_files()
                    message = csv_import_via_ui(
                        "autotest_valid.csv",
                        "НАЗВАНИЕ;БАЛЛЫ;ДАТА;ОТЗЫВ\n"
                        + edited_title + ";0;;\n"
                        + "IOL CSV New;78;27.08.2019;\n",
                        expect_success=True,
                    )
                    assert "Добавлено: 1" in message and "Изменено: 1" in message
                    # Validate the exact backup reported by the real import
                    # worker; a before/after filename count can race another
                    # automatic backup on Windows.
                    label = "Резервная копия перед импортом:\n"
                    assert label in message, "CSV result missing backup path"
                    from pathlib import Path
                    snapshot = Path(message.split(label, 1)[1].strip())
                    assert snapshot.resolve().parent == paths.backups_dir.resolve()
                    assert snapshot.is_file() and snapshot.stat().st_size > 0
                    from contextlib import closing
                    with closing(sqlite3.connect(str(snapshot))) as copied:
                        assert copied.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                        row = copied.execute(
                            "SELECT sm_points FROM games WHERE id=?", (record_id,)
                        ).fetchone()
                        assert row is not None and int(row[0]) == 456
                    old = db.get_game(record_id)
                    assert old.sm_points == 0, "explicit zero points not applied"
                    assert old.review == "Synthetic review", "blank CSV erased review"
                    new = db.find_game_by_title("IOL CSV New")
                    assert new is not None and new.sm_points == 78
                    assert new.release_date == "2019-08-27"
                    assert db.count_all_games() == 2
                    assert tab.table.rowCount() == 2, "list was not refreshed"

                check("sandbox_csv_ui_merge_zero_and_safety_backup", csv_normal_merge_with_backup)

                def csv_invalid_is_atomic():
                    before = safety_backup_files()
                    original = db.get_game(record_id)
                    count = db.count_all_games()
                    message = csv_import_via_ui(
                        "autotest_invalid.csv",
                        "НАЗВАНИЕ;БАЛЛЫ;СТАТУС\n"
                        "IOL CSV Atomic Good;99;НЕ ИГРАЛ\n"
                        "IOL CSV Atomic Bad;50;НЕИЗВЕСТНО\n",
                        expect_success=False,
                    )
                    assert "Импорт не выполнен" in message, "missing import error detail"
                    assert "СТАТУС" in message and "строка 3" in message
                    assert_backup_is_valid(before)
                    assert db.count_all_games() == count, "invalid CSV changed database"
                    assert db.find_game_by_title("IOL CSV Atomic Good") is None
                    assert db.get_game(record_id) == original, "failed import changed record"
                    assert tab.table.rowCount() == count

                check("sandbox_csv_ui_error_atomicity_and_backup", csv_invalid_is_atomic)

                def csv_legacy_pipe():
                    before = safety_backup_files()
                    message = csv_import_via_ui(
                        "autotest_legacy.csv",
                        "IOL CSV Legacy|125\n",
                        expect_success=True,
                    )
                    assert "Добавлено: 1" in message
                    assert_backup_is_valid(before)
                    record = db.find_game_by_title("IOL CSV Legacy")
                    assert record is not None and record.sm_points == 125
                    assert db.count_all_games() == 3
                    assert tab.table.rowCount() == 3

                check("sandbox_csv_ui_legacy_pipe_and_backup", csv_legacy_pipe)

                # AUTO-TEST-002C: joint XLSX table UI and real worker file
                # protocol. File dialogs return paths under ONLY this temp root.
                # The "remote" client is another SQLite DB under the same root,
                # not a Google Drive or Twitch connection.
                from .constants import SHARED_XLSX_ENABLED_KEY, SHARED_XLSX_PATH_KEY
                from .shared_xlsx import (
                    main_games_rows, read_shared_xlsx, state_hash,
                    write_shared_xlsx,
                )

                auction = window.auction_tab
                xlsx_path = paths.root_dir / "inone_operator_shared_test.xlsx"
                remote_title = "IOL XLSX External"
                remote_record_id = None

                def wait_xlsx_idle():
                    deadline = time.monotonic() + 40.0
                    while time.monotonic() < deadline:
                        app.processEvents()
                        if (
                            auction._shared_xlsx_worker is None
                            and not auction._shared_xlsx_write_timer.isActive()
                            and not auction._shared_xlsx_write_pending
                        ):
                            app.processEvents()
                            if auction._shared_xlsx_worker is None:
                                return
                        time.sleep(0.025)
                    raise AssertionError("XLSX worker or debounce timer did not finish")

                def assert_xlsx_matches_local():
                    payload = read_shared_xlsx(xlsx_path)
                    assert payload["hash"] == state_hash(main_games_rows(db))
                    return payload

                def xlsx_create_connected():
                    window._set_current_main_page(tab)
                    assert auction._shared_xlsx_path is None
                    original = QFileDialog.getSaveFileName
                    try:
                        QFileDialog.getSaveFileName = staticmethod(
                            lambda *args, **kwargs: (str(xlsx_path), "Excel (*.xlsx)")
                        )
                        assert auction.shared_xlsx_create_btn.isEnabled()
                        auction.shared_xlsx_create_btn.click()
                    finally:
                        QFileDialog.getSaveFileName = original
                    wait_xlsx_idle()
                    assert xlsx_path.is_file(), "XLSX was not created"
                    assert auction._shared_xlsx_path == xlsx_path
                    assert db.get_setting(SHARED_XLSX_ENABLED_KEY) == "1"
                    assert db.get_setting(SHARED_XLSX_PATH_KEY) == str(xlsx_path)
                    assert auction.shared_xlsx_path_label.text() == str(xlsx_path)
                    assert auction.shared_xlsx_disconnect_btn.isEnabled()
                    assert len(assert_xlsx_matches_local()["rows"]) == 3
                    assert "Синхронизировано" in auction.shared_xlsx_status_label.text()

                check("sandbox_xlsx_ui_create_connect_and_persist", xlsx_create_connected)

                def xlsx_local_write():
                    assert auction._shared_xlsx_path == xlsx_path, "not connected"
                    target = db.find_game_by_title("IOL CSV New")
                    assert target is not None
                    db.update_game(target.id, {"sm_points": 321})
                    window.notify_game_data_changed()
                    wait_xlsx_idle()
                    payload = assert_xlsx_matches_local()
                    exported = next(
                        row for row in payload["rows"] if row["title"] == "IOL CSV New"
                    )
                    assert exported["sm_points"] == 321
                    assert auction._shared_xlsx_worker is None
                    assert "Синхронизировано" in auction.shared_xlsx_status_label.text()

                check("sandbox_xlsx_local_change_syncs_to_file", xlsx_local_write)

                def xlsx_external_file_import():
                    nonlocal remote_record_id
                    assert auction._shared_xlsx_path == xlsx_path, "not connected"
                    # An external app/client produces a new valid XLSX file
                    # through the same public exporter, from a different DB.
                    external_db = Database(paths.root_dir / "external_xlsx_client.db")
                    external_db.sync_main_games_state(main_games_rows(db))
                    ext_record = external_db.find_game_by_title("IOL CSV New")
                    assert ext_record is not None
                    external_db.update_game(ext_record.id, {"sm_points": 654})
                    external_db.add_game(
                        Game(None, remote_title, None, 777, 0, "not_played", "")
                    )
                    before_backup = safety_backup_files()
                    new_xlsx = write_shared_xlsx(external_db, xlsx_path)
                    assert new_xlsx["hash"] != state_hash(main_games_rows(db))
                    # Real stable-file poll: first observation, then confirmed
                    # unchanged signature, then the real async import worker.
                    auction._shared_xlsx_poll()
                    auction._shared_xlsx_poll()
                    wait_xlsx_idle()
                    assert_backup_is_valid(before_backup)
                    synced = db.find_game_by_title("IOL CSV New")
                    assert synced is not None and synced.sm_points == 654
                    new = db.find_game_by_title(remote_title)
                    assert new is not None and new.sm_points == 777
                    remote_record_id = new.id
                    assert db.count_all_games() == 4
                    assert_xlsx_matches_local()
                    tab.refresh()
                    assert tab.table.rowCount() == 4

                check("sandbox_xlsx_external_replace_import_and_backup", xlsx_external_file_import)

                def xlsx_disconnect_reconnect():
                    assert remote_record_id is not None, "external import missing"
                    assert auction.shared_xlsx_disconnect_btn.isEnabled()
                    file_hash = read_shared_xlsx(xlsx_path)["hash"]
                    auction.shared_xlsx_disconnect_btn.click()
                    assert auction._shared_xlsx_path is None
                    assert db.get_setting(SHARED_XLSX_ENABLED_KEY) == "0"
                    assert db.get_setting(SHARED_XLSX_PATH_KEY) == ""
                    assert xlsx_path.exists(), "disconnect deleted the XLSX file"

                    # A detached local edit must NOT write the disk file.
                    db.update_game(remote_record_id, {"sm_points": 888})
                    window.notify_game_data_changed()
                    app.processEvents()
                    assert read_shared_xlsx(xlsx_path)["hash"] == file_hash
                    assert db.get_game(remote_record_id).sm_points == 888

                    before_backup = safety_backup_files()
                    original = QFileDialog.getOpenFileName
                    try:
                        QFileDialog.getOpenFileName = staticmethod(
                            lambda *args, **kwargs: (str(xlsx_path), "Excel (*.xlsx)")
                        )
                        assert auction.shared_xlsx_connect_btn.isEnabled()
                        auction.shared_xlsx_connect_btn.click()
                    finally:
                        QFileDialog.getOpenFileName = original
                    app.processEvents()  # QTimer.singleShot(0, force_import)
                    wait_xlsx_idle()
                    assert_backup_is_valid(before_backup)
                    assert db.get_game(remote_record_id).sm_points == 777, (
                        "reconnected file did not restore authoritative XLSX value"
                    )
                    assert auction._shared_xlsx_path == xlsx_path
                    assert db.get_setting(SHARED_XLSX_ENABLED_KEY) == "1"
                    assert db.get_setting(SHARED_XLSX_PATH_KEY) == str(xlsx_path)
                    assert_xlsx_matches_local()
                    tab.refresh()
                    assert tab.table.rowCount() == 4

                    # Sandbox cleanup never schedules a write to the old XLSX.
                    auction.shared_xlsx_disconnect_btn.click()
                    assert db.get_setting(SHARED_XLSX_ENABLED_KEY) == "0"
                    assert xlsx_path.exists()

                check("sandbox_xlsx_disconnect_preserve_and_reconnect", xlsx_disconnect_reconnect)

                # AUTO-TEST-002D: destructive UI handlers are exercised only
                # inside this independent temp DB, after XLSX is disconnected.
                # Dialog confirmation is simulated, never backup or DB deletion.
                from contextlib import closing
                from PySide6.QtCore import QTimer
                from .views.games import DeleteAllGamesDialog

                def wait_destructive_idle(worker_name):
                    deadline = time.monotonic() + 100.0
                    while time.monotonic() < deadline:
                        app.processEvents()
                        if getattr(tab, worker_name) is None:
                            app.processEvents()
                            return
                        time.sleep(0.025)
                    raise AssertionError(f"{worker_name} did not complete in sandbox")

                def click_delete_confirmation(label):
                    original_exec = QMessageBox.exec

                    def automated_exec(box):
                        match = [button for button in box.buttons()
                                 if button.text() == label]
                        assert len(match) == 1, "delete confirmation button missing"
                        QTimer.singleShot(0, match[0].click)
                        return original_exec(box)

                    QMessageBox.exec = automated_exec
                    return original_exec

                def delete_cancel_preserves_data():
                    record = db.find_game_by_title("IOL CSV Legacy")
                    assert record is not None, "test delete target absent"
                    tab.focus_game(record.id)
                    assert tab.selected_game_id() == record.id
                    assert tab.delete_btn.isEnabled(), "Delete button unavailable"
                    previous_count = db.count_all_games()
                    previous_log = db.games_refresh_snapshot()["stats"]["total"]
                    before_backup = safety_backup_files()
                    original_exec = click_delete_confirmation("Нет")
                    try:
                        tab.delete_btn.click()
                    finally:
                        QMessageBox.exec = original_exec
                    app.processEvents()
                    assert tab._delete_worker is None, "cancel started destructive worker"
                    assert db.get_game(record.id) is not None
                    assert db.count_all_games() == previous_count
                    assert db.games_refresh_snapshot()["stats"]["total"] == previous_log
                    assert safety_backup_files() == before_backup

                check("sandbox_delete_cancel_keeps_records_no_backup", delete_cancel_preserves_data)

                def delete_confirmed_with_backup_and_audit():
                    record = db.find_game_by_title("IOL CSV Legacy")
                    assert record is not None
                    survivor = db.find_game_by_title("IOL CSV New")
                    assert survivor is not None
                    db.set_setting("stream_current_game_id", str(record.id))
                    previous_count = db.count_all_games()
                    tab.focus_game(record.id)
                    assert tab.delete_btn.isEnabled()
                    info_messages = []
                    error_messages = []
                    original_info, original_error = QMessageBox.information, QMessageBox.critical
                    original_exec = click_delete_confirmation("Да, удалить")
                    before_backup = safety_backup_files()
                    try:
                        QMessageBox.information = staticmethod(
                            lambda *args, **kwargs:
                            info_messages.append(str(args[2]) if len(args)>2 else "")
                            or QMessageBox.Ok
                        )
                        QMessageBox.critical = staticmethod(
                            lambda *args, **kwargs:
                            error_messages.append(str(args[2]) if len(args)>2 else "")
                            or QMessageBox.Ok
                        )
                        tab.delete_btn.click()
                        assert tab._delete_worker is not None, "delete worker not started"
                        wait_destructive_idle("_delete_worker")
                    finally:
                        QMessageBox.exec = original_exec
                        QMessageBox.information = original_info
                        QMessageBox.critical = original_error
                    assert not error_messages, "unexpected delete error"
                    assert len(info_messages) == 1, "delete result message missing"
                    backup_path = assert_backup_is_valid(before_backup)
                    with closing(sqlite3.connect(str(backup_path))) as copied:
                        assert copied.execute(
                            "SELECT COUNT(*) FROM games WHERE id=?", (record.id,)
                        ).fetchone()[0] == 1, "snapshot lacks deleted record"
                        assert copied.execute(
                            "SELECT COUNT(*) FROM games"
                        ).fetchone()[0] == previous_count, "snapshot taken after delete"
                    assert db.get_game(record.id) is None
                    assert db.get_game(survivor.id) is not None
                    assert db.count_all_games() == previous_count - 1
                    assert db.get_setting("stream_current_game_id") == ""
                    with db.connect() as conn:
                        rows = conn.execute(
                            "SELECT action FROM change_log "
                            "WHERE entity_type='game' AND entity_id=?",
                            (record.id,),
                        ).fetchall()
                        assert [str(row[0]) for row in rows] == ["delete"], (
                            "previous record-specific log not pruned to delete event"
                        )
                    tab.refresh()
                    assert tab.table.rowCount() == previous_count - 1
                    assert tab.delete_btn.text() == "Удалить"

                check("sandbox_delete_confirm_worker_backup_and_survivors", delete_confirmed_with_backup_and_audit)

                def clear_cancel_without_backup():
                    assert db.count_all_games() >= 2
                    original_exec = DeleteAllGamesDialog.exec
                    count = db.count_all_games()
                    before_backup = safety_backup_files()

                    def reject_dialog(dialog):
                        assert not dialog.delete_button.isEnabled()
                        dialog.confirm_edit.setText("неправильное подтверждение")
                        assert not dialog.delete_button.isEnabled(), (
                            "clear button unlocked by wrong phrase"
                        )
                        dialog.reject()
                        return dialog.result()

                    DeleteAllGamesDialog.exec = reject_dialog
                    try:
                        assert tab.clear_all_btn.isEnabled()
                        tab.clear_all_btn.click()
                    finally:
                        DeleteAllGamesDialog.exec = original_exec
                    assert tab._clear_all_worker is None
                    assert db.count_all_games() == count
                    assert safety_backup_files() == before_backup

                check("sandbox_clear_cancel_requires_exact_phrase", clear_cancel_without_backup)

                def clear_confirmed_preserves_history_and_backup():
                    # Set up a closed local auction using the actual DB API;
                    # do not insert an invented "closed" row in auction tables.
                    assert auction._shared_xlsx_path is None, (
                        "shared XLSX must be disconnected before deletion"
                    )
                    archived = db.add_game(
                        Game(None, "IOL Clear Archived", None, 30, 0, "not_played", "")
                    )
                    db.archive_game(archived, True)
                    closed_id = db.create_auction_session(
                        "max_amount", duration_seconds=5
                    )
                    db.cancel_auction(closed_id)
                    assert db.get_open_auction_session() is None
                    with db.connect() as conn:
                        entry_before = conn.execute(
                            "SELECT COUNT(*) FROM auction_entries WHERE auction_id=?",
                            (closed_id,),
                        ).fetchone()[0]
                    assert entry_before >= 2, "closed session lacks preserved entries"
                    count_before = db.count_all_games()
                    assert count_before >= 4
                    target = db.find_game_by_title("IOL CSV New")
                    assert target is not None
                    db.set_setting("stream_current_game_id", str(target.id))
                    db.set_setting("operator_autotest_unrelated_setting", "keep")
                    tab.refresh()

                    old_exec = DeleteAllGamesDialog.exec
                    old_info = QMessageBox.information
                    old_error = QMessageBox.critical
                    info_messages = []
                    error_messages = []
                    backups_before = safety_backup_files()
                    def accept_dialog(dialog):
                        assert not dialog.delete_button.isEnabled()
                        dialog.confirm_edit.setText("УДАЛИТЬ ЗАПИСИ")
                        assert dialog.delete_button.isEnabled(), (
                            "clear exact confirmation did not enable delete"
                        )
                        dialog.delete_button.click()
                        return dialog.result()
                    try:
                        DeleteAllGamesDialog.exec = accept_dialog
                        QMessageBox.information = staticmethod(
                            lambda *args, **kwargs:
                            info_messages.append(str(args[2]) if len(args)>2 else "")
                            or QMessageBox.Ok
                        )
                        QMessageBox.critical = staticmethod(
                            lambda *args, **kwargs:
                            error_messages.append(str(args[2]) if len(args)>2 else "")
                            or QMessageBox.Ok
                        )
                        tab.clear_all_btn.click()
                        assert tab._clear_all_worker is not None, "clear worker absent"
                        wait_destructive_idle("_clear_all_worker")
                    finally:
                        DeleteAllGamesDialog.exec = old_exec
                        QMessageBox.information = old_info
                        QMessageBox.critical = old_error
                    assert not error_messages, "unexpected clear error"
                    assert len(info_messages) == 1, "clear result message missing"
                    assert f"Удалено записей: {count_before}" in info_messages[0]
                    snapshot = assert_backup_is_valid(backups_before)
                    with closing(sqlite3.connect(str(snapshot))) as copied:
                        assert copied.execute(
                            "SELECT COUNT(*) FROM games"
                        ).fetchone()[0] == count_before, "backup missing pre-clear rows"
                        assert copied.execute(
                            "SELECT COUNT(*) FROM auction_entries WHERE auction_id=?",
                            (closed_id,),
                        ).fetchone()[0] == entry_before, "backup missing history"

                    assert db.count_all_games() == 0, "clear kept live games"
                    assert db.get_setting("stream_current_game_id") == ""
                    assert db.get_setting("operator_autotest_unrelated_setting") == "keep"
                    with db.connect() as conn:
                        assert conn.execute(
                            "SELECT COUNT(*) FROM contributions"
                        ).fetchone()[0] == 0, "clear left live contributions"
                        saved = conn.execute(
                            "SELECT game_id,snapshot_title FROM auction_entries "
                            "WHERE auction_id=?", (closed_id,)
                        ).fetchall()
                        assert len(saved) == entry_before, "closed history lost"
                        assert all(row["game_id"] is None and row["snapshot_title"]
                                   for row in saved), "closed history snapshots lost"
                        assert conn.execute(
                            "SELECT COUNT(*) FROM change_log "
                            "WHERE entity_type='games' AND action='delete_all'"
                        ).fetchone()[0] == 1, "clear missing journal audit"
                    tab.refresh()
                    assert tab.table.rowCount() == 0
                    assert tab.clear_all_btn.text() == "Очистить список"
                    assert not tab.clear_all_btn.isEnabled(), "empty list allows clear"

                check("sandbox_clear_confirm_backup_empty_and_closed_history", clear_confirmed_preserves_history_and_backup)

                from .operator_autotest_public import run_public_checks
                run_public_checks(check, window, db, paths, app)

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
