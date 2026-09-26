from __future__ import annotations

import json
import mimetypes
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from .constants import APP_VERSION
from .database import Database
from .media import (
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS,
    is_supported_media_name,
    managed_media_directory,
    resolve_media_asset_path,
    supported_media_extensions,
)

OVERLAY_VERSION_HEADER = "X-InOneLine-Version"
OVERLAY_HANDSHAKE_SCRIPT_ID = "iol-version-handshake"


def _inject_overlay_version_handshake(html: str, page_version: str) -> str:
    """Inject the E2 stale-page/version handshake into one OBS overlay page.

    Existing overlays already poll localhost JSON endpoints.  The injected
    wrapper observes those normal fetch responses, so E2 adds no extra polling
    timer or request stream.  If the running application reports a different
    version, the page performs one cache-busting reload.  `_iol_v` is also the
    loop guard if OBS somehow serves the stale HTML again after that reload.
    """
    if f'id="{OVERLAY_HANDSHAKE_SCRIPT_ID}"' in html:
        return html
    marker = "</head>"
    if marker not in html:
        raise ValueError("OBS Browser Source HTML has no </head> marker")

    page_version_json = json.dumps(str(page_version), ensure_ascii=False)
    header_json = json.dumps(OVERLAY_VERSION_HEADER)
    script = (
        f'<script id="{OVERLAY_HANDSHAKE_SCRIPT_ID}">\n'
        '(() => {\n'
        '  "use strict";\n'
        f'  const PAGE_VERSION = {page_version_json};\n'
        f'  const VERSION_HEADER = {header_json};\n'
        '  const nativeFetch = window.fetch.bind(window);\n'
        '  let reloadStarted = false;\n\n'
        '  function maybeReloadForVersion(response) {\n'
        '    if (reloadStarted || !response || !response.headers) return;\n'
        '    const serverVersion = response.headers.get(VERSION_HEADER);\n'
        '    if (!serverVersion || serverVersion === PAGE_VERSION) return;\n\n'
        '    const currentUrl = new URL(window.location.href);\n'
        '    if (currentUrl.searchParams.get("_iol_v") === serverVersion) return;\n\n'
        '    reloadStarted = true;\n'
        '    currentUrl.searchParams.set("_iol_v", serverVersion);\n'
        '    currentUrl.searchParams.set("_iol_cb", Date.now().toString());\n'
        '    window.location.replace(currentUrl.toString());\n'
        '  }\n\n'
        '  window.fetch = (...args) => nativeFetch(...args).then((response) => {\n'
        '    try { maybeReloadForVersion(response); } catch (_error) {}\n'
        '    return response;\n'
        '  });\n'
        '})();\n'
        '</script>'
    )
    return html.replace(marker, script + "\n" + marker, 1)


class LocalApiServer:
    def __init__(self, db: Database, host: str = "127.0.0.1", port: int = 8765):
        self.db = db
        self.host = host
        self.port = int(port)
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.last_error: str = ""
        self._auction_lots_runtime_lock = threading.Lock()
        self._auction_lots_runtime = {
            "mode": "max_amount",
            "auto_scroll": False,
        }

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive() and self._httpd)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def set_auction_lots_runtime(
        self,
        *,
        mode: str | None = None,
        auto_scroll: bool | None = None,
    ) -> None:
        with self._auction_lots_runtime_lock:
            if mode in {"max_amount", "weighted_wheel"}:
                self._auction_lots_runtime["mode"] = str(mode)
            if auto_scroll is not None:
                self._auction_lots_runtime["auto_scroll"] = bool(auto_scroll)

    def auction_lots_runtime(self) -> dict[str, object]:
        with self._auction_lots_runtime_lock:
            return dict(self._auction_lots_runtime)

    def start(self) -> None:
        if self.running:
            return
        db = self.db
        api_server = self
        overlay_path = Path(__file__).resolve().parent / "web" / "overlay.html"
        list_overlay_path = Path(__file__).resolve().parent / "web" / "list_overlay.html"
        wheel_overlay_path = Path(__file__).resolve().parent / "web" / "wheel_overlay.html"
        rules_overlay_path = Path(__file__).resolve().parent / "web" / "rules_overlay.html"
        timer_overlay_path = Path(__file__).resolve().parent / "web" / "timer_overlay.html"
        auction_lots_overlay_path = (
            Path(__file__).resolve().parent / "web" / "auction_lots_overlay.html"
        )
        # Static HTML does not change while the program is running. Read once
        # instead of hitting disk for every browser-source navigation/refresh.
        overlay_html = _inject_overlay_version_handshake(
            overlay_path.read_text(encoding="utf-8"), APP_VERSION
        )
        list_overlay_html = _inject_overlay_version_handshake(
            list_overlay_path.read_text(encoding="utf-8"), APP_VERSION
        )
        wheel_overlay_html = _inject_overlay_version_handshake(
            wheel_overlay_path.read_text(encoding="utf-8"), APP_VERSION
        )
        rules_overlay_html = _inject_overlay_version_handshake(
            rules_overlay_path.read_text(encoding="utf-8"), APP_VERSION
        )
        timer_overlay_html = _inject_overlay_version_handshake(
            timer_overlay_path.read_text(encoding="utf-8"), APP_VERSION
        )
        auction_lots_overlay_html = _inject_overlay_version_handshake(
            auction_lots_overlay_path.read_text(encoding="utf-8"), APP_VERSION
        )
        data_root = db.path.parent
        background_dir = managed_media_directory(
            data_root, MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
        )
        background_dir.mkdir(parents=True, exist_ok=True)

        class Handler(BaseHTTPRequestHandler):
            server_version = f"StreamingManagerLocalAPI/{APP_VERSION}"

            def _send_json(
                self,
                payload: object,
                status: int = 200,
                pretty: bool = False,
            ) -> None:
                dump_kwargs = {
                    "ensure_ascii": False,
                    "indent": 2 if pretty else None,
                }
                if not pretty:
                    # Browser Sources poll these endpoints continuously. Compact
                    # JSON is semantically identical and reduces both encoder
                    # work and bytes copied through localhost.
                    dump_kwargs["separators"] = (",", ":")
                body = json.dumps(payload, **dump_kwargs).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Expose-Headers", OVERLAY_VERSION_HEADER)
                self.send_header(OVERLAY_VERSION_HEADER, APP_VERSION)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def _send_html(self, text: str, status: int = 200) -> None:
                body = text.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header(OVERLAY_VERSION_HEADER, APP_VERSION)
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.end_headers()
                self.wfile.write(body)

            def _send_local_media_path(
                self,
                target: Path,
                *,
                allowed_extensions: frozenset[str],
                not_found_error: str,
                unsupported_error: str,
                head_only: bool = False,
            ) -> None:
                ext = target.suffix.lower()
                if ext not in allowed_extensions:
                    self._send_json({"error": unsupported_error}, 415)
                    return

                try:
                    size = target.stat().st_size
                except OSError:
                    self._send_json({"error": not_found_error}, 404)
                    return

                start = 0
                end = max(0, size - 1)
                status = 200
                range_header = self.headers.get("Range", "").strip()

                # Chromium/OBS requests video in byte ranges.  The same guarded
                # local-serving path is shared by managed copies and registered
                # external references; no external filesystem path appears in
                # the URL.
                if range_header.startswith("bytes=") and size > 0:
                    range_value = range_header[6:].split(",", 1)[0].strip()
                    try:
                        left, right = range_value.split("-", 1)
                        if left:
                            start = int(left)
                            end = int(right) if right else size - 1
                        elif right:
                            suffix_length = int(right)
                            if suffix_length <= 0:
                                raise ValueError
                            start = max(0, size - suffix_length)
                            end = size - 1
                        else:
                            raise ValueError
                        if start < 0 or start >= size or end < start:
                            raise ValueError
                        end = min(end, size - 1)
                        status = 206
                    except (ValueError, TypeError):
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{size}")
                        self.send_header("Accept-Ranges", "bytes")
                        self.send_header("Cache-Control", "no-store")
                        self.end_headers()
                        return

                length = 0 if size == 0 else end - start + 1
                content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                if status == 206:
                    self.send_header(
                        "Content-Range",
                        f"bytes {start}-{end}/{size}",
                    )
                self.send_header("Cache-Control", "no-store")
                self.end_headers()

                if head_only or length <= 0:
                    return

                try:
                    with target.open("rb") as file:
                        file.seek(start)
                        remaining = length
                        while remaining > 0:
                            chunk = file.read(min(256 * 1024, remaining))
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            remaining -= len(chunk)
                except (OSError, BrokenPipeError, ConnectionResetError):
                    # OBS can close an obsolete request immediately after media
                    # is changed.  This is not a server/application failure.
                    return

            def _send_background_file(
                self,
                filename: str,
                head_only: bool = False,
            ) -> None:
                # Legacy pre-W2 route: only one basename directly from the
                # dedicated managed overlay-background directory.
                decoded = unquote(filename)
                if not decoded or Path(decoded).name != decoded:
                    self._send_json({"error": "invalid_background_path"}, 400)
                    return
                self._send_local_media_path(
                    background_dir / decoded,
                    allowed_extensions=supported_media_extensions(
                        MEDIA_CATEGORY_OVERLAY_BACKGROUNDS
                    ),
                    not_found_error="background_not_found",
                    unsupported_error="unsupported_background_type",
                    head_only=head_only,
                )

            def _send_registered_media(
                self,
                asset_id_text: str,
                head_only: bool = False,
            ) -> None:
                if not asset_id_text.isdigit():
                    self._send_json({"error": "invalid_media_id"}, 400)
                    return
                asset = db.get_media_asset(int(asset_id_text))
                if asset is None:
                    self._send_json({"error": "media_not_found"}, 404)
                    return
                try:
                    target = resolve_media_asset_path(data_root, asset)
                    allowed_extensions = supported_media_extensions(asset.category)
                except (OSError, ValueError):
                    self._send_json({"error": "media_unavailable"}, 404)
                    return
                if not is_supported_media_name(asset.category, target.name):
                    self._send_json({"error": "unsupported_media_type"}, 415)
                    return
                self._send_local_media_path(
                    target,
                    allowed_extensions=allowed_extensions,
                    not_found_error="media_unavailable",
                    unsupported_error="unsupported_media_type",
                    head_only=head_only,
                )

            def do_HEAD(self):
                parsed = urlparse(self.path)
                media_prefix = "/media/"
                if parsed.path.startswith(media_prefix):
                    self._send_registered_media(
                        parsed.path[len(media_prefix):],
                        head_only=True,
                    )
                    return
                background_prefix = "/overlay-background/"
                if parsed.path.startswith(background_prefix):
                    self._send_background_file(
                        parsed.path[len(background_prefix):],
                        head_only=True,
                    )
                    return
                self.send_response(404)
                self.end_headers()

            def do_OPTIONS(self):
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def do_GET(self):
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/") or "/"
                query = parse_qs(parsed.query)
                pretty = str(query.get("pretty", ["0"])[0]).lower() in (
                    "1", "true", "yes", "on"
                )

                if path in ("/overlay", "/obs-overlay"):
                    try:
                        self._send_html(overlay_html)
                    except OSError as exc:
                        self._send_html(
                            "<h1>Overlay unavailable</h1><pre>"
                            + str(exc)
                            + "</pre>",
                            status=500,
                        )
                    return

                if path in ("/list-overlay", "/obs-list", "/overlay/list"):
                    try:
                        self._send_html(list_overlay_html)
                    except OSError as exc:
                        self._send_html(
                            "<h1>List overlay unavailable</h1><pre>"
                            + str(exc)
                            + "</pre>",
                            status=500,
                        )
                    return

                if path in ("/wheel-overlay", "/obs-wheel", "/overlay/wheel"):
                    try:
                        self._send_html(wheel_overlay_html)
                    except OSError as exc:
                        self._send_html(
                            "<h1>Wheel overlay unavailable</h1><pre>"
                            + str(exc)
                            + "</pre>",
                            status=500,
                        )
                    return

                if path in (
                    "/auction-lots-overlay",
                    "/obs-auction-lots",
                    "/overlay/auction-lots",
                ):
                    try:
                        self._send_html(auction_lots_overlay_html)
                    except OSError as exc:
                        self._send_html(
                            "<h1>Auction lots overlay unavailable</h1><pre>"
                            + str(exc)
                            + "</pre>",
                            status=500,
                        )
                    return

                if path in ("/rules-overlay", "/obs-rules", "/overlay/rules"):
                    try:
                        self._send_html(rules_overlay_html)
                    except OSError as exc:
                        self._send_html(
                            "<h1>Rules overlay unavailable</h1><pre>"
                            + str(exc)
                            + "</pre>",
                            status=500,
                        )
                    return

                if path in ("/timer-overlay", "/obs-timer", "/overlay/timer"):
                    try:
                        self._send_html(timer_overlay_html)
                    except OSError as exc:
                        self._send_html(
                            "<h1>Timer overlay unavailable</h1><pre>"
                            + str(exc)
                            + "</pre>",
                            status=500,
                        )
                    return

                media_prefix = "/media/"
                if parsed.path.startswith(media_prefix):
                    self._send_registered_media(parsed.path[len(media_prefix):])
                    return

                background_prefix = "/overlay-background/"
                if parsed.path.startswith(background_prefix):
                    self._send_background_file(
                        parsed.path[len(background_prefix):]
                    )
                    return

                if path in ("/health", "/api/health"):
                    self._send_json(
                        {
                            "ok": True,
                            "service": "In one line",
                            "version": APP_VERSION,
                        },
                        pretty=pretty,
                    )
                    return
                if path in ("/api/data", "/data"):
                    self._send_json(db.current_stream_payload(), pretty=pretty)
                    return
                if path in ("/api/public", "/public"):
                    self._send_json(
                        {"games": db.public_games()},
                        pretty=pretty,
                    )
                    return
                if path in ("/api/pointauc", "/pointauc"):
                    self._send_json(
                        {
                            "games": [
                                {"id": g.id, "title": g.title, "sm_points": g.sm_points, "sum": g.sm_points}
                                for g in db.pointauc_games()
                            ]
                        },
                        pretty=pretty,
                    )
                    return
                if path in ("/api/wheel", "/wheel"):
                    self._send_json(
                        db.current_wheel_payload(),
                        pretty=pretty,
                    )
                    return

                if path in ("/api/auction-lots", "/auction-lots"):
                    self._send_json(
                        db.current_auction_lots_payload(
                            api_server.auction_lots_runtime()
                        ),
                        pretty=pretty,
                    )
                    return

                if path in ("/api/timer", "/timer"):
                    self._send_json(
                        db.current_timer_payload(),
                        pretty=pretty,
                    )
                    return

                if path in ("/api/rules", "/rules"):
                    self._send_json(
                        db.current_rules_payload(),
                        pretty=pretty,
                    )
                    return
                self._send_json({"error": "not_found"}, 404)

            def log_message(self, format: str, *args) -> None:
                return

        try:
            self._httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        except OSError as exc:
            self.last_error = str(exc)
            self._httpd = None
            raise
        self._thread = threading.Thread(target=self._httpd.serve_forever, name="StreamingManagerAPI", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._httpd = None
        self._thread = None
