from __future__ import annotations

"""DonationAlerts adapter and OAuth/API primitives.

DonationAlerts documents two OAuth flows.  The desktop application deliberately
uses the Implicit grant as a public client so no Client Secret is embedded or
stored.  The browser redirects to a loopback-only callback page; JavaScript on
that page forwards the URL fragment to the local process because OAuth fragments
are never sent to HTTP servers by the browser.

Only the access token is secret.  It is serialized into the common CredentialStore
(DPAPI on Windows); SQLite keeps non-secret provider/account metadata only.
"""

import json
import secrets
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from .conversion import ConversionUnit, UNIT_KIND_CURRENCY
from .integrations import (
    STATUS_CONNECTED,
    STATUS_NOT_CONFIGURED,
    IntegrationAdapter,
    IntegrationAuthRequired,
    IntegrationError,
    IntegrationOperationResult,
    IntegrationTemporaryError,
)

DONATIONALERTS_SERVICE_KEY = "donationalerts"
DONATIONALERTS_DISPLAY_NAME = "DonationAlerts"
DONATIONALERTS_DONATION_EVENT_TYPE = "donationalerts_donation"
DONATIONALERTS_AUTHORIZE_URL = "https://www.donationalerts.com/oauth/authorize"
DONATIONALERTS_API_BASE = "https://www.donationalerts.com/api/v1"
DONATIONALERTS_PROFILE_URL = DONATIONALERTS_API_BASE + "/user/oauth"
DONATIONALERTS_DONATIONS_URL = DONATIONALERTS_API_BASE + "/alerts/donations"
DONATIONALERTS_CENTRIFUGE_SUBSCRIBE_URL = DONATIONALERTS_API_BASE + "/centrifuge/subscribe"
DONATIONALERTS_CENTRIFUGO_URL = "wss://centrifugo.donationalerts.com/connection/websocket"
DONATIONALERTS_REQUIRED_SCOPES = (
    "oauth-user-show",
    "oauth-donation-subscribe",
    "oauth-donation-index",
)
# Public OAuth application identifier for In one line. DonationAlerts documents
# client_id as publicly exposed; the desktop Implicit grant does not embed or use
# a Client Secret. Users therefore only complete browser authorization.
DONATIONALERTS_PUBLIC_CLIENT_ID = "20915"
DONATIONALERTS_LOOPBACK_HOST = "127.0.0.1"
DONATIONALERTS_LOOPBACK_PORT = 17643
DONATIONALERTS_CALLBACK_PATH = "/donationalerts/oauth/callback"
DONATIONALERTS_CAPTURE_PATH = "/donationalerts/oauth/complete"
DONATIONALERTS_REDIRECT_URI = (
    f"http://{DONATIONALERTS_LOOPBACK_HOST}:{DONATIONALERTS_LOOPBACK_PORT}"
    f"{DONATIONALERTS_CALLBACK_PATH}"
)
DONATIONALERTS_OAUTH_TIMEOUT_SECONDS = 5 * 60
DONATIONALERTS_CURRENCIES = (
    "RUB",
    "USD",
    "EUR",
    "BYN",
    "KZT",
    "UAH",
    "BRL",
    "TRY",
)


class DonationAlertsHttpError(RuntimeError):
    def __init__(self, status: int, message: str, payload: dict | None = None):
        super().__init__(str(message or f"HTTP {status}"))
        self.status = int(status)
        self.payload = dict(payload or {})


@dataclass(frozen=True)
class DonationAlertsOAuthRequest:
    authorization_url: str
    redirect_uri: str
    expires_at: float


@dataclass(frozen=True)
class DonationAlertsCredential:
    access: str
    client_id: str
    expires_at: float = 0.0
    scopes: tuple[str, ...] = ()

    @classmethod
    def from_json(cls, raw: str | None) -> "DonationAlertsCredential":
        if not raw:
            raise IntegrationAuthRequired("DonationAlerts требует входа.")
        try:
            payload = json.loads(str(raw))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise IntegrationAuthRequired(
                "Сохранённая авторизация DonationAlerts повреждена."
            ) from exc
        if not isinstance(payload, dict):
            raise IntegrationAuthRequired(
                "Сохранённая авторизация DonationAlerts повреждена."
            )
        access = str(payload.get("access") or "").strip()
        client_id = str(payload.get("client_id") or "").strip()
        if not access or not client_id:
            raise IntegrationAuthRequired("DonationAlerts требует повторного входа.")
        try:
            expires_at = float(payload.get("expires_at") or 0.0)
        except (TypeError, ValueError):
            expires_at = 0.0
        scopes_raw = payload.get("scopes") or []
        if isinstance(scopes_raw, str):
            scopes_raw = scopes_raw.split()
        if not isinstance(scopes_raw, (list, tuple)):
            scopes_raw = []
        scopes = tuple(sorted({str(item) for item in scopes_raw if str(item).strip()}))
        return cls(
            access=access,
            client_id=client_id,
            expires_at=expires_at,
            scopes=scopes,
        )

    @classmethod
    def from_fragment_payload(
        cls,
        payload: dict,
        *,
        client_id: str,
        now: float,
    ) -> "DonationAlertsCredential":
        access = str(payload.get("access_token") or "").strip()
        if not access:
            raise IntegrationAuthRequired(
                "DonationAlerts не вернул access token. Авторизация не завершена."
            )
        try:
            expires_in = max(0, int(payload.get("expires_in") or 0))
        except (TypeError, ValueError):
            expires_in = 0
        scopes_raw = payload.get("scope") or payload.get("scopes") or []
        if isinstance(scopes_raw, str):
            scopes_raw = scopes_raw.replace(",", " ").split()
        if not isinstance(scopes_raw, (list, tuple)):
            scopes_raw = []
        scopes = tuple(sorted({str(item) for item in scopes_raw if str(item).strip()}))
        return cls(
            access=access,
            client_id=str(client_id),
            expires_at=(float(now) + float(expires_in)) if expires_in else 0.0,
            scopes=scopes,
        )

    def to_json(self) -> str:
        return json.dumps(
            {
                "access": self.access,
                "client_id": self.client_id,
                "expires_at": self.expires_at,
                "scopes": list(self.scopes),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


class DonationAlertsApiClient:
    """Small stdlib-only HTTP client used off the Qt GUI thread."""

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
        query: dict | None = None,
        json_body: dict | None = None,
        access: str | None = None,
    ) -> dict:
        target = str(url)
        if query:
            target += ("&" if "?" in target else "?") + urlparse.urlencode(
                query,
                doseq=True,
            )
        data = None
        headers = {"Accept": "application/json"}
        if access:
            headers["Authorization"] = f"Bearer {access}"
        if json_body is not None:
            data = json.dumps(
                json_body,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urlrequest.Request(
            target,
            data=data,
            headers=headers,
            method=str(method).upper(),
        )
        try:
            with urlrequest.urlopen(req, timeout=self.timeout) as response:
                return self._decode_json(response.read())
        except urlerror.HTTPError as exc:
            try:
                raw = exc.read()
            except OSError:
                raw = b""
            payload = self._decode_json(raw)
            message = str(
                payload.get("message")
                or payload.get("error_description")
                or payload.get("error")
                or exc.reason
                or f"HTTP {exc.code}"
            )
            raise DonationAlertsHttpError(int(exc.code), message, payload) from exc
        except (urlerror.URLError, TimeoutError, OSError) as exc:
            raise IntegrationTemporaryError(
                "DonationAlerts временно недоступен по сети."
            ) from exc

    def get_profile(self, access: str) -> dict:
        return self._request_json("GET", DONATIONALERTS_PROFILE_URL, access=access)

    def list_donations(self, access: str, *, page: int = 1) -> dict:
        return self._request_json(
            "GET",
            DONATIONALERTS_DONATIONS_URL,
            query={"page": max(1, int(page))},
            access=access,
        )

    def subscribe_centrifugo(
        self,
        access: str,
        *,
        channels: list[str],
        client_id: str,
    ) -> dict:
        return self._request_json(
            "POST",
            DONATIONALERTS_CENTRIFUGE_SUBSCRIBE_URL,
            json_body={"channels": [str(item) for item in channels], "client": str(client_id)},
            access=access,
        )


class DonationAlertsOAuthReceiver:
    """Loopback-only receiver for the public OAuth Implicit fragment."""

    def __init__(
        self,
        *,
        state: str,
        host: str = DONATIONALERTS_LOOPBACK_HOST,
        port: int = DONATIONALERTS_LOOPBACK_PORT,
    ):
        self.state = str(state)
        self.host = str(host)
        self.port = int(port)
        self.redirect_uri = f"http://{self.host}:{self.port}{DONATIONALERTS_CALLBACK_PATH}"
        self._event = threading.Event()
        self._payload: dict | None = None
        self._error = ""
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def _callback_html(self) -> bytes:
        # The browser never sends URL fragments to HTTP servers.  This same-origin
        # page forwards only the OAuth fragment to the loopback process, then
        # scrubs it from browser history immediately.
        state_json = json.dumps(self.state, ensure_ascii=True)
        return ("""<!doctype html><html lang='ru'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>In one line - DonationAlerts</title></head><body>
<h2>In one line</h2><p id='status'>Завершаю подключение DonationAlerts...</p>
<script>
(async function(){
""" + f"const localState = {state_json};\n" + """
  const status = document.getElementById('status');
  const fragment = location.hash.startsWith('#') ? location.hash.slice(1) : '';
  const params = new URLSearchParams(fragment);
  const body = new URLSearchParams();
  for (const [key, value] of params.entries()) body.append(key, value);
  body.set('_inone_state', localState);
  history.replaceState(null, '', location.pathname);
  try {
    const response = await fetch('/donationalerts/oauth/complete', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'},
      body: body.toString(),
      cache: 'no-store'
    });
    const text = await response.text();
    status.textContent = response.ok
      ? 'DonationAlerts подключён. Можно закрыть эту вкладку и вернуться в In one line.'
      : ('Не удалось завершить подключение: ' + text);
  } catch (e) {
    status.textContent = 'Не удалось передать результат авторизации локальному приложению.';
  }
})();
</script></body></html>""").encode("utf-8")

    def start(self) -> None:
        receiver = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "InOneLineDonationAlertsOAuth/1"

            def log_message(self, _format, *_args):
                return

            def _send(self, status: int, body: bytes, content_type: str) -> None:
                self.send_response(int(status))
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Pragma", "no-cache")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'none'; script-src 'unsafe-inline'; connect-src 'self'; style-src 'none'",
                )
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler contract
                path = urlparse.urlsplit(self.path).path
                if path != DONATIONALERTS_CALLBACK_PATH:
                    self._send(404, b"Not Found", "text/plain; charset=utf-8")
                    return
                self._send(
                    200,
                    receiver._callback_html(),
                    "text/html; charset=utf-8",
                )

            def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler contract
                path = urlparse.urlsplit(self.path).path
                if path != DONATIONALERTS_CAPTURE_PATH:
                    self._send(404, b"Not Found", "text/plain; charset=utf-8")
                    return
                try:
                    length = int(self.headers.get("Content-Length") or 0)
                except (TypeError, ValueError):
                    length = 0
                if length < 0 or length > 64 * 1024:
                    self._send(413, b"Payload too large", "text/plain; charset=utf-8")
                    return
                raw = self.rfile.read(length).decode("utf-8", errors="replace")
                form = urlparse.parse_qs(raw, keep_blank_values=True)
                payload = {
                    str(key): (str(values[-1]) if values else "")
                    for key, values in form.items()
                }
                # DonationAlerts documentation does not promise an OAuth `state`
                # echo for the Implicit grant.  The callback page therefore gets
                # a one-time local nonce from this loopback server and must return
                # it on the same-origin POST.  If the provider does echo `state`,
                # validate that too.
                if str(payload.get("_inone_state") or "") != receiver.state:
                    receiver._error = "Локальная OAuth-проверка не совпала. Подключение отменено из соображений безопасности."
                    receiver._event.set()
                    self._send(400, b"Local OAuth state mismatch", "text/plain; charset=utf-8")
                    return
                provider_state = str(payload.get("state") or "")
                if provider_state and provider_state != receiver.state:
                    receiver._error = "OAuth state не совпал. Подключение отменено из соображений безопасности."
                    receiver._event.set()
                    self._send(400, b"OAuth state mismatch", "text/plain; charset=utf-8")
                    return
                if payload.get("error"):
                    receiver._error = str(
                        payload.get("error_description")
                        or payload.get("error")
                        or "DonationAlerts authorization failed"
                    )
                    receiver._event.set()
                    self._send(400, b"Authorization denied", "text/plain; charset=utf-8")
                    return
                if not str(payload.get("access_token") or ""):
                    receiver._error = "DonationAlerts не вернул access token."
                    receiver._event.set()
                    self._send(400, b"Missing access token", "text/plain; charset=utf-8")
                    return
                receiver._payload = payload
                receiver._event.set()
                self._send(200, b"OK", "text/plain; charset=utf-8")

        try:
            self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        except OSError as exc:
            raise IntegrationError(
                f"Не удалось открыть локальный OAuth callback {self.redirect_uri}. "
                "Проверьте, что порт не занят другой программой."
            ) from exc
        self._server.daemon_threads = True
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="DonationAlertsOAuthLoopback",
            daemon=True,
        )
        self._thread.start()

    def wait(self, timeout: float) -> dict:
        if not self._event.wait(timeout=max(1.0, float(timeout))):
            raise IntegrationAuthRequired(
                "Время ожидания авторизации DonationAlerts истекло. Запустите подключение снова."
            )
        if self._error:
            raise IntegrationAuthRequired(self._error)
        if self._payload is None:
            raise IntegrationAuthRequired("Авторизация DonationAlerts отменена.")
        return dict(self._payload)

    def cancel(self) -> None:
        self._error = "Авторизация DonationAlerts отменена пользователем."
        self._event.set()

    def close(self) -> None:
        server = self._server
        self._server = None
        if server is not None:
            try:
                server.shutdown()
            except Exception:
                pass
            try:
                server.server_close()
            except Exception:
                pass
        thread = self._thread
        self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)


class DonationAlertsAdapter(IntegrationAdapter):
    service_key = DONATIONALERTS_SERVICE_KEY
    display_name = DONATIONALERTS_DISPLAY_NAME
    capabilities = frozenset(
        {
            "OAuth Implicit (Public desktop)",
            "Donation history",
            "Centrifugo WebSocket",
            "RUB/USD/EUR and other DonationAlerts currencies",
        }
    )
    accepted_event_types = frozenset({DONATIONALERTS_DONATION_EVENT_TYPE})

    def __init__(
        self,
        *,
        client: DonationAlertsApiClient | None = None,
        client_id: str = DONATIONALERTS_PUBLIC_CLIENT_ID,
        redirect_uri: str = DONATIONALERTS_REDIRECT_URI,
        now: Callable[[], float] = time.time,
        oauth_receiver_factory: Callable[..., DonationAlertsOAuthReceiver] | None = None,
    ):
        self.client = client or DonationAlertsApiClient()
        self.public_client_id = self._normalize_client_id(client_id, allow_empty=True)
        self.redirect_uri = str(redirect_uri or DONATIONALERTS_REDIRECT_URI)
        self.now = now
        self.oauth_receiver_factory = oauth_receiver_factory or DonationAlertsOAuthReceiver
        self._oauth_ready_callback: Callable[[DonationAlertsOAuthRequest], None] | None = None
        self._active_receiver: DonationAlertsOAuthReceiver | None = None
        self._oauth_lock = threading.RLock()

    @staticmethod
    def _normalize_client_id(value: object, *, allow_empty: bool = False) -> str:
        client_id = str(value or "").strip()
        if not client_id and allow_empty:
            return ""
        if not client_id or len(client_id) > 64 or not client_id.isdigit():
            raise ValueError("DonationAlerts Client ID должен состоять только из цифр.")
        return client_id

    def set_oauth_ready_callback(
        self,
        callback: Callable[[DonationAlertsOAuthRequest], None] | None,
    ) -> None:
        self._oauth_ready_callback = callback

    def cancel_authorization(self) -> None:
        with self._oauth_lock:
            receiver = self._active_receiver
            if receiver is not None:
                receiver.cancel()

    def _client_id(self, context) -> str:
        if self.public_client_id:
            return self.public_client_id
        configured = str((context.provider_config or {}).get("client_id") or "").strip()
        if not configured:
            raise IntegrationAuthRequired(
                "Сначала укажите публичный DonationAlerts Client ID в карточке интеграции. "
                f"Redirect URI для регистрации приложения: {self.redirect_uri}"
            )
        return self._normalize_client_id(configured)

    def has_built_in_client_id(self) -> bool:
        return bool(self.public_client_id)

    def configured_client_id_from_row(self, provider_config: dict | None) -> str:
        if self.public_client_id:
            return self.public_client_id
        return str((provider_config or {}).get("client_id") or "").strip()

    def set_public_client_id(self, context, client_id: str) -> IntegrationOperationResult:
        if self.public_client_id:
            raise IntegrationError(
                "В этой сборке DonationAlerts Client ID уже встроен и не изменяется пользователем."
            )
        normalized = self._normalize_client_id(client_id)
        config = dict(context.provider_config or {})
        config["client_id"] = normalized
        # Any token issued to a previous application identity must not be silently
        # reused.  Credential JSON carries its own client_id; connect() will force
        # a fresh browser grant if they differ.
        return IntegrationOperationResult(
            status=STATUS_NOT_CONFIGURED,
            provider_config=config,
        )

    @staticmethod
    def _map_http_error(exc: DonationAlertsHttpError) -> None:
        if exc.status == 429 or exc.status >= 500:
            raise IntegrationTemporaryError(
                "DonationAlerts временно недоступен. Повторите позже."
            ) from exc
        if exc.status in {401, 403}:
            raise IntegrationAuthRequired(
                "Авторизация DonationAlerts недействительна или отозвана."
            ) from exc
        raise IntegrationError(f"DonationAlerts API: {exc}") from exc

    def _profile(self, access: str) -> dict:
        try:
            payload = self.client.get_profile(access)
        except DonationAlertsHttpError as exc:
            self._map_http_error(exc)
            raise AssertionError("unreachable")
        data = payload.get("data") or {}
        if not isinstance(data, dict):
            raise IntegrationError("DonationAlerts не вернул профиль подключённого аккаунта.")
        user_id = str(data.get("id") or "").strip()
        if not user_id:
            raise IntegrationError("DonationAlerts не вернул ID подключённого аккаунта.")
        return dict(data)

    def _result_for_profile(
        self,
        context,
        credential: DonationAlertsCredential,
        profile: dict,
    ) -> IntegrationOperationResult:
        config = dict(context.provider_config or {})
        if not self.public_client_id:
            config["client_id"] = credential.client_id
        else:
            config.pop("client_id", None)
        config.update(
            {
                "oauth_flow": "implicit_public_loopback",
                "donationalerts_user_id": str(profile.get("id") or ""),
                "code": str(profile.get("code") or ""),
                "display_name": str(profile.get("name") or profile.get("code") or ""),
                "granted_scopes": list(credential.scopes or DONATIONALERTS_REQUIRED_SCOPES),
                "redirect_uri": self.redirect_uri,
            }
        )
        return IntegrationOperationResult(
            status=STATUS_CONNECTED,
            provider_config=config,
            credential=credential.to_json(),
        )

    def _check(self, context) -> IntegrationOperationResult:
        client_id = self._client_id(context)
        credential = DonationAlertsCredential.from_json(context.credential)
        if credential.client_id != client_id:
            raise IntegrationAuthRequired(
                "DonationAlerts Client ID изменён. Требуется повторная авторизация."
            )
        if credential.expires_at and credential.expires_at <= self.now() + 30.0:
            raise IntegrationAuthRequired(
                "Сессия DonationAlerts истекла. Требуется повторный вход."
            )
        profile = self._profile(credential.access)
        return self._result_for_profile(context, credential, profile)

    def _oauth_flow(self, context) -> IntegrationOperationResult:
        client_id = self._client_id(context)
        state = secrets.token_urlsafe(32)
        receiver = self.oauth_receiver_factory(state=state)
        if str(getattr(receiver, "redirect_uri", self.redirect_uri)) != self.redirect_uri:
            # Test receivers may omit/replace the property; production receiver
            # must exactly match the registered redirect URI.
            receiver_redirect = str(getattr(receiver, "redirect_uri", "") or "")
            if receiver_redirect:
                raise IntegrationError(
                    "DonationAlerts OAuth receiver использует неожиданный redirect URI."
                )
        receiver.start()
        with self._oauth_lock:
            self._active_receiver = receiver
        try:
            query = {
                "client_id": client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "token",
                "scope": " ".join(DONATIONALERTS_REQUIRED_SCOPES),
                "state": state,
            }
            authorization_url = DONATIONALERTS_AUTHORIZE_URL + "?" + urlparse.urlencode(query)
            info = DonationAlertsOAuthRequest(
                authorization_url=authorization_url,
                redirect_uri=self.redirect_uri,
                expires_at=self.now() + DONATIONALERTS_OAUTH_TIMEOUT_SECONDS,
            )
            if self._oauth_ready_callback is not None:
                self._oauth_ready_callback(info)
            fragment = receiver.wait(DONATIONALERTS_OAUTH_TIMEOUT_SECONDS)
            credential = DonationAlertsCredential.from_fragment_payload(
                fragment,
                client_id=client_id,
                now=self.now(),
            )
            # Persist the grant before profile/network work can fail, mirroring
            # the common Twitch single-flight credential safety rule.
            if context.save_credential is None:
                raise IntegrationError("CredentialStore callback недоступен.")
            context.save_credential(credential.to_json())
            profile = self._profile(credential.access)
            return self._result_for_profile(context, credential, profile)
        finally:
            with self._oauth_lock:
                self._active_receiver = None
            receiver.close()

    def connect(self, context) -> IntegrationOperationResult:
        if context.credential:
            try:
                return self._check(context)
            except IntegrationAuthRequired:
                pass
        return self._oauth_flow(context)

    def check_connection(self, context) -> IntegrationOperationResult:
        return self._check(context)

    def reconnect(self, context) -> IntegrationOperationResult:
        return self._oauth_flow(context)

    def disconnect(self, context) -> None:
        # DonationAlerts public API does not document a token-revoke endpoint.
        # Common B1 disconnect only disables local use; "Удалить подключение"
        # removes the DPAPI credential entirely.
        return None

    def runtime_snapshot(self, context) -> dict:
        result = self._check(context)
        credential = DonationAlertsCredential.from_json(result.credential)
        profile = self._profile(credential.access)
        socket_token = str(profile.get("socket_connection_token") or "").strip()
        if not socket_token:
            raise IntegrationError("DonationAlerts не вернул Centrifugo socket token.")
        return {
            "access": credential.access,
            "user_id": str(profile.get("id") or ""),
            "socket_connection_token": socket_token,
        }

    def list_donations_page(self, context, page: int = 1) -> dict:
        client_id = self._client_id(context)
        credential = DonationAlertsCredential.from_json(context.credential)
        if credential.client_id != client_id:
            raise IntegrationAuthRequired("DonationAlerts требует повторного входа.")
        try:
            return self.client.list_donations(credential.access, page=max(1, int(page)))
        except DonationAlertsHttpError as exc:
            self._map_http_error(exc)
            raise AssertionError("unreachable")

    def subscribe_centrifugo(
        self,
        context,
        client_id: str,
        channel: str,
    ) -> str:
        oauth_client_id = self._client_id(context)
        credential = DonationAlertsCredential.from_json(context.credential)
        if credential.client_id != oauth_client_id:
            raise IntegrationAuthRequired("DonationAlerts требует повторного входа.")
        try:
            payload = self.client.subscribe_centrifugo(
                credential.access,
                channels=[str(channel)],
                client_id=str(client_id),
            )
        except DonationAlertsHttpError as exc:
            self._map_http_error(exc)
            raise AssertionError("unreachable")
        channels = payload.get("channels") or []
        if not isinstance(channels, list):
            raise IntegrationError("DonationAlerts вернул некорректный Centrifugo subscribe response.")
        for row in channels:
            if not isinstance(row, dict):
                continue
            if str(row.get("channel") or "") != str(channel):
                continue
            token = str(row.get("token") or "").strip()
            if token:
                return token
        raise IntegrationError("DonationAlerts не вернул токен приватного donation-канала.")

    def conversion_units(self) -> list[ConversionUnit]:
        return [
            ConversionUnit(
                currency,
                currency,
                DONATIONALERTS_DISPLAY_NAME,
                UNIT_KIND_CURRENCY,
            )
            for currency in DONATIONALERTS_CURRENCIES
        ]

    def view_details(self, provider_config: dict) -> tuple[str, ...]:
        details: list[str] = []
        display_name = str(provider_config.get("display_name") or "").strip()
        code = str(provider_config.get("code") or "").strip()
        user_id = str(provider_config.get("donationalerts_user_id") or "").strip()
        if display_name:
            details.append(f"Аккаунт: {display_name}" + (f" (@{code})" if code else ""))
        if user_id:
            details.append(f"DonationAlerts User ID: {user_id}")
        return tuple(details)


__all__ = [
    "DONATIONALERTS_SERVICE_KEY",
    "DONATIONALERTS_DISPLAY_NAME",
    "DONATIONALERTS_DONATION_EVENT_TYPE",
    "DONATIONALERTS_AUTHORIZE_URL",
    "DONATIONALERTS_API_BASE",
    "DONATIONALERTS_PROFILE_URL",
    "DONATIONALERTS_DONATIONS_URL",
    "DONATIONALERTS_CENTRIFUGE_SUBSCRIBE_URL",
    "DONATIONALERTS_CENTRIFUGO_URL",
    "DONATIONALERTS_REQUIRED_SCOPES",
    "DONATIONALERTS_PUBLIC_CLIENT_ID",
    "DONATIONALERTS_REDIRECT_URI",
    "DONATIONALERTS_CURRENCIES",
    "DonationAlertsHttpError",
    "DonationAlertsOAuthRequest",
    "DonationAlertsCredential",
    "DonationAlertsApiClient",
    "DonationAlertsOAuthReceiver",
    "DonationAlertsAdapter",
]
