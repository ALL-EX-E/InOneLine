"""P11-K4: isolated read-only preview of a selected Rules template.

Protects the current auction's live Rules, normal Browser Sources, global
fallback, invalid input and the single existing Rules renderer/route.
"""
from __future__ import annotations

import json
import socket
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database, Game
from streaming_manager.constants import (
    STATUS_NOT_PLAYED, STATUS_PLAYED,
    RULES_OVERLAY_BACKGROUND_KEY, RULES_OVERLAY_BACKGROUND_COLOR_KEY,
    RULES_OVERLAY_BACKGROUND_OPACITY_KEY, RULES_OVERLAY_PADDING_KEY,
    RULES_OVERLAY_AUTOSCROLL_KEY,
)


def main() -> int:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as root:
        db = Database(Path(root) / "rules_preview.db")
        a = int(db.get_active_rule_template()["id"])
        db.save_rule_template(a, "<p>ON AIR PRIMARY</p>")
        b = db.create_rule_template(
            "Preview-only secondary", content_html="<p>SELECTED INACTIVE</p>",
            make_active=False,
        )
        db.set_settings_bulk({
            RULES_OVERLAY_AUTOSCROLL_KEY: "0",
            RULES_OVERLAY_BACKGROUND_KEY: "color",
            RULES_OVERLAY_BACKGROUND_COLOR_KEY: "#123456",
            RULES_OVERLAY_BACKGROUND_OPACITY_KEY: "45",
            RULES_OVERLAY_PADDING_KEY: "27",
        })
        db.save_rule_template_presentation(
            b,
            {
                "autoscroll": True, "background": "color",
                "background_color": "#ABCDEF",
                "background_opacity": 71, "padding": 63,
            },
        )
        db.add_game(Game(None, "Preview lot one", "2026-01-01", 100, 0, STATUS_PLAYED, ""))
        db.add_game(Game(None, "Preview lot two", "2026-01-01", 200, 0, STATUS_NOT_PLAYED, ""))
        auction_id = db.create_auction_session("max_amount", 60)
        source_before = db.get_auction_rules_snapshot(auction_id)
        settings_before = db.get_settings()
        templates_before = db.list_rule_templates()
        live_before = db.current_rules_payload()
        assert live_before["source"] == "auction_snapshot"
        assert "ON AIR PRIMARY" in live_before["content_html"]
        assert live_before["presentation"]["padding"] == 27

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        server = LocalApiServer(db, port=port)
        server.start()

        def get(path: str) -> tuple[int, dict]:
            try:
                with urlopen(server.base_url + path, timeout=5) as response:
                    return response.status, json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                return error.code, json.loads(error.read().decode("utf-8"))

        try:
            status, active = get("/api/rules")
            assert status == 200 and active == live_before
            status, explicit = get(f"/api/rules?preview=1&template_id={b}")
            assert status == 200 and explicit["source"] == "template_preview"
            assert explicit["auction_id"] is None
            assert explicit["template_name"] == "Preview-only secondary"
            assert "SELECTED INACTIVE" in explicit["content_html"]
            assert "ON AIR PRIMARY" not in explicit["content_html"]
            assert explicit["presentation"]["background_color"] == "#ABCDEF"
            assert explicit["presentation"]["padding"] == 63
            # A browser preview following an editor uses a process-only
            # selector. Every poll resolves the current selection without
            # changing the active template or persisted auction snapshots.
            token = "A_valid_editor_preview_token_123456"
            db.set_rules_preview_selection(token, b)
            status, following = get(f"/api/rules?preview=1&follow_token={token}")
            assert status == 200 and "SELECTED INACTIVE" in following["content_html"]
            db.set_rules_preview_selection(token, a)
            status, following = get(f"/api/rules?preview=1&follow_token={token}")
            assert status == 200 and "ON AIR PRIMARY" in following["content_html"]
            status, normal_token = get(f"/api/rules?follow_token={token}")
            assert status == 200 and normal_token == live_before
            db.clear_rules_preview_selection(token)
            status, expired = get(f"/api/rules?preview=1&follow_token={token}")
            assert status == 404 and expired["error"] == "preview_expired"
            status, invalid = get("/api/rules?preview=1&follow_token=bad")
            assert status == 400 and invalid["error"] == "invalid_preview_token"
            status, fallback = get(f"/api/rules?preview=1&template_id={a}")
            assert status == 200 and fallback["source"] == "template_preview"
            assert fallback["presentation"] == live_before["presentation"]
            assert "ON AIR PRIMARY" in fallback["content_html"]
            # Preview selector is ignored unless it is explicitly marked preview:
            for path in (
                f"/api/rules?template_id={b}",
                f"/api/rules?preview=0&template_id={b}",
                "/api/rules?preview=1",
                f"/rules?template_id={b}",
            ):
                code, normal = get(path)
                assert code == 200 and normal == live_before, (path, normal)
            for value in ("0", "-1", "abc", "1%20%20", "99999999999"):
                code, data = get(f"/api/rules?preview=1&template_id={value}")
                assert code == 400 and data["error"] == "invalid_template_id", value
            code, data = get("/api/rules?preview=1&template_id=9999999999")
            assert code == 404 and data["error"] == "template_not_found"
            # The exact same existing Rules overlay HTML is served to both.
            with urlopen(server.base_url + "/rules-overlay", timeout=5) as a_page:
                default_html = a_page.read()
            with urlopen(
                server.base_url + f"/rules-overlay?preview=1&template_id={b}", timeout=5
            ) as b_page:
                preview_html = b_page.read()
            assert default_html == preview_html, "a second renderer was introduced"
            assert b"/api/rules?preview=1&template_id=" in default_html
        finally:
            server.stop()

        assert db.get_settings() == settings_before
        assert db.get_rule_template_presentation(a) is None
        assert db.list_rule_templates() == templates_before
        assert db.get_auction_rules_snapshot(auction_id) == source_before
        assert db.current_rules_payload() == live_before

    print("P11_K4_SELECTED_RULES_TEMPLATE_READONLY_PREVIEW_NO_ONAIR_CHANGE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
