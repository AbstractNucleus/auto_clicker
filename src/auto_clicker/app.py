from __future__ import annotations

import sys

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication
from PySide6.QtWidgets import QApplication

from auto_clicker.engine.config import TriggerMode
from auto_clicker.engine.engine import ClickEngine
from auto_clicker.engine.sinks import SendInputSink  # type: ignore[attr-defined]
from auto_clicker.hotkeys.backend import KeyBinding, Win32Backend  # type: ignore[attr-defined]
from auto_clicker.hotkeys.controller import HotkeyController
from auto_clicker.ui.main_window import MainWindow
from auto_clicker.ui.theme import apply_theme


class _HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, backend: Win32Backend) -> None:
        super().__init__()
        self._backend = backend

    def nativeEventFilter(self, event_type, message):  # type: ignore[override]
        if event_type != b"windows_generic_MSG":
            return False, 0
        import ctypes

        from auto_clicker.win32.hotkey import WM_HOTKEY

        # Decode MSG struct: hwnd, message, wParam, lParam, time, pt
        raw = ctypes.string_at(int(message), 48)
        # On 64-bit: hwnd(8), message(4)+pad(4), wParam(8), lParam(8), time(4), pt(8)
        wm = int.from_bytes(raw[8:12], "little")
        wparam = int.from_bytes(raw[16:24], "little")
        if wm == WM_HOTKEY:
            self._backend.on_wm_hotkey(wparam)
        return False, 0


def main() -> int:
    if sys.platform != "win32":
        print("auto_clicker is Windows-only.", file=sys.stderr)
        return 1

    app = QApplication(sys.argv)
    apply_theme(app)

    window = MainWindow()
    engine = ClickEngine(sink=SendInputSink())
    backend = Win32Backend()
    controller = HotkeyController(
        backend=backend,
        on_start=lambda: _start(window, engine, controller),
        on_stop=lambda: _stop(window, engine, controller),
        on_hold_started=lambda: _start(window, engine, controller),
        on_hold_ended=lambda: _stop(window, engine, controller),
    )

    filter_ = _HotkeyFilter(backend)
    QCoreApplication.instance().installNativeEventFilter(filter_)  # type: ignore[union-attr]

    def _apply_binding(binding: KeyBinding, mode: TriggerMode) -> None:
        controller.set_binding(binding, mode)

    window.binding_changed.connect(_apply_binding)
    window.bind_actions(
        on_start=lambda: _start(window, engine, controller),
        on_stop=lambda: _stop(window, engine, controller),
    )

    # apply initial binding
    _apply_binding(window.current_binding(), TriggerMode.TOGGLE)

    window.show()
    exit_code = app.exec()
    engine.shutdown()
    backend.clear()
    return exit_code


def _start(window: MainWindow, engine: ClickEngine, controller: HotkeyController) -> None:
    try:
        engine.start(config=window.current_config(), stops=window.current_stops())
    except Exception as exc:  # noqa: BLE001
        print(f"engine.start failed: {exc}", file=sys.stderr)
        return
    window.set_state("running")


def _stop(window: MainWindow, engine: ClickEngine, controller: HotkeyController) -> None:
    engine.stop()
    engine.wait_until_idle(timeout=1.0)
    controller.mark_idle()
    window.set_state("idle")
