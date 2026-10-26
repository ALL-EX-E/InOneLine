from __future__ import annotations

"""D10 native Qt geometry/interaction smoke; runs without opening a real browser."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QRect, QThreadPool
from PySide6.QtTest import QTest
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
                app.processEvents()
                # Windows CI may clamp the requested outer size to its virtual
                # desktop. Observe the actual native size after show(), then
                # reject any resizing triggered by switching Settings pages.
                stable_size = window.size()
                for tab in range(4):
                    settings.settings_tabs.setCurrentIndex(tab)
                    app.processEvents()
                    window._update_responsive_layout()
                    app.processEvents()
                    window._position_settings_github_button()
                    assert button.isVisible()
                    assert scroll.isVisible()
                    assert window.size() == stable_size, (
                        "Settings page resized main window",
                        (width, height), tab, stable_size, window.size(),
                    )
                    viewport = scroll.viewport().geometry()
                    control = button.geometry()
                    assert control.top() > viewport.bottom(), (width, height, tab, control, viewport)
                    assert control.bottom() < scroll.height(), (width, height, tab, control, scroll.size())
                    assert control.left() >= viewport.left()
                    assert control.right() < viewport.right()
                    scrollbar = scroll.verticalScrollBar()
                    if scrollbar.isVisible():
                        # QScrollBar.geometry() is relative to its own Qt scroll
                        # container, not to the QScrollArea. Convert to the same
                        # coordinates and compare real two-dimensional overlap.
                        scrollbar_rect = QRect(
                            scrollbar.mapTo(scroll, QPoint(0, 0)), scrollbar.size()
                        )
                        assert not control.intersects(scrollbar_rect), (
                            width, height, tab, control, scrollbar_rect
                        )
                    scrollbar.setValue(scrollbar.maximum())
                    app.processEvents()
                    assert button.geometry().top() > scroll.viewport().geometry().bottom()
                    assert button.isVisible()
                assert window.size() == stable_size, (
                    "Settings tab switch changed main-window size",
                    (width, height), stable_size, window.size(),
                )

            with patch("streaming_manager.views.main_window.QDesktopServices.openUrl", return_value=True) as launch:
                button.click()
                assert launch.call_count == 1
                assert launch.call_args.args[0].toString() == "https://github.com/ALL-EX-E/InOneLine"
            print("D10_GITHUB_ICON_FOOTER_NATIVE_QT=PASS")
        finally:
            # Startup/backup workers must finish before the temporary DB folder
            # is deleted; otherwise unrelated async teardown errors are emitted.
            QTest.qWait(600)
            window.api.stop()
            QThreadPool.globalInstance().waitForDone(15000)
            window.close()
            app.processEvents()


if __name__ == "__main__":
    main()
