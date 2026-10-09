from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QThreadPool, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..app_paths import AppPaths
from ..api_server import LocalApiServer
from ..constants import (
    PUBLIC_XLSX_ENABLED_KEY,
    PUBLIC_XLSX_LOCAL_WRITE_DEBOUNCE_MS,
    PUBLIC_XLSX_MISSING_POLL_INTERVAL_MS,
    PUBLIC_XLSX_PATH_KEY,
)
from ..diagnostic_logs import append_performance_trace
from ..database import Database, format_points, normalize_text_key
from ..exporters import export_public_csv, export_public_json, export_public_xlsx
from ..public_xlsx import (
    PublicXlsxTransientError, public_mirror_rows, public_state_hash,
    write_public_xlsx,
)
from ..workers import FunctionWorker
from .common import autosize_compact_columns_once, suspend_live_content_resize

class PublicTab(QWidget):
    _COMPACT_COLUMNS = (0, 2, 4)

    def __init__(self, db: Database, api: LocalApiServer):
        super().__init__()
        self.db = db
        self.api = api
        self.thread_pool = QThreadPool.globalInstance()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)

        desc = QLabel(
            "Публичный список формируется напрямую из основной локальной базы: "
            "ПОЗИЦИЯ / НАЗВАНИЕ / БАЛЛЫ / ОТЗЫВ / СТАТУС. "
            "Независимой копии данных нет. "
            "Архивные записи в публичный список не включаются."
        )
        desc.setWordWrap(True)
        desc.setProperty("muted", True)
        layout.addWidget(desc)

        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по названию или отзыву…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._search_text_changed)
        self.search.returnPressed.connect(self.activate_search)

        self.count_label = QLabel()
        self.count_label.setProperty("badge", True)

        top.addWidget(self.search, 1)
        top.addWidget(self.count_label)
        layout.addLayout(top)

        public_export_separator = QFrame()
        public_export_separator.setFrameShape(QFrame.HLine)
        public_export_separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(public_export_separator)

        public_export_title = QLabel("Экспорт списка")
        public_export_title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        layout.addWidget(public_export_title)

        public_export_note = QLabel(
            "CSV, JSON и Excel создают одноразовый снимок текущего публичного списка "
            "и автоматически не обновляются. «Публичная таблица» ниже — отдельное "
            "одностороннее зеркало с автоматическим обновлением."
        )
        public_export_note.setWordWrap(True)
        public_export_note.setProperty("muted", True)
        layout.addWidget(public_export_note)

        public_export_buttons = QHBoxLayout()
        self.public_export_csv_btn = QPushButton("Экспорт CSV")
        self.public_export_json_btn = QPushButton("Экспорт JSON")
        self.public_export_xlsx_btn = QPushButton("Экспорт Excel")
        self.public_export_csv_btn.clicked.connect(self.export_csv)
        self.public_export_json_btn.clicked.connect(self.export_json)
        self.public_export_xlsx_btn.clicked.connect(self.export_xlsx)
        public_export_buttons.addWidget(self.public_export_csv_btn)
        public_export_buttons.addWidget(self.public_export_json_btn)
        public_export_buttons.addWidget(self.public_export_xlsx_btn)
        public_export_buttons.addStretch()
        layout.addLayout(public_export_buttons)

        public_xlsx_separator = QFrame()
        public_xlsx_separator.setFrameShape(QFrame.HLine)
        public_xlsx_separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(public_xlsx_separator)

        public_xlsx_title = QLabel("Публичная таблица")
        public_xlsx_title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        layout.addWidget(public_xlsx_title)

        public_xlsx_description = QLabel(
            "Одностороннее зеркало публичного списка в обычный XLSX. "
            "In one line всегда является источником: внешние изменения файла "
            "и изменения через Google Таблицы обратно в программу не импортируются."
        )
        public_xlsx_description.setWordWrap(True)
        public_xlsx_description.setProperty("muted", True)
        layout.addWidget(public_xlsx_description)

        public_xlsx_buttons = QHBoxLayout()
        self.public_xlsx_create_btn = QPushButton("Создать таблицу")
        self.public_xlsx_connect_btn = QPushButton("Подключить таблицу")
        self.public_xlsx_disconnect_btn = QPushButton("Отключить")
        self.public_xlsx_create_btn.clicked.connect(self._public_xlsx_create)
        self.public_xlsx_connect_btn.clicked.connect(self._public_xlsx_connect)
        self.public_xlsx_disconnect_btn.clicked.connect(self._public_xlsx_disconnect)
        public_xlsx_buttons.addWidget(self.public_xlsx_create_btn)
        public_xlsx_buttons.addWidget(self.public_xlsx_connect_btn)
        public_xlsx_buttons.addWidget(self.public_xlsx_disconnect_btn)
        public_xlsx_buttons.addStretch()
        layout.addLayout(public_xlsx_buttons)

        public_xlsx_form = QFormLayout()
        self.public_xlsx_path_label = QLabel("Не подключена")
        self.public_xlsx_path_label.setWordWrap(True)
        self.public_xlsx_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.public_xlsx_status_label = QLabel("Выключено")
        self.public_xlsx_status_label.setWordWrap(True)
        self.public_xlsx_modified_label = QLabel("—")
        public_xlsx_form.addRow("Таблица:", self.public_xlsx_path_label)
        public_xlsx_form.addRow("Состояние:", self.public_xlsx_status_label)
        public_xlsx_form.addRow("Последнее обновление:", self.public_xlsx_modified_label)
        layout.addLayout(public_xlsx_form)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ПОЗИЦИЯ", "НАЗВАНИЕ", "БАЛЛЫ", "ОТЗЫВ", "СТАТУС"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(32)
        header = self.table.horizontalHeader()
        header.setResizeContentsPrecision(0)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.viewport().installEventFilter(self)
        layout.addWidget(self.table, 1)

        self._init_public_xlsx_mirror()
        self.refresh()

    def eventFilter(self, watched, event):
        if (
            watched is self.table.viewport()
            and event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
            and not self.table.indexAt(event.position().toPoint()).isValid()
        ):
            self.table.clearSelection()
            self.table.setCurrentCell(-1, -1)
            self.table.setFocus(Qt.MouseFocusReason)
            return True
        return super().eventFilter(watched, event)

    def _init_public_xlsx_mirror(self) -> None:
        self._public_xlsx_path: Path | None = None
        self._public_xlsx_worker: FunctionWorker | None = None
        self._public_xlsx_last_hash = ""
        self._public_xlsx_write_pending = False
        self._public_xlsx_write_retry = False
        self._public_xlsx_shutdown = False

        self._public_xlsx_write_timer = QTimer(self)
        self._public_xlsx_write_timer.setSingleShot(True)
        self._public_xlsx_write_timer.setInterval(PUBLIC_XLSX_LOCAL_WRITE_DEBOUNCE_MS)
        self._public_xlsx_write_timer.timeout.connect(self._public_xlsx_start_local_write)

        # This timer never reads XLSX contents.  It only notices a deleted
        # destination so the application can recreate its one-way mirror.
        self._public_xlsx_missing_timer = QTimer(self)
        self._public_xlsx_missing_timer.setInterval(PUBLIC_XLSX_MISSING_POLL_INTERVAL_MS)
        self._public_xlsx_missing_timer.timeout.connect(self._public_xlsx_check_target_exists)

        settings = self.db.get_settings((PUBLIC_XLSX_ENABLED_KEY, PUBLIC_XLSX_PATH_KEY))
        enabled = str(settings.get(PUBLIC_XLSX_ENABLED_KEY, "0")).strip() == "1"
        saved_path = str(settings.get(PUBLIC_XLSX_PATH_KEY, "")).strip()
        if enabled and saved_path:
            self._public_xlsx_activate(Path(saved_path), persist=False, force_write=True)
        else:
            self._public_xlsx_update_controls()

    def _public_xlsx_set_status(self, text: str, *, mtime: float | None = None) -> None:
        self.public_xlsx_status_label.setText(str(text))
        if mtime is not None:
            self.public_xlsx_modified_label.setText(
                datetime.fromtimestamp(float(mtime)).strftime("%d.%m.%Y %H:%M:%S")
            )

    def _public_xlsx_update_controls(self) -> None:
        connected = self._public_xlsx_path is not None
        busy = self._public_xlsx_worker is not None
        self.public_xlsx_path_label.setText(
            str(self._public_xlsx_path) if connected else "Не подключена"
        )
        self.public_xlsx_create_btn.setEnabled(not busy)
        self.public_xlsx_connect_btn.setEnabled(not busy)
        self.public_xlsx_disconnect_btn.setVisible(connected)
        self.public_xlsx_disconnect_btn.setEnabled(connected and not busy)
        if not connected:
            self.public_xlsx_modified_label.setText("—")

    @staticmethod
    def _public_xlsx_normalize_path(path: Path) -> Path:
        path = Path(path)
        return path if path.suffix.lower() == ".xlsx" else path.with_suffix(".xlsx")

    def _public_xlsx_create(self) -> None:
        initial = "Публичный список.xlsx"
        if self._public_xlsx_path is not None:
            initial = str(self._public_xlsx_path.parent / initial)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Создать публичную таблицу",
            initial,
            "Excel (*.xlsx)",
        )
        if not path:
            return
        target = self._public_xlsx_normalize_path(Path(path))
        if target.exists():
            answer = QMessageBox.question(
                self,
                "Заменить таблицу?",
                f"Файл уже существует:\n{target}\n\n"
                "Заменить его текущим публичным списком?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
        self._public_xlsx_activate(target, persist=True, force_write=True)

    def _public_xlsx_connect(self) -> None:
        initial = str(self._public_xlsx_path.parent) if self._public_xlsx_path else ""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Подключить публичную таблицу",
            initial,
            "Excel (*.xlsx)",
        )
        if not path:
            return
        # One-way contract: selected XLSX is a destination, not an import
        # source.  Its current contents are deliberately ignored/overwritten.
        self._public_xlsx_activate(Path(path), persist=True, force_write=True)

    def _public_xlsx_activate(self, path: Path, *, persist: bool, force_write: bool) -> None:
        self._public_xlsx_path = self._public_xlsx_normalize_path(path)
        self._public_xlsx_last_hash = ""
        self._public_xlsx_write_pending = False
        self._public_xlsx_write_retry = False
        if persist:
            self.db.set_settings_bulk(
                {
                    PUBLIC_XLSX_ENABLED_KEY: "1",
                    PUBLIC_XLSX_PATH_KEY: str(self._public_xlsx_path),
                }
            )
        self._public_xlsx_missing_timer.start()
        self._public_xlsx_update_controls()
        self._public_xlsx_set_status("Подключено. Запись актуального списка…")
        if force_write:
            QTimer.singleShot(0, self._public_xlsx_force_write)

    def _public_xlsx_disconnect(self) -> None:
        if self._public_xlsx_worker is not None:
            return
        self._public_xlsx_write_timer.stop()
        self._public_xlsx_missing_timer.stop()
        self._public_xlsx_path = None
        self._public_xlsx_last_hash = ""
        self._public_xlsx_write_pending = False
        self._public_xlsx_write_retry = False
        self.db.set_settings_bulk(
            {PUBLIC_XLSX_ENABLED_KEY: "0", PUBLIC_XLSX_PATH_KEY: ""}
        )
        self._public_xlsx_update_controls()
        self._public_xlsx_set_status("Выключено")

    def public_xlsx_local_data_changed(self) -> None:
        """Schedule the one-way mirror after a possible public-data mutation."""
        if self._public_xlsx_shutdown or self._public_xlsx_path is None:
            return
        self._public_xlsx_write_pending = True
        self._public_xlsx_write_retry = False
        self._public_xlsx_write_timer.start(PUBLIC_XLSX_LOCAL_WRITE_DEBOUNCE_MS)

    def _public_xlsx_check_target_exists(self) -> None:
        if (
            self._public_xlsx_shutdown
            or self._public_xlsx_path is None
            or self._public_xlsx_worker is not None
            or self._public_xlsx_write_timer.isActive()
        ):
            return
        if self._public_xlsx_path.exists():
            return
        self._public_xlsx_set_status("Файл отсутствует. Восстановление…")
        self._public_xlsx_write_pending = True
        self._public_xlsx_write_retry = True
        self._public_xlsx_write_timer.start(0)

    def _public_xlsx_force_write(self) -> None:
        if self._public_xlsx_path is None or self._public_xlsx_shutdown:
            return
        self._public_xlsx_start_write(self._public_xlsx_path, force=True)

    def _public_xlsx_start_local_write(self) -> None:
        if self._public_xlsx_path is None or self._public_xlsx_shutdown:
            return
        if self._public_xlsx_worker is not None:
            self._public_xlsx_write_pending = True
            return
        self._public_xlsx_write_pending = False
        self._public_xlsx_start_write(self._public_xlsx_path, force=False)

    def _public_xlsx_start_write(self, path: Path, *, force: bool) -> None:
        if self._public_xlsx_worker is not None or self._public_xlsx_shutdown:
            self._public_xlsx_write_pending = True
            return
        self._public_xlsx_set_status("Запись таблицы…")
        previous_hash = self._public_xlsx_last_hash

        def write_task():
            rows = public_mirror_rows(self.db)
            logical_hash = public_state_hash(rows)
            if not force and path.exists() and logical_hash == previous_hash:
                stat = path.stat()
                return {
                    "path": str(path),
                    "hash": logical_hash,
                    "rows": len(rows),
                    "signature": (int(stat.st_mtime_ns), int(stat.st_size)),
                    "mtime": float(stat.st_mtime),
                    "written": False,
                }
            result = write_public_xlsx(self.db, path)
            result["written"] = True
            return result

        worker = FunctionWorker(write_task)
        self._public_xlsx_worker = worker
        self._public_xlsx_update_controls()
        worker.signals.result.connect(self._public_xlsx_write_succeeded)
        worker.signals.error.connect(self._public_xlsx_worker_failed)
        worker.signals.finished.connect(self._public_xlsx_worker_finished)
        self.thread_pool.start(worker)

    def _public_xlsx_write_succeeded(self, result: dict) -> None:
        self._public_xlsx_write_retry = False
        self._public_xlsx_last_hash = str(result.get("hash") or "")
        self._public_xlsx_set_status("Синхронизировано", mtime=result.get("mtime"))

    def _public_xlsx_worker_failed(self, exc: Exception) -> None:
        if isinstance(exc, PublicXlsxTransientError):
            self._public_xlsx_set_status(str(exc))
            self._public_xlsx_write_pending = True
            self._public_xlsx_write_retry = True
            return
        self._public_xlsx_set_status(f"Ошибка синхронизации: {exc}")

    def _public_xlsx_worker_finished(self) -> None:
        self._public_xlsx_worker = None
        self._public_xlsx_update_controls()
        if self._public_xlsx_write_pending and self._public_xlsx_path is not None:
            delay = 1500 if self._public_xlsx_write_retry else PUBLIC_XLSX_LOCAL_WRITE_DEBOUNCE_MS
            self._public_xlsx_write_timer.start(delay)

    def shutdown_public_xlsx(self) -> None:
        self._public_xlsx_shutdown = True
        self._public_xlsx_write_timer.stop()
        self._public_xlsx_missing_timer.stop()

    def _search_text_changed(self, text: str):
        """Refresh through MainWindow so hidden synchronized tables stay lazy."""
        window = self.window()
        if hasattr(window, "sync_search_text"):
            window.sync_search_text("public", text)
        else:
            self.refresh()

    def selected_game_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def select_synced_search_result(self, game_id: int) -> bool:
        """Выделяет в публичном списке ту же активную игру."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                continue
            value = item.data(Qt.UserRole)
            try:
                row_id = int(value)
            except (TypeError, ValueError):
                continue
            if row_id != game_id:
                continue

            self.table.selectRow(row)
            self.table.scrollToItem(item)
            return True
        return False

    def activate_search(self):
        """Переходит к первой строке результата поиска."""
        query = self.search.text().strip()

        self.refresh()

        if self.table.rowCount() == 0:
            if query:
                QMessageBox.information(
                    self,
                    "Поиск",
                    f"По запросу «{query}» ничего не найдено.",
                )
            return

        self.table.selectRow(0)
        target = self.table.item(0, 0)
        if target is not None:
            self.table.scrollToItem(target)
        self.table.setFocus()

        game_id = self.selected_game_id()
        window = self.window()
        if game_id is not None and hasattr(window, "sync_search_result"):
            window.sync_search_result(game_id, source="public")

    def refresh(self):
        started = time.perf_counter()
        # Используем ту же Unicode-нормализацию, что и на вкладке «Игры».
        # Поэтому поиск одинаково работает с лишними пробелами, регистром и
        # совместимыми Unicode-символами на обеих вкладках.
        query = normalize_text_key(self.search.text())
        snapshot = self.db.public_refresh_snapshot()
        rows = snapshot["rows"]
        positions = snapshot["positions"]
        if query:
            rows = [
                row for row in rows
                if query in normalize_text_key(row["title"])
                or query in normalize_text_key(row["review"])
            ]
        db_seconds = time.perf_counter() - started
        self.count_label.setText(f"Строк: {len(rows)}")

        # Full QTableWidget population is intentionally batched.  On Windows
        # repainting every setItem() made A3's extra columns amplify refresh
        # latency into visible multi-second stalls.
        previous_blocked = self.table.blockSignals(True)
        suspend_live_content_resize(self.table, self._COMPACT_COLUMNS)
        self.table.setUpdatesEnabled(False)
        fill_started = time.perf_counter()
        fill_seconds = 0.0
        autosize_seconds = 0.0
        reactivate_seconds = 0.0
        try:
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                _start_position, current_position = positions.get(
                    int(row["id"]), (None, None)
                )
                values = [
                    "" if current_position is None else str(current_position),
                    row["title"],
                    format_points(int(row["sm_points"])),
                    row["review"],
                    row["status"],
                ]
                for c, value in enumerate(values):
                    text = str(value)
                    item = self.table.item(r, c)
                    if item is None:
                        item = QTableWidgetItem()
                        self.table.setItem(r, c, item)
                    if item.text() != text:
                        item.setText(text)
                    if c == 0:
                        item.setData(Qt.UserRole, int(row["id"]))
                    if c in (0, 2, 4):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    item.setToolTip(str(row["review"]) if c == 3 and row["review"] else "")
            fill_seconds = time.perf_counter() - fill_started

            autosize_started = time.perf_counter()
            autosize_compact_columns_once(self.table, self._COMPACT_COLUMNS)
            autosize_seconds = time.perf_counter() - autosize_started

            reactivate_started = time.perf_counter()
            self.table.setUpdatesEnabled(True)
            reactivate_seconds = time.perf_counter() - reactivate_started
        finally:
            if not self.table.updatesEnabled():
                self.table.setUpdatesEnabled(True)
            self.table.blockSignals(previous_blocked)

        try:
            append_performance_trace(
                AppPaths.from_database_path(self.db.path).logs_dir,
                "PUBLIC_REFRESH "
                f"rows={len(rows)} db={db_seconds:.3f}s "
                f"fill={fill_seconds:.3f}s "
                f"autosize={autosize_seconds:.3f}s "
                f"reactivate={reactivate_seconds:.3f}s "
                f"total={time.perf_counter()-started:.3f}s",
            )
        except Exception:
            pass

    def _save(self, title: str, suffix: str, fn):
        path, _ = QFileDialog.getSaveFileName(
            self, title, f"public_list{suffix}", f"*{suffix}"
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() != suffix.lower():
            target = target.with_suffix(suffix)
        try:
            fn(self.db, target)
            QMessageBox.information(self, "Экспорт", f"Файл сохранён:\n{target}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка экспорта", str(exc))

    def export_csv(self):
        self._save("Экспорт CSV", ".csv", export_public_csv)

    def export_json(self):
        self._save("Экспорт JSON", ".json", export_public_json)

    def export_xlsx(self):
        self._save("Экспорт Excel", ".xlsx", export_public_xlsx)

