"""Own normalization of YouTube web chat responses. No UI or network code."""

from dataclasses import dataclass
import json
import math
import re
from urllib.parse import parse_qs, urlsplit
from .media import safe_emoji_url, safe_avatar_url


class ProtocolError(ValueError):
    """YouTube did not supply the expected chat data."""

    def __init__(self, message, *, permanent=False):
        super().__init__(message)
        self.permanent = permanent


@dataclass(frozen=True)
class Fragment:
    kind: str
    text: str
    image_url: str = ""


@dataclass(frozen=True)
class Message:
    id: str
    author_id: str
    author: str
    text: str
    sent_at: float | None
    emoji_count: int = 0
    fragments: tuple[Fragment, ...] = ()
    avatar_url: str = ""


@dataclass(frozen=True)
class Event:
    kind: str
    target: str = ""
    message: Message | None = None


@dataclass(frozen=True)
class Bootstrap:
    token: str
    context: dict
    title: str = ""


@dataclass(frozen=True)
class Batch:
    token: str
    delay: float
    events: tuple[Event, ...] = ()
    all_selected: bool | None = None
    all_token: str | None = None


def parse_video_id(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    try:
        url = urlsplit(value)
        valid = (url.scheme == "https" and url.hostname in {
            "youtube.com", "www.youtube.com", "m.youtube.com", "studio.youtube.com", "youtu.be"}
            and not url.username and not url.password and url.port in {None, 443})
        if not valid:
            raise ValueError
        query = parse_qs(url.query, keep_blank_values=True)
        if len(query.get("v", [])) > 1:
            raise ValueError
        if url.hostname == "youtu.be":
            video = url.path.strip("/")
        elif url.path.rstrip("/") in {"/watch", "/live_chat"}:
            video = query.get("v", [""])[0]
        else:
            match = re.fullmatch(r"/(?:live|shorts|embed)/([A-Za-z0-9_-]{11})/?", url.path)
            video = match.group(1) if match else ""
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", video):
            return video
    except (ValueError, TypeError):
        pass
    raise ValueError("Вставьте HTTPS-ссылку на конкретную трансляцию или её чат YouTube.")


def find(value, key):
    """Search within a selected response section, never for an arbitrary cursor."""
    if isinstance(value, dict):
        if key in value:
            return value[key]
        values = value.values()
    elif isinstance(value, list):
        values = value
    else:
        return None
    for child in values:
        result = find(child, key)
        if result is not None:
            return result
    return None


def _cursor(continuations):
    for item in continuations if isinstance(continuations, list) else []:
        if not isinstance(item, dict):
            continue
        for key in ("invalidationContinuationData", "timedContinuationData", "reloadContinuationData"):
            data = item.get(key)
            if isinstance(data, dict) and isinstance(data.get("continuation"), str) and data["continuation"]:
                ms = data.get("timeoutMs", 1000)
                if (isinstance(ms, bool) or not isinstance(ms, (int, float))
                        or not math.isfinite(ms) or not 0 <= ms <= 86_400_000):
                    raise ProtocolError("YouTube вернул неверный интервал ожидания.")
                return data["continuation"], max(1.0, ms / 1000)
    raise ProtocolError("YouTube не вернул маркер продолжения чата.")


def _embedded(page, pattern):
    decoder = json.JSONDecoder()
    for match in re.finditer(pattern, page):
        try:
            value = decoder.raw_decode(page[match.end():])[0]
            if isinstance(value, dict):
                yield value
        except (ValueError, RecursionError):
            continue


def parse_bootstrap(page: str, video_id: str) -> Bootstrap:
    initial = next(_embedded(page, r'(?:ytInitialData|window\["ytInitialData"\])\s*=\s*'), None)
    if initial is None:
        raise ProtocolError("Страница YouTube не содержит данных чата. Проверьте доступность ссылки.")
    chat = find(initial, "liveChatRenderer")
    if not isinstance(chat, dict):
        raise ProtocolError("У выбранного видео нет доступного чата.", permanent=True)
    token, _ = _cursor(chat.get("continuations"))
    configs = list(_embedded(page, r"ytcfg\.set\(\s*"))
    context = next((x["INNERTUBE_CONTEXT"] for x in configs if "INNERTUBE_CONTEXT" in x), None)
    if not isinstance(context, dict) or not isinstance(context.get("client"), dict):
        raise ProtocolError("Не удалось получить параметры подключения YouTube.")
    client = context["client"]
    if not client.get("clientName") or not client.get("clientVersion"):
        raise ProtocolError("YouTube не вернул параметры веб-клиента.")
    player = next(_embedded(page, r"ytInitialPlayerResponse\s*=\s*"), {})
    details = player.get("videoDetails", {})
    if details.get("videoId") and details["videoId"] != video_id:
        raise ProtocolError("YouTube открыл другое видео. Проверьте ссылку.", permanent=True)
    return Bootstrap(token, context, str(details.get("title", ""))[:300])


def _text(value):
    if not isinstance(value, dict):
        return "", 0, ()
    if isinstance(value.get("simpleText"), str):
        text = value["simpleText"][:20000]
        return text, 0, (Fragment("text", text),) if text else ()
    runs = value.get("runs", [])
    if not isinstance(runs, list):
        raise ProtocolError("YouTube вернул неожиданный формат содержимого сообщения.")
    parts, fragments, emojis, remaining = [], [], 0, 20000
    for run in runs[:2000]:
        if remaining <= 0:
            break
        if not isinstance(run, dict):
            continue
        if isinstance(run.get("text"), str):
            text = run["text"][:remaining]
            parts.append(text)
            fragments.append(Fragment("text", text))
            remaining -= len(text)
        elif isinstance(run.get("emoji"), dict):
            emoji = run["emoji"]
            shortcuts = emoji.get("shortcuts") or []
            if not isinstance(shortcuts, list):
                shortcuts = []
            label = find(emoji.get("image", {}), "label")
            fallback = emoji.get("emojiId", "")
            if not isinstance(fallback, str) or fallback.isascii():
                fallback = "[эмодзи]"
            text = (next((s for s in shortcuts if isinstance(s, str) and s), None)
                    or (label if isinstance(label, str) and label else fallback))[:min(remaining, 160)]
            image = emoji.get("image")
            thumbnails = image.get("thumbnails", []) if isinstance(image, dict) else []
            candidates = []
            for thumb in thumbnails if isinstance(thumbnails, list) else []:
                if isinstance(thumb, dict) and (url := safe_emoji_url(thumb.get("url"))):
                    width = thumb.get("width")
                    score = abs(width - 48) if isinstance(width, (int, float)) and math.isfinite(width) else 1000
                    candidates.append((score, url))
            image_url = min(candidates, key=lambda item: item[0])[1] if candidates else ""
            parts.append(text)
            fragments.append(Fragment("emoji", text, image_url))
            remaining -= len(text)
            emojis += 1
    return "".join(parts), emojis, tuple(fragments)


def _message(wrapped):
    if not isinstance(wrapped, dict):
        return None
    for kind, raw in wrapped.items():
        if kind not in {"liveChatTextMessageRenderer", "liveChatPaidMessageRenderer"} or not isinstance(raw, dict):
            continue
        if not isinstance(raw.get("id"), str) or not raw["id"]:
            continue
        text, count, fragments = _text(raw.get("message"))
        if not text:
            continue
        sent = None
        try:
            stamp = int(raw.get("timestampUsec", "")) / 1_000_000
            if math.isfinite(stamp) and 0 <= stamp <= 253402300799:
                sent = stamp
        except (ValueError, TypeError, OverflowError):
            pass
        author, _, _ = _text(raw.get("authorName"))
        avatar = raw.get("authorPhoto")
        thumbnails = avatar.get("thumbnails", []) if isinstance(avatar, dict) else []
        candidates = []
        for thumb in thumbnails if isinstance(thumbnails, list) else []:
            if not isinstance(thumb, dict):
                continue
            url = safe_avatar_url(thumb.get("url"))
            if not url:
                continue
            width = thumb.get("width")
            score = abs(width - 32) if isinstance(width, (int, float)) and math.isfinite(width) else 1000
            candidates.append((score, url))
        avatar_url = min(candidates, key=lambda item: item[0])[1] if candidates else ""
        return Message(raw["id"][:1000], str(raw.get("authorExternalChannelId", ""))[:1000],
                       author[:300] or "Зритель", text, sent, count, fragments, avatar_url)
    return None


def parse_batch(data: dict) -> Batch:
    try:
        live = data["continuationContents"]["liveChatContinuation"]
        token, delay = _cursor(live.get("continuations"))
    except (KeyError, TypeError, AttributeError) as exc:
        raise ProtocolError("Ответ YouTube не содержит данных чата.") from exc
    events = []
    for action in live.get("actions", []):
        if not isinstance(action, dict):
            continue
        for kind, item in action.items():
            if not isinstance(item, dict):
                continue
            if kind in {"addChatItemAction", "replaceChatItemAction"}:
                msg = _message(item.get("item") or item.get("replacementItem"))
                if msg:
                    events.append(Event("add" if kind == "addChatItemAction" else "replace",
                                        str(item.get("targetItemId", "")), msg))
            elif kind in {"removeChatItemAction", "markChatItemAsDeletedAction"}:
                if isinstance(item.get("targetItemId"), str) and item["targetItemId"]:
                    events.append(Event("delete", item["targetItemId"]))
            elif kind in {"removeChatItemByAuthorAction", "markChatItemsByAuthorAsDeletedAction"}:
                if isinstance(item.get("externalChannelId"), str) and item["externalChannelId"]:
                    events.append(Event("delete_author", item["externalChannelId"]))
    selected, all_token = None, None
    menu = find(live.get("header", {}), "sortFilterSubMenuRenderer")
    if isinstance(menu, dict):
        for item in menu.get("subMenuItems", []):
            if isinstance(item, dict) and str(item.get("title", "")).casefold() in {"live chat", "все сообщения"}:
                selected = item.get("selected") is True
                continuation = item.get("continuation", {})
                if not isinstance(continuation, dict):
                    raise ProtocolError("YouTube вернул неожиданные параметры режима чата.")
                control = continuation.get("reloadContinuationData", {})
                if not isinstance(control, dict):
                    raise ProtocolError("YouTube вернул неожиданный маркер режима чата.")
                if isinstance(control.get("continuation"), str):
                    all_token = control["continuation"]
    return Batch(token, delay, tuple(events), selected, all_token)
