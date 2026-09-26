from __future__ import annotations

import json
import time
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QThreadPool, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView, QHeaderView, QLabel, QLineEdit, QTableView, QVBoxLayout, QWidget,
)

from ..app_paths import AppPaths
from ..constants import COOP_LABELS, STATUS_LABELS
from ..database import Database, display_date, display_datetime_local, format_points
from ..diagnostic_logs import append_performance_trace
from ..workers import FunctionWorker


class LogTableModel(QAbstractTableModel):
    HEADERS = ("ВРЕМЯ", "ОБЪЕКТ", "ID", "ДЕЙСТВИЕ", "ПОДРОБНОСТИ")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[tuple[str, str, str, str, str]] = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        column = index.column()
        if row < 0 or row >= len(self._rows):
            return None
        value = self._rows[row][column]
        if role == Qt.DisplayRole:
            return value
        if role == Qt.ToolTipRole and column == 4:
            return value
        if role == Qt.TextAlignmentRole and column in (1, 2, 3):
            return int(Qt.AlignCenter)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def replace_rows(self, rows: list[tuple[str, str, str, str, str]]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()


class LogTab(QWidget):
    """Technical journal optimized for frequent refreshes.

    The old implementation rebuilt up to 2,500 QTableWidgetItem objects and
    forced four ResizeToContents scans every time the tab became dirty. On a
    large Windows/Qt window that could block the event loop for several
    seconds. The journal now uses a lightweight model and prepares rows in a
    worker thread; switching to the tab is therefore non-blocking.
    """

    FIELD_LABELS = {
        "title": "Название",
        "release_date": "Дата выхода",
        "sm_points": "Баллы",
        "amount_kopecks": "Сумма (legacy RUB)",
        "coop": "Кооп",
        "status": "Статус",
        "review": "Отзыв",
        "archived": "Архив",
    }

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.thread_pool = QThreadPool.globalInstance()
        self._refresh_worker: FunctionWorker | None = None
        self._refresh_pending = False
        self._last_refresh_started = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)

        desc = QLabel(
            "Журнал локальных изменений. Новые интеграции позже будут писать события сюда же."
        )
        desc.setProperty("muted", True)
        layout.addWidget(desc)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск в журнале…")
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)

        # Search is debounced so rapid typing does not start a database worker
        # for every single keystroke.  The worker still uses the same existing
        # FunctionWorker/QThreadPool infrastructure as normal journal refresh.
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self.refresh)
        self.search.textChanged.connect(self._search_text_changed)

        self.model = LogTableModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(32)
        h = self.table.horizontalHeader()
        # Fixed/interactive widths avoid the expensive full-model
        # ResizeToContents pass on every refresh. Details consumes the rest.
        h.setSectionResizeMode(0, QHeaderView.Interactive)
        h.setSectionResizeMode(1, QHeaderView.Interactive)
        h.setSectionResizeMode(2, QHeaderView.Interactive)
        h.setSectionResizeMode(3, QHeaderView.Interactive)
        h.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 165)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 150)
        layout.addWidget(self.table, 1)
        self.refresh()

    def _format_value(self, key: str, value):
        if key == "release_date":
            return display_date(value)
        if key in {"sm_points", "amount_kopecks"}:
            return format_points(int(value or 0)) if key == "sm_points" else str(value or 0)
        if key == "coop":
            return COOP_LABELS.get(int(value or 0), str(value))
        if key == "status":
            return STATUS_LABELS.get(str(value), str(value))
        if key == "archived":
            return "Да" if value else "Нет"
        return "" if value is None else str(value)

    def _details(self, row) -> str:
        before = {}
        after = {}
        try:
            before = json.loads(row["before_json"]) if row["before_json"] else {}
            after = json.loads(row["after_json"]) if row["after_json"] else {}
        except Exception:
            return row["after_json"] or row["before_json"] or ""

        if row["entity_type"] == "auction_lot":
            title = after.get("title") or before.get("title") or ""
            if row["action"] == "create":
                return f"Создан лот «{title}»" if title else "Создан лот"
            if row["action"] == "delete":
                return f"Удалён лот «{title}»" if title else "Лот удалён"
            return str(after or before)

        if row["entity_type"] != "game":
            if isinstance(after, dict) and "key" in after:
                return f"{after.get('key')}: {after.get('value', '')}"
            return str(after or before)

        title = after.get("title") or before.get("title") or ""
        if row["action"] == "create":
            return f"Создана игра «{title}»"
        if row["action"] == "delete":
            return f"Удалена игра «{title}»" if title else "Игра удалена"

        changes = []
        for key, label in self.FIELD_LABELS.items():
            if key in before or key in after:
                old = before.get(key)
                new = after.get(key)
                if old != new:
                    changes.append(
                        f"{label}: {self._format_value(key, old)} → {self._format_value(key, new)}"
                    )
        return f"{title}: " + "; ".join(changes) if changes else title

    def _load_rows(self, search_text: str = ""):
        query = search_text.strip().casefold()

        db_started = time.perf_counter()
        # Empty search keeps the existing fast 500-row journal window.  A real
        # search reads the complete journal in the worker so an older matching
        # event is not hidden merely because it fell outside that window.
        rows = self.db.list_log(limit=None if query else 500)
        db_seconds = time.perf_counter() - db_started

        format_started = time.perf_counter()
        formatted: list[tuple[str, str, str, str, str]] = []
        for row in rows:
            action = {
                "create": "СОЗДАНИЕ",
                "update": "ИЗМЕНЕНИЕ",
                "delete": "УДАЛЕНИЕ",
                "add": "ДОБАВЛЕНИЕ",
                "decrease": "УМЕНЬШЕНИЕ",
            }.get(row["action"], row["action"].upper())
            display_row = (
                display_datetime_local(row["created_at"]),
                {
                    "game": "Игра",
                    "auction_lot": "Лот аукциона",
                }.get(row["entity_type"], row["entity_type"]),
                "" if row["entity_id"] is None else str(row["entity_id"]),
                action,
                self._details(row),
            )

            if query:
                # Search both what the operator actually sees and the raw
                # stored fields.  This makes Russian UI labels, formatted
                # details, English technical actions (e.g. ``delete``), IDs
                # and JSON event content all searchable with one field.
                raw_values = (
                    row["entity_type"],
                    row["entity_id"],
                    row["action"],
                    row["before_json"],
                    row["after_json"],
                    row["created_at"],
                )
                haystack = "\n".join(
                    [*(str(value) for value in display_row),
                     *("" if value is None else str(value) for value in raw_values)]
                ).casefold()
                if query not in haystack:
                    continue

            formatted.append(display_row)

        return {
            "rows": formatted,
            "search_text": search_text.strip(),
            "db_seconds": db_seconds,
            "format_seconds": time.perf_counter() - format_started,
        }

    def _search_text_changed(self, _text: str):
        # Mark an in-flight result as stale immediately; the timer will launch
        # one refresh with the latest text after the user pauses typing.
        if self._refresh_worker is not None:
            self._refresh_pending = True
        self._search_timer.start()

    def refresh(self):
        # Refresh is deliberately asynchronous. MainWindow calls this directly
        # from currentChanged when a dirty tab is opened; doing heavy table work
        # here would freeze every button in the application until it completed.
        if self._refresh_worker is not None:
            self._refresh_pending = True
            return

        self._last_refresh_started = time.perf_counter()
        search_text = self.search.text().strip()
        worker = FunctionWorker(self._load_rows, search_text)
        self._refresh_worker = worker
        worker.signals.result.connect(self._apply_rows)
        worker.signals.finished.connect(self._refresh_finished)
        self.thread_pool.start(worker)

    def _apply_rows(self, result):
        # A worker can finish after the user has already changed the query.
        # Never flash stale results; _refresh_finished() will run the pending
        # refresh with the newest text.
        if result.get("search_text", "") != self.search.text().strip():
            return

        model_started = time.perf_counter()
        self.model.replace_rows(result["rows"])
        model_seconds = time.perf_counter() - model_started
        total_seconds = time.perf_counter() - self._last_refresh_started

        # The old stabilization trace is disabled by default.  It can be
        # explicitly re-enabled for diagnostics with
        # STREAMING_MANAGER_PERFORMANCE_LOG=1 and remains size-capped.
        try:
            append_performance_trace(
                AppPaths.from_database_path(self.db.path).logs_dir,
                "LOG_REFRESH "
                f"rows={len(result['rows'])} "
                f"db={result['db_seconds']:.3f}s "
                f"format={result['format_seconds']:.3f}s "
                f"model={model_seconds:.3f}s "
                f"total={total_seconds:.3f}s",
            )
        except Exception:
            pass

    def _refresh_finished(self):
        self._refresh_worker = None
        if self._refresh_pending:
            self._refresh_pending = False
            # If pending work came from textChanged, the latest query is
            # already known.  Stop the debounce timer so it cannot trigger a
            # redundant second worker after this immediate catch-up refresh.
            self._search_timer.stop()
            self.refresh()
