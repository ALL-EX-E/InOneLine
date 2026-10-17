"""P15-H: native operator center hover, click-through and persistent hint."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.ui import MainWindow
from streaming_manager.views.wheel import AuctionWheelWidget
from streaming_manager.views.common import APP_STYLE


class CenterHoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.wheel = AuctionWheelWidget()
        self.wheel.resize(420, 420)
        self.wheel.show()
        self.wheel.raise_()
        self.wheel.activateWindow()
        self.assertTrue(QTest.qWaitForWindowActive(self.wheel, 2000))
        QTest.qWait(70)  # Activation precedes the native surface/initial paint.
        # Always enter from outside the hub: native mouseMove at the current
        # screen position may not generate an event after a previous Qt test.
        self.move_pointer(QPoint(12, 12))

    def tearDown(self):
        self.wheel.close()
        self.wheel.deleteLater()
        self.app.processEvents()

    def move_pointer(self, pos):
        # Place the real cursor for resize checks, then deliver the Qt event
        # explicitly. Windows may coalesce native moves around GL resizes or
        # reuse a screen position, making OS event arrival unsuitable as a
        # clock for these widget geometry/hover regression assertions.
        QTest.mouseMove(self.wheel, pos)
        QTest.qWait(40)
        event = QMouseEvent(
            QEvent.MouseMove, QPointF(pos), QPointF(self.wheel.mapToGlobal(pos)),
            Qt.NoButton, Qt.NoButton, Qt.NoModifier,
        )
        self.app.sendEvent(self.wheel, event)
        # Assertions follow synchronously; unrelated late native Leave events
        # must not overwrite the explicitly delivered event under test.

    def center(self):
        # Independently derive the existing rendered hub, including bottom caption.
        return self.wheel.rect().adjusted(10, 10, -10, -68).center()

    def test_center_hover_shows_edit_and_hand_only_inside_circle(self):
        self.assertTrue(self.wheel.hasMouseTracking())
        self.move_pointer(self.center())
        self.assertEqual(self.wheel.cursor().shape(), Qt.PointingHandCursor)
        label = self.wheel.findChild(QLabel, "wheel-center-edit")
        self.assertIsNotNone(label)
        self.assertTrue(label.isVisible())
        self.assertEqual(label.text(), "Изменить")
        self.assertEqual(self.wheel.toolTip(), "")
        # Outside the circular hitbox but inside its bounding square.
        self.move_pointer(self.center() + QPoint(37, 37))
        self.assertFalse(label.isVisible())
        self.assertEqual(self.wheel.cursor().shape(), Qt.ArrowCursor)

    def test_edit_badge_passes_click_to_existing_center_signal(self):
        hits = []
        self.wheel.centerClicked.connect(lambda: hits.append(True))
        self.move_pointer(self.center())
        label = self.wheel.findChild(QLabel, "wheel-center-edit")
        self.assertIsNotNone(label, "Missing center edit affordance")
        QTest.mouseClick(self.wheel, Qt.LeftButton, pos=self.center())
        self.assertEqual(hits, [True])
        self.assertIsNone(self.wheel.childAt(self.center()), "Badge intercepts native center hit-testing")
        self.assertTrue(label.testAttribute(Qt.WA_TransparentForMouseEvents))

    def test_leave_resets_hover_and_resize_keeps_badge_readable(self):
        for width, height in ((300, 300), (650, 420)):
            self.wheel.resize(width, height)
            QTest.qWait(30)
            self.move_pointer(self.center())
            label = self.wheel.findChild(QLabel, "wheel-center-edit")
            self.assertIsNotNone(label, "Missing center edit affordance")
            self.assertTrue(label.isVisible())
            self.assertLessEqual(label.fontMetrics().horizontalAdvance(label.text()), label.contentsRect().width())
            self.assertLess((label.geometry().center() - self.center()).manhattanLength(), 3)
            self.app.sendEvent(self.wheel, QEvent(QEvent.Leave))
            self.assertFalse(label.isVisible())
            self.assertEqual(self.wheel.cursor().shape(), Qt.ArrowCursor)

    def test_stationary_pointer_stops_hover_when_resize_moves_hub(self):
        self.move_pointer(self.center())
        label = self.wheel.findChild(QLabel, "wheel-center-edit")
        self.assertIsNotNone(label)
        self.assertTrue(label.isVisible())
        self.wheel.resize(650, 420)
        QTest.qWait(40)
        self.assertFalse(label.isVisible(), "Resize left an edit badge far from stationary pointer")
        self.assertEqual(self.wheel.cursor().shape(), Qt.ArrowCursor)

    def test_badge_fits_circle_with_real_application_font_style(self):
        self.wheel.setStyleSheet(APP_STYLE)
        for width, height in ((300, 300), (650, 420)):
            self.wheel.resize(width, height)
            QTest.qWait(70)  # Let native geometry settle before mapping pointer.
            self.move_pointer(QPoint(12, 12))
            self.move_pointer(self.center())
            label = self.wheel.findChild(QLabel, "wheel-center-edit")
            self.assertIsNotNone(label)
            self.assertTrue(label.isVisible())
            self.assertLessEqual(label.fontMetrics().horizontalAdvance(label.text()), label.contentsRect().width(), "Application QSS overrides fitted badge font")
            self.assertLessEqual(label.fontMetrics().height(), label.contentsRect().height(), "Badge text is vertically clipped")
            region = self.wheel.rect().adjusted(10, 10, -10, -68)
            radius = min(region.width(), region.height()) * 0.5 * 0.24
            for corner in (label.geometry().topLeft(), label.geometry().topRight(), label.geometry().bottomLeft(), label.geometry().bottomRight()):
                delta = corner - self.center()
                self.assertLessEqual(delta.x()**2 + delta.y()**2, (radius - 2)**2, "Badge extends into center outline")

    def test_operator_hint_is_present_at_narrow_width_without_global_tooltip(self):
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            paths = AppPaths.from_root(tmp)
            paths.ensure_runtime_dirs()
            window = MainWindow(Database(paths.database_path), paths)
            try:
                window.resize(520, 850)
                window.show()
                window._set_current_main_page(window.auction_tab)
                window.auction_tab.wheel_panel.setVisible(True)
                QTest.qWait(650)
                hint = getattr(window.auction_tab, "wheel_center_hint", None)
                self.assertIsNotNone(hint, "Missing persistent operator hint")
                self.assertTrue(hint.isVisible())
                self.assertEqual(hint.text(), "Нажмите на центр колеса, чтобы изменить изображение")
                self.assertTrue(hint.wordWrap())
                self.assertGreaterEqual(hint.height(), hint.heightForWidth(hint.width()))
                self.assertEqual(window.auction_tab.wheel_widget.toolTip(), "")
            finally:
                window.thread_pool.waitForDone(5000)
                window.close()
                window.deleteLater()
                self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
