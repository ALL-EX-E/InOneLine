"""P11-K3: Qt Rules editor owns appearance, common Save, legacy fallback.

This uses the real editor and Database, with no OBS route or second UI state.
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

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QInputDialog, QLabel
from streaming_manager.database import Database
from streaming_manager.views.rules_editor import AuctionRulesEditorDialog
from streaming_manager.constants import (
    RULES_OVERLAY_AUTOSCROLL_KEY, RULES_OVERLAY_BACKGROUND_KEY,
    RULES_OVERLAY_BACKGROUND_COLOR_KEY, RULES_OVERLAY_BACKGROUND_OPACITY_KEY,
    RULES_OVERLAY_PADDING_KEY,
)


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "rules_editor_k3.db")
        active = int(db.get_active_rule_template()["id"])
        db.save_rule_template(active, "")
        db.set_settings_bulk({
            RULES_OVERLAY_AUTOSCROLL_KEY: "0",
            RULES_OVERLAY_BACKGROUND_KEY: "color",
            RULES_OVERLAY_BACKGROUND_COLOR_KEY: "#123456",
            RULES_OVERLAY_BACKGROUND_OPACITY_KEY: "35",
            RULES_OVERLAY_PADDING_KEY: "37",
        })
        original_settings = db.get_settings()
        inactive = db.create_rule_template(
            "P11-K3 Другой шаблон",
            content_html="",
            make_active=False,
        )
        url = "http://127.0.0.1:8765/rules-overlay"
        dialog = AuctionRulesEditorDialog(
            db, initial_template_id=active, rules_overlay_url=lambda: url,
        )
        try:
            dialog.show()
            app.processEvents()
            assert dialog.rules_editor_splitter.count() == 2
            assert dialog.rules_editor_splitter.widget(0) is dialog.rules_text_page
            assert dialog.rules_editor_splitter.widget(1) is dialog.rules_obs_scroll
            assert dialog.rules_obs_scroll.widget() is dialog.rules_obs_page
            assert dialog.rules_obs_color_btn is not None
            assert not hasattr(dialog, "rules_obs_padding")
            assert not any(label.text() == "Внутренний отступ:"
                           for label in dialog.findChildren(QLabel))
            assert dialog._loaded_template_id == active
            assert db.get_rule_template_presentation(active) is None
            assert dialog._obs_presentation_values() == {
                "autoscroll": False,
                "background": "color",
                "background_color": "#123456",
                "background_opacity": 35,
                "padding": 37,
            }
            assert dialog._is_dirty() is False
            dialog.rules_obs_opacity.setValue(81)
            dialog.rules_obs_autoscroll.setChecked(True)
            dialog._set_color_button(
                dialog.rules_obs_color_btn, QColor("#554433"), "Цвет фона"
            )
            dialog._editor_changed()
            app.processEvents()
            assert dialog._is_dirty() is True
            with patch.object(dialog, "_choose_save_action", return_value="replace"):
                assert dialog._save_with_choice()
            assert not dialog._is_dirty()
            saved = db.get_rule_template_presentation(active)
            assert saved is not None
            assert saved["padding"] == 37 and saved["background_opacity"] == 81
            assert saved["background_color"] == "#554433"
            assert saved["autoscroll"] is True
            assert db.get_settings() == original_settings
            assert db.current_rules_payload()["presentation"] == saved

            # Independent inactive template inherits same old global Rules
            # settings until explicitly saved; no accidental style copy.
            dialog._reload_templates(selected_id=inactive)
            assert dialog._obs_presentation_values()["padding"] == 37
            assert db.get_rule_template_presentation(inactive) is None
            assert dialog._is_dirty() is False
            dialog.rules_obs_opacity.setValue(47)
            app.processEvents()
            assert dialog._is_dirty()
            with patch.object(dialog, "_confirm_discard_or_save", return_value=False):
                dialog.template_combo.setCurrentIndex(
                    dialog.template_combo.findData(active)
                )
            assert dialog._loaded_template_id == inactive
            assert dialog._is_dirty()
            assert dialog.template_combo.currentData() == inactive

            with patch.object(dialog, "_choose_save_action", return_value="replace"):
                assert dialog._save_with_choice()
            assert db.get_rule_template_presentation(inactive)["background_opacity"] == 47
            assert db.get_rule_template_presentation(active)["background_opacity"] == 81

            # Saving a copy preserves appearance without making it active.
            dialog.rules_obs_opacity.setValue(69)
            with patch.object(dialog, "_choose_save_action", return_value="new"), patch.object(
                QInputDialog, "getText", return_value=("P11-K3 копия", True)
            ):
                assert dialog._save_with_choice()
            copied = int(dialog._loaded_template_id)
            assert copied not in (active, inactive)
            assert db.get_rule_template_presentation(copied)["background_opacity"] == 69
            assert db.get_active_rule_template()["id"] == active
            assert db.get_rule_template_presentation(inactive)["background_opacity"] == 47

            db.set_active_rule_template(copied)
            assert db.current_rules_payload()["presentation"]["background_opacity"] == 69
            assert db.get_settings() == original_settings
            db.save_rule_template_presentation(copied, None)
            assert db.current_rules_payload()["presentation"]["padding"] == 37
        finally:
            with patch.object(dialog, "_confirm_discard_or_save", return_value=True):
                dialog.close()
            dialog.deleteLater()
            app.processEvents()

    print("P11_K3_RULES_EDITOR_COMPOSITE_STYLE_SAVE_FALLBACK_QT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
