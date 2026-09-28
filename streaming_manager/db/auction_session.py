from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from ..constants import (
    AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_DEFAULT,
    AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_KEY,
    AUCTION_AUTO_EXTEND_EXTERNAL_SERVICE_UNITS_ENABLED_DEFAULT,
    AUCTION_AUTO_EXTEND_EXTERNAL_SERVICE_UNITS_ENABLED_KEY,
    AUCTION_AUTO_EXTEND_EXTERNAL_MS_DEFAULT,
    AUCTION_AUTO_EXTEND_EXTERNAL_MS_KEY,
    AUCTION_AUTO_EXTEND_LEADER_ENABLED_DEFAULT,
    AUCTION_AUTO_EXTEND_LEADER_ENABLED_KEY,
    AUCTION_AUTO_EXTEND_LEADER_MS_DEFAULT,
    AUCTION_AUTO_EXTEND_LEADER_MS_KEY,
    AUCTION_AUTO_EXTEND_MAX_MS,
    AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_DEFAULT,
    AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_KEY,
    AUCTION_AUTO_EXTEND_NEW_LOT_MS_DEFAULT,
    AUCTION_AUTO_EXTEND_NEW_LOT_MS_KEY,
    AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_DEFAULT,
    AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_KEY,
    AUCTION_AUTO_EXTEND_THRESHOLD_MS_DEFAULT,
    AUCTION_AUTO_EXTEND_THRESHOLD_MS_KEY,
    AUCTION_MIN_DURATION_MS, AUCTION_MAX_DURATION_MS,
    STATUS_NOT_PLAYED, STATUS_PLAYED, STATUS_PLAYING,
)
from .common import normalize_title_key, utc_now


class AuctionSessionMixin:
    WHEEL_MIN_DURATION_MS = 3_000
    WHEEL_MAX_DURATION_MS = 24 * 60 * 60 * 1000

    AUCTION_OPEN_STATUSES = (
        "running", "paused", "awaiting_wheel", "winner_selected", "tie_break_required",
    )
    AUCTION_MODES = ("max_amount", "weighted_wheel")

    @staticmethod
    def _auction_row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    def _get_auction_session_conn(
        self,
        conn: sqlite3.Connection,
        auction_id: int,
    ) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM auction_sessions WHERE id=?",
            (auction_id,),
        ).fetchone()
        return self._auction_row_to_dict(row)

    def get_auction_session(self, auction_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            return self._get_auction_session_conn(conn, auction_id)

    def _get_open_auction_session_conn(
        self,
        conn: sqlite3.Connection,
    ) -> dict[str, Any] | None:
        placeholders = ",".join("?" for _ in self.AUCTION_OPEN_STATUSES)
        row = conn.execute(
            f"""
            SELECT *
            FROM auction_sessions
            WHERE provider='local'
              AND status IN ({placeholders})
            ORDER BY id DESC
            LIMIT 1
            """,
            self.AUCTION_OPEN_STATUSES,
        ).fetchone()
        return self._auction_row_to_dict(row)

    def get_open_auction_session(self) -> dict[str, Any] | None:
        with self.connect() as conn:
            return self._get_open_auction_session_conn(conn)

    @staticmethod
    def _parse_provider_timestamp(value: Any) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def find_running_auction_at(self, timestamp: Any) -> int | None:
        """Return the local auction that was accepting bids at ``timestamp``.

        Provider events may be delivered late.  Current auction status alone is
        therefore insufficient: a redemption made between auctions must stay an
        outside-auction top-up even if a new auction starts before delivery, and
        a redemption made during an older auction must never leak into a newer
        one.  ``change_log`` already contains every relevant status transition,
        so no new schema is required.
        """
        target = self._parse_provider_timestamp(timestamp)
        if target is None:
            return None
        with self.connect() as conn:
            sessions = conn.execute(
                "SELECT id,started_at FROM auction_sessions "
                "WHERE provider='local' ORDER BY id DESC"
            ).fetchall()
            for session in sessions:
                started = self._parse_provider_timestamp(session["started_at"])
                if started is None or started > target:
                    continue
                auction_id = int(session["id"])
                logs = conn.execute(
                    "SELECT action,after_json,created_at FROM change_log "
                    "WHERE entity_type='auction_session' AND entity_id=? "
                    "ORDER BY id ASC",
                    (auction_id,),
                ).fetchall()
                status_at_target: str | None = None
                # ``started_at`` is written immediately before the create audit
                # row.  A provider timestamp can legitimately fall in those few
                # microseconds, so seed the initial status from the create audit
                # payload before applying later transitions by timestamp.
                for log in logs:
                    if str(log["action"]) != "create":
                        continue
                    try:
                        created_payload = json.loads(str(log["after_json"] or "{}"))
                    except (TypeError, ValueError, json.JSONDecodeError):
                        created_payload = {}
                    if isinstance(created_payload, dict) and created_payload.get("status"):
                        status_at_target = str(created_payload["status"])
                    break
                for log in logs:
                    if str(log["action"]) == "create":
                        continue
                    logged_at = self._parse_provider_timestamp(log["created_at"])
                    if logged_at is None or logged_at > target:
                        break
                    try:
                        payload = json.loads(str(log["after_json"] or "{}"))
                    except (TypeError, ValueError, json.JSONDecodeError):
                        payload = {}
                    if isinstance(payload, dict) and payload.get("status"):
                        status_at_target = str(payload["status"])
                if status_at_target == "running":
                    return auction_id
        return None

    def _get_open_auction_session_for_game_conn(
        self,
        conn: sqlite3.Connection,
        game_id: int,
    ) -> dict[str, Any] | None:
        """Return an unfinished local auction that still references ``game_id``.

        The lookup intentionally does not filter ``auction_entries.active``. During
        a tie-break, entries that are no longer leaders become inactive but remain
        part of the still-open auction history until the session is closed.
        """
        placeholders = ",".join("?" for _ in self.AUCTION_OPEN_STATUSES)
        row = conn.execute(
            f"""
            SELECT s.*
            FROM auction_sessions s
            JOIN auction_entries ae ON ae.auction_id=s.id
            WHERE s.provider='local'
              AND s.status IN ({placeholders})
              AND ae.game_id=?
            ORDER BY s.id DESC
            LIMIT 1
            """,
            (*self.AUCTION_OPEN_STATUSES, int(game_id)),
        ).fetchone()
        return self._auction_row_to_dict(row)

    def get_open_auction_session_for_game(
        self,
        game_id: int,
    ) -> dict[str, Any] | None:
        """Public guard lookup used by UI and destructive DB operations."""
        with self.connect() as conn:
            return self._get_open_auction_session_for_game_conn(conn, game_id)

    def create_auction_session(
        self,
        mode: str,
        duration_seconds: int,
        rng_method: str = "local",
        rng_ticket_id: str | None = None,
        wheel_duration_ms: int = 8000,
        *,
        duration_ms: int | None = None,
        start_in_wheel_mode: bool = False,
    ) -> int:
        """Создаёт локальную сессию из текущего ДЛЯ АУКА.

        Обычно сессия сразу запускает приём ставок. Для прямого режима
        ``weighted_wheel`` флаг ``start_in_wheel_mode`` создаёт её сразу в
        ``awaiting_wheel``: отдельный аукционный отсчёт в этом сценарии не нужен.
        """
        if mode not in self.AUCTION_MODES:
            raise ValueError("Неизвестный способ определения победителя.")
        if rng_method not in ("local", "random_org", "random_org_plus"):
            raise ValueError("Неизвестный метод генерации случайных чисел.")
        if rng_method == "random_org_plus" and not rng_ticket_id:
            raise ValueError("Для Random.org+ требуется заранее созданный билет.")

        start_in_wheel_mode = bool(start_in_wheel_mode)
        if start_in_wheel_mode and mode != "weighted_wheel":
            raise ValueError(
                "Прямой запуск колеса доступен только для режима weighted_wheel."
            )

        duration_seconds = int(duration_seconds)
        duration_ms = (
            int(duration_ms)
            if duration_ms is not None
            else duration_seconds * 1000
        )
        wheel_duration_ms = int(wheel_duration_ms)
        if not (
            self.WHEEL_MIN_DURATION_MS
            <= wheel_duration_ms
            <= self.WHEEL_MAX_DURATION_MS
        ):
            raise ValueError(
                "Время вращения колеса должно быть от 00:00:03.000 "
                "до 24:00:00.000."
            )

        if start_in_wheel_mode:
            # В прямом сценарии взвешенного колеса большой таймер относится
            # только к wheel_duration_ms. Аукционный deadline не создаём.
            duration_seconds = 0
            duration_ms = 0
            initial_status = "awaiting_wheel"
            remaining_seconds = 0
            remaining_ms = 0
        else:
            if duration_ms < AUCTION_MIN_DURATION_MS or duration_ms > AUCTION_MAX_DURATION_MS:
                raise ValueError(
                    "Длительность аукциона должна быть от 1 секунды до 24 часов."
                )
            # Старые секундные поля остаются совместимым округлённым представлением.
            duration_seconds = max(1, math.ceil(duration_ms / 1000))
            initial_status = "running"
            remaining_seconds = duration_seconds
            remaining_ms = duration_ms

        games = self.auction_eligible_games()
        if len(games) < 2:
            raise ValueError("Для запуска аукциона нужно минимум два лота.")

        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat(timespec="microseconds")
        deadline = (
            None
            if start_in_wheel_mode
            else (now_dt + timedelta(milliseconds=duration_ms)).isoformat(
                timespec="microseconds"
            )
        )

        with self.connect() as conn:
            placeholders = ",".join("?" for _ in self.AUCTION_OPEN_STATUSES)
            existing = conn.execute(
                f"""
                SELECT id FROM auction_sessions
                WHERE provider='local'
                  AND status IN ({placeholders})
                LIMIT 1
                """,
                self.AUCTION_OPEN_STATUSES,
            ).fetchone()
            if existing is not None:
                raise RuntimeError("Сначала завершите или отмените текущий аукцион.")

            rules_snapshot = self._active_rule_snapshot_conn(conn)
            cursor = conn.execute(
                """
                INSERT INTO auction_sessions(
                    name, mode, provider, started_at, created_at,
                    status, duration_seconds, remaining_seconds,
                    duration_ms, remaining_ms, deadline_at, updated_at,
                    rng_method, rng_ticket_id, wheel_duration_ms,
                    rules_template_id, rules_template_name, rules_html
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    "Новый аукцион",
                    mode,
                    "local",
                    now,
                    now,
                    initial_status,
                    duration_seconds,
                    remaining_seconds,
                    duration_ms,
                    remaining_ms,
                    deadline,
                    now,
                    rng_method,
                    rng_ticket_id,
                    wheel_duration_ms,
                    rules_snapshot["template_id"],
                    rules_snapshot["template_name"],
                    rules_snapshot["content_html"],
                ),
            )
            auction_id = int(cursor.lastrowid)
            name = f"Аукцион #{auction_id}"
            conn.execute(
                "UPDATE auction_sessions SET name=? WHERE id=?",
                (name, auction_id),
            )

            for start_position, game in enumerate(games, start=1):
                conn.execute(
                    """
                    INSERT INTO auction_entries(
                        auction_id, game_id, weight, active,
                        starting_sm_points, bid_sm_points,
                        snapshot_title, snapshot_release_date, snapshot_coop,
                        snapshot_status, snapshot_review, start_position
                    )
                    VALUES(?,?,?,?,?,0,?,?,?,?,?,?)
                    """,
                    (
                        auction_id,
                        int(game.id),
                        max(0, int(game.sm_points)),
                        1,
                        max(0, int(game.sm_points)),
                        game.title,
                        game.release_date,
                        int(game.coop),
                        game.status,
                        game.review,
                        start_position,
                    ),
                )

            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "create",
                None,
                {
                    "id": auction_id,
                    "name": name,
                    "mode": mode,
                    "status": initial_status,
                    "duration_seconds": duration_seconds,
                    "duration_ms": duration_ms,
                    "lots": len(games),
                    "rules_template_id": rules_snapshot["template_id"],
                    "rules_template_name": rules_snapshot["template_name"],
                    "rng_method": rng_method,
                    "rng_ticket_id": rng_ticket_id,
                    "wheel_duration_ms": wheel_duration_ms,
                },
            )

        return auction_id

    def auction_total_sm_points(self, auction_id: int) -> int:
        """Return the full point total of one auction session.

        A6 intentionally sums every historical lot that still belongs to the
        session, including entries made inactive by tie-break narrowing. Only
        an A5 operator-removed erroneous temporary lot is excluded.
        """
        auction_id = int(auction_id)
        with self.connect() as conn:
            if conn.execute(
                "SELECT 1 FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone() is None:
                raise KeyError(auction_id)
            value = conn.execute(
                """
                SELECT COALESCE(SUM(starting_sm_points + bid_sm_points), 0)
                FROM auction_entries
                WHERE auction_id=?
                  AND COALESCE(result, '') <> 'removed'
                """,
                (auction_id,),
            ).fetchone()[0]
        return max(0, int(value or 0))

    def _list_auction_entries_conn(
        self,
        conn: sqlite3.Connection,
        auction_id: int,
    ) -> list[dict[str, Any]]:
        """Return the authoritative ordered lot rows through an existing connection."""
        rows = conn.execute(
            """
            SELECT
                ae.id AS entry_id,
                ae.auction_id,
                ae.game_id,
                ae.active,
                ae.result,
                ae.starting_sm_points,
                ae.bid_sm_points,
                ae.start_position,
                (ae.starting_sm_points + ae.bid_sm_points)
                    AS total_sm_points,
                COALESCE(g.title, ae.snapshot_title) AS title,
                COALESCE(g.review, ae.snapshot_review) AS review,
                COALESCE(g.status, ae.snapshot_status) AS status,
                COALESCE(g.archived, 0) AS archived,
                COALESCE(g.auction_only, 0) AS auction_only
            FROM auction_entries ae
            LEFT JOIN games g ON g.id = ae.game_id
            WHERE ae.auction_id=? AND ae.active=1
            ORDER BY
                total_sm_points DESC,
                CASE WHEN ae.start_position IS NULL THEN 1 ELSE 0 END ASC,
                ae.start_position ASC,
                COALESCE(g.title, ae.snapshot_title) COLLATE NOCASE ASC,
                ae.game_id ASC,
                ae.id ASC
            """,
            (int(auction_id),),
        ).fetchall()
        result = [dict(row) for row in rows]
        for current_position, row in enumerate(result, start=1):
            row["current_position"] = current_position
        return result

    def list_auction_entries(self, auction_id: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return self._list_auction_entries_conn(conn, auction_id)

    def list_auction_history_events(
        self,
        auction_id: int,
        *,
        after_id: int = 0,
    ) -> dict[str, Any]:
        """Return A7 audit events for one auction session, oldest first.

        ``change_log`` remains the single audit backend.  The cursor is a global
        change-log ID, so unrelated rows are skipped only once and later polls
        can continue strictly after ``last_log_id`` without rereading history.
        """
        auction_id = int(auction_id)
        cursor = max(0, int(after_id or 0))

        with self.connect() as conn:
            if cursor <= 0:
                first = conn.execute(
                    """
                    SELECT MIN(id) AS first_id
                    FROM change_log
                    WHERE entity_type='auction_session' AND entity_id=?
                    """,
                    (auction_id,),
                ).fetchone()
                if first is None or first["first_id"] is None:
                    return {"events": [], "last_log_id": 0}
                cursor = max(0, int(first["first_id"]) - 1)

            high_water_row = conn.execute(
                "SELECT MAX(id) AS last_id FROM change_log"
            ).fetchone()
            high_water = int(high_water_row["last_id"] or cursor)
            if high_water <= cursor:
                return {"events": [], "last_log_id": cursor}

            rows = conn.execute(
                """
                SELECT *
                FROM change_log
                WHERE id>? AND id<=?
                  AND entity_type IN ('auction_session','auction_bid','auction_lot')
                ORDER BY id ASC
                """,
                (cursor, high_water),
            ).fetchall()

            entry_rows = conn.execute(
                """
                SELECT id, game_id, snapshot_title
                FROM auction_entries
                WHERE auction_id=?
                """,
                (auction_id,),
            ).fetchall()
            entry_map = {int(row["id"]): dict(row) for row in entry_rows}
            title_by_game = {
                int(row["game_id"]): str(row["snapshot_title"] or "")
                for row in entry_rows
                if row["game_id"] is not None
            }

            events: list[dict[str, Any]] = []
            last_log_id = high_water
            for row in rows:

                def _payload(raw: Any) -> dict[str, Any]:
                    if not raw:
                        return {}
                    try:
                        value = json.loads(str(raw))
                    except (TypeError, ValueError, json.JSONDecodeError):
                        return {}
                    return value if isinstance(value, dict) else {}

                before = _payload(row["before_json"])
                after = _payload(row["after_json"])
                entity_type = str(row["entity_type"] or "")
                entity_id = row["entity_id"]

                belongs = bool(
                    entity_type == "auction_session"
                    and entity_id is not None
                    and int(entity_id) == auction_id
                )
                if not belongs:
                    payload_auction_id = after.get("auction_id", before.get("auction_id"))
                    try:
                        belongs = int(payload_auction_id) == auction_id
                    except (TypeError, ValueError):
                        belongs = False
                if not belongs:
                    continue

                game_id = after.get("game_id")
                if game_id is None:
                    game_id = before.get("game_id")
                title = str(after.get("title") or before.get("title") or "")

                if entity_type == "auction_bid":
                    try:
                        entry = entry_map.get(int(entity_id)) if entity_id is not None else None
                    except (TypeError, ValueError):
                        entry = None
                    if entry is not None:
                        if game_id is None:
                            game_id = entry.get("game_id")
                        if not title:
                            title = str(entry.get("snapshot_title") or "")

                if entity_type == "auction_lot" and game_id is None and entity_id is not None:
                    game_id = entity_id

                if entity_type == "auction_session" and game_id is None:
                    game_id = after.get("winner_game_id")
                    if game_id is None:
                        game_id = before.get("winner_game_id")

                try:
                    normalized_game_id = int(game_id) if game_id is not None else None
                except (TypeError, ValueError):
                    normalized_game_id = None
                if not title and normalized_game_id is not None:
                    title = title_by_game.get(normalized_game_id, "")

                events.append(
                    {
                        "id": int(row["id"]),
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "action": str(row["action"] or ""),
                        "created_at": row["created_at"],
                        "before": before,
                        "after": after,
                        "game_id": normalized_game_id,
                        "title": title,
                    }
                )

            return {"events": events, "last_log_id": last_log_id}

    def list_auction_integration_bets(
        self,
        auction_id: int,
        *,
        after_id: int = 0,
    ) -> dict[str, Any]:
        """Return B5 accepted integration bets for one auction, oldest first.

        ``change_log`` is the cursor/high-water source, while the authoritative
        source/contributor/value fields are read back from ``external_events``
        and ``contributions``.  Only successful ``integration_event`` apply
        rows whose saved ``auction_id`` equals this exact session are exposed.
        Outside-auction credits, Pending/inapplicable events and events from
        other sessions therefore cannot leak into the operator feed.
        """
        auction_id = int(auction_id)
        cursor = max(0, int(after_id or 0))

        with self.connect() as conn:
            if cursor <= 0:
                first = conn.execute(
                    """
                    SELECT MIN(id) AS first_id
                    FROM change_log
                    WHERE entity_type='auction_session' AND entity_id=?
                    """,
                    (auction_id,),
                ).fetchone()
                if first is None or first["first_id"] is None:
                    return {"events": [], "last_log_id": 0}
                cursor = max(0, int(first["first_id"]) - 1)

            high_water_row = conn.execute(
                "SELECT MAX(id) AS last_id FROM change_log"
            ).fetchone()
            high_water = int(high_water_row["last_id"] or cursor)
            if high_water <= cursor:
                return {"events": [], "last_log_id": cursor}

            rows = conn.execute(
                """
                SELECT
                    cl.id,
                    cl.entity_id,
                    cl.action,
                    cl.before_json,
                    cl.after_json,
                    cl.created_at,
                    ee.source AS event_source,
                    ee.external_event_id AS event_external_id,
                    ee.event_type AS event_type,
                    ee.payload_json AS event_payload_json,
                    ee.processing_status AS event_status,
                    c.game_id AS contribution_game_id,
                    c.source AS contribution_source,
                    c.external_event_id AS contribution_external_id,
                    c.contributor AS contributor,
                    c.source_amount_text AS contribution_source_amount_text,
                    c.source_unit AS contribution_source_unit,
                    c.conversion_rate AS contribution_conversion_rate,
                    c.credited_sm_points AS contribution_credited_sm_points
                FROM change_log cl
                LEFT JOIN external_events ee
                    ON ee.id = cl.entity_id
                LEFT JOIN contributions c
                    ON c.source = ee.source
                   AND c.external_event_id = ee.external_event_id
                WHERE cl.id>? AND cl.id<=?
                  AND cl.entity_type='integration_event'
                  AND cl.action IN ('apply','apply_pending')
                ORDER BY cl.id ASC
                """,
                (cursor, high_water),
            ).fetchall()

            entry_rows = conn.execute(
                """
                SELECT game_id, snapshot_title
                FROM auction_entries
                WHERE auction_id=?
                """,
                (auction_id,),
            ).fetchall()
            title_by_game = {
                int(row["game_id"]): str(row["snapshot_title"] or "")
                for row in entry_rows
                if row["game_id"] is not None
            }

            events: list[dict[str, Any]] = []
            for row in rows:
                def _payload(raw: Any) -> dict[str, Any]:
                    if not raw:
                        return {}
                    try:
                        value = json.loads(str(raw))
                    except (TypeError, ValueError, json.JSONDecodeError):
                        return {}
                    return value if isinstance(value, dict) else {}

                after = _payload(row["after_json"])
                try:
                    payload_auction_id = int(after.get("auction_id"))
                except (TypeError, ValueError):
                    continue
                if payload_auction_id != auction_id:
                    continue
                if str(row["event_status"] or "") != "processed":
                    continue

                provider_payload = _payload(row["event_payload_json"])
                normalized = provider_payload.get("normalized")
                if not isinstance(normalized, dict):
                    normalized = {}

                source = str(
                    row["contribution_source"]
                    or row["event_source"]
                    or after.get("source")
                    or normalized.get("service_key")
                    or ""
                )
                external_event_id = str(
                    row["contribution_external_id"]
                    or row["event_external_id"]
                    or after.get("external_event_id")
                    or normalized.get("external_event_id")
                    or ""
                )
                game_id = row["contribution_game_id"]
                if game_id is None:
                    game_id = after.get("game_id", normalized.get("game_id"))
                try:
                    normalized_game_id = int(game_id) if game_id is not None else None
                except (TypeError, ValueError):
                    normalized_game_id = None

                title = str(
                    title_by_game.get(normalized_game_id, "")
                    if normalized_game_id is not None else ""
                ).strip()
                if not title:
                    title = str(
                        after.get("lot_title")
                        or normalized.get("lot_title")
                        or ""
                    ).strip()
                if not title and normalized_game_id is not None:
                    game_row = conn.execute(
                        "SELECT title FROM games WHERE id=?",
                        (normalized_game_id,),
                    ).fetchone()
                    if game_row is not None:
                        title = str(game_row["title"] or "")

                source_amount_text = str(
                    row["contribution_source_amount_text"]
                    or after.get("source_amount_text")
                    or normalized.get("source_amount_text")
                    or ""
                )
                source_unit = str(
                    row["contribution_source_unit"]
                    or after.get("source_unit")
                    or normalized.get("source_unit")
                    or ""
                )
                source_unit_label = str(
                    normalized.get("source_unit_label")
                    or source_unit
                )
                conversion_rate = str(
                    row["contribution_conversion_rate"]
                    or after.get("conversion_rate")
                    or ""
                )
                credited = row["contribution_credited_sm_points"]
                if credited is None:
                    credited = after.get("credited_sm_points")
                try:
                    credited_sm_points = int(credited)
                except (TypeError, ValueError):
                    continue

                contributor = str(
                    row["contributor"]
                    or normalized.get("contributor")
                    or ""
                )

                events.append(
                    {
                        "id": int(row["id"]),
                        "external_event_row_id": int(row["entity_id"]),
                        "action": str(row["action"] or ""),
                        "created_at": row["created_at"],
                        "source": source,
                        "external_event_id": external_event_id,
                        "event_type": str(row["event_type"] or ""),
                        "contributor": contributor,
                        "game_id": normalized_game_id,
                        "title": title,
                        "source_amount_text": source_amount_text,
                        "source_unit": source_unit,
                        "source_unit_label": source_unit_label,
                        "conversion_rate": conversion_rate,
                        "credited_sm_points": credited_sm_points,
                    }
                )

            return {"events": events, "last_log_id": high_water}

    COMPLETED_AUCTION_STATUSES = (
        "confirmed", "cancelled", "finished_no_winner", "finished",
    )

    @staticmethod
    def _completed_auction_filters(
        *,
        search_text: str = "",
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[str, list[Any]]:
        clauses = ["s.status IN ('confirmed','cancelled','finished_no_winner','finished')"]
        params: list[Any] = []
        if date_from:
            clauses.append("COALESCE(s.finished_at, s.started_at, s.created_at) >= ?")
            params.append(str(date_from))
        if date_to:
            clauses.append("COALESCE(s.finished_at, s.started_at, s.created_at) < ?")
            params.append(str(date_to))
        query = str(search_text or "").strip()
        if query:
            pattern = f"%{query}%"
            clauses.append(
                "(" 
                "s.name LIKE ? COLLATE NOCASE OR CAST(s.id AS TEXT) LIKE ? OR "
                "EXISTS (SELECT 1 FROM auction_entries se "
                "        WHERE se.auction_id=s.id "
                "          AND COALESCE(se.result,'') <> 'removed' "
                "          AND se.snapshot_title LIKE ? COLLATE NOCASE)"
                ")"
            )
            params.extend((pattern, pattern, pattern))
        return " AND ".join(clauses), params

    def list_completed_auction_sessions(
        self,
        *,
        search_text: str = "",
        date_from: str | None = None,
        date_to: str | None = None,
        sort_order: str = "newest",
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        where_sql, params = self._completed_auction_filters(
            search_text=search_text, date_from=date_from, date_to=date_to,
        )
        sort_sql = {
            "oldest": "sort_time ASC, s.id ASC",
            "name_asc": "s.name COLLATE NOCASE ASC, sort_time DESC, s.id DESC",
            "name_desc": "s.name COLLATE NOCASE DESC, sort_time DESC, s.id DESC",
        }.get(sort_order, "sort_time DESC, s.id DESC")
        limit = max(1, min(500, int(limit or 50)))
        offset = max(0, int(offset or 0))
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    s.*,
                    COALESCE(s.finished_at, s.started_at, s.created_at) AS sort_time,
                    (SELECT COUNT(*) FROM auction_entries ce
                     WHERE ce.auction_id=s.id AND COALESCE(ce.result,'') <> 'removed') AS lot_count,
                    (SELECT we.snapshot_title FROM auction_entries we
                     WHERE we.auction_id=s.id
                       AND COALESCE(we.result,'') <> 'removed'
                       AND (we.result='winner' OR (s.winner_game_id IS NOT NULL AND we.game_id=s.winner_game_id))
                     ORDER BY CASE WHEN we.result='winner' THEN 0 ELSE 1 END, we.id
                     LIMIT 1) AS winner_title
                FROM auction_sessions s
                WHERE {where_sql}
                ORDER BY {sort_sql}
                LIMIT ? OFFSET ?
                """,
                (*params, limit, offset),
            ).fetchall()
        return [dict(row) for row in rows]

    def completed_auction_summary(
        self,
        *,
        search_text: str = "",
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, int]:
        where_sql, params = self._completed_auction_filters(
            search_text=search_text, date_from=date_from, date_to=date_to,
        )
        with self.connect() as conn:
            row = conn.execute(
                f"""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN s.status='confirmed' THEN 1 ELSE 0 END) AS confirmed,
                    SUM(CASE WHEN s.status='cancelled' THEN 1 ELSE 0 END) AS cancelled,
                    SUM(CASE WHEN s.status='finished_no_winner' THEN 1 ELSE 0 END) AS no_winner
                FROM auction_sessions s
                WHERE {where_sql}
                """,
                params,
            ).fetchone()
        return {
            "total": int(row["total"] or 0),
            "confirmed": int(row["confirmed"] or 0),
            "cancelled": int(row["cancelled"] or 0),
            "no_winner": int(row["no_winner"] or 0),
        }

    def completed_auction_details(self, auction_id: int) -> dict[str, Any] | None:
        auction_id = int(auction_id)
        with self.connect() as conn:
            session = conn.execute(
                "SELECT *, COALESCE(finished_at, started_at, created_at) AS sort_time "
                "FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            if session is None or str(session["status"] or "") not in self.COMPLETED_AUCTION_STATUSES:
                return None
            entries = conn.execute(
                """
                SELECT id AS entry_id, auction_id, game_id, result,
                       starting_sm_points, bid_sm_points, start_position,
                       (starting_sm_points + bid_sm_points) AS total_sm_points,
                       snapshot_title, snapshot_release_date, snapshot_coop,
                       snapshot_status, snapshot_review
                FROM auction_entries
                WHERE auction_id=? AND COALESCE(result,'') <> 'removed'
                ORDER BY CASE WHEN start_position IS NULL THEN 1 ELSE 0 END,
                         start_position ASC, id ASC
                """,
                (auction_id,),
            ).fetchall()
            winner_title = ""
            for entry in entries:
                if entry["result"] == "winner" or (
                    session["winner_game_id"] is not None
                    and entry["game_id"] == session["winner_game_id"]
                ):
                    winner_title = str(entry["snapshot_title"] or "")
                    break
        return {
            "session": dict(session),
            "entries": [dict(row) for row in entries],
            "winner_title": winner_title,
        }

    def _auction_position_map_conn(
        self, conn: sqlite3.Connection
    ) -> dict[int, tuple[int, int]]:
        """Position map through an already-open connection for UI snapshots."""
        session = self._get_open_auction_session_conn(conn)
        if session is None:
            rows = conn.execute(
                """
                SELECT id
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
            return {
                int(row["id"]): (position, position)
                for position, row in enumerate(rows, start=1)
            }

        rows = conn.execute(
            """
            SELECT
                ae.game_id,
                ae.start_position,
                (ae.starting_sm_points + ae.bid_sm_points) AS total_sm_points,
                COALESCE(g.title, ae.snapshot_title) AS title,
                ae.id AS entry_id
            FROM auction_entries ae
            LEFT JOIN games g ON g.id = ae.game_id
            WHERE ae.auction_id=? AND ae.active=1
            ORDER BY
                total_sm_points DESC,
                CASE WHEN ae.start_position IS NULL THEN 1 ELSE 0 END ASC,
                ae.start_position ASC,
                COALESCE(g.title, ae.snapshot_title) COLLATE NOCASE ASC,
                ae.game_id ASC,
                ae.id ASC
            """,
            (int(session["id"]),),
        ).fetchall()

        positions: dict[int, tuple[int, int]] = {}
        for current_position, row in enumerate(rows, start=1):
            game_id = row["game_id"]
            start_position = row["start_position"]
            if game_id is None or start_position is None:
                continue
            positions[int(game_id)] = (
                int(start_position),
                current_position,
            )
        return positions

    def auction_position_map(self) -> dict[int, tuple[int, int]]:
        """Return displayed (start, current) positions by live game id.

        This remains the public compatibility method.  UI refresh snapshots can
        reuse :meth:`_auction_position_map_conn` so Games/Public data, counters
        and positions share one SQLite connection instead of several short
        connections per refresh.
        """
        with self.connect() as conn:
            return self._auction_position_map_conn(conn)

    @staticmethod
    def _remaining_ms_from_session(session: dict[str, Any]) -> int:
        status = str(session.get("status") or "")
        if status == "paused":
            stored_ms = session.get("remaining_ms")
            if stored_ms is not None:
                return max(0, int(stored_ms))
            return max(0, int(session.get("remaining_seconds") or 0) * 1000)
        if status != "running":
            return 0

        deadline_raw = session.get("deadline_at")
        if not deadline_raw:
            stored_ms = session.get("remaining_ms")
            if stored_ms is not None:
                return max(0, int(stored_ms))
            return max(0, int(session.get("remaining_seconds") or 0) * 1000)
        try:
            deadline = datetime.fromisoformat(str(deadline_raw))
            now = datetime.now(timezone.utc)
            milliseconds = (deadline - now).total_seconds() * 1000.0
            return max(0, math.ceil(milliseconds))
        except (TypeError, ValueError):
            stored_ms = session.get("remaining_ms")
            if stored_ms is not None:
                return max(0, int(stored_ms))
            return max(0, int(session.get("remaining_seconds") or 0) * 1000)

    @classmethod
    def _remaining_from_session(cls, session: dict[str, Any]) -> int:
        """Compatibility seconds view, rounded upward like the old timer."""
        remaining_ms = cls._remaining_ms_from_session(session)
        return max(0, math.ceil(remaining_ms / 1000))

    def auction_remaining_milliseconds(self, auction_id: int) -> int:
        session = self.get_auction_session(auction_id)
        if session is None:
            return 0
        return self._remaining_ms_from_session(session)

    def auction_remaining_seconds(self, auction_id: int) -> int:
        remaining_ms = self.auction_remaining_milliseconds(auction_id)
        return max(0, math.ceil(remaining_ms / 1000))

    @staticmethod
    def _auto_extend_bool(value: Any, default: bool) -> bool:
        if value is None:
            return bool(default)
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", ""}:
            return False
        return bool(default)

    @staticmethod
    def _auto_extend_duration(value: Any, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return int(default)
        if not 1 <= parsed <= AUCTION_AUTO_EXTEND_MAX_MS:
            return int(default)
        return parsed

    def _auto_extend_settings_conn(self, conn: sqlite3.Connection) -> dict[str, Any]:
        """Read S2 configuration using the caller's current transaction."""
        keys = (
            AUCTION_AUTO_EXTEND_LEADER_ENABLED_KEY,
            AUCTION_AUTO_EXTEND_LEADER_MS_KEY,
            AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_KEY,
            AUCTION_AUTO_EXTEND_NEW_LOT_MS_KEY,
            AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_KEY,
            AUCTION_AUTO_EXTEND_EXTERNAL_SERVICE_UNITS_ENABLED_KEY,
            AUCTION_AUTO_EXTEND_EXTERNAL_MS_KEY,
            AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_KEY,
            AUCTION_AUTO_EXTEND_THRESHOLD_MS_KEY,
        )
        placeholders = ",".join("?" for _ in keys)
        rows = conn.execute(
            f"SELECT key,value FROM settings WHERE key IN ({placeholders})",
            keys,
        ).fetchall()
        values = {str(row["key"]): str(row["value"]) for row in rows}
        return {
            "leader_change": {
                "enabled": self._auto_extend_bool(
                    values.get(AUCTION_AUTO_EXTEND_LEADER_ENABLED_KEY),
                    AUCTION_AUTO_EXTEND_LEADER_ENABLED_DEFAULT,
                ),
                "extension_ms": self._auto_extend_duration(
                    values.get(AUCTION_AUTO_EXTEND_LEADER_MS_KEY),
                    AUCTION_AUTO_EXTEND_LEADER_MS_DEFAULT,
                ),
            },
            "new_lot": {
                "enabled": self._auto_extend_bool(
                    values.get(AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_KEY),
                    AUCTION_AUTO_EXTEND_NEW_LOT_ENABLED_DEFAULT,
                ),
                "extension_ms": self._auto_extend_duration(
                    values.get(AUCTION_AUTO_EXTEND_NEW_LOT_MS_KEY),
                    AUCTION_AUTO_EXTEND_NEW_LOT_MS_DEFAULT,
                ),
            },
            "external_donation": {
                "enabled": self._auto_extend_bool(
                    values.get(AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_KEY),
                    AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_DEFAULT,
                ),
                "extension_ms": self._auto_extend_duration(
                    values.get(AUCTION_AUTO_EXTEND_EXTERNAL_MS_KEY),
                    AUCTION_AUTO_EXTEND_EXTERNAL_MS_DEFAULT,
                ),
            },
            "external_service_unit": {
                "enabled": (
                    self._auto_extend_bool(
                        values.get(AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_KEY),
                        AUCTION_AUTO_EXTEND_EXTERNAL_ENABLED_DEFAULT,
                    )
                    and self._auto_extend_bool(
                        values.get(
                            AUCTION_AUTO_EXTEND_EXTERNAL_SERVICE_UNITS_ENABLED_KEY
                        ),
                        AUCTION_AUTO_EXTEND_EXTERNAL_SERVICE_UNITS_ENABLED_DEFAULT,
                    )
                ),
                "extension_ms": self._auto_extend_duration(
                    values.get(AUCTION_AUTO_EXTEND_EXTERNAL_MS_KEY),
                    AUCTION_AUTO_EXTEND_EXTERNAL_MS_DEFAULT,
                ),
            },
            "threshold_enabled": self._auto_extend_bool(
                values.get(AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_KEY),
                AUCTION_AUTO_EXTEND_THRESHOLD_ENABLED_DEFAULT,
            ),
            "threshold_ms": self._auto_extend_duration(
                values.get(AUCTION_AUTO_EXTEND_THRESHOLD_MS_KEY),
                AUCTION_AUTO_EXTEND_THRESHOLD_MS_DEFAULT,
            ),
        }

    def _maybe_auto_extend_auction_timer_conn(
        self,
        conn: sqlite3.Connection,
        auction_id: int,
        *,
        reason_codes: list[str] | tuple[str, ...],
        origin_action: str,
        game_id: int | None = None,
        source: str | None = None,
        external_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply at most one S2 extension for one originating business action.

        The caller supplies semantic reasons discovered while performing the
        action. This helper filters them by persisted settings, applies the
        largest enabled extension once, respects the shared threshold and 24h
        ceiling, and writes one auditable ``auction_session/auto_extend`` row.
        It never queues an extension for paused/non-running sessions and never
        resurrects an expired deadline.
        """
        auction_id = int(auction_id)
        session_row = conn.execute(
            "SELECT * FROM auction_sessions WHERE id=?",
            (auction_id,),
        ).fetchone()
        if session_row is None:
            raise KeyError(auction_id)
        session = dict(session_row)
        if str(session.get("status") or "") != "running":
            return {"extended": False, "reason": "not_running"}

        before_ms = self._remaining_ms_from_session(session)
        if before_ms <= 0:
            return {"extended": False, "reason": "expired"}

        config = self._auto_extend_settings_conn(conn)
        if bool(config["threshold_enabled"]) and before_ms > int(config["threshold_ms"]):
            return {"extended": False, "reason": "above_threshold"}

        matched: list[dict[str, Any]] = []
        for code in dict.fromkeys(str(item) for item in reason_codes):
            reason = config.get(code)
            if not isinstance(reason, dict) or not bool(reason.get("enabled")):
                continue
            extension_ms = int(reason.get("extension_ms") or 0)
            if extension_ms <= 0:
                continue
            matched.append({"code": code, "extension_ms": extension_ms})

        if not matched:
            return {"extended": False, "reason": "no_enabled_reason"}

        requested_ms = max(int(item["extension_ms"]) for item in matched)
        after_ms = min(AUCTION_AUTO_EXTEND_MAX_MS, before_ms + requested_ms)
        actual_delta_ms = after_ms - before_ms
        if actual_delta_ms <= 0:
            return {"extended": False, "reason": "ceiling"}

        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat(timespec="microseconds")
        deadline = (now_dt + timedelta(milliseconds=after_ms)).isoformat(
            timespec="microseconds"
        )
        after_seconds = max(0, math.ceil(after_ms / 1000))
        before_seconds = max(0, math.ceil(before_ms / 1000))
        cursor = conn.execute(
            """
            UPDATE auction_sessions
            SET remaining_seconds=?, remaining_ms=?, deadline_at=?, updated_at=?
            WHERE id=? AND status='running'
            """,
            (after_seconds, after_ms, deadline, now, auction_id),
        )
        if cursor.rowcount != 1:
            return {"extended": False, "reason": "state_changed"}

        self._log_conn(
            conn,
            "auction_session",
            auction_id,
            "auto_extend",
            {
                "status": "running",
                "remaining_seconds": before_seconds,
                "remaining_ms": before_ms,
                "origin_action": str(origin_action),
                "game_id": int(game_id) if game_id is not None else None,
            },
            {
                "status": "running",
                "remaining_seconds": after_seconds,
                "remaining_ms": after_ms,
                "delta_ms": actual_delta_ms,
                "requested_extension_ms": requested_ms,
                "matched_reasons": [item["code"] for item in matched],
                "reason_extensions_ms": {
                    item["code"]: int(item["extension_ms"]) for item in matched
                },
                "origin_action": str(origin_action),
                "game_id": int(game_id) if game_id is not None else None,
                "source": str(source or ""),
                "external_event_id": (
                    str(external_event_id) if external_event_id is not None else None
                ),
            },
        )
        return {
            "extended": True,
            "before_ms": before_ms,
            "after_ms": after_ms,
            "delta_ms": actual_delta_ms,
            "requested_extension_ms": requested_ms,
            "matched_reasons": [item["code"] for item in matched],
        }

    def add_or_increment_auction_lot(
        self,
        auction_id: int,
        title: str,
        sm_points: int = 0,
        *,
        source: str = "manual_new_lot",
        contributor: str | None = None,
        external_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Добавляет новый лот только в активную сессию.

        Если такой лот уже есть в текущем аукционе, указанные баллы просто
        прибавляется к нему. Совершенно новая игра создаётся как auction_only=1
        и не видна на вкладках Игры/Публичный список до подтверждения результата.
        Этот же метод рассчитан на будущие донат-интеграции.
        """
        title = str(title or "").strip()
        key = normalize_title_key(title)
        if not key:
            raise ValueError("Введите название нового лота.")

        sm_points = int(sm_points)
        if sm_points < 0:
            raise ValueError("Баллы нового лота не могут быть отрицательными.")

        with self.connect() as conn:
            return self._add_or_increment_auction_lot_conn(
                conn,
                auction_id,
                title,
                sm_points,
                source=source,
                contributor=contributor,
                external_event_id=external_event_id,
            )

    def _add_or_increment_auction_lot_conn(
        self,
        conn: sqlite3.Connection,
        auction_id: int,
        title: str,
        sm_points: int,
        *,
        source: str,
        contributor: str | None,
        external_event_id: str | None,
        record_contribution: bool = True,
        extra_auto_extend_reasons: tuple[str, ...] = (),
        preferred_game_id: int | None = None,
    ) -> dict[str, Any]:
        """Transactional core shared by local lot actions and B3 events."""
        title = str(title or "").strip()
        key = normalize_title_key(title)
        if not key:
            raise ValueError("Введите название нового лота.")
        sm_points = int(sm_points)
        if sm_points < 0:
            raise ValueError("Баллы нового лота не могут быть отрицательными.")
        now = utc_now()
        session = conn.execute(
            "SELECT * FROM auction_sessions WHERE id=?",
            (auction_id,),
        ).fetchone()
        if session is None:
            raise KeyError(auction_id)
        if session["status"] != "running":
            raise RuntimeError(
                "Новые лоты можно добавлять только во время приёма ставок."
            )

        _before_max, before_leaders = self._max_leaders_conn(conn, auction_id)
        before_leader_set = set(before_leaders)

        # 1) Уже есть в этой сессии -> не плодим дубликат, а увеличиваем баллы.
        current_rows = conn.execute(
            """
            SELECT
                ae.id AS entry_id,
                ae.game_id,
                ae.starting_sm_points,
                ae.bid_sm_points,
                g.title
            FROM auction_entries ae
            JOIN games g ON g.id=ae.game_id
            WHERE ae.auction_id=? AND ae.active=1
            """,
            (auction_id,),
        ).fetchall()
        for row in current_rows:
            if preferred_game_id is not None:
                if int(row["game_id"]) != int(preferred_game_id):
                    continue
            elif normalize_title_key(row["title"]) != key:
                continue
            game_id = int(row["game_id"])
            if sm_points > 0:
                new_bid = int(row["bid_sm_points"]) + sm_points
                total = int(row["starting_sm_points"]) + new_bid
                conn.execute(
                    """
                    UPDATE auction_entries
                    SET bid_sm_points=?, weight=?
                    WHERE id=?
                    """,
                    (new_bid, total, int(row["entry_id"])),
                )
                conn.execute(
                    """
                    UPDATE games
                    SET sm_points=sm_points+?, updated_at=?
                    WHERE id=?
                    """,
                    (sm_points, now, game_id),
                )
                if record_contribution:
                    conn.execute(
                        """
                        INSERT INTO contributions(
                            game_id, source, external_event_id, contributor,
                            amount_minor, currency, points, unit, note, created_at,
                            source_amount_text, source_unit, conversion_rate,
                            credited_sm_points
                        )
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            game_id,
                            source,
                            external_event_id,
                            contributor,
                            None,
                            None,
                            sm_points,
                            "SM",
                            f"auction:{auction_id}:existing_lot",
                            now,
                            str(sm_points),
                            "SM",
                            "1",
                            sm_points,
                        ),
                    )
            self._log_conn(
                conn,
                "auction_lot",
                game_id,
                "increment" if sm_points > 0 else "reuse",
                None,
                {
                    "auction_id": auction_id,
                    "title": row["title"],
                    "added_sm_points": sm_points,
                    "source": source,
                },
            )
            reasons: list[str] = (
                list(
                    dict.fromkeys(
                        str(item) for item in extra_auto_extend_reasons if str(item)
                    )
                )
                if sm_points > 0
                else []
            )
            if sm_points > 0:
                _after_max, after_leaders = self._max_leaders_conn(conn, auction_id)
                if set(after_leaders) != before_leader_set:
                    reasons.append("leader_change")
            self._maybe_auto_extend_auction_timer_conn(
                conn,
                auction_id,
                reason_codes=reasons,
                origin_action=(
                    "auction_lot:increment" if sm_points > 0 else "auction_lot:reuse"
                ),
                game_id=game_id,
                source=source,
                external_event_id=external_event_id,
            )
            return {
                "game_id": game_id,
                "title": str(row["title"]),
                "created": False,
                "temporary": bool(
                    conn.execute(
                        "SELECT auction_only FROM games WHERE id=?",
                        (game_id,),
                    ).fetchone()[0]
                ),
                "merged": True,
            }

        # 2) Игра уже существует в основной базе, но не была в стартовом
        # снимке этого аукциона: подключаем её к сессии, не создавая дубль.
        game_row = None
        if preferred_game_id is not None:
            game_row = conn.execute(
                "SELECT * FROM games WHERE id=?",
                (int(preferred_game_id),),
            ).fetchone()
            if game_row is None:
                raise KeyError(preferred_game_id)
        else:
            for row in conn.execute(
                "SELECT * FROM games ORDER BY auction_only ASC, id ASC"
            ).fetchall():
                if normalize_title_key(row["title"]) == key:
                    game_row = row
                    break

        created = False
        temporary = False
        if game_row is None:
            # Совершенно новый лот. Пока аукцион не завершён, основные
            # представления его не видят.
            cursor = conn.execute(
                """
                INSERT INTO games(
                    title, release_date, sm_points, coop, status,
                    review, archived, auction_only, created_at, updated_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    title,
                    None,
                    sm_points,
                    0,
                    STATUS_NOT_PLAYED,
                    "",
                    0,
                    1,
                    now,
                    now,
                ),
            )
            game_id = int(cursor.lastrowid)
            starting = sm_points
            bid_amount = 0
            created = True
            temporary = True
        else:
            game_id = int(game_row["id"])
            starting = int(game_row["sm_points"])
            bid_amount = sm_points
            temporary = bool(game_row["auction_only"])
            if sm_points > 0:
                conn.execute(
                    """
                    UPDATE games
                    SET sm_points=sm_points+?, updated_at=?
                    WHERE id=?
                    """,
                    (sm_points, now, game_id),
                )

        total = starting + bid_amount
        conn.execute(
            """
            INSERT INTO auction_entries(
                auction_id, game_id, weight, active,
                starting_sm_points, bid_sm_points,
                snapshot_title, snapshot_release_date, snapshot_coop,
                snapshot_status, snapshot_review, start_position
            )
            SELECT ?, ?, ?, ?, ?, ?, title, release_date, coop, status, review, NULL
            FROM games
            WHERE id=?
            """,
            (
                auction_id,
                game_id,
                total,
                1,
                starting,
                bid_amount,
                game_id,
            ),
        )

        entry_id_row = conn.execute(
            "SELECT id FROM auction_entries WHERE auction_id=? AND game_id=?",
            (auction_id, game_id),
        ).fetchone()
        entry_id = int(entry_id_row["id"])
        ordered_entry_ids = [
            int(row["id"])
            for row in conn.execute(
                """
                SELECT ae.id
                FROM auction_entries ae
                LEFT JOIN games g ON g.id=ae.game_id
                WHERE ae.auction_id=? AND ae.active=1
                ORDER BY
                    (ae.starting_sm_points + ae.bid_sm_points) DESC,
                    CASE WHEN ae.start_position IS NULL THEN 1 ELSE 0 END ASC,
                    ae.start_position ASC,
                    COALESCE(g.title, ae.snapshot_title) COLLATE NOCASE ASC,
                    ae.game_id ASC,
                    ae.id ASC
                """,
                (auction_id,),
            ).fetchall()
        ]
        # A3: freeze the new lot at the position produced by the live
        # active-auction ordering.  Because existing rows already have
        # frozen positions, assigning the first candidate can itself
        # affect an equal-points tie.  Re-rank until the displayed frozen
        # position and the resulting live position agree.
        start_position = ordered_entry_ids.index(entry_id) + 1
        for _ in range(len(ordered_entry_ids) + 2):
            conn.execute(
                "UPDATE auction_entries SET start_position=? WHERE id=?",
                (start_position, entry_id),
            )
            reranked_ids = [
                int(row["id"])
                for row in conn.execute(
                    """
                    SELECT ae.id
                    FROM auction_entries ae
                    LEFT JOIN games g ON g.id=ae.game_id
                    WHERE ae.auction_id=? AND ae.active=1
                    ORDER BY
                        (ae.starting_sm_points + ae.bid_sm_points) DESC,
                        CASE WHEN ae.start_position IS NULL THEN 1 ELSE 0 END ASC,
                        ae.start_position ASC,
                        COALESCE(g.title, ae.snapshot_title) COLLATE NOCASE ASC,
                        ae.game_id ASC,
                        ae.id ASC
                    """,
                    (auction_id,),
                ).fetchall()
            ]
            live_position = reranked_ids.index(entry_id) + 1
            if live_position == start_position:
                break
            start_position = live_position
        else:
            raise RuntimeError(
                "Не удалось стабилизировать стартовую позицию нового лота."
            )

        if sm_points > 0 and record_contribution:
            conn.execute(
                """
                INSERT INTO contributions(
                    game_id, source, external_event_id, contributor,
                    amount_minor, currency, points, unit, note, created_at,
                    source_amount_text, source_unit, conversion_rate,
                    credited_sm_points
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    game_id,
                    source,
                    external_event_id,
                    contributor,
                    None,
                    None,
                    sm_points,
                    "SM",
                    f"auction:{auction_id}:new_lot",
                    now,
                    str(sm_points),
                    "SM",
                    "1",
                    sm_points,
                ),
            )

        self._log_conn(
            conn,
            "auction_lot",
            game_id,
            "create",
            None,
            {
                "auction_id": auction_id,
                "title": title,
                "starting_sm_points": starting,
                "added_sm_points": bid_amount,
                "temporary": temporary,
                "source": source,
            },
        )
        reasons: list[str] = (
            list(
                dict.fromkeys(
                    str(item) for item in extra_auto_extend_reasons if str(item)
                )
            )
            if sm_points > 0
            else []
        )
        if created and temporary:
            reasons.append("new_lot")
        if sm_points > 0:
            _after_max, after_leaders = self._max_leaders_conn(conn, auction_id)
            if set(after_leaders) != before_leader_set:
                reasons.append("leader_change")
        self._maybe_auto_extend_auction_timer_conn(
            conn,
            auction_id,
            reason_codes=reasons,
            origin_action="auction_lot:create",
            game_id=game_id,
            source=source,
            external_event_id=external_event_id,
        )
        return {
            "game_id": game_id,
            "title": title if created else str(game_row["title"]),
            "created": created,
            "temporary": temporary,
            "merged": False,
        }

    def add_auction_bid(
        self,
        auction_id: int,
        game_id: int,
        sm_points: int,
        contributor: str = "Ручная ставка",
    ) -> None:
        """Добавляет целые баллы SM к лоту и постоянному значению игры."""
        sm_points = int(sm_points)
        if sm_points <= 0:
            raise ValueError("Количество баллов должно быть больше нуля.")

        now = utc_now()
        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            if session is None:
                raise KeyError(auction_id)
            if session["status"] != "running":
                raise RuntimeError("Ставки принимаются только во время запущенного аукциона.")

            _before_max, before_leaders = self._max_leaders_conn(conn, auction_id)
            before_leader_set = set(before_leaders)

            entry = conn.execute(
                """
                SELECT * FROM auction_entries
                WHERE auction_id=? AND game_id=? AND active=1
                """,
                (auction_id, game_id),
            ).fetchone()
            if entry is None:
                raise ValueError("Выбранная игра не является активным лотом этого аукциона.")

            game = conn.execute(
                "SELECT * FROM games WHERE id=?",
                (game_id,),
            ).fetchone()
            if game is None:
                raise KeyError(game_id)

            before_total = int(entry["starting_sm_points"]) + int(
                entry["bid_sm_points"]
            )
            after_total = before_total + sm_points

            conn.execute(
                """
                UPDATE auction_entries
                SET bid_sm_points = bid_sm_points + ?,
                    weight = ?
                WHERE id=?
                """,
                (sm_points, after_total, entry["id"]),
            )
            conn.execute(
                """
                UPDATE games
                SET sm_points = sm_points + ?,
                    updated_at=?
                WHERE id=?
                """,
                (sm_points, now, game_id),
            )
            conn.execute(
                """
                INSERT INTO contributions(
                    game_id, source, external_event_id, contributor,
                    amount_minor, currency, points, unit, note, created_at,
                    source_amount_text, source_unit, conversion_rate,
                    credited_sm_points
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    game_id,
                    "local_auction",
                    None,
                    contributor,
                    None,
                    None,
                    sm_points,
                    "SM",
                    f"auction:{auction_id}",
                    now,
                    str(sm_points),
                    "SM",
                    "1",
                    sm_points,
                ),
            )
            self._log_conn(
                conn,
                "auction_bid",
                int(entry["id"]),
                "add",
                {
                    "auction_id": auction_id,
                    "game_id": game_id,
                    "sm_points": before_total,
                },
                {
                    "auction_id": auction_id,
                    "game_id": game_id,
                    "added_sm_points": sm_points,
                    "sm_points": after_total,
                },
            )
            _after_max, after_leaders = self._max_leaders_conn(conn, auction_id)
            reasons = (
                ["leader_change"]
                if set(after_leaders) != before_leader_set
                else []
            )
            self._maybe_auto_extend_auction_timer_conn(
                conn,
                auction_id,
                reason_codes=reasons,
                origin_action="auction_bid:add",
                game_id=game_id,
                source="local_auction",
            )

    def decrease_auction_bid(
        self,
        auction_id: int,
        game_id: int,
        sm_points: int,
    ) -> None:
        """Уменьшает только добавленные в текущем аукционе баллы лота.

        ``starting_sm_points`` — неизменяемая нижняя граница A4. Поэтому
        уменьшение разрешено только в пределах текущего ``bid_sm_points`` и
        никогда не откатывает доаукционную/base сумму. Операция атомарно
        уменьшает и auction entry, и постоянные баллы игры. Отрицательная
        contribution намеренно не создаётся: корректировка остаётся отдельным
        аудируемым change_log-событием ``decrease``.
        """
        sm_points = int(sm_points)
        if sm_points <= 0:
            raise ValueError("Количество баллов должно быть больше нуля.")

        now = utc_now()
        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            if session is None:
                raise KeyError(auction_id)
            if session["status"] != "running":
                raise RuntimeError("Корректировка доступна только во время запущенного аукциона.")

            entry = conn.execute(
                """
                SELECT * FROM auction_entries
                WHERE auction_id=? AND game_id=? AND active=1
                """,
                (auction_id, game_id),
            ).fetchone()
            if entry is None:
                raise ValueError("Выбранная игра не является активным лотом этого аукциона.")

            game = conn.execute(
                "SELECT * FROM games WHERE id=?",
                (game_id,),
            ).fetchone()
            if game is None:
                raise KeyError(game_id)

            starting = int(entry["starting_sm_points"])
            current_bid = int(entry["bid_sm_points"])
            if sm_points > current_bid:
                raise ValueError(
                    f"Можно уменьшить максимум на {current_bid} баллов. "
                    f"Ниже стартовой суммы {starting} опустить лот нельзя."
                )

            before_total = starting + current_bid
            after_bid = current_bid - sm_points
            after_total = starting + after_bid

            conn.execute(
                """
                UPDATE auction_entries
                SET bid_sm_points = bid_sm_points - ?,
                    weight = ?
                WHERE id=?
                """,
                (sm_points, after_total, entry["id"]),
            )
            conn.execute(
                """
                UPDATE games
                SET sm_points = sm_points - ?,
                    updated_at=?
                WHERE id=?
                """,
                (sm_points, now, game_id),
            )
            self._log_conn(
                conn,
                "auction_bid",
                int(entry["id"]),
                "decrease",
                {
                    "auction_id": auction_id,
                    "game_id": game_id,
                    "starting_sm_points": starting,
                    "bid_sm_points": current_bid,
                    "sm_points": before_total,
                },
                {
                    "auction_id": auction_id,
                    "game_id": game_id,
                    "starting_sm_points": starting,
                    "decreased_sm_points": sm_points,
                    "bid_sm_points": after_bid,
                    "sm_points": after_total,
                },
            )

    def delete_temporary_auction_lot(
        self,
        auction_id: int,
        game_id: int,
    ) -> dict[str, Any]:
        """Удаляет ошибочный temporary ``auction_only``-лот текущей сессии.

        A5 намеренно разрешает физическое удаление только совершенно новой
        временной игры текущего ``running``-аукциона. Обычные игры и уже
        promoted-лоты этим путём удалить нельзя. Историческая
        ``auction_entries``-строка сохраняется как ``active=0/result=removed``;
        ``game_id`` затем становится NULL через ON DELETE SET NULL. Связанные
        contributions удаляются штатным ON DELETE CASCADE, а независимый
        change_log сохраняет создание/ставки/удаление для аудита.
        """
        auction_id = int(auction_id)
        game_id = int(game_id)
        now = utc_now()

        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            if session is None:
                raise KeyError(auction_id)
            if session["status"] != "running":
                raise RuntimeError(
                    "Удалить временный лот можно только во время приёма ставок."
                )

            row = conn.execute(
                """
                SELECT
                    ae.id AS entry_id,
                    ae.starting_sm_points,
                    ae.bid_sm_points,
                    ae.start_position,
                    ae.snapshot_title,
                    g.title,
                    g.sm_points,
                    g.auction_only
                FROM auction_entries ae
                JOIN games g ON g.id=ae.game_id
                WHERE ae.auction_id=? AND ae.game_id=? AND ae.active=1
                """,
                (auction_id, game_id),
            ).fetchone()
            if row is None:
                raise ValueError(
                    "Выбранная игра не является активным лотом этого аукциона."
                )
            if int(row["auction_only"] or 0) != 1:
                raise ValueError(
                    "Удалить можно только временный лот, созданный в текущем аукционе."
                )

            entry_id = int(row["entry_id"])
            title = str(row["title"] or row["snapshot_title"] or "")
            starting = int(row["starting_sm_points"] or 0)
            bid = int(row["bid_sm_points"] or 0)
            total = starting + bid
            contribution_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM contributions WHERE game_id=?",
                    (game_id,),
                ).fetchone()[0]
            )

            # Сначала замораживаем историческую строку, затем удаляем только
            # temporary game. FK ON DELETE SET NULL оставляет snapshot записи.
            conn.execute(
                """
                UPDATE auction_entries
                SET active=0, result='removed'
                WHERE id=?
                """,
                (entry_id,),
            )
            self._log_conn(
                conn,
                "auction_lot",
                game_id,
                "delete",
                {
                    "auction_id": auction_id,
                    "entry_id": entry_id,
                    "game_id": game_id,
                    "title": title,
                    "starting_sm_points": starting,
                    "bid_sm_points": bid,
                    "sm_points": total,
                    "start_position": row["start_position"],
                    "temporary": True,
                    "contributions": contribution_count,
                },
                {
                    "auction_id": auction_id,
                    "entry_id": entry_id,
                    "game_id": None,
                    "title": title,
                    "active": False,
                    "result": "removed",
                    "temporary": True,
                },
            )
            conn.execute("DELETE FROM games WHERE id=?", (game_id,))

            return {
                "auction_id": auction_id,
                "entry_id": entry_id,
                "game_id": game_id,
                "title": title,
                "removed_contributions": contribution_count,
            }

    def pause_auction(self, auction_id: int) -> int:
        session = self.get_auction_session(auction_id)
        if session is None:
            raise KeyError(auction_id)
        if session["status"] != "running":
            raise RuntimeError("На паузу можно поставить только запущенный аукцион.")

        remaining_ms = self._remaining_ms_from_session(session)
        remaining = max(0, math.ceil(remaining_ms / 1000))
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE auction_sessions
                SET status='paused',
                    remaining_seconds=?,
                    remaining_ms=?,
                    deadline_at=NULL,
                    updated_at=?
                WHERE id=? AND status='running'
                """,
                (remaining, remaining_ms, now, auction_id),
            )
            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "pause",
                {"status": "running"},
                {
                    "status": "paused",
                    "remaining_seconds": remaining,
                    "remaining_ms": remaining_ms,
                },
            )
        return remaining

    def resume_auction(self, auction_id: int) -> int:
        session = self.get_auction_session(auction_id)
        if session is None:
            raise KeyError(auction_id)
        if session["status"] != "paused":
            raise RuntimeError("Продолжить можно только аукцион на паузе.")

        remaining_ms = self._remaining_ms_from_session(session)
        remaining = max(0, math.ceil(remaining_ms / 1000))
        if remaining_ms <= 0:
            self.finish_auction(auction_id)
            return 0

        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat(timespec="microseconds")
        deadline = (now_dt + timedelta(milliseconds=remaining_ms)).isoformat(
            timespec="microseconds"
        )
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE auction_sessions
                SET status='running',
                    deadline_at=?,
                    updated_at=?
                WHERE id=? AND status='paused'
                """,
                (deadline, now, auction_id),
            )
            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "resume",
                {"status": "paused"},
                {
                    "status": "running",
                    "remaining_seconds": remaining,
                    "remaining_ms": remaining_ms,
                },
            )
        return remaining

    def adjust_auction_time_ms(self, auction_id: int, delta_ms: int) -> int:
        """Changes remaining running/paused time with millisecond precision."""
        session = self.get_auction_session(auction_id)
        if session is None:
            raise KeyError(auction_id)
        status = str(session.get("status") or "")
        if status not in ("running", "paused"):
            raise RuntimeError(
                "Изменять таймер можно только у запущенного аукциона или на паузе."
            )

        before_ms = self._remaining_ms_from_session(session)
        if status == "running" and before_ms <= 0:
            return 0

        limit_ms = 24 * 60 * 60 * 1000
        after_ms = max(0, min(limit_ms, before_ms + int(delta_ms)))
        if after_ms == before_ms:
            return after_ms

        before_seconds = max(0, math.ceil(before_ms / 1000))
        after_seconds = max(0, math.ceil(after_ms / 1000))
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat(timespec="microseconds")
        deadline = (
            (now_dt + timedelta(milliseconds=after_ms)).isoformat(
                timespec="microseconds"
            )
            if status == "running" and after_ms > 0
            else None
        )
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE auction_sessions
                SET remaining_seconds=?, remaining_ms=?, deadline_at=?, updated_at=?
                WHERE id=? AND status=?
                """,
                (after_seconds, after_ms, deadline, now, auction_id, status),
            )
            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "adjust_time",
                {
                    "status": status,
                    "remaining_seconds": before_seconds,
                    "remaining_ms": before_ms,
                },
                {
                    "status": status,
                    "remaining_seconds": after_seconds,
                    "remaining_ms": after_ms,
                    "delta_ms": int(delta_ms),
                    "delta_seconds": int(delta_ms) / 1000,
                },
            )
        return after_ms

    def adjust_auction_time(self, auction_id: int, delta_seconds: int) -> int:
        """Compatibility seconds API used by older callers/tests."""
        remaining_ms = self.adjust_auction_time_ms(
            auction_id,
            int(delta_seconds) * 1000,
        )
        return max(0, math.ceil(remaining_ms / 1000))

    def reset_auction_timer_ms(self, auction_id: int) -> int:
        """Restores running/paused timer to its original millisecond duration."""
        session = self.get_auction_session(auction_id)
        if session is None:
            raise KeyError(auction_id)
        status = str(session.get("status") or "")
        if status not in ("running", "paused"):
            raise RuntimeError(
                "Сбрасывать таймер можно только у запущенного аукциона или на паузе."
            )

        before_ms = self._remaining_ms_from_session(session)
        duration_ms = session.get("duration_ms")
        if duration_ms is None:
            duration_ms = int(session.get("duration_seconds") or 0) * 1000
        duration_ms = max(AUCTION_MIN_DURATION_MS, min(AUCTION_MAX_DURATION_MS, int(duration_ms)))
        duration_seconds = max(1, math.ceil(duration_ms / 1000))
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat(timespec="microseconds")
        deadline = (
            (now_dt + timedelta(milliseconds=duration_ms)).isoformat(
                timespec="microseconds"
            )
            if status == "running"
            else None
        )
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE auction_sessions
                SET remaining_seconds=?, remaining_ms=?, deadline_at=?, updated_at=?
                WHERE id=? AND status=?
                """,
                (duration_seconds, duration_ms, deadline, now, auction_id, status),
            )
            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "reset_timer",
                {
                    "status": status,
                    "remaining_seconds": max(0, math.ceil(before_ms / 1000)),
                    "remaining_ms": before_ms,
                },
                {
                    "status": status,
                    "remaining_seconds": duration_seconds,
                    "remaining_ms": duration_ms,
                },
            )
        return duration_ms

    def reset_auction_timer(self, auction_id: int) -> int:
        duration_ms = self.reset_auction_timer_ms(auction_id)
        return max(0, math.ceil(duration_ms / 1000))

    def _max_leaders_conn(
        self,
        conn: sqlite3.Connection,
        auction_id: int,
    ) -> tuple[int, list[int]]:
        rows = conn.execute(
            """
            SELECT
                game_id,
                (starting_sm_points + bid_sm_points) AS total
            FROM auction_entries
            WHERE auction_id=? AND active=1
            ORDER BY total DESC, game_id ASC
            """,
            (auction_id,),
        ).fetchall()
        if not rows:
            return 0, []

        maximum = int(rows[0]["total"] or 0)
        leaders = [
            int(row["game_id"])
            for row in rows
            if int(row["total"] or 0) == maximum
        ]
        return maximum, leaders

    def finish_auction(self, auction_id: int) -> dict[str, Any]:
        """Останавливает приём ставок и переходит к результату выбранного режима."""
        now = utc_now()
        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            if session is None:
                raise KeyError(auction_id)
            if session["status"] not in ("running", "paused"):
                return dict(session)

            mode = str(session["mode"])
            winner_game_id: int | None = None
            tie_game_ids: list[int] = []

            if mode == "max_amount":
                _maximum, leaders = self._max_leaders_conn(conn, auction_id)
                if len(leaders) == 1:
                    winner_game_id = leaders[0]
                    new_status = "winner_selected"
                elif len(leaders) > 1:
                    tie_game_ids = leaders
                    new_status = "tie_break_required"
                else:
                    new_status = "finished_no_winner"
            elif mode == "weighted_wheel":
                new_status = "awaiting_wheel"
            else:
                raise RuntimeError("У текущего аукциона неизвестный режим.")

            conn.execute(
                """
                UPDATE auction_sessions
                SET status=?,
                    remaining_seconds=0,
                    remaining_ms=0,
                    deadline_at=NULL,
                    winner_game_id=?,
                    finished_at=?,
                    updated_at=?
                WHERE id=?
                """,
                (new_status, winner_game_id, now, now, auction_id),
            )

            if winner_game_id is not None:
                conn.execute(
                    """
                    UPDATE auction_entries
                    SET result=CASE
                        WHEN game_id=? THEN 'winner'
                        ELSE 'not_winner'
                    END
                    WHERE auction_id=?
                    """,
                    (winner_game_id, auction_id),
                )
            elif tie_game_ids:
                placeholders = ",".join("?" for _ in tie_game_ids)
                # Для дополнительного времени/колеса остаются только лидеры.
                # Остальные лоты не удаляются из истории, а лишь inactive.
                conn.execute(
                    f"""
                    UPDATE auction_entries
                    SET active=CASE
                            WHEN game_id IN ({placeholders}) THEN 1
                            ELSE 0
                        END,
                        result=CASE
                            WHEN game_id IN ({placeholders}) THEN 'tie'
                            ELSE 'not_winner'
                        END
                    WHERE auction_id=?
                    """,
                    (*tie_game_ids, *tie_game_ids, auction_id),
                )

            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "finish",
                {"status": session["status"]},
                {
                    "status": new_status,
                    "mode": mode,
                    "winner_game_id": winner_game_id,
                    "tie_game_ids": tie_game_ids,
                },
            )

            updated = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            return dict(updated)

    def set_auction_wheel_duration_ms(
        self,
        auction_id: int,
        wheel_duration_ms: int,
    ) -> int:
        """Обновляет длительность ещё не запущенного колеса."""
        wheel_duration_ms = int(wheel_duration_ms)
        if not (
            self.WHEEL_MIN_DURATION_MS
            <= wheel_duration_ms
            <= self.WHEEL_MAX_DURATION_MS
        ):
            raise ValueError(
                "Время вращения колеса должно быть от 00:00:03.000 "
                "до 24:00:00.000."
            )

        now = utc_now()
        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            if session is None:
                raise KeyError(auction_id)
            if session["status"] != "awaiting_wheel":
                raise RuntimeError(
                    "Время вращения можно менять только перед запуском колеса."
                )
            if session["wheel_spin_id"]:
                raise RuntimeError("Запущенное колесо уже нельзя перенастроить.")

            before_ms = int(session["wheel_duration_ms"] or 8000)
            if before_ms == wheel_duration_ms:
                return wheel_duration_ms

            conn.execute(
                """
                UPDATE auction_sessions
                SET wheel_duration_ms=?, updated_at=?
                WHERE id=?
                """,
                (wheel_duration_ms, now, auction_id),
            )
            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "wheel_duration",
                {"wheel_duration_ms": before_ms},
                {"wheel_duration_ms": wheel_duration_ms},
            )
        return wheel_duration_ms

    def start_auction_tie_overtime(
        self,
        auction_id: int,
        duration_seconds: int,
        *,
        duration_ms: int | None = None,
    ) -> None:
        duration_seconds = int(duration_seconds)
        duration_ms = (
            int(duration_ms)
            if duration_ms is not None
            else duration_seconds * 1000
        )
        if duration_ms < AUCTION_MIN_DURATION_MS or duration_ms > AUCTION_MAX_DURATION_MS:
            raise ValueError(
                "Дополнительное время должно быть от 1 секунды до 24 часов."
            )
        # Старое секундное поле остаётся совместимым округлённым представлением,
        # а точное значение таймера хранится в миллисекундах.
        duration_seconds = max(1, math.ceil(duration_ms / 1000))

        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat(timespec="microseconds")
        deadline = (now_dt + timedelta(milliseconds=duration_ms)).isoformat(
            timespec="microseconds"
        )

        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            if session is None:
                raise KeyError(auction_id)
            if session["status"] != "tie_break_required":
                raise RuntimeError("Дополнительное время доступно только при ничьей.")

            conn.execute(
                """
                UPDATE auction_sessions
                SET status='running',
                    duration_seconds=?,
                    remaining_seconds=?,
                    duration_ms=?,
                    remaining_ms=?,
                    deadline_at=?,
                    winner_game_id=NULL,
                    finished_at=NULL,
                    updated_at=?
                WHERE id=?
                """,
                (
                    duration_seconds, duration_seconds, duration_ms, duration_ms,
                    deadline, now, auction_id,
                ),
            )
            conn.execute(
                """
                UPDATE auction_entries
                SET result=NULL
                WHERE auction_id=? AND active=1
                """,
                (auction_id,),
            )
            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "tie_overtime",
                {"status": "tie_break_required"},
                {
                    "status": "running",
                    "duration_seconds": duration_seconds,
                    "duration_ms": duration_ms,
                },
            )

    def start_auction_tie_wheel(
        self,
        auction_id: int,
        wheel_duration_ms: int | None = None,
    ) -> None:
        now = utc_now()
        if wheel_duration_ms is not None:
            wheel_duration_ms = int(wheel_duration_ms)
            if not (
                self.WHEEL_MIN_DURATION_MS
                <= wheel_duration_ms
                <= self.WHEEL_MAX_DURATION_MS
            ):
                raise ValueError(
                    "Время вращения колеса должно быть от 00:00:03.000 "
                    "до 24:00:00.000."
                )
        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            if session is None:
                raise KeyError(auction_id)
            if session["status"] != "tie_break_required":
                raise RuntimeError("Колесо как тай-брейк доступно только при ничьей.")

            effective_duration = (
                wheel_duration_ms
                if wheel_duration_ms is not None
                else int(session["wheel_duration_ms"] or 8000)
            )
            conn.execute(
                """
                UPDATE auction_sessions
                SET status='awaiting_wheel',
                    wheel_duration_ms=?,
                    updated_at=?
                WHERE id=?
                """,
                (effective_duration, now, auction_id),
            )
            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "tie_wheel",
                {"status": "tie_break_required"},
                {
                    "status": "awaiting_wheel",
                    "wheel_duration_ms": effective_duration,
                },
            )

    def confirm_auction_winner(self, auction_id: int) -> int:
        """Фиксирует результат и переводит выигравшую игру в ПРОХОДИТСЯ."""
        now = utc_now()
        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            if session is None:
                raise KeyError(auction_id)
            if session["status"] != "winner_selected":
                raise RuntimeError("В этой сессии ещё нет выбранного победителя.")

            winner_game_id = int(session["winner_game_id"])
            game = conn.execute(
                "SELECT * FROM games WHERE id=?",
                (winner_game_id,),
            ).fetchone()
            if game is None:
                raise RuntimeError("Игра-победитель больше не существует.")

            # Все временные лоты этой завершённой сессии теперь становятся
            # обычными играми. Незнакомые поля пользователь заполнит позже вручную.
            conn.execute(
                """
                UPDATE games
                SET auction_only=0,
                    updated_at=?
                WHERE auction_only=1
                  AND id IN (
                      SELECT game_id
                      FROM auction_entries
                      WHERE auction_id=?
                  )
                """,
                (now, auction_id),
            )
            conn.execute(
                """
                UPDATE games
                SET status=?,
                    archived=0,
                    updated_at=?
                WHERE id=?
                """,
                (STATUS_PLAYING, now, winner_game_id),
            )
            conn.execute(
                """
                UPDATE auction_sessions
                SET status='confirmed',
                    updated_at=?,
                    finished_at=COALESCE(finished_at, ?)
                WHERE id=?
                """,
                (now, now, auction_id),
            )
            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "confirm_winner",
                {"status": "winner_selected"},
                {
                    "status": "confirmed",
                    "winner_game_id": winner_game_id,
                },
            )
            return winner_game_id

    def cancel_auction(self, auction_id: int) -> None:
        """Закрывает текущую сессию без потери накопленных баллов SM.

        Временные лоты этой сессии становятся обычными играми. Это сохраняет
        их баллы и не оставляет скрытых ``auction_only``-записей, которые затем
        могли неожиданно объединяться с новым лотом того же имени.
        """
        now = utc_now()
        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM auction_sessions WHERE id=?",
                (auction_id,),
            ).fetchone()
            if session is None:
                raise KeyError(auction_id)
            if session["status"] not in self.AUCTION_OPEN_STATUSES:
                return

            promoted_rows = conn.execute(
                """
                SELECT g.id, g.title
                FROM games g
                JOIN auction_entries ae ON ae.game_id=g.id
                WHERE ae.auction_id=? AND g.auction_only=1
                ORDER BY g.id
                """,
                (auction_id,),
            ).fetchall()
            conn.execute(
                """
                UPDATE games
                SET auction_only=0, updated_at=?
                WHERE auction_only=1
                  AND id IN (
                      SELECT game_id
                      FROM auction_entries
                      WHERE auction_id=?
                  )
                """,
                (now, auction_id),
            )

            conn.execute(
                """
                UPDATE auction_sessions
                SET status='cancelled',
                    deadline_at=NULL,
                    remaining_seconds=0,
                    remaining_ms=0,
                    finished_at=COALESCE(finished_at, ?),
                    updated_at=?
                WHERE id=?
                """,
                (now, now, auction_id),
            )
            self._log_conn(
                conn,
                "auction_session",
                auction_id,
                "cancel",
                {"status": session["status"]},
                {
                    "status": "cancelled",
                    "promoted_temporary_lots": [
                        {"id": int(row["id"]), "title": str(row["title"])}
                        for row in promoted_rows
                    ],
                },
            )
