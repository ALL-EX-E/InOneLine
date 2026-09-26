from __future__ import annotations

import hashlib
import math
import time
from datetime import datetime, timedelta, timezone
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QDialogButtonBox, QLabel, QTabWidget, QTextEdit, QVBoxLayout, QWidget

from ...app_paths import AppPaths
from ...database import format_points, normalize_text_key
from ...diagnostic_logs import append_performance_trace
from ...exporters import export_pointauc_csv, pointauc_text
from ...random_sources import RandomDraw, RandomOrgClient
from ...workers import FunctionWorker


class AuctionStateMixin:
    def refresh(self):
        if not getattr(self, "_main_tab_visible", True):
            self._refresh_pending = True
            return
        self._refresh_visible_state()

    def refresh_force(self):
        """Explicit user refresh may rebuild Auction even while its tab is hidden."""
        self._refresh_visible_state()

    @staticmethod
    def _set_timer_running(timer, should_run: bool) -> None:
        """Start/stop a QTimer only when its desired state actually changes."""
        if bool(should_run):
            if not timer.isActive():
                timer.start()
        elif timer.isActive():
            timer.stop()

    def _sync_auction_timer_activity(self, session: dict | None) -> None:
        # The 500-ms timer is functional (automatic deadline completion and
        # live leader refresh), so it must keep running while an auction is
        # open even when the Auction tab is hidden.  With no open session it
        # has no work and should not wake the GUI/SQLite twice per second.
        timer = getattr(self, "auction_timer", None)
        if timer is not None:
            self._set_timer_running(timer, session is not None)

    def _sync_timer_display_activity(self) -> None:
        # The precise 25-ms timer is presentation-only. Paused/prestart/empty
        # states are static and do not need 40 Python callbacks per second.
        timer = getattr(self, "timer_display_timer", None)
        if timer is None:
            return
        should_run = bool(
            getattr(self, "_main_tab_visible", True)
            and (
                self._timer_display_kind == "wheel"
                or (
                    self._timer_display_kind == "auction"
                    and self._timer_display_status == "running"
                )
            )
        )
        self._set_timer_running(timer, should_run)

    def _refresh_visible_state(self):
        started = time.perf_counter()
        self._refresh_pending = False
        selected_id = self.selected_game_id()
        conduct_selected_id = self.selected_conduct_game_id()
        session = self._current_session()
        self._sync_auction_timer_activity(session)

        # Если приложение было закрыто до истечения таймера, при следующем
        # обновлении автоматически завершаем приём ставок.
        if (
            session is not None
            and session.get("status") == "running"
            and self.db.auction_remaining_milliseconds(int(session["id"])) <= 0
        ):
            self.db.finish_auction(int(session["id"]))
            self._stop_auction_soundtrack(immediate=False)
            session = self.db.get_open_auction_session()
            self._sync_auction_timer_activity(session)
            self._active_auction_id = int(session["id"]) if session else None

        all_rows = self._entries_for_table(session)
        wheel_payload = (
            self._load_wheel_payload(session)
            if self._wheel_context_relevant(session)
            else {}
        )
        wheel_probabilities = self._wheel_probability_map(
            wheel_payload
            if self._weighted_wheel_chance_context(session)
            else {}
        )
        db_seconds = time.perf_counter() - started

        # Основной поиск вкладки «Лоты» синхронизирован с первыми двумя
        # основными вкладками программы.
        query = normalize_text_key(self.search.text())
        rows = all_rows
        if query:
            rows = [
                row for row in all_rows
                if query in normalize_text_key(row["title"])
            ]

        self.count_label.setText(f"Лотов: {len(rows)}")
        lots_started = time.perf_counter()
        lots_timing = self._populate_lot_table(
            self.table,
            rows,
            selected_id,
        )
        lots_seconds = time.perf_counter() - lots_started

        # На «Проведение» — отдельный локальный поиск по текущим лотам.
        conduct_query = normalize_text_key(self.conduct_search.text())
        conduct_rows = all_rows
        if conduct_query:
            conduct_rows = [
                row for row in all_rows
                if conduct_query in normalize_text_key(row["title"])
            ]

        conduct_started = time.perf_counter()
        conduct_timing = self._populate_lot_table(
            self.conduct_table,
            conduct_rows,
            conduct_selected_id,
            wheel_probabilities=wheel_probabilities,
        )
        conduct_seconds = time.perf_counter() - conduct_started

        controls_started = time.perf_counter()
        self._update_session_controls(
            session,
            all_rows,
            wheel_payload=wheel_payload,
        )
        self._sync_auction_bets(session)
        self._sync_auction_history(session)
        controls_seconds = time.perf_counter() - controls_started
        try:
            append_performance_trace(
                AppPaths.from_database_path(self.db.path).logs_dir,
                "AUCTION_REFRESH "
                f"rows={len(all_rows)} db={db_seconds:.3f}s "
                f"lots={lots_seconds:.3f}s "
                f"lots_fill={lots_timing['fill']:.3f}s "
                f"lots_autosize={lots_timing['autosize']:.3f}s "
                f"lots_reactivate={lots_timing['reactivate']:.3f}s "
                f"conduct={conduct_seconds:.3f}s "
                f"conduct_fill={conduct_timing['fill']:.3f}s "
                f"conduct_autosize={conduct_timing['autosize']:.3f}s "
                f"conduct_reactivate={conduct_timing['reactivate']:.3f}s "
                f"controls={controls_seconds:.3f}s "
                f"total={time.perf_counter()-started:.3f}s",
            )
        except Exception:
            pass

    def _sync_session_state_without_table_rebuild(self) -> None:
        """Catch up controls/timer on a clean tab return without rebuilding rows."""
        session = self._current_session()
        self._sync_auction_timer_activity(session)
        if (
            session is not None
            and session.get("status") == "running"
            and self.db.auction_remaining_milliseconds(int(session["id"])) <= 0
        ):
            self.db.finish_auction(int(session["id"]))
            self._stop_auction_soundtrack(immediate=False)
            self._refresh_visible_state()
            return
        self._update_session_controls(session)
        self._refresh_conduct_wheel_chances_in_place(session)
        self._sync_auction_history(session)

    def _update_session_controls(
        self,
        session: dict | None,
        all_rows=None,
        wheel_payload: dict | None = None,
    ):
        active = session is not None
        status = str(session["status"]) if active else ""
        mode = str(session["mode"]) if active else ""

        running = status == "running"
        paused = status == "paused"
        awaiting_wheel = status == "awaiting_wheel"
        winner_selected = status == "winner_selected"
        tie_break_required = status == "tie_break_required"
        pending_overtime = bool(
            tie_break_required and self._pending_tie_overtime
        )

        spin_running = bool(
            winner_selected
            and session
            and session.get("wheel_spin_id")
            and not self._wheel_spin_complete(session)
        )

        preparing_rng = self._auction_rng_worker is not None
        preparing_wheel_rng = self._wheel_rng_worker is not None
        prestart_enabled = (not active) and not preparing_rng
        prestart_wheel = bool(
            not active
            and str(self.mode_combo.currentData() or "") == "weighted_wheel"
        )

        self._set_enabled_state(self.mode_combo, prestart_enabled)
        self._set_enabled_state(self.rng_combo, prestart_enabled)
        self._set_enabled_state(self.rng_methods_btn, prestart_enabled)
        self._set_visible_state(self.setup_widget, not active)
        self._set_visible_state(self.state_widget, active)

        if awaiting_wheel or spin_running:
            self._timer_context = "wheel"
        elif running or paused or pending_overtime:
            self._timer_context = "auction"

        # 9.3: единый большой таймер остаётся на экране всегда. После выбора
        # победителя он служит точкой доступа к отмене завершённого результата.
        timer_visible = True
        self._set_visible_state(self.timer_widget, True)

        timer_editable = bool(
            ((not active) and not preparing_rng)
            or pending_overtime
            or (awaiting_wheel and not preparing_wheel_rng)
        )
        self.timer_edit.setReadOnly(not timer_editable)
        self.timer_edit.setEnabled(timer_visible and not preparing_rng)

        timer_action_visible = bool(
            (not active)
            or running
            or paused
            or pending_overtime
            or awaiting_wheel
        )
        self._set_visible_state(self.start_btn, timer_action_visible)
        self._set_enabled_state(
            self.start_btn,
            timer_action_visible
            and not preparing_rng
            and not preparing_wheel_rng,
        )
        if not preparing_rng and not preparing_wheel_rng:
            if paused:
                self.start_btn.setText("Продолжить")
            elif running:
                self.start_btn.setText("Пауза")
            elif awaiting_wheel or prestart_wheel:
                self.start_btn.setText("Крутить")
            else:
                self.start_btn.setText("Старт")

        auction_adjust_context = bool(
            running
            or paused
            or pending_overtime
            or ((not active) and not prestart_wheel)
        )
        timer_adjust_enabled = bool(
            auction_adjust_context
            and not preparing_rng
            and not preparing_wheel_rng
        )
        for timer_button in (
            self.timer_minus10_btn,
            self.timer_minus_btn,
            self.timer_plus_btn,
            self.timer_plus10_btn,
        ):
            self._set_visible_state(timer_button, auction_adjust_context)
            self._set_enabled_state(timer_button, timer_adjust_enabled)

        reset_visible = bool(
            (not active)
            or running
            or paused
            or pending_overtime
            or awaiting_wheel
        )
        self._set_visible_state(self.timer_reset_btn, reset_visible)
        self._set_enabled_state(
            self.timer_reset_btn,
            reset_visible
            and not preparing_rng
            and not preparing_wheel_rng,
        )

        self._set_visible_state(self.finish_btn, running or paused)
        self._set_enabled_state(self.finish_btn, running or paused)

        can_cancel = active and status in self.db.AUCTION_OPEN_STATUSES
        self._set_visible_state(self.cancel_btn, can_cancel)
        self._set_enabled_state(self.cancel_btn, can_cancel)
        self._set_visible_state(
            self.timer_finish_widget,
            (running or paused) or can_cancel,
        )

        can_confirm = winner_selected and not spin_running
        self._set_visible_state(self.confirm_btn, can_confirm)
        self._set_enabled_state(self.confirm_btn, can_confirm)

        self._set_visible_state(
            self.tie_overtime_btn,
            tie_break_required and not pending_overtime,
        )
        self._set_enabled_state(
            self.tie_overtime_btn,
            tie_break_required and not pending_overtime,
        )
        # Пока пользователь настраивает допвремя, возможность вместо него
        # перейти к колесу остаётся доступной.
        self._set_visible_state(self.tie_wheel_btn, tie_break_required)
        self._set_enabled_state(self.tie_wheel_btn, tie_break_required)

        ticket_id = session.get("rng_ticket_id") if active else None
        signed_proof = bool(
            active
            and session.get("rng_random_json")
            and session.get("rng_signature")
        )
        self._set_visible_state(self.copy_ticket_btn, bool(ticket_id))
        self._set_enabled_state(self.copy_ticket_btn, bool(ticket_id))
        self._set_visible_state(self.verify_rng_btn, signed_proof)
        self._set_enabled_state(self.verify_rng_btn, signed_proof)

        has_actions = any((
            can_confirm, tie_break_required, bool(ticket_id), signed_proof,
        ))
        self._set_visible_state(self.session_buttons_widget, has_actions)

        # Ручные ставки существуют только в реальном периоде приёма ставок.
        self._set_visible_state(self.bid_widget, running)
        self._set_enabled_state(self.add_bid_btn, running)
        self._set_enabled_state(self.decrease_bid_btn, running)
        self._set_enabled_state(self.bid_amount, running)
        self._update_delete_lot_action_state(running=running)

        self._set_visible_state(self.new_lot_widget, running)
        self._set_enabled_state(self.new_lot_title, running)
        self._set_enabled_state(self.new_lot_points, running)
        self._set_enabled_state(self.new_lot_btn, running)

        self._sync_wheel_chance_visibility(session)
        self._update_wheel_panel(session, wheel_payload=wheel_payload)
        self._update_auction_soundtrack_panel(session)
        self._update_winner_chance_display(
            session,
            spin_running=spin_running,
            wheel_payload=wheel_payload,
        )
        self._sync_timer_display_state(session)
        self._update_auction_total_display(session)

        if not active:
            self.state_label.setText("Состояние: НЕТ АКТИВНОГО АУКЦИОНА")
            self.mode_label.setText("Режим: —")
            self.rng_label.setText("RNG: —")
            self.time_label.setText("Осталось: —")
            self.leader_label.setText("Лидер: —")
            return

        self.state_label.setText(
            f"Состояние: {self.STATUS_LABELS.get(status, status)}"
        )
        if awaiting_wheel and mode == "max_amount":
            self.mode_label.setText(
                "Режим: Максимальная сумма → Колесо (тай-брейк)"
            )
        else:
            self.mode_label.setText(
                f"Режим: {self.MODE_LABELS.get(mode, mode)}"
            )

        rng_method = str(session.get("rng_method") or "local")
        rng_text = self.RNG_LABELS.get(rng_method, rng_method)
        if session.get("rng_ticket_id"):
            rng_text += f" | билет: {session['rng_ticket_id']}"
        if session.get("rng_serial_number") is not None:
            rng_text += f" | № {session['rng_serial_number']}"
        self.rng_label.setText(f"RNG: {rng_text}")

        if status in ("running", "paused"):
            remaining_ms = self._timer_display_remaining_ms()
            formatted = self._format_milliseconds(remaining_ms)
            self.timer_edit.setText(formatted)
            self.time_label.setText(f"Осталось: {formatted}")
        elif awaiting_wheel:
            wheel_ms = int(session.get("wheel_duration_ms") or 8000)
            formatted = self._format_milliseconds(wheel_ms)
            if not self.timer_edit.hasFocus():
                self.timer_edit.setText(formatted)
            self.time_label.setText(f"Вращение: {formatted}")
        elif spin_running:
            remaining_ms = self._timer_display_remaining_ms()
            formatted = self._format_milliseconds(remaining_ms)
            self.timer_edit.setText(formatted)
            self.time_label.setText(f"Вращение: {formatted}")
        elif pending_overtime:
            self.time_label.setText("Доп. время: задайте таймер")
        elif winner_selected:
            formatted = self._format_milliseconds(0)
            self.timer_edit.setText(formatted)
            if session.get("wheel_spin_id"):
                self.time_label.setText(f"Вращение: {formatted}")
            else:
                self.time_label.setText(f"Осталось: {formatted}")
        else:
            self.time_label.setText("Осталось: —")

        if all_rows is None:
            all_rows = self.db.list_auction_entries(int(session["id"]))
        if all_rows:
            leader = all_rows[0]
            self.leader_label.setText(
                f"Лидер: {leader['title']} — "
                f"{format_points(int(leader['total_sm_points']))}"
            )
        else:
            self.leader_label.setText("Лидер: —")

        if winner_selected:
            if spin_running:
                self.state_label.setText("Состояние: КОЛЕСО ВРАЩАЕТСЯ")
                self.leader_label.setText("Победитель определяется…")
            else:
                winner_id = session.get("winner_game_id")
                winner = self.db.get_game(int(winner_id)) if winner_id else None
                if winner is not None:
                    self.leader_label.setText(
                        f"Победитель: {winner.title} — "
                        f"{format_points(winner.sm_points)}"
                    )

    def _update_winner_chance_display(
        self,
        session: dict | None,
        *,
        spin_running: bool,
        wheel_payload: dict | None = None,
    ) -> None:
        """W4: show the frozen winner chance only after a direct weighted spin."""
        applicable = bool(
            session
            and str(session.get("mode") or "") == "weighted_wheel"
            and str(session.get("status") or "") == "winner_selected"
            and not spin_running
        )
        self._set_visible_state(self.winner_chance_label, applicable)
        if not applicable:
            self.winner_chance_label.setText("")
            return

        payload = (
            self._load_wheel_payload(session)
            if wheel_payload is None
            else wheel_payload
        )
        chance = ((payload or {}).get("winner") or {}).get("chance")
        if not chance or not bool(chance.get("available")):
            self.winner_chance_label.setText(
                "Шанс победителя в этом вращении: недоступен"
            )
            return
        probability = chance.get("probability")
        if probability is None:
            self.winner_chance_label.setText(
                "Шанс победителя в этом вращении: недоступен"
            )
            return
        self.winner_chance_label.setText(
            "Шанс победителя в этом вращении: "
            f"{self._format_wheel_probability(float(probability))}"
        )

    def _update_auction_total_display(self, session: dict | None) -> None:
        """Refresh the always-visible A6 total without mutating auction state."""
        if session is None:
            total = sum(
                max(0, int(game.sm_points))
                for game in self.db.pointauc_games()
            )
        else:
            total = self.db.auction_total_sm_points(int(session["id"]))
        formatted = f"{int(total):,}".replace(",", " ")
        self.auction_total_label.setText(f"Всего: {formatted} баллов")

    @staticmethod
    def _wheel_spin_complete(session: dict | None) -> bool:
        if not session or not session.get("wheel_spin_id"):
            return True
        started_at = session.get("wheel_started_at")
        duration_ms = int(session.get("wheel_duration_ms") or 8000)
        if not started_at:
            return True
        try:
            start = datetime.fromisoformat(str(started_at))
            return datetime.now(timezone.utc) >= (
                start + timedelta(milliseconds=duration_ms)
            )
        except (TypeError, ValueError):
            return True

    def _weighted_wheel_chance_context(self, session: dict | None) -> bool:
        """A6.1 is relevant only for the real weighted_wheel mode."""
        if session is None:
            return (
                str(self.mode_combo.currentData() or "")
                == "weighted_wheel"
            )
        return str(session.get("mode") or "") == "weighted_wheel"

    def _sync_wheel_chance_visibility(self, session: dict | None) -> None:
        weighted = self._weighted_wheel_chance_context(session)
        self._set_visible_state(self.wheel_chance_checkbox, weighted)
        self.conduct_table.setColumnHidden(
            3,
            not (weighted and self._wheel_chance_visible),
        )

    def _refresh_conduct_wheel_chances_in_place(
        self,
        session: dict | None,
        wheel_payload: dict | None = None,
    ) -> None:
        """Refresh only A6.1 chance cells without rebuilding Conduct rows."""
        if not self._weighted_wheel_chance_context(session):
            return

        payload = (
            self._load_wheel_payload(session)
            if wheel_payload is None
            else wheel_payload
        )
        probabilities = self._wheel_probability_map(payload)
        for row_index in range(self.conduct_table.rowCount()):
            id_item = self.conduct_table.item(row_index, 0)
            chance_item = self.conduct_table.item(row_index, 3)
            if id_item is None or chance_item is None:
                continue
            try:
                game_id = int(id_item.data(Qt.UserRole))
            except (TypeError, ValueError):
                continue
            chance_item.setText(
                self._format_wheel_probability(
                    probabilities.get(game_id, 0.0)
                )
            )

    @staticmethod
    def _wheel_probability_map(payload: dict | None) -> dict[int, float]:
        result: dict[int, float] = {}
        for sector in (payload or {}).get("sectors", []):
            try:
                result[int(sector["game_id"])] = float(
                    sector.get("probability") or 0.0
                )
            except (KeyError, TypeError, ValueError):
                continue
        return result

    def _wheel_context_relevant(self, session: dict | None) -> bool:
        if session is None:
            return (
                str(self.mode_combo.currentData() or "")
                == "weighted_wheel"
            )

        status = str(session.get("status") or "")
        mode = str(session.get("mode") or "")
        return (
            mode == "weighted_wheel"
            or status == "awaiting_wheel"
            or bool(session.get("wheel_spin_id"))
        )

    def _load_wheel_payload(self, session: dict | None) -> dict:
        try:
            if session is None:
                return self.db.current_wheel_payload()
            return self.db.wheel_payload(int(session["id"]))
        except Exception:
            return {}

    def _update_wheel_panel(
        self,
        session: dict | None,
        wheel_payload: dict | None = None,
    ):
        show = self._wheel_context_relevant(session)
        self._set_visible_state(self.wheel_panel, show)
        self._set_visible_state(self.wheel_obs_widget, show)

        if not show:
            self.wheel_widget.set_payload({})
            return

        payload = (
            self._load_wheel_payload(session)
            if wheel_payload is None
            else wheel_payload
        )
        self.wheel_widget.set_payload(payload or {})
        self._refresh_wheel_soundtrack_availability()
        self._set_wheel_soundtrack_edit_enabled(not self.wheel_widget.is_spinning())


    def _sync_timer_display_state(self, session: dict | None) -> None:
        self._timer_display_deadline = None
        self._timer_display_wheel_start = None
        self._timer_display_wheel_duration_ms = 0
        self._timer_display_kind = ""

        if session is None:
            self._timer_display_session_id = None
            self._timer_display_status = ""
            self._timer_display_paused_ms = 0
            self._timer_expiry_handled_id = None
            self._sync_timer_display_activity()
            return

        session_id = int(session["id"])
        status = str(session.get("status") or "")
        self._timer_display_session_id = session_id
        self._timer_display_status = status

        spin_running = bool(
            status == "winner_selected"
            and session.get("wheel_spin_id")
            and not self._wheel_spin_complete(session)
        )
        if spin_running:
            self._timer_display_kind = "wheel"
            duration_ms = int(session.get("wheel_duration_ms") or 8000)
            self._timer_display_wheel_duration_ms = max(0, duration_ms)
            started_at = session.get("wheel_started_at")
            if started_at:
                try:
                    start = datetime.fromisoformat(str(started_at))
                    self._timer_display_wheel_start = start
                    self._timer_display_deadline = start + timedelta(
                        milliseconds=duration_ms
                    )
                except (TypeError, ValueError):
                    self._timer_display_wheel_start = None
                    self._timer_display_deadline = None
            self._timer_display_paused_ms = duration_ms
            self._timer_expiry_handled_id = None
            self._sync_timer_display_activity()
            return

        if status == "paused":
            self._timer_display_kind = "auction"
            stored_ms = session.get("remaining_ms")
            if stored_ms is None:
                stored_ms = int(session.get("remaining_seconds") or 0) * 1000
            self._timer_display_paused_ms = max(0, int(stored_ms))
        elif status == "running":
            self._timer_display_kind = "auction"
            deadline_raw = session.get("deadline_at")
            if deadline_raw:
                try:
                    self._timer_display_deadline = datetime.fromisoformat(
                        str(deadline_raw)
                    )
                except (TypeError, ValueError):
                    self._timer_display_deadline = None
            stored_ms = session.get("remaining_ms")
            if stored_ms is None:
                stored_ms = int(session.get("remaining_seconds") or 0) * 1000
            self._timer_display_paused_ms = max(0, int(stored_ms))
        else:
            self._timer_display_paused_ms = 0

        if status != "running":
            self._timer_expiry_handled_id = None
        self._sync_timer_display_activity()

    def _timer_display_remaining_ms(self) -> int:
        if self._timer_display_kind == "wheel":
            duration_ms = max(0, int(self._timer_display_wheel_duration_ms))
            start = self._timer_display_wheel_start
            deadline = self._timer_display_deadline
            if start is None or deadline is None:
                return duration_ms
            now = datetime.now(timezone.utc)
            # prepare_wheel_animation() имеет короткий lead-in. До фактического
            # старта показываем полную заданную длительность, а не duration+lead-in.
            if now < start:
                return duration_ms
            milliseconds = (deadline - now).total_seconds() * 1000.0
            return max(0, math.ceil(milliseconds))

        if self._timer_display_status == "paused":
            return max(0, int(self._timer_display_paused_ms))
        if self._timer_display_kind != "auction" or self._timer_display_status != "running":
            return 0
        deadline = self._timer_display_deadline
        if deadline is None:
            return max(0, int(self._timer_display_paused_ms))
        milliseconds = (deadline - datetime.now(timezone.utc)).total_seconds() * 1000.0
        return max(0, math.ceil(milliseconds))

    def _tick_timer_display(self):
        if self._timer_display_kind not in ("auction", "wheel"):
            return

        remaining_ms = self._timer_display_remaining_ms()
        formatted = self._format_milliseconds(remaining_ms)
        self.timer_edit.setText(formatted)
        if self._timer_display_kind == "wheel":
            self.time_label.setText(f"Вращение: {formatted}")
            return

        self.time_label.setText(f"Осталось: {formatted}")
        if (
            self._timer_display_status == "running"
            and remaining_ms <= 0
            and self._timer_display_session_id is not None
            and self._timer_expiry_handled_id != self._timer_display_session_id
        ):
            auction_id = int(self._timer_display_session_id)
            self._timer_expiry_handled_id = auction_id
            QTimer.singleShot(
                0,
                lambda aid=auction_id: self._finish_expired_timer(aid),
            )

    def _finish_expired_timer(self, auction_id: int) -> None:
        session = self._current_session()
        if (
            session is None
            or int(session["id"]) != int(auction_id)
            or session.get("status") != "running"
        ):
            return
        if self.db.auction_remaining_milliseconds(auction_id) <= 0:
            self.finish_auction(automatic=True)

    def _tick_auction(self):
        # Вращение имеет собственный высокоточный кадровый таймер.
        # Пока оно идёт, не трогаем SQLite, labels, action controls и колесо
        # через 500-мс auction_timer: даже короткие операции в GUI-потоке
        # заметно нарушали равномерность кадров.
        if self.wheel_widget.is_spinning():
            return

        session = self._current_session()

        # 500-мс таймер остаётся функциональным даже при скрытой основной
        # вкладке: deadline_at должен завершить running-сессию вовремя.
        if session is not None and session.get("status") == "running":
            remaining_ms = self.db.auction_remaining_milliseconds(
                int(session["id"])
            )
            if remaining_ms <= 0:
                self.finish_auction(automatic=True)
                return

        # Всё ниже — только визуальная синхронизация скрытого AuctionTab.
        # Она откладывается до возвращения пользователя на основную вкладку.
        if not getattr(self, "_main_tab_visible", True):
            return

        if session is None:
            self._update_wheel_panel(None)
            return

        # Лидер может измениться из будущих внешних интеграций без действий UI.
        self._update_session_controls(session)

    def _handle_local_wheel_spin_finished(self):
        # Здесь можно снова выполнять обычные запросы/перерисовку.
        # Обновляем ровно один раз: раскрываем победителя и кнопку подтверждения.
        self.refresh()
