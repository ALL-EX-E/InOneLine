from __future__ import annotations

import sqlite3
from pathlib import Path
from contextlib import contextmanager

from ..constants import SCHEMA_VERSION
from ..media import (
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
    MEDIA_STORAGE_MANAGED,
    managed_media_directory,
    supported_media_extensions,
)
from .common import utc_now


class SchemaMixin:
    def _configure_database(self) -> None:
        """One-time database pragmas.

        WAL is a persistent database setting, so reissuing ``journal_mode=WAL``
        on every short read connection only adds needless work. Connection-local
        pragmas stay in :meth:`connect`.
        """
        conn = sqlite3.connect(self.path, timeout=10)
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA busy_timeout = 10000")
            conn.commit()
        finally:
            conn.close()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 10000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _run_migration(conn, name: str, version: int, migration) -> bool:
        row = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE name=?",
            (name,),
        ).fetchone()
        if row is not None:
            return False
        migration(conn)
        conn.execute(
            "INSERT INTO schema_migrations(name, version, applied_at) "
            "VALUES(?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
            (name, int(version)),
        )
        return True

    def _init_schema(self) -> None:
        protected_migration_ran = False
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS schema_migrations (
                    name TEXT PRIMARY KEY,
                    version INTEGER NOT NULL,
                    applied_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    release_date TEXT,
                    amount_kopecks INTEGER NOT NULL DEFAULT 0 CHECK(amount_kopecks >= 0),
                    sm_points INTEGER NOT NULL DEFAULT 0 CHECK(sm_points >= 0),
                    coop INTEGER NOT NULL DEFAULT 0 CHECK(coop IN (0,1)),
                    status TEXT NOT NULL CHECK(status IN ('playing','played','not_played','completed','abandoned')),
                    review TEXT NOT NULL DEFAULT '',
                    archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1)),
                    auction_only INTEGER NOT NULL DEFAULT 0 CHECK(auction_only IN (0,1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_games_title ON games(title COLLATE NOCASE);
                CREATE INDEX IF NOT EXISTS idx_games_status ON games(status, archived);

                CREATE TABLE IF NOT EXISTS change_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER,
                    action TEXT NOT NULL,
                    before_json TEXT,
                    after_json TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                    source TEXT NOT NULL,
                    external_event_id TEXT,
                    contributor TEXT,
                    amount_minor INTEGER,
                    currency TEXT,
                    points REAL,
                    unit TEXT,
                    source_amount_text TEXT,
                    source_unit TEXT,
                    conversion_rate TEXT,
                    credited_sm_points INTEGER CHECK(credited_sm_points IS NULL OR credited_sm_points >= 0),
                    note TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(source, external_event_id)
                );

                CREATE TABLE IF NOT EXISTS external_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    external_event_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    processing_status TEXT NOT NULL DEFAULT 'new',
                    created_at TEXT NOT NULL,
                    processed_at TEXT,
                    UNIQUE(source, external_event_id)
                );

                CREATE TABLE IF NOT EXISTS conversion_units (
                    unit TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    unit_kind TEXT NOT NULL
                        CHECK(unit_kind IN ('currency','service')),
                    service TEXT NOT NULL DEFAULT '',
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS auction_rule_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    content_html TEXT NOT NULL DEFAULT '',
                    is_active INTEGER NOT NULL DEFAULT 0 CHECK(is_active IN (0,1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_auction_rule_templates_active
                    ON auction_rule_templates(is_active) WHERE is_active=1;

                CREATE TABLE IF NOT EXISTS auction_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'normal',
                    provider TEXT NOT NULL DEFAULT 'local',
                    started_at TEXT,
                    finished_at TEXT,
                    created_at TEXT NOT NULL,
                    rules_template_id INTEGER REFERENCES auction_rule_templates(id) ON DELETE SET NULL,
                    rules_template_name TEXT NOT NULL DEFAULT '',
                    rules_html TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS auction_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    auction_id INTEGER NOT NULL REFERENCES auction_sessions(id) ON DELETE CASCADE,
                    game_id INTEGER REFERENCES games(id) ON DELETE SET NULL,
                    weight REAL NOT NULL DEFAULT 1,
                    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
                    external_lot_id TEXT,
                    result TEXT,
                    starting_amount_kopecks INTEGER NOT NULL DEFAULT 0,
                    bid_amount_kopecks INTEGER NOT NULL DEFAULT 0,
                    starting_sm_points INTEGER NOT NULL DEFAULT 0,
                    bid_sm_points INTEGER NOT NULL DEFAULT 0,
                    snapshot_title TEXT NOT NULL DEFAULT '',
                    snapshot_release_date TEXT,
                    snapshot_coop INTEGER CHECK(snapshot_coop IN (0,1) OR snapshot_coop IS NULL),
                    snapshot_status TEXT,
                    snapshot_review TEXT NOT NULL DEFAULT '',
                    start_position INTEGER CHECK(start_position IS NULL OR start_position >= 1),
                    UNIQUE(auction_id, game_id)
                );

                CREATE TABLE IF NOT EXISTS pending_conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_event_row_id INTEGER NOT NULL UNIQUE
                        REFERENCES external_events(id) ON DELETE CASCADE,
                    game_id INTEGER REFERENCES games(id) ON DELETE SET NULL,
                    auction_id INTEGER REFERENCES auction_sessions(id) ON DELETE SET NULL,
                    source_amount_text TEXT NOT NULL,
                    source_unit TEXT NOT NULL,
                    source_unit_label TEXT NOT NULL,
                    unit_kind TEXT NOT NULL
                        CHECK(unit_kind IN ('currency','service')),
                    contributor TEXT,
                    note TEXT,
                    status TEXT NOT NULL DEFAULT 'awaiting_rate'
                        CHECK(status IN ('awaiting_rate','awaiting_manual_apply','applied','cancelled','error')),
                    applied_rate TEXT,
                    credited_sm_points INTEGER
                        CHECK(credited_sm_points IS NULL OR credited_sm_points >= 0),
                    created_at TEXT NOT NULL,
                    applied_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_pending_conversions_status
                    ON pending_conversions(status, id);
                CREATE INDEX IF NOT EXISTS idx_pending_conversions_unit
                    ON pending_conversions(source_unit, status);

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            # Named, idempotent migrations make future schema growth explicit.
            # Existing 0.2.x databases have no migration history; the legacy
            # migration functions are safe to run once and then are recorded.
            self._run_migration(
                conn,
                "games_status_abandoned",
                4,
                self._migrate_games_status_check_if_needed,
            )
            self._run_migration(
                conn,
                "games_auction_only",
                5,
                self._migrate_games_auction_only_if_needed,
            )
            self._run_migration(
                conn,
                "auction_session_extended",
                6,
                self._migrate_auction_schema_if_needed,
            )
            self._run_migration(
                conn,
                "promote_cancelled_temporary_auction_lots",
                8,
                self._migrate_cancelled_temporary_lots,
            )
            self._run_migration(
                conn,
                "performance_indexes",
                9,
                self._migrate_performance_indexes,
            )
            self._run_migration(
                conn,
                "auction_entry_game_snapshots",
                10,
                self._migrate_auction_entry_game_snapshots,
            )
            self._run_migration(
                conn,
                "auction_timer_milliseconds",
                11,
                self._migrate_auction_timer_milliseconds,
            )
            self._run_migration(
                conn,
                "streaming_manager_integer_points",
                12,
                self._migrate_streaming_manager_integer_points,
            )
            self._run_migration(
                conn,
                "dynamic_conversion_registry_and_pending_events",
                13,
                self._migrate_dynamic_conversion_registry_and_pending_events,
            )
            self._run_migration(
                conn,
                "auction_start_positions",
                14,
                self._migrate_auction_start_positions,
            )
            self._run_migration(
                conn,
                "wheel_verification_snapshots",
                15,
                self._migrate_wheel_verification_snapshots,
            )
            self._run_migration(
                conn,
                "common_media_assets",
                16,
                self._migrate_common_media_assets,
            )
            protected_migration_ran = self._run_migration(
                conn,
                "integration_connections_and_protected_credentials",
                17,
                self._migrate_integration_connections_and_protected_credentials,
            )
            self._run_migration(
                conn,
                "auction_rules_templates_and_session_snapshot",
                18,
                self._migrate_auction_rules_templates_and_session_snapshot,
            )
            conn.execute(
                "INSERT OR REPLACE INTO schema_meta(key,value) VALUES('schema_version',?)",
                (str(SCHEMA_VERSION),),
            )
            defaults = {
                "stream_current_game_id": "",
                "stream_info": "",
                "stream_info_enabled": "1",
                "stream_format": "16:9",
                "overlay_webcam_enabled": "1",
                "overlay_webcam_position": "top_right",
                "overlay_list_enabled": "1",
                "overlay_list_side": "auto",
                "overlay_info_position": "auto",
                "overlay_background_file": "",
                "overlay_background_media_id": "",
                "overlay_background_mode": "stretch",
                "overlay_frame_color": "#FFFFFF",
                "overlay_font_title_family": "Segoe UI",
                "overlay_font_title_size": "30",
                "overlay_font_title_color": "#FFFFFF",
                "overlay_font_top1_family": "Segoe UI",
                "overlay_font_top1_size": "17",
                "overlay_font_top1_color": "#FFFFFF",
                "overlay_font_top2_family": "Segoe UI",
                "overlay_font_top2_size": "17",
                "overlay_font_top2_color": "#FFFFFF",
                "overlay_font_top3_family": "Segoe UI",
                "overlay_font_top3_size": "17",
                "overlay_font_top3_color": "#FFFFFF",
                "overlay_font_list_family": "Segoe UI",
                "overlay_font_list_size": "17",
                "overlay_font_list_color": "#FFFFFF",
                "overlay_font_info_family": "Segoe UI",
                "overlay_font_info_size": "17",
                "overlay_font_info_color": "#FFFFFF",
                "api_port": "8765",
                "random_org_credential_ref": "",
                "conversion_rub_points_per_unit": "1",
                # S2 settings are ordinary persisted preferences; inserting
                # defaults here does not change the schema version.
                "auction_auto_extend_leader_enabled": "0",
                "auction_auto_extend_leader_ms": "30000",
                "auction_auto_extend_new_lot_enabled": "0",
                "auction_auto_extend_new_lot_ms": "60000",
                "auction_auto_extend_external_enabled": "0",
                "auction_auto_extend_external_ms": "60000",
                "auction_auto_extend_threshold_enabled": "1",
                "auction_auto_extend_threshold_ms": "120000",
            }
            for key, value in defaults.items():
                conn.execute(
                    "INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (key, value)
                )

        if protected_migration_ran:
            self._scrub_legacy_plaintext_secrets()

    def _scrub_legacy_plaintext_secrets(self) -> None:
        """One-time schema-17 physical scrub after moving legacy secrets.

        Deleting a SQLite row is not enough because old payload bytes can remain
        in database pages.  After the migration transaction commits, checkpoint
        the scrubbed pages, VACUUM the database, then truncate WAL so the former
        plaintext RANDOM.ORG key cannot remain in SQLite/WAL free space.
        """
        conn = sqlite3.connect(self.path, timeout=10)
        try:
            conn.execute("PRAGMA busy_timeout = 10000")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.execute("VACUUM")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            conn.close()

    def _migrate_common_media_assets(self, conn: sqlite3.Connection) -> None:
        """Create W2 shared media metadata and adopt the legacy background library.

        The infrastructure is shared, while each media purpose keeps its own
        managed folder.  Existing ``data/overlay_backgrounds`` files are not
        moved or rewritten; they are registered in place so 0.3.48 users keep
        the same library and selected background after migration.
        """
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS media_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                storage_mode TEXT NOT NULL
                    CHECK(storage_mode IN ('managed','external')),
                managed_name TEXT NOT NULL DEFAULT '',
                external_path TEXT NOT NULL DEFAULT '',
                original_name TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK(
                    (storage_mode='managed' AND managed_name<>'' AND external_path='')
                    OR
                    (storage_mode='external' AND external_path<>'' AND managed_name='')
                )
            );
            CREATE INDEX IF NOT EXISTS idx_media_assets_category
                ON media_assets(category, id);
            CREATE INDEX IF NOT EXISTS idx_media_assets_storage
                ON media_assets(category, storage_mode, id);
            """
        )

        category = MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
        directory = managed_media_directory(self.path.parent, category)
        directory.mkdir(parents=True, exist_ok=True)
        allowed = supported_media_extensions(category)
        known: dict[str, int] = {}
        for row in conn.execute(
            "SELECT id, managed_name FROM media_assets "
            "WHERE category=? AND storage_mode=?",
            (category, MEDIA_STORAGE_MANAGED),
        ).fetchall():
            known[str(row["managed_name"] or "").casefold()] = int(row["id"])

        names = [
            path.name
            for path in sorted(directory.iterdir(), key=lambda item: item.name.casefold())
            if path.is_file() and path.suffix.lower() in allowed
        ]
        legacy_row = conn.execute(
            "SELECT value FROM settings WHERE key='overlay_background_file'"
        ).fetchone()
        legacy_selected = str(legacy_row["value"] if legacy_row else "").strip()
        if (
            legacy_selected
            and Path(legacy_selected).name == legacy_selected
            and Path(legacy_selected).suffix.lower() in allowed
            and legacy_selected.casefold() not in {name.casefold() for name in names}
        ):
            # Keep a selected-but-manually-missing legacy file visible as an
            # unavailable managed asset instead of silently forgetting it.
            names.append(legacy_selected)

        now = utc_now()
        for name in names:
            key = name.casefold()
            if key in known:
                continue
            cursor = conn.execute(
                """
                INSERT INTO media_assets(
                    category,storage_mode,managed_name,external_path,
                    original_name,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (category, MEDIA_STORAGE_MANAGED, name, "", name, now, now),
            )
            known[key] = int(cursor.lastrowid)

        if legacy_selected:
            asset_id = known.get(legacy_selected.casefold())
            if asset_id is not None:
                conn.execute(
                    "INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",
                    ("overlay_background_media_id", str(asset_id)),
                )

    def _migrate_auction_entry_game_snapshots(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Makes completed auction history independent from the live games table.

        ``auction_entries`` used to cascade-delete when a game was removed.  A
        full games reset must not erase already completed auction results, so
        each entry now owns a minimal immutable game snapshot and its live
        ``game_id`` becomes nullable with ``ON DELETE SET NULL``.  Open auction
        sessions still use normal live game IDs; bulk deletion is blocked while
        such a session exists.
        """
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(auction_entries)").fetchall()
        }
        if "snapshot_title" in columns:
            return

        conn.executescript(
            """
            ALTER TABLE auction_entries RENAME TO auction_entries_legacy_v10;

            CREATE TABLE auction_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id INTEGER NOT NULL
                    REFERENCES auction_sessions(id) ON DELETE CASCADE,
                game_id INTEGER
                    REFERENCES games(id) ON DELETE SET NULL,
                weight REAL NOT NULL DEFAULT 1,
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
                external_lot_id TEXT,
                result TEXT,
                starting_amount_kopecks INTEGER NOT NULL DEFAULT 0,
                bid_amount_kopecks INTEGER NOT NULL DEFAULT 0,
                snapshot_title TEXT NOT NULL DEFAULT '',
                snapshot_release_date TEXT,
                snapshot_coop INTEGER CHECK(snapshot_coop IN (0,1) OR snapshot_coop IS NULL),
                snapshot_status TEXT,
                snapshot_review TEXT NOT NULL DEFAULT '',
                UNIQUE(auction_id, game_id)
            );

            INSERT INTO auction_entries(
                id, auction_id, game_id, weight, active, external_lot_id, result,
                starting_amount_kopecks, bid_amount_kopecks,
                snapshot_title, snapshot_release_date, snapshot_coop,
                snapshot_status, snapshot_review
            )
            SELECT
                ae.id, ae.auction_id, ae.game_id, ae.weight, ae.active,
                ae.external_lot_id, ae.result,
                ae.starting_amount_kopecks, ae.bid_amount_kopecks,
                COALESCE(g.title, ''), g.release_date, g.coop, g.status,
                COALESCE(g.review, '')
            FROM auction_entries_legacy_v10 ae
            LEFT JOIN games g ON g.id=ae.game_id;

            DROP TABLE auction_entries_legacy_v10;

            CREATE INDEX IF NOT EXISTS idx_auction_entries_auction
                ON auction_entries(auction_id, active);
            CREATE INDEX IF NOT EXISTS idx_auction_entries_game
                ON auction_entries(game_id);
            """
        )

    def _migrate_auction_timer_milliseconds(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Adds millisecond timer persistence without breaking old backups.

        ``duration_seconds`` / ``remaining_seconds`` stay synchronized for
        compatibility with older code and diagnostics, while the new columns
        preserve sub-second pause/resume/reset state exactly.
        """
        columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(auction_sessions)"
            ).fetchall()
        }
        if "duration_ms" not in columns:
            conn.execute(
                "ALTER TABLE auction_sessions "
                "ADD COLUMN duration_ms INTEGER"
            )
        if "remaining_ms" not in columns:
            conn.execute(
                "ALTER TABLE auction_sessions "
                "ADD COLUMN remaining_ms INTEGER"
            )

        conn.execute(
            """
            UPDATE auction_sessions
            SET duration_ms=COALESCE(duration_ms, duration_seconds * 1000),
                remaining_ms=COALESCE(remaining_ms, remaining_seconds * 1000)
            """
        )

    def _migrate_streaming_manager_integer_points(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Schema 12: whole internal Streaming Manager points.

        Legacy monetary columns are retained only for upgrade/backup compatibility.
        They stop being authoritative after this migration. Existing RUB totals use
        the explicit migration rule 1 RUB = 1 SM point with ceiling to a whole
        point. Historical change_log JSON is intentionally left untouched.
        """
        game_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(games)").fetchall()
        }
        added_game_points = "sm_points" not in game_columns
        if added_game_points:
            conn.execute(
                "ALTER TABLE games ADD COLUMN "
                "sm_points INTEGER NOT NULL DEFAULT 0 CHECK(sm_points >= 0)"
            )
            conn.execute(
                "UPDATE games SET sm_points = "
                "CASE WHEN amount_kopecks <= 0 THEN 0 "
                "ELSE CAST((amount_kopecks + 99) / 100 AS INTEGER) END"
            )

        entry_columns = {
            row["name"] for row in conn.execute(
                "PRAGMA table_info(auction_entries)"
            ).fetchall()
        }
        if "starting_sm_points" not in entry_columns:
            conn.execute(
                "ALTER TABLE auction_entries ADD COLUMN "
                "starting_sm_points INTEGER NOT NULL DEFAULT 0"
            )
            conn.execute(
                "UPDATE auction_entries SET starting_sm_points = "
                "CASE WHEN starting_amount_kopecks <= 0 THEN 0 "
                "ELSE CAST((starting_amount_kopecks + 99) / 100 AS INTEGER) END"
            )
        if "bid_sm_points" not in entry_columns:
            conn.execute(
                "ALTER TABLE auction_entries ADD COLUMN "
                "bid_sm_points INTEGER NOT NULL DEFAULT 0"
            )
            # Do not ceil the legacy starting and bid aggregates independently:
            # that can inflate the lot by one point (e.g. 15.50 + 0.50 RUB).
            # Preserve the rounded current total, then keep the rounded starting
            # baseline and store only the non-negative difference as bid points.
            conn.execute(
                "UPDATE auction_entries SET bid_sm_points = MAX(0, "
                "CASE WHEN (starting_amount_kopecks + bid_amount_kopecks) <= 0 THEN 0 "
                "ELSE CAST((starting_amount_kopecks + bid_amount_kopecks + 99) / 100 AS INTEGER) END "
                "- starting_sm_points)"
            )

        contribution_columns = {
            row["name"] for row in conn.execute(
                "PRAGMA table_info(contributions)"
            ).fetchall()
        }
        contribution_additions = (
            ("source_amount_text", "TEXT"),
            ("source_unit", "TEXT"),
            ("conversion_rate", "TEXT"),
            ("credited_sm_points",
             "INTEGER CHECK(credited_sm_points IS NULL OR credited_sm_points >= 0)"),
        )
        for name, definition in contribution_additions:
            if name not in contribution_columns:
                conn.execute(
                    f"ALTER TABLE contributions ADD COLUMN {name} {definition}"
                )

        # Preserve current wheel meaning immediately after migration.
        conn.execute(
            "UPDATE auction_entries SET weight = "
            "starting_sm_points + bid_sm_points"
        )

    def _migrate_auction_start_positions(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Schema 14: frozen start positions for active auction lots.

        Historical finished sessions are intentionally left untouched because
        older schemas never persisted this fact.  If a schema-13 database is
        upgraded while a local auction is still open, its current authoritative
        active-entry order becomes the one-time starting baseline.
        """
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(auction_entries)").fetchall()
        }
        if "start_position" not in columns:
            conn.execute(
                "ALTER TABLE auction_entries ADD COLUMN "
                "start_position INTEGER "
                "CHECK(start_position IS NULL OR start_position >= 1)"
            )

        placeholders = ",".join("?" for _ in self.AUCTION_OPEN_STATUSES)
        sessions = conn.execute(
            f"""
            SELECT id
            FROM auction_sessions
            WHERE provider='local'
              AND status IN ({placeholders})
            ORDER BY id ASC
            """,
            self.AUCTION_OPEN_STATUSES,
        ).fetchall()
        for session in sessions:
            auction_id = int(session["id"])
            rows = conn.execute(
                """
                SELECT ae.id
                FROM auction_entries ae
                LEFT JOIN games g ON g.id=ae.game_id
                WHERE ae.auction_id=? AND ae.active=1
                ORDER BY
                    (ae.starting_sm_points + ae.bid_sm_points) DESC,
                    COALESCE(g.title, ae.snapshot_title) COLLATE NOCASE ASC,
                    ae.game_id ASC,
                    ae.id ASC
                """,
                (auction_id,),
            ).fetchall()
            for position, row in enumerate(rows, start=1):
                conn.execute(
                    "UPDATE auction_entries "
                    "SET start_position=? "
                    "WHERE id=? AND start_position IS NULL",
                    (position, int(row["id"])),
                )

    def _migrate_dynamic_conversion_registry_and_pending_events(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Schema 13: dynamic source-unit registry and safe pending conversion queue.

        Connection state is intentionally not persisted here. Currency rows may
        persist after they were encountered or received a saved rate;
        service-specific units remain visible only when a connected adapter
        supplies the corresponding capability. Pending external values are kept
        separate from contributions until the operator explicitly applies them.
        """
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversion_units (
                unit TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                unit_kind TEXT NOT NULL
                    CHECK(unit_kind IN ('currency','service')),
                service TEXT NOT NULL DEFAULT '',
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pending_conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_event_row_id INTEGER NOT NULL UNIQUE
                    REFERENCES external_events(id) ON DELETE CASCADE,
                game_id INTEGER REFERENCES games(id) ON DELETE SET NULL,
                auction_id INTEGER REFERENCES auction_sessions(id) ON DELETE SET NULL,
                source_amount_text TEXT NOT NULL,
                source_unit TEXT NOT NULL,
                source_unit_label TEXT NOT NULL,
                unit_kind TEXT NOT NULL
                    CHECK(unit_kind IN ('currency','service')),
                contributor TEXT,
                note TEXT,
                status TEXT NOT NULL DEFAULT 'awaiting_rate'
                    CHECK(status IN ('awaiting_rate','awaiting_manual_apply','applied','cancelled','error')),
                applied_rate TEXT,
                credited_sm_points INTEGER
                    CHECK(credited_sm_points IS NULL OR credited_sm_points >= 0),
                created_at TEXT NOT NULL,
                applied_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_pending_conversions_status
                ON pending_conversions(status, id);
            CREATE INDEX IF NOT EXISTS idx_pending_conversions_unit
                ON pending_conversions(source_unit, status);
            """
        )

        now = utc_now()
        conn.execute(
            "INSERT OR IGNORE INTO conversion_units("
            "unit,label,unit_kind,service,first_seen_at,last_seen_at"
            ") VALUES('RUB','RUB','currency','',?,?)",
            (now, now),
        )

        # Preserve any rates already saved by 0.3.20. A three-letter code is
        # treated as a currency; other keys are retained as service units but
        # are not made visible while their service is disconnected.
        rows = conn.execute(
            "SELECT key,value FROM settings "
            "WHERE key LIKE 'conversion_%_points_per_unit' AND value<>''"
        ).fetchall()
        prefix = "conversion_"
        suffix = "_points_per_unit"
        for row in rows:
            key = str(row["key"])
            if not (key.startswith(prefix) and key.endswith(suffix)):
                continue
            unit = key[len(prefix):-len(suffix)].upper()
            if not unit:
                continue
            kind = "currency" if len(unit) == 3 and unit.isalpha() else "service"
            conn.execute(
                "INSERT OR IGNORE INTO conversion_units("
                "unit,label,unit_kind,service,first_seen_at,last_seen_at"
                ") VALUES(?,?,?,?,?,?)",
                (unit, unit, kind, "", now, now),
            )

    def _migrate_wheel_verification_snapshots(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Adds immutable per-spin verification data for wheel results.

        Historical sessions are intentionally not backfilled: versions before
        schema 15 did not persist enough information to reconstruct the exact
        mathematical input of an already completed spin.
        """
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS wheel_verification_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                auction_id INTEGER NOT NULL UNIQUE
                    REFERENCES auction_sessions(id) ON DELETE CASCADE,
                algorithm_version TEXT NOT NULL,
                mode TEXT NOT NULL,
                rng_method TEXT NOT NULL,
                rng_value INTEGER NOT NULL,
                draw_upper INTEGER NOT NULL CHECK(draw_upper > 0),
                total_weight INTEGER NOT NULL CHECK(total_weight >= 0),
                equal_fallback INTEGER NOT NULL DEFAULT 0
                    CHECK(equal_fallback IN (0,1)),
                winner_game_id INTEGER NOT NULL,
                winner_title TEXT NOT NULL,
                rng_ticket_id TEXT,
                rng_serial_number INTEGER,
                rng_random_json TEXT,
                rng_signature TEXT,
                rng_verified INTEGER CHECK(rng_verified IN (0,1) OR rng_verified IS NULL),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS wheel_verification_participants (
                snapshot_id INTEGER NOT NULL
                    REFERENCES wheel_verification_snapshots(id) ON DELETE CASCADE,
                position INTEGER NOT NULL CHECK(position >= 1),
                game_id INTEGER NOT NULL,
                snapshot_title TEXT NOT NULL,
                source_weight INTEGER NOT NULL CHECK(source_weight >= 0),
                effective_weight INTEGER NOT NULL CHECK(effective_weight >= 0),
                interval_start INTEGER NOT NULL CHECK(interval_start >= 0),
                interval_end INTEGER NOT NULL CHECK(interval_end >= interval_start),
                PRIMARY KEY(snapshot_id, position),
                UNIQUE(snapshot_id, game_id)
            );

            CREATE INDEX IF NOT EXISTS idx_wheel_verification_auction
                ON wheel_verification_snapshots(auction_id);
            CREATE INDEX IF NOT EXISTS idx_wheel_verification_participants_game
                ON wheel_verification_participants(snapshot_id, game_id);
            """
        )

    def _migrate_performance_indexes(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Добавляет индексы для связей и часто используемых служебных запросов.

        Они не меняют данные и особенно важны при росте журнала, истории
        аукционов и будущих внешних поступлений. До schema 9 несколько
        операций по game_id и выбор активной локальной сессии требовали
        полного прохода по соответствующим таблицам.
        """
        conn.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_change_log_entity
                ON change_log(entity_type, entity_id, id DESC);

            CREATE INDEX IF NOT EXISTS idx_contributions_game
                ON contributions(game_id);

            CREATE INDEX IF NOT EXISTS idx_auction_entries_game
                ON auction_entries(game_id);

            CREATE INDEX IF NOT EXISTS idx_auction_sessions_provider_status
                ON auction_sessions(provider, status, id DESC);
            """
        )


    def _migrate_auction_rules_templates_and_session_snapshot(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Schema 18: reusable WYSIWYG rule templates + frozen session snapshot."""
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auction_rule_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content_html TEXT NOT NULL DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 0 CHECK(is_active IN (0,1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_auction_rule_templates_active
                ON auction_rule_templates(is_active) WHERE is_active=1
            """
        )

        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(auction_sessions)").fetchall()
        }
        if "rules_template_id" not in columns:
            conn.execute(
                "ALTER TABLE auction_sessions ADD COLUMN rules_template_id INTEGER "
                "REFERENCES auction_rule_templates(id) ON DELETE SET NULL"
            )
        if "rules_template_name" not in columns:
            conn.execute(
                "ALTER TABLE auction_sessions ADD COLUMN rules_template_name TEXT NOT NULL DEFAULT ''"
            )
        if "rules_html" not in columns:
            conn.execute(
                "ALTER TABLE auction_sessions ADD COLUMN rules_html TEXT NOT NULL DEFAULT ''"
            )

        row = conn.execute(
            "SELECT id FROM auction_rule_templates ORDER BY is_active DESC, id ASC LIMIT 1"
        ).fetchone()
        if row is None:
            now = utc_now()
            conn.execute(
                """
                INSERT INTO auction_rule_templates(
                    name, content_html, is_active, created_at, updated_at
                )
                VALUES('Основной', '', 1, ?, ?)
                """,
                (now, now),
            )
        elif conn.execute(
            "SELECT 1 FROM auction_rule_templates WHERE is_active=1 LIMIT 1"
        ).fetchone() is None:
            conn.execute(
                "UPDATE auction_rule_templates SET is_active=1 WHERE id=?",
                (int(row["id"]),),
            )

    def _migrate_integration_connections_and_protected_credentials(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Schema 17: B1 integration connection metadata + protected secrets.

        The table intentionally contains only non-secret provider metadata and an
        opaque ``credential_ref``.  Existing RANDOM.ORG plaintext from schema 16
        is moved to ``CredentialStore`` before the legacy setting is deleted.
        """
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS integration_connections (
                service_key TEXT PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
                status TEXT NOT NULL DEFAULT 'not_configured'
                    CHECK(status IN ('not_configured','requires_login','connected','error')),
                credential_ref TEXT NOT NULL DEFAULT '',
                provider_config_json TEXT NOT NULL DEFAULT '{}',
                last_check_at TEXT,
                last_error TEXT NOT NULL DEFAULT '',
                last_event_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_integration_connections_status
                ON integration_connections(enabled, status, service_key);
            """
        )

        conn.execute("PRAGMA secure_delete = ON")
        legacy = conn.execute(
            "SELECT value FROM settings WHERE key='random_org_api_key'"
        ).fetchone()
        ref_row = conn.execute(
            "SELECT value FROM settings WHERE key='random_org_credential_ref'"
        ).fetchone()
        existing_ref = str(ref_row["value"] or "").strip() if ref_row else ""
        secret = str(legacy["value"] or "").strip() if legacy else ""
        if secret:
            protected_ref = self.credential_store.put(
                secret, credential_ref=existing_ref or None
            )
            conn.execute(
                "INSERT INTO settings(key,value) VALUES('random_org_credential_ref',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (protected_ref,),
            )
        else:
            conn.execute(
                "INSERT OR IGNORE INTO settings(key,value) "
                "VALUES('random_org_credential_ref','')"
            )
        conn.execute("DELETE FROM settings WHERE key='random_org_api_key'")

    def _migrate_games_auction_only_if_needed(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Добавляет скрытый флаг временных лотов текущего аукциона."""
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(games)").fetchall()
        }
        if "auction_only" not in columns:
            conn.execute(
                "ALTER TABLE games ADD COLUMN "
                "auction_only INTEGER NOT NULL DEFAULT 0 "
                "CHECK(auction_only IN (0,1))"
            )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_games_auction_only "
            "ON games(auction_only, archived, status)"
        )

    def _migrate_cancelled_temporary_lots(
        self,
        conn: sqlite3.Connection,
    ) -> None:
        """Возвращает скрытые временные лоты закрытых сессий в основную базу.

        В 0.2.68–0.2.77 временный лот после отмены аукциона мог остаться
        ``auction_only=1``. Он не показывался в основной таблице и не попадал
        в стартовый список следующего аукциона, но повторное добавление находило
        ту же скрытую запись и прибавляло значение. Сохраняем данные и делаем такие
        лоты обычными играми, если они больше не принадлежат открытой сессии.
        """
        now = utc_now()
        open_statuses = (
            "running", "paused", "awaiting_wheel",
            "winner_selected", "tie_break_required",
        )
        placeholders = ",".join("?" for _ in open_statuses)
        conn.execute(
            f"""
            UPDATE games
            SET auction_only=0, updated_at=?
            WHERE auction_only=1
              AND NOT EXISTS (
                  SELECT 1
                  FROM auction_entries ae
                  JOIN auction_sessions s ON s.id=ae.auction_id
                  WHERE ae.game_id=games.id
                    AND s.provider='local'
                    AND s.status IN ({placeholders})
              )
            """,
            (now, *open_statuses),
        )

    def _migrate_auction_schema_if_needed(self, conn: sqlite3.Connection) -> None:
        """Расширяет заготовочные таблицы полноценной локальной сессией аукциона."""
        session_columns = {
            row["name"] for row in conn.execute(
                "PRAGMA table_info(auction_sessions)"
            ).fetchall()
        }
        session_additions = (
            ("status", "TEXT NOT NULL DEFAULT 'finished'"),
            ("duration_seconds", "INTEGER NOT NULL DEFAULT 600"),
            ("remaining_seconds", "INTEGER NOT NULL DEFAULT 0"),
            ("deadline_at", "TEXT"),
            ("winner_game_id", "INTEGER"),
            ("updated_at", "TEXT"),
            ("rng_method", "TEXT NOT NULL DEFAULT 'local'"),
            ("rng_ticket_id", "TEXT"),
            ("rng_value", "INTEGER"),
            ("rng_serial_number", "INTEGER"),
            ("rng_random_json", "TEXT"),
            ("rng_signature", "TEXT"),
            ("rng_verified", "INTEGER"),
            ("wheel_duration_ms", "INTEGER NOT NULL DEFAULT 8000"),
            ("wheel_spin_id", "TEXT"),
            ("wheel_started_at", "TEXT"),
            ("wheel_target_rotation", "REAL"),
        )
        for name, definition in session_additions:
            if name not in session_columns:
                conn.execute(
                    f"ALTER TABLE auction_sessions ADD COLUMN {name} {definition}"
                )

        entry_columns = {
            row["name"] for row in conn.execute(
                "PRAGMA table_info(auction_entries)"
            ).fetchall()
        }
        entry_additions = (
            ("starting_amount_kopecks", "INTEGER NOT NULL DEFAULT 0"),
            ("bid_amount_kopecks", "INTEGER NOT NULL DEFAULT 0"),
        )
        for name, definition in entry_additions:
            if name not in entry_columns:
                conn.execute(
                    f"ALTER TABLE auction_entries ADD COLUMN {name} {definition}"
                )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_auction_sessions_status "
            "ON auction_sessions(status, id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_auction_entries_auction "
            "ON auction_entries(auction_id, active)"
        )

    def _migrate_games_status_check_if_needed(self, conn: sqlite3.Connection) -> None:
        """Расширяет старую таблицу games статусом abandoned без потери данных.

        В версиях до 0.2.10 CHECK разрешал только четыре статуса. SQLite не умеет
        менять CHECK через ALTER COLUMN, поэтому таблица безопасно пересоздаётся.
        """
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='games'"
        ).fetchone()
        table_sql = (row["sql"] if row else "") or ""
        if "'abandoned'" in table_sql or '"abandoned"' in table_sql:
            return

        # Миграция выполняется с отключённой проверкой внешних ключей.
        # Данные связанных таблиц не удаляются: game_id остаются теми же.
        conn.commit()
        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            conn.executescript(
                """
                BEGIN IMMEDIATE;

                CREATE TABLE games_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    release_date TEXT,
                    amount_kopecks INTEGER NOT NULL DEFAULT 0 CHECK(amount_kopecks >= 0),
                    coop INTEGER NOT NULL DEFAULT 0 CHECK(coop IN (0,1)),
                    status TEXT NOT NULL CHECK(status IN ('playing','played','not_played','completed','abandoned')),
                    review TEXT NOT NULL DEFAULT '',
                    archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1)),
                    auction_only INTEGER NOT NULL DEFAULT 0 CHECK(auction_only IN (0,1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                INSERT INTO games_new(
                    id,title,release_date,amount_kopecks,coop,status,review,
                    archived,auction_only,created_at,updated_at
                )
                SELECT
                    id,title,release_date,amount_kopecks,coop,status,review,
                    archived,0,created_at,updated_at
                FROM games;

                DROP TABLE games;
                ALTER TABLE games_new RENAME TO games;

                CREATE INDEX IF NOT EXISTS idx_games_title ON games(title COLLATE NOCASE);
                CREATE INDEX IF NOT EXISTS idx_games_status ON games(status, archived);

                COMMIT;
                """
            )
        except Exception:
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            conn.execute("PRAGMA foreign_keys = ON")

        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(
                "Ошибка миграции базы: нарушены внешние связи после добавления статуса ЗАБРОШЕНО."
            )
