from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from auto_clicker.engine.config import TriggerMode
from auto_clicker.hotkeys.backend import HotkeyBackend, KeyBinding


@dataclass
class HotkeyController:
    backend: HotkeyBackend
    on_start: Callable[[], None] = field(default=lambda: None)
    on_stop: Callable[[], None] = field(default=lambda: None)
    on_hold_started: Callable[[], None] = field(default=lambda: None)
    on_hold_ended: Callable[[], None] = field(default=lambda: None)
    _running: bool = False
    _binding: KeyBinding | None = None
    _mode: TriggerMode | None = None

    def set_binding(self, binding: KeyBinding, mode: TriggerMode) -> None:
        self.backend.clear()
        self._binding = binding
        self._mode = mode
        self._running = False
        if mode is TriggerMode.TOGGLE:
            self.backend.register_toggle(binding, self._toggle)
        else:
            self.backend.register_hold(binding, self._hold_down, self._hold_up)

    def clear(self) -> None:
        self.backend.clear()
        self._binding = None
        self._mode = None
        self._running = False

    def mark_idle(self) -> None:
        """Called by the engine when a run ends — keeps toggle state accurate."""
        self._running = False

    def _toggle(self) -> None:
        if self._running:
            self._running = False
            self.on_stop()
        else:
            self._running = True
            self.on_start()

    def _hold_down(self) -> None:
        self.on_hold_started()

    def _hold_up(self) -> None:
        self.on_hold_ended()
