"""Public list operator smoke checks in a disposable local sandbox only."""
import csv
import json
import time
from pathlib import Path

from openpyxl import load_workbook
from PySide6.QtWidgets import QFileDialog, QMessageBox

from .constants import PUBLIC_XLSX_ENABLED_KEY, PUBLIC_XLSX_PATH_KEY
from .database import Game
from .public_xlsx import public_mirror_rows, public_state_hash


def run_public_checks(check, window, db, paths, app):
    public = window.public_tab
    active = "IOL Public Active"
    secondary = "IOL Public Secondary"
    archived = "IOL Public Archived"
    mirror = paths.root_dir / "operator_public_mirror.xlsx"
    ids = {}

    def xlsx_rows(path):
        book = load_workbook(path, read_only=True, data_only=True)
        try:
            return list(book.active.iter_rows(values_only=True))
        finally:
            book.close()

    def idle():
        end = time.monotonic() + 45
        while time.monotonic() < end:
            app.processEvents()
            if (public._public_xlsx_worker is None
                    and not public._public_xlsx_write_timer.isActive()
                    and not public._public_xlsx_write_pending):
                app.processEvents()
                if public._public_xlsx_worker is None:
                    return
            time.sleep(.03)
        raise AssertionError("public mirror worker timeout")

    def projection():
        assert db.count_all_games() == 0
        ids["a"] = db.add_game(Game(None, active, None, 91, 0, "not_played", "Отзыв Автотест Публичный"))
        ids["b"] = db.add_game(Game(None, secondary, None, 27, 0, "not_played", ""))
        ids["c"] = db.add_game(Game(None, archived, None, 88, 0, "not_played", ""))
        db.archive_game(ids["c"], True)
        window.notify_game_data_changed()
        window._set_current_main_page(public)
        public.search.clear()
        app.processEvents()
        public.refresh()
        assert public.table.columnCount() == 5 and public.table.rowCount() == 2
        assert public.count_label.text() == "Строк: 2"
        assert {public.table.item(i, 1).text() for i in range(2)} == {active, secondary}
        public.search.setText("  iol PUBLIC active  ")
        app.processEvents()
        assert window.games_tab.search.text() == public.search.text()
        assert public.table.rowCount() == 1
        public.activate_search()
        assert public.selected_game_id() == ids["a"]
        assert window.games_tab.selected_game_id() == ids["a"]
        public.search.setText("отзыв автотест публичный")
        app.processEvents()
        assert public.table.rowCount() == 1
        public.search.setText("IOL_NO_PUBLIC_MATCH_987")
        app.processEvents()
        assert public.table.rowCount() == 0
        public.search.clear()
        app.processEvents()
        public.refresh()
        assert public.table.rowCount() == 2

    check("sandbox_public_projection_search_and_selection", projection)

    def exports():
        paths_by_title = {
            "Экспорт CSV": paths.root_dir / "public_sample.csv",
            "Экспорт JSON": paths.root_dir / "public_sample.json",
            "Экспорт Excel": paths.root_dir / "public_sample.xlsx",
        }
        old_picker = QFileDialog.getSaveFileName
        old_ok, old_error = QMessageBox.information, QMessageBox.critical
        notices, errors = [], []
        try:
            QFileDialog.getSaveFileName = staticmethod(
                lambda *a, **kw: (str(paths_by_title[a[1]]), "File")
            )
            QMessageBox.information = staticmethod(
                lambda *a, **kw: notices.append(a[1]) or QMessageBox.Ok
            )
            QMessageBox.critical = staticmethod(
                lambda *a, **kw: errors.append(a[1]) or QMessageBox.Ok
            )
            public.public_export_csv_btn.click()
            public.public_export_json_btn.click()
            public.public_export_xlsx_btn.click()
        finally:
            QFileDialog.getSaveFileName = old_picker
            QMessageBox.information, QMessageBox.critical = old_ok, old_error
        assert len(notices) == 3 and not errors
        assert all(p.is_file() and p.stat().st_size for p in paths_by_title.values())
        with paths_by_title["Экспорт CSV"].open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            assert reader.fieldnames == ["НАЗВАНИЕ ИГРЫ", "БАЛЛЫ", "ОТЗЫВ", "СТАТУС"]
            rows_csv = list(reader)
        data = json.loads(paths_by_title["Экспорт JSON"].read_text(encoding="utf-8"))
        rows_xlsx = xlsx_rows(paths_by_title["Экспорт Excel"])
        assert data["version"] == 1 and len(data["games"]) == 2
        assert len(rows_csv) == 2 and len(rows_xlsx) == 3
        assert {x["НАЗВАНИЕ ИГРЫ"] for x in rows_csv} == {active, secondary}
        assert {x["title"] for x in data["games"]} == {active, secondary}
        assert {x[0] for x in rows_xlsx[1:]} == {active, secondary}
        assert db.count_all_games() == 3 and db.get_game(ids["c"]).archived == 1

    check("sandbox_public_csv_json_xlsx_exports", exports)

    def mirror_create():
        assert public._public_xlsx_path is None
        old = QFileDialog.getSaveFileName
        try:
            QFileDialog.getSaveFileName = staticmethod(lambda *a, **kw: (str(mirror), "Excel"))
            public.public_xlsx_create_btn.click()
        finally:
            QFileDialog.getSaveFileName = old
        idle()
        assert mirror.is_file() and public._public_xlsx_path == mirror
        assert db.get_setting(PUBLIC_XLSX_ENABLED_KEY) == "1"
        assert db.get_setting(PUBLIC_XLSX_PATH_KEY) == str(mirror)
        rows = xlsx_rows(mirror)
        assert rows[0] == ("ПОЗИЦИЯ", "НАЗВАНИЕ ИГРЫ", "БАЛЛЫ", "ОТЗЫВ", "СТАТУС")
        assert len(rows) == 3
        assert {row[1] for row in rows[1:]} == {active, secondary}
        assert public._public_xlsx_last_hash == public_state_hash(public_mirror_rows(db))
        assert "Синхронизировано" in public.public_xlsx_status_label.text()

    check("sandbox_public_mirror_create_and_persist", mirror_create)
