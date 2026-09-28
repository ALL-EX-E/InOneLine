from __future__ import annotations

import hashlib
from pathlib import Path

from .media import MEDIA_CATEGORY_WHEEL_CENTER_ICONS, managed_media_directory
from .remote_image import download_external_image, load_local_image


_ALLOWED_EXTENSIONS = frozenset({".png", ".gif", ".webp"})


def prepare_local_center_image(path: str) -> dict:
    prepared = load_local_image(path)
    return {
        "data": prepared.image_bytes,
        "extension": prepared.extension,
        "animated": prepared.animated,
        "label": Path(path).name,
        "source": str(path),
    }


def prepare_remote_center_image(
    source: str,
    *,
    twitch_profile_resolver=None,
) -> dict:
    result = download_external_image(
        source,
        twitch_profile_resolver=twitch_profile_resolver,
    )
    return {
        "data": result.image_bytes,
        "extension": result.extension,
        "animated": result.animated,
        "label": result.display_name,
        "source": result.resolved_url,
    }


def store_prepared_center_image(db, prepared: dict):
    data = bytes(prepared.get("data") or b"")
    if not data:
        raise ValueError("Подготовленное изображение пустое.")
    extension = str(prepared.get("extension") or ".png").strip().lower()
    if extension not in _ALLOWED_EXTENSIONS:
        raise ValueError("Получен неподдерживаемый формат изображения.")

    media_dir = managed_media_directory(
        db.path.parent, MEDIA_CATEGORY_WHEEL_CENTER_ICONS
    )
    media_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()[:16]
    name = f"wheel-center-{digest}{extension}"
    target = media_dir / name
    if not target.exists():
        temporary = target.with_name(target.name + ".tmp")
        try:
            temporary.write_bytes(data)
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    label = str(prepared.get("label") or name).strip() or name
    return db.ensure_managed_media_asset(
        MEDIA_CATEGORY_WHEEL_CENTER_ICONS,
        name,
        label,
    )
