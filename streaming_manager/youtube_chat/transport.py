"""Anonymous, bounded HTTP transport. No account cookies or raw response logs."""

import datetime
import email.utils
import json
import socket
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from .protocol import ProtocolError, parse_bootstrap, parse_batch


class FetchError(Exception):
    def __init__(self, message, *, retryable=True, reset=False, retry_after=0, rate_limited=False):
        super().__init__(message)
        self.retryable = retryable
        self.reset = reset
        self.retry_after = retry_after
        self.rate_limited = rate_limited


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if target.scheme != "https" or target.hostname not in {"www.youtube.com", "youtube.com"}:
            raise FetchError("YouTube перенаправляет на страницу входа или подтверждения. Откройте ссылку в браузере.",
                             retryable=False)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _retry_after(value):
    if not value:
        return 0
    try:
        return max(0, min(int(value), 86400))
    except (ValueError, TypeError):
        try:
            moment = email.utils.parsedate_to_datetime(value)
            return max(0, min((moment - datetime.datetime.now(datetime.timezone.utc)).total_seconds(), 86400))
        except (ValueError, TypeError, OverflowError):
            return 0


class Transport:
    BASE = "https://www.youtube.com"
    MAX_BYTES = 8_000_000

    def __init__(self, *, opener=None):
        self._open = opener or urllib.request.build_opener(SafeRedirect()).open

    def _request(self, path, payload=None):
        headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"}
        if payload is not None:
            headers.update({"Content-Type": "application/json", "Origin": self.BASE,
                            "Referer": self.BASE + "/"})
        request = urllib.request.Request(self.BASE + path,
                                        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
                                        headers=headers)
        try:
            with self._open(request, timeout=10) as response:
                if response.status != 200:
                    raise FetchError("Неожиданный ответ YouTube.")
                body = response.read(self.MAX_BYTES + 1)
                if len(body) > self.MAX_BYTES:
                    raise FetchError("Ответ YouTube слишком велик.", retryable=False)
                return body
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise FetchError("YouTube попросил уменьшить частоту запросов.",
                                 retry_after=_retry_after(exc.headers.get("Retry-After")),
                                 rate_limited=True) from None
            if exc.code in {401, 403}:
                raise FetchError("YouTube ограничил доступ к этому чату.", retryable=False) from None
            if exc.code == 400 and payload is not None:
                raise FetchError("Маркер чата устарел; обновляем подключение.", reset=True) from None
            if exc.code in {404, 410}:
                raise FetchError("Видео или чат недоступны.", retryable=False) from None
            raise FetchError("YouTube временно недоступен (HTTP " + str(exc.code) + ").",
                             retryable=exc.code >= 500) from None
        except (urllib.error.URLError, OSError, socket.timeout):
            raise FetchError("Не удалось связаться с YouTube. Проверяем соединение.") from None

    def bootstrap(self, video_id):
        page = self._request("/watch?v=" + video_id + "&hl=en").decode("utf-8", "replace")
        try:
            return parse_bootstrap(page, video_id)
        except ProtocolError as exc:
            raise FetchError(str(exc), retryable=not exc.permanent) from None

    def poll(self, context, token):
        body = self._request("/youtubei/v1/live_chat/get_live_chat", {"context": context, "continuation": token})
        try:
            return parse_batch(json.loads(body))
        except (ValueError, TypeError, RecursionError) as exc:
            message = str(exc) if isinstance(exc, ProtocolError) else "YouTube вернул неожиданный формат ответа."
            raise FetchError(message, reset=True) from None
