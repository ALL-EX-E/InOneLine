from __future__ import annotations

"""D10 native Qt geometry/interaction smoke; runs without opening a real browser."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.views.main_window import MainWindow


def main() -> None:
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        paths = AppPaths.from_root(Path(tmp))
        paths.ensure_runtime_dirs()
        db = Database(paths.database_path)
        window = MainWindow(db, paths)
        try:
            settings = window.settings_tab
            scroll = window._main_tab_scroll_by_page[settings]
            button = window._settings_github_button
            assert button.parent() is scroll
            assert scroll.viewportMargins().bottom() >= 48
            assert button.icon().isNull() is False
            assert not button.icon().pixmap(24, 24).isNull()
            assert button.toolTip() == "Открыть GitHub проекта"
            assert button.accessibleName() == "Открыть GitHub проекта"
            assert settings.settings_tabs.count() == 4

            window._set_current_main_page(settings)
            for width, height in ((520, 360), (720, 540), (1550, 900), (2560, 1440)):
                window.resize(width, height)
                window.show()
                for tab in range(4):
                    settings.settings_tabs.setCurrentIndex(tab)
                    app.processEvents()
                    window._update_responsive_layout()
                    app.processEvents()
                    window._position_settings_github_button()
                    assert button.isVisible()
                    assert scroll.isVisible()
                    viewport = scroll.viewport().geometry()
                    control = button.geometry()
                    assert control.top() > viewport.bottom(), (width, height, tab, control, viewport)
                    assert control.bottom() < scroll.height(), (width, height, tab, control, scroll.size())
                    assert control.left() >= viewport.left()
                    assert control.right() < viewport.right()
                    scrollbar = scroll.verticalScrollBar()
                    if scrollbar.isVisible():
                        assert control.right() < scrollbar.geometry().left()
                    scrollbar.setValue(scrollbar.maximum())
                    app.processEvents()
                    assert button.geometry().top() > scroll.viewport().geometry().bottom()
                    assert button.isVisible()
                assert window.width() == width and window.height() == height

            with patch("streaming_manager.views.main_window.QDesktopServices.openUrl", return_value=True) as launch:
                button.click()
                assert launch.call_count == 1
                assert launch.call_args.args[0].toString() == "https://github.com/ALL-EX-E/InOneLine"
            print("D10_GITHUB_ICON_FOOTER_NATIVE_QT=PASS")
        finally:
            window.api.stop()
            window.close()
            app.processEvents()


if __name__ == "__main__":
    main()
