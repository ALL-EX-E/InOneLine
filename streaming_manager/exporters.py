from __future__ import annotations

import csv
import json
import os
from contextlib import contextmanager
from uuid import uuid4
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from .database import Database


PUBLIC_HEADERS = ["НАЗВАНИЕ ИГРЫ", "БАЛЛЫ", "ОТЗЫВ", "СТАТУС"]


@contextmanager
def _export_destination(path: Path):
    """Replace a completed export on the same volume, retaining an existing file on failure."""
    temporary = path.with_name(f".inone-export-{uuid4().hex}{path.suffix}")
    try:
        yield temporary
        with temporary.open("rb+") as stream:
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def export_public_csv(db: Database, path: str | Path) -> Path:
    path = Path(path)
    with _export_destination(path) as temporary:
        with temporary.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(PUBLIC_HEADERS)
            for row in db.public_games():
                writer.writerow([row["title"], int(row["sm_points"]), row["review"], row["status"]])
    return path


def export_public_json(db: Database, path: str | Path) -> Path:
    path = Path(path)
    payload = {
        "version": 1,
        "columns": PUBLIC_HEADERS,
        "games": db.public_games(),
    }
    with _export_destination(path) as temporary:
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def export_public_xlsx(db: Database, path: str | Path) -> Path:
    path = Path(path)
    wb = Workbook()
    ws = wb.active
    ws.title = "spisok"
    ws.append(PUBLIC_HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for row in db.public_games():
        ws.append([row["title"], int(row["sm_points"]), row["review"], row["status"]])
    ws.column_dimensions["A"].width = 42
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 55
    ws.column_dimensions["D"].width = 18
    for row in ws.iter_rows(min_row=2):
        row[1].number_format = '#,##0'
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    try:
        with _export_destination(path) as temporary:
            wb.save(temporary)
    finally:
        wb.close()
    return path
