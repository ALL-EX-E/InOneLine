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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTextEdit
from PySide6.QtGui import QColor, QTextCursor

from streaming_manager.database import Database
from streaming_manager.constants import (
    RULES_OVERLAY_BACKGROUND_KEY,
    RULES_OVERLAY_BACKGROUND_COLOR_KEY,
    RULES_OVERLAY_BACKGROUND_OPACITY_KEY,
    RULES_OVERLAY_PADDING_KEY,
)
from streaming_manager.views.rules_editor import AuctionRulesEditorDialog
from streaming_manager.media import MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, managed_media_directory
from PySide6.QtGui import QImage



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
            assert not hasattr(dialog, "rules_obs_padding")
            assert dialog._responsive_rules_padding(320, 180) == 8.0
            assert dialog._responsive_rules_padding(1200, 1000) == 22.0
            assert dialog._responsive_rules_padding(2000, 1500) == 24.0
            assert editor.document().documentMargin() == dialog._responsive_rules_padding(
                editor.viewport().width(), editor.viewport().height()
            )
            assert editor.document().documentMargin() < 37.0
            assert editor.isReadOnly() is False
            assert dialog._is_dirty() is False
            assert "border-radius: 8px" in editor.viewport().styleSheet()
            assert dialog._rules_glow_effect.isEnabled() is False
            dialog.rules_obs_glow.setChecked(True)
            dialog._set_color_button(
                dialog.rules_obs_glow_color_btn, QColor("#1188CC"), "Цвет контура"
            )
            dialog._editor_changed()
            app.processEvents()
            assert dialog._rules_glow_effect.isEnabled() is True
            assert dialog._rules_glow_effect.color().blue() == 204
            assert "border-radius: 8px" in editor.viewport().styleSheet()
            assert editor.toHtml() == initial_html
            assert db.get_rule_template_presentation(active) is None
            dialog.rules_obs_glow.setChecked(False)
            app.processEvents()
            assert dialog._rules_glow_effect.isEnabled() is False
            assert dialog.rules_editor_splitter.count() == 2
            assert dialog.rules_editor_splitter.orientation() == Qt.Horizontal
            assert editor.isVisible() and dialog.rules_obs_page.isVisible()
            assert editor.document().documentMargin() == dialog._responsive_rules_padding(
                editor.viewport().width(), editor.viewport().height()
            )
            dialog.resize(800, 680)
            app.processEvents()
            assert dialog.rules_editor_splitter.orientation() == Qt.Vertical
            assert editor.isVisible() and dialog.rules_obs_page.isVisible()
            assert editor.document().documentMargin() == dialog._responsive_rules_padding(
                editor.viewport().width(), editor.viewport().height()
            )
            dialog.resize(1100, 760)
            app.processEvents()
            assert dialog.rules_editor_splitter.orientation() == Qt.Horizontal
            assert editor.isVisible() and dialog.rules_obs_page.isVisible()
            assert editor.document().documentMargin() == dialog._responsive_rules_padding(
                editor.viewport().width(), editor.viewport().height()
            )

            dialog.rules_obs_opacity.setValue(80)
            app.processEvents()
            assert "rgba(18, 52, 86, 204)" in editor.viewport().styleSheet()
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
            assert editor.document().documentMargin() == dialog._responsive_rules_padding(
                editor.viewport().width(), editor.viewport().height()
            )
            assert editor.toPlainText().strip() == "Другие правила"
            assert dialog._is_dirty() is False
            assert db.current_rules_payload()["source"] == "active_template"
            assert db.get_active_rule_template()["id"] == active

            # K8A: existing shared-library image is selected without a second
            # imported asset, saved model or modified underlying HTML.
            media_dir = managed_media_directory(db.path.parent, MEDIA_CATEGORY_OVERLAY_BACKGROUNDS)
            media_dir.mkdir(parents=True, exist_ok=True)
            image_file = media_dir / "rules_k8a_preview.png"
            image = QImage(16, 16, QImage.Format_RGB32)
            image.fill(QColor("#3377BB"))
            assert image.save(str(image_file))
            asset = db.ensure_managed_media_asset(
                MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, image_file.name, image_file.name
            )
            dialog._refresh_rules_media_library(asset.id)
            assert dialog.rules_obs_media_combo.currentData() == asset.id
            dialog.rules_obs_media_mode.setChecked(True)
            app.processEvents()
            local_style = editor.viewport().styleSheet()
            assert "background: palette(base)" in local_style
            assert dialog._rules_media_source_key is not None
            assert dialog._rules_media_source_key[0] == str(image_file)
            assert not editor.viewport().palette().brush(
                __import__("PySide6.QtGui", fromlist=["QPalette"]).QPalette.Base
            ).texture().isNull(), "Missing native Qt background pixmap brush"
            snapshot = editor.viewport().grab().toImage()
            point = snapshot.pixelColor(
                snapshot.width() // 2, snapshot.height() * 3 // 4,
            )
            assert (abs(point.red() - 51) < 6
                    and abs(point.green() - 119) < 6
                    and abs(point.blue() - 187) < 6), (
                f"Qt text editor is not actually painting its image: {point.name()}"
            )
            # Refresh from the library must repaint instantly without Save.
            dialog.rules_obs_media_refresh.click()
            app.processEvents()
            assert dialog._rules_media_source_key[0] == str(image_file)
            assert editor.toHtml() == inactive_html
            assert editor.toPlainText().strip() == "Другие правила"
            assert dialog._is_dirty() is True
            assert db.get_rule_template_presentation(inactive)["background"] == "transparent"
            assert db.get_active_rule_template()["id"] == active
            # Existing content and live template are unaffected before Save.
            dialog.rules_obs_transparent.setChecked(True)
            app.processEvents()
            assert "background: palette(base)" not in editor.viewport().styleSheet()
            assert dialog._rules_media_source_key is None
        finally:
            with patch.object(dialog, "_confirm_discard_or_save", return_value=True):
                dialog.close()
            dialog.deleteLater()
            app.processEvents()

    print("P11_K6_RULES_EDITABLE_BACKGROUND_AND_RESPONSIVE_INSET_QT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
