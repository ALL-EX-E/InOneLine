from __future__ import annotations

"""B1 common integration adapter/status contract.

No real provider adapter is registered in B1.  B2+ adapters plug into this
registry and automatically inherit persistence, status handling, protected
credential storage and common UI actions.
"""

import time
from dataclasses import dataclass, field
from threading import Lock, RLock
from typing import Callable, Iterable

from .conversion import ConversionUnit
from .db.common import utc_now
from .diagnostic_logs import sanitize_diagnostic_text

STATUS_NOT_CONFIGURED = "not_configured"
STATUS_REQUIRES_LOGIN = "requires_login"
STATUS_CONNECTED = "connected"
STATUS_ERROR = "error"
INTEGRATION_STATUSES = frozenset(
    {STATUS_NOT_CONFIGURED, STATUS_REQUIRES_LOGIN, STATUS_CONNECTED, STATUS_ERROR}
)
STATUS_LABELS = {
    STATUS_NOT_CONFIGURED: "Не настроено",
    STATUS_REQUIRES_LOGIN: "Требует входа",
    STATUS_CONNECTED: "Подключено",
    STATUS_ERROR: "Ошибка",
}


class IntegrationError(RuntimeError):
    pass


class IntegrationAuthRequired(IntegrationError):
    """Authentication is missing, expired, revoked or invalid."""


class IntegrationTemporaryError(IntegrationError):
    """Retryable temporary network/provider failure."""


@dataclass(frozen=True)
class IntegrationOperationResult:
    status: str = STATUS_CONNECTED
    message: str = ""
    provider_config: dict | None = None
    credential: str | None = None

    def __post_init__(self):
        if self.status not in INTEGRATION_STATUSES:
            raise ValueError(f"Unsupported integration status: {self.status}")


@dataclass(frozen=True)
class NormalizedIntegrationEvent:
    """Provider-neutral B3 event accepted from a provider-specific adapter.

    Adapters own provider payload parsing, permissions and matching.  B3 receives
    only this normalized form and never performs fuzzy/AI title matching.
    """

    service_key: str
    external_event_id: str
    event_type: str
    source_amount: object
    source_unit: str
    contributor: str = ""
    game_id: int | None = None
    lot_title: str = ""
    source_unit_label: str = ""
    unit_kind: str = ""
    note: str = ""
    provider_metadata: dict = field(default_factory=dict)
    # Optional source-time auction context.  B4 Twitch uses redeemed_at to
    # distinguish a redemption made during one specific running auction from
    # a redemption made outside an auction.  This prevents delayed provider
    # delivery from being applied to a newer auction that happens to be running
    # when the event finally reaches the desktop app.
    auction_id_hint: int | None = None
    force_outside_auction: bool = False


class IntegrationAdapter:
    """Base contract for B2+ service adapters."""

    service_key: str = ""
    display_name: str = ""
    capabilities: frozenset[str] = frozenset()
    accepted_event_types: frozenset[str] = frozenset()

    def accepts_event_type(self, event_type: str) -> bool:
        return str(event_type or "").strip() in self.accepted_event_types

    def connect(self, context: "IntegrationContext") -> IntegrationOperationResult:
        raise NotImplementedError

    def check_connection(self, context: "IntegrationContext") -> IntegrationOperationResult:
        raise NotImplementedError

    def reconnect(self, context: "IntegrationContext") -> IntegrationOperationResult:
        return self.connect(context)

    def disconnect(self, context: "IntegrationContext") -> None:
        """Optional provider-side disconnect; local credentials remain intact."""

    def conversion_units(self) -> list[ConversionUnit]:
        return []

    def view_details(self, provider_config: dict) -> tuple[str, ...]:
        """Optional non-secret provider details shown on the integration card."""
        return ()


@dataclass(frozen=True)
class IntegrationContext:
    service_key: str
    credential: str | None
    provider_config: dict
    save_credential: Callable[[str], str] | None = None


@dataclass(frozen=True)
class IntegrationView:
    service_key: str
    display_name: str
    capabilities: tuple[str, ...]
    enabled: bool
    status: str
    status_label: str
    message: str
    details: tuple[str, ...]
    last_check_at: str | None
    last_event_at: str | None


class IntegrationRegistry:
    def __init__(self):
        self._adapters: dict[str, IntegrationAdapter] = {}

    @staticmethod
    def _validate_adapter(adapter: IntegrationAdapter) -> tuple[str, str]:
        key = str(getattr(adapter, "service_key", "") or "").strip()
        name = str(getattr(adapter, "display_name", "") or "").strip()
        if not key or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for ch in key):
            raise ValueError("service_key должен быть стабильным lowercase идентификатором.")
        if not name:
            raise ValueError("display_name адаптера не задан.")
        return key, name

    def register(self, adapter: IntegrationAdapter) -> None:
        key, _name = self._validate_adapter(adapter)
        if key in self._adapters:
            raise ValueError(f"Adapter already registered: {key}")
        self._adapters[key] = adapter

    def get(self, service_key: str) -> IntegrationAdapter | None:
        return self._adapters.get(str(service_key))

    def adapters(self) -> tuple[IntegrationAdapter, ...]:
        return tuple(self._adapters[key] for key in sorted(self._adapters))


class IntegrationManager:
    """Common orchestration for adapter lifecycle and persisted status."""

    def __init__(
        self,
        db,
        registry: IntegrationRegistry | None = None,
        *,
        retry_delays: Iterable[float] = (0.5, 1.5),
        sleeper: Callable[[float], None] = time.sleep,
    ):
        self.db = db
        self.registry = registry or IntegrationRegistry()
        self.retry_delays = tuple(max(0.0, float(delay)) for delay in retry_delays)
        self.sleeper = sleeper
        self._operation_locks: dict[str, RLock] = {}
        self._operation_locks_guard = Lock()

    def _adapter(self, service_key: str) -> IntegrationAdapter:
        adapter = self.registry.get(service_key)
        if adapter is None:
            raise KeyError(f"Unsupported integration adapter: {service_key}")
        return adapter

    def _operation_lock(self, service_key: str) -> RLock:
        key = str(service_key)
        with self._operation_locks_guard:
            return self._operation_locks.setdefault(key, RLock())

    def _save_credential_immediately(self, service_key: str, secret: str) -> str:
        """Atomically rotate a provider credential before later network work.

        Public OAuth refresh tokens may be one-time-use.  Adapters can call this
        from inside an operation immediately after a successful refresh/exchange
        so a later provider failure cannot strand the application with the old
        already-consumed refresh token.
        """
        current = self.db.get_integration_connection(service_key) or {}
        ref = str(current.get("credential_ref") or "")
        new_ref = self.db.credential_store.put(str(secret), credential_ref=ref or None)
        self.db.upsert_integration_connection(service_key, credential_ref=new_ref)
        return new_ref

    def _context(self, service_key: str) -> IntegrationContext:
        row = self.db.get_integration_connection(service_key) or {}
        ref = str(row.get("credential_ref") or "")
        credential = self.db.credential_store.get(ref) if ref else None
        return IntegrationContext(
            service_key=str(service_key),
            credential=credential,
            provider_config=dict(row.get("provider_config") or {}),
            save_credential=lambda secret: self._save_credential_immediately(service_key, secret),
        )

    def _persist_result(
        self,
        service_key: str,
        result: IntegrationOperationResult,
        *,
        enabled: bool = True,
    ) -> dict:
        current = self.db.get_integration_connection(service_key) or {}
        credential_ref = str(current.get("credential_ref") or "")
        if result.credential is not None:
            credential_ref = self.db.credential_store.put(
                result.credential,
                credential_ref=credential_ref or None,
            )
        return self.db.upsert_integration_connection(
            service_key,
            enabled=enabled,
            status=result.status,
            credential_ref=credential_ref,
            provider_config=(
                result.provider_config
                if result.provider_config is not None
                else dict(current.get("provider_config") or {})
            ),
            last_check_at=utc_now(),
            last_error=(
                sanitize_diagnostic_text(result.message)
                if result.status == STATUS_ERROR else ""
            ),
        )

    def _run_adapter_operation(self, service_key: str, method_name: str) -> dict:
        # Serialize operations per service.  Besides avoiding duplicate connect/check
        # races, this guarantees that OAuth refresh-token rotation occurs in one
        # worker at a time, as required by providers such as Twitch.
        with self._operation_lock(service_key):
            adapter = self._adapter(service_key)
            attempts = len(self.retry_delays) + 1
            last_error = ""
            for attempt in range(attempts):
                try:
                    method = getattr(adapter, method_name)
                    result = method(self._context(service_key))
                    if not isinstance(result, IntegrationOperationResult):
                        raise IntegrationError("Adapter returned an invalid operation result.")
                    return self._persist_result(service_key, result, enabled=True)
                except IntegrationAuthRequired as exc:
                    return self.db.upsert_integration_connection(
                        service_key,
                        enabled=True,
                        status=STATUS_REQUIRES_LOGIN,
                        last_check_at=utc_now(),
                        last_error=sanitize_diagnostic_text(str(exc)),
                    )
                except IntegrationTemporaryError as exc:
                    last_error = sanitize_diagnostic_text(str(exc))
                    if attempt < len(self.retry_delays):
                        self.sleeper(self.retry_delays[attempt])
                        continue
                    break
                except Exception as exc:
                    last_error = sanitize_diagnostic_text(str(exc) or type(exc).__name__)
                    break
            return self.db.upsert_integration_connection(
                service_key,
                enabled=True,
                status=STATUS_ERROR,
                last_check_at=utc_now(),
                last_error=last_error,
            )

    def connect(self, service_key: str) -> dict:
        return self._run_adapter_operation(service_key, "connect")

    def check_connection(self, service_key: str) -> dict:
        return self._run_adapter_operation(service_key, "check_connection")

    def reconnect(self, service_key: str) -> dict:
        return self._run_adapter_operation(service_key, "reconnect")

    def disconnect(self, service_key: str) -> dict:
        with self._operation_lock(service_key):
            return self._disconnect_locked(service_key)

    def _disconnect_locked(self, service_key: str) -> dict:
        adapter = self._adapter(service_key)
        try:
            adapter.disconnect(self._context(service_key))
        except IntegrationAuthRequired:
            pass
        except IntegrationTemporaryError as exc:
            return self.db.upsert_integration_connection(
                service_key,
                status=STATUS_ERROR,
                last_check_at=utc_now(),
                last_error=sanitize_diagnostic_text(str(exc)),
            )
        row = self.db.get_integration_connection(service_key)
        if row is None:
            row = self.db.upsert_integration_connection(service_key)
        return self.db.upsert_integration_connection(
            service_key,
            enabled=False,
            status=str(row.get("status") or STATUS_NOT_CONFIGURED),
        )

    def remove_connection(self, service_key: str) -> None:
        with self._operation_lock(service_key):
            self._adapter(service_key)
            row = self.db.get_integration_connection(service_key)
            if row is not None:
                ref = str(row.get("credential_ref") or "")
                if ref:
                    self.db.credential_store.delete(ref)
            self.db.delete_integration_connection(service_key)

    def accept_normalized_event(self, event: NormalizedIntegrationEvent) -> dict:
        """Apply one B3 event through the common provider-neutral engine.

        The provider adapter has already parsed/matched the raw provider event.
        This method enforces the registered+enabled+connected+allowed-event gate
        and serializes processing per service before entering the atomic DB core.
        """
        if not isinstance(event, NormalizedIntegrationEvent):
            raise TypeError("Ожидалось NormalizedIntegrationEvent.")
        service_key = str(event.service_key or "").strip()
        with self._operation_lock(service_key):
            adapter = self._adapter(service_key)
            if not adapter.accepts_event_type(event.event_type):
                raise IntegrationError(
                    f"Тип события {event.event_type!r} не разрешён адаптером {service_key}."
                )
            row = self.db.get_integration_connection(service_key)
            if row is None or not bool(row.get("enabled")) or str(row.get("status")) != STATUS_CONNECTED:
                raise IntegrationError(
                    f"Интеграция {service_key} должна быть включена и находиться в состоянии «Подключено»."
                )
            return self.db.process_normalized_integration_event(
                service_key=service_key,
                external_event_id=event.external_event_id,
                event_type=event.event_type,
                source_amount=event.source_amount,
                source_unit=event.source_unit,
                contributor=event.contributor,
                game_id=event.game_id,
                lot_title=event.lot_title,
                source_unit_label=event.source_unit_label,
                unit_kind=event.unit_kind,
                note=event.note,
                provider_metadata=dict(event.provider_metadata or {}),
                auction_id_hint=event.auction_id_hint,
                force_outside_auction=event.force_outside_auction,
            )

    def call_adapter(self, service_key: str, method_name: str, *args, **kwargs):
        """Call one adapter-specific operation with serialized credential access.

        B4 needs a few provider-specific management/runtime operations that are
        deliberately not part of the common B1 lifecycle.  Keeping the call
        behind the same per-service lock preserves the refresh-token single-
        flight guarantee while still letting adapters persist a rotated grant
        through ``context.save_credential``.
        """
        with self._operation_lock(service_key):
            adapter = self._adapter(service_key)
            method = getattr(adapter, str(method_name))
            result = method(self._context(service_key), *args, **kwargs)
            if isinstance(result, IntegrationOperationResult):
                return self._persist_result(service_key, result, enabled=True)
            return result

    def views(self) -> list[IntegrationView]:
        # Read every registered provider state in one SQLite snapshot.  The
        # status button refreshes periodically; opening one connection per
        # adapter made that tiny UI poll needlessly expensive as providers are
        # added.
        rows = {
            str(row.get("service_key") or ""): row
            for row in self.db.list_integration_connections()
        }
        views: list[IntegrationView] = []
        for adapter in self.registry.adapters():
            row = rows.get(adapter.service_key) or {}
            status = str(row.get("status") or STATUS_NOT_CONFIGURED)
            if status not in INTEGRATION_STATUSES:
                status = STATUS_ERROR
            message = str(row.get("last_error") or "")
            views.append(
                IntegrationView(
                    service_key=adapter.service_key,
                    display_name=adapter.display_name,
                    capabilities=tuple(sorted(str(item) for item in adapter.capabilities)),
                    enabled=bool(row.get("enabled", True)),
                    status=status,
                    status_label=STATUS_LABELS[status],
                    message=message,
                    details=tuple(adapter.view_details(dict(row.get("provider_config") or {}))),
                    last_check_at=row.get("last_check_at"),
                    last_event_at=row.get("last_event_at"),
                )
            )
        return views

    def operational_status_text(
        self,
        views: list[IntegrationView] | None = None,
    ) -> str:
        views = self.views() if views is None else views
        active = [view for view in views if view.enabled and view.status != STATUS_NOT_CONFIGURED]
        if not active:
            return "Интеграции: не настроены"
        if any(view.status == STATUS_ERROR for view in active):
            return "Интеграции: ошибка"
        if any(view.status == STATUS_REQUIRES_LOGIN for view in active):
            return "Интеграции: требуется внимание"
        if all(view.status == STATUS_CONNECTED for view in active):
            return "Интеграции: всё подключено"
        return "Интеграции: требуется внимание"

    def conversion_units(self) -> list[ConversionUnit]:
        units: list[ConversionUnit] = []
        for view in self.views():
            if not view.enabled or view.status != STATUS_CONNECTED:
                continue
            adapter = self._adapter(view.service_key)
            units.extend(adapter.conversion_units())
        return units


__all__ = [
    "STATUS_NOT_CONFIGURED",
    "STATUS_REQUIRES_LOGIN",
    "STATUS_CONNECTED",
    "STATUS_ERROR",
    "INTEGRATION_STATUSES",
    "STATUS_LABELS",
    "IntegrationError",
    "IntegrationAuthRequired",
    "IntegrationTemporaryError",
    "IntegrationOperationResult",
    "NormalizedIntegrationEvent",
    "IntegrationAdapter",
    "IntegrationContext",
    "IntegrationView",
    "IntegrationRegistry",
    "IntegrationManager",
]
