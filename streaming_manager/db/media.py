from __future__ import annotations

from pathlib import Path

from ..media import (
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

    def sync_managed_media_category(self, category: str) -> list[MediaAsset]:
        """Mirror one managed category to the files physically present on disk.

        D26 makes the managed directory the source of truth: supported files
        copied in manually appear on refresh, while missing managed files no
        longer survive as dead library rows. External references remain
        registered but callers decide whether an unavailable path should be
        exposed in their UI.
        """
        directory = managed_media_directory(self.path.parent, category)
        directory.mkdir(parents=True, exist_ok=True)
        allowed = supported_media_extensions(category)
        present: dict[str, Path] = {}
        for path in sorted(directory.iterdir(), key=lambda item: item.name.casefold()):
            if path.is_file() and path.suffix.lower() in allowed:
                present[path.name.casefold()] = path
                self.ensure_managed_media_asset(category, path.name, path.name)

        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, managed_name FROM media_assets "
                "WHERE category=? AND storage_mode=?",
                (str(category), MEDIA_STORAGE_MANAGED),
            ).fetchall()
            stale_ids = [
                int(row["id"])
                for row in rows
                if str(row["managed_name"] or "").casefold() not in present
            ]
            if stale_ids:
                placeholders = ",".join("?" for _ in stale_ids)
                conn.execute(
                    f"DELETE FROM media_assets WHERE id IN ({placeholders})",
                    tuple(stale_ids),
                )
        return self.list_media_assets(category)
