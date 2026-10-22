"""P11-K8B: the modal Rules editor reuses Stream/OBS's single media importer.

This test verifies managed/external promotion and shared filename dedup without
a second import implementation, duplicate assets or an unintended on-air Save.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from streaming_manager.api_server import LocalApiServer
from streaming_manager.database import Database
from streaming_manager.media import (
    MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, MEDIA_STORAGE_EXTERNAL,
    MEDIA_STORAGE_MANAGED, media_asset_available,
)
from streaming_manager.views.rules_editor import AuctionRulesEditorDialog
from streaming_manager.views.stream import StreamTab


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        db = Database(root / "data" / "app.db")
        server = LocalApiServer(db, port=0)
        stream = StreamTab(db, server)
        editor = AuctionRulesEditorDialog(
            db, import_background=stream.import_rules_background_media
        )
        try:
            stream.show()
            editor.show()
            app.processEvents()
            assert editor.rules_obs_media_add.isEnabled() is False
            editor.rules_obs_media_mode.setChecked(True)
            app.processEvents()
            assert editor.rules_obs_media_add.isEnabled()
            assert editor.rules_obs_media_add.text() == "Добавить фон…"
            active = int(db.get_active_rule_template()["id"])
            original_presentation = db.get_rule_template_presentation(active)
            original_settings = db.get_settings([
                "overlay_background_media_id",
                "auction_lots_overlay_background_media_id",
                "timer_overlay_background_media_id",
            ])
            original_main_selection = stream.background_combo.currentData()
            source = root / "rules-k8b-shared.png"
            image = QImage(12, 12, QImage.Format_RGB32)
            image.fill(QColor("#44AA55"))
            assert image.save(str(source))

            # Original shared managed/external choice, including source-file
            # reference, works inside modal Rules editor rather than Stream.
            with (
                patch.object(QFileDialog, "getOpenFileNames",
                             return_value=([str(source)], "Изображения")) as picker,
                patch.object(stream, "_choose_background_storage_mode",
                             return_value=MEDIA_STORAGE_EXTERNAL) as storage,
            ):
                editor.rules_obs_media_add.click()
            assert picker.call_args.args[0] is editor
            assert storage.call_args.kwargs.get("dialog_parent") is editor
            matches = db.media_assets_by_filename(
                MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, source.name
            )
            assert len(matches) == 1 and matches[0].storage_mode == MEDIA_STORAGE_EXTERNAL
            ident = matches[0].id
            assert editor.rules_obs_media_combo.currentData() == ident
            assert editor.rules_obs_media_mode.isChecked()
            assert editor._is_dirty() is True
            assert editor._obs_presentation_values()["background_media_id"] == ident
            assert db.get_rule_template_presentation(active) == original_presentation
            assert stream.background_combo.currentData() == original_main_selection
            assert db.get_settings(list(original_settings)) == original_settings
            assert db.get_active_rule_template()["id"] == active

            # Repeated same-name import reuses existing ID; selecting managed
            # promotes the external row without duplicating it or changing
            # any other widget's saved media settings.
            with (
                patch.object(QFileDialog, "getOpenFileNames",
                             return_value=([str(source)], "Изображения")),
                patch.object(stream, "_choose_background_storage_mode",
                             return_value=MEDIA_STORAGE_MANAGED),
                patch.object(QMessageBox, "information"),
            ):
                editor.rules_obs_media_add.click()
            promoted = db.get_media_asset(ident)
            assert promoted is not None
            assert promoted.storage_mode == MEDIA_STORAGE_MANAGED
            assert media_asset_available(db.path.parent, promoted)
            assert len(db.media_assets_by_filename(
                MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, source.name
            )) == 1
            assert editor.rules_obs_media_combo.currentData() == ident
            source.unlink()
            assert media_asset_available(db.path.parent, promoted)

            # Cancel and invalid GIF fail closed, do not create a row or touch
            # selected/stored settings. Animated sources come in a later K8.
            with patch.object(QFileDialog, "getOpenFileNames",
                              return_value=("", "")):
                editor.rules_obs_media_add.click()
            unsupported = root / "not-yet-supported.gif"
            unsupported.write_bytes(b"GIF89a")
            with (
                patch.object(QFileDialog, "getOpenFileNames",
                             return_value=(str(unsupported), "Все файлы")),
                patch.object(QMessageBox, "warning") as warning,
            ):
                editor.rules_obs_media_add.click()
                assert warning.call_count == 1
            assert editor.rules_obs_media_combo.currentData() == ident
            assert db.get_rule_template_presentation(active) == original_presentation
            assert db.get_settings(list(original_settings)) == original_settings
            assert not db.media_assets_by_filename(
                MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, unsupported.name
            )
        finally:
            with patch.object(editor, "_confirm_discard_or_save", return_value=True):
                editor.close()
            stream.close()
            editor.deleteLater()
            stream.deleteLater()
            app.processEvents()
            server.stop()
    print("P11_K8B_SHARED_RULES_MODAL_BACKGROUND_IMPORT_MANAGED_EXTERNAL_DEDUP=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
