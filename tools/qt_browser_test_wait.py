"""Qt browser test waits that let the Python localhost server respond."""

from PySide6.QtCore import QEventLoop, QTimer, Qt


def wait_with_http_workers(milliseconds: int) -> None:
    # On Windows, PySide's QTest.qWait holds the GIL. Chromium keeps polling
    # while the Python server threads are prevented from serving those polls.
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.setTimerType(Qt.TimerType.PreciseTimer)
    timer.timeout.connect(loop.quit)
    timer.start(milliseconds)
    loop.exec()
