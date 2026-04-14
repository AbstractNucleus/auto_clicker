from __future__ import annotations

import sys

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from auto_clicker.engine.config import FixedPoint


class PointCapture(QWidget):
    captured = Signal(object)  # FixedPoint

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._button = QPushButton("Pick point")
        self._label = QLabel("—")
        self._button.clicked.connect(self._arm)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._button)
        layout.addWidget(self._label, 1)
        self._hook = None  # type: ignore[assignment]

    def _arm(self) -> None:
        if sys.platform != "win32":
            self._label.setText("Windows only")
            return
        from auto_clicker.win32 import hooks

        self._button.setText("Click anywhere…")

        def on_event(msg: int, x: int, y: int) -> bool:
            if msg == hooks.WM_LBUTTONDOWN:
                self._finish(x, y)
                return True
            return False

        self._hook = hooks.install_mouse_hook(on_event)

    def _finish(self, x: int, y: int) -> None:
        if self._hook is not None:
            self._hook.unhook()
            self._hook = None
        self._button.setText("Pick point")
        self._label.setText(f"Fixed at {x}, {y}")
        self.captured.emit(FixedPoint(x=x, y=y))
