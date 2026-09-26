from __future__ import annotations
from ..diagnostic_logs import sanitize_diagnostic_text

import json
import sqlite3
from typing import Any

from ..integrations import INTEGRATION_STATUSES, STATUS_NOT_CONFIGURED
from .common import utc_now


_SECRET_KEY_FRAGMENTS = (
    "token",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
)


def _assert_non_secret_provider_config(value: Any, path: str = "provider_config") -> None:
    """Reject secret-looking values from SQLite provider config recursively."""
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().casefold().replace("-", "_")
            if any(fragment in normalized for fragment in _SECRET_KEY_FRAGMENTS):
                raise ValueError(
                    f"Секретное поле {path}.{key} нельзя хранить в SQLite; используйте CredentialStore."
                )
            _assert_non_secret_provider_config(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_non_secret_provider_config(item, f"{path}[{index}]")


class IntegrationsMixin:
    RANDOM_ORG_CREDENTIAL_REF_KEY = "random_org_credential_ref"

    @staticmethod
    def _normalize_integration_status(status: str) -> str:
        normalized = str(status or STATUS_NOT_CONFIGURED)
        if normalized not in INTEGRATION_STATUSES:
            raise ValueError(f"Некорректный integration status: {normalized}")
        return normalized

    def list_integration_connections(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM integration_connections ORDER BY service_key"
            ).fetchall()
        return [self._integration_row_to_dict(row) for row in rows]

    def get_integration_connection(self, service_key: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM integration_connections WHERE service_key=?",
                (str(service_key),),
            ).fetchone()
        return self._integration_row_to_dict(row) if row is not None else None

    @staticmethod
    def _integration_row_to_dict(row: sqlite3.Row) -> dict:
        try:
            provider_config = json.loads(str(row["provider_config_json"] or "{}"))
        except (TypeError, ValueError, json.JSONDecodeError):
            provider_config = {}
        if not isinstance(provider_config, dict):
            provider_config = {}
        return {
            "service_key": str(row["service_key"]),
            "enabled": bool(row["enabled"]),
            "status": str(row["status"]),
            "credential_ref": str(row["credential_ref"] or ""),
            "provider_config": provider_config,
            "last_check_at": row["last_check_at"],
            "last_error": str(row["last_error"] or ""),
            "last_event_at": row["last_event_at"],
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def upsert_integration_connection(
        self,
        service_key: str,
        *,
        enabled: bool | None = None,
        status: str | None = None,
        credential_ref: str | None = None,
        provider_config: dict | None = None,
        last_check_at: str | None = None,
        last_error: str | None = None,
        last_event_at: str | None = None,
    ) -> dict:
        key = str(service_key).strip()
        if not key:
            raise ValueError("service_key не задан.")
        existing = self.get_integration_connection(key)
        now = utc_now()
        final_enabled = bool(existing["enabled"]) if existing is not None else True
        if enabled is not None:
            final_enabled = bool(enabled)
        final_status = self._normalize_integration_status(
            status if status is not None else (
                existing["status"] if existing is not None else STATUS_NOT_CONFIGURED
            )
        )
        final_ref = (
            str(credential_ref)
            if credential_ref is not None
            else str(existing["credential_ref"] if existing is not None else "")
        )
        if final_ref and not final_ref.startswith("cred_"):
            raise ValueError("credential_ref должен быть opaque CredentialStore reference.")
        final_config = (
            dict(provider_config)
            if provider_config is not None
            else dict(existing["provider_config"] if existing is not None else {})
        )
        _assert_non_secret_provider_config(final_config)
        final_check = last_check_at if last_check_at is not None else (
            existing["last_check_at"] if existing is not None else None
        )
        final_error = sanitize_diagnostic_text(
            str(last_error) if last_error is not None else (
                str(existing["last_error"]) if existing is not None else ""
            )
        )
        final_event = last_event_at if last_event_at is not None else (
            existing["last_event_at"] if existing is not None else None
        )
        created_at = str(existing["created_at"] if existing is not None else now)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO integration_connections(
                    service_key,enabled,status,credential_ref,provider_config_json,
                    last_check_at,last_error,last_event_at,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(service_key) DO UPDATE SET
                    enabled=excluded.enabled,
                    status=excluded.status,
                    credential_ref=excluded.credential_ref,
                    provider_config_json=excluded.provider_config_json,
                    last_check_at=excluded.last_check_at,
                    last_error=excluded.last_error,
                    last_event_at=excluded.last_event_at,
                    updated_at=excluded.updated_at
                """,
                (
                    key,
                    1 if final_enabled else 0,
                    final_status,
                    final_ref,
                    json.dumps(final_config, ensure_ascii=False, sort_keys=True),
                    final_check,
                    final_error,
                    final_event,
                    created_at,
                    now,
                ),
            )
        return self.get_integration_connection(key) or {}

    def delete_integration_connection(self, service_key: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM integration_connections WHERE service_key=?",
                (str(service_key),),
            )

    def get_random_org_api_key(self) -> str:
        ref = self.get_setting(self.RANDOM_ORG_CREDENTIAL_REF_KEY, "").strip()
        if not ref:
            return ""
        try:
            return str(self.credential_store.get(ref) or "")
        except Exception:
            return ""

    def has_random_org_api_key(self) -> bool:
        return bool(self.get_random_org_api_key().strip())

    def set_random_org_api_key(self, api_key: str) -> None:
        secret = str(api_key).strip()
        ref = self.get_setting(self.RANDOM_ORG_CREDENTIAL_REF_KEY, "").strip()
        if not secret:
            if ref:
                self.credential_store.delete(ref)
            self.set_setting(self.RANDOM_ORG_CREDENTIAL_REF_KEY, "")
            return
        new_ref = self.credential_store.put(secret, credential_ref=ref or None)
        self.set_setting(self.RANDOM_ORG_CREDENTIAL_REF_KEY, new_ref)


__all__ = ["IntegrationsMixin", "_assert_non_secret_provider_config"]
