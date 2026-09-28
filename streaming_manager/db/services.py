from __future__ import annotations

import csv
import json
import sqlite3
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from ..constants import (
    AUCTION_MANUAL_BID_POINTS_DEFAULT, AUCTION_MANUAL_BID_POINTS_KEY,
    AUCTION_MANUAL_BID_POINTS_MAX, AUCTION_MANUAL_BID_POINTS_MIN,
    AUCTION_MIN_DURATION_MS, AUCTION_MAX_DURATION_MS,
    AUCTION_WHEEL_CHANCE_VISIBLE_DEFAULT, AUCTION_WHEEL_CHANCE_VISIBLE_KEY,
    AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_DEFAULT, AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_KEY,
    AUCTION_LOTS_OVERLAY_BACKGROUND_DEFAULT, AUCTION_LOTS_OVERLAY_BACKGROUND_KEY,
    AUCTION_LOTS_OVERLAY_BACKGROUND_MEDIA_ID_KEY,
    AUCTION_LOTS_OVERLAY_FONT_COLOR_DEFAULT, AUCTION_LOTS_OVERLAY_FONT_COLOR_KEY,
    AUCTION_LOTS_OVERLAY_FONT_FAMILY_DEFAULT, AUCTION_LOTS_OVERLAY_FONT_FAMILY_KEY,
    AUCTION_LOTS_OVERLAY_FONT_SIZE_DEFAULT, AUCTION_LOTS_OVERLAY_FONT_SIZE_KEY,
    TIMER_OVERLAY_BACKGROUND_COLOR_DEFAULT, TIMER_OVERLAY_BACKGROUND_COLOR_KEY,
    TIMER_OVERLAY_BACKGROUND_DEFAULT, TIMER_OVERLAY_BACKGROUND_KEY,
    TIMER_OVERLAY_FONT_COLOR_DEFAULT, TIMER_OVERLAY_FONT_COLOR_KEY,
    TIMER_OVERLAY_FONT_FAMILY_DEFAULT, TIMER_OVERLAY_FONT_FAMILY_KEY,
    TIMER_OVERLAY_FONT_SIZE_DEFAULT, TIMER_OVERLAY_FONT_SIZE_KEY,
    COOP_FROM_LABEL,
    STATUS_FROM_LABEL, STATUS_NOT_PLAYED, STATUS_PLAYED, STATUS_PLAYING,
)
from ..backup_restore import create_sqlite_backup, prune_backup_files
from ..media import (
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
    MEDIA_STORAGE_MANAGED,
    media_asset_available,
    media_kind_for_name,
    managed_media_directory,
)
from ..conversion import (
    BASE_CURRENCY_CONVERSION_UNITS, ConversionUnit, UNIT_KIND_CURRENCY,
    UNIT_KIND_SERVICE, convert_source_to_sm_points, decimal_to_storage_text,
    format_rate, infer_unit_kind, merge_conversion_units, normalize_unit_key,
    parse_decimal, parse_positive_rate,
)
from .common import (
    Game, points_from_text, display_date, format_points,
    normalize_title_key, parse_date, utc_now,
)


SECRET_SETTING_KEY_FRAGMENTS = (
    "token", "secret", "password", "passwd", "api_key", "apikey", "authorization", "bearer",
)


def _external_auto_extend_reasons(unit_kind: str) -> tuple[str, ...]:
    """Map normalized external units to one auditable S2 reason."""
    normalized = str(unit_kind or "").strip().lower()
    if normalized == UNIT_KIND_CURRENCY:
        return ("external_donation",)
    if normalized == UNIT_KIND_SERVICE:
        return ("external_service_unit",)
    return ()


def _setting_key_is_secret(key: str) -> bool:
    normalized = str(key).strip().casefold().replace("-", "_")
    if normalized.endswith("credential_ref") or normalized == "random_org_credential_ref":
        return False
    return any(fragment in normalized for fragment in SECRET_SETTING_KEY_FRAGMENTS)


def _setting_audit_value(key: str, value: str | None) -> str | None:
    # B1 no longer permits secret setting values at all.  This defensive
    # redaction remains for malformed/legacy callers and historical audits.
    if _setting_key_is_secret(key):
        return "[СКРЫТО]"
    return value


class ServicesMixin:
    def _log_conn(self, conn: sqlite3.Connection, entity_type: str, entity_id: int | None,
                  action: str, before: dict[str, Any] | None, after: dict[str, Any] | None) -> None:
        conn.execute(
            """INSERT INTO change_log(entity_type,entity_id,action,before_json,after_json,created_at)
               VALUES(?,?,?,?,?,?)""",
            (
                entity_type,
                entity_id,
                action,
                json.dumps(before, ensure_ascii=False, default=str) if before is not None else None,
                json.dumps(after, ensure_ascii=False, default=str) if after is not None else None,
                utc_now(),
            ),
        )

    def list_log(self, limit: int | None = 500) -> list[sqlite3.Row]:
        """Return journal rows newest first.

        The normal journal view intentionally keeps the historical 500-row
        window.  Search may pass ``None`` so filtering can cover the complete
        journal without silently ignoring older matches.
        """
        with self.connect() as conn:
            if limit is None:
                return conn.execute(
                    "SELECT * FROM change_log ORDER BY id DESC"
                ).fetchall()
            return conn.execute(
                "SELECT * FROM change_log ORDER BY id DESC LIMIT ?",
                (max(0, int(limit)),),
            ).fetchall()

    @staticmethod
    def _get_settings_conn(
        conn: sqlite3.Connection,
        keys: Iterable[str] | None = None,
    ) -> dict[str, str]:
        """Read settings through an already-open connection.

        Hot compound reads such as OBS payloads use this helper so one request
        does not repeatedly create/close SQLite connections for logically one
        snapshot.  Public callers keep the same ``get_settings`` API below.
        """
        if keys is None:
            rows = conn.execute(
                "SELECT key, value FROM settings"
            ).fetchall()
        else:
            wanted = tuple(dict.fromkeys(str(key) for key in keys))
            if not wanted:
                return {}
            placeholders = ",".join("?" for _ in wanted)
            rows = conn.execute(
                f"SELECT key, value FROM settings WHERE key IN ({placeholders})",
                wanted,
            ).fetchall()
        return {str(row["key"]): str(row["value"]) for row in rows}

    def get_settings(self, keys: Iterable[str] | None = None) -> dict[str, str]:
        """Reads settings in one SQLite connection.

        ``None`` returns the complete settings table. A key collection only
        fetches those values. This is intentionally the primary path for UI
        refreshes and OBS payloads; repeatedly opening SQLite for each key was
        one of the largest avoidable costs in 0.2.72.
        """
        with self.connect() as conn:
            return self._get_settings_conn(conn, keys)

    def get_setting(self, key: str, default: str = "") -> str:
        return self.get_settings((key,)).get(key, default)

    def set_settings_bulk(self, values: dict[str, Any]) -> int:
        """Atomically writes multiple settings and logs only real changes."""
        normalized = {str(key): str(value) for key, value in values.items()}
        forbidden = [key for key in normalized if _setting_key_is_secret(key)]
        if forbidden:
            raise ValueError(
                "Секреты нельзя хранить в SQLite settings; используйте CredentialStore: "
                + ", ".join(sorted(forbidden))
            )
        if not normalized:
            return 0

        keys = tuple(normalized)
        placeholders = ",".join("?" for _ in keys)
        changed = 0
        with self.connect() as conn:
            existing_rows = conn.execute(
                f"SELECT key, value FROM settings WHERE key IN ({placeholders})",
                keys,
            ).fetchall()
            existing = {
                str(row["key"]): str(row["value"])
                for row in existing_rows
            }

            for key, value in normalized.items():
                before = existing.get(key)
                if before == value:
                    continue
                conn.execute(
                    "INSERT INTO settings(key,value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, value),
                )
                self._log_conn(
                    conn,
                    "setting",
                    None,
                    "update",
                    {"key": key, "value": _setting_audit_value(key, before)},
                    {"key": key, "value": _setting_audit_value(key, value)},
                )
                changed += 1
        return changed

    def set_setting(self, key: str, value: str) -> None:
        self.set_settings_bulk({key: value})

    def get_auction_manual_bid_points(self) -> int:
        """Return the persisted shared manual auction amount or its safe default."""
        raw = self.get_setting(AUCTION_MANUAL_BID_POINTS_KEY, "")
        try:
            points = int(str(raw).strip())
        except (TypeError, ValueError):
            return AUCTION_MANUAL_BID_POINTS_DEFAULT
        if not AUCTION_MANUAL_BID_POINTS_MIN <= points <= AUCTION_MANUAL_BID_POINTS_MAX:
            return AUCTION_MANUAL_BID_POINTS_DEFAULT
        return points

    def set_auction_manual_bid_points(self, value: Any) -> int:
        """Persist the one shared manual auction amount after range validation."""
        try:
            points = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Количество баллов должно быть целым числом.") from exc
        if not AUCTION_MANUAL_BID_POINTS_MIN <= points <= AUCTION_MANUAL_BID_POINTS_MAX:
            raise ValueError(
                "Количество баллов должно быть от "
                f"{AUCTION_MANUAL_BID_POINTS_MIN} до {AUCTION_MANUAL_BID_POINTS_MAX}."
            )
        self.set_setting(AUCTION_MANUAL_BID_POINTS_KEY, str(points))
        return points

    def get_auction_wheel_chance_visible(self) -> bool:
        """Return persisted A6.1 desktop chance-column visibility."""
        default = bool(AUCTION_WHEEL_CHANCE_VISIBLE_DEFAULT)
        raw = self.get_setting(
            AUCTION_WHEEL_CHANCE_VISIBLE_KEY,
            "1" if default else "0",
        )
        normalized = str(raw).strip().casefold()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default

    def set_auction_wheel_chance_visible(self, visible: Any) -> bool:
        """Persist only the A6.1 presentation preference, never wheel math."""
        normalized = bool(visible)
        self.set_setting(
            AUCTION_WHEEL_CHANCE_VISIBLE_KEY,
            "1" if normalized else "0",
        )
        return normalized


    @staticmethod
    def _conversion_rate_key(source_unit: str) -> str:
        unit = normalize_unit_key(source_unit)
        return f"conversion_{unit.lower()}_points_per_unit"

    @staticmethod
    def _register_conversion_unit_conn(
        conn: sqlite3.Connection,
        descriptor: ConversionUnit,
    ) -> ConversionUnit:
        unit = descriptor.normalized_unit()
        kind = descriptor.normalized_kind()
        label = str(descriptor.label or unit).strip() or unit
        # Currency identity is global. A provider may report that it supports
        # USD, but the stored USD row must not become DonationAlerts-specific.
        service = "" if kind == UNIT_KIND_CURRENCY else str(descriptor.service or "").strip()
        now = utc_now()
        existing = conn.execute(
            "SELECT * FROM conversion_units WHERE unit=?",
            (unit,),
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO conversion_units("
                "unit,label,unit_kind,service,first_seen_at,last_seen_at"
                ") VALUES(?,?,?,?,?,?)",
                (unit, label, kind, service, now, now),
            )
        else:
            old_label = str(existing["label"] or unit)
            old_service = str(existing["service"] or "")
            old_kind = str(existing["unit_kind"] or kind)
            # Prefer explicit metadata over a fallback label=unit. Do not turn
            # an already global currency into a service-specific unit.
            final_kind = UNIT_KIND_CURRENCY if old_kind == UNIT_KIND_CURRENCY or kind == UNIT_KIND_CURRENCY else UNIT_KIND_SERVICE
            final_label = label if label != unit or old_label == unit else old_label
            final_service = "" if final_kind == UNIT_KIND_CURRENCY else (service or old_service)
            conn.execute(
                "UPDATE conversion_units SET label=?,unit_kind=?,service=?,last_seen_at=? "
                "WHERE unit=?",
                (final_label, final_kind, final_service, now, unit),
            )
        return ConversionUnit(unit, label, service, kind)

    def register_conversion_unit(
        self,
        source_unit: str,
        *,
        label: str | None = None,
        kind: str | None = None,
        service: str = "",
    ) -> ConversionUnit:
        unit = normalize_unit_key(source_unit)
        descriptor = ConversionUnit(
            unit,
            str(label or unit),
            str(service or ""),
            str(kind or infer_unit_kind(unit)),
        )
        with self.connect() as conn:
            self._register_conversion_unit_conn(conn, descriptor)
        return descriptor

    def list_registered_conversion_units(self) -> list[ConversionUnit]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT unit,label,unit_kind,service FROM conversion_units "
                "ORDER BY CASE unit_kind WHEN 'currency' THEN 0 ELSE 1 END, unit"
            ).fetchall()
        return [
            ConversionUnit(
                str(row["unit"]),
                str(row["label"]),
                str(row["service"] or ""),
                str(row["unit_kind"]),
            )
            for row in rows
        ]

    def get_conversion_rate(self, source_unit: str) -> str:
        unit = normalize_unit_key(source_unit)
        key = self._conversion_rate_key(unit)
        return self.get_setting(key, "1" if unit == "RUB" else "")

    def _update_pending_rate_status(self, source_unit: str, *, has_rate: bool) -> None:
        unit = normalize_unit_key(source_unit)
        target_status = "awaiting_manual_apply" if has_rate else "awaiting_rate"
        other_status = "awaiting_rate" if has_rate else "awaiting_manual_apply"
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id,external_event_row_id FROM pending_conversions "
                "WHERE source_unit=? AND status=?",
                (unit, other_status),
            ).fetchall()
            if not rows:
                return
            pending_ids = [int(row["id"]) for row in rows]
            event_ids = [int(row["external_event_row_id"]) for row in rows]
            placeholders = ",".join("?" for _ in pending_ids)
            conn.execute(
                f"UPDATE pending_conversions SET status=? WHERE id IN ({placeholders})",
                (target_status, *pending_ids),
            )
            event_placeholders = ",".join("?" for _ in event_ids)
            conn.execute(
                f"UPDATE external_events SET processing_status=? "
                f"WHERE id IN ({event_placeholders})",
                (target_status, *event_ids),
            )

    def set_conversion_rate(
        self,
        source_unit: str,
        points_per_unit: Any,
        *,
        label: str | None = None,
        kind: str | None = None,
        service: str = "",
    ) -> str:
        unit = normalize_unit_key(source_unit)
        normalized = format_rate(parse_positive_rate(points_per_unit)).replace(",", ".")
        self.register_conversion_unit(
            unit,
            label=label or unit,
            kind=kind or infer_unit_kind(unit),
            service=service,
        )
        self.set_setting(self._conversion_rate_key(unit), normalized)
        self._update_pending_rate_status(unit, has_rate=True)
        return normalized

    def clear_conversion_rate(self, source_unit: str) -> None:
        unit = normalize_unit_key(source_unit)
        # RUB keeps its explicit schema-default conversion if an empty editor is
        # submitted; other units may legitimately become unconfigured.
        value = "1" if unit == "RUB" else ""
        self.set_setting(self._conversion_rate_key(unit), value)
        self._update_pending_rate_status(unit, has_rate=bool(value))

    def visible_conversion_units(
        self,
        connected_service_units: Iterable[ConversionUnit] = (),
    ) -> list[ConversionUnit]:
        """Return rows that should currently be visible in Conversion settings.

        Persistent currencies are visible after they were encountered or got a
        saved rate. Connected adapters may add currencies and service-specific
        units transiently. Persisted service-specific units stay hidden while
        their adapter is disconnected; their saved rate remains in SQLite.
        """
        connected = list(connected_service_units)
        connected_keys = {item.normalized_unit() for item in connected}
        registered = self.list_registered_conversion_units()
        persistent_visible = [
            item for item in registered
            if item.normalized_kind() == UNIT_KIND_CURRENCY
            or item.normalized_unit() in connected_keys
        ]
        return merge_conversion_units(
            BASE_CURRENCY_CONVERSION_UNITS,
            persistent_visible,
            connected,
        )

    def convert_to_sm_points(self, amount: Any, source_unit: str) -> int:
        unit = normalize_unit_key(source_unit)
        rate = self.get_conversion_rate(unit)
        if not rate:
            raise ValueError(f"Для {unit} не настроен курс конвертации в баллы.")
        return convert_source_to_sm_points(amount, rate)

    @staticmethod
    def _sanitize_external_event_metadata(value: Any) -> Any:
        """Remove secret-looking provider fields before SQLite audit storage."""
        if isinstance(value, dict):
            clean: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key)
                if _setting_key_is_secret(key_text):
                    clean[key_text] = "[СКРЫТО]"
                else:
                    clean[key_text] = ServicesMixin._sanitize_external_event_metadata(item)
            return clean
        if isinstance(value, (list, tuple)):
            return [ServicesMixin._sanitize_external_event_metadata(item) for item in value]
        return value

    def _existing_external_event_result_conn(
        self,
        conn: sqlite3.Connection,
        event_row: sqlite3.Row,
    ) -> dict[str, Any]:
        event_row_id = int(event_row["id"])
        contribution = conn.execute(
            "SELECT game_id,credited_sm_points FROM contributions "
            "WHERE source=? AND external_event_id=? ORDER BY id DESC LIMIT 1",
            (str(event_row["source"]), str(event_row["external_event_id"])),
        ).fetchone()
        pending = conn.execute(
            "SELECT id,auction_id,game_id,status FROM pending_conversions "
            "WHERE external_event_row_id=?",
            (event_row_id,),
        ).fetchone()
        return {
            "status": str(event_row["processing_status"]),
            "duplicate": True,
            "external_event_row_id": event_row_id,
            "pending_id": int(pending["id"]) if pending is not None else None,
            "auction_id": (
                int(pending["auction_id"])
                if pending is not None and pending["auction_id"] is not None
                else None
            ),
            "game_id": (
                int(contribution["game_id"])
                if contribution is not None
                else (
                    int(pending["game_id"])
                    if pending is not None and pending["game_id"] is not None
                    else None
                )
            ),
            "credited_sm_points": (
                int(contribution["credited_sm_points"] or 0)
                if contribution is not None
                else None
            ),
        }

    def _mark_external_event_inapplicable_conn(
        self,
        conn: sqlite3.Connection,
        *,
        event_row_id: int,
        service_key: str,
        external_event_id: str,
        event_type: str,
        reason: str,
        game_id: int | None,
        lot_title: str,
        now: str,
    ) -> dict[str, Any]:
        conn.execute(
            "UPDATE external_events SET processing_status='inapplicable',processed_at=? WHERE id=?",
            (now, int(event_row_id)),
        )
        self._log_conn(
            conn,
            "integration_event",
            int(event_row_id),
            "inapplicable",
            None,
            {
                "source": service_key,
                "external_event_id": external_event_id,
                "event_type": event_type,
                "game_id": int(game_id) if game_id is not None else None,
                "lot_title": lot_title,
                "reason": reason,
            },
        )
        return {
            "status": "inapplicable",
            "duplicate": False,
            "external_event_row_id": int(event_row_id),
            "game_id": int(game_id) if game_id is not None else None,
            "auction_id": None,
            "credited_sm_points": None,
            "reason": reason,
        }

    def process_normalized_integration_event(
        self,
        *,
        service_key: str,
        external_event_id: str,
        event_type: str,
        source_amount: Any,
        source_unit: str,
        contributor: str = "",
        game_id: int | None = None,
        lot_title: str = "",
        source_unit_label: str = "",
        unit_kind: str = "",
        note: str = "",
        provider_metadata: dict | None = None,
        auction_id_hint: int | None = None,
        force_outside_auction: bool = False,
    ) -> dict[str, Any]:
        """B3 provider-neutral automatic acceptance core.

        The adapter has already parsed and matched the provider payload.  This
        method owns deduplication, running-auction safety, conversion, the
        persistent-game path outside auctions, atomic auction/game/contribution
        mutation, raw-event audit and ``last_event_at``.
        """
        source = str(service_key or "").strip()
        provider_event_id = str(external_event_id or "").strip()
        normalized_event_type = str(event_type or "").strip()
        title = str(lot_title or "").strip()
        if not source:
            raise ValueError("Не указан сервис интеграции.")
        if not provider_event_id:
            raise ValueError("Не указан идентификатор внешнего события.")
        if not normalized_event_type:
            raise ValueError("Не указан тип внешнего события.")

        parsed_amount = parse_decimal(source_amount)
        if not parsed_amount.is_finite() or parsed_amount < 0:
            raise ValueError("Исходное значение не может быть отрицательным.")
        amount_text = decimal_to_storage_text(parsed_amount)
        unit = normalize_unit_key(source_unit)
        kind = str(unit_kind or infer_unit_kind(unit)).strip().lower()
        descriptor = ConversionUnit(
            unit,
            str(source_unit_label or unit),
            source if kind == UNIT_KIND_SERVICE else "",
            kind,
        )
        kind = descriptor.normalized_kind()
        normalized_game_id = int(game_id) if game_id is not None else None
        safe_metadata = self._sanitize_external_event_metadata(provider_metadata or {})
        payload = {
            "normalized": {
                "service_key": source,
                "external_event_id": provider_event_id,
                "event_type": normalized_event_type,
                "contributor": str(contributor or ""),
                "game_id": normalized_game_id,
                "lot_title": title,
                "source_amount_text": amount_text,
                "source_unit": unit,
                "source_unit_label": str(source_unit_label or unit),
                "unit_kind": kind,
                "note": str(note or ""),
                "auction_id_hint": int(auction_id_hint) if auction_id_hint is not None else None,
                "force_outside_auction": bool(force_outside_auction),
            },
            "provider_metadata": safe_metadata,
        }
        payload_text = json.dumps(payload, ensure_ascii=False, default=str, sort_keys=True)
        now = utc_now()

        with self.connect() as conn:
            connection = conn.execute(
                "SELECT enabled,status FROM integration_connections WHERE service_key=?",
                (source,),
            ).fetchone()
            if (
                connection is None
                or not bool(connection["enabled"])
                or str(connection["status"]) != "connected"
            ):
                raise RuntimeError(
                    "Внешнее событие можно принять только от включённой интеграции "
                    "в состоянии «Подключено»."
                )

            cursor = conn.execute(
                "INSERT OR IGNORE INTO external_events("
                "source,external_event_id,event_type,payload_json,processing_status,created_at"
                ") VALUES(?,?,?,?,?,?)",
                (
                    source,
                    provider_event_id,
                    normalized_event_type,
                    payload_text,
                    "processing",
                    now,
                ),
            )
            if cursor.rowcount == 0:
                existing = conn.execute(
                    "SELECT * FROM external_events WHERE source=? AND external_event_id=?",
                    (source, provider_event_id),
                ).fetchone()
                if existing is None:
                    raise RuntimeError("Не удалось разрешить duplicate external event.")
                return self._existing_external_event_result_conn(conn, existing)
            event_row_id = int(cursor.lastrowid)

            self._register_conversion_unit_conn(conn, descriptor)
            running_auction_id: int | None = None
            if force_outside_auction:
                # Source-time context explicitly says the event was created
                # outside a running auction.  A newer auction must not capture
                # delayed provider delivery.
                running_auction_id = None
            elif auction_id_hint is not None:
                hinted = self._get_auction_session_conn(conn, int(auction_id_hint))
                if hinted is None or str(hinted.get("status") or "") != "running":
                    return self._mark_external_event_inapplicable_conn(
                        conn,
                        event_row_id=event_row_id,
                        service_key=source,
                        external_event_id=provider_event_id,
                        event_type=normalized_event_type,
                        reason="source_auction_not_running",
                        game_id=normalized_game_id,
                        lot_title=title,
                        now=now,
                    )
                running_auction_id = int(hinted["id"])
            else:
                open_session = self._get_open_auction_session_conn(conn)
                running_auction_id = (
                    int(open_session["id"])
                    if open_session is not None and str(open_session.get("status") or "") == "running"
                    else None
                )

            game_row = None
            if normalized_game_id is not None:
                game_row = conn.execute(
                    "SELECT id,title,sm_points,archived,auction_only FROM games WHERE id=?",
                    (normalized_game_id,),
                ).fetchone()
                if game_row is None:
                    return self._mark_external_event_inapplicable_conn(
                        conn,
                        event_row_id=event_row_id,
                        service_key=source,
                        external_event_id=provider_event_id,
                        event_type=normalized_event_type,
                        reason="target_game_missing",
                        game_id=normalized_game_id,
                        lot_title=title,
                        now=now,
                    )
                if int(game_row["archived"]):
                    return self._mark_external_event_inapplicable_conn(
                        conn,
                        event_row_id=event_row_id,
                        service_key=source,
                        external_event_id=provider_event_id,
                        event_type=normalized_event_type,
                        reason="target_game_archived",
                        game_id=normalized_game_id,
                        lot_title=str(game_row["title"]),
                        now=now,
                    )
                if int(game_row["auction_only"]) and running_auction_id is None:
                    return self._mark_external_event_inapplicable_conn(
                        conn,
                        event_row_id=event_row_id,
                        service_key=source,
                        external_event_id=provider_event_id,
                        event_type=normalized_event_type,
                        reason="temporary_lot_not_running",
                        game_id=normalized_game_id,
                        lot_title=str(game_row["title"]),
                        now=now,
                    )
                title = str(game_row["title"])
            elif not title:
                return self._mark_external_event_inapplicable_conn(
                    conn,
                    event_row_id=event_row_id,
                    service_key=source,
                    external_event_id=provider_event_id,
                    event_type=normalized_event_type,
                    reason="missing_target",
                    game_id=None,
                    lot_title=title,
                    now=now,
                )
            elif running_auction_id is None:
                # Outside an auction a usable adapter-supplied title targets the
                # persistent game list.  Reuse an exact normalized title when it
                # already exists; otherwise defer creation until we know that the
                # event can actually be credited (known rate / explicit Pending
                # apply).  This prevents unknown-rate events from polluting the
                # catalogue before any points are accepted.
                matched_game = self._find_game_by_title_conn(conn, title)
                if matched_game is not None:
                    normalized_game_id = int(matched_game.id)
                    game_row = conn.execute(
                        "SELECT id,title,sm_points,archived,auction_only FROM games WHERE id=?",
                        (normalized_game_id,),
                    ).fetchone()
                    if game_row is None:
                        raise RuntimeError("Не удалось разрешить найденную постоянную игру.")
                    if int(game_row["archived"]):
                        return self._mark_external_event_inapplicable_conn(
                            conn,
                            event_row_id=event_row_id,
                            service_key=source,
                            external_event_id=provider_event_id,
                            event_type=normalized_event_type,
                            reason="target_game_archived",
                            game_id=normalized_game_id,
                            lot_title=str(game_row["title"]),
                            now=now,
                        )
                    if int(game_row["auction_only"]):
                        return self._mark_external_event_inapplicable_conn(
                            conn,
                            event_row_id=event_row_id,
                            service_key=source,
                            external_event_id=provider_event_id,
                            event_type=normalized_event_type,
                            reason="temporary_lot_not_running",
                            game_id=normalized_game_id,
                            lot_title=str(game_row["title"]),
                            now=now,
                        )
                    title = str(game_row["title"])

            rate_row = conn.execute(
                "SELECT value FROM settings WHERE key=?",
                (self._conversion_rate_key(unit),),
            ).fetchone()
            rate = str(rate_row["value"]) if rate_row is not None else ("1" if unit == "RUB" else "")
            if not rate:
                pending_cursor = conn.execute(
                    "INSERT INTO pending_conversions("
                    "external_event_row_id,game_id,auction_id,source_amount_text,"
                    "source_unit,source_unit_label,unit_kind,contributor,note,status,created_at"
                    ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        event_row_id,
                        normalized_game_id,
                        running_auction_id,
                        amount_text,
                        unit,
                        str(source_unit_label or unit),
                        kind,
                        str(contributor or "") or None,
                        str(note or "") or None,
                        "awaiting_rate",
                        now,
                    ),
                )
                pending_id = int(pending_cursor.lastrowid)
                conn.execute(
                    "UPDATE external_events SET processing_status='awaiting_rate' WHERE id=?",
                    (event_row_id,),
                )
                self._log_conn(
                    conn,
                    "integration_event",
                    event_row_id,
                    "awaiting_rate",
                    None,
                    {
                        "source": source,
                        "external_event_id": provider_event_id,
                        "event_type": normalized_event_type,
                        "game_id": normalized_game_id,
                        "auction_id": running_auction_id,
                        "lot_title": title,
                        "source_amount_text": amount_text,
                        "source_unit": unit,
                    },
                )
                return {
                    "status": "awaiting_rate",
                    "duplicate": False,
                    "external_event_row_id": event_row_id,
                    "pending_id": pending_id,
                    "game_id": normalized_game_id,
                    "auction_id": running_auction_id,
                    "credited_sm_points": None,
                }

            normalized_rate = format_rate(parse_positive_rate(rate)).replace(",", ".")
            credited = convert_source_to_sm_points(amount_text, normalized_rate)
            if credited <= 0:
                return self._mark_external_event_inapplicable_conn(
                    conn,
                    event_row_id=event_row_id,
                    service_key=source,
                    external_event_id=provider_event_id,
                    event_type=normalized_event_type,
                    reason="non_positive_credit",
                    game_id=normalized_game_id,
                    lot_title=title,
                    now=now,
                )

            auction_applied = False
            target_game_id = normalized_game_id
            if running_auction_id is not None:
                lot_result = self._add_or_increment_auction_lot_conn(
                    conn,
                    running_auction_id,
                    title,
                    credited,
                    source=source,
                    contributor=str(contributor or "") or None,
                    external_event_id=provider_event_id,
                    record_contribution=False,
                    extra_auto_extend_reasons=_external_auto_extend_reasons(kind),
                    preferred_game_id=normalized_game_id,
                )
                target_game_id = int(lot_result["game_id"])
                auction_applied = True
            else:
                if game_row is not None and normalized_game_id is not None:
                    conn.execute(
                        "UPDATE games SET sm_points=sm_points+?,updated_at=? WHERE id=?",
                        (credited, now, normalized_game_id),
                    )
                else:
                    # A valid game-targeted top-up outside an auction creates a
                    # normal persistent game.  It must not create/start/resume an
                    # auction, must not create an auction_only row, and must stay
                    # inside this same transaction as the credit/event audit.
                    target_game_id = self._add_game_conn(
                        conn,
                        Game(
                            None,
                            title,
                            None,
                            credited,
                            0,
                            STATUS_NOT_PLAYED,
                            "",
                        ),
                    )

            conn.execute(
                """
                INSERT INTO contributions(
                    game_id,source,external_event_id,contributor,
                    amount_minor,currency,points,unit,note,created_at,
                    source_amount_text,source_unit,conversion_rate,credited_sm_points
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    int(target_game_id),
                    source,
                    provider_event_id,
                    str(contributor or "") or None,
                    None,
                    unit if kind == UNIT_KIND_CURRENCY else None,
                    credited,
                    "SM",
                    str(note or "") or None,
                    now,
                    amount_text,
                    unit,
                    normalized_rate,
                    credited,
                ),
            )
            conn.execute(
                "UPDATE external_events SET processing_status='processed',processed_at=? WHERE id=?",
                (now, event_row_id),
            )
            conn.execute(
                "UPDATE integration_connections SET last_event_at=?,updated_at=? WHERE service_key=?",
                (now, now, source),
            )
            self._log_conn(
                conn,
                "integration_event",
                event_row_id,
                "apply",
                None,
                {
                    "source": source,
                    "external_event_id": provider_event_id,
                    "event_type": normalized_event_type,
                    "game_id": int(target_game_id),
                    "auction_id": running_auction_id if auction_applied else None,
                    "lot_title": title,
                    "source_amount_text": amount_text,
                    "source_unit": unit,
                    "conversion_rate": normalized_rate,
                    "credited_sm_points": credited,
                },
            )
            return {
                "status": "processed",
                "duplicate": False,
                "external_event_row_id": event_row_id,
                "pending_id": None,
                "game_id": int(target_game_id),
                "auction_id": running_auction_id if auction_applied else None,
                "credited_sm_points": credited,
                "conversion_rate": normalized_rate,
            }

    def queue_external_conversion_event(
        self,
        *,
        source: str,
        external_event_id: str,
        game_id: int,
        amount: Any,
        source_unit: str,
        unit_label: str | None = None,
        unit_kind: str | None = None,
        service: str = "",
        contributor: str | None = None,
        auction_id: int | None = None,
        note: str | None = None,
        event_type: str = "external_value",
        payload: Any | None = None,
    ) -> dict[str, Any]:
        """Persist an external value without changing points until manual apply.

        This is the fail-safe path for an unfamiliar/unconfigured source unit.
        It is also usable by future adapters that deliberately require operator
        confirmation. The raw event is deduplicated by ``source`` + provider
        event ID, and the normalized conversion request is stored separately.
        """
        source_name = str(source or "").strip()
        provider_event_id = str(external_event_id or "").strip()
        if not source_name:
            raise ValueError("Не указан источник внешнего события.")
        if not provider_event_id:
            raise ValueError("Не указан идентификатор внешнего события.")
        unit = normalize_unit_key(source_unit)
        kind = str(unit_kind or infer_unit_kind(unit)).strip().lower()
        descriptor = ConversionUnit(
            unit,
            str(unit_label or unit),
            str(service or source_name if kind == UNIT_KIND_SERVICE else ""),
            kind,
        )
        # Validate kind and amount before beginning the write transaction.
        kind = descriptor.normalized_kind()
        parsed_amount = parse_decimal(amount)
        if not parsed_amount.is_finite() or parsed_amount < 0:
            raise ValueError("Исходное значение не может быть отрицательным.")
        amount_text = decimal_to_storage_text(parsed_amount)
        raw_payload = payload if payload is not None else {}
        if isinstance(raw_payload, str):
            payload_text = raw_payload
        else:
            payload_text = json.dumps(raw_payload, ensure_ascii=False, default=str)
        now = utc_now()

        with self.connect() as conn:
            game = conn.execute(
                "SELECT id,title,archived FROM games WHERE id=?",
                (int(game_id),),
            ).fetchone()
            if game is None:
                raise KeyError(game_id)
            if int(game["archived"]):
                raise ValueError("Нельзя поставить внешнее начисление в очередь для архивной игры.")
            if auction_id is not None:
                session = conn.execute(
                    "SELECT id FROM auction_sessions WHERE id=?",
                    (int(auction_id),),
                ).fetchone()
                if session is None:
                    raise KeyError(auction_id)

            existing = conn.execute(
                "SELECT id FROM external_events WHERE source=? AND external_event_id=?",
                (source_name, provider_event_id),
            ).fetchone()
            if existing is not None:
                pending = conn.execute(
                    "SELECT id FROM pending_conversions WHERE external_event_row_id=?",
                    (int(existing["id"]),),
                ).fetchone()
                if pending is None:
                    raise RuntimeError(
                        "Внешнее событие уже существует, но не относится к очереди конвертации."
                    )
                pending_id = int(pending["id"])
            else:
                self._register_conversion_unit_conn(conn, descriptor)
                rate_row = conn.execute(
                    "SELECT value FROM settings WHERE key=?",
                    (self._conversion_rate_key(unit),),
                ).fetchone()
                rate = (
                    str(rate_row["value"])
                    if rate_row is not None
                    else ("1" if unit == "RUB" else "")
                )
                status = "awaiting_manual_apply" if rate else "awaiting_rate"
                cursor = conn.execute(
                    "INSERT INTO external_events("
                    "source,external_event_id,event_type,payload_json,processing_status,created_at"
                    ") VALUES(?,?,?,?,?,?)",
                    (
                        source_name, provider_event_id, str(event_type or "external_value"),
                        payload_text, status, now,
                    ),
                )
                external_row_id = int(cursor.lastrowid)
                cursor = conn.execute(
                    "INSERT INTO pending_conversions("
                    "external_event_row_id,game_id,auction_id,source_amount_text,"
                    "source_unit,source_unit_label,unit_kind,contributor,note,status,created_at"
                    ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        external_row_id, int(game_id),
                        int(auction_id) if auction_id is not None else None,
                        amount_text, unit, str(unit_label or unit), kind,
                        contributor, note, status, now,
                    ),
                )
                pending_id = int(cursor.lastrowid)
                self._log_conn(
                    conn,
                    "external_conversion",
                    pending_id,
                    "queue",
                    None,
                    {
                        "source": source_name,
                        "external_event_id": provider_event_id,
                        "game_id": int(game_id),
                        "auction_id": int(auction_id) if auction_id is not None else None,
                        "source_amount_text": amount_text,
                        "source_unit": unit,
                        "status": status,
                    },
                )
        return self.get_pending_conversion_event(pending_id)

    def _pending_conversion_rows(self, *, pending_id: int | None = None) -> list[sqlite3.Row]:
        query = """
            SELECT
                pc.*,
                ee.source,
                ee.external_event_id,
                ee.event_type,
                ee.payload_json,
                ee.processing_status,
                g.title AS game_title
            FROM pending_conversions pc
            JOIN external_events ee ON ee.id=pc.external_event_row_id
            LEFT JOIN games g ON g.id=pc.game_id
        """
        params: tuple[Any, ...] = ()
        if pending_id is None:
            query += " WHERE pc.status IN ('awaiting_rate','awaiting_manual_apply') ORDER BY pc.id"
        else:
            query += " WHERE pc.id=?"
            params = (int(pending_id),)
        with self.connect() as conn:
            return conn.execute(query, params).fetchall()

    def _pending_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        unit = str(row["source_unit"])
        status = str(row["status"])
        if status == "applied":
            rate = str(row["applied_rate"] or "")
            credited = (
                int(row["credited_sm_points"])
                if row["credited_sm_points"] is not None
                else None
            )
        else:
            rate = self.get_conversion_rate(unit)
            credited: int | None = None
            if rate:
                credited = convert_source_to_sm_points(row["source_amount_text"], rate)
        return {
            "id": int(row["id"]),
            "source": str(row["source"]),
            "external_event_id": str(row["external_event_id"]),
            "event_type": str(row["event_type"]),
            "game_id": int(row["game_id"]) if row["game_id"] is not None else None,
            "game_title": str(row["game_title"] or ""),
            "auction_id": int(row["auction_id"]) if row["auction_id"] is not None else None,
            "source_amount_text": str(row["source_amount_text"]),
            "source_unit": unit,
            "source_unit_label": str(row["source_unit_label"]),
            "unit_kind": str(row["unit_kind"]),
            "contributor": str(row["contributor"] or ""),
            "note": str(row["note"] or ""),
            "status": status,
            "conversion_rate": rate,
            "preview_sm_points": credited,
            "created_at": str(row["created_at"]),
        }

    def list_pending_conversion_events(self) -> list[dict[str, Any]]:
        return [self._pending_row_to_dict(row) for row in self._pending_conversion_rows()]

    def get_pending_conversion_event(self, pending_id: int) -> dict[str, Any]:
        rows = self._pending_conversion_rows(pending_id=int(pending_id))
        if not rows:
            raise KeyError(pending_id)
        return self._pending_row_to_dict(rows[0])

    def apply_pending_conversion_event(self, pending_id: int) -> dict[str, Any]:
        """Apply one unknown-rate event without retroactively mutating closed auctions.

        A stored running-auction context is used only while that exact session is
        still ``running``.  If it has since paused/closed, a matched permanent
        game may still receive its points (the approved outside-auction rule),
        but auction entries/timer/wheel state stay immutable.  A title-only event
        that originally arrived outside any auction may create/reuse a permanent
        game when explicitly applied; a title-only event that originally belonged
        to an auction still cannot be reinterpreted after that auction stops.
        """
        now = utc_now()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT pc.*,ee.source,ee.external_event_id,ee.event_type,ee.payload_json
                FROM pending_conversions pc
                JOIN external_events ee ON ee.id=pc.external_event_row_id
                WHERE pc.id=?
                """,
                (int(pending_id),),
            ).fetchone()
            if row is None:
                raise KeyError(pending_id)
            status = str(row["status"])
            if status not in {"awaiting_rate", "awaiting_manual_apply"}:
                raise RuntimeError("Это внешнее событие уже обработано или недоступно для применения.")

            unit = normalize_unit_key(row["source_unit"])
            rate_row = conn.execute(
                "SELECT value FROM settings WHERE key=?",
                (self._conversion_rate_key(unit),),
            ).fetchone()
            rate = (
                str(rate_row["value"])
                if rate_row is not None
                else ("1" if unit == "RUB" else "")
            )
            if not rate:
                raise ValueError(f"Для {unit} не настроен курс конвертации в баллы.")
            normalized_rate = format_rate(parse_positive_rate(rate)).replace(",", ".")
            credited = convert_source_to_sm_points(row["source_amount_text"], normalized_rate)
            if credited <= 0:
                raise RuntimeError("Событие не даёт положительного количества баллов.")

            try:
                payload = json.loads(str(row["payload_json"] or "{}"))
            except (TypeError, ValueError, json.JSONDecodeError):
                payload = {}
            normalized_payload = payload.get("normalized", {}) if isinstance(payload, dict) else {}
            if not isinstance(normalized_payload, dict):
                normalized_payload = {}
            lot_title = str(normalized_payload.get("lot_title") or "").strip()

            game_id = int(row["game_id"]) if row["game_id"] is not None else None
            game = None
            before_game_points: int | None = None
            if game_id is not None:
                game = conn.execute(
                    "SELECT id,title,sm_points,archived,auction_only FROM games WHERE id=?",
                    (game_id,),
                ).fetchone()
                if game is None or int(game["archived"]):
                    raise RuntimeError("Игра для ожидающего внешнего события недоступна.")
                before_game_points = int(game["sm_points"])
                lot_title = str(game["title"])

            stored_auction_id = int(row["auction_id"]) if row["auction_id"] is not None else None
            running_auction_id: int | None = None
            if stored_auction_id is not None:
                session = conn.execute(
                    "SELECT id,status FROM auction_sessions WHERE id=?",
                    (stored_auction_id,),
                ).fetchone()
                if session is not None and str(session["status"]) == "running":
                    running_auction_id = stored_auction_id

            target_game_id = game_id
            auction_applied = False
            if running_auction_id is not None:
                if game_id is None and not lot_title:
                    raise RuntimeError("Для ожидающего события не сохранилось пригодное указание лота.")
                result = self._add_or_increment_auction_lot_conn(
                    conn,
                    running_auction_id,
                    lot_title,
                    credited,
                    source=str(row["source"]),
                    contributor=str(row["contributor"] or "") or None,
                    external_event_id=str(row["external_event_id"]),
                    record_contribution=False,
                    extra_auto_extend_reasons=_external_auto_extend_reasons(
                        str(row["unit_kind"] or infer_unit_kind(unit))
                    ),
                    preferred_game_id=game_id,
                )
                target_game_id = int(result["game_id"])
                auction_applied = True
                if before_game_points is None:
                    created_game = conn.execute(
                        "SELECT sm_points FROM games WHERE id=?",
                        (target_game_id,),
                    ).fetchone()
                    before_game_points = max(0, int(created_game["sm_points"] or 0) - credited)
            else:
                if game is not None and game_id is not None:
                    if int(game["auction_only"]):
                        raise RuntimeError(
                            "Временный лот больше нельзя изменять вне запущенного аукциона."
                        )
                    conn.execute(
                        "UPDATE games SET sm_points=sm_points+?,updated_at=? WHERE id=?",
                        (credited, now, game_id),
                    )
                elif stored_auction_id is not None:
                    raise RuntimeError(
                        "Аукцион этого события уже не принимает ставки, а постоянная игра не определена."
                    )
                elif lot_title:
                    matched_game = self._find_game_by_title_conn(conn, lot_title)
                    if matched_game is not None:
                        matched_row = conn.execute(
                            "SELECT id,title,sm_points,archived,auction_only FROM games WHERE id=?",
                            (int(matched_game.id),),
                        ).fetchone()
                        if matched_row is None or int(matched_row["archived"]):
                            raise RuntimeError("Игра для ожидающего внешнего события недоступна.")
                        if int(matched_row["auction_only"]):
                            raise RuntimeError(
                                "Временный лот больше нельзя изменять вне запущенного аукциона."
                            )
                        target_game_id = int(matched_row["id"])
                        conn.execute(
                            "UPDATE games SET sm_points=sm_points+?,updated_at=? WHERE id=?",
                            (credited, now, target_game_id),
                        )
                    else:
                        target_game_id = self._add_game_conn(
                            conn,
                            Game(
                                None,
                                lot_title,
                                None,
                                credited,
                                0,
                                STATUS_NOT_PLAYED,
                                "",
                            ),
                        )
                else:
                    raise RuntimeError(
                        "Для ожидающего внешнего события не сохранилось пригодное указание игры."
                    )

            kind = str(row["unit_kind"])
            conn.execute(
                """
                INSERT INTO contributions(
                    game_id,source,external_event_id,contributor,
                    amount_minor,currency,points,unit,note,created_at,
                    source_amount_text,source_unit,conversion_rate,credited_sm_points
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    int(target_game_id), str(row["source"]), str(row["external_event_id"]),
                    row["contributor"], None,
                    unit if kind == UNIT_KIND_CURRENCY else None,
                    credited, "SM", row["note"], now,
                    str(row["source_amount_text"]), unit, normalized_rate, credited,
                ),
            )
            conn.execute(
                "UPDATE pending_conversions SET game_id=?,status='applied',applied_rate=?,"
                "credited_sm_points=?,applied_at=? WHERE id=?",
                (int(target_game_id), normalized_rate, credited, now, int(pending_id)),
            )
            conn.execute(
                "UPDATE external_events SET processing_status='processed',processed_at=? WHERE id=?",
                (now, int(row["external_event_row_id"])),
            )
            conn.execute(
                "UPDATE integration_connections SET last_event_at=?,updated_at=? WHERE service_key=?",
                (now, now, str(row["source"])),
            )
            self._log_conn(
                conn,
                "integration_event",
                int(row["external_event_row_id"]),
                "apply_pending",
                {
                    "pending_id": int(pending_id),
                    "status": status,
                    "stored_auction_id": stored_auction_id,
                },
                {
                    "pending_id": int(pending_id),
                    "game_id": int(target_game_id),
                    "auction_id": running_auction_id if auction_applied else None,
                    "source_amount_text": str(row["source_amount_text"]),
                    "source_unit": unit,
                    "conversion_rate": normalized_rate,
                    "credited_sm_points": credited,
                    "status": "applied",
                },
            )

        return {
            "id": int(pending_id),
            "game_id": int(target_game_id),
            "auction_id": running_auction_id if auction_applied else None,
            "source_unit": unit,
            "source_amount_text": str(row["source_amount_text"]),
            "conversion_rate": normalized_rate,
            "credited_sm_points": credited,
            "status": "applied",
        }

    @staticmethod
    def _timer_overlay_color(value: Any, default: str) -> str:
        color = str(value or default).strip().upper()
        if len(color) != 7 or not color.startswith("#"):
            return default
        try:
            int(color[1:], 16)
        except ValueError:
            return default
        return color

    @staticmethod
    def _timer_overlay_bounded_int(
        value: Any, default: int, minimum: int, maximum: int
    ) -> int:
        try:
            parsed = int(str(value).strip())
        except (TypeError, ValueError):
            return int(default)
        return max(int(minimum), min(int(maximum), parsed))

    @staticmethod
    def _format_timer_overlay_milliseconds(milliseconds: int) -> str:
        milliseconds = max(0, int(milliseconds))
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        seconds, millis = divmod(remainder, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"

    def current_timer_payload(
        self,
        runtime_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Read-only contract for the standalone authoritative OBS timer.

        This is deliberately a presentation adapter over the existing auction
        timer state. It never creates, advances or persists a second timer.
        """
        runtime = dict(runtime_state or {})
        runtime_mode = str(runtime.get("mode") or "max_amount")
        if runtime_mode not in {"max_amount", "weighted_wheel"}:
            runtime_mode = "max_amount"

        raw_audio = runtime.get("audio")
        raw_audio = dict(raw_audio) if isinstance(raw_audio, dict) else {}
        audio_owner = str(raw_audio.get("owner") or "idle")
        if audio_owner not in {"idle", "music_player", "auction"}:
            audio_owner = "idle"
        audio_kind = str(raw_audio.get("kind") or "none")
        if audio_kind not in {"none", "auction", "wheel"}:
            audio_kind = "none"
        try:
            audio_media_id = int(raw_audio.get("media_id"))
        except (TypeError, ValueError):
            audio_media_id = None
        try:
            audio_position_ms = max(0, int(raw_audio.get("position_ms") or 0))
        except (TypeError, ValueError):
            audio_position_ms = 0
        try:
            audio_gain = max(0.0, min(1.0, float(raw_audio.get("gain") or 0.0)))
        except (TypeError, ValueError):
            audio_gain = 0.0
        audio_enabled = bool(raw_audio.get("enabled"))
        audio_active = bool(
            audio_enabled
            and raw_audio.get("active")
            and audio_media_id is not None
            and audio_kind in {"auction", "wheel"}
        )
        audio_payload = {
            "enabled": audio_enabled,
            "owner": audio_owner,
            "active": audio_active,
            "kind": audio_kind if audio_active else "none",
            "media_id": audio_media_id if audio_active else None,
            "url": f"/media/{audio_media_id}" if audio_active else "",
            "playing": bool(raw_audio.get("playing")) if audio_active else False,
            "paused": bool(raw_audio.get("paused")) if audio_active else False,
            "position_ms": audio_position_ms if audio_active else 0,
            "gain": audio_gain if audio_active else 0.0,
            "muted": bool(raw_audio.get("muted")) if audio_active else False,
            "loop": bool(raw_audio.get("loop")) if audio_active else False,
        }

        keys = (
            "auction_max_amount_default_duration_ms",
            "auction_wheel_default_duration_ms",
            TIMER_OVERLAY_FONT_FAMILY_KEY,
            TIMER_OVERLAY_FONT_SIZE_KEY,
            TIMER_OVERLAY_FONT_COLOR_KEY,
            TIMER_OVERLAY_BACKGROUND_KEY,
            TIMER_OVERLAY_BACKGROUND_COLOR_KEY,
        )
        with self.connect() as conn:
            settings = self._get_settings_conn(conn, keys)
            session = self._get_open_auction_session_conn(conn)

        timer_kind = "auction"
        timer_running = False
        timer_paused = False
        if session is None:
            if runtime_mode == "weighted_wheel":
                default_ms = self._timer_overlay_bounded_int(
                    settings.get("auction_wheel_default_duration_ms"),
                    8_000,
                    self.WHEEL_MIN_DURATION_MS,
                    self.WHEEL_MAX_DURATION_MS,
                )
                timer_kind = "wheel"
            else:
                default_ms = self._timer_overlay_bounded_int(
                    settings.get("auction_max_amount_default_duration_ms"),
                    600_000,
                    AUCTION_MIN_DURATION_MS,
                    AUCTION_MAX_DURATION_MS,
                )
            remaining_ms = default_ms
            auction_id: int | None = None
            status = "idle"
            mode = runtime_mode
        else:
            auction_id = int(session["id"])
            status = str(session.get("status") or "")
            mode = str(session.get("mode") or "")
            if status in {"running", "paused"}:
                remaining_ms = self._remaining_ms_from_session(session)
                timer_running = status == "running"
                timer_paused = status == "paused"
            elif status == "awaiting_wheel":
                timer_kind = "wheel"
                remaining_ms = max(
                    0,
                    int(session.get("wheel_duration_ms") or 8_000),
                )
            elif status == "winner_selected" and session.get("wheel_spin_id"):
                timer_kind = "wheel"
                wheel_timer = self._wheel_animation_timer_state(session)
                remaining_ms = int(wheel_timer["remaining_ms"])
                timer_running = bool(wheel_timer["running"])
            else:
                remaining_ms = 0

        background = str(
            settings.get(TIMER_OVERLAY_BACKGROUND_KEY, TIMER_OVERLAY_BACKGROUND_DEFAULT)
            or TIMER_OVERLAY_BACKGROUND_DEFAULT
        ).strip().casefold()
        if background not in {"transparent", "color"}:
            background = TIMER_OVERLAY_BACKGROUND_DEFAULT

        family = str(
            settings.get(TIMER_OVERLAY_FONT_FAMILY_KEY, TIMER_OVERLAY_FONT_FAMILY_DEFAULT)
            or TIMER_OVERLAY_FONT_FAMILY_DEFAULT
        ).strip()
        if not family:
            family = TIMER_OVERLAY_FONT_FAMILY_DEFAULT
        # CSS is assigned through element.style.fontFamily, not HTML. Keep the
        # setting compact and bounded even for malformed legacy/manual values.
        family = family[:160]

        return {
            "auction_id": auction_id,
            "active": session is not None,
            "status": status,
            "mode": mode,
            "timer_kind": timer_kind,
            "running": bool(timer_running),
            "paused": bool(timer_paused),
            "remaining_ms": int(remaining_ms),
            "text": self._format_timer_overlay_milliseconds(remaining_ms),
            "audio": audio_payload,
            "presentation": {
                "font_family": family,
                "font_size": self._timer_overlay_bounded_int(
                    settings.get(TIMER_OVERLAY_FONT_SIZE_KEY),
                    TIMER_OVERLAY_FONT_SIZE_DEFAULT, 8, 300,
                ),
                "font_color": self._timer_overlay_color(
                    settings.get(TIMER_OVERLAY_FONT_COLOR_KEY),
                    TIMER_OVERLAY_FONT_COLOR_DEFAULT,
                ),
                "background": background,
                "background_color": self._timer_overlay_color(
                    settings.get(TIMER_OVERLAY_BACKGROUND_COLOR_KEY),
                    TIMER_OVERLAY_BACKGROUND_COLOR_DEFAULT,
                ),
            },
        }

    def current_auction_lots_payload(
        self,
        runtime_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Read-only OBS adapter over the existing Auction lot list."""
        runtime = dict(runtime_state or {})
        runtime_mode = str(runtime.get("mode") or "max_amount")
        if runtime_mode not in {"max_amount", "weighted_wheel"}:
            runtime_mode = "max_amount"
        auto_scroll = bool(runtime.get("auto_scroll", False))

        keys = (
            AUCTION_WHEEL_CHANCE_VISIBLE_KEY,
            AUCTION_LOTS_OVERLAY_FONT_FAMILY_KEY,
            AUCTION_LOTS_OVERLAY_FONT_SIZE_KEY,
            AUCTION_LOTS_OVERLAY_FONT_COLOR_KEY,
            AUCTION_LOTS_OVERLAY_BACKGROUND_KEY,
            AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_KEY,
            AUCTION_LOTS_OVERLAY_BACKGROUND_MEDIA_ID_KEY,
        )
        with self.connect() as conn:
            settings = self._get_settings_conn(conn, keys)
            session = self._get_open_auction_session_conn(conn)

            if session is None:
                mode = runtime_mode
                # Reuse the same canonical pre-start auction source
                # instead of repeating its status/filter/order business rules.
                game_rows = self._list_games_conn(
                    conn,
                    status_filter="middle",
                )
                rows = [
                    {
                        "game_id": int(game.id),
                        "start_position": position,
                        "current_position": position,
                        "title": str(game.title),
                        "total_sm_points": int(game.sm_points or 0),
                    }
                    for position, game in enumerate(game_rows, start=1)
                ]
                wheel_payload = (
                    self._preview_wheel_payload_from_conn(conn)
                    if mode == "weighted_wheel"
                    else {}
                )
                auction_id: int | None = None
                status = "preview"
            else:
                auction_id = int(session["id"])
                mode = str(session.get("mode") or "max_amount")
                status = str(session.get("status") or "")
                rows = self._list_auction_entries_conn(conn, auction_id)
                wheel_payload = (
                    self._wheel_payload_from_conn(conn, session)
                    if mode == "weighted_wheel"
                    else {}
                )

            media_raw = str(
                settings.get(AUCTION_LOTS_OVERLAY_BACKGROUND_MEDIA_ID_KEY, "")
            ).strip()
            background_asset = (
                self._get_media_asset_conn(conn, int(media_raw))
                if media_raw.isdigit()
                else None
            )

        chance_raw = str(
            settings.get(
                AUCTION_WHEEL_CHANCE_VISIBLE_KEY,
                "1" if AUCTION_WHEEL_CHANCE_VISIBLE_DEFAULT else "0",
            )
        ).strip().casefold()
        show_wheel_chance = bool(
            mode == "weighted_wheel"
            and chance_raw in {"1", "true", "yes", "on"}
        )
        probability_by_game = {
            int(sector["game_id"]): float(sector.get("probability") or 0.0)
            for sector in (wheel_payload or {}).get("sectors", [])
            if sector.get("game_id") is not None
        }

        payload_rows = []
        for row in rows:
            game_id = int(row["game_id"])
            probability = probability_by_game.get(game_id, 0.0)
            payload_rows.append({
                "game_id": game_id,
                "start_position": row.get("start_position") or "",
                "current_position": row.get("current_position") or "",
                "title": str(row.get("title") or ""),
                "total_sm_points": int(row.get("total_sm_points") or 0),
                "points_text": format_points(int(row.get("total_sm_points") or 0)),
                "probability": probability,
                "chance_text": (
                    f"{max(0.0, probability) * 100.0:.2f}".replace(".", ",")
                    + " %"
                ),
            })

        background = str(
            settings.get(
                AUCTION_LOTS_OVERLAY_BACKGROUND_KEY,
                AUCTION_LOTS_OVERLAY_BACKGROUND_DEFAULT,
            )
            or AUCTION_LOTS_OVERLAY_BACKGROUND_DEFAULT
        ).strip().casefold()
        if background not in {"transparent", "color", "media"}:
            background = AUCTION_LOTS_OVERLAY_BACKGROUND_DEFAULT

        family = str(
            settings.get(
                AUCTION_LOTS_OVERLAY_FONT_FAMILY_KEY,
                AUCTION_LOTS_OVERLAY_FONT_FAMILY_DEFAULT,
            )
            or AUCTION_LOTS_OVERLAY_FONT_FAMILY_DEFAULT
        ).strip()[:160] or AUCTION_LOTS_OVERLAY_FONT_FAMILY_DEFAULT

        if (
            background_asset is not None
            and background_asset.category == MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
        ):
            background_file = background_asset.display_name
            background_type = media_kind_for_name(background_file)
            background_available = media_asset_available(
                self.path.parent, background_asset
            )
            background_url = (
                f"/media/{background_asset.id}" if background_available else ""
            )
            background_asset_id: int | None = background_asset.id
        else:
            background_file = ""
            background_type = ""
            background_available = False
            background_url = ""
            background_asset_id = None

        return {
            "auction_id": auction_id,
            "status": status,
            "mode": mode,
            "show_wheel_chance": show_wheel_chance,
            "auto_scroll": auto_scroll,
            "rows": payload_rows,
            "presentation": {
                "font_family": family,
                "font_size": self._timer_overlay_bounded_int(
                    settings.get(AUCTION_LOTS_OVERLAY_FONT_SIZE_KEY),
                    AUCTION_LOTS_OVERLAY_FONT_SIZE_DEFAULT, 8, 160,
                ),
                "font_color": self._timer_overlay_color(
                    settings.get(AUCTION_LOTS_OVERLAY_FONT_COLOR_KEY),
                    AUCTION_LOTS_OVERLAY_FONT_COLOR_DEFAULT,
                ),
                "background": background,
                "background_color": self._timer_overlay_color(
                    settings.get(AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_KEY),
                    AUCTION_LOTS_OVERLAY_BACKGROUND_COLOR_DEFAULT,
                ),
                "background_media": {
                    "asset_id": background_asset_id,
                    "file": background_file,
                    "type": background_type,
                    "available": bool(background_available),
                    "url": background_url,
                },
            },
        }

    def current_stream_payload(self) -> dict[str, Any]:
        # Keep the complete OBS snapshot on one SQLite connection.  Earlier
        # versions already batched settings, but /api/data still opened a
        # second connection for games and sometimes a third for background
        # media.  OBS can have both the main overlay and standalone list open,
        # so avoiding those connection churn costs matters on Windows/OneDrive.
        with self.connect() as conn:
            settings = self._get_settings_conn(conn)
            # Browser Sources need only five game fields.  Avoid materializing
            # reviews/coop/timestamps for every row on every 1-second poll.
            games = conn.execute(
                f"""
                SELECT id, title, release_date, sm_points, status
                FROM games
                WHERE auction_only=0 AND archived=0
                ORDER BY {self.GAME_ORDER_SQL}
                """
            ).fetchall()

            media_id_raw = str(
                settings.get("overlay_background_media_id", "")
            ).strip()
            background_asset = (
                self._get_media_asset_conn(conn, int(media_id_raw))
                if media_id_raw.isdigit()
                else None
            )

        def setting(key: str, default: str = "") -> str:
            return settings.get(key, default)

        game_id_raw = setting("stream_current_game_id", "")
        game = None
        if game_id_raw.isdigit():
            wanted_id = int(game_id_raw)
            game = next((row for row in games if int(row["id"]) == wanted_id), None)
        if game is None:
            game = next((row for row in games if row["status"] == STATUS_PLAYING), None)

        info_enabled = setting("stream_info_enabled", "1") == "1"
        info_text = setting("stream_info", "")
        legacy_frame_color = setting("overlay_frame_color", "#FFFFFF")
        legacy_background_file = setting("overlay_background_file", "")
        if (
            background_asset is not None
            and background_asset.category != MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
        ):
            background_asset = None

        if background_asset is not None:
            background_file = background_asset.display_name
            background_type = media_kind_for_name(background_file)
            background_available = media_asset_available(self.path.parent, background_asset)
            background_storage_mode = background_asset.storage_mode
            background_url = (
                f"/media/{background_asset.id}" if background_available else ""
            )
            background_asset_id: int | None = background_asset.id
        else:
            # Legacy fallback is intentionally retained for databases/settings
            # written by pre-W2 versions.  Migration 16 normally adopts this
            # value into media_assets, including a selected missing file.
            background_file = legacy_background_file
            background_type = media_kind_for_name(background_file)
            background_asset_id = None
            background_storage_mode = MEDIA_STORAGE_MANAGED if background_file else ""
            legacy_path = (
                managed_media_directory(
                    self.path.parent, MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
                ) / background_file
                if background_file and Path(background_file).name == background_file
                else None
            )
            background_available = bool(
                legacy_path is not None
                and legacy_path.is_file()
                and background_type
            )
            background_url = (
                f"/overlay-background/{background_file}"
                if background_available
                else ""
            )

        auction_games = [
            row for row in games
            if row["status"] in (STATUS_PLAYED, STATUS_NOT_PLAYED)
        ]

        typography_defaults = {
            "title": ("Segoe UI", "30", "#FFFFFF"),
            "top1": ("Segoe UI", "17", "#FFFFFF"),
            "top2": ("Segoe UI", "17", "#FFFFFF"),
            "top3": ("Segoe UI", "17", "#FFFFFF"),
            "list": ("Segoe UI", "17", "#FFFFFF"),
            "info": ("Segoe UI", "17", "#FFFFFF"),
        }
        typography = {
            key: {
                "family": setting(f"overlay_font_{key}_family", defaults[0]),
                "size": setting(f"overlay_font_{key}_size", defaults[1]),
                "color": setting(f"overlay_font_{key}_color", defaults[2]),
            }
            for key, defaults in typography_defaults.items()
        }

        return {
            "game": {
                "id": int(game["id"]) if game else None,
                "name": str(game["title"]) if game else "",
                "date": display_date(game["release_date"]) if game else "",
                "reviews": info_text if info_enabled else "",
                "reviews_enabled": info_enabled,
                "format": setting("stream_format", "16:9"),
            },
            "list": [
                {
                    "id": int(row["id"]),
                    "title": str(row["title"]),
                    "sm_points": int(row["sm_points"]),
                    "sum": int(row["sm_points"]),
                }
                for row in games
            ],
            "auction_list": [
                {
                    "id": int(row["id"]),
                    "title": str(row["title"]),
                    "sm_points": int(row["sm_points"]),
                    "sum": int(row["sm_points"]),
                }
                for row in auction_games
            ],
            "overlay": {
                "webcam_enabled": setting("overlay_webcam_enabled", "1") == "1",
                "webcam_position": setting("overlay_webcam_position", "top_right"),
                "list_enabled": setting("overlay_list_enabled", "1") == "1",
                "list_side": setting("overlay_list_side", "auto"),
                "info_position": setting("overlay_info_position", "auto"),
                "background": {
                    "asset_id": background_asset_id,
                    "file": background_file,
                    "type": background_type,
                    "mode": setting("overlay_background_mode", "stretch"),
                    "storage_mode": background_storage_mode,
                    "available": bool(background_available),
                    "status": (
                        "ready"
                        if background_file and background_available
                        else "unavailable"
                        if background_file
                        else "none"
                    ),
                    # Deliberately expose only the local HTTP resource URL.
                    # Absolute external filesystem paths never enter Browser Source.
                    "url": background_url,
                },
                "frame_color": legacy_frame_color,
                "frame_colors": {
                    "game": setting("overlay_frame_game_color", legacy_frame_color),
                    "webcam": setting("overlay_frame_webcam_color", legacy_frame_color),
                    "list": setting("overlay_frame_list_color", legacy_frame_color),
                    "info": setting("overlay_frame_info_color", legacy_frame_color),
                },
                "typography": typography,
            },
        }

    def backup(self, backup_dir: str | Path) -> Path:
        return create_sqlite_backup(self.path, backup_dir)

    def backup_isolated(self, backup_dir: str | Path) -> Path:
        """Create a consistent SQLite backup in a separate process.

        In source mode the helper is ``python app.py --create-backup``.  In a
        PyInstaller build ``sys.executable`` is the application executable, so
        the same operation becomes ``InOneLine.exe --create-backup``.  This
        avoids the invalid frozen ``InOneLine.exe -c ...`` path while keeping
        slow filesystem filters outside the Qt GUI process.
        """
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        target = backup_dir / f"streaming_{stamp}.db"
        error_file = backup_dir / f".backup_{stamp}.error.txt"

        if getattr(sys, "frozen", False):
            command = [sys.executable]
        else:
            app_path = Path(__file__).resolve().parents[2] / "app.py"
            command = [sys.executable, str(app_path)]

        command += [
            "--create-backup",
            str(self.path.resolve()),
            str(target.resolve()),
            str(error_file.resolve()),
        ]
        kwargs: dict[str, Any] = {
            "args": command,
            "check": False,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "text": True,
            "timeout": 90.0,
        }
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            if getattr(sys, "frozen", False):
                # E4: preserve frozen helper launches when sys.executable is
                # beyond classic MAX_PATH by using an explicit application name.
                kwargs["executable"] = sys.executable

        try:
            proc = subprocess.run(**kwargs)
        except subprocess.TimeoutExpired as exc:
            target.unlink(missing_ok=True)
            error_file.unlink(missing_ok=True)
            raise RuntimeError(
                "Резервное копирование не завершилось за 90 секунд и было остановлено. "
                "Исходная база не изменена."
            ) from exc

        try:
            if proc.returncode != 0 or not target.is_file() or target.stat().st_size <= 0:
                try:
                    message = error_file.read_text(encoding="utf-8").strip()
                except OSError:
                    message = "Неизвестная ошибка резервного копирования"
                target.unlink(missing_ok=True)
                raise RuntimeError(message or "Неизвестная ошибка резервного копирования")
            return target
        finally:
            error_file.unlink(missing_ok=True)

    def clear_all_games_with_backup(
        self,
        backup_dir: str | Path,
        keep_backups: int = 30,
    ) -> dict[str, Any]:
        """Clear live games only after a successfully created safety backup."""
        backup_dir = Path(backup_dir)
        try:
            backup_path = self.backup_isolated(backup_dir)
        except Exception as exc:
            raise RuntimeError(
                "Не удалось создать резервную копию перед очисткой игр. "
                "Ни одна игра не была удалена.\n\n" + str(exc)
            ) from exc

        try:
            self.prune_backups(backup_dir, keep_backups)
        except Exception as exc:
            raise RuntimeError(
                "Резервная копия создана, но не удалось очистить старые копии. "
                "Игры не были удалены.\n\n"
                f"Резервная копия: {backup_path}\n\n{exc}"
            ) from exc

        try:
            result = self.clear_all_games()
        except Exception as exc:
            raise RuntimeError(
                f"Игры не были удалены: {exc}\n\n"
                f"Резервная копия перед попыткой очистки: {backup_path}"
            ) from exc

        return {
            **result,
            "backup_path": str(backup_path),
        }

    def import_csv_with_backup(
        self,
        path: str | Path,
        backup_dir: str | Path,
        merge: bool = True,
        keep_backups: int = 30,
    ) -> dict[str, Any]:
        """Run the existing strict CSV importer only after a safety backup.

        This is intentionally an orchestration wrapper, not a second importer:
        validation, normalization and database writes remain in ``import_csv``.
        The invariant is that a failed safety backup can never be followed by
        import writes.
        """
        backup_dir = Path(backup_dir)
        try:
            backup_path = self.backup_isolated(backup_dir)
        except Exception as exc:
            raise RuntimeError(
                "Не удалось создать резервную копию перед импортом. "
                "Импорт не был выполнен.\n\n" + str(exc)
            ) from exc

        try:
            self.prune_backups(backup_dir, keep_backups)
        except Exception as exc:
            raise RuntimeError(
                "Резервная копия создана, но не удалось очистить старые копии. "
                "Импорт не был выполнен.\n\n"
                f"Резервная копия: {backup_path}\n\n{exc}"
            ) from exc

        try:
            result = self.import_csv(path, merge=merge)
        except Exception as exc:
            raise RuntimeError(
                f"Импорт не выполнен: {exc}\n\n"
                f"Резервная копия перед попыткой импорта: {backup_path}"
            ) from exc

        return {
            "backup_path": str(backup_path),
            "created": int(result["created"]),
            "updated": int(result["updated"]),
            "skipped": int(result["skipped"]),
        }

    def import_csv(self, path: str | Path, merge: bool = True) -> dict[str, int]:
        """Import games from a flexible CSV or legacy pipe-delimited CSV.

        Normal CSV requires only the ``НАЗВАНИЕ ИГРЫ`` header. Other supported
        columns are optional, may be in any order, and blank cells mean
        "value not provided". Unknown columns are ignored. For existing games
        only the non-empty values that were actually provided are updated.

        Legacy pipe-delimited files are also accepted unchanged: one value per line
        in the form ``Название игры|Баллы`` without a header.

        The complete file is validated before the first database write, and
        the entire write phase is committed atomically as one transaction.
        """
        path = Path(path)
        parsed_rows: list[tuple[str, dict[str, Any]]] = []
        skipped_empty = 0
        seen_titles: dict[str, str] = {}

        def register_title(title: str) -> None:
            title_key = normalize_title_key(title)
            if title_key in seen_titles:
                raise ValueError(
                    f"Дубликат названия в CSV: «{title}» "
                    f"(ранее встречалось как «{seen_titles[title_key]}»)."
                )
            seen_titles[title_key] = title

        def parse_optional_payload(
            title: str,
            line_no: int,
            values: dict[str, str],
        ) -> dict[str, Any]:
            payload: dict[str, Any] = {"title": title}

            status_text = values.get("СТАТУС", "").strip()
            if status_text:
                status_key = status_text.upper()
                if status_key not in STATUS_FROM_LABEL:
                    raise ValueError(
                        f"Неизвестный статус у «{title}» (строка {line_no}): "
                        f"{status_text!r}"
                    )
                payload["status"] = STATUS_FROM_LABEL[status_key]

            coop_text = values.get("КООП/НЕ КООП", "").strip()
            if coop_text:
                coop_key = coop_text.upper()
                if coop_key not in COOP_FROM_LABEL:
                    raise ValueError(
                        f"Неизвестное значение КООП/НЕ КООП у «{title}» "
                        f"(строка {line_no}): {coop_text!r}. "
                        "Допустимо: КООП или НЕ КООП."
                    )
                payload["coop"] = COOP_FROM_LABEL[coop_key]

            date_text = values.get("ДАТА ВЫХОДА", "").strip()
            if date_text:
                try:
                    payload["release_date"] = parse_date(date_text)
                except ValueError as exc:
                    raise ValueError(
                        f"Некорректная дата у «{title}» (строка {line_no})."
                    ) from exc

            points_text = values.get("БАЛЛЫ", "").strip() or values.get("БАЛЛЫ SM", "").strip()
            legacy_amount_text = values.get("СУММА", "").strip()
            amount_text = points_text or legacy_amount_text
            if amount_text:
                try:
                    payload["sm_points"] = points_from_text(amount_text)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Некорректное значение баллов у «{title}» (строка {line_no})."
                    ) from exc

            review_text = values.get("ОТЗЫВ", "").strip()
            if review_text:
                payload["review"] = review_text

            return payload

        with path.open("r", encoding="utf-8-sig", newline="") as f:
            raw_text = f.read()

        lines = [line for line in raw_text.splitlines() if line.strip()]
        if not lines:
            return {"created": 0, "updated": 0, "skipped": 0}

        supported_headers = {
            "НАЗВАНИЕ ИГРЫ",
            "ДАТА ВЫХОДА",
            "БАЛЛЫ",
            "БАЛЛЫ SM",
            "СУММА",
            "КООП/НЕ КООП",
            "СТАТУС",
            "ОТЗЫВ",
        }

        # Legacy compatibility: exactly the old headerless
        # ``Название|Баллы`` representation exported by earlier versions.
        first_nonempty = lines[0].strip()
        is_legacy_pipe = (
            "|" in first_nonempty
            and "НАЗВАНИЕ ИГРЫ" not in first_nonempty.upper()
        )

        if is_legacy_pipe:
            for line_no, line in enumerate(raw_text.splitlines(), start=1):
                text = line.strip()
                if not text:
                    skipped_empty += 1
                    continue
                if "|" not in text:
                    raise ValueError(
                        f"Некорректная строка формата «Название|Баллы» (строка {line_no}): "
                        "ожидается формат Название игры|Баллы."
                    )
                title, amount_text = text.rsplit("|", 1)
                title = title.strip()
                amount_text = amount_text.strip()
                if not title:
                    skipped_empty += 1
                    continue
                if not amount_text:
                    raise ValueError(
                        f"Не указаны баллы у «{title}» (строка {line_no})."
                    )
                register_title(title)
                try:
                    sm_points = points_from_text(amount_text)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Некорректное значение баллов у «{title}» (строка {line_no})."
                    ) from exc
                parsed_rows.append(
                    (title, {"title": title, "sm_points": sm_points})
                )
        else:
            sample = raw_text[:4096]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
            except csv.Error:
                dialect = csv.excel
                dialect.delimiter = ";"

            reader = csv.DictReader(raw_text.splitlines(), dialect=dialect)
            if not reader.fieldnames:
                raise ValueError("CSV не содержит заголовков.")

            norm = {
                str(header).strip().upper(): header
                for header in reader.fieldnames
                if header is not None and str(header).strip()
            }
            if "НАЗВАНИЕ ИГРЫ" not in norm:
                raise ValueError(
                    "Не найден обязательный столбец: НАЗВАНИЕ ИГРЫ. "
                    "Либо используйте формат «Название игры|Баллы»."
                )

            available = supported_headers.intersection(norm)
            for line_no, row in enumerate(reader, start=2):
                title = str(row.get(norm["НАЗВАНИЕ ИГРЫ"], "") or "").strip()
                if not title:
                    skipped_empty += 1
                    continue
                register_title(title)
                values = {
                    header: str(row.get(norm[header], "") or "")
                    for header in available
                    if header != "НАЗВАНИЕ ИГРЫ"
                }
                parsed_rows.append(
                    (title, parse_optional_payload(title, line_no, values))
                )

        # Only after successful validation of the complete file do we modify DB.
        # The entire write phase is one transaction: any exception rolls back
        # every game mutation and its corresponding change_log entries.
        created = updated = skipped = 0
        with self.connect() as conn:
            for title, payload in parsed_rows:
                existing = (
                    self._find_game_by_title_conn(conn, title)
                    if merge
                    else None
                )
                if existing:
                    if self._update_game_conn(conn, existing.id, payload):
                        updated += 1
                    else:
                        skipped += 1
                else:
                    new_payload = {
                        "title": title,
                        "release_date": None,
                        "sm_points": 0,
                        "coop": 0,
                        "status": STATUS_NOT_PLAYED,
                        "review": "",
                    }
                    new_payload.update(payload)
                    self._add_game_conn(
                        conn,
                        Game(id=None, archived=0, **new_payload),
                    )
                    created += 1

        return {
            "created": created,
            "updated": updated,
            "skipped": skipped + skipped_empty,
        }

    def prune_backups(self, backup_dir: str | Path, keep: int = 30) -> None:
        prune_backup_files(backup_dir, keep)
