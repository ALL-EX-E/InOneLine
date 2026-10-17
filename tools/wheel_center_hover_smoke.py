"""P15-H: native operator center hover, click-through and persistent hint."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel

from streaming_manager.app_paths import AppPaths
from streaming_manager.database import Database
from streaming_manager.ui import MainWindow
from streaming_manager.views.wheel import AuctionWheelWidget


class CenterHoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.wheel = AuctionWheelWidget()
        self.wheel.resize(420, 420)
        self.wheel.show()
        QTest.qWait(70)

    def tearDown(self):
        self.wheel.close()
        self.wheel.deleteLater()
        self.app.processEvents()

    def center(self):
        # Independently derive the existing rendered hub, including bottom caption.
        return self.wheel.rect().adjusted(10, 10, -10, -68).center()

    def test_center_hover_shows_edit_and_hand_only_inside_circle(self):
        QTest.mouseMove(self.wheel, self.center())
        QTest.qWait(40)  # Native Windows queues the pointer move asynchronously.
        self.assertEqual(self.wheel.cursor().shape(), Qt.PointingHandCursor)
        label = self.wheel.findChild(QLabel, "wheel-center-edit")
        self.assertIsNotNone(label)
        self.assertTrue(label.isVisible())
        self.assertEqual(label.text(), "Изменить")
        self.assertEqual(self.wheel.toolTip(), "")
        # Outside the circular hitbox but inside its bounding square.
        QTest.mouseMove(self.wheel, self.center() + QPoint(37, 37))
        QTest.qWait(40)
        self.assertFalse(label.isVisible())
        self.assertEqual(self.wheel.cursor().shape(), Qt.ArrowCursor)

    def test_edit_badge_passes_click_to_existing_center_signal(self):
        hits = []
        self.wheel.centerClicked.connect(lambda: hits.append(True))
        QTest.mouseMove(self.wheel, self.center())
        QTest.qWait(40)
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
            QTest.mouseMove(self.wheel, self.center())
            QTest.qWait(40)
            label = self.wheel.findChild(QLabel, "wheel-center-edit")
            self.assertIsNotNone(label, "Missing center edit affordance")
            self.assertTrue(label.isVisible())
            self.assertLessEqual(label.fontMetrics().horizontalAdvance(label.text()), label.contentsRect().width())
            self.assertLess((label.geometry().center() - self.center()).manhattanLength(), 3)
            self.app.sendEvent(self.wheel, QEvent(QEvent.Leave))
            self.assertFalse(label.isVisible())
            self.assertEqual(self.wheel.cursor().shape(), Qt.ArrowCursor)

    def test_stationary_pointer_stops_hover_when_resize_moves_hub(self):
        QTest.mouseMove(self.wheel, self.center())
        QTest.qWait(40)
        label = self.wheel.findChild(QLabel, "wheel-center-edit")
        self.assertIsNotNone(label)
        self.assertTrue(label.isVisible())
        self.wheel.resize(650, 420)
        QTest.qWait(40)
        self.assertFalse(label.isVisible(), "Resize left an edit badge far from stationary pointer")
        self.assertEqual(self.wheel.cursor().shape(), Qt.ArrowCursor)

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
