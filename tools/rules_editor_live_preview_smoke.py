"""P11-K5: existing Rules OBS paint settings must follow the editable Qt document.

The browser remains the independent saved-state preview; this view never writes
the database or changes active/current-auction Rules.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QTextEdit
from PySide6.QtGui import QTextCursor

from streaming_manager.database import Database
from streaming_manager.constants import (
    RULES_OVERLAY_BACKGROUND_KEY,
    RULES_OVERLAY_BACKGROUND_COLOR_KEY,
    RULES_OVERLAY_BACKGROUND_OPACITY_KEY,
    RULES_OVERLAY_PADDING_KEY,
)
from streaming_manager.views.rules_editor import AuctionRulesEditorDialog


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "rules_k5_live_preview.db")
        active = int(db.get_active_rule_template()["id"])
        # The app stores QTextEdit.toHtml() on Save; use the same canonical Qt
        # serialization rather than a manually typed <p> string as baseline.
        fixture_editor = QTextEdit()
        fixture_editor.setHtml("<p>Проверка <b>редактируемого</b> текста</p>")
        db.save_rule_template(active, fixture_editor.toHtml())
        fixture_editor.setHtml("<p>Другие правила</p>")
        inactive_html = fixture_editor.toHtml()
        fixture_editor.deleteLater()
        inactive = db.create_rule_template(
            "Другой стиль", content_html=inactive_html, make_active=False
        )
        db.save_rule_template_presentation(inactive, {
            "autoscroll": False,
            "background": "transparent",
            "background_color": "#ABCDEF",
            "background_opacity": 99,
            "padding": 14,
        })
        db.set_settings_bulk({
            RULES_OVERLAY_BACKGROUND_KEY: "color",
            RULES_OVERLAY_BACKGROUND_COLOR_KEY: "#123456",
            RULES_OVERLAY_BACKGROUND_OPACITY_KEY: "35",
            RULES_OVERLAY_PADDING_KEY: "37",
        })
        saved_active = dict(db.get_rule_template(active))
        original_settings = db.get_settings()
        dialog = AuctionRulesEditorDialog(
            db, initial_template_id=active,
            rules_overlay_url=lambda: "http://127.0.0.1:8765/rules-overlay",
        )
        try:
            dialog.show()
            app.processEvents()
            editor = dialog.editor
            initial_html = editor.toHtml()
            assert "rgba(18, 52, 86, 89)" in editor.viewport().styleSheet()
            assert editor.document().documentMargin() == 37.0
            assert editor.isReadOnly() is False
            assert dialog._is_dirty() is False

            dialog.rules_obs_opacity.setValue(80)
            app.processEvents()
            assert "rgba(18, 52, 86, 204)" in editor.viewport().styleSheet()
            dialog.rules_obs_padding.setValue(51)
            app.processEvents()
            assert editor.document().documentMargin() == 51.0
            dialog.rules_obs_transparent.setChecked(True)
            app.processEvents()
            assert "background-color: transparent" in editor.viewport().styleSheet()
            dialog.rules_obs_color_mode.setChecked(True)
            app.processEvents()
            assert "rgba(18, 52, 86, 204)" in editor.viewport().styleSheet()

            # Background changes alter the VIEW only, never serialized HTML.
            assert editor.toHtml() == initial_html
            assert db.get_rule_template_presentation(active) is None
            assert db.get_rule_template(active) == saved_active
            assert db.get_settings() == original_settings
            assert db.get_active_rule_template()["id"] == active

            editor.moveCursor(QTextCursor.End)
            editor.insertPlainText(" ДОПОЛНЕНО")
            assert "ДОПОЛНЕНО" in editor.toPlainText()
            assert dialog._is_dirty()

            # Loading another template refreshes the same editor in place.
            dialog._load_template(inactive)
            app.processEvents()
            assert "background-color: transparent" in editor.viewport().styleSheet()
            assert editor.document().documentMargin() == 14.0
            assert editor.toPlainText().strip() == "Другие правила"
            assert dialog._is_dirty() is False
            assert db.current_rules_payload()["source"] == "active_template"
            assert db.get_active_rule_template()["id"] == active
        finally:
            with patch.object(dialog, "_confirm_discard_or_save", return_value=True):
                dialog.close()
            dialog.deleteLater()
            app.processEvents()

    print("P11_K5_RULES_EDITABLE_BACKGROUND_OPACITY_INSET_LIVE_PREVIEW_QT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
