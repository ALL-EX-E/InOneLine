from __future__ import annotations

"""Twitch integration adapter (B2 connection + B4 Channel Points management).

The desktop application uses Twitch Device Code Grant Flow as a Public client:
no Client Secret is accepted or stored.  OAuth access/refresh tokens are kept as
one JSON credential inside CredentialStore; only non-secret account/capability
metadata is written to SQLite provider_config.
"""

import json
import time
from dataclasses import dataclass
from threading import Event
from typing import Callable
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from .conversion import ConversionUnit, UNIT_KIND_SERVICE
from .integrations import (
    STATUS_CONNECTED,
    IntegrationAdapter,
    IntegrationAuthRequired,
    IntegrationError,
    IntegrationOperationResult,
    IntegrationTemporaryError,
)

TWITCH_SERVICE_KEY = "twitch"
TWITCH_DISPLAY_NAME = "Twitch"
TWITCH_REQUIRED_SCOPE = "channel:read:redemptions"
TWITCH_MANAGE_SCOPE = "channel:manage:redemptions"
TWITCH_CHANNEL_POINTS_UNIT = "TWITCH_CHANNEL_POINTS"
TWITCH_CHANNEL_POINTS_LABEL = "Twitch Channel Points"
TWITCH_CHANNEL_POINTS_EVENT_TYPE = "twitch_channel_points_redemption"
TWITCH_PUBLIC_CLIENT_ID = "n7ozt7mpj10ov280u9vd1sx01gr2zn"
TWITCH_DEVICE_URL = "https://id.twitch.tv/oauth2/device"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"
TWITCH_USERS_URL = "https://api.twitch.tv/helix/users"
TWITCH_REWARDS_URL = "https://api.twitch.tv/helix/channel_points/custom_rewards"
TWITCH_REDEMPTIONS_URL = TWITCH_REWARDS_URL + "/redemptions"
TWITCH_EVENTSUB_SUBSCRIPTIONS_URL = "https://api.twitch.tv/helix/eventsub/subscriptions"
TWITCH_DEVICE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"


class TwitchHttpError(RuntimeError):
    def __init__(self, status: int, message: str, payload: dict | None = None):
        super().__init__(str(message or f"HTTP {status}"))
        self.status = int(status)
        self.payload = dict(payload or {})


@dataclass(frozen=True)
class TwitchDeviceCode:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int
    expires_at: float


@dataclass(frozen=True)
class TwitchCredential:
    access: str
    refresh: str
    expires_at: float
    scopes: tuple[str, ...]

    @classmethod
    def from_json(cls, raw: str | None) -> "TwitchCredential":
        if not raw:
            raise IntegrationAuthRequired("Twitch требует входа.")
        try:
            payload = json.loads(str(raw))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise IntegrationAuthRequired("Сохранённая авторизация Twitch повреждена.") from exc
        if not isinstance(payload, dict):
            raise IntegrationAuthRequired("Сохранённая авторизация Twitch повреждена.")
        access = str(payload.get("access") or "")
        refresh = str(payload.get("refresh") or "")
        if not access or not refresh:
            raise IntegrationAuthRequired("Twitch требует повторного входа.")
        try:
            expires_at = float(payload.get("expires_at") or 0.0)
        except (TypeError, ValueError):
            expires_at = 0.0
        scopes_raw = payload.get("scopes") or []
        if not isinstance(scopes_raw, (list, tuple)):
            scopes_raw = []
        scopes = tuple(sorted({str(item) for item in scopes_raw if str(item).strip()}))
        return cls(access=access, refresh=refresh, expires_at=expires_at, scopes=scopes)

    @classmethod
    def from_token_payload(cls, payload: dict, now: float) -> "TwitchCredential":
        access = str(payload.get("access_token") or "")
        refresh = str(payload.get("refresh_token") or "")
        if not access or not refresh:
            raise IntegrationError("Twitch не вернул полную пару OAuth tokens.")
        try:
            expires_in = max(0, int(payload.get("expires_in") or 0))
        except (TypeError, ValueError):
            expires_in = 0
        scopes_raw = payload.get("scope") or []
        if isinstance(scopes_raw, str):
            scopes_raw = scopes_raw.split()
        if not isinstance(scopes_raw, (list, tuple)):
            scopes_raw = []
        scopes = tuple(sorted({str(item) for item in scopes_raw if str(item).strip()}))
        return cls(
            access=access,
            refresh=refresh,
            expires_at=float(now) + float(expires_in),
            scopes=scopes,
        )

    def to_json(self) -> str:
        return json.dumps(
            {
                "access": self.access,
                "refresh": self.refresh,
                "expires_at": self.expires_at,
                "scopes": list(self.scopes),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


class TwitchApiClient:
    """Small stdlib-only Twitch HTTP client, suitable for background workers."""

    def __init__(self, *, timeout: float = 15.0):
        self.timeout = max(1.0, float(timeout))

    @staticmethod
    def _decode_json(raw: bytes) -> dict:
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        form: dict | None = None,
        json_body: dict | None = None,
        query: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        target = str(url)
        if query:
            target += ("&" if "?" in target else "?") + urlparse.urlencode(query, doseq=True)
        data = None
        final_headers = {"Accept": "application/json"}
        if headers:
            final_headers.update({str(k): str(v) for k, v in headers.items()})
        if form is not None:
            data = urlparse.urlencode(form).encode("utf-8")
            final_headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif json_body is not None:
            data = json.dumps(json_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            final_headers["Content-Type"] = "application/json"
        req = urlrequest.Request(target, data=data, headers=final_headers, method=str(method).upper())
        try:
            with urlrequest.urlopen(req, timeout=self.timeout) as response:
                return self._decode_json(response.read())
        except urlerror.HTTPError as exc:
            try:
                raw = exc.read()
            except OSError:
                raw = b""
            payload = self._decode_json(raw)
            message = str(payload.get("message") or payload.get("error") or exc.reason or f"HTTP {exc.code}")
            raise TwitchHttpError(int(exc.code), message, payload) from exc
        except (urlerror.URLError, TimeoutError, OSError) as exc:
            raise IntegrationTemporaryError("Twitch временно недоступен по сети.") from exc

    def start_device_authorization(self, client_id: str, scopes: tuple[str, ...]) -> dict:
        return self._request_json(
            "POST",
            TWITCH_DEVICE_URL,
            form={"client_id": client_id, "scopes": " ".join(scopes)},
        )

    def poll_device_token(self, client_id: str, scopes: tuple[str, ...], device_code: str) -> dict:
        return self._request_json(
            "POST",
            TWITCH_TOKEN_URL,
            form={
                "client_id": client_id,
                "scopes": " ".join(scopes),
                "device_code": device_code,
                "grant_type": TWITCH_DEVICE_GRANT_TYPE,
            },
        )

    def refresh_access_token(self, client_id: str, refresh: str) -> dict:
        # Public Device Code clients intentionally send no confidential-client secret.
        return self._request_json(
            "POST",
            TWITCH_TOKEN_URL,
            form={
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                "client_id": client_id,
            },
        )

    def validate(self, access: str) -> dict:
        return self._request_json(
            "GET",
            TWITCH_VALIDATE_URL,
            headers={"Authorization": f"OAuth {access}"},
        )

    def get_current_user(self, client_id: str, access: str) -> dict:
        return self._request_json(
            "GET",
            TWITCH_USERS_URL,
            headers={"Client-Id": client_id, "Authorization": f"Bearer {access}"},
        )

    def get_user_by_login(self, client_id: str, access: str, login: str) -> dict:
        return self._request_json(
            "GET",
            TWITCH_USERS_URL,
            query={"login": str(login or "").strip()},
            headers={"Client-Id": client_id, "Authorization": f"Bearer {access}"},
        )

    @staticmethod
    def _api_headers(client_id: str, access: str) -> dict[str, str]:
        return {"Client-Id": client_id, "Authorization": f"Bearer {access}"}

    def get_custom_rewards(
        self,
        client_id: str,
        access: str,
        broadcaster_id: str,
        *,
        only_manageable_rewards: bool = False,
    ) -> dict:
        return self._request_json(
            "GET",
            TWITCH_REWARDS_URL,
            query={
                "broadcaster_id": broadcaster_id,
                "only_manageable_rewards": "true" if only_manageable_rewards else "false",
            },
            headers=self._api_headers(client_id, access),
        )

    def create_custom_reward(
        self,
        client_id: str,
        access: str,
        broadcaster_id: str,
        body: dict,
    ) -> dict:
        return self._request_json(
            "POST",
            TWITCH_REWARDS_URL,
            query={"broadcaster_id": broadcaster_id},
            json_body=body,
            headers=self._api_headers(client_id, access),
        )

    def update_custom_reward(
        self,
        client_id: str,
        access: str,
        broadcaster_id: str,
        reward_id: str,
        body: dict,
    ) -> dict:
        return self._request_json(
            "PATCH",
            TWITCH_REWARDS_URL,
            query={"broadcaster_id": broadcaster_id, "id": reward_id},
            json_body=body,
            headers=self._api_headers(client_id, access),
        )

    def delete_custom_reward(
        self,
        client_id: str,
        access: str,
        broadcaster_id: str,
        reward_id: str,
    ) -> dict:
        return self._request_json(
            "DELETE",
            TWITCH_REWARDS_URL,
            query={"broadcaster_id": broadcaster_id, "id": reward_id},
            headers=self._api_headers(client_id, access),
        )

    def get_custom_reward_redemptions(
        self,
        client_id: str,
        access: str,
        broadcaster_id: str,
        reward_id: str,
        *,
        status: str = "UNFULFILLED",
        first: int = 50,
        after: str | None = None,
    ) -> dict:
        query = {
            "broadcaster_id": broadcaster_id,
            "reward_id": reward_id,
            "status": status,
            "first": max(1, min(50, int(first))),
            "sort": "OLDEST",
        }
        if after:
            query["after"] = str(after)
        return self._request_json(
            "GET",
            TWITCH_REDEMPTIONS_URL,
            query=query,
            headers=self._api_headers(client_id, access),
        )

    def update_redemption_status(
        self,
        client_id: str,
        access: str,
        broadcaster_id: str,
        reward_id: str,
        redemption_id: str,
        status: str,
    ) -> dict:
        return self._request_json(
            "PATCH",
            TWITCH_REDEMPTIONS_URL,
            query={
                "broadcaster_id": broadcaster_id,
                "reward_id": reward_id,
                "id": redemption_id,
            },
            json_body={"status": str(status)},
            headers=self._api_headers(client_id, access),
        )

    def create_eventsub_subscription(
        self,
        client_id: str,
        access: str,
        *,
        session_id: str,
        broadcaster_id: str,
        reward_id: str,
    ) -> dict:
        return self._request_json(
            "POST",
            TWITCH_EVENTSUB_SUBSCRIPTIONS_URL,
            json_body={
                "type": "channel.channel_points_custom_reward_redemption.add",
                "version": "1",
                "condition": {
                    "broadcaster_user_id": str(broadcaster_id),
                    "reward_id": str(reward_id),
                },
                "transport": {"method": "websocket", "session_id": str(session_id)},
            },
            headers=self._api_headers(client_id, access),
        )


class TwitchAdapter(IntegrationAdapter):
    service_key = TWITCH_SERVICE_KEY
    display_name = TWITCH_DISPLAY_NAME
    capabilities = frozenset(
        {
            "OAuth Device Code (Public)",
            "Twitch identity",
            "Channel Points / Custom Rewards",
            "EventSub WebSocket",
        }
    )
    accepted_event_types = frozenset({TWITCH_CHANNEL_POINTS_EVENT_TYPE})
    required_scopes = (TWITCH_REQUIRED_SCOPE,)

    def __init__(
        self,
        *,
        client: TwitchApiClient | None = None,
        client_id: str = TWITCH_PUBLIC_CLIENT_ID,
        now: Callable[[], float] = time.time,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        normalized_client_id = str(client_id or "").strip()
        if not normalized_client_id or len(normalized_client_id) > 128 or any(
            ch.isspace() for ch in normalized_client_id
        ):
            raise ValueError("Twitch public Client ID is invalid")
        self.client = client or TwitchApiClient()
        self.client_id = normalized_client_id
        self.now = now
        self.sleeper = sleeper
        self._cancel_authorization = Event()
        self._device_code_callback: Callable[[TwitchDeviceCode], None] | None = None

    def set_device_code_callback(self, callback: Callable[[TwitchDeviceCode], None] | None) -> None:
        self._device_code_callback = callback

    def cancel_authorization(self) -> None:
        self._cancel_authorization.set()

    def _client_id(self, _context=None) -> str:
        # Public application identity is built into In one line. Users never need
        # to register their own Twitch Developer application or configure a Client ID.
        return self.client_id

    @staticmethod
    def _map_http_error(exc: TwitchHttpError, *, auth_401: bool = True) -> None:
        if exc.status == 429 or exc.status >= 500:
            raise IntegrationTemporaryError("Twitch временно недоступен. Повторите проверку позже.") from exc
        if auth_401 and exc.status == 401:
            raise IntegrationAuthRequired("Авторизация Twitch недействительна или отозвана.") from exc
        raise IntegrationError(f"Twitch API: {exc}") from exc

    def _save_rotated_credential(self, context, credential: TwitchCredential) -> None:
        if context.save_credential is None:
            raise IntegrationError("CredentialStore callback недоступен.")
        context.save_credential(credential.to_json())

    def _refresh(self, context, client_id: str, credential: TwitchCredential) -> TwitchCredential:
        try:
            payload = self.client.refresh_access_token(client_id, credential.refresh)
        except TwitchHttpError as exc:
            if exc.status in {400, 401}:
                raise IntegrationAuthRequired("Сессия Twitch истекла. Требуется повторный вход.") from exc
            self._map_http_error(exc)
            raise AssertionError("unreachable")
        rotated = TwitchCredential.from_token_payload(payload, self.now())
        # Public refresh tokens rotate/expire. Persist the new pair before any
        # subsequent API call can fail.
        self._save_rotated_credential(context, rotated)
        return rotated

    def _validate_with_refresh(
        self,
        context,
        client_id: str,
        credential: TwitchCredential,
    ) -> tuple[TwitchCredential, dict]:
        # DCF access tokens are short-lived. Refresh proactively near local expiry.
        if credential.expires_at and credential.expires_at <= self.now() + 90.0:
            credential = self._refresh(context, client_id, credential)
        try:
            validation = self.client.validate(credential.access)
        except TwitchHttpError as exc:
            if exc.status == 401:
                # One centralized refresh attempt is allowed. Revoked/invalid grants
                # will fail refresh and become Требует входа; there is no silent loop.
                credential = self._refresh(context, client_id, credential)
                try:
                    validation = self.client.validate(credential.access)
                except TwitchHttpError as second:
                    self._map_http_error(second)
                    raise AssertionError("unreachable")
            else:
                self._map_http_error(exc)
                raise AssertionError("unreachable")

        token_client_id = str(validation.get("client_id") or "")
        if token_client_id != client_id:
            raise IntegrationAuthRequired("Авторизация Twitch создана для другого приложения. Выполните повторный вход.")
        scopes = tuple(sorted({str(item) for item in (validation.get("scopes") or [])}))
        if not ({TWITCH_REQUIRED_SCOPE, TWITCH_MANAGE_SCOPE} & set(scopes)):
            raise IntegrationAuthRequired(
                "Авторизация Twitch не содержит права чтения/управления Channel Points redemptions."
            )
        return credential, validation

    def _profile_and_capability(
        self,
        context,
        client_id: str,
        credential: TwitchCredential,
        validation: dict,
    ) -> IntegrationOperationResult:
        try:
            user_payload = self.client.get_current_user(client_id, credential.access)
        except TwitchHttpError as exc:
            self._map_http_error(exc)
            raise AssertionError("unreachable")
        users = user_payload.get("data") or []
        if not isinstance(users, list) or not users or not isinstance(users[0], dict):
            raise IntegrationError("Twitch не вернул данные подключённого аккаунта.")
        user = users[0]
        user_id = str(user.get("id") or validation.get("user_id") or "")
        login = str(user.get("login") or validation.get("login") or "")
        display_name = str(user.get("display_name") or login)
        broadcaster_type = str(user.get("broadcaster_type") or "")
        if not user_id:
            raise IntegrationError("Twitch не вернул ID подключённого аккаунта.")

        rewards_available = True
        rewards_reason = "Доступны"
        rewards_count = 0
        try:
            rewards_payload = self.client.get_custom_rewards(
                client_id,
                credential.access,
                user_id,
            )
            rewards = rewards_payload.get("data") or []
            rewards_count = len(rewards) if isinstance(rewards, list) else 0
        except TwitchHttpError as exc:
            if exc.status == 403:
                # Non-Affiliate/Partner channels legitimately cannot use Channel Points.
                rewards_available = False
                rewards_reason = "Недоступны для этого канала (нужен Affiliate или Partner)"
            else:
                self._map_http_error(exc)
                raise AssertionError("unreachable")

        provider_config = dict(context.provider_config)
        # 0.3.59 stored a user-supplied public Client ID in provider_config.
        # 0.3.60 owns one application Client ID, so legacy config is discarded.
        provider_config.pop("client_id", None)
        provider_config.update(
            {
                "oauth_flow": "device_code_public",
                "twitch_user_id": user_id,
                "login": login,
                "display_name": display_name,
                "broadcaster_type": broadcaster_type,
                "granted_scopes": list(validation.get("scopes") or []),
                "channel_points_custom_rewards_available": rewards_available,
                "channel_points_custom_rewards_reason": rewards_reason,
                "custom_rewards_count": int(rewards_count),
            }
        )
        return IntegrationOperationResult(
            status=STATUS_CONNECTED,
            provider_config=provider_config,
            credential=credential.to_json(),
        )

    def resolve_profile_image(self, context, login: str) -> str:
        """Return one Twitch profile-image URL through the existing authorized client."""
        normalized = str(login or "").strip().lstrip("@").casefold()
        if not normalized or len(normalized) > 64 or not all(
            ch.isalnum() or ch == "_" for ch in normalized
        ):
            raise IntegrationError("Некорректное имя Twitch-канала.")
        client_id = self._client_id(context)
        credential = TwitchCredential.from_json(context.credential)
        credential, _validation = self._validate_with_refresh(
            context, client_id, credential
        )
        try:
            payload = self.client.get_user_by_login(
                client_id, credential.access, normalized
            )
        except TwitchHttpError as exc:
            self._map_http_error(exc)
            raise AssertionError("unreachable")
        users = payload.get("data") or []
        if not isinstance(users, list) or not users or not isinstance(users[0], dict):
            raise IntegrationError(f"Twitch-канал @{normalized} не найден.")
        image_url = str(users[0].get("profile_image_url") or "").strip()
        if not image_url:
            raise IntegrationError("Twitch не вернул изображение профиля этого канала.")
        return image_url

    def _check(self, context) -> IntegrationOperationResult:
        client_id = self._client_id(context)
        credential = TwitchCredential.from_json(context.credential)
        credential, validation = self._validate_with_refresh(context, client_id, credential)
        return self._profile_and_capability(context, client_id, credential, validation)

    def _device_flow(
        self,
        context,
        scopes: tuple[str, ...] | None = None,
    ) -> IntegrationOperationResult:
        client_id = self._client_id(context)
        requested_scopes = tuple(scopes or self.required_scopes)
        self._cancel_authorization.clear()
        try:
            payload = self.client.start_device_authorization(client_id, requested_scopes)
        except TwitchHttpError as exc:
            self._map_http_error(exc, auth_401=False)
            raise AssertionError("unreachable")
        device_code = str(payload.get("device_code") or "")
        user_code = str(payload.get("user_code") or "")
        verification_uri = str(payload.get("verification_uri") or "")
        try:
            expires_in = max(1, int(payload.get("expires_in") or 0))
            interval = max(1, int(payload.get("interval") or 5))
        except (TypeError, ValueError) as exc:
            raise IntegrationError("Twitch вернул некорректный Device Code response.") from exc
        if not device_code or not user_code or not verification_uri:
            raise IntegrationError("Twitch вернул неполный Device Code response.")
        started = self.now()
        info = TwitchDeviceCode(
            device_code=device_code,
            user_code=user_code,
            verification_uri=verification_uri,
            expires_in=expires_in,
            interval=interval,
            expires_at=started + expires_in,
        )
        if self._device_code_callback is not None:
            self._device_code_callback(info)

        poll_delay = float(interval)
        while self.now() < info.expires_at:
            if self._cancel_authorization.is_set():
                raise IntegrationAuthRequired("Авторизация Twitch отменена пользователем.")
            try:
                token_payload = self.client.poll_device_token(
                    client_id,
                    requested_scopes,
                    device_code,
                )
            except TwitchHttpError as exc:
                message = str(exc.payload.get("message") or exc).strip().casefold()
                if exc.status == 400 and "authorization_pending" in message:
                    self.sleeper(poll_delay)
                    continue
                if exc.status == 400 and "slow_down" in message:
                    poll_delay = min(30.0, poll_delay + 5.0)
                    self.sleeper(poll_delay)
                    continue
                if exc.status in {400, 401} and any(
                    marker in message
                    for marker in ("access_denied", "denied", "expired", "invalid device")
                ):
                    raise IntegrationAuthRequired("Авторизация Twitch не завершена или отклонена.") from exc
                self._map_http_error(exc, auth_401=False)
                raise AssertionError("unreachable")
            credential = TwitchCredential.from_token_payload(token_payload, self.now())
            # Persist immediately before validate/profile/capability network calls.
            self._save_rotated_credential(context, credential)
            credential, validation = self._validate_with_refresh(context, client_id, credential)
            return self._profile_and_capability(context, client_id, credential, validation)
        raise IntegrationAuthRequired("Код авторизации Twitch истёк. Запустите подключение снова.")

    def connect(self, context) -> IntegrationOperationResult:
        if context.credential:
            try:
                return self._check(context)
            except IntegrationAuthRequired:
                pass
        return self._device_flow(context)

    def check_connection(self, context) -> IntegrationOperationResult:
        return self._check(context)

    def reconnect(self, context) -> IntegrationOperationResult:
        return self._device_flow(context)

    def reconnect_for_channel_points(self, context) -> IntegrationOperationResult:
        """Force a fresh public grant that retains the B4 management scope."""
        return self._device_flow(context, (TWITCH_MANAGE_SCOPE,))

    def ensure_manage_scope(self, context) -> IntegrationOperationResult:
        """Upgrade the public grant only when B4 needs reward management."""
        if context.credential:
            try:
                client_id = self._client_id(context)
                credential = TwitchCredential.from_json(context.credential)
                credential, validation = self._validate_with_refresh(
                    context,
                    client_id,
                    credential,
                )
                scopes = {str(item) for item in (validation.get("scopes") or [])}
                if TWITCH_MANAGE_SCOPE in scopes:
                    return self._profile_and_capability(
                        context,
                        client_id,
                        credential,
                        validation,
                    )
            except IntegrationAuthRequired:
                pass
        return self._device_flow(context, (TWITCH_MANAGE_SCOPE,))

    def _managed_snapshot(self, context) -> dict:
        client_id = self._client_id(context)
        credential = TwitchCredential.from_json(context.credential)
        credential, validation = self._validate_with_refresh(
            context,
            client_id,
            credential,
        )
        scopes = {str(item) for item in (validation.get("scopes") or [])}
        if TWITCH_MANAGE_SCOPE not in scopes:
            raise IntegrationAuthRequired(
                "Для Channel Points требуется повторно подтвердить право channel:manage:redemptions."
            )
        broadcaster_id = str(validation.get("user_id") or context.provider_config.get("twitch_user_id") or "")
        if not broadcaster_id:
            raise IntegrationError("Twitch не вернул ID подключённого канала.")
        return {
            "client_id": client_id,
            "access": credential.access,
            "broadcaster_id": broadcaster_id,
            "scopes": tuple(sorted(scopes)),
        }

    def eventsub_snapshot(self, context) -> dict:
        return self._managed_snapshot(context)

    def list_manageable_rewards(self, context) -> list[dict]:
        snap = self._managed_snapshot(context)
        try:
            payload = self.client.get_custom_rewards(
                snap["client_id"],
                snap["access"],
                snap["broadcaster_id"],
                only_manageable_rewards=True,
            )
        except TwitchHttpError as exc:
            self._map_http_error(exc)
            raise AssertionError("unreachable")
        rows = payload.get("data") or []
        return [dict(row) for row in rows if isinstance(row, dict)]

    def create_managed_reward(self, context, body: dict) -> dict:
        snap = self._managed_snapshot(context)
        try:
            payload = self.client.create_custom_reward(
                snap["client_id"], snap["access"], snap["broadcaster_id"], dict(body)
            )
        except TwitchHttpError as exc:
            self._map_http_error(exc)
            raise AssertionError("unreachable")
        rows = payload.get("data") or []
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            raise IntegrationError("Twitch не вернул созданную Custom Reward.")
        return dict(rows[0])

    def update_managed_reward(self, context, reward_id: str, body: dict) -> dict:
        snap = self._managed_snapshot(context)
        try:
            payload = self.client.update_custom_reward(
                snap["client_id"], snap["access"], snap["broadcaster_id"], str(reward_id), dict(body)
            )
        except TwitchHttpError as exc:
            self._map_http_error(exc)
            raise AssertionError("unreachable")
        rows = payload.get("data") or []
        return dict(rows[0]) if isinstance(rows, list) and rows and isinstance(rows[0], dict) else {}

    def delete_managed_reward(self, context, reward_id: str) -> None:
        snap = self._managed_snapshot(context)
        try:
            self.client.delete_custom_reward(
                snap["client_id"], snap["access"], snap["broadcaster_id"], str(reward_id)
            )
        except TwitchHttpError as exc:
            if exc.status == 404:
                return
            self._map_http_error(exc)

    def update_redemption_status(
        self,
        context,
        reward_id: str,
        redemption_id: str,
        status: str,
    ) -> dict:
        snap = self._managed_snapshot(context)
        try:
            return self.client.update_redemption_status(
                snap["client_id"],
                snap["access"],
                snap["broadcaster_id"],
                str(reward_id),
                str(redemption_id),
                str(status),
            )
        except TwitchHttpError as exc:
            self._map_http_error(exc)
            raise AssertionError("unreachable")

    def create_eventsub_subscription(self, context, session_id: str, reward_id: str) -> dict:
        snap = self._managed_snapshot(context)
        try:
            return self.client.create_eventsub_subscription(
                snap["client_id"],
                snap["access"],
                session_id=str(session_id),
                broadcaster_id=snap["broadcaster_id"],
                reward_id=str(reward_id),
            )
        except TwitchHttpError as exc:
            self._map_http_error(exc)
            raise AssertionError("unreachable")

    def list_unfulfilled_redemptions(self, context, reward_id: str) -> list[dict]:
        snap = self._managed_snapshot(context)
        result: list[dict] = []
        cursor: str | None = None
        for _page in range(10):
            try:
                payload = self.client.get_custom_reward_redemptions(
                    snap["client_id"],
                    snap["access"],
                    snap["broadcaster_id"],
                    str(reward_id),
                    status="UNFULFILLED",
                    first=50,
                    after=cursor,
                )
            except TwitchHttpError as exc:
                self._map_http_error(exc)
                raise AssertionError("unreachable")
            rows = payload.get("data") or []
            result.extend(dict(row) for row in rows if isinstance(row, dict))
            pagination = payload.get("pagination") or {}
            cursor = str(pagination.get("cursor") or "") if isinstance(pagination, dict) else ""
            if not cursor:
                break
        return result

    def conversion_units(self) -> list[ConversionUnit]:
        return [
            ConversionUnit(
                TWITCH_CHANNEL_POINTS_UNIT,
                TWITCH_CHANNEL_POINTS_LABEL,
                service=TWITCH_DISPLAY_NAME,
                kind=UNIT_KIND_SERVICE,
            )
        ]

    def disconnect(self, context) -> None:
        self.cancel_authorization()

    def view_details(self, provider_config: dict) -> tuple[str, ...]:
        details: list[str] = []
        display_name = str(provider_config.get("display_name") or "")
        login = str(provider_config.get("login") or "")
        if display_name or login:
            account = display_name or login
            if login:
                account += f" (@{login})"
            details.append("Аккаунт: " + account)
        broadcaster_type = str(provider_config.get("broadcaster_type") or "")
        if broadcaster_type:
            channel_label = {
                "partner": "Partner",
                "affiliate": "Affiliate",
            }.get(broadcaster_type.casefold(), broadcaster_type)
            details.append("Тип канала: " + channel_label)
        elif provider_config.get("twitch_user_id"):
            details.append("Тип канала: обычный")
        if "channel_points_custom_rewards_available" in provider_config:
            reason = str(provider_config.get("channel_points_custom_rewards_reason") or "")
            if bool(provider_config.get("channel_points_custom_rewards_available")):
                count = int(provider_config.get("custom_rewards_count") or 0)
                details.append(f"Channel Points / Custom Rewards: доступны · найдено {count}")
            else:
                details.append("Channel Points / Custom Rewards: " + (reason or "недоступны"))
        granted = {str(item) for item in (provider_config.get("granted_scopes") or [])}
        if TWITCH_MANAGE_SCOPE in granted:
            details.append("Права B4: управление Channel Points разрешено")
        elif provider_config.get("twitch_user_id"):
            details.append("Права B4: потребуется подтверждение при включении Channel Points")
        return tuple(details)


__all__ = [
    "TWITCH_SERVICE_KEY",
    "TWITCH_DISPLAY_NAME",
    "TWITCH_REQUIRED_SCOPE",
    "TWITCH_MANAGE_SCOPE",
    "TWITCH_CHANNEL_POINTS_UNIT",
    "TWITCH_CHANNEL_POINTS_LABEL",
    "TWITCH_CHANNEL_POINTS_EVENT_TYPE",
    "TWITCH_PUBLIC_CLIENT_ID",
    "TWITCH_DEVICE_URL",
    "TWITCH_TOKEN_URL",
    "TWITCH_VALIDATE_URL",
    "TWITCH_USERS_URL",
    "TWITCH_REWARDS_URL",
    "TWITCH_REDEMPTIONS_URL",
    "TWITCH_EVENTSUB_SUBSCRIPTIONS_URL",
    "TwitchHttpError",
    "TwitchDeviceCode",
    "TwitchCredential",
    "TwitchApiClient",
    "TwitchAdapter",
]
