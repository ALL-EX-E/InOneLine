from __future__ import annotations

import hashlib
import json
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QDialogButtonBox, QLabel, QTabWidget, QTextEdit, QVBoxLayout, QWidget

from ...database import format_points
from ...exporters import export_pointauc_csv, pointauc_text
from ...random_sources import RandomDraw, RandomOrgClient
from ...workers import FunctionWorker
from ..winner_verification import format_verification_preview, show_readonly_text_dialog


class AuctionRngMixin:
    def _random_org_client(self) -> RandomOrgClient:
        return RandomOrgClient(
            self.db.get_random_org_api_key(),
        )

    @staticmethod
    def _rng_user_data(auction_id: int, draw_info: dict) -> dict:
        snapshot = "|".join(
            f"{game_id}:{weight}"
            for game_id, weight in draw_info["weighted"]
        )
        return {
            "streamingManagerAuctionId": int(auction_id),
            "drawUpper": int(draw_info["draw_upper"]),
            "lotCount": len(draw_info["weighted"]),
            "lotWeightsSha256": hashlib.sha256(
                snapshot.encode("utf-8")
            ).hexdigest(),
        }

    def run_wheel(self, confirm: bool = True):
        if self._wheel_rng_worker is not None:
            return

        session = self._current_session()
        if session is None or session.get("status") != "awaiting_wheel":
            return

        try:
            wheel_duration_ms = self._wheel_timer_ms()
            self.db.set_auction_wheel_duration_ms(
                int(session["id"]),
                wheel_duration_ms,
            )
            session = self.db.get_auction_session(int(session["id"])) or session
        except ValueError as exc:
            QMessageBox.warning(self, "Время вращения", str(exc))
            self.timer_edit.setFocus()
            return
        except Exception as exc:
            QMessageBox.critical(self, "Колесо", str(exc))
            return

        rng_method = str(session.get("rng_method") or "local")
        if session.get("mode") == "max_amount":
            wheel_text = (
                "Определить победителя колесом между лотами с одинаковой "
                "максимальным количеством баллов?\n\nВсе оставшиеся лоты имеют равный шанс."
            )
        else:
            wheel_text = (
                "Определить победителя взвешенным случайным выбором?\n\n"
                "Шанс каждого лота пропорционален его текущим баллам SM; "
                "лот с 0 баллов участвует с минимальным весом 1."
            )
        wheel_text += (
            "\n\nГенератор: "
            + self.RNG_LABELS.get(rng_method, rng_method)
            + "\nВремя вращения: "
            + self._format_milliseconds(wheel_duration_ms)
        )

        if confirm:
            answer = QMessageBox.question(
                self,
                "Крутить колесо",
                wheel_text,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        try:
            auction_id = int(session["id"])
            draw_info = self.db.get_wheel_draw_info(auction_id)
        except Exception as exc:
            QMessageBox.critical(self, "Колесо", str(exc))
            return

        if rng_method == "local":
            self._apply_wheel_draw(auction_id, None)
            return

        api_key = self.db.get_random_org_api_key().strip()
        if not api_key:
            QMessageBox.information(
                self,
                "RANDOM.ORG",
                "Сначала укажите API key на вкладке «Настройки».",
            )
            return

        signed = rng_method == "random_org_plus"
        ticket_id = str(session.get("rng_ticket_id") or "") if signed else None
        user_data = self._rng_user_data(auction_id, draw_info) if signed else None

        self.start_btn.setEnabled(False)
        self.start_btn.setText("Получение случайного числа…")

        def request_draw():
            return RandomOrgClient(api_key).draw_below(
                int(draw_info["draw_upper"]),
                signed=signed,
                ticket_id=ticket_id,
                user_data=user_data,
            )

        worker = FunctionWorker(request_draw)
        self._wheel_rng_worker = worker
        self._update_session_controls(self._current_session())
        worker.signals.result.connect(
            lambda draw, aid=auction_id: self._apply_wheel_draw(aid, draw)
        )
        worker.signals.error.connect(self._wheel_rng_failed)
        worker.signals.finished.connect(self._wheel_rng_finished)
        self.thread_pool.start(worker)

    def _apply_wheel_draw(self, auction_id: int, draw: RandomDraw | None):
        try:
            if draw is None:
                self.db.run_weighted_wheel(auction_id)
            else:
                self.db.run_weighted_wheel(
                    auction_id,
                    pick=draw.value,
                    rng_metadata=draw.metadata(),
                )
            wheel_payload = self.db.prepare_wheel_animation(auction_id)
        except Exception as exc:
            QMessageBox.critical(self, "Колесо", str(exc))
            return

        # Audio uses the exact same authoritative wheel_started_at/duration as
        # the visual animation.  Any audio failure is contained by W3 and must
        # never alter the already-fixed winner/RNG lifecycle.
        self._schedule_wheel_soundtrack(wheel_payload)

        # Победитель уже математически зафиксирован, но интерфейс и OBS
        # раскрывают его только после завершения синхронной анимации.
        self.refresh()
        self.auction_tabs.setCurrentWidget(self.conduct_page)

    def _wheel_rng_failed(self, exc):
        QMessageBox.critical(self, "Колесо", str(exc))

    def _wheel_rng_finished(self):
        self._wheel_rng_worker = None
        self._update_session_controls(self._current_session())

    def copy_rng_ticket(self):
        session = self._current_session()
        ticket_id = str(session.get("rng_ticket_id") or "") if session else ""
        if not ticket_id:
            return
        QApplication.clipboard().setText(ticket_id)
        QMessageBox.information(
            self,
            "Random.org+",
            f"Билет скопирован:\n{ticket_id}",
        )

    def open_rng_verification(self):
        session = self._current_session()
        if not session:
            return
        try:
            random_json = session.get("rng_random_json")
            signature = session.get("rng_signature")
            if not random_json or not signature:
                raise RuntimeError("У текущего результата нет подписанного доказательства.")
            draw = RandomDraw(
                value=int(session.get("rng_value") or 0),
                method="random_org_plus",
                serial_number=session.get("rng_serial_number"),
                ticket_id=session.get("rng_ticket_id"),
                random_object=json.loads(str(random_json)),
                signature=str(signature),
                verified=bool(session.get("rng_verified")),
            )
            url = draw.verification_url()
            if not url:
                raise RuntimeError("Не удалось сформировать ссылку проверки.")
            QDesktopServices.openUrl(QUrl(url))
        except Exception as exc:
            QMessageBox.critical(self, "Random.org+", str(exc))

    def show_pre_spin_verification(self):
        """Show read-only mathematical inputs without RNG, network or DB writes."""
        session = self._current_session()
        try:
            if session is not None and str(session.get("status") or "") == "awaiting_wheel":
                preview = self.db.preview_wheel_verification_data(
                    int(session["id"]),
                    mode=str(session.get("mode") or "weighted_wheel"),
                    rng_method=str(session.get("rng_method") or "local"),
                )
            elif session is None and str(self.mode_combo.currentData() or "") == "weighted_wheel":
                preview = self.db.preview_wheel_verification_data(
                    None,
                    mode="weighted_wheel",
                    rng_method=str(self.rng_combo.currentData() or "local"),
                )
            else:
                QMessageBox.information(
                    self,
                    "Данные проверки",
                    "До вращения данные доступны для режима «Взвешенное колесо». "
                    "В режиме «Максимальная сумма» точный состав колеса становится "
                    "известен только после возникновения ничьей и перехода к тай-брейку.",
                )
                return
        except Exception as exc:
            QMessageBox.warning(self, "Данные проверки", str(exc))
            return

        show_readonly_text_dialog(
            self,
            "Данные проверки перед вращением",
            format_verification_preview(preview),
        )

    def show_rng_methods(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Методы генерации случайных чисел")
        dialog.resize(760, 500)
        root = QVBoxLayout(dialog)
        tabs = QTabWidget()
        root.addWidget(tabs, 1)
        descriptions = [
            (
                "Стандартный",
                "Локальный криптографически стойкий генератор Python secrets.\n\n"
                "Работает без интернета и без лимитов запросов. Внешнего "
                "доказательства результата нет.",
            ),
            (
                "Random.org",
                "При запуске колеса программа получает случайное целое число через "
                "RANDOM.ORG Core API.\n\nНужны интернет и API key. Basic API "
                "не создаёт подписанного доказательства результата.",
            ),
            (
                "Random.org+",
                "До старта сессии создаётся билет RANDOM.ORG с showResult=true. "
                "Его ID сохраняется заранее. При запуске колеса используется Signed API "
                "с этим билетом. Подписанный random-объект, серийный номер и подпись "
                "сохраняются в базе и могут быть проверены через RANDOM.ORG.\n\n"
                "Если сеть оборвалась после генерации, программа проверяет билет и "
                "восстанавливает уже созданный результат вместо новой генерации.",
            ),
        ]
        for title, text in descriptions:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            editor = QTextEdit()
            editor.setReadOnly(True)
            editor.setPlainText(text)
            page_layout.addWidget(editor)
            tabs.addTab(page, title)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.reject)
        root.addWidget(buttons)
        dialog.exec()

    def confirm_winner(self):
        session = self._current_session()
        if session is None or session.get("status") != "winner_selected":
            return

        winner_id = session.get("winner_game_id")
        winner = self.db.get_game(int(winner_id)) if winner_id else None
        if winner is None:
            QMessageBox.critical(
                self,
                "Аукцион",
                "Не удалось найти игру-победителя.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Подтвердить победителя",
            f"Подтвердить победителя «{winner.title}»?\n\n"
            "Статус игры будет изменён на ПРОХОДИТСЯ.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            self.db.confirm_auction_winner(int(session["id"]))
        except Exception as exc:
            QMessageBox.critical(self, "Аукцион", str(exc))
            return

        self._active_auction_id = None
        self._prepare_next_max_amount_timer()

        # Статус победителя изменён в основной БД — обновляем все списки сразу.
        self.changed()

        QMessageBox.information(
            self,
            "Аукцион",
            f"Победитель подтверждён: «{winner.title}».\n"
            "Игра переведена в статус ПРОХОДИТСЯ.",
        )
        self.refresh()
