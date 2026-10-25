from __future__ import annotations

"""D41-03: read-only YouTube OAuth desktop adapter. Credentials live in DPAPI.

The public Google Client ID is configuration, not a Client Secret. OAuth code
and PKCE verifier are exchanged from a worker, never from the OBS/browser view.
"""
import base64
import hashlib
import json
import secrets
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from .integrations import (
    IntegrationAdapter, IntegrationAuthRequired, IntegrationError,
    IntegrationOperationResult, IntegrationTemporaryError,
)

YOUTUBE_SERVICE_KEY = "youtube"
YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
YOUTUBE_API = "https://www.googleapis.com/youtube/v3"
YOUTUBE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_TOKEN = "https://oauth2.googleapis.com/token"
YOUTUBE_CALLBACK_PATH = "/youtube/oauth/callback"


@dataclass(frozen=True)
class YouTubeOAuthRequest:
    authorization_url: str
    redirect_uri: str


@dataclass(frozen=True)
class YouTubeCredential:
    access: str
    refresh: str
    client_id: str
    expires_at: float

    def serialize(self) -> str:
        return json.dumps({
            "access": self.access, "refresh": self.refresh,
            "client_id": self.client_id, "expires_at": self.expires_at,
        }, separators=(",", ":"), sort_keys=True)

    @classmethod
    def parse(cls, raw: str | None) -> "YouTubeCredential":
        try:
            row = json.loads(raw or "null")
            if not isinstance(row, dict) or not row.get("access") or not row.get("client_id"):
                raise ValueError("missing fields")
            return cls(str(row["access"]), str(row.get("refresh") or ""),
                       str(row["client_id"]), float(row.get("expires_at") or 0))
        except (ValueError, TypeError) as exc:
            raise IntegrationAuthRequired("YouTube требует авторизации через «Интеграции».") from exc

    @classmethod
    def token(cls, data: dict, client_id: str, *, previous_refresh: str = "") -> "YouTubeCredential":
        access = str(data.get("access_token") or "")
        refresh = str(data.get("refresh_token") or previous_refresh)
        if not access or not refresh:
            raise IntegrationAuthRequired("Google не выдал токен для дальнейшего чтения YouTube.")
        return cls(access, refresh, client_id, time.time() + max(0, int(data.get("expires_in") or 3600)))


class YouTubeHttpError(IntegrationError):
    def __init__(self, status: int, reason: str):
        self.status = status
        self.reason = str(reason or "unknown")
        super().__init__(f"YouTube HTTP {status}: {self.reason}")


class YouTubeApi:
    def __init__(self, timeout: float = 15.0):
        self.timeout = float(timeout)

    def _json(self, url: str, *, params: dict | None = None,
              access: str = "", post: dict | None = None) -> dict:
        if params:
            url += "?" + urlparse.urlencode(params)
        body = urlparse.urlencode(post).encode("utf-8") if post is not None else None
        req = urlrequest.Request(url, data=body, headers={
            "Accept": "application/json",
            **({"Content-Type": "application/x-www-form-urlencoded"} if body is not None else {}),
            **({"Authorization": "Bearer " + access} if access else {}),
        })
        try:
            with urlrequest.urlopen(req, timeout=self.timeout) as response:
                raw = response.read(5_000_001)
            if len(raw) > 5_000_000:
                raise IntegrationError("Слишком большой ответ YouTube API.")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise IntegrationError("Некорректный ответ YouTube API.")
            return result
        except urlerror.HTTPError as exc:
            reason = ""
            try:
                payload = json.loads(exc.read(16384))
                detail = payload.get("error", {})
                if isinstance(detail, dict):
                    errors = detail.get("errors") or []
                    reason = str((errors[0] if errors else {}).get("reason") or detail.get("status") or "")
                else:
                    reason = str(detail)
            except (ValueError, AttributeError, TypeError):
                pass
            raise YouTubeHttpError(exc.code, reason) from None
        except (urlerror.URLError, TimeoutError, OSError) as exc:
            raise IntegrationTemporaryError("Нет соединения с Google/YouTube.") from exc

    def exchange(self, *, code: str, redirect_uri: str, verifier: str, client_id: str) -> dict:
        return self._json(YOUTUBE_TOKEN, post={
            "code": code, "client_id": client_id, "code_verifier": verifier,
            "grant_type": "authorization_code", "redirect_uri": redirect_uri,
        })

    def refresh(self, credential: YouTubeCredential) -> dict:
        return self._json(YOUTUBE_TOKEN, post={
            "client_id": credential.client_id, "refresh_token": credential.refresh,
            "grant_type": "refresh_token",
        })

    def channels(self, access: str) -> list[dict]:
        return self._json(YOUTUBE_API + "/channels", access=access,
                          params={"part": "snippet", "mine": "true", "maxResults": 50}).get("items") or []

    def broadcasts(self, access: str) -> list[dict]:
        all_items = []
        page = ""
        for _ in range(20):
            params = {"part": "id,snippet,status", "mine": "true",
                      "broadcastStatus": "active", "broadcastType": "all", "maxResults": 50}
            if page:
                params["pageToken"] = page
            result = self._json(YOUTUBE_API + "/liveBroadcasts", access=access, params=params)
            all_items.extend(result.get("items") or [])
            page = str(result.get("nextPageToken") or "")
            if not page:
                break
        else:
            raise IntegrationError("Невозможно подтвердить полный список эфиров YouTube.")
        return all_items

    def chat_page(self, access: str, live_chat_id: str, page_token: str = "") -> dict:
        params = {"liveChatId": live_chat_id, "part": "id,snippet,authorDetails", "maxResults": 200}
        if page_token:
            params["pageToken"] = page_token
        return self._json(YOUTUBE_API + "/liveChat/messages", access=access, params=params)


class _GoogleLoopback:
    def __init__(self):
        self.state = secrets.token_urlsafe(32)
        self.verifier = secrets.token_urlsafe(72)
        self.event = threading.Event()
        self.result: dict = {}
        self.server = None
        self.thread = None
        self.redirect_uri = ""

    def __enter__(self):
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def do_GET(self):  # noqa: N802
                parsed = urlparse.urlsplit(self.path)
                if parsed.path != YOUTUBE_CALLBACK_PATH or self.client_address[0] not in ("127.0.0.1", "::1"):
                    self.send_error(404)
                    return
                query = urlparse.parse_qs(parsed.query)
                incoming_state = str((query.get("state") or [""])[0])
                if not secrets.compare_digest(incoming_state, parent.state):
                    self.send_error(400, "OAuth state mismatch")
                    return
                parent.result = {
                    "code": str((query.get("code") or [""])[0]),
                    "error": str((query.get("error") or [""])[0]),
                }
                parent.event.set()
                payload = ("<!doctype html><meta charset='utf-8'><title>InOneLine YouTube</title>"
                           "<p>Вход обработан. Можно закрыть вкладку и вернуться в InOneLine.</p>").encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Security-Policy", "default-src 'none'")
                self.end_headers()
                self.wfile.write(payload)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.redirect_uri = f"http://127.0.0.1:{self.server.server_port}{YOUTUBE_CALLBACK_PATH}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="YouTubeOAuthCallback")
        self.thread.start()
        return self

    def __exit__(self, *_args):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=2)

    def await_code(self, cancel: threading.Event, timeout: float = 300) -> str:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not cancel.is_set():
            if self.event.wait(0.25):
                if self.result.get("error"):
                    raise IntegrationAuthRequired("Вход Google был отменён.")
                code = str(self.result.get("code") or "")
                if code:
                    return code
                raise IntegrationAuthRequired("Google не вернул код OAuth.")
        raise IntegrationAuthRequired("Вход YouTube отменён или истекло время ожидания.")


class YouTubeAdapter(IntegrationAdapter):
    service_key = YOUTUBE_SERVICE_KEY
    display_name = "YouTube"
    capabilities = frozenset({"YouTube read-only live chat", "OAuth PKCE (Public desktop)"})

    def __init__(self, *, api: YouTubeApi | None = None, public_client_id: str = ""):
        self.api = api or YouTubeApi()
        self.public_client_id = str(public_client_id or "").strip()
        self._auth_ready = None
        self._cancel = threading.Event()

    def set_oauth_ready_callback(self, callback):
        self._auth_ready = callback

    def cancel_authorization(self):
        self._cancel.set()

    @staticmethod
    def normalize_client_id(value: str) -> str:
        cid = str(value or "").strip()
        if not cid.endswith(".apps.googleusercontent.com") or len(cid) > 250:
            raise ValueError("Нужен публичный OAuth Client ID настольного приложения Google.")
        return cid

    def _client_id(self, context) -> str:
        configured = str(context.provider_config.get("youtube_client_id") or self.public_client_id).strip()
        if not configured:
            raise IntegrationAuthRequired("Сначала укажите OAuth Client ID Google в «Интеграциях».")
        return self.normalize_client_id(configured)

    def set_public_client_id(self, context, client_id: str) -> IntegrationOperationResult:
        value = self.normalize_client_id(client_id)
        config = dict(context.provider_config)
        config["youtube_client_id"] = value
        # Change of public OAuth app must not silently destroy a working credential.
        return IntegrationOperationResult(
            status="requires_login", provider_config=config,
            message="Для нового Google Client ID выполните «Подключить» или «Переподключить».",
        )

    @staticmethod
    def _one_channel(items: list[dict]) -> tuple[str, str]:
        if len(items) != 1:
            raise IntegrationAuthRequired(
                "Не удалось однозначно определить авторизованный YouTube-канал. "
                "Проверьте канал Google и выполните повторный вход."
            )
        row = items[0]
        channel_id = str(row.get("id") or "")
        name = str((row.get("snippet") or {}).get("title") or "")
        if not channel_id or not name:
            raise IntegrationAuthRequired("Google не предоставил ID и название YouTube-канала.")
        return channel_id, name

    def _credential(self, context) -> YouTubeCredential:
        c = YouTubeCredential.parse(context.credential)
        if c.expires_at - time.time() < 90:
            if not c.refresh:
                raise IntegrationAuthRequired("Повторно авторизуйте YouTube.")
            try:
                c = YouTubeCredential.token(self.api.refresh(c), c.client_id, previous_refresh=c.refresh)
            except YouTubeHttpError as exc:
                if exc.status in (400, 401):
                    raise IntegrationAuthRequired("Google требует повторной авторизации YouTube.") from None
                self._map_http_error(exc)
            if context.save_credential:
                context.save_credential(c.serialize())
        return c

    @staticmethod
    def _map_http_error(exc: YouTubeHttpError):
        if exc.status == 401:
            raise IntegrationAuthRequired("Требуется повторная авторизация YouTube.") from None
        if exc.status in (429, 500, 502, 503, 504) or exc.reason in (
                "rateLimitExceeded", "userRateLimitExceeded", "quotaExceeded"):
            raise IntegrationTemporaryError("YouTube временно недоступен или ограничил квоту.") from None
        if exc.status == 403:
            raise IntegrationError("YouTube отклонил запрос. Проверьте доступ API, канал и разрешения.") from None
        raise IntegrationError("Ошибка чтения YouTube API.") from None

    def connect(self, context) -> IntegrationOperationResult:
        client_id = self._client_id(context)
        self._cancel.clear()
        with _GoogleLoopback() as callback:
            challenge = base64.urlsafe_b64encode(
                hashlib.sha256(callback.verifier.encode("ascii")).digest()
            ).rstrip(b"=").decode("ascii")
            url = YOUTUBE_AUTH + "?" + urlparse.urlencode({
                "client_id": client_id,
                "redirect_uri": callback.redirect_uri,
                "response_type": "code",
                "scope": YOUTUBE_SCOPE,
                "access_type": "offline",
                "prompt": "consent select_account",
                "state": callback.state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            })
            if not self._auth_ready:
                raise IntegrationError("Нет обработчика входа Google в интерфейсе.")
            self._auth_ready(YouTubeOAuthRequest(url, callback.redirect_uri))
            code = callback.await_code(self._cancel)
            try:
                credential = YouTubeCredential.token(self.api.exchange(
                    code=code, redirect_uri=callback.redirect_uri,
                    verifier=callback.verifier, client_id=client_id,
                ), client_id)
                channel_id, name = self._one_channel(self.api.channels(credential.access))
            except YouTubeHttpError as exc:
                self._map_http_error(exc)
            config = dict(context.provider_config)
            config.update(youtube_client_id=client_id, youtube_channel_id=channel_id,
                          youtube_channel_name=name)
            return IntegrationOperationResult(
                provider_config=config, credential=credential.serialize())

    def reconnect(self, context) -> IntegrationOperationResult:
        return self.connect(context)

    def check_connection(self, context) -> IntegrationOperationResult:
        credential = self._credential(context)
        try:
            channel_id, name = self._one_channel(self.api.channels(credential.access))
        except YouTubeHttpError as exc:
            self._map_http_error(exc)
        config = dict(context.provider_config)
        config.update(youtube_client_id=credential.client_id,
                      youtube_channel_id=channel_id, youtube_channel_name=name)
        return IntegrationOperationResult(provider_config=config)

    def account_access(self, context) -> str:
        return self._credential(context).access

    def view_details(self, config: dict) -> tuple[str, ...]:
        name = str(config.get("youtube_channel_name") or "")
        return (f"Авторизованный YouTube-канал: {name}",) if name else ()
