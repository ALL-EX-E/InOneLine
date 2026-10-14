"""P11-K8C smoke: existing Rules media library drives Qt GIF/video behind QTextEdit."""
from __future__ import annotations

import base64
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
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication
from PySide6.QtMultimedia import QMediaPlayer

from streaming_manager.database import Database
from streaming_manager.media import MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, managed_media_directory
from streaming_manager.views.rules_editor import AuctionRulesEditorDialog


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        db = Database(Path(temp) / "rules_animated.db")
        active = int(db.get_active_rule_template()["id"])
        media_dir = managed_media_directory(db.path.parent, MEDIA_CATEGORY_OVERLAY_BACKGROUNDS)
        media_dir.mkdir(parents=True, exist_ok=True)

        gif = media_dir / "rules_animation.gif"
        gif.write_bytes(base64.b64decode("R0lGODlhAQABAAD/ACwAAAAAAQABAAACAUwAOw=="))
        gif_asset = db.ensure_managed_media_asset(MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, gif.name, gif.name)
        video = media_dir / "rules_silent.webm"
        video.write_bytes((Path(__file__).parent / "fixtures" / "rules_k8c_loop.webm").read_bytes())
        video_asset = db.ensure_managed_media_asset(MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, video.name, video.name)
        still = media_dir / "rules_still.png"
        image = QImage(16, 16, QImage.Format_RGB32)
        image.fill(QColor("#1566AA"))
        assert image.save(str(still))
        still_asset = db.ensure_managed_media_asset(MEDIA_CATEGORY_OVERLAY_BACKGROUNDS, still.name, still.name)

        dialog = AuctionRulesEditorDialog(db, initial_template_id=active)
        try:
            dialog.show()
            app.processEvents()
            initial_html = dialog.editor.toHtml()
            assert not hasattr(dialog, "rules_obs_media_refresh")
            for asset in (gif_asset, video_asset, still_asset):
                assert dialog.rules_obs_media_combo.findData(asset.id) >= 0
            dialog._rules_media_imported(gif_asset.id)
            app.processEvents()
            assert dialog._rules_media_kind == "gif"
            assert dialog._rules_media_movie is not None
            assert dialog._rules_media_movie.isValid()
            assert dialog._rules_media_player is None
            assert dialog._rules_media_label.isVisible()

            dialog._rules_media_imported(video_asset.id)
            app.processEvents()
            assert dialog._rules_media_movie is None
            assert dialog._rules_media_kind == "video"
            player = dialog._rules_media_player
            assert isinstance(player, QMediaPlayer)
            assert player.audioOutput() is None, "The local Rules preview must be silent"
            assert player.loops() == QMediaPlayer.Infinite
            # An intentionally invalid MP4 header may be rejected immediately
            # by FFmpeg/Windows Media Foundation in CI, clearing player.source().
            # The shared registered path (not codec support) is the tested contract.
            assert dialog._rules_media_source_key[0] == str(video)
            assert dialog._rules_video_sink is not None

            dialog._rules_media_imported(still_asset.id)
            app.processEvents()
            assert dialog._rules_media_movie is None
            assert dialog._rules_media_player is None
            assert dialog._rules_media_kind == "image"
            assert not dialog._rules_media_label.pixmap().isNull()
            assert dialog.editor.toHtml() == initial_html
            assert db.get_rule_template_presentation(active) is None

            # Deleted external/managed file fails closed on next refresh;
            # neither registered paths nor user data are rewritten.
            still.unlink()
            dialog._refresh_local_rules_preview()
            app.processEvents()
            assert dialog._rules_media_source_key is None
            assert dialog._rules_media_label.isHidden()
        finally:
            with patch.object(dialog, "_confirm_discard_or_save", return_value=True):
                dialog.close()
            dialog.deleteLater()
    print("P11_K8C_QT_RULES_GIF_AND_SILENT_VIDEO=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
