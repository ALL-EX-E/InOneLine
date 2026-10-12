"""P11-K2: persisted per-template Rules appearance and auction source-sync tests.

No user interface or OBS renderer appearance is switched in this increment.
"""
from __future__ import annotations

import tempfile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streaming_manager.constants import (
    STATUS_PLAYED,
    STATUS_NOT_PLAYED,
    RULES_OVERLAY_AUTOSCROLL_KEY,
    RULES_OVERLAY_BACKGROUND_KEY,
    RULES_OVERLAY_BACKGROUND_COLOR_KEY,
    RULES_OVERLAY_BACKGROUND_OPACITY_KEY,
    RULES_OVERLAY_PADDING_KEY,
)
from streaming_manager.database import Database, Game


def main() -> int:
    style_a = {
        "autoscroll": False, "background": "color",
        "background_color": "#1122aa", "background_opacity": 68, "padding": 17,
    }
    style_a2 = {**style_a, "padding": 53}
    style_b = {
        "autoscroll": True, "background": "transparent",
        "background_color": "#ABCDE0", "background_opacity": 0, "padding": 24,
    }
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "rules_access.db")
        a = int(db.get_active_rule_template()["id"])
        b = db.create_rule_template(
            "P11-K2 inactive rules", content_html="<p>Other Rules</p>",
            make_active=False,
        )
        db.save_rule_template(a, "<p>Original Rules</p>")
        db.set_settings_bulk({
            RULES_OVERLAY_AUTOSCROLL_KEY: "1",
            RULES_OVERLAY_BACKGROUND_KEY: "color",
            RULES_OVERLAY_BACKGROUND_COLOR_KEY: "#654321",
            RULES_OVERLAY_BACKGROUND_OPACITY_KEY: "40",
            RULES_OVERLAY_PADDING_KEY: "49",
        })
        before = db.current_rules_payload()
        assert db.get_rule_template_presentation(a) is None
        assert db.get_rule_template_presentation(b) is None
        db.save_rule_template_presentation(a, style_a)
        db.save_rule_template_presentation(b, style_b)
        assert db.get_rule_template_presentation(a) == {
            **style_a, "background_color": "#1122AA"
        }
        assert db.get_rule_template_presentation(b) == style_b
        assert db.current_rules_payload() == before, "saved style leaked to OBS"

        # Strict field/value checking and atomic failure.
        for invalid in (
            {},
            {**style_a, "unexpected": "hidden"},
            {**style_a, "padding": True},
            {**style_a, "background_opacity": 101},
            {**style_a, "background_color": "#ZZZZZZ"},
            {**style_a, "autoscroll": "yes"},
        ):
            try:
                db.save_rule_template_presentation(a, invalid)
            except ValueError:
                pass
            else:
                raise AssertionError(f"accepted invalid Rules presentation: {invalid!r}")
        assert db.get_rule_template_presentation(a)["padding"] == 17
        try:
            db.save_rule_template_presentation(-123, style_a)
        except ValueError:
            pass
        else:
            raise AssertionError("missing template accepted")
        assert db.current_rules_payload() == before

        db.add_game(Game(None, "K2 Lot A", "2026-01-01", 100, 0, STATUS_PLAYED, ""))
        db.add_game(Game(None, "K2 Lot B", "2026-01-01", 200, 0, STATUS_NOT_PLAYED, ""))
        auction_id = db.create_auction_session("max_amount", 60)
        assert db.get_auction_rules_presentation_snapshot(auction_id) == {
            **style_a, "background_color": "#1122AA"
        }, "new session did not capture active template appearance"
        assert db.current_rules_payload()["source"] == "auction_snapshot"
        assert db.current_rules_payload()["presentation"] == before["presentation"]

        # Inactive source cannot change on-air session appearance.
        db.save_rule_template_presentation(b, {**style_b, "padding": 81})
        assert db.get_auction_rules_presentation_snapshot(auction_id)["padding"] == 17
        # Saving live source style mirrors the current session.
        db.save_rule_template_presentation(a, style_a2)
        db.save_rule_template_presentation(a, style_a2)  # idempotent Save: no extra audit
        assert db.get_auction_rules_presentation_snapshot(auction_id)["padding"] == 53
        db.set_active_rule_template(b)
        assert db.get_auction_rules_presentation_snapshot(auction_id)["padding"] == 81
        assert db.get_auction_rules_snapshot(auction_id)["template_id"] == b
        assert "Other Rules" in db.current_rules_payload()["content_html"]
        assert db.current_rules_payload()["presentation"] == before["presentation"]

        # Resetting explicit style retains the same legacy global fallback.
        db.save_rule_template_presentation(b, None)
        assert db.get_rule_template_presentation(b) is None
        assert db.get_auction_rules_presentation_snapshot(auction_id) is None
        assert db.current_rules_payload()["presentation"] == before["presentation"]

        # History is immutable after the session is closed.
        with db.connect() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM change_log WHERE entity_type='auction_session'"
                " AND entity_id=? AND action='sync_rules_presentation'",
                (auction_id,),
            ).fetchone()[0]
            assert count == 2, count
            conn.execute(
                "UPDATE auction_sessions SET status='cancelled' WHERE id=?",
                (auction_id,),
            )
        closed = db.get_auction_rules_snapshot(auction_id)
        db.set_active_rule_template(a)
        db.save_rule_template_presentation(a, style_a)
        assert db.get_auction_rules_snapshot(auction_id) == closed
        assert db.get_auction_rules_presentation_snapshot(auction_id) is None

        # Bad legacy JSON must not crash DB readers or contaminate live OBS.
        with db.connect() as conn:
            conn.execute(
                "UPDATE auction_rule_templates SET presentation_json='not-json' WHERE id=?",
                (a,),
            )
        assert db.get_rule_template_presentation(a) is None
        assert db.current_rules_payload()["presentation"] == before["presentation"]
        db.save_rule_template_presentation(a, style_a)
        assert db.get_rule_template_presentation(a)["padding"] == 17
        Database(db.path)  # idempotent reopen preserves valid customization
        assert db.get_rule_template_presentation(a)["padding"] == 17

    print("P11_K2_RULES_PRESENTATION_TEMPLATE_SESSION_SYNC_NO_OBS_SWITCH=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
