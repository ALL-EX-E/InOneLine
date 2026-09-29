from __future__ import annotations

import math
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from ..constants import (
    AUCTION_WHEEL_FORMAT_DEFAULT,
    AUCTION_WHEEL_FORMAT_ELIMINATION,
    AUCTION_WHEEL_FORMAT_STANDARD,
    STATUS_NOT_PLAYED,
    STATUS_PLAYED,
    WHEEL_CENTER_IMAGE_MEDIA_ID_KEY,
)
from ..media import MEDIA_CATEGORY_WHEEL_CENTER_ICONS, media_asset_available
from .common import utc_now


class WheelMixin:
    WHEEL_ALGORITHM_V1 = "weighted-cumulative-v1"
    WHEEL_ALGORITHM_V2 = "weighted-cumulative-v2-min-one"
    WHEEL_ALGORITHM_VERSION = WHEEL_ALGORITHM_V2

    @classmethod
    def _wheel_algorithm_for_mode(cls, mode: str) -> str:
        return cls.WHEEL_ALGORITHM_V2 if str(mode or "") == "weighted_wheel" else cls.WHEEL_ALGORITHM_V1

    @classmethod
    def _effective_wheel_weight(
        cls,
        *,
        algorithm_version: str,
        source_weight: int,
        equal_fallback: bool,
    ) -> int:
        source = max(0, int(source_weight))
        if algorithm_version == cls.WHEEL_ALGORITHM_V2:
            return max(1, source)
        if algorithm_version == cls.WHEEL_ALGORITHM_V1:
            return 1 if bool(equal_fallback) else source
        raise ValueError(f"Неподдерживаемая версия алгоритма колеса: {algorithm_version}")

    def _wheel_draw_info_conn(self, conn, auction_id: int) -> dict[str, Any]:
        session = conn.execute(
            "SELECT * FROM auction_sessions WHERE id=?",
            (int(auction_id),),
        ).fetchone()
        if session is None:
            raise KeyError(auction_id)
        rows = conn.execute(
            """
            SELECT
                ae.game_id,
                (ae.starting_sm_points + ae.bid_sm_points) AS total,
                COALESCE(NULLIF(ae.snapshot_title,''), g.title, '') AS snapshot_title
            FROM auction_entries ae
            LEFT JOIN games g ON g.id=ae.game_id
            WHERE ae.auction_id=? AND ae.active=1
            ORDER BY ae.game_id ASC
            """,
            (int(auction_id),),
        ).fetchall()
        participants = [
            {
                "game_id": int(row["game_id"]),
                "title": str(row["snapshot_title"] or ""),
                "source_weight": max(0, int(row["total"] or 0)),
            }
            for row in rows
        ]
        if not participants:
            raise ValueError("В колесе нет активных лотов.")
        total_weight = sum(int(row["source_weight"]) for row in participants)
        equal_fallback = total_weight <= 0
        algorithm_version = self._wheel_algorithm_for_mode(str(session["mode"] or ""))
        effective_weights = [
            self._effective_wheel_weight(
                algorithm_version=algorithm_version,
                source_weight=int(row["source_weight"]),
                equal_fallback=equal_fallback,
            )
            for row in participants
        ]
        draw_upper = sum(effective_weights)
        spin_row = conn.execute(
            "SELECT COALESCE(MAX(spin_index), 0) + 1 AS next_spin_index "
            "FROM wheel_verification_snapshots WHERE auction_id=?",
            (int(auction_id),),
        ).fetchone()
        next_spin_index = max(1, int(spin_row["next_spin_index"] or 1))
        return {
            "session": dict(session),
            "participants": participants,
            "weighted": [
                (
                    int(row["game_id"]),
                    int(weight)
                    if algorithm_version == self.WHEEL_ALGORITHM_V2
                    else int(row["source_weight"]),
                )
                for row, weight in zip(participants, effective_weights)
            ],
            "total_weight": total_weight,
            "draw_upper": draw_upper,
            "equal_fallback": equal_fallback,
            "algorithm_version": algorithm_version,
            "next_spin_index": next_spin_index,
            "wheel_format": str(
                session["wheel_format"] or AUCTION_WHEEL_FORMAT_DEFAULT
            ),
        }

    def get_wheel_draw_info(self, auction_id: int) -> dict[str, Any]:
        with self.connect() as conn:
            draw = self._wheel_draw_info_conn(conn, auction_id)
        return {
            "weighted": draw["weighted"],
            "total_weight": int(draw["total_weight"]),
            "draw_upper": int(draw["draw_upper"]),
            "next_spin_index": int(draw["next_spin_index"]),
            "wheel_format": str(draw["wheel_format"]),
        }

    @classmethod
    def _verification_participants(cls, draw: dict[str, Any]) -> list[dict[str, Any]]:
        equal_fallback = bool(draw["equal_fallback"])
        algorithm_version = str(draw.get("algorithm_version") or cls.WHEEL_ALGORITHM_V1)
        cursor = 0
        result: list[dict[str, Any]] = []
        for position, participant in enumerate(draw["participants"], start=1):
            source_weight = max(0, int(participant["source_weight"]))
            effective_weight = cls._effective_wheel_weight(
                algorithm_version=algorithm_version,
                source_weight=source_weight,
                equal_fallback=equal_fallback,
            )
            start = cursor
            cursor += effective_weight
            result.append(
                {
                    "position": position,
                    "game_id": int(participant["game_id"]),
                    "snapshot_title": str(participant.get("title") or ""),
                    "source_weight": source_weight,
                    "effective_weight": effective_weight,
                    "interval_start": start,
                    "interval_end": cursor,
                }
            )
        return result

    def _insert_wheel_verification_snapshot_conn(
        self,
        conn,
        *,
        auction_id: int,
        session: dict[str, Any],
        draw: dict[str, Any],
        pick: int,
        winner_game_id: int,
        rng_method: str,
        rng_ticket_id: str | None,
        rng_serial_number: int | None,
        rng_random_json: str | None,
        rng_signature: str | None,
        rng_verified: int | None,
        created_at: str,
    ) -> str:
        participants = self._verification_participants(draw)
        winner_title = next(
            (
                str(row["snapshot_title"])
                for row in participants
                if int(row["game_id"]) == int(winner_game_id)
            ),
            "",
        )
        wheel_format = str(
            session.get("wheel_format") or AUCTION_WHEEL_FORMAT_DEFAULT
        )
        result_kind = (
            "eliminated"
            if wheel_format == AUCTION_WHEEL_FORMAT_ELIMINATION
            else "winner"
        )
        spin_index = int(draw.get("next_spin_index") or 1)
        run_id = secrets.token_hex(16)
        cursor = conn.execute(
            """
            INSERT INTO wheel_verification_snapshots(
                run_id, auction_id, spin_index, result_kind,
                algorithm_version, mode, rng_method,
                rng_value, draw_upper, total_weight, equal_fallback,
                winner_game_id, winner_title, rng_ticket_id, rng_serial_number,
                rng_random_json, rng_signature, rng_verified, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                run_id,
                int(auction_id),
                spin_index,
                result_kind,
                str(draw["algorithm_version"]),
                str(session.get("mode") or "weighted_wheel"),
                str(rng_method or "local"),
                int(pick),
                int(draw["draw_upper"]),
                int(draw["total_weight"]),
                1 if draw["equal_fallback"] else 0,
                int(winner_game_id),
                winner_title,
                rng_ticket_id,
                rng_serial_number,
                rng_random_json,
                rng_signature,
                rng_verified,
                created_at,
            ),
        )
        snapshot_id = int(cursor.lastrowid)
        conn.executemany(
            """
            INSERT INTO wheel_verification_participants(
                snapshot_id, position, game_id, snapshot_title,
                source_weight, effective_weight, interval_start, interval_end
            ) VALUES(?,?,?,?,?,?,?,?)
            """,
            [
                (
                    snapshot_id,
                    int(row["position"]),
                    int(row["game_id"]),
                    str(row["snapshot_title"]),
                    int(row["source_weight"]),
                    int(row["effective_weight"]),
                    int(row["interval_start"]),
                    int(row["interval_end"]),
                )
                for row in participants
            ],
        )
        return run_id

    def run_weighted_wheel(
        self,
        auction_id: int,
        pick: int | None = None,
        rng_metadata: dict[str, Any] | None = None,
    ) -> int:
        """Atomically persist winner, immutable verification snapshot and audit log."""
        now = utc_now()
        with self.connect() as conn:
            draw = self._wheel_draw_info_conn(conn, auction_id)
            session = draw["session"]
            if session["status"] != "awaiting_wheel":
                raise RuntimeError(
                    "Колесо доступно только после завершения приёма ставок."
                )

            draw_upper = int(draw["draw_upper"])
            total_weight = int(draw["total_weight"])
            if pick is None:
                pick = secrets.randbelow(draw_upper)
            pick = int(pick)
            if pick < 0 or pick >= draw_upper:
                raise ValueError(
                    f"Случайное значение {pick} вне диапазона 0..{draw_upper - 1}."
                )

            verification_rows = self._verification_participants(draw)
            winner_row = next(
                (
                    row
                    for row in verification_rows
                    if int(row["interval_start"]) <= pick < int(row["interval_end"])
                ),
                None,
            )
            if winner_row is None:
                raise RuntimeError("Не удалось определить победителя по диапазону колеса.")
            winner_game_id = int(winner_row["game_id"])

            metadata = dict(rng_metadata or {})
            rng_method = str(
                metadata.get("rng_method") or session.get("rng_method") or "local"
            )
            rng_ticket_id = metadata.get("rng_ticket_id") or session.get("rng_ticket_id")
            rng_serial_number = metadata.get("rng_serial_number")
            rng_random_json = metadata.get("rng_random_json")
            rng_signature = metadata.get("rng_signature")
            rng_verified = metadata.get("rng_verified")
            if rng_verified is not None:
                rng_verified = 1 if bool(rng_verified) else 0

            run_id = self._insert_wheel_verification_snapshot_conn(
                conn,
                auction_id=int(auction_id),
                session=session,
                draw=draw,
                pick=pick,
                winner_game_id=winner_game_id,
                rng_method=rng_method,
                rng_ticket_id=rng_ticket_id,
                rng_serial_number=rng_serial_number,
                rng_random_json=rng_random_json,
                rng_signature=rng_signature,
                rng_verified=rng_verified,
                created_at=now,
            )

            conn.execute(
                """
                UPDATE auction_sessions
                SET status='winner_selected',
                    winner_game_id=?,
                    rng_method=?,
                    rng_ticket_id=?,
                    rng_value=?,
                    rng_serial_number=?,
                    rng_random_json=?,
                    rng_signature=?,
                    rng_verified=?,
                    updated_at=?
                WHERE id=?
                """,
                (
                    winner_game_id,
                    rng_method,
                    rng_ticket_id,
                    pick,
                    rng_serial_number,
                    rng_random_json,
                    rng_signature,
                    rng_verified,
                    now,
                    int(auction_id),
                ),
            )
            wheel_format = str(
                session.get("wheel_format") or AUCTION_WHEEL_FORMAT_DEFAULT
            )
            if wheel_format == AUCTION_WHEEL_FORMAT_ELIMINATION:
                conn.execute(
                    """
                    UPDATE auction_entries
                    SET result=CASE
                        WHEN game_id=? THEN 'elimination_selected'
                        ELSE NULL
                    END
                    WHERE auction_id=? AND active=1
                    """,
                    (winner_game_id, int(auction_id)),
                )
            else:
                conn.execute(
                    """
                    UPDATE auction_entries
                    SET result=CASE WHEN game_id=? THEN 'winner' ELSE 'not_winner' END
                    WHERE auction_id=? AND active=1
                    """,
                    (winner_game_id, int(auction_id)),
                )
            self._log_conn(
                conn,
                "auction_session",
                int(auction_id),
                "wheel",
                {"status": "awaiting_wheel"},
                {
                    "status": "winner_selected",
                    "winner_game_id": winner_game_id,
                    "total_weight": total_weight,
                    "rng_method": rng_method,
                    "rng_value": pick,
                    "rng_ticket_id": rng_ticket_id,
                    "rng_serial_number": rng_serial_number,
                    "rng_verified": rng_verified,
                    "verification_run_id": run_id,
                    "verification_algorithm": str(draw["algorithm_version"]),
                    "spin_index": int(draw.get("next_spin_index") or 1),
                    "wheel_format": str(
                        session.get("wheel_format") or AUCTION_WHEEL_FORMAT_DEFAULT
                    ),
                },
            )
            return winner_game_id

    def set_auction_rng_ticket_id(self, auction_id: int, ticket_id: str) -> None:
        """Persist a fresh Random.org+ ticket before that ticket is consumed."""
        ticket_id = str(ticket_id or "").strip()
        if not ticket_id:
            raise ValueError("Пустой Random.org+ ticket.")
        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (int(auction_id),),
            ).fetchone()
            if session is None:
                raise KeyError(auction_id)
            if str(session["status"] or "") != "awaiting_wheel":
                raise RuntimeError("Новый билет можно назначить только перед вращением.")
            if str(session["rng_method"] or "") != "random_org_plus":
                raise RuntimeError("Новый билет нужен только для Random.org+.")
            conn.execute(
                """
                UPDATE auction_sessions
                SET rng_ticket_id=?, rng_value=NULL, rng_serial_number=NULL,
                    rng_random_json=NULL, rng_signature=NULL, rng_verified=NULL,
                    updated_at=?
                WHERE id=?
                """,
                (ticket_id, utc_now(), int(auction_id)),
            )

    def archive_elimination_result(self, auction_id: int) -> dict[str, Any]:
        """Atomically archive the selected lot and prepare the next D21 spin."""
        now = utc_now()
        with self.connect() as conn:
            session_row = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (int(auction_id),),
            ).fetchone()
            if session_row is None:
                raise KeyError(auction_id)
            session = dict(session_row)
            if str(session.get("mode") or "") != "weighted_wheel":
                raise RuntimeError("Выбывание доступно только для взвешенного колеса.")
            if str(session.get("wheel_format") or "") != AUCTION_WHEEL_FORMAT_ELIMINATION:
                raise RuntimeError("Текущий формат колеса — не «Выбывание».")
            if str(session.get("status") or "") != "winner_selected":
                raise RuntimeError("Сейчас нет лота, ожидающего отправки в архив.")
            if not self._wheel_animation_complete(session):
                raise RuntimeError("Дождитесь полной остановки колеса.")

            game_id = int(session.get("winner_game_id") or 0)
            if game_id <= 0:
                raise RuntimeError("Не удалось определить выбранный лот.")
            entry = conn.execute(
                """
                SELECT ae.*, COALESCE(g.title, ae.snapshot_title) AS title
                FROM auction_entries ae
                LEFT JOIN games g ON g.id=ae.game_id
                WHERE ae.auction_id=? AND ae.game_id=? AND ae.active=1
                LIMIT 1
                """,
                (int(auction_id), game_id),
            ).fetchone()
            if entry is None:
                raise RuntimeError("Выбранный лот уже не участвует в аукционе.")
            game = conn.execute(
                "SELECT * FROM games WHERE id=?",
                (game_id,),
            ).fetchone()
            if game is None:
                raise RuntimeError("Выбранная игра больше не существует.")

            conn.execute(
                """
                UPDATE auction_entries
                SET active=0, result='eliminated'
                WHERE auction_id=? AND game_id=? AND active=1
                """,
                (int(auction_id), game_id),
            )
            conn.execute(
                """
                UPDATE games
                SET archived=1, auction_only=0, updated_at=?
                WHERE id=?
                """,
                (now, game_id),
            )
            conn.execute(
                """
                UPDATE auction_entries
                SET result=NULL
                WHERE auction_id=? AND active=1
                """,
                (int(auction_id),),
            )
            remaining = int(
                conn.execute(
                    "SELECT COUNT(*) FROM auction_entries "
                    "WHERE auction_id=? AND active=1",
                    (int(auction_id),),
                ).fetchone()[0]
            )
            next_status = "awaiting_wheel" if remaining > 0 else "finished_no_winner"
            finished_at = now if remaining <= 0 else None
            conn.execute(
                """
                UPDATE auction_sessions
                SET status=?,
                    winner_game_id=NULL,
                    rng_ticket_id=NULL,
                    rng_value=NULL,
                    rng_serial_number=NULL,
                    rng_random_json=NULL,
                    rng_signature=NULL,
                    rng_verified=NULL,
                    wheel_spin_id=NULL,
                    wheel_started_at=NULL,
                    wheel_target_rotation=NULL,
                    finished_at=CASE WHEN ? IS NULL THEN finished_at ELSE ? END,
                    updated_at=?
                WHERE id=?
                """,
                (
                    next_status,
                    finished_at,
                    finished_at,
                    now,
                    int(auction_id),
                ),
            )
            title = str(entry["title"] or "")
            self._log_conn(
                conn,
                "auction_session",
                int(auction_id),
                "elimination_archive",
                {
                    "status": "winner_selected",
                    "winner_game_id": game_id,
                },
                {
                    "status": next_status,
                    "game_id": game_id,
                    "title": title,
                    "remaining_lots": remaining,
                },
            )
            self._log_conn(
                conn,
                "game",
                game_id,
                "archive",
                {"archived": int(game["archived"] or 0)},
                {"archived": 1, "source": "auction_elimination"},
            )
            return {
                "game_id": game_id,
                "title": title,
                "remaining_lots": remaining,
                "status": next_status,
            }

    def list_wheel_verification_snapshots(
        self,
        auction_id: int,
    ) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM wheel_verification_snapshots "
                "WHERE auction_id=? ORDER BY spin_index ASC",
                (int(auction_id),),
            ).fetchall()
            result: list[dict[str, Any]] = []
            for row in rows:
                snapshot = dict(row)
                participants = conn.execute(
                    """
                    SELECT position, game_id, snapshot_title, source_weight,
                           effective_weight, interval_start, interval_end
                    FROM wheel_verification_participants
                    WHERE snapshot_id=?
                    ORDER BY position ASC
                    """,
                    (int(snapshot["id"]),),
                ).fetchall()
                snapshot["participants"] = [dict(item) for item in participants]
                result.append(snapshot)
        return result

    def get_wheel_verification_snapshot_by_run_id(
        self,
        run_id: str,
    ) -> dict[str, Any] | None:
        run_id = str(run_id or "").strip()
        if not run_id:
            return None
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM wheel_verification_snapshots WHERE run_id=?",
                (run_id,),
            ).fetchone()
            if row is None:
                return None
            snapshot = dict(row)
            participants = conn.execute(
                """
                SELECT position, game_id, snapshot_title, source_weight,
                       effective_weight, interval_start, interval_end
                FROM wheel_verification_participants
                WHERE snapshot_id=?
                ORDER BY position ASC
                """,
                (int(snapshot["id"]),),
            ).fetchall()
        snapshot["participants"] = [dict(item) for item in participants]
        return snapshot

    def get_wheel_verification_snapshot(self, auction_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM wheel_verification_snapshots "
                "WHERE auction_id=? ORDER BY spin_index DESC LIMIT 1",
                (int(auction_id),),
            ).fetchone()
            if row is None:
                return None
            snapshot = dict(row)
            participants = conn.execute(
                """
                SELECT position, game_id, snapshot_title, source_weight,
                       effective_weight, interval_start, interval_end
                FROM wheel_verification_participants
                WHERE snapshot_id=?
                ORDER BY position ASC
                """,
                (int(snapshot["id"]),),
            ).fetchall()
        snapshot["participants"] = [dict(item) for item in participants]
        return snapshot

    @staticmethod
    def _resolved_winner_chance_from_conn(
        conn,
        *,
        auction_id: int,
        winner_game_id: int,
    ) -> dict[str, Any] | None:
        """Return W4 chance only from the immutable resolved weighted-wheel snapshot."""
        row = conn.execute(
            """
            SELECT
                s.run_id,
                s.mode,
                s.draw_upper,
                p.effective_weight
            FROM wheel_verification_snapshots s
            JOIN wheel_verification_participants p
              ON p.snapshot_id=s.id
            WHERE s.auction_id=?
              AND s.winner_game_id=?
              AND p.game_id=?
            ORDER BY s.spin_index DESC
            LIMIT 1
            """,
            (
                int(auction_id),
                int(winner_game_id),
                int(winner_game_id),
            ),
        ).fetchone()
        if row is None:
            return {
                "available": False,
                "probability": None,
                "effective_weight": None,
                "draw_upper": None,
                "run_id": None,
                "source": "verification_snapshot",
            }
        if str(row["mode"] or "") != "weighted_wheel":
            return None

        draw_upper = int(row["draw_upper"] or 0)
        effective_weight = int(row["effective_weight"] or 0)
        if draw_upper <= 0 or effective_weight < 0:
            return {
                "available": False,
                "probability": None,
                "effective_weight": effective_weight,
                "draw_upper": draw_upper,
                "run_id": str(row["run_id"] or ""),
                "source": "verification_snapshot",
            }
        return {
            "available": True,
            "probability": effective_weight / draw_upper,
            "effective_weight": effective_weight,
            "draw_upper": draw_upper,
            "run_id": str(row["run_id"] or ""),
            "source": "verification_snapshot",
        }

    def verify_wheel_result(
        self,
        auction_id: int,
        *,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """Deterministically verify one frozen spin without RNG/network/writes."""
        snapshot = (
            self.get_wheel_verification_snapshot_by_run_id(run_id)
            if run_id
            else self.get_wheel_verification_snapshot(int(auction_id))
        )
        if snapshot is None:
            return {
                "status": "unavailable",
                "label": "Невозможно проверить",
                "reason": "Verification snapshot для этого аукциона отсутствует.",
                "expected_winner_game_id": None,
                "expected_winner_title": "",
            }
        algorithm_version = str(snapshot.get("algorithm_version") or "")
        if algorithm_version not in {self.WHEEL_ALGORITHM_V1, self.WHEEL_ALGORITHM_V2}:
            return {
                "status": "unavailable",
                "label": "Невозможно проверить",
                "reason": "Версия алгоритма snapshot не поддерживается этой версией программы.",
                "expected_winner_game_id": None,
                "expected_winner_title": "",
            }

        try:
            participants = list(snapshot.get("participants") or [])
            if not participants:
                raise ValueError("В snapshot отсутствуют участники.")
            positions = [int(row["position"]) for row in participants]
            if positions != list(range(1, len(participants) + 1)):
                raise ValueError("Нарушен порядок участников snapshot.")

            source_weights = [int(row["source_weight"]) for row in participants]
            if any(weight < 0 for weight in source_weights):
                raise ValueError("В snapshot найден отрицательный вес.")
            total_weight = sum(source_weights)
            if total_weight != int(snapshot["total_weight"]):
                raise ValueError("Суммарный вес snapshot повреждён.")
            equal_fallback = bool(int(snapshot["equal_fallback"]))
            if equal_fallback != (total_weight <= 0):
                raise ValueError("Признак equal-fallback snapshot повреждён.")

            cursor = 0
            for row, source_weight in zip(participants, source_weights):
                expected_effective = self._effective_wheel_weight(
                    algorithm_version=algorithm_version,
                    source_weight=source_weight,
                    equal_fallback=equal_fallback,
                )
                if int(row["effective_weight"]) != expected_effective:
                    raise ValueError("Эффективный вес snapshot повреждён.")
                if int(row["interval_start"]) != cursor:
                    raise ValueError("Начало диапазона snapshot повреждено.")
                cursor += expected_effective
                if int(row["interval_end"]) != cursor:
                    raise ValueError("Конец диапазона snapshot повреждён.")
            if cursor != int(snapshot["draw_upper"]):
                raise ValueError("Диапазон случайного числа snapshot повреждён.")

            pick = int(snapshot["rng_value"])
            if pick < 0 or pick >= cursor:
                raise ValueError("Случайное значение snapshot находится вне диапазона.")
            expected = next(
                row
                for row in participants
                if int(row["interval_start"]) <= pick < int(row["interval_end"])
            )
        except (KeyError, TypeError, ValueError, StopIteration) as exc:
            return {
                "status": "unavailable",
                "label": "Невозможно проверить",
                "reason": str(exc) or "Snapshot повреждён.",
                "expected_winner_game_id": None,
                "expected_winner_title": "",
            }

        expected_id = int(expected["game_id"])
        expected_title = str(expected.get("snapshot_title") or "")
        winner_matches = (
            expected_id == int(snapshot["winner_game_id"])
            and expected_title == str(snapshot.get("winner_title") or "")
        )
        if winner_matches:
            return {
                "status": "match",
                "label": "Совпадает",
                "reason": (
                    "Сохранённый результат совпадает с детерминированным "
                    "пересчётом snapshot."
                ),
                "expected_winner_game_id": expected_id,
                "expected_winner_title": expected_title,
            }
        return {
            "status": "mismatch",
            "label": "НЕ СОВПАДАЕТ",
            "reason": (
                "Сохранённый результат не совпадает с детерминированным "
                "пересчётом snapshot."
            ),
            "expected_winner_game_id": expected_id,
            "expected_winner_title": expected_title,
        }

    def preview_wheel_verification_data(
        self,
        auction_id: int | None = None,
        *,
        mode: str = "weighted_wheel",
        rng_method: str = "local",
        wheel_format: str = AUCTION_WHEEL_FORMAT_STANDARD,
    ) -> dict[str, Any]:
        """Read-only pre-spin mathematical preview. Never creates a snapshot."""
        with self.connect() as conn:
            if auction_id is not None:
                draw = self._wheel_draw_info_conn(conn, int(auction_id))
                session = draw["session"]
                if str(session.get("status") or "") != "awaiting_wheel":
                    raise RuntimeError("Данные проверки доступны только перед фактическим вращением.")
                effective_mode = str(session.get("mode") or mode)
                effective_rng = str(session.get("rng_method") or rng_method or "local")
                effective_wheel_format = str(
                    draw.get("wheel_format") or AUCTION_WHEEL_FORMAT_STANDARD
                )
                next_spin_index = int(draw.get("next_spin_index") or 1)
                authoritative_input = True
            else:
                rows = conn.execute(
                    """
                    SELECT id AS game_id, title, sm_points
                    FROM games
                    WHERE auction_only=0
                      AND archived=0
                      AND status IN (?, ?)
                    ORDER BY id ASC
                    """,
                    (STATUS_PLAYED, STATUS_NOT_PLAYED),
                ).fetchall()
                participants = [
                    {
                        "game_id": int(row["game_id"]),
                        "title": str(row["title"]),
                        "source_weight": max(0, int(row["sm_points"] or 0)),
                    }
                    for row in rows
                ]
                if not participants:
                    raise ValueError("В предварительном колесе нет доступных лотов.")
                total_weight = sum(int(row["source_weight"]) for row in participants)
                effective_mode = str(mode or "weighted_wheel")
                equal_fallback = total_weight <= 0
                algorithm_version = self._wheel_algorithm_for_mode(effective_mode)
                draw = {
                    "participants": participants,
                    "total_weight": total_weight,
                    "draw_upper": sum(
                        self._effective_wheel_weight(
                            algorithm_version=algorithm_version,
                            source_weight=int(row["source_weight"]),
                            equal_fallback=equal_fallback,
                        )
                        for row in participants
                    ),
                    "equal_fallback": equal_fallback,
                    "algorithm_version": algorithm_version,
                }
                effective_rng = str(rng_method or "local")
                effective_wheel_format = (
                    AUCTION_WHEEL_FORMAT_ELIMINATION
                    if str(wheel_format or "") == AUCTION_WHEEL_FORMAT_ELIMINATION
                    else AUCTION_WHEEL_FORMAT_STANDARD
                )
                next_spin_index = 1
                authoritative_input = False

        verification_rows = self._verification_participants(draw)
        return {
            "algorithm_version": str(draw["algorithm_version"]),
            "mode": effective_mode,
            "wheel_format": effective_wheel_format,
            "next_spin_index": next_spin_index,
            "rng_method": effective_rng,
            "draw_upper": int(draw["draw_upper"]),
            "total_weight": int(draw["total_weight"]),
            "equal_fallback": bool(draw["equal_fallback"]),
            "participants": verification_rows,
            "authoritative_input": authoritative_input,
            "snapshot_created": False,
        }

    @staticmethod
    def _wheel_animation_timer_state(session: dict[str, Any]) -> dict[str, Any]:
        """Return the authoritative wheel countdown derived from saved spin fields."""
        duration_ms = max(0, int(session.get("wheel_duration_ms") or 8000))
        spin_id = session.get("wheel_spin_id")
        started_at = session.get("wheel_started_at")
        if not spin_id or not started_at:
            return {
                "remaining_ms": duration_ms,
                "running": False,
                "complete": True,
            }
        try:
            start = datetime.fromisoformat(str(started_at))
            now = datetime.now(timezone.utc)
            if now < start:
                return {
                    "remaining_ms": duration_ms,
                    "running": False,
                    "complete": False,
                }
            finish = start + timedelta(milliseconds=duration_ms)
            remaining_ms = max(
                0,
                math.ceil((finish - now).total_seconds() * 1000.0),
            )
            return {
                "remaining_ms": remaining_ms,
                "running": remaining_ms > 0,
                "complete": remaining_ms <= 0,
            }
        except (TypeError, ValueError):
            return {
                "remaining_ms": duration_ms,
                "running": False,
                "complete": True,
            }

    @classmethod
    def _wheel_animation_complete(cls, session: dict[str, Any]) -> bool:
        return bool(cls._wheel_animation_timer_state(session)["complete"])

    def prepare_wheel_animation(
        self,
        auction_id: int,
        lead_in_ms: int = 1200,
    ) -> dict[str, Any]:
        """Фиксирует параметры одной синхронной визуальной анимации колеса."""
        with self.connect() as conn:
            session_row = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            if session_row is None:
                raise KeyError(auction_id)
            session = dict(session_row)
            if session["status"] != "winner_selected":
                raise RuntimeError(
                    "Анимацию колеса можно подготовить только после выбора победителя."
                )
            if session.get("rng_value") is None:
                raise RuntimeError("Для колеса отсутствует случайное значение.")

        draw = self.get_wheel_draw_info(auction_id)
        draw_upper = int(draw["draw_upper"])
        if draw_upper <= 0:
            raise RuntimeError("Некорректный диапазон визуального колеса.")

        pick = int(session["rng_value"])
        sample_angle = ((pick + 0.5) / draw_upper) * 360.0
        stop_rotation = (360.0 - sample_angle) % 360.0

        # Количество полных оборотов влияет только на внешний вид, а не на результат.
        # Для длительных вращений не растягиваем прежние 6–9 оборотов на часы:
        # масштабируем число оборотов относительно базовых 8 секунд.
        base_turns = 6 + secrets.randbelow(4)
        duration_ms = max(1, int(session.get("wheel_duration_ms") or 8000))
        duration_scale = max(1.0, duration_ms / 8000.0)
        full_turns = max(base_turns, round(base_turns * duration_scale))
        target_rotation = full_turns * 360.0 + stop_rotation

        now_dt = datetime.now(timezone.utc)
        start_dt = now_dt + timedelta(milliseconds=max(300, int(lead_in_ms)))
        started_at = start_dt.isoformat(timespec="milliseconds")
        spin_id = secrets.token_hex(12)

        with self.connect() as conn:
            conn.execute(
                """
                UPDATE auction_sessions
                SET wheel_spin_id=?,
                    wheel_started_at=?,
                    wheel_target_rotation=?,
                    updated_at=?
                WHERE id=?
                """,
                (
                    spin_id,
                    started_at,
                    float(target_rotation),
                    utc_now(),
                    auction_id,
                ),
            )
            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "wheel_animation",
                None,
                {
                    "wheel_spin_id": spin_id,
                    "wheel_started_at": started_at,
                    "wheel_duration_ms": int(
                        session.get("wheel_duration_ms") or 8000
                    ),
                    "wheel_target_rotation": target_rotation,
                },
            )

        return self.wheel_payload(auction_id)

    def _wheel_center_image_payload_from_conn(self, conn) -> dict[str, Any]:
        row = conn.execute(
            "SELECT value FROM settings WHERE key=?",
            (WHEEL_CENTER_IMAGE_MEDIA_ID_KEY,),
        ).fetchone()
        raw = str(row["value"] if row is not None else "").strip()
        if not raw.isdigit():
            return {"enabled": False, "asset_id": None, "url": "", "animated": False}
        asset = self._get_media_asset_conn(conn, int(raw))
        if (
            asset is None
            or asset.category != MEDIA_CATEGORY_WHEEL_CENTER_ICONS
            or not media_asset_available(self.path.parent, asset)
        ):
            return {"enabled": False, "asset_id": None, "url": "", "animated": False}
        media_name = str(asset.managed_name or asset.external_path or "").casefold()
        return {
            "enabled": True,
            "asset_id": int(asset.id),
            "url": f"/media/{int(asset.id)}",
            "name": asset.display_name,
            "animated": media_name.endswith((".gif", ".webp")),
        }

    def _wheel_payload_from_conn(
        self,
        conn,
        session: dict[str, Any],
    ) -> dict[str, Any]:
        """Build wheel payload without opening nested SQLite connections."""
        auction_id = int(session["id"])

        # Порядок секторов обязан совпадать с get_wheel_draw_info(), потому
        # что rng_value интерпретируется по его кумулятивным диапазонам.
        # JOIN сразу приносит title и устраняет прежний get_game() на сектор.
        rows = conn.execute(
            """
            SELECT
                ae.game_id,
                (ae.starting_sm_points + ae.bid_sm_points) AS total,
                g.title
            FROM auction_entries ae
            LEFT JOIN games g ON g.id=ae.game_id
            WHERE ae.auction_id=? AND ae.active=1
            ORDER BY ae.game_id ASC
            """,
            (auction_id,),
        ).fetchall()

        weighted = [
            (
                int(row["game_id"]),
                max(0, int(row["total"] or 0)),
                None if row["title"] is None else str(row["title"]),
            )
            for row in rows
        ]
        if not weighted:
            raise ValueError("В колесе нет активных лотов.")

        total_weight = sum(raw_weight for _, raw_weight, _ in weighted)
        equal_mode = total_weight <= 0
        algorithm_version = self._wheel_algorithm_for_mode(str(session.get("mode") or ""))
        effective_total = sum(
            self._effective_wheel_weight(
                algorithm_version=algorithm_version,
                source_weight=raw_weight,
                equal_fallback=equal_mode,
            )
            for _, raw_weight, _ in weighted
        )

        sectors: list[dict[str, Any]] = []
        for game_id, raw_weight, title in weighted:
            # Сохраняем прежнюю семантику повреждённой старой истории:
            # вес отсутствующей live-игры всё ещё входит в draw, но сектор
            # без title не показывается. Новые A3/A4 не дают создать такое
            # состояние для незавершённого аукциона.
            if title is None:
                continue
            weight = self._effective_wheel_weight(
                algorithm_version=algorithm_version,
                source_weight=raw_weight,
                equal_fallback=equal_mode,
            )
            probability = (
                (weight / effective_total) if effective_total > 0 else 0.0
            )
            sectors.append(
                {
                    "game_id": game_id,
                    "title": title,
                    "sm_points": raw_weight,
                    "weight": int(weight),
                    "probability": probability,
                }
            )

        winner = None
        winner_id = session.get("winner_game_id")
        animation_complete = self._wheel_animation_complete(session)
        if winner_id is not None and animation_complete:
            winner_row = conn.execute(
                "SELECT id, title FROM games WHERE id=?",
                (int(winner_id),),
            ).fetchone()
            if winner_row is not None:
                winner_chance = None
                if str(session.get("mode") or "") == "weighted_wheel":
                    winner_chance = self._resolved_winner_chance_from_conn(
                        conn,
                        auction_id=auction_id,
                        winner_game_id=int(winner_id),
                    )
                winner = {
                    "game_id": int(winner_row["id"]),
                    "title": str(winner_row["title"]),
                    "chance": winner_chance,
                }

        # Browser Source и локальный виджет показывают колесо постоянно,
        # пока есть активная сессия; вращение лишь меняет его угол.
        visible = bool(sectors)

        return {
            "auction_id": auction_id,
            "status": str(session.get("status") or ""),
            "mode": str(session.get("mode") or ""),
            "wheel_format": str(
                session.get("wheel_format") or AUCTION_WHEEL_FORMAT_DEFAULT
            ),
            "rng_method": str(session.get("rng_method") or "local"),
            "ready": str(session.get("status") or "") == "awaiting_wheel",
            "visible": visible,
            "equal_weights": equal_mode,
            "sectors": sectors,
            "winner": winner,
            "center_image": self._wheel_center_image_payload_from_conn(conn),
            "animation": {
                "spin_id": session.get("wheel_spin_id"),
                "started_at": session.get("wheel_started_at"),
                "duration_ms": int(
                    session.get("wheel_duration_ms") or 8000
                ),
                "target_rotation": float(
                    session.get("wheel_target_rotation") or 0.0
                ),
                "complete": animation_complete,
            },
            "server_time": datetime.now(timezone.utc).isoformat(
                timespec="milliseconds"
            ),
        }

    def wheel_payload(self, auction_id: int) -> dict[str, Any]:
        """Единое состояние колеса для Qt-интерфейса и OBS Browser Source."""
        with self.connect() as conn:
            session = self._get_auction_session_conn(conn, auction_id)
            if session is None:
                raise KeyError(auction_id)
            return self._wheel_payload_from_conn(conn, session)

    def _preview_wheel_payload_from_conn(self, conn) -> dict[str, Any]:
        """Build the existing pre-start wheel preview without a nested DB connection."""
        rows = conn.execute(
            """
            SELECT id, title, sm_points
            FROM games
            WHERE auction_only=0
              AND archived=0
              AND status IN (?, ?)
            ORDER BY
                sm_points DESC,
                CASE WHEN release_date IS NULL THEN 1 ELSE 0 END ASC,
                release_date DESC,
                updated_at DESC,
                id ASC
            """,
            (STATUS_PLAYED, STATUS_NOT_PLAYED),
        ).fetchall()

        raw = [
            (
                int(row["id"]),
                max(0, int(row["sm_points"] or 0)),
                str(row["title"]),
            )
            for row in rows
        ]
        total = sum(weight for _, weight, _ in raw)
        equal_mode = total <= 0 and bool(raw)
        algorithm_version = self.WHEEL_ALGORITHM_V2
        effective_total = sum(
            self._effective_wheel_weight(
                algorithm_version=algorithm_version,
                source_weight=raw_weight,
                equal_fallback=equal_mode,
            )
            for _, raw_weight, _ in raw
        )

        sectors = []
        for game_id, raw_weight, title in raw:
            weight = self._effective_wheel_weight(
                algorithm_version=algorithm_version,
                source_weight=raw_weight,
                equal_fallback=equal_mode,
            )
            sectors.append(
                {
                    "game_id": game_id,
                    "title": title,
                    "sm_points": raw_weight,
                    "weight": weight,
                    "probability": (
                        weight / effective_total if effective_total > 0 else 0.0
                    ),
                }
            )

        return {
            "auction_id": None,
            "status": "preview",
            "mode": "weighted_wheel",
            "wheel_format": AUCTION_WHEEL_FORMAT_STANDARD,
            "rng_method": "local",
            "ready": False,
            "visible": True,
            "equal_weights": equal_mode,
            "sectors": sectors,
            "winner": None,
            "center_image": self._wheel_center_image_payload_from_conn(conn),
            "animation": {
                "spin_id": None,
                "started_at": None,
                "duration_ms": 8000,
                "target_rotation": 0.0,
                "complete": True,
            },
            "server_time": datetime.now(timezone.utc).isoformat(
                timespec="milliseconds"
            ),
        }

    def current_wheel_payload(self) -> dict[str, Any]:
        """Состояние колеса для OBS даже до запуска сессии."""
        with self.connect() as conn:
            session = self._get_open_auction_session_conn(conn)
            if session is not None:
                return self._wheel_payload_from_conn(conn, session)
            return self._preview_wheel_payload_from_conn(conn)
