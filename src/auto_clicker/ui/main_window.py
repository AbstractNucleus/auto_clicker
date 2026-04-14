from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from auto_clicker.engine.config import (
    Button,
    ClickConfig,
    CursorMode,
    FixedPoint,
    FollowCursor,
    TriggerMode,
)
from auto_clicker.engine.stops import ClickLimit, DurationLimit, StopCondition
from auto_clicker.hotkeys.backend import KeyBinding
from auto_clicker.ui.widgets.hotkey_edit import HotkeyEdit
from auto_clicker.ui.widgets.point_capture import PointCapture


class MainWindow(QMainWindow):
    start_requested = Signal()
    stop_requested = Signal()
    binding_changed = Signal(object, object)  # KeyBinding, TriggerMode

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Auto Clicker")
        self.setFixedWidth(360)

        root = QWidget()
        layout = QVBoxLayout(root)
        form = QFormLayout()
        layout.addLayout(form)

        self._cps = QSpinBox()
        self._cps.setRange(1, 100)
        self._cps.setValue(10)
        form.addRow("Clicks per second", self._cps)

        self._button_group = QButtonGroup(self)
        btn_row = QHBoxLayout()
        self._btn_left = QRadioButton("Left")
        self._btn_right = QRadioButton("Right")
        self._btn_middle = QRadioButton("Middle")
        self._btn_left.setChecked(True)
        for b in (self._btn_left, self._btn_right, self._btn_middle):
            self._button_group.addButton(b)
            btn_row.addWidget(b)
        form.addRow("Mouse button", self._wrap(btn_row))

        self._cursor_follow = QRadioButton("Follow cursor")
        self._cursor_fixed = QRadioButton("Fixed point")
        self._cursor_follow.setChecked(True)
        self._point_capture = PointCapture()
        self._fixed_point: FixedPoint | None = None
        self._point_capture.captured.connect(self._on_point_captured)
        cursor_col = QVBoxLayout()
        cursor_col.addWidget(self._cursor_follow)
        cursor_col.addWidget(self._cursor_fixed)
        cursor_col.addWidget(self._point_capture)
        form.addRow("Cursor mode", self._wrap(cursor_col))

        self._trig_toggle = QRadioButton("Toggle")
        self._trig_hold = QRadioButton("Hold")
        self._trig_toggle.setChecked(True)
        trig_col = QVBoxLayout()
        trig_col.addWidget(self._trig_toggle)
        trig_col.addWidget(self._trig_hold)
        form.addRow("Trigger mode", self._wrap(trig_col))

        self._hotkey = HotkeyEdit(KeyBinding(vk=0x75))  # F6
        self._hotkey.binding_changed.connect(self._on_binding_changed)
        form.addRow("Hotkey", self._hotkey)

        self._use_duration = QCheckBox("Duration")
        self._duration = QSpinBox()
        self._duration.setRange(1, 3600)
        self._duration.setValue(30)
        dur_row = QHBoxLayout()
        dur_row.addWidget(self._use_duration)
        dur_row.addWidget(self._duration)
        dur_row.addWidget(QLabel("seconds"))
        form.addRow("", self._wrap(dur_row))

        self._use_click_limit = QCheckBox("Click count")
        self._click_limit = QSpinBox()
        self._click_limit.setRange(1, 1_000_000)
        self._click_limit.setValue(100)
        cnt_row = QHBoxLayout()
        cnt_row.addWidget(self._use_click_limit)
        cnt_row.addWidget(self._click_limit)
        form.addRow("", self._wrap(cnt_row))

        self._state_label = QLabel("● Idle")
        self._state_label.setStyleSheet("color: #888;")
        layout.addWidget(self._state_label)

        self._start_button = QPushButton("START (F6)")
        self._start_button.setObjectName("primary")
        self._start_button.clicked.connect(self._on_start_clicked)
        layout.addWidget(self._start_button)

        self._trig_toggle.toggled.connect(lambda _checked: self._emit_binding())
        self._trig_hold.toggled.connect(lambda _checked: self._emit_binding())

        self.setCentralWidget(root)

    @staticmethod
    def _wrap(layout: QHBoxLayout | QVBoxLayout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    def _on_point_captured(self, point: FixedPoint) -> None:
        self._fixed_point = point
        self._cursor_fixed.setChecked(True)

    def _on_binding_changed(self, binding: KeyBinding) -> None:
        self._emit_binding(binding)

    def _emit_binding(self, binding: KeyBinding | None = None) -> None:
        if binding is None:
            binding = self._hotkey._binding  # type: ignore[attr-defined]
        mode = TriggerMode.TOGGLE if self._trig_toggle.isChecked() else TriggerMode.HOLD
        self.binding_changed.emit(binding, mode)

    def _on_start_clicked(self) -> None:
        if self._start_button.text().startswith("STOP"):
            self.stop_requested.emit()
        else:
            self.start_requested.emit()

    # Public API wired from app.py

    def current_config(self) -> ClickConfig:
        cursor: CursorMode
        if self._cursor_fixed.isChecked() and self._fixed_point is not None:
            cursor = self._fixed_point
        else:
            cursor = FollowCursor()
        button = Button.LEFT
        if self._btn_right.isChecked():
            button = Button.RIGHT
        elif self._btn_middle.isChecked():
            button = Button.MIDDLE
        mode = TriggerMode.TOGGLE if self._trig_toggle.isChecked() else TriggerMode.HOLD
        return ClickConfig(
            cps=self._cps.value(), button=button, cursor_mode=cursor, trigger_mode=mode
        )

    def current_stops(self) -> list[StopCondition]:
        stops: list[StopCondition] = []
        if self._use_duration.isChecked():
            stops.append(DurationLimit(seconds=float(self._duration.value())))
        if self._use_click_limit.isChecked():
            stops.append(ClickLimit(count=self._click_limit.value()))
        return stops

    def current_binding(self) -> KeyBinding:
        return self._hotkey._binding  # type: ignore[attr-defined,return-value]

    def set_state(self, state: str) -> None:
        colors = {"idle": "#888", "running": "#5EC8D6", "armed": "#d6a55e"}
        self._state_label.setText(f"● {state.capitalize()}")
        self._state_label.setStyleSheet(f"color: {colors.get(state, '#888')};")
        editable = state == "idle"
        for w in (
            self._cps, self._btn_left, self._btn_right, self._btn_middle,
            self._cursor_follow, self._cursor_fixed, self._trig_toggle, self._trig_hold,
            self._hotkey, self._use_duration, self._duration,
            self._use_click_limit, self._click_limit,
        ):
            w.setEnabled(editable)
        self._start_button.setText("STOP" if state == "running" else "START")

    def bind_actions(self, on_start: Callable[[], None], on_stop: Callable[[], None]) -> None:
        self.start_requested.connect(on_start)
        self.stop_requested.connect(on_stop)
