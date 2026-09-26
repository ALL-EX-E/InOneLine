from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QVBoxLayout,
)

from .common import ScrollSafeSpinBox, make_wide_step_control


class AuctionTimeDialog(QDialog):
    """Выбор времени без проблемной нативной области стрелок QSpinBox."""

    def __init__(
        self,
        title: str,
        label: str,
        *,
        value: int,
        minimum: int,
        maximum: int,
        suffix: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)
        row = QHBoxLayout()
        row.addWidget(QLabel(label))

        self.spin = ScrollSafeSpinBox()
        self.spin.setRange(minimum, maximum)
        self.spin.setValue(value)
        self.spin.setSuffix(suffix)
        self.spin.setMinimumWidth(110)

        control = make_wide_step_control(
            self.spin,
            up_tooltip="Увеличить время",
            down_tooltip="Уменьшить время",
        )
        row.addWidget(control)
        row.addStretch()
        root.addLayout(row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Ok).setText("Продолжить")
        buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    @property
    def value(self) -> int:
        return int(self.spin.value())
