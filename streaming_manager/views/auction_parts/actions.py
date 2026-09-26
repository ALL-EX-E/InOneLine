from __future__ import annotations

import hashlib
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QDialogButtonBox, QLabel, QTabWidget, QTextEdit, QVBoxLayout, QWidget

from ...database import format_points
from ...diagnostic_logs import sanitize_diagnostic_text
from ...exporters import export_pointauc_csv, pointauc_text
from ...random_sources import RandomDraw, RandomOrgClient
from ...workers import FunctionWorker


class AuctionActionMixin:
    def handle_timer_action(self):
        """Одна кнопка управляет текущим смыслом большого таймера."""
        session = self._current_session()
        if session is None:
            self.start_auction()
            return

        status = str(session.get("status") or "")
        if status == "tie_break_required" and self._pending_tie_overtime:
            self._start_pending_tie_overtime()
            return
        if status == "awaiting_wheel":
            self.run_wheel()
            return
        if status in ("running", "paused"):
            self.toggle_pause()

    def start_auction(self):
        if self._auction_rng_worker is not None:
            return

        mode = str(self.mode_combo.currentData() or "max_amount")
        try:
            if mode == "weighted_wheel":
                wheel_duration_ms = self._wheel_timer_ms()
                duration_ms = 0
                self._prestart_wheel_duration_ms = wheel_duration_ms
            else:
                duration_ms = self._prestart_timer_ms()
                wheel_duration_ms = int(self._prestart_wheel_duration_ms)
                self._prestart_auction_duration_ms = duration_ms
        except ValueError as exc:
            QMessageBox.warning(self, "Время", str(exc))
            self.timer_edit.setFocus()
            return

        params = {
            "mode": mode,
            "rng_method": str(self.rng_combo.currentData() or "local"),
            "wheel_duration_ms": wheel_duration_ms,
            "duration_ms": duration_ms,
            "lot_count": len(self.db.pointauc_games()),
        }

        if params["rng_method"] not in ("random_org", "random_org_plus"):
            self._confirm_and_create_auction(params, None)
            return

        api_key = self.db.get_random_org_api_key().strip()
        if not api_key:
            QMessageBox.information(
                self,
                "RANDOM.ORG",
                "Сначала укажите API key на вкладке «Настройки».",
            )
            return

        self.start_btn.setEnabled(False)
        self.start_btn.setText("Проверка RANDOM.ORG…")

        def prepare_remote_rng():
            client = RandomOrgClient(api_key)
            client.get_usage()
            if params["rng_method"] == "random_org_plus":
                return str(client.create_ticket()["ticketId"])
            return None

        worker = FunctionWorker(prepare_remote_rng)
        self._auction_rng_worker = worker
        self.refresh()
        worker.signals.result.connect(
            lambda ticket_id, p=params: self._confirm_and_create_auction(
                p,
                ticket_id,
            )
        )
        worker.signals.error.connect(self._auction_rng_failed)
        worker.signals.finished.connect(self._auction_rng_finished)
        self.thread_pool.start(worker)

    def _auction_rng_failed(self, exc):
        QMessageBox.critical(self, "RANDOM.ORG", sanitize_diagnostic_text(str(exc)))

    def _auction_rng_finished(self):
        self._auction_rng_worker = None
        self.refresh()

    def _confirm_and_create_auction(self, params: dict, rng_ticket_id: str | None):
        mode = str(params["mode"])
        rng_method = str(params["rng_method"])
        wheel_duration_ms = int(params["wheel_duration_ms"])
        duration_ms = int(params["duration_ms"])
        lot_count = int(params["lot_count"])
        direct_wheel = mode == "weighted_wheel"

        if direct_wheel:
            prompt = (
                "Запустить взвешенное колесо?\n\n"
                f"Лотов: {lot_count}\n"
                f"Режим: {self.MODE_LABELS.get(mode, mode)}\n"
                f"Генератор: {self.RNG_LABELS.get(rng_method, rng_method)}\n"
                + (f"Билет Random.org+: {rng_ticket_id}\n" if rng_ticket_id else "")
                + f"Время вращения: {self._format_milliseconds(wheel_duration_ms)}\n\n"
                "Победитель будет определён выпавшим сектором."
            )
            title = "Крутить колесо"
        else:
            prompt = (
                "Начать новый аукцион?\n\n"
                f"Лотов: {lot_count}\n"
                f"Режим: {self.MODE_LABELS.get(mode, mode)}\n"
                f"Генератор: {self.RNG_LABELS.get(rng_method, rng_method)}\n"
                + (f"Билет Random.org+: {rng_ticket_id}\n" if rng_ticket_id else "")
                + f"Длительность приёма ставок: {self._format_milliseconds(duration_ms)}\n\n"
                "После старта способ определения победителя изменить нельзя."
            )
            title = "Начать аукцион"

        answer = QMessageBox.question(
            self,
            title,
            prompt,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            auction_id = self.db.create_auction_session(
                mode,
                0 if direct_wheel else max(1, (duration_ms + 999) // 1000),
                rng_method=rng_method,
                rng_ticket_id=rng_ticket_id,
                wheel_duration_ms=wheel_duration_ms,
                duration_ms=0 if direct_wheel else duration_ms,
                start_in_wheel_mode=direct_wheel,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Аукцион", str(exc))
            return

        self._active_auction_id = auction_id
        self._pending_tie_overtime = False
        self.auction_tabs.setCurrentWidget(self.conduct_page)
        self.refresh()
        QTimer.singleShot(0, self._reset_conduct_auto_scroll)

        if direct_wheel:
            # Нажатие «Крутить» уже является явным подтверждением запуска,
            # поэтому второй диалог run_wheel здесь не нужен.
            QTimer.singleShot(0, lambda: self.run_wheel(confirm=False))

    def toggle_pause(self):
        session = self._current_session()
        if session is None:
            return
        try:
            if session["status"] == "running":
                self.db.pause_auction(int(session["id"]))
            elif session["status"] == "paused":
                self.db.resume_auction(int(session["id"]))
        except Exception as exc:
            QMessageBox.critical(self, "Аукцион", str(exc))
        self.refresh()

    def adjust_timer_minutes(self, delta_minutes: int):
        delta_minutes = int(delta_minutes)
        if delta_minutes == 0:
            return

        session = self._current_session()
        if session is None:
            if self._timer_context == "wheel":
                return
            try:
                before_ms = self._prestart_timer_ms()
            except ValueError as exc:
                QMessageBox.warning(self, "Время аукциона", str(exc))
                self.timer_edit.setFocus()
                return
            after_ms = before_ms + delta_minutes * 60_000
            self._set_prestart_timer_ms(after_ms)
            self._prestart_auction_duration_ms = self._prestart_timer_ms()
            return

        if (
            session.get("status") == "tie_break_required"
            and self._pending_tie_overtime
        ):
            try:
                before_ms = self._prestart_timer_ms()
            except ValueError as exc:
                QMessageBox.warning(self, "Дополнительное время", str(exc))
                self.timer_edit.setFocus()
                return
            self._set_prestart_timer_ms(before_ms + delta_minutes * 60_000)
            return

        if session.get("status") not in ("running", "paused"):
            return

        try:
            remaining_ms = self.db.adjust_auction_time_ms(
                int(session["id"]),
                delta_minutes * 60_000,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Аукцион", str(exc))
            return

        if remaining_ms <= 0:
            self.finish_auction(automatic=True)
            return
        self.refresh()

    def reset_auction_timer(self):
        session = self._current_session()
        if session is None:
            if self._timer_context == "wheel":
                default_ms = self._saved_wheel_default_duration_ms()
                self._default_wheel_duration_ms = default_ms
                self._prestart_wheel_duration_ms = default_ms
                self._set_wheel_timer_ms(default_ms)
            else:
                default_ms = self._saved_max_amount_default_duration_ms()
                self._default_auction_duration_ms = default_ms
                self._prestart_auction_duration_ms = default_ms
                self._set_prestart_timer_ms(default_ms)
            return

        status = str(session.get("status") or "")
        if status == "tie_break_required" and self._pending_tie_overtime:
            self._set_prestart_timer_ms(self._saved_wheel_default_duration_ms())
            return

        if status == "awaiting_wheel":
            default_ms = self._saved_wheel_default_duration_ms()
            try:
                self.db.set_auction_wheel_duration_ms(int(session["id"]), default_ms)
            except Exception as exc:
                QMessageBox.critical(self, "Колесо", str(exc))
                return
            self._set_wheel_timer_ms(default_ms)
            self.refresh()
            return

        if status not in ("running", "paused"):
            return

        duration_ms = session.get("duration_ms")
        if duration_ms is None:
            duration_ms = int(session.get("duration_seconds") or 0) * 1000
        duration_ms = max(0, int(duration_ms))
        answer = QMessageBox.question(
            self,
            "Сбросить таймер",
            "Вернуть таймер к исходной длительности "
            f"{self._format_milliseconds(duration_ms)}?\n\n"
            "Лоты и ставки не изменятся.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            self.db.reset_auction_timer_ms(int(session["id"]))
        except Exception as exc:
            QMessageBox.critical(self, "Аукцион", str(exc))
            return
        self.refresh()

    def finish_auction(self, automatic: bool = False):
        session = self._current_session()
        if session is None:
            return

        if not automatic:
            answer = QMessageBox.question(
                self,
                "Завершить приём ставок",
                "Завершить приём ставок в текущем аукционе?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        try:
            result = self.db.finish_auction(int(session["id"]))
        except Exception as exc:
            QMessageBox.critical(self, "Аукцион", str(exc))
            return

        # Timer/Auction Music belongs to the authoritative bid-intake timer.
        # Finish/expiry always fades and stops it before tie/winner handling.
        self._stop_auction_soundtrack(immediate=False)

        status = result.get("status")
        self._pending_tie_overtime = False
        if status == "awaiting_wheel":
            QMessageBox.information(
                self,
                "Аукцион",
                "Сессия готова к колесу. Задайте время вращения и нажмите «Крутить».",
            )
        elif status == "winner_selected":
            winner_id = result.get("winner_game_id")
            winner = self.db.get_game(int(winner_id)) if winner_id else None
            if winner is not None:
                QMessageBox.information(
                    self,
                    "Аукцион",
                    f"Победитель по максимальным баллам: «{winner.title}».\n"
                    "Проверьте результат и нажмите «Подтвердить победителя».",
                )
        elif status == "tie_break_required":
            self.refresh()
            self._show_tie_break_dialog()
            return
        elif status == "finished_no_winner":
            QMessageBox.warning(
                self,
                "Аукцион",
                "Победитель не определён.",
            )
            self._active_auction_id = None
            self._prepare_next_max_amount_timer()

        self.refresh()

    def _show_tie_break_dialog(self):
        session = self._current_session()
        if session is None or session.get("status") != "tie_break_required":
            return

        box = QMessageBox(self)
        box.setWindowTitle("Аукцион")
        box.setIcon(QMessageBox.Information)
        box.setText("Несколько победителей.")
        box.setInformativeText(
            "Несколько лотов набрали одинаковое максимальное количество баллов. "
            "Можно продолжить аукцион только между ними ещё некоторое "
            "время или определить победителя колесом."
        )
        overtime_btn = box.addButton(
            "Дополнительное время",
            QMessageBox.AcceptRole,
        )
        wheel_btn = box.addButton(
            "Использовать колесо",
            QMessageBox.ActionRole,
        )
        box.addButton("Позже", QMessageBox.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked is overtime_btn:
            self.start_tie_overtime()
        elif clicked is wheel_btn:
            self.use_wheel_for_tie()

    def start_tie_overtime(self):
        session = self._current_session()
        if session is None or session.get("status") != "tie_break_required":
            return

        # Сначала только переключаем большой таймер в контекст допвремени.
        # Отсчёт начинается отдельным нажатием «Старт».
        self._pending_tie_overtime = True
        self._timer_context = "auction"
        self._set_prestart_timer_ms(self._saved_wheel_default_duration_ms())
        self.auction_tabs.setCurrentWidget(self.conduct_page)
        self.refresh()
        self.timer_edit.setFocus()

    def _start_pending_tie_overtime(self):
        session = self._current_session()
        if (
            session is None
            or session.get("status") != "tie_break_required"
            or not self._pending_tie_overtime
        ):
            return
        try:
            duration_ms = self._prestart_timer_ms()
        except ValueError as exc:
            QMessageBox.warning(self, "Дополнительное время", str(exc))
            self.timer_edit.setFocus()
            return

        try:
            self.db.start_auction_tie_overtime(
                int(session["id"]),
                max(1, (duration_ms + 999) // 1000),
                duration_ms=duration_ms,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Аукцион", str(exc))
            return

        self._pending_tie_overtime = False
        self._start_auction_soundtrack_for_session(
            self._current_session(),
            restart=True,
        )
        self.conduct_search.clear()
        self.changed()
        self.auction_tabs.setCurrentWidget(self.conduct_page)
        QTimer.singleShot(0, self._reset_conduct_auto_scroll)

    def use_wheel_for_tie(self):
        session = self._current_session()
        if session is None or session.get("status") != "tie_break_required":
            return

        default_ms = self._saved_wheel_default_duration_ms()
        try:
            self.db.start_auction_tie_wheel(
                int(session["id"]),
                wheel_duration_ms=default_ms,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Аукцион", str(exc))
            return

        self._pending_tie_overtime = False
        self._default_wheel_duration_ms = default_ms
        self._prestart_wheel_duration_ms = default_ms
        self._timer_context = "wheel"
        self._set_wheel_timer_ms(default_ms)
        self.changed()
        self.auction_tabs.setCurrentWidget(self.conduct_page)
        self.refresh()
        self.timer_edit.setFocus()

    def cancel_auction(self):
        session = self._current_session()
        if session is None:
            return

        winner_selected = str(session.get("status") or "") == "winner_selected"
        if winner_selected:
            title = "Отменить аукцион"
            message = (
                "Победитель уже определён. Отменить текущую сессию и считать "
                "результат отменённым?\n\n"
                "История определения победителя останется в журнале.\n"
                "Уже добавленные ставки останутся в баллах SM игр и не будут откатаны.\n"
                "Новые временные лоты этой сессии будут перенесены в основной список."
            )
        else:
            title = "Остановить аукцион"
            message = (
                "Остановить текущую сессию без определения победителя?\n\n"
                "Уже добавленные ставки останутся в баллах SM игр и не будут откатаны.\n"
                "Новые временные лоты этой сессии будут перенесены в основной список."
            )

        answer = QMessageBox.warning(
            self,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            self.db.cancel_auction(int(session["id"]))
        except Exception as exc:
            QMessageBox.critical(self, "Аукцион", str(exc))
            return

        self._stop_auction_soundtrack(immediate=False)
        self._stop_wheel_soundtrack(immediate=True)
        self._active_auction_id = None
        self._prepare_next_max_amount_timer()
        # Отмена может перевести временные auction_only-лоты в обычные игры.
        # Сообщаем главному окну об изменении общей игровой базы: текущая
        # вкладка аукциона обновится сразу, а скрытые Игры/Публичный список/
        # Журнал будут помечены dirty и перечитают данные при открытии.
        self.changed()

    def add_new_auction_lot(self):
        session = self._current_session()
        if session is None or session.get("status") != "running":
            QMessageBox.information(
                self,
                "Новый лот",
                "Новый лот можно добавить только во время приёма ставок.",
            )
            return

        title = self.new_lot_title.text().strip()
        if not title:
            QMessageBox.information(
                self,
                "Новый лот",
                "Введите название лота.",
            )
            return

        points = int(self.new_lot_points.value())
        try:
            result = self.db.add_or_increment_auction_lot(
                int(session["id"]),
                title,
                points,
                source="manual_new_lot",
                contributor="Ручное добавление",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Новый лот", str(exc))
            return

        # Очищаем inline-строку только после успешной операции. Ошибка оставляет
        # введённые данные на месте, чтобы оператор мог их исправить.
        self.new_lot_title.clear()
        self.new_lot_points.setValue(0)

        # Новый временный лот не должен появляться в основных таблицах,
        # поэтому обновляем именно аукцион и его колесо.
        self.refresh()
        self.select_conduct_game_id(int(result["game_id"]))

        if result.get("merged"):
            QMessageBox.information(
                self,
                "Новый лот",
                "Лот с таким названием уже участвовал в аукционе. "
                "Указанные баллы добавлены к существующему лоту.",
            )

    def add_manual_bid(self):
        session = self._current_session()
        if session is None or session.get("status") != "running":
            QMessageBox.information(
                self,
                "Аукцион",
                "Сначала запустите аукцион.",
            )
            return

        game_id = self.selected_conduct_game_id()
        if game_id is None:
            QMessageBox.information(
                self,
                "Аукцион",
                "Выберите лот на вкладке «Проведение».",
            )
            return

        points = int(self.bid_amount.value())
        try:
            self.db.set_auction_manual_bid_points(points)
            self.db.add_auction_bid(
                int(session["id"]),
                game_id,
                points,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Аукцион", str(exc))
            return

        # Баллы SM изменились в единой базе — немедленно обновляем все связанные
        # списки. OBS и отдельный список читают те же данные через локальный API.
        self.changed()
        self.select_conduct_game_id(game_id)

        # После успешной ставки ручная операция закончена — автопрокрутка может
        # снова продолжиться, при этом выделение лота сохраняется.
        self.conduct_table.clearFocus()
        self.bid_amount.clearFocus()
        self.add_bid_btn.clearFocus()
        self.decrease_bid_btn.clearFocus()

    def decrease_manual_bid(self):
        session = self._current_session()
        if session is None or session.get("status") != "running":
            QMessageBox.information(
                self,
                "Аукцион",
                "Сначала запустите аукцион.",
            )
            return

        game_id = self.selected_conduct_game_id()
        if game_id is None:
            QMessageBox.information(
                self,
                "Аукцион",
                "Выберите лот на вкладке «Проведение».",
            )
            return

        points = int(self.bid_amount.value())
        try:
            self.db.set_auction_manual_bid_points(points)
            self.db.decrease_auction_bid(
                int(session["id"]),
                game_id,
                points,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Аукцион", str(exc))
            return

        self.changed()
        self.select_conduct_game_id(game_id)

        self.conduct_table.clearFocus()
        self.bid_amount.clearFocus()
        self.add_bid_btn.clearFocus()
        self.decrease_bid_btn.clearFocus()

    def delete_temporary_lot(self):
        session = self._current_session()
        if session is None or session.get("status") != "running":
            QMessageBox.information(
                self,
                "Удалить лот",
                "Удалить временный лот можно только во время приёма ставок.",
            )
            return

        game_id = self.selected_conduct_game_id()
        if game_id is None:
            QMessageBox.information(
                self,
                "Удалить лот",
                "Выберите временный лот на вкладке «Проведение».",
            )
            return
        if not self._selected_conduct_is_temporary_lot():
            QMessageBox.information(
                self,
                "Удалить лот",
                "Удалить можно только временный лот, созданный в текущем аукционе.",
            )
            return

        row = self.conduct_table.currentRow()
        title_item = self.conduct_table.item(row, 2) if row >= 0 else None
        title = title_item.text().strip() if title_item is not None else str(game_id)
        answer = QMessageBox.warning(
            self,
            "Удалить временный лот?",
            f"Удалить временный лот «{title}» из текущего аукциона?\n\n"
            "Он не будет перенесён в основной список после завершения или "
            "отмены аукциона. История создания и удаления останется в журнале.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            self.db.delete_temporary_auction_lot(
                int(session["id"]),
                game_id,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Удалить лот", str(exc))
            return

        # Удалённый temporary game больше не существует. Обычные списки его и
        # раньше не показывали, но журнал и текущий аукцион должны немедленно
        # получить dirty/update через общий проверенный путь.
        self.changed()
        self.conduct_table.clearFocus()
        self.delete_lot_btn.clearFocus()

    def export_pointauc(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт Pointauc",
            "pointauc.csv",
            "CSV (*.csv);;Все файлы (*.*)",
        )
        if not path:
            return
        try:
            export_pointauc_csv(self.db, path)
            QMessageBox.information(self, "Pointauc", f"Список сохранён:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))

    def copy_pointauc(self):
        QApplication.clipboard().setText(pointauc_text(self.db))
        QMessageBox.information(
            self,
            "Pointauc",
            "Список скопирован в буфер обмена.",
        )
