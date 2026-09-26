from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes

from PySide6.QtCore import QEvent, QObject, Qt


class WindowsInputGuard(QObject):
    """Не позволяет мыши нажимать In one line сквозь чужое окно.

    На Windows проверяются сразу два признака:
    - какой процесс владеет окном переднего плана;
    - какой процесс владеет окном непосредственно под курсором.

    Если событие мыши каким-либо образом дошло до Qt, но сверху/в фокусе
    находится окно другого процесса, событие поглощается до виджетов.
    """

    _DIRECT_MOUSE_TYPES = {
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseButtonRelease,
        QEvent.Type.MouseButtonDblClick,
        QEvent.Type.Wheel,
        QEvent.Type.ContextMenu,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pid = int(os.getpid())
        self._user32 = None

        if sys.platform != "win32":
            return

        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)

            user32.GetForegroundWindow.argtypes = []
            user32.GetForegroundWindow.restype = wintypes.HWND

            user32.GetCursorPos.argtypes = [
                ctypes.POINTER(wintypes.POINT)
            ]
            user32.GetCursorPos.restype = wintypes.BOOL

            user32.WindowFromPoint.argtypes = [wintypes.POINT]
            user32.WindowFromPoint.restype = wintypes.HWND

            user32.GetWindowThreadProcessId.argtypes = [
                wintypes.HWND,
                ctypes.POINTER(wintypes.DWORD),
            ]
            user32.GetWindowThreadProcessId.restype = wintypes.DWORD

            self._user32 = user32
        except Exception:
            # Защита дополнительная. Если WinAPI недоступен по необычной
            # причине, приложение всё равно должно запускаться.
            self._user32 = None

    @property
    def enabled(self) -> bool:
        return self._user32 is not None

    def _process_id_for_window(self, hwnd) -> int:
        if not self._user32 or not hwnd:
            return 0

        process_id = wintypes.DWORD(0)
        try:
            self._user32.GetWindowThreadProcessId(
                hwnd,
                ctypes.byref(process_id),
            )
        except Exception:
            return 0
        return int(process_id.value)

    def _foreground_process_id(self) -> int:
        if not self._user32:
            return 0
        try:
            hwnd = self._user32.GetForegroundWindow()
        except Exception:
            return 0
        return self._process_id_for_window(hwnd)

    def _cursor_window_process_id(self) -> int:
        if not self._user32:
            return 0

        point = wintypes.POINT()
        try:
            if not self._user32.GetCursorPos(ctypes.byref(point)):
                return 0
            hwnd = self._user32.WindowFromPoint(point)
        except Exception:
            return 0
        return self._process_id_for_window(hwnd)

    def _foreign_window_owns_input(self) -> bool:
        """True, если сейчас ввод относится не к нашему процессу."""
        if not self._user32:
            return False

        foreground_pid = self._foreground_process_id()
        if foreground_pid and foreground_pid != self._pid:
            return True

        cursor_pid = self._cursor_window_process_id()
        if cursor_pid and cursor_pid != self._pid:
            return True

        return False

    def eventFilter(self, watched, event):
        event_type = event.type()

        should_check = event_type in self._DIRECT_MOUSE_TYPES

        # Продолжающееся перетаскивание тоже не должно воздействовать на
        # скрытые контролы. Обычные MouseMove без зажатых кнопок не проверяем,
        # чтобы не делать WinAPI-вызовы на каждое движение курсора.
        if event_type == QEvent.Type.MouseMove:
            try:
                should_check = event.buttons() != Qt.MouseButton.NoButton
            except Exception:
                should_check = False

        if should_check and self._foreign_window_owns_input():
            event.accept()
            return True

        return super().eventFilter(watched, event)
