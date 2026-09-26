from __future__ import annotations

import sqlite3
from dataclasses import asdict
from typing import Any

from ..constants import (
    STATUS_ABANDONED, STATUS_COMPLETED, STATUS_LABELS, STATUS_NOT_PLAYED, STATUS_PLAYED, STATUS_PLAYING
)
from .common import DuplicateGameError, Game, normalize_text_key, normalize_title_key, utc_now


class GamesMixin:
    # Shared sort contract for every normal-game view/API query.  Keeping the
    # SQL in one place prevents lightweight hot-path projections from drifting
    # away from the canonical Games/Public order.
    GAME_ORDER_SQL = """
        archived ASC,
        CASE
            WHEN status='playing' THEN 1
            WHEN status IN ('played','not_played') THEN 2
            WHEN status='completed' THEN 3
            WHEN status='abandoned' THEN 4
            ELSE 9
        END ASC,
        CASE WHEN status='playing' THEN CASE WHEN release_date IS NULL THEN 1 ELSE 0 END ELSE 0 END ASC,
        CASE WHEN status='playing' THEN release_date END DESC,
        CASE WHEN status='playing' THEN sm_points END DESC,
        CASE WHEN status IN ('played','not_played','completed','abandoned') THEN sm_points END DESC,
        CASE WHEN status IN ('played','not_played','completed','abandoned') THEN CASE WHEN release_date IS NULL THEN 1 ELSE 0 END ELSE 0 END ASC,
        CASE WHEN status IN ('played','not_played','completed','abandoned') THEN release_date END DESC,
        updated_at DESC,
        id ASC
    """

    def _assert_game_not_in_open_auction_conn(
        self,
        conn: sqlite3.Connection,
        game_id: int,
        *,
        action: str,
    ) -> None:
        session = self._get_open_auction_session_for_game_conn(conn, game_id)
        if session is None:
            return
        name = str(session.get("name") or "Аукцион")
        status = str(session.get("status") or "неизвестный статус")
        raise RuntimeError(
            f"Нельзя {action} игру, пока она участвует в незавершённом "
            f"аукционе «{name}» ({status}). Сначала завершите или отмените аукцион."
        )

    @staticmethod
    def _row_to_game(row: sqlite3.Row) -> Game:
        return Game(
            id=row["id"],
            title=row["title"],
            release_date=row["release_date"],
            sm_points=row["sm_points"],
            coop=row["coop"],
            status=row["status"],
            review=row["review"],
            archived=row["archived"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _find_game_by_title_conn(
        self,
        conn: sqlite3.Connection,
        title: str,
        exclude_id: int | None = None,
    ) -> Game | None:
        key = normalize_title_key(title)
        if not key:
            return None

        rows = conn.execute(
            "SELECT * FROM games ORDER BY archived ASC, id ASC"
        ).fetchall()
        for row in rows:
            if exclude_id is not None and int(row["id"]) == int(exclude_id):
                continue
            if normalize_title_key(row["title"]) == key:
                return self._row_to_game(row)
        return None

    def _get_game_conn(self, conn: sqlite3.Connection, game_id: int) -> Game | None:
        row = conn.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
        return self._row_to_game(row) if row else None

    def _add_game_conn(
        self,
        conn: sqlite3.Connection,
        game: Game,
        log: bool = True,
    ) -> int:
        """Insert a game using an already-open transaction.

        Public ``add_game`` delegates here, and bulk operations such as CSV
        import reuse the same validation/logging without opening nested
        transactions for every row.
        """
        title = game.title.strip()
        now = utc_now()
        duplicate = self._find_game_by_title_conn(conn, title)
        if duplicate is not None:
            raise DuplicateGameError(duplicate.id, duplicate.title)

        cur = conn.execute(
            """
            INSERT INTO games(title,release_date,sm_points,coop,status,review,archived,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                title, game.release_date, game.sm_points, game.coop,
                game.status, game.review.strip(), game.archived, now, now,
            ),
        )
        game_id = int(cur.lastrowid)
        if log:
            after = asdict(game)
            after.update({"id": game_id, "created_at": now, "updated_at": now})
            self._log_conn(conn, "game", game_id, "create", None, after)
        return game_id

    def add_game(self, game: Game, log: bool = True) -> int:
        with self.connect() as conn:
            return self._add_game_conn(conn, game, log=log)

    def _update_game_conn(
        self,
        conn: sqlite3.Connection,
        game_id: int,
        changes: dict[str, Any],
    ) -> bool:
        """Update a game inside an existing transaction.

        The business rules are shared with ``update_game`` so CSV import and
        normal UI edits cannot drift apart.
        """
        allowed = {"title", "release_date", "sm_points", "coop", "status", "review", "archived"}
        bad = set(changes) - allowed
        if bad:
            raise ValueError(f"Недопустимые поля: {', '.join(sorted(bad))}")
        before = self._get_game_conn(conn, game_id)
        if before is None:
            raise KeyError(game_id)

        values = dict(changes)
        if "title" in values:
            values["title"] = str(values["title"]).strip()
            duplicate = self._find_game_by_title_conn(
                conn,
                values["title"],
                exclude_id=game_id,
            )
            if duplicate is not None:
                raise DuplicateGameError(duplicate.id, duplicate.title)
        if "review" in values:
            values["review"] = str(values["review"]).strip()

        if not any(getattr(before, key) != value for key, value in values.items()):
            return False

        if int(values.get("archived", 0) or 0) == 1 and not int(before.archived):
            self._assert_game_not_in_open_auction_conn(
                conn,
                game_id,
                action="переместить в архив",
            )

        values["updated_at"] = utc_now()
        fields = ", ".join(f"{k}=?" for k in values)
        conn.execute(
            f"UPDATE games SET {fields} WHERE id=?",
            [*values.values(), game_id],
        )
        after = self._get_game_conn(conn, game_id)
        self._log_conn(conn, "game", game_id, "update", asdict(before), asdict(after))
        return True

    def update_game(self, game_id: int, changes: dict[str, Any]) -> bool:
        """Обновляет игру только при реальном изменении данных.

        Это важно для updated_at: простое открытие формы и нажатие «Сохранить»
        не должно менять порядок игр при полном равенстве сортировочных полей.
        """
        with self.connect() as conn:
            return self._update_game_conn(conn, game_id, changes)

    def archive_game(self, game_id: int, archived: bool = True) -> None:
        self.update_game(game_id, {"archived": 1 if archived else 0})

    def delete_game(self, game_id: int) -> None:
        """Безвозвратно удаляет игру и связанные рабочие данные.

        Contributions удаляются каскадно. Auction entries удаляются явно, чтобы
        одиночное удаление сохранило прежнюю семантику даже после schema 10,
        где исторические записи умеют переживать массовую очистку игр.
        Предыдущая подробная история change_log по игре очищается, после чего
        сохраняется только минимальная audit-запись о самом факте удаления.
        """
        game = self.get_game(game_id)
        if game is None:
            raise KeyError(game_id)

        with self.connect() as conn:
            self._assert_game_not_in_open_auction_conn(
                conn,
                game_id,
                action="удалить",
            )

            # Если игра была выбрана как текущая для OBS — очищаем ссылку.
            current = conn.execute(
                "SELECT value FROM settings WHERE key='stream_current_game_id'"
            ).fetchone()
            if current and str(current[0]) == str(game_id):
                conn.execute(
                    "UPDATE settings SET value='' WHERE key='stream_current_game_id'"
                )

            # change_log не имеет внешнего ключа, поэтому чистим его явно.
            conn.execute(
                "DELETE FROM change_log WHERE entity_type='game' AND entity_id=?",
                (game_id,),
            )

            # В schema 10 auction_entries.game_id использует ON DELETE SET NULL
            # ради сохранения завершённой истории при массовой очистке. Одиночное
            # удаление остаётся прежним: связанные записи этого game_id удаляем
            # явно, contributions уйдут каскадно вместе с games.
            conn.execute("DELETE FROM auction_entries WHERE game_id=?", (game_id,))
            conn.execute("DELETE FROM games WHERE id=?", (game_id,))

            # Предыдущие снимки игры удалены выше, но сам факт безвозвратного
            # удаления должен оставаться видимым в техническом журнале.
            self._log_conn(
                conn,
                "game",
                game_id,
                "delete",
                None,
                {"title": game.title, "deleted": True},
            )

    def sync_main_games_state(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        """Replace the permanent main-list state from a validated shared XLSX.

        Matching intentionally uses the same normalized title rule as the normal
        UI. The XLSX is the complete shared state: missing permanent rows are
        deleted, new rows are added, and existing rows are updated atomically.
        Temporary ``auction_only`` lots are outside this contract.
        """
        incoming: dict[str, dict[str, Any]] = {}
        for row in rows:
            title = str(row.get("title") or "").strip()
            key = normalize_title_key(title)
            if not key:
                raise ValueError("Совместная таблица содержит строку без названия игры.")
            if key in incoming:
                raise ValueError(f"Дубликат названия в совместной таблице: «{title}».")
            incoming[key] = {
                "title": title,
                "release_date": row.get("release_date") or None,
                "sm_points": max(0, int(row.get("sm_points") or 0)),
                "coop": 1 if int(row.get("coop") or 0) else 0,
                "status": str(row.get("status") or STATUS_NOT_PLAYED),
                "review": str(row.get("review") or "").strip(),
                "archived": 1 if int(row.get("archived") or 0) else 0,
            }

        created = updated = deleted = unchanged = 0
        with self.connect() as conn:
            existing_rows = conn.execute(
                "SELECT * FROM games WHERE auction_only=0 ORDER BY id ASC"
            ).fetchall()
            existing = {
                normalize_title_key(row["title"]): self._row_to_game(row)
                for row in existing_rows
            }

            # Preflight every destructive/archive transition before the first
            # write so one blocked open-auction game cannot cause partial sync.
            for key, game in existing.items():
                payload = incoming.get(key)
                if payload is None:
                    self._assert_game_not_in_open_auction_conn(
                        conn, int(game.id), action="удалить"
                    )
                elif payload["archived"] and not int(game.archived):
                    self._assert_game_not_in_open_auction_conn(
                        conn, int(game.id), action="переместить в архив"
                    )

            for key, payload in incoming.items():
                game = existing.get(key)
                if game is None:
                    self._add_game_conn(conn, Game(id=None, **payload))
                    created += 1
                    continue
                if self._update_game_conn(conn, int(game.id), payload):
                    updated += 1
                else:
                    unchanged += 1

            for key, game in existing.items():
                if key in incoming:
                    continue
                game_id = int(game.id)

                current = conn.execute(
                    "SELECT value FROM settings WHERE key='stream_current_game_id'"
                ).fetchone()
                if current and str(current[0]) == str(game_id):
                    conn.execute(
                        "UPDATE settings SET value='' WHERE key='stream_current_game_id'"
                    )

                # Preserve the established permanent-delete semantics. Closed
                # auction history survives via snapshots; live linked rows are
                # removed with the game just as with the normal Delete action.
                conn.execute(
                    "DELETE FROM change_log WHERE entity_type='game' AND entity_id=?",
                    (game_id,),
                )
                conn.execute("DELETE FROM auction_entries WHERE game_id=?", (game_id,))
                conn.execute("DELETE FROM games WHERE id=?", (game_id,))
                self._log_conn(
                    conn,
                    "game",
                    game_id,
                    "delete",
                    None,
                    {"title": game.title, "deleted": True, "source": "shared_xlsx"},
                )
                deleted += 1

            if created or updated or deleted:
                self._log_conn(
                    conn,
                    "shared_xlsx",
                    None,
                    "apply",
                    None,
                    {
                        "created": created,
                        "updated": updated,
                        "deleted": deleted,
                        "unchanged": unchanged,
                    },
                )

        return {
            "created": created,
            "updated": updated,
            "deleted": deleted,
            "unchanged": unchanged,
        }

    def count_all_games(self) -> int:
        """Counts every game row, including archived and temporary auction lots."""
        with self.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM games").fetchone()[0] or 0)

    def clear_all_games(self) -> dict[str, int | bool]:
        """Deletes the live games database while preserving closed auction history.

        The operation is intentionally atomic and refuses to run while a local
        auction is open.  Completed/cancelled session rows and their
        ``auction_entries`` survive through the schema-10 snapshot columns;
        general ``change_log`` history is also kept intact.
        """
        with self.connect() as conn:
            placeholders = ",".join("?" for _ in self.AUCTION_OPEN_STATUSES)
            open_session = conn.execute(
                f"""
                SELECT id, name, status
                FROM auction_sessions
                WHERE provider='local'
                  AND status IN ({placeholders})
                ORDER BY id DESC
                LIMIT 1
                """,
                self.AUCTION_OPEN_STATUSES,
            ).fetchone()
            if open_session is not None:
                raise RuntimeError(
                    "Сначала завершите или отмените текущий аукцион "
                    f"«{open_session['name']}» ({open_session['status']})."
                )

            total = int(conn.execute("SELECT COUNT(*) FROM games").fetchone()[0] or 0)
            if total == 0:
                return {
                    "deleted_games": 0,
                    "preserved_auction_entries": int(
                        conn.execute("SELECT COUNT(*) FROM auction_entries").fetchone()[0] or 0
                    ),
                    "cleared_current_game": False,
                }

            # Defensive refresh for rows created by older builds. New schema-10
            # inserts already own these snapshots, but filling them again before
            # detaching game_id makes the preservation guarantee explicit.
            conn.execute(
                """
                UPDATE auction_entries
                SET snapshot_title = CASE
                        WHEN snapshot_title='' THEN COALESCE(
                            (SELECT title FROM games WHERE id=auction_entries.game_id), ''
                        ) ELSE snapshot_title END,
                    snapshot_release_date = COALESCE(
                        snapshot_release_date,
                        (SELECT release_date FROM games WHERE id=auction_entries.game_id)
                    ),
                    snapshot_coop = COALESCE(
                        snapshot_coop,
                        (SELECT coop FROM games WHERE id=auction_entries.game_id)
                    ),
                    snapshot_status = COALESCE(
                        snapshot_status,
                        (SELECT status FROM games WHERE id=auction_entries.game_id)
                    ),
                    snapshot_review = CASE
                        WHEN snapshot_review='' THEN COALESCE(
                            (SELECT review FROM games WHERE id=auction_entries.game_id), ''
                        ) ELSE snapshot_review END
                WHERE game_id IS NOT NULL
                """
            )

            current = conn.execute(
                "SELECT value FROM settings WHERE key='stream_current_game_id'"
            ).fetchone()
            cleared_current = bool(current and str(current[0]).strip())
            if cleared_current:
                conn.execute(
                    "UPDATE settings SET value='' WHERE key='stream_current_game_id'"
                )

            preserved_entries = int(
                conn.execute("SELECT COUNT(*) FROM auction_entries").fetchone()[0] or 0
            )
            contributions = int(
                conn.execute("SELECT COUNT(*) FROM contributions").fetchone()[0] or 0
            )

            # ON DELETE SET NULL detaches completed auction snapshots; contribution
            # rows remain live-game data and are removed through their CASCADE FK.
            conn.execute("DELETE FROM games")

            self._log_conn(
                conn,
                "games",
                None,
                "delete_all",
                None,
                {
                    "deleted_games": total,
                    "preserved_auction_entries": preserved_entries,
                    "deleted_contributions": contributions,
                    "cleared_current_game": cleared_current,
                },
            )
            return {
                "deleted_games": total,
                "preserved_auction_entries": preserved_entries,
                "cleared_current_game": cleared_current,
            }

    def get_game(self, game_id: int) -> Game | None:
        with self.connect() as conn:
            return self._get_game_conn(conn, game_id)

    def find_game_by_title(
        self,
        title: str,
        exclude_id: int | None = None,
    ) -> Game | None:
        """Ищет игру Unicode-регистронезависимо и без учёта лишних пробелов."""
        with self.connect() as conn:
            return self._find_game_by_title_conn(conn, title, exclude_id=exclude_id)

    def _game_stats_conn(self, conn: sqlite3.Connection) -> dict[str, int]:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN archived=0 AND status=? THEN 1 ELSE 0 END) AS playing,
                SUM(CASE WHEN archived=0 AND status=? THEN 1 ELSE 0 END) AS played,
                SUM(CASE WHEN archived=0 AND status=? THEN 1 ELSE 0 END) AS not_played,
                SUM(CASE WHEN archived=0 AND status=? THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN archived=0 AND status=? THEN 1 ELSE 0 END) AS abandoned,
                SUM(CASE WHEN archived=1 THEN 1 ELSE 0 END) AS archived,
                SUM(CASE WHEN archived=0 AND coop=1 THEN 1 ELSE 0 END) AS coop,
                SUM(CASE WHEN archived=0 AND coop=0 THEN 1 ELSE 0 END) AS noncoop
            FROM games
            WHERE auction_only=0
            """,
            (
                STATUS_PLAYING, STATUS_PLAYED, STATUS_NOT_PLAYED,
                STATUS_COMPLETED, STATUS_ABANDONED,
            ),
        ).fetchone()
        result = {key: int(row[key] or 0) for key in row.keys()}
        result["for_auction"] = result["played"] + result["not_played"]
        return result

    def game_stats(self) -> dict[str, int]:
        """Return dashboard counters with one aggregate SQLite query."""
        with self.connect() as conn:
            return self._game_stats_conn(conn)

    def _list_games_conn(
        self,
        conn: sqlite3.Connection,
        search: str = "",
        status_filter: str = "all",
        include_archived: bool = False,
    ) -> list[Game]:
        """Return normal games through an already-open SQLite connection."""
        # Временные лоты, добавленные во время аукциона, существуют в БД,
        # но до завершения сессии видны только внутри аукциона.
        where = ["auction_only=0"]
        params: list[Any] = []
        if status_filter == "archive":
            where.append("archived=1")
        elif not include_archived:
            where.append("archived=0")

        if status_filter in STATUS_LABELS:
            where.append("status=?")
            params.append(status_filter)
        elif status_filter == "middle":
            where.append("status IN (?,?)")
            params.extend([STATUS_PLAYED, STATUS_NOT_PLAYED])
        elif status_filter == "coop":
            where.append("coop=1")
        elif status_filter == "noncoop":
            where.append("coop=0")

        # Главное правило: сначала статусная группа, потом сортировка внутри группы.
        # 1) ПРОХОДИТСЯ: дата ↓, баллы SM ↓, updated ↓, id ↑
        # 2) ИГРАЛ + НЕ ИГРАЛ: баллы SM ↓, дата ↓, updated ↓, id ↑
        # 3) ПРОЙДЕНО: баллы SM ↓, дата ↓, updated ↓, id ↑
        # 4) ЗАБРОШЕНО: баллы SM ↓, дата ↓, updated ↓, id ↑
        sql = (
            f"SELECT * FROM games WHERE {' AND '.join(where)} "
            f"ORDER BY {self.GAME_ORDER_SQL}"
        )
        games = [self._row_to_game(r) for r in conn.execute(sql, params).fetchall()]

        # SQLite NOCASE работает в основном для ASCII. Фильтруем поиск в Python,
        # чтобы русский и любой другой Unicode искался без учёта регистра.
        query_key = normalize_text_key(search)
        if query_key:
            games = [
                g for g in games
                if query_key in normalize_text_key(g.title)
                or query_key in normalize_text_key(g.review)
            ]
        return games

    def list_games(
        self,
        search: str = "",
        status_filter: str = "all",
        include_archived: bool = False,
    ) -> list[Game]:
        with self.connect() as conn:
            return self._list_games_conn(
                conn,
                search=search,
                status_filter=status_filter,
                include_archived=include_archived,
            )

    def _public_games_conn(self, conn: sqlite3.Connection) -> list[dict[str, Any]]:
        rows = conn.execute(
            f"""
            SELECT id, title, sm_points, review, status
            FROM games
            WHERE auction_only=0 AND archived=0
            ORDER BY {self.GAME_ORDER_SQL}
            """
        ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "title": str(row["title"]),
                "sm_points": int(row["sm_points"]),
                "sum": int(row["sm_points"]),
                "review": str(row["review"] or ""),
                "status": STATUS_LABELS[str(row["status"])],
            }
            for row in rows
        ]

    def public_games(self) -> list[dict[str, Any]]:
        # Public/P1 needs only a subset of Game.  Avoid SELECT * + dataclass
        # construction on every UI refresh/XLSX synchronization while keeping
        # the exact canonical game order.
        with self.connect() as conn:
            return self._public_games_conn(conn)

    def games_refresh_snapshot(
        self,
        search: str = "",
        status_filter: str = "all",
        include_archived: bool = False,
    ) -> dict[str, Any]:
        """One-connection state for the Games table refresh hot path."""
        with self.connect() as conn:
            games = self._list_games_conn(
                conn,
                search=search,
                status_filter=status_filter,
                include_archived=include_archived,
            )
            positions = self._auction_position_map_conn(conn)
            stats = self._game_stats_conn(conn)
        return {"games": games, "positions": positions, "stats": stats}

    def public_refresh_snapshot(self) -> dict[str, Any]:
        """One-connection state for the Public table refresh hot path."""
        with self.connect() as conn:
            rows = self._public_games_conn(conn)
            positions = self._auction_position_map_conn(conn)
        return {"rows": rows, "positions": positions}

    def pointauc_games(self) -> list[Game]:
        # Let SQLite filter the auction group instead of loading unrelated rows
        # and discarding them in Python.
        return self.list_games(status_filter="middle")
