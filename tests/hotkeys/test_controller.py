from __future__ import annotations

from auto_clicker.engine.config import TriggerMode
from auto_clicker.hotkeys.backend import FakeBackend, KeyBinding
from auto_clicker.hotkeys.controller import HotkeyController


def _controller(backend: FakeBackend) -> tuple[HotkeyController, dict[str, int]]:
    counts = {"start": 0, "stop": 0, "hold_started": 0, "hold_ended": 0}
    ctrl = HotkeyController(
        backend=backend,
        on_start=lambda: counts.__setitem__("start", counts["start"] + 1),
        on_stop=lambda: counts.__setitem__("stop", counts["stop"] + 1),
        on_hold_started=lambda: counts.__setitem__("hold_started", counts["hold_started"] + 1),
        on_hold_ended=lambda: counts.__setitem__("hold_ended", counts["hold_ended"] + 1),
    )
    return ctrl, counts


def test_toggle_mode_alternates_start_and_stop():
    backend = FakeBackend()
    ctrl, counts = _controller(backend)
    ctrl.set_binding(KeyBinding(vk=0x75), TriggerMode.TOGGLE)  # F6
    backend.fire_toggle()
    backend.fire_toggle()
    backend.fire_toggle()
    assert counts["start"] == 2
    assert counts["stop"] == 1


def test_hold_mode_emits_hold_events():
    backend = FakeBackend()
    ctrl, counts = _controller(backend)
    ctrl.set_binding(KeyBinding(vk=0x75), TriggerMode.HOLD)
    backend.press_hold()
    backend.release_hold()
    backend.press_hold()
    assert counts["hold_started"] == 2
    assert counts["hold_ended"] == 1


def test_rebinding_replaces_old_registration():
    backend = FakeBackend()
    ctrl, _ = _controller(backend)
    ctrl.set_binding(KeyBinding(vk=0x75), TriggerMode.TOGGLE)
    ctrl.set_binding(KeyBinding(vk=0x76), TriggerMode.TOGGLE)
    assert backend.history == ["clear", "toggle:117", "clear", "toggle:118"]


def test_switching_modes_reregisters():
    backend = FakeBackend()
    ctrl, _ = _controller(backend)
    ctrl.set_binding(KeyBinding(vk=0x75), TriggerMode.TOGGLE)
    ctrl.set_binding(KeyBinding(vk=0x75), TriggerMode.HOLD)
    assert backend.history == ["clear", "toggle:117", "clear", "hold:117"]


def test_clear_removes_everything():
    backend = FakeBackend()
    ctrl, _ = _controller(backend)
    ctrl.set_binding(KeyBinding(vk=0x75), TriggerMode.TOGGLE)
    ctrl.clear()
    assert backend.history[-1] == "clear"
