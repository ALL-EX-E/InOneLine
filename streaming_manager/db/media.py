from __future__ import annotations

import filecmp
import shutil
from pathlib import Path

from ..constants import WHEEL_SOUNDTRACK_MEDIA_ID_KEY
from ..media import (
    LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES,
    MEDIA_CATEGORY_MUSIC,
    MEDIA_CATEGORY_SOUNDTRACK,
    MEDIA_STORAGE_EXTERNAL,
    MEDIA_STORAGE_MANAGED,
    MediaAsset,
    is_supported_media_name,
    managed_media_directory,
    supported_media_extensions,
)
from .common import utc_now


class MediaMixin:
    @staticmethod
    def _media_asset_from_row(row) -> MediaAsset:
        return MediaAsset(
            id=int(row["id"]),
            category=str(row["category"]),
            storage_mode=str(row["storage_mode"]),
            managed_name=str(row["managed_name"] or ""),
            external_path=str(row["external_path"] or ""),
            original_name=str(row["original_name"] or ""),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def list_media_assets(self, category: str) -> list[MediaAsset]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM media_assets WHERE category=? ORDER BY id ASC",
                (str(category),),
            ).fetchall()
        assets = [self._media_asset_from_row(row) for row in rows]
        return sorted(assets, key=lambda item: (item.display_name.casefold(), item.id))

    def _get_media_asset_conn(self, conn, asset_id: int) -> MediaAsset | None:
        row = conn.execute(
            "SELECT * FROM media_assets WHERE id=?",
            (int(asset_id),),
        ).fetchone()
        return self._media_asset_from_row(row) if row is not None else None

    def get_media_asset(self, asset_id: int) -> MediaAsset | None:
        with self.connect() as conn:
            return self._get_media_asset_conn(conn, asset_id)

    @staticmethod
    def _media_asset_filename(asset: MediaAsset) -> str:
        if asset.storage_mode == MEDIA_STORAGE_MANAGED:
            return Path(asset.managed_name).name
        if asset.storage_mode == MEDIA_STORAGE_EXTERNAL:
            return Path(asset.external_path).name
        return str(asset.display_name or "")

    def media_assets_by_filename(
        self,
        category: str,
        filename: str,
    ) -> list[MediaAsset]:
        wanted = Path(str(filename)).name.casefold()
        if not wanted:
            return []
        return [
            asset
            for asset in self.list_media_assets(category)
            if self._media_asset_filename(asset).casefold() == wanted
        ]

    def promote_external_media_asset_to_managed(
        self,
        asset_id: int,
        managed_name: str,
        original_name: str | None = None,
    ) -> MediaAsset:
        name = Path(str(managed_name)).name
        if not name or name != str(managed_name):
            raise ValueError("Managed media must be one filename")

        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM media_assets WHERE id=?",
                (int(asset_id),),
            ).fetchone()
            if row is None:
                raise ValueError("Media asset not found")
            current = self._media_asset_from_row(row)
            if current.storage_mode != MEDIA_STORAGE_EXTERNAL:
                raise ValueError("Only external media references can be promoted")
            if not is_supported_media_name(current.category, name):
                raise ValueError(
                    f"Unsupported media type for {current.category}: {name}"
                )

            collisions = conn.execute(
                """
                SELECT id, managed_name
                FROM media_assets
                WHERE category=? AND storage_mode=? AND id<>?
                """,
                (
                    current.category,
                    MEDIA_STORAGE_MANAGED,
                    int(asset_id),
                ),
            ).fetchall()
            for collision in collisions:
                if str(collision["managed_name"] or "").casefold() == name.casefold():
                    raise ValueError("Managed media with this filename already exists")

            conn.execute(
                """
                UPDATE media_assets
                SET storage_mode=?, managed_name=?, external_path=?,
                    original_name=?, updated_at=?
                WHERE id=? AND storage_mode=?
                """,
                (
                    MEDIA_STORAGE_MANAGED,
                    name,
                    "",
                    str(original_name or name),
                    utc_now(),
                    int(asset_id),
                    MEDIA_STORAGE_EXTERNAL,
                ),
            )
            row = conn.execute(
                "SELECT * FROM media_assets WHERE id=?",
                (int(asset_id),),
            ).fetchone()
        assert row is not None
        return self._media_asset_from_row(row)

    def ensure_managed_media_asset(
        self,
        category: str,
        managed_name: str,
        original_name: str | None = None,
    ) -> MediaAsset:
        name = Path(str(managed_name)).name
        if not name or name != str(managed_name):
            raise ValueError("Managed media must be one filename")
        if not is_supported_media_name(category, name):
            raise ValueError(f"Unsupported media type for {category}: {name}")

        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM media_assets WHERE category=? AND storage_mode=?",
                (str(category), MEDIA_STORAGE_MANAGED),
            ).fetchall()
            for row in rows:
                if str(row["managed_name"] or "").casefold() == name.casefold():
                    return self._media_asset_from_row(row)

            now = utc_now()
            cursor = conn.execute(
                """
                INSERT INTO media_assets(
                    category,storage_mode,managed_name,external_path,
                    original_name,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    str(category),
                    MEDIA_STORAGE_MANAGED,
                    name,
                    "",
                    str(original_name or name),
                    now,
                    now,
                ),
            )
            row = conn.execute(
                "SELECT * FROM media_assets WHERE id=?",
                (int(cursor.lastrowid),),
            ).fetchone()
        assert row is not None
        return self._media_asset_from_row(row)

    def register_external_media_asset(
        self,
        category: str,
        external_path: str | Path,
    ) -> MediaAsset:
        path = Path(external_path).expanduser().resolve(strict=False)
        if not is_supported_media_name(category, path.name):
            raise ValueError(f"Unsupported media type for {category}: {path.name}")
        normalized = str(path)

        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM media_assets WHERE category=? AND storage_mode=?",
                (str(category), MEDIA_STORAGE_EXTERNAL),
            ).fetchall()
            for row in rows:
                if str(row["external_path"] or "").casefold() == normalized.casefold():
                    return self._media_asset_from_row(row)

            now = utc_now()
            cursor = conn.execute(
                """
                INSERT INTO media_assets(
                    category,storage_mode,managed_name,external_path,
                    original_name,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    str(category),
                    MEDIA_STORAGE_EXTERNAL,
                    "",
                    normalized,
                    path.name,
                    now,
                    now,
                ),
            )
            row = conn.execute(
                "SELECT * FROM media_assets WHERE id=?",
                (int(cursor.lastrowid),),
            ).fetchone()
        assert row is not None
        return self._media_asset_from_row(row)

    def update_external_media_asset(
        self,
        asset_id: int,
        external_path: str | Path,
    ) -> MediaAsset:
        current = self.get_media_asset(asset_id)
        if current is None:
            raise ValueError("Media asset not found")
        if current.storage_mode != MEDIA_STORAGE_EXTERNAL:
            raise ValueError("Only external media references can be repaired")

        path = Path(external_path).expanduser().resolve(strict=False)
        if not is_supported_media_name(current.category, path.name):
            raise ValueError(
                f"Unsupported media type for {current.category}: {path.name}"
            )
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE media_assets
                SET external_path=?, original_name=?, updated_at=?
                WHERE id=? AND storage_mode=?
                """,
                (
                    str(path),
                    path.name,
                    utc_now(),
                    int(asset_id),
                    MEDIA_STORAGE_EXTERNAL,
                ),
            )
            row = conn.execute(
                "SELECT * FROM media_assets WHERE id=?",
                (int(asset_id),),
            ).fetchone()
        assert row is not None
        return self._media_asset_from_row(row)

    def migrate_legacy_wheel_jingles(self) -> dict[str, int]:
        """Adopt the pre-D26 wheel soundtrack library into data/soundtrack.

        In 1.0.6 managed wheel audio lived in data/wheel_jingles and media
        rows used category=wheel_jingles. D26 deliberately unified wheel and
        auction soundtracks under data/soundtrack, but old installations and
        old full backups can still carry the legacy directory/category.

        The migration is idempotent, preserves media IDs whenever possible,
        re-points the selected wheel soundtrack when an equivalent soundtrack
        row already exists, never overwrites a different file, and removes the
        legacy directory only after it is empty.
        """
        legacy_dir = self.path.parent / LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES
        soundtrack_dir = managed_media_directory(
            self.path.parent, MEDIA_CATEGORY_SOUNDTRACK
        )
        soundtrack_dir.mkdir(parents=True, exist_ok=True)

        selected_raw = str(
            self.get_setting(WHEEL_SOUNDTRACK_MEDIA_ID_KEY, "") or ""
        ).strip()
        selected_id = int(selected_raw) if selected_raw.isdigit() else None

        migrated_rows = 0
        moved_files = 0
        merged_rows = 0
        selected_repointed = 0

        def unique_target(source: Path) -> Path:
            candidate = soundtrack_dir / source.name
            if not candidate.exists():
                return candidate
            try:
                if filecmp.cmp(source, candidate, shallow=False):
                    return candidate
            except OSError:
                pass
            counter = 2
            while True:
                candidate = soundtrack_dir / (
                    f"{source.stem} (legacy wheel {counter}){source.suffix}"
                )
                if not candidate.exists():
                    return candidate
                try:
                    if filecmp.cmp(source, candidate, shallow=False):
                        return candidate
                except OSError:
                    pass
                counter += 1

        with self.connect() as conn:
            legacy_rows = conn.execute(
                "SELECT * FROM media_assets WHERE category=? ORDER BY id ASC",
                (LEGACY_MEDIA_CATEGORY_WHEEL_JINGLES,),
            ).fetchall()

            for row in legacy_rows:
                asset = self._media_asset_from_row(row)
                final_name = asset.managed_name
                duplicate_id: int | None = None

                if asset.storage_mode == MEDIA_STORAGE_MANAGED:
                    name = Path(asset.managed_name).name
                    source = legacy_dir / name
                    target = soundtrack_dir / name

                    if source.is_file():
                        target = unique_target(source)
                        if target.exists():
                            try:
                                same_file = filecmp.cmp(source, target, shallow=False)
                            except OSError:
                                same_file = False
                            if same_file:
                                source.unlink(missing_ok=True)
                            else:
                                raise RuntimeError(
                                    f"Legacy soundtrack collision was not resolved: {source}"
                                )
                        else:
                            shutil.move(str(source), str(target))
                            moved_files += 1
                        final_name = target.name
                    elif target.is_file():
                        final_name = target.name
                    else:
                        # The legacy DB row no longer has a physical managed
                        # file. It is stale and cannot be migrated usefully.
                        if selected_id == asset.id:
                            selected_id = None
                            selected_repointed += 1
                        conn.execute("DELETE FROM media_assets WHERE id=?", (asset.id,))
                        migrated_rows += 1
                        continue

                    candidates = conn.execute(
                        """
                        SELECT id FROM media_assets
                        WHERE category=? AND storage_mode=? AND id<>?
                        """,
                        (
                            MEDIA_CATEGORY_SOUNDTRACK,
                            MEDIA_STORAGE_MANAGED,
                            asset.id,
                        ),
                    ).fetchall()
                    for candidate in candidates:
                        candidate_asset = self._get_media_asset_conn(
                            conn, int(candidate["id"])
                        )
                        if (
                            candidate_asset is not None
                            and candidate_asset.managed_name.casefold()
                            == final_name.casefold()
                        ):
                            duplicate_id = candidate_asset.id
                            break
                else:
                    candidates = conn.execute(
                        """
                        SELECT id, external_path FROM media_assets
                        WHERE category=? AND storage_mode=? AND id<>?
                        """,
                        (
                            MEDIA_CATEGORY_SOUNDTRACK,
                            MEDIA_STORAGE_EXTERNAL,
                            asset.id,
                        ),
                    ).fetchall()
                    for candidate in candidates:
                        if (
                            str(candidate["external_path"] or "").casefold()
                            == asset.external_path.casefold()
                        ):
                            duplicate_id = int(candidate["id"])
                            break

                if duplicate_id is not None:
                    if selected_id == asset.id:
                        selected_id = duplicate_id
                        selected_repointed += 1
                    conn.execute("DELETE FROM media_assets WHERE id=?", (asset.id,))
                    merged_rows += 1
                    migrated_rows += 1
                    continue

                conn.execute(
                    """
                    UPDATE media_assets
                    SET category=?, managed_name=?, updated_at=?
                    WHERE id=?
                    """,
                    (
                        MEDIA_CATEGORY_SOUNDTRACK,
                        final_name if asset.storage_mode == MEDIA_STORAGE_MANAGED else "",
                        utc_now(),
                        asset.id,
                    ),
                )
                migrated_rows += 1

            # Preserve manually copied legacy audio that never had a DB row.
            if legacy_dir.is_dir():
                allowed = supported_media_extensions(MEDIA_CATEGORY_SOUNDTRACK)
                for source in sorted(
                    legacy_dir.iterdir(), key=lambda item: item.name.casefold()
                ):
                    if not source.is_file() or source.suffix.lower() not in allowed:
                        continue
                    target = unique_target(source)
                    if target.exists():
                        try:
                            same_file = filecmp.cmp(source, target, shallow=False)
                        except OSError:
                            same_file = False
                        if same_file:
                            source.unlink(missing_ok=True)
                        else:
                            continue
                    else:
                        shutil.move(str(source), str(target))
                        moved_files += 1

                    existing = conn.execute(
                        """
                        SELECT id, managed_name FROM media_assets
                        WHERE category=? AND storage_mode=?
                        """,
                        (MEDIA_CATEGORY_SOUNDTRACK, MEDIA_STORAGE_MANAGED),
                    ).fetchall()
                    if not any(
                        str(item["managed_name"] or "").casefold()
                        == target.name.casefold()
                        for item in existing
                    ):
                        now = utc_now()
                        conn.execute(
                            """
                            INSERT INTO media_assets(
                                category,storage_mode,managed_name,external_path,
                                original_name,created_at,updated_at
                            ) VALUES(?,?,?,?,?,?,?)
                            """,
                            (
                                MEDIA_CATEGORY_SOUNDTRACK,
                                MEDIA_STORAGE_MANAGED,
                                target.name,
                                "",
                                target.name,
                                now,
                                now,
                            ),
                        )

            desired_setting = str(selected_id) if selected_id is not None else ""
            if desired_setting != selected_raw:
                conn.execute(
                    "INSERT INTO settings(key,value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (WHEEL_SOUNDTRACK_MEDIA_ID_KEY, desired_setting),
                )
                if hasattr(self, "_log_conn"):
                    self._log_conn(
                        conn,
                        "setting",
                        None,
                        "legacy_wheel_soundtrack_migration",
                        {"key": WHEEL_SOUNDTRACK_MEDIA_ID_KEY, "value": selected_raw},
                        {"key": WHEEL_SOUNDTRACK_MEDIA_ID_KEY, "value": desired_setting},
                    )

        if legacy_dir.is_dir():
            try:
                legacy_dir.rmdir()
            except OSError:
                # Unsupported/user files are never deleted implicitly.
                pass

        return {
            "migrated_rows": migrated_rows,
            "moved_files": moved_files,
            "merged_rows": merged_rows,
            "selected_repointed": selected_repointed,
        }

    def sync_managed_media_category(self, category: str) -> list[MediaAsset]:
        """Mirror one managed category to the files physically present on disk.

        D26 makes the managed directory the source of truth: supported files
        copied in manually appear on refresh, while missing managed files no
        longer survive as dead library rows. External references remain
        registered but callers decide whether an unavailable path should be
        exposed in their UI.

        One sync deliberately uses one SQLite transaction. The former
        per-file ensure loop reopened SQLite and rescanned the same category
        for every file, which made large music libraries progressively more
        expensive without changing semantics.
        """
        directory = managed_media_directory(self.path.parent, category)
        directory.mkdir(parents=True, exist_ok=True)
        allowed = supported_media_extensions(category)
        present_paths = [
            path
            for path in sorted(directory.iterdir(), key=lambda item: item.name.casefold())
            if path.is_file() and path.suffix.lower() in allowed
        ]
        present_names = {path.name.casefold() for path in present_paths}

        with self.connect() as conn:
            managed_rows = conn.execute(
                "SELECT * FROM media_assets "
                "WHERE category=? AND storage_mode=? ORDER BY id ASC",
                (str(category), MEDIA_STORAGE_MANAGED),
            ).fetchall()
            managed_names = {
                str(row["managed_name"] or "").casefold()
                for row in managed_rows
            }

            for path in present_paths:
                key = path.name.casefold()
                if key in managed_names:
                    continue
                now = utc_now()
                conn.execute(
                    """
                    INSERT INTO media_assets(
                        category,storage_mode,managed_name,external_path,
                        original_name,created_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?)
                    """,
                    (
                        str(category),
                        MEDIA_STORAGE_MANAGED,
                        path.name,
                        "",
                        path.name,
                        now,
                        now,
                    ),
                )
                managed_names.add(key)

            # D26 changes source-of-truth semantics only for its audio
            # libraries. Existing overlay/background/center-image categories
            # keep their established missing-file recovery behavior.
            if str(category) in {MEDIA_CATEGORY_MUSIC, MEDIA_CATEGORY_SOUNDTRACK}:
                stale_ids = [
                    int(row["id"])
                    for row in managed_rows
                    if str(row["managed_name"] or "").casefold()
                    not in present_names
                ]
                if stale_ids:
                    placeholders = ",".join("?" for _ in stale_ids)
                    conn.execute(
                        f"DELETE FROM media_assets WHERE id IN ({placeholders})",
                        tuple(stale_ids),
                    )

            rows = conn.execute(
                "SELECT * FROM media_assets WHERE category=? ORDER BY id ASC",
                (str(category),),
            ).fetchall()

        assets = [self._media_asset_from_row(row) for row in rows]
        return sorted(assets, key=lambda item: (item.display_name.casefold(), item.id))
