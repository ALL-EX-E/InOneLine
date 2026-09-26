from __future__ import annotations

from html import escape
from html.parser import HTMLParser
from functools import lru_cache
from typing import Iterable


_ALLOWED_TAGS = {
    "p", "div", "span", "br", "b", "strong", "i", "em", "u",
    "h1", "h2", "h3", "h4", "ul", "ol", "li", "blockquote",
}
_VOID_TAGS = {"br"}
_ALLOWED_ATTRS = {"style", "align"}
_DANGEROUS_STYLE_TOKENS = ("url(", "expression", "javascript:", "@import", "behavior:")


def _safe_style(value: str) -> str:
    text = str(value or "").strip()
    lowered = text.casefold().replace(" ", "")
    if any(token in lowered for token in _DANGEROUS_STYLE_TOKENS):
        return ""
    # QTextEdit produces ordinary inline typography/paragraph CSS.  Preserve
    # that formatting, but never permit markup to reference external content.
    return text


class _RulesHtmlSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._blocked_depth = 0

    def handle_starttag(self, tag: str, attrs: Iterable[tuple[str, str | None]]) -> None:
        name = str(tag).casefold()
        if name in {"meta", "link"}:
            return
        if name in {"script", "iframe", "object", "embed", "svg", "math", "style"}:
            self._blocked_depth += 1
            return
        if self._blocked_depth or name not in _ALLOWED_TAGS:
            return

        safe_attrs: list[str] = []
        for key, raw_value in attrs:
            attr = str(key).casefold()
            if attr not in _ALLOWED_ATTRS:
                continue
            value = str(raw_value or "")
            if attr == "style":
                value = _safe_style(value)
                if not value:
                    continue
            elif attr == "align":
                value = value.casefold()
                if value not in {"left", "center", "right", "justify"}:
                    continue
            safe_attrs.append(f' {attr}="{escape(value, quote=True)}"')

        self.parts.append(f"<{name}{''.join(safe_attrs)}>")

    def handle_startendtag(self, tag: str, attrs: Iterable[tuple[str, str | None]]) -> None:
        name = str(tag).casefold()
        if name == "br" and not self._blocked_depth:
            self.parts.append("<br>")

    def handle_endtag(self, tag: str) -> None:
        name = str(tag).casefold()
        if name in {"meta", "link"}:
            return
        if name in {"script", "iframe", "object", "embed", "svg", "math", "style"}:
            if self._blocked_depth:
                self._blocked_depth -= 1
            return
        if self._blocked_depth or name not in _ALLOWED_TAGS or name in _VOID_TAGS:
            return
        self.parts.append(f"</{name}>")

    def handle_data(self, data: str) -> None:
        if not self._blocked_depth:
            self.parts.append(escape(str(data), quote=False))


@lru_cache(maxsize=8)
def _sanitize_rules_html_cached(value: str) -> str:
    parser = _RulesHtmlSanitizer()
    parser.feed(value)
    parser.close()
    return "".join(parser.parts).strip()


def sanitize_rules_html(value: str) -> str:
    """Return the safe rich-text subset rendered by the OBS rules viewer.

    Rules are authored locally in QTextEdit, but the Browser Source still treats
    HTML as executable markup.  The API therefore strips executable/embedded
    content and preserves only the formatting tags/attributes produced by the
    approved WYSIWYG editor.
    """
    # /api/rules is polled frequently while the saved HTML usually stays
    # unchanged for minutes or hours.  Sanitization is pure, so a small bounded
    # cache removes repeated HTMLParser work without weakening the security
    # boundary or retaining unbounded user content.
    return _sanitize_rules_html_cached(str(value or ""))
