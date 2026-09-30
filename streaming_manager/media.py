from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


MEDIA_STORAGE_MANAGED = "managed"
MEDIA_STORAGE_EXTERNAL = "external"

MEDIA_CATEGORY_OVERLAY_BACKGROUNDS = "overlay_backgrounds"
MEDIA_CATEGORY_MUSIC = "music"
MEDIA_CATEGORY_WHEEL_JINGLES = "wheel_jingles"
MEDIA_CATEGORY_SOUNDTRACK = "soundtrack"
MEDIA_CATEGORY_WHEEL_CENTER_ICONS = "wheel_center_icons"

# One shared media contract, but every functional purpose has its own physical
# managed directory.  This intentionally preserves the historical
# data/overlay_backgrounds location while reserving dedicated folders for the
# next approved media features.
MANAGED_MEDIA_FOLDERS: dict[str, str] = {
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS: "overlay_backgrounds",
    MEDIA_CATEGORY_MUSIC: "music",
    MEDIA_CATEGORY_WHEEL_JINGLES: "wheel_jingles",
    MEDIA_CATEGORY_SOUNDTRACK: "soundtrack",
    MEDIA_CATEGORY_WHEEL_CENTER_ICONS: "wheel_center_icons",
}

MEDIA_CATEGORY_EXTENSIONS: dict[str, frozenset[str]] = {
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS: frozenset(
        {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm"}
    ),
    MEDIA_CATEGORY_MUSIC: frozenset({".mp3", ".wav", ".ogg"}),
    MEDIA_CATEGORY_WHEEL_JINGLES: frozenset({".mp3", ".wav", ".ogg"}),
    MEDIA_CATEGORY_SOUNDTRACK: frozenset({".mp3", ".wav", ".ogg"}),
    MEDIA_CATEGORY_WHEEL_CENTER_ICONS: frozenset(
        {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    ),
}

IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})
VIDEO_EXTENSIONS = frozenset({".mp4", ".webm"})
AUDIO_EXTENSIONS = frozenset({".mp3", ".wav", ".ogg"})


@dataclass(frozen=True)
class MediaAsset:
    id: int
    category: str
    storage_mode: str
    managed_name: str
    external_path: str
    original_name: str
    created_at: str
    updated_at: str

    @property
    def display_name(self) -> str:
        return self.original_name or self.managed_name or Path(self.external_path).name


def managed_media_directory(data_root: str | Path, category: str) -> Path:
    try:
        folder = MANAGED_MEDIA_FOLDERS[category]
    except KeyError as exc:
        raise ValueError(f"Unknown media category: {category}") from exc
    return Path(data_root) / folder


def ensure_managed_media_directories(data_root: str | Path) -> None:
    for category in MANAGED_MEDIA_FOLDERS:
        managed_media_directory(data_root, category).mkdir(parents=True, exist_ok=True)


def supported_media_extensions(category: str) -> frozenset[str]:
    try:
        return MEDIA_CATEGORY_EXTENSIONS[category]
    except KeyError as exc:
        raise ValueError(f"Unknown media category: {category}") from exc


def is_supported_media_name(category: str, name: str) -> bool:
    return Path(name).suffix.lower() in supported_media_extensions(category)


def media_kind_for_name(name: str) -> str:
    suffix = Path(name).suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in AUDIO_EXTENSIONS:
        return "audio"
    return ""


def resolve_media_asset_path(data_root: str | Path, asset: MediaAsset) -> Path:
    """Resolve a registered asset without turning HTTP input into a file path.

    Managed assets are constrained to one basename inside the category folder;
    external assets resolve only to the exact path previously registered in
    SQLite.  Browser Source therefore never supplies an arbitrary filesystem
    path to the local server.
    """
    if asset.storage_mode == MEDIA_STORAGE_MANAGED:
        if not asset.managed_name or Path(asset.managed_name).name != asset.managed_name:
            raise ValueError("Invalid managed media name")
        directory = managed_media_directory(data_root, asset.category)
        candidate = directory / asset.managed_name
        # Reject managed symlinks/path tricks that resolve outside the dedicated
        # category directory.
        resolved_directory = directory.resolve(strict=False)
        resolved_candidate = candidate.resolve(strict=False)
        if resolved_candidate.parent != resolved_directory:
            raise ValueError("Managed media escaped its category directory")
        return candidate

    if asset.storage_mode == MEDIA_STORAGE_EXTERNAL:
        if not asset.external_path:
            raise ValueError("External media path is empty")
        return Path(asset.external_path).expanduser()

    raise ValueError(f"Unknown media storage mode: {asset.storage_mode}")


def media_asset_available(data_root: str | Path, asset: MediaAsset) -> bool:
    try:
        path = resolve_media_asset_path(data_root, asset)
    except (OSError, ValueError):
        return False
    return path.is_file() and is_supported_media_name(asset.category, path.name)
