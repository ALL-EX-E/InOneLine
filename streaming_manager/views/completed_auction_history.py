from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from PySide6.QtCore import QDate, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..database import Database, display_datetime_local, format_points
from ..random_sources import RandomDraw
from .auction_history import MODE_LABELS, format_auction_history_event
from .winner_verification import format_verification_snapshot, show_readonly_text_dialog


STATUS_LABELS = {
    "confirmed": "ЗАВЕРШЁН",
    "cancelled": "ОТМЕНЁН",
    "finished_no_winner": "БЕЗ ПОБЕДИТЕЛЯ",
    "finished": "ЗАВЕРШЁН (legacy)",
}
RESULT_LABELS = {
    "winner": "Победитель",
    "not_winner": "Не победил",
    "tie": "Ничья",
    "": "—",
}


class CompletedAuctionHistoryTab(QWidget):
    PAGE_SIZE = 50

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self._loaded = 0
        self._has_more = False
        self._selected_auction_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(9)

        desc = QLabel("Архив завершённых аукционов. Все данные доступны только для просмотра.")
        desc.setProperty("muted", True)
        root.addWidget(desc)

        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по аукциону, ID, победителю или лоту…")
        self.search.setClearButtonEnabled(True)
        controls.addWidget(self.search, 2)

        self.period = QComboBox()
        for label, code in (
            ("Всё время", "all"), ("Сегодня", "today"),
            ("Последние 7 дней", "7d"), ("Последние 30 дней", "30d"),
            ("Этот месяц", "month"), ("Произвольный период", "custom"),
        ):
            self.period.addItem(label, code)
        controls.addWidget(self.period)

        self.date_from = QDateEdit(QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        controls.addWidget(self.date_from)
        controls.addWidget(QLabel("—"))
        controls.addWidget(self.date_to)

        self.sort = QComboBox()
        for label, code in (
            ("Новые → старые", "newest"), ("Старые → новые", "oldest"),
            ("Название А → Я", "name_asc"), ("Название Я → А", "name_desc"),
        ):
            self.sort.addItem(label, code)
        controls.addWidget(self.sort)
        root.addLayout(controls)

        stats = QHBoxLayout()
        self.stat_total = QLabel()
        self.stat_confirmed = QLabel()
        self.stat_cancelled = QLabel()
        self.stat_no_winner = QLabel()
        for widget in (self.stat_total, self.stat_confirmed, self.stat_cancelled, self.stat_no_winner):
            widget.setProperty("badge", True)
            stats.addWidget(widget)
        stats.addStretch(1)
        root.addLayout(stats)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(("ДАТА", "АУКЦИОН", "РЕЖИМ", "СТАТУС", "ПОБЕДИТЕЛЬ", "ЛОТОВ"))
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        root.addWidget(self.table, 3)

        self.load_more_btn = QPushButton("Загрузить ещё")
        self.load_more_btn.clicked.connect(self.load_more)
        root.addWidget(self.load_more_btn, 0, Qt.AlignCenter)

        self.details_tabs = QTabWidget()
        self.general_page = QWidget()
        general_layout = QGridLayout(self.general_page)
        self.general_labels: dict[str, QLabel] = {}
        for row, (key, title) in enumerate((
            ("id", "ID:"), ("name", "Аукцион:"), ("mode", "Режим:"),
            ("status", "Статус:"), ("started", "Начало:"),
            ("finished", "Завершение:"), ("winner", "Победитель:"),
        )):
            general_layout.addWidget(QLabel(title), row, 0)
            value = QLabel("—")
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            general_layout.addWidget(value, row, 1)
            self.general_labels[key] = value
        general_layout.setColumnStretch(1, 1)
        general_layout.setRowStretch(7, 1)
        self.details_tabs.addTab(self.general_page, "Общие")

        self.lots_table = QTableWidget(0, 6)
        self.lots_table.setHorizontalHeaderLabels(("СТАРТ", "НАЗВАНИЕ", "НА СТАРТЕ", "ДОБАВЛЕНО", "ИТОГ", "РЕЗУЛЬТАТ"))
        self.lots_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lots_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.lots_table.setAlternatingRowColors(True)
        self.lots_table.verticalHeader().setVisible(False)
        lh = self.lots_table.horizontalHeader()
        lh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        lh.setSectionResizeMode(1, QHeaderView.Stretch)
        for col in (2, 3, 4, 5):
            lh.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.details_tabs.addTab(self.lots_table, "Лоты")

        self.events = QListWidget()
        self.events.setSelectionMode(QAbstractItemView.NoSelection)
        self.details_tabs.addTab(self.events, "События")

        self.verification_page = QWidget()
        verification_layout = QVBoxLayout(self.verification_page)
        verification_layout.setContentsMargins(10, 10, 10, 10)
        verification_layout.setSpacing(8)
        self.verification_notice = QLabel(
            "Для результатов колеса версии 0.3.41+ здесь хранится immutable snapshot."
        )
        self.verification_notice.setWordWrap(True)
        self.verification_notice.setProperty("muted", True)
        verification_layout.addWidget(self.verification_notice)

        verification_grid = QGridLayout()
        self.verification_labels: dict[str, QLabel] = {}
        for row, (key, title) in enumerate((
            ("run_id", "Run ID:"),
            ("algorithm", "Алгоритм:"),
            ("rng", "RNG:"),
            ("created", "Время snapshot:"),
            ("value", "Случайное значение:"),
            ("participants", "Участников:"),
            ("winner", "Сохранённый победитель:"),
            ("result", "Проверка результата:"),
            ("random_org", "Random.org+:"),
        )):
            verification_grid.addWidget(QLabel(title), row, 0)
            value = QLabel("—")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            verification_grid.addWidget(value, row, 1)
            self.verification_labels[key] = value
        verification_grid.setColumnStretch(1, 1)
        verification_layout.addLayout(verification_grid)

        verification_buttons = QHBoxLayout()
        self.verify_result_btn = QPushButton("Проверить результат")
        self.verify_result_btn.clicked.connect(self._verify_selected_result)
        self.verification_details_btn = QPushButton("Подробные данные")
        self.verification_details_btn.clicked.connect(self._show_verification_details)
        self.verification_random_org_btn = QPushButton("Открыть проверку RANDOM.ORG")
        self.verification_random_org_btn.clicked.connect(self._open_verification_random_org)
        verification_buttons.addWidget(self.verify_result_btn)
        verification_buttons.addWidget(self.verification_details_btn)
        verification_buttons.addWidget(self.verification_random_org_btn)
        verification_buttons.addStretch()
        verification_layout.addLayout(verification_buttons)
        verification_layout.addStretch(1)
        self.details_tabs.addTab(self.verification_page, "Проверка результата")
        self._verification_snapshot: dict | None = None

        root.addWidget(self.details_tabs, 2)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self.refresh)
        self.search.textChanged.connect(lambda _text: self._search_timer.start())
        self.period.currentIndexChanged.connect(self._period_changed)
        self.sort.currentIndexChanged.connect(self.refresh)
        self.date_from.dateChanged.connect(self._custom_date_changed)
        self.date_to.dateChanged.connect(self._custom_date_changed)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self._period_changed()
        self.refresh()

    def _period_changed(self):
        custom = self.period.currentData() == "custom"
        self.date_from.setVisible(custom)
        self.date_to.setVisible(custom)
        self.refresh()

    def _custom_date_changed(self):
        if self.period.currentData() == "custom":
            self.refresh()

    @staticmethod
    def _utc_iso_for_local_day(qdate: QDate) -> str:
        local = datetime(qdate.year(), qdate.month(), qdate.day()).astimezone()
        return local.astimezone(timezone.utc).isoformat(timespec="microseconds")

    def _date_bounds(self) -> tuple[str | None, str | None]:
        code = self.period.currentData()
        if code == "all":
            return None, None
        today = QDate.currentDate()
        if code == "today":
            start, end = today, today.addDays(1)
        elif code == "7d":
            start, end = today.addDays(-6), today.addDays(1)
        elif code == "30d":
            start, end = today.addDays(-29), today.addDays(1)
        elif code == "month":
            start = QDate(today.year(), today.month(), 1)
            end = start.addMonths(1)
        else:
            start = self.date_from.date()
            end = self.date_to.date().addDays(1)
            if end <= start:
                end = start.addDays(1)
        return self._utc_iso_for_local_day(start), self._utc_iso_for_local_day(end)

    def _query_args(self) -> dict:
        date_from, date_to = self._date_bounds()
        return {
            "search_text": self.search.text().strip(),
            "date_from": date_from,
            "date_to": date_to,
        }

    def refresh(self):
        self._loaded = 0
        self.table.setRowCount(0)
        self._clear_details()
        self._refresh_summary()
        self.load_more()

    def _refresh_summary(self):
        summary = self.db.completed_auction_summary(**self._query_args())
        self.stat_total.setText(f"Закрыто аукционов: {summary['total']}")
        self.stat_confirmed.setText(f"С победителем: {summary['confirmed']}")
        self.stat_cancelled.setText(f"Отменено: {summary['cancelled']}")
        self.stat_no_winner.setText(f"Без победителя: {summary['no_winner']}")

    def load_more(self):
        rows = self.db.list_completed_auction_sessions(
            **self._query_args(),
            sort_order=str(self.sort.currentData() or "newest"),
            limit=self.PAGE_SIZE + 1,
            offset=self._loaded,
        )
        visible = rows[:self.PAGE_SIZE]
        self._has_more = len(rows) > self.PAGE_SIZE
        for row in visible:
            table_row = self.table.rowCount()
            self.table.insertRow(table_row)
            values = (
                display_datetime_local(row.get("sort_time")),
                str(row.get("name") or f"Аукцион #{row['id']}"),
                MODE_LABELS.get(str(row.get("mode") or ""), str(row.get("mode") or "—")),
                STATUS_LABELS.get(str(row.get("status") or ""), str(row.get("status") or "—")),
                str(row.get("winner_title") or "—") if row.get("status") == "confirmed" else "—",
                str(int(row.get("lot_count") or 0)),
            )
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setData(Qt.UserRole, int(row["id"]))
                if col in (0, 2, 3, 5):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(table_row, col, item)
        self._loaded += len(visible)
        self.load_more_btn.setVisible(self._has_more)
        if self.table.rowCount() and self.table.currentRow() < 0:
            self.table.selectRow(0)

    def _selection_changed(self):
        row = self.table.currentRow()
        if row < 0:
            self._clear_details()
            return
        item = self.table.item(row, 0)
        auction_id = item.data(Qt.UserRole) if item else None
        if auction_id is None:
            self._clear_details()
            return
        self._selected_auction_id = int(auction_id)
        self._load_details(self._selected_auction_id)

    def _clear_details(self):
        self._selected_auction_id = None
        for label in self.general_labels.values():
            label.setText("—")
        self.lots_table.setRowCount(0)
        self.events.clear()
        self._clear_verification_details()

    def _clear_verification_details(self):
        self._verification_snapshot = None
        for label in self.verification_labels.values():
            label.setText("—")
        self.verification_notice.setText(
            "Для результатов колеса версии 0.3.41+ здесь хранится immutable snapshot."
        )
        self.verify_result_btn.setEnabled(False)
        self.verification_details_btn.setEnabled(False)
        self.verification_random_org_btn.setVisible(False)

    def _load_verification_details(self, auction_id: int):
        snapshot = self.db.get_wheel_verification_snapshot(int(auction_id))
        self._verification_snapshot = snapshot
        if snapshot is None:
            self.verification_notice.setText(
                "Verification snapshot отсутствует. Для аукционов, завершённых до 0.3.41, "
                "точные входные данные прошлого вращения намеренно не восстанавливаются."
            )
            for label in self.verification_labels.values():
                label.setText("—")
            self.verification_labels["result"].setText("Невозможно проверить")
            self.verify_result_btn.setEnabled(False)
            self.verification_details_btn.setEnabled(False)
            self.verification_random_org_btn.setVisible(False)
            return

        self.verification_notice.setText(
            "Snapshot зафиксирован во время фактического вращения и не зависит от текущих данных игр."
        )
        self.verification_labels["run_id"].setText(str(snapshot.get("run_id") or "—"))
        self.verification_labels["algorithm"].setText(str(snapshot.get("algorithm_version") or "—"))
        rng_method = str(snapshot.get("rng_method") or "local")
        rng_label = {
            "local": "Стандартный (локальный)",
            "random_org": "Random.org",
            "random_org_plus": "Random.org+",
        }.get(rng_method, rng_method)
        self.verification_labels["rng"].setText(rng_label)
        self.verification_labels["created"].setText(
            display_datetime_local(snapshot.get("created_at")) or "—"
        )
        self.verification_labels["value"].setText(str(snapshot.get("rng_value")))
        self.verification_labels["participants"].setText(
            str(len(snapshot.get("participants") or []))
        )
        self.verification_labels["winner"].setText(
            f"ID {snapshot.get('winner_game_id')} — {snapshot.get('winner_title') or '—'}"
        )
        verification = self.db.verify_wheel_result(int(auction_id))
        self.verification_labels["result"].setText(
            f"{verification['label']}. {verification.get('reason') or ''}".strip()
        )
        if rng_method == "random_org_plus":
            verified = snapshot.get("rng_verified")
            proof = "подпись подтверждена" if verified == 1 else "подпись НЕ подтверждена" if verified == 0 else "статус подписи неизвестен"
            self.verification_labels["random_org"].setText(
                f"Ticket ID: {snapshot.get('rng_ticket_id') or '—'}; {proof}"
            )
        else:
            self.verification_labels["random_org"].setText("—")
        self.verify_result_btn.setEnabled(True)
        self.verification_details_btn.setEnabled(True)
        self.verification_random_org_btn.setVisible(
            rng_method == "random_org_plus"
            and bool(snapshot.get("rng_random_json"))
            and bool(snapshot.get("rng_signature"))
        )

    def _verify_selected_result(self):
        if self._selected_auction_id is None:
            return
        result = self.db.verify_wheel_result(self._selected_auction_id)
        self.verification_labels["result"].setText(
            f"{result['label']}. {result.get('reason') or ''}".strip()
        )
        if result["status"] == "match":
            QMessageBox.information(self, "Проверка результата", result["label"])
        elif result["status"] == "mismatch":
            QMessageBox.warning(
                self,
                "Проверка результата",
                f"{result['label']}\n\nОжидаемый победитель: "
                f"ID {result.get('expected_winner_game_id')} — {result.get('expected_winner_title') or '—'}",
            )
        else:
            QMessageBox.warning(
                self,
                "Проверка результата",
                f"{result['label']}\n\n{result.get('reason') or ''}",
            )

    def _show_verification_details(self):
        if not self._verification_snapshot:
            return
        show_readonly_text_dialog(
            self,
            "Подробные данные проверки результата",
            format_verification_snapshot(self._verification_snapshot),
        )

    def _open_verification_random_org(self):
        snapshot = self._verification_snapshot
        if not snapshot:
            return
        try:
            random_json = snapshot.get("rng_random_json")
            signature = snapshot.get("rng_signature")
            if not random_json or not signature:
                raise RuntimeError("В snapshot отсутствует подписанное доказательство RANDOM.ORG.")
            draw = RandomDraw(
                value=int(snapshot.get("rng_value") or 0),
                method="random_org_plus",
                serial_number=snapshot.get("rng_serial_number"),
                ticket_id=snapshot.get("rng_ticket_id"),
                random_object=json.loads(str(random_json)),
                signature=str(signature),
                verified=(
                    True if snapshot.get("rng_verified") == 1
                    else False if snapshot.get("rng_verified") == 0
                    else None
                ),
            )
            url = draw.verification_url()
            if not url:
                raise RuntimeError("Не удалось сформировать официальную ссылку проверки.")
            QDesktopServices.openUrl(QUrl(url))
        except Exception as exc:
            QMessageBox.critical(self, "Random.org+", str(exc))

    def _load_details(self, auction_id: int):
        data = self.db.completed_auction_details(auction_id)
        if not data:
            self._clear_details()
            return
        session = data["session"]
        status = str(session.get("status") or "")
        self.general_labels["id"].setText(str(session.get("id") or "—"))
        self.general_labels["name"].setText(str(session.get("name") or "—"))
        self.general_labels["mode"].setText(MODE_LABELS.get(str(session.get("mode") or ""), str(session.get("mode") or "—")))
        self.general_labels["status"].setText(STATUS_LABELS.get(status, status or "—"))
        self.general_labels["started"].setText(display_datetime_local(session.get("started_at")) or "—")
        self.general_labels["finished"].setText(display_datetime_local(session.get("finished_at") or session.get("sort_time")) or "—")
        self.general_labels["winner"].setText(str(data.get("winner_title") or "—") if status == "confirmed" else "—")

        entries = data["entries"]
        self.lots_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            start = entry.get("start_position")
            values = (
                "—" if start is None else str(start),
                str(entry.get("snapshot_title") or "—"),
                format_points(entry.get("starting_sm_points") or 0),
                "+" + format_points(entry.get("bid_sm_points") or 0),
                format_points(entry.get("total_sm_points") or 0),
                RESULT_LABELS.get(str(entry.get("result") or ""), str(entry.get("result") or "—")),
            )
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col in (0, 2, 3, 4, 5):
                    item.setTextAlignment(Qt.AlignCenter)
                self.lots_table.setItem(row, col, item)

        self.events.clear()
        payload = self.db.list_auction_history_events(auction_id, after_id=0)
        for event in payload.get("events", []):
            formatted = format_auction_history_event(event)
            item = QListWidgetItem(formatted["text"])
            item.setToolTip(f"Точное время: {formatted['exact_time']}\nchange_log ID: {formatted['event_id']}")
            self.events.addItem(item)

        self._load_verification_details(auction_id)
