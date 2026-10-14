from __future__ import annotations

import json
import sqlite3
from typing import Any

from ..constants import (
    RULES_OVERLAY_AUTOSCROLL_DEFAULT,
    RULES_OVERLAY_AUTOSCROLL_KEY,
    RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT,
    RULES_OVERLAY_BACKGROUND_COLOR_KEY,
    RULES_OVERLAY_BACKGROUND_DEFAULT,
    RULES_OVERLAY_BACKGROUND_KEY,
    RULES_OVERLAY_BACKGROUND_OPACITY_DEFAULT,
    RULES_OVERLAY_BACKGROUND_OPACITY_KEY,
    RULES_OVERLAY_PADDING_DEFAULT,
    RULES_OVERLAY_PADDING_KEY,
    RULES_OVERLAY_VISIBLE_KEY,
)
from ..obs_visibility import WIDGETS, show_mode, visibility_payload
from ..rules_html import sanitize_rules_html
from .common import normalize_text_key, utc_now


class RulesMixin:
    """Persistent auction-rules templates and per-session rule snapshots.

    A session starts from an exact copy of the active template.  While that local
    session is still open, explicit saves/renames of its source template are mirrored
    into the session copy so the operator uses one editor and one remembered ruleset.
    Once the session is finished, its last synchronized copy remains historical.
    """

    RULE_TEMPLATE_NAME_MAX = 80
    DEFAULT_RULE_TEMPLATE_NAME = "Основной"

    @staticmethod
    def _rule_row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    @classmethod
    def _validate_rule_template_name(cls, value: Any) -> str:
        name = " ".join(str(value or "").split())
        if not name:
            raise ValueError("Название шаблона не может быть пустым.")
        if len(name) > cls.RULE_TEMPLATE_NAME_MAX:
            raise ValueError(
                f"Название шаблона не может быть длиннее {cls.RULE_TEMPLATE_NAME_MAX} символов."
            )
        return name

    def _ensure_default_rule_template_conn(self, conn: sqlite3.Connection) -> int:
        row = conn.execute(
            "SELECT id FROM auction_rule_templates ORDER BY is_active DESC, id ASC LIMIT 1"
        ).fetchone()
        if row is None:
            now = utc_now()
            cursor = conn.execute(
                """
                INSERT INTO auction_rule_templates(
                    name, content_html, is_active, created_at, updated_at
                )
                VALUES(?, '', 1, ?, ?)
                """,
                (self.DEFAULT_RULE_TEMPLATE_NAME, now, now),
            )
            return int(cursor.lastrowid)

        active = conn.execute(
            "SELECT id FROM auction_rule_templates WHERE is_active=1 ORDER BY id ASC LIMIT 1"
        ).fetchone()
        if active is not None:
            return int(active["id"])

        template_id = int(row["id"])
        conn.execute("UPDATE auction_rule_templates SET is_active=0")
        conn.execute(
            "UPDATE auction_rule_templates SET is_active=1 WHERE id=?",
            (template_id,),
        )
        return template_id

    def ensure_default_rule_template(self) -> int:
        with self.connect() as conn:
            return self._ensure_default_rule_template_conn(conn)

    def list_rule_templates(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            self._ensure_default_rule_template_conn(conn)
            rows = conn.execute(
                """
                SELECT id, name, content_html, is_active, created_at, updated_at
                FROM auction_rule_templates
                ORDER BY is_active DESC, name COLLATE NOCASE ASC, id ASC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def get_rule_template(self, template_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, content_html, is_active, created_at, updated_at
                FROM auction_rule_templates
                WHERE id=?
                """,
                (int(template_id),),
            ).fetchone()
            return self._rule_row_to_dict(row)

    def get_active_rule_template(self) -> dict[str, Any]:
        with self.connect() as conn:
            template_id = self._ensure_default_rule_template_conn(conn)
            row = conn.execute(
                """
                SELECT id, name, content_html, is_active, created_at, updated_at
                FROM auction_rule_templates
                WHERE id=?
                """,
                (template_id,),
            ).fetchone()
            assert row is not None
            return dict(row)

    def _assert_rule_template_name_unique_conn(
        self,
        conn: sqlite3.Connection,
        name: str,
        *,
        exclude_id: int | None = None,
    ) -> None:
        normalized = normalize_text_key(name)
        rows = conn.execute(
            "SELECT id, name FROM auction_rule_templates"
        ).fetchall()
        for row in rows:
            row_id = int(row["id"])
            if exclude_id is not None and row_id == int(exclude_id):
                continue
            if normalize_text_key(row["name"]) == normalized:
                raise ValueError("Шаблон с таким названием уже существует.")

    def create_rule_template(
        self,
        name: str,
        *,
        content_html: str = "",
        make_active: bool = True,
    ) -> int:
        clean_name = self._validate_rule_template_name(name)
        now = utc_now()
        with self.connect() as conn:
            self._ensure_default_rule_template_conn(conn)
            self._assert_rule_template_name_unique_conn(conn, clean_name)
            if make_active:
                conn.execute("UPDATE auction_rule_templates SET is_active=0")
            cursor = conn.execute(
                """
                INSERT INTO auction_rule_templates(
                    name, content_html, is_active, created_at, updated_at
                )
                VALUES(?,?,?,?,?)
                """,
                (
                    clean_name,
                    str(content_html or ""),
                    1 if make_active else 0,
                    now,
                    now,
                ),
            )
            return int(cursor.lastrowid)

    @staticmethod
    def _validated_rule_presentation(value: Any) -> dict[str, Any]:
        """Validate original 5-field or new 7-field composite Rules styling.

        Old templates and auction snapshots remain readable without migration.
        Show/visibility mode remains global, not a per-template preference.
        """
        legacy_keys = {
            "autoscroll", "background", "background_color",
            "background_opacity", "padding",
        }
        glow_keys = {"glow", "glow_color"}
        if not isinstance(value, dict) or set(value) not in (
            legacy_keys, legacy_keys | glow_keys
        ):
            raise ValueError("Некорректный состав полей оформления правил.")
        if type(value["autoscroll"]) is not bool:
            raise ValueError("Автопрокрутка должна быть включена или выключена.")
        background = value["background"]
        if background not in ("transparent", "color"):
            raise ValueError("Неизвестный тип фона правил.")
        color = value["background_color"]
        if not (isinstance(color, str) and len(color) == 7 and color.startswith("#")):
            raise ValueError("Некорректный цвет фона правил.")
        try:
            int(color[1:], 16)
        except ValueError as exc:
            raise ValueError("Некорректный цвет фона правил.") from exc
        opacity = value["background_opacity"]
        padding = value["padding"]
        if type(opacity) is not int or not 0 <= opacity <= 100:
            raise ValueError("Непрозрачность должна быть от 0 до 100.")
        if type(padding) is not int or not 0 <= padding <= 200:
            raise ValueError("Внутренний отступ должен быть от 0 до 200.")
        cleaned = {
            "autoscroll": value["autoscroll"],
            "background": background,
            "background_color": color.upper(),
            "background_opacity": opacity,
            "padding": padding,
        }
        if "glow" in value:
            if type(value["glow"]) is not bool:
                raise ValueError("Светящийся контур должен быть включён или выключен.")
            glow_color = value["glow_color"]
            if (not isinstance(glow_color, str) or len(glow_color) != 7
                    or not glow_color.startswith("#")):
                raise ValueError("Некорректный цвет подсветки правил.")
            try:
                int(glow_color[1:], 16)
            except ValueError as exc:
                raise ValueError("Некорректный цвет подсветки правил.") from exc
            cleaned["glow"] = value["glow"]
            cleaned["glow_color"] = glow_color.upper()
        return cleaned

    @classmethod
    def _read_rule_presentation_json(cls, raw: Any) -> dict[str, Any] | None:
        """NULL/corrupt legacy values inherit unchanged global OBS styling."""
        if raw is None:
            return None
        try:
            parsed = json.loads(str(raw))
            return cls._validated_rule_presentation(parsed)
        except (TypeError, ValueError, OverflowError):
            return None

    def get_rule_template_presentation(
        self, template_id: int,
    ) -> dict[str, Any] | None:
        """Read saved per-template appearance, or None for global fallback."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT presentation_json FROM auction_rule_templates WHERE id=?",
                (int(template_id),),
            ).fetchone()
            if row is None:
                raise ValueError("Шаблон правил не найден.")
            return self._read_rule_presentation_json(row["presentation_json"])

    def save_rule_template_presentation(
        self, template_id: int, presentation: dict[str, Any] | None,
    ) -> None:
        """Save style and synchronize its current local-auction source atomically.

        Current OBS rendering stays on legacy global settings until an
        independently verified UI/renderer cutover.
        """
        template_id = int(template_id)
        clean = None if presentation is None else self._validated_rule_presentation(presentation)
        serialized = (
            json.dumps(clean, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            if clean is not None else None
        )
        with self.connect() as conn:
            row = conn.execute(
                "SELECT presentation_json FROM auction_rule_templates WHERE id=?",
                (template_id,),
            ).fetchone()
            if row is None:
                raise ValueError("Шаблон правил не найден.")
            if row["presentation_json"] == serialized:
                return
            conn.execute(
                "UPDATE auction_rule_templates SET presentation_json=?, updated_at=? WHERE id=?",
                (serialized, utc_now(), template_id),
            )
            placeholders = ",".join("?" for _ in self.AUCTION_OPEN_STATUSES)
            sessions = conn.execute(
                f"""SELECT id, rules_presentation_json FROM auction_sessions
                    WHERE provider='local' AND status IN ({placeholders})
                      AND rules_template_id=?""",
                (*self.AUCTION_OPEN_STATUSES, template_id),
            ).fetchall()
            for session in sessions:
                previous = session["rules_presentation_json"]
                if previous == serialized:
                    continue
                conn.execute(
                    "UPDATE auction_sessions SET rules_presentation_json=?, updated_at=? WHERE id=?",
                    (serialized, utc_now(), int(session["id"])),
                )
                self._log_conn(
                    conn, "auction_session", int(session["id"]),
                    "sync_rules_presentation",
                    {"rules_presentation_json": previous},
                    {"rules_presentation_json": serialized},
                )

    def get_auction_rules_presentation_snapshot(
        self, auction_id: int,
    ) -> dict[str, Any] | None:
        """Read stored session style only; do not change live OBS presentation."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT rules_presentation_json FROM auction_sessions WHERE id=?",
                (int(auction_id),),
            ).fetchone()
            if row is None:
                raise ValueError("Аукцион не найден.")
            return self._read_rule_presentation_json(row["rules_presentation_json"])

    def _sync_open_sessions_from_rule_template_conn(
        self,
        conn: sqlite3.Connection,
        template_id: int,
        *,
        template_name: str,
        content_html: str,
    ) -> None:
        """Mirror one template into any open local session created from it."""
        placeholders = ",".join("?" for _ in self.AUCTION_OPEN_STATUSES)
        rows = conn.execute(
            f"""
            SELECT id, rules_template_name, rules_html
            FROM auction_sessions
            WHERE provider='local'
              AND status IN ({placeholders})
              AND rules_template_id=?
            """,
            (*self.AUCTION_OPEN_STATUSES, int(template_id)),
        ).fetchall()
        now = utc_now()
        for row in rows:
            session_id = int(row["id"])
            before_name = str(row["rules_template_name"] or "")
            before_html = str(row["rules_html"] or "")
            if before_name == template_name and before_html == content_html:
                continue
            conn.execute(
                """
                UPDATE auction_sessions
                SET rules_template_name=?, rules_html=?, updated_at=?
                WHERE id=?
                """,
                (template_name, content_html, now, session_id),
            )
            self._log_conn(
                conn,
                "auction_session",
                session_id,
                "sync_rules_from_template",
                {
                    "rules_template_id": int(template_id),
                    "rules_template_name": before_name,
                    "rules_html": before_html,
                },
                {
                    "rules_template_id": int(template_id),
                    "rules_template_name": template_name,
                    "rules_html": content_html,
                },
            )

    def rename_rule_template(self, template_id: int, name: str) -> None:
        template_id = int(template_id)
        clean_name = self._validate_rule_template_name(name)
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, content_html FROM auction_rule_templates WHERE id=?",
                (template_id,),
            ).fetchone()
            if row is None:
                raise ValueError("Шаблон правил не найден.")
            self._assert_rule_template_name_unique_conn(
                conn,
                clean_name,
                exclude_id=template_id,
            )
            conn.execute(
                "UPDATE auction_rule_templates SET name=?, updated_at=? WHERE id=?",
                (clean_name, utc_now(), template_id),
            )
            self._sync_open_sessions_from_rule_template_conn(
                conn,
                template_id,
                template_name=clean_name,
                content_html=str(row["content_html"] or ""),
            )

    def save_rule_template(self, template_id: int, content_html: str) -> None:
        template_id = int(template_id)
        html = str(content_html or "")
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, name FROM auction_rule_templates WHERE id=?",
                (template_id,),
            ).fetchone()
            if row is None:
                raise ValueError("Шаблон правил не найден.")
            conn.execute(
                "UPDATE auction_rule_templates SET content_html=?, updated_at=? WHERE id=?",
                (html, utc_now(), template_id),
            )
            self._sync_open_sessions_from_rule_template_conn(
                conn,
                template_id,
                template_name=str(row["name"]),
                content_html=html,
            )

    def set_active_rule_template(self, template_id: int) -> None:
        """Activate Rules and switch the current local auction in one transaction."""
        template_id = int(template_id)
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, name, content_html, presentation_json FROM auction_rule_templates WHERE id=?",
                (template_id,),
            ).fetchone()
            if row is None:
                raise ValueError("Шаблон правил не найден.")
            conn.execute("UPDATE auction_rule_templates SET is_active=0")
            conn.execute(
                "UPDATE auction_rule_templates SET is_active=1 WHERE id=?",
                (template_id,),
            )

            # An open auction reads its own Rules snapshot in /rules-overlay.
            # Switching the global active template alone left that snapshot
            # pointing at the pre-auction template. Reuse the authoritative
            # session instead of introducing a second live-Rules override.
            session = self._get_open_auction_session_conn(conn)
            if session is None:
                return
            before = {
                "rules_template_id": session.get("rules_template_id"),
                "rules_template_name": str(session.get("rules_template_name") or ""),
                "rules_html": str(session.get("rules_html") or ""),
                "rules_presentation_json": session.get("rules_presentation_json"),
            }
            after = {
                "rules_template_id": template_id,
                "rules_template_name": str(row["name"]),
                "rules_html": str(row["content_html"] or ""),
                "rules_presentation_json": row["presentation_json"],
            }
            if before == after:
                return
            conn.execute(
                """
                UPDATE auction_sessions
                SET rules_template_id=?, rules_template_name=?,
                    rules_html=?, rules_presentation_json=?, updated_at=?
                WHERE id=?
                """,
                (
                    after["rules_template_id"], after["rules_template_name"],
                    after["rules_html"], after["rules_presentation_json"],
                    utc_now(), int(session["id"]),
                ),
            )
            self._log_conn(
                conn, "auction_session", int(session["id"]),
                "switch_rules_template", before, after,
            )

    def delete_rule_template(self, template_id: int) -> int:
        """Delete a template and return the active template id after deletion."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, is_active FROM auction_rule_templates ORDER BY id ASC"
            ).fetchall()
            if not rows:
                return self._ensure_default_rule_template_conn(conn)
            ids = [int(row["id"]) for row in rows]
            target_id = int(template_id)
            if target_id not in ids:
                raise ValueError("Шаблон правил не найден.")
            if len(ids) <= 1:
                raise ValueError("Последний шаблон правил удалить нельзя.")

            was_active = any(
                int(row["id"]) == target_id and int(row["is_active"]) == 1
                for row in rows
            )
            conn.execute(
                "DELETE FROM auction_rule_templates WHERE id=?",
                (target_id,),
            )
            if was_active:
                fallback = conn.execute(
                    "SELECT id FROM auction_rule_templates ORDER BY name COLLATE NOCASE ASC, id ASC LIMIT 1"
                ).fetchone()
                assert fallback is not None
                fallback_id = int(fallback["id"])
                conn.execute("UPDATE auction_rule_templates SET is_active=0")
                conn.execute(
                    "UPDATE auction_rule_templates SET is_active=1 WHERE id=?",
                    (fallback_id,),
                )
                return fallback_id

            active = conn.execute(
                "SELECT id FROM auction_rule_templates WHERE is_active=1 LIMIT 1"
            ).fetchone()
            if active is None:
                return self._ensure_default_rule_template_conn(conn)
            return int(active["id"])

    def get_auction_rules_snapshot(self, auction_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, rules_template_id, rules_template_name, rules_html
                FROM auction_sessions
                WHERE id=?
                """,
                (int(auction_id),),
            ).fetchone()
            if row is None:
                return None
            return {
                "auction_id": int(row["id"]),
                "template_id": (
                    int(row["rules_template_id"])
                    if row["rules_template_id"] is not None
                    else None
                ),
                "template_name": str(row["rules_template_name"] or ""),
                "content_html": str(row["rules_html"] or ""),
            }

    def _active_rule_snapshot_conn(self, conn: sqlite3.Connection) -> dict[str, Any]:
        template_id = self._ensure_default_rule_template_conn(conn)
        row = conn.execute(
            "SELECT id, name, content_html, presentation_json FROM auction_rule_templates WHERE id=?",
            (template_id,),
        ).fetchone()
        assert row is not None
        return {
            "template_id": int(row["id"]),
            "template_name": str(row["name"]),
            "content_html": str(row["content_html"] or ""),
            "presentation_json": row["presentation_json"],
        }

    @staticmethod
    def _bounded_int_setting(value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(str(value).strip())
        except (TypeError, ValueError):
            return int(default)
        return max(int(minimum), min(int(maximum), parsed))

    def set_rules_preview_selection(self, token: str, template_id: int) -> None:
        """Set one editor's transient preview target; never activate a template.

        Only an explicit preview token can read this value. The normal
        on-air Rules route is entirely independent of this registry.
        """
        if not isinstance(token, str) or not token or len(token) > 128:
            raise ValueError("Некорректная ссылка предпросмотра правил.")
        template_id = int(template_id)
        with self.connect() as conn:
            exists = conn.execute(
                "SELECT 1 FROM auction_rule_templates WHERE id=?",
                (template_id,),
            ).fetchone()
        if exists is None:
            raise ValueError("Шаблон правил для предпросмотра не найден.")
        with self._rules_preview_selection_lock:
            self._rules_preview_selections[token] = template_id

    def get_rules_preview_selection(self, token: str) -> int | None:
        """Resolve a running editor preview, not a stored Rules preference."""
        if not isinstance(token, str) or not token:
            return None
        with self._rules_preview_selection_lock:
            return self._rules_preview_selections.get(token)

    def clear_rules_preview_selection(self, token: str) -> None:
        """Expire the editor's preview link on dialog close."""
        with self._rules_preview_selection_lock:
            self._rules_preview_selections.pop(token, None)

    def current_rules_payload(
        self, *, preview_template_id: int | None = None,
    ) -> dict[str, Any]:
        """Read-only Rules API. Only preview callers may select another template.

        Without a preview selector, open-session ownership and active-template
        rendering are strictly unchanged. No read request writes template state.
        """
        keys = (
            RULES_OVERLAY_VISIBLE_KEY,
            WIDGETS["rules"].key,
            RULES_OVERLAY_AUTOSCROLL_KEY,
            RULES_OVERLAY_BACKGROUND_KEY,
            RULES_OVERLAY_BACKGROUND_COLOR_KEY,
            RULES_OVERLAY_BACKGROUND_OPACITY_KEY,
            RULES_OVERLAY_PADDING_KEY,
        )
        # /rules-overlay polls frequently.  Read settings + current source from
        # one consistent SQLite snapshot instead of opening three short-lived
        # connections per request.
        with self.connect() as conn:
            settings = self._get_settings_conn(conn, keys)
            if preview_template_id is not None:
                row = conn.execute(
                    """SELECT name, content_html, presentation_json
                       FROM auction_rule_templates WHERE id=?""",
                    (int(preview_template_id),),
                ).fetchone()
                if row is None:
                    raise ValueError("Шаблон правил для предпросмотра не найден.")
                source = "template_preview"
                auction_id: int | None = None
                template_name = str(row["name"] or "")
                raw_html = str(row["content_html"] or "")
                raw_presentation = row["presentation_json"]
            else:
                session = self._get_open_auction_session_conn(conn)
                if session is not None:
                    source = "auction_snapshot"
                    auction_id = int(session["id"])
                    template_name = str(session.get("rules_template_name") or "")
                    raw_html = str(session.get("rules_html") or "")
                    raw_presentation = session.get("rules_presentation_json")
                else:
                    template = self._active_rule_snapshot_conn(conn)
                    source = "active_template"
                    auction_id = None
                    template_name = str(template["template_name"] or "")
                    raw_html = str(template["content_html"] or "")
                    raw_presentation = template["presentation_json"]

        background = str(settings.get(
            RULES_OVERLAY_BACKGROUND_KEY, RULES_OVERLAY_BACKGROUND_DEFAULT
        ) or RULES_OVERLAY_BACKGROUND_DEFAULT).strip().casefold()
        if background not in {"transparent", "color"}:
            background = RULES_OVERLAY_BACKGROUND_DEFAULT

        color = str(settings.get(
            RULES_OVERLAY_BACKGROUND_COLOR_KEY, RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT
        ) or RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT).strip().upper()
        if len(color) != 7 or not color.startswith("#"):
            color = RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT
        else:
            try:
                int(color[1:], 16)
            except ValueError:
                color = RULES_OVERLAY_BACKGROUND_COLOR_DEFAULT

        # The current session owns its frozen/live-synchronized appearance.
        # Legacy NULL or corrupt values retain the exact original global
        # presentation; widget visibility stays governed by global policy.
        template_presentation = self._read_rule_presentation_json(raw_presentation)
        return {
            "visible": show_mode(settings, "rules") != "hidden",
            "visibility": visibility_payload(settings, "rules"),
            "source": source,
            "auction_id": auction_id,
            "template_name": template_name,
            "content_html": sanitize_rules_html(raw_html),
            "presentation": template_presentation if template_presentation is not None else {
                "autoscroll": settings.get(
                    RULES_OVERLAY_AUTOSCROLL_KEY,
                    "1" if RULES_OVERLAY_AUTOSCROLL_DEFAULT else "0",
                ) == "1",
                "background": background,
                "background_color": color,
                "background_opacity": self._bounded_int_setting(
                    settings.get(RULES_OVERLAY_BACKGROUND_OPACITY_KEY),
                    RULES_OVERLAY_BACKGROUND_OPACITY_DEFAULT, 0, 100,
                ),
                "padding": self._bounded_int_setting(
                    settings.get(RULES_OVERLAY_PADDING_KEY),
                    RULES_OVERLAY_PADDING_DEFAULT, 0, 200,
                ),
            },
        }

