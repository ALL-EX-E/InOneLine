from __future__ import annotations

from pathlib import Path

from .db.auction import AuctionMixin
from .db.common import (
    DuplicateGameError,
    Game,
    points_from_text,
    display_date,
    display_datetime_local,
    format_points,
    normalize_date_text,
    normalize_text_key,
    normalize_title_key,
    parse_date,
    utc_now,
)
from .db.games import GamesMixin
from .db.media import MediaMixin
from .db.integrations import IntegrationsMixin
from .db.schema import SchemaMixin
from .media import ensure_managed_media_directories
from .credentials import CredentialStore, create_credential_store
from .db.services import ServicesMixin
from .db.rules import RulesMixin


class Database(SchemaMixin, GamesMixin, AuctionMixin, MediaMixin, IntegrationsMixin, ServicesMixin, RulesMixin):
    """Единый фасад локальной SQLite-базы.

    Реализация разделена по предметным областям, но внешний API класса сохранён,
    поэтому UI и плагины продолжают использовать ``Database`` как раньше.
    """

    def __init__(self, path: str | Path, credential_store: CredentialStore | None = None):
        self.path = Path(path)
        self.credential_store = credential_store or create_credential_store(self.path.parent)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        ensure_managed_media_directories(self.path.parent)
        self._configure_database()
        self._init_schema()


__all__ = [
    "Database", "DuplicateGameError", "Game", "points_from_text",
    "display_date", "display_datetime_local", "format_points",
    "normalize_date_text", "normalize_text_key", "normalize_title_key",
    "parse_date", "utc_now",
]
