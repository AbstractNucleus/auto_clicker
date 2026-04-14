from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from auto_clicker.hotkeys.backend import KeyBinding

_VK_MAP = {
    Qt.Key.Key_F1: 0x70,
    Qt.Key.Key_F2: 0x71,
    Qt.Key.Key_F3: 0x72,
    Qt.Key.Key_F4: 0x73,
    Qt.Key.Key_F5: 0x74,
    Qt.Key.Key_F6: 0x75,
    Qt.Key.Key_F7: 0x76,
    Qt.Key.Key_F8: 0x77,
    Qt.Key.Key_F9: 0x78,
    Qt.Key.Key_F10: 0x79,
    Qt.Key.Key_F11: 0x7A,
    Qt.Key.Key_F12: 0x7B,
}

_RESERVED = {Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape, Qt.Key.Key_Tab}


class HotkeyEdit(QWidget):
    binding_changed = Signal(object)  # KeyBinding

    def __init__(self, initial: KeyBinding, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._binding = initial
        self._label = QLineEdit(self._render(initial))
        self._label.setReadOnly(True)
        self._button = QPushButton("change")
        self._button.clicked.connect(self._start_capture)
        self._error = QLabel("")
        self._error.setStyleSheet("color: #f48771;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label, 1)
        layout.addWidget(self._button)
        layout.addWidget(self._error, 1)
        self._capturing = False

    def _start_capture(self) -> None:
        self._capturing = True
        self._label.setText("Press a key…")
        self._error.setText("")
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._capturing:
            super().keyPressEvent(event)
            return
        qt_key = Qt.Key(event.key())
        if qt_key == Qt.Key.Key_Escape:
            self._capturing = False
            self._label.setText(self._render(self._binding))
            return
        if qt_key in _RESERVED:
            self._error.setText("Reserved key — pick another.")
            return
        vk = _VK_MAP.get(qt_key)
        if vk is None:
            self._error.setText("Only F1–F12 are supported in v0.1.")
            return
        self._binding = KeyBinding(vk=vk)
        self._capturing = False
        self._label.setText(self._render(self._binding))
        self.binding_changed.emit(self._binding)

    @staticmethod
    def _render(binding: KeyBinding) -> str:
        for key, vk in _VK_MAP.items():
            if vk == binding.vk:
                return key.name.removeprefix("Key_")
        return f"VK_{binding.vk:#x}"
