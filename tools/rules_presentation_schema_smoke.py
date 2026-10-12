"""P11-K: legacy schema-19 -> nullable per-template Rules presentation storage.

This is deliberately schema-only. The existing OBS rendering, global Rules
settings, template rich-text editor and live auction policy do not change.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from streaming_manager.constants import (
    SCHEMA_VERSION,
    RULES_OVERLAY_AUTOSCROLL_KEY,
    RULES_OVERLAY_BACKGROUND_COLOR_KEY,
    RULES_OVERLAY_BACKGROUND_KEY,
    RULES_OVERLAY_BACKGROUND_OPACITY_KEY,
    RULES_OVERLAY_PADDING_KEY,
)
from streaming_manager.database import Database


MIGRATION_NAME = "auction_rules_presentation_storage"


def check_columns(conn: sqlite3.Connection, expect: bool) -> None:
    for table, column in (
        ("auction_rule_templates", "presentation_json"),
        ("auction_sessions", "rules_presentation_json"),
    ):
        present = column in {
            row[1] for row in conn.execute(f"PRAGMA table_info({table})")
        }
        assert present is expect, (table, column, present, expect)


def main() -> int:
    assert SCHEMA_VERSION == 20
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = Path(tmp) / "legacy_rules.db"
        db = Database(path)
        active_id = int(db.get_active_rule_template()["id"])
        db.save_rule_template(active_id, "<p>Сохранённые правила</p>")
        other_id = db.create_rule_template(
            "Отдельный шаблон", content_html="<p>Другие правила</p>",
            make_active=False,
        )
        db.set_settings_bulk({
            RULES_OVERLAY_AUTOSCROLL_KEY: "0",
            RULES_OVERLAY_BACKGROUND_KEY: "color",
            RULES_OVERLAY_BACKGROUND_COLOR_KEY: "#123456",
            RULES_OVERLAY_BACKGROUND_OPACITY_KEY: "63",
            RULES_OVERLAY_PADDING_KEY: "37",
        })
        # A genuine legacy auction snapshot should survive the upgrade with
        # original template ID, name and text, without introducing OBS changes.
        with db.connect() as conn:
            conn.execute(
                """INSERT INTO auction_sessions(
                       name, mode, provider, started_at, created_at, status,
                       rules_template_id, rules_template_name, rules_html)
                   VALUES(?, 'max_amount', 'local', ?, ?, 'running', ?, ?, ?)""",
                ("Legacy rules auction", "2026-10-12T00:00:00+00:00",
                 "2026-10-12T00:00:00+00:00", active_id, "Основной",
                 "<p>Сохранённые правила</p>"),
            )
        before = db.current_rules_payload()
        assert before["source"] == "auction_snapshot"
        assert before["presentation"] == {
            "autoscroll": False,
            "background": "color",
            "background_color": "#123456",
            "background_opacity": 63,
            "padding": 37,
        }, before["presentation"]

        # Reproduce a schema-19 database without depending on an old executable
        # or overwriting the user's real database. SQLite >=3.35 supports DROP.
        with sqlite3.connect(path) as conn:
            check_columns(conn, True)
            conn.execute(
                "ALTER TABLE auction_rule_templates DROP COLUMN presentation_json"
            )
            conn.execute(
                "ALTER TABLE auction_sessions DROP COLUMN rules_presentation_json"
            )
            conn.execute("DELETE FROM schema_migrations WHERE name=?", (MIGRATION_NAME,))
            conn.execute(
                "UPDATE schema_meta SET value='19' WHERE key='schema_version'"
            )
            check_columns(conn, False)
            assert conn.execute(
                "SELECT COUNT(*) FROM schema_migrations"
            ).fetchone()[0] == 15

        upgraded = Database(path)
        with upgraded.connect() as conn:
            check_columns(conn, True)
            assert conn.execute(
                "SELECT value FROM schema_meta WHERE key='schema_version'"
            ).fetchone()[0] == "20"
            assert conn.execute(
                "SELECT COUNT(*) FROM schema_migrations"
            ).fetchone()[0] == 16
            assert conn.execute(
                "SELECT COUNT(*) FROM schema_migrations WHERE name=?",
                (MIGRATION_NAME,),
            ).fetchone()[0] == 1
            for template in conn.execute(
                "SELECT id,presentation_json FROM auction_rule_templates"
            ).fetchall():
                assert template["presentation_json"] is None, dict(template)
            snap = conn.execute(
                "SELECT rules_template_id,rules_template_name,rules_html,"
                "rules_presentation_json FROM auction_sessions WHERE status='running'"
            ).fetchone()
            assert snap["rules_template_id"] == active_id
            assert snap["rules_template_name"] == "Основной"
            assert snap["rules_html"] == "<p>Сохранённые правила</p>"
            assert snap["rules_presentation_json"] is None
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert upgraded.current_rules_payload() == before
        assert upgraded.get_rule_template(other_id)["content_html"] == "<p>Другие правила</p>"

        # The new nullable slots must remain dormant until explicit separate
        # template-format work. A repeated startup cannot reset stored values.
        with upgraded.connect() as conn:
            conn.execute(
                "UPDATE auction_rule_templates SET presentation_json=? WHERE id=?",
                ('{"background":"transparent"}', other_id),
            )
            conn.execute(
                "UPDATE auction_sessions SET rules_presentation_json=? "
                "WHERE status='running'",
                ('{"background":"transparent"}',),
            )
        Database(path)
        with upgraded.connect() as conn:
            assert conn.execute(
                "SELECT presentation_json FROM auction_rule_templates WHERE id=?",
                (other_id,),
            ).fetchone()[0] == '{"background":"transparent"}'
            assert conn.execute(
                "SELECT rules_presentation_json FROM auction_sessions "
                "WHERE status='running'"
            ).fetchone()[0] == '{"background":"transparent"}'
            assert conn.execute(
                "SELECT COUNT(*) FROM schema_migrations WHERE name=?",
                (MIGRATION_NAME,),
            ).fetchone()[0] == 1
        assert upgraded.current_rules_payload() == before
        # Creating a new template retains the legacy (NULL) fallback.
        new_id = upgraded.create_rule_template("После обновления", make_active=False)
        with upgraded.connect() as conn:
            assert conn.execute(
                "SELECT presentation_json FROM auction_rule_templates WHERE id=?",
                (new_id,),
            ).fetchone()[0] is None

    print("P11_K_RULES_SCHEMA19_COMPATIBLE_PRESENTATION_STORAGE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
