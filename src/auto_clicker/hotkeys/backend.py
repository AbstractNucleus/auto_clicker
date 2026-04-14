from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class KeyBinding:
    vk: int
    modifiers: int = 0


class HotkeyBackend(Protocol):
    def register_toggle(self, binding: KeyBinding, on_fire: Callable[[], None]) -> None: ...
    def register_hold(
        self,
        binding: KeyBinding,
        on_down: Callable[[], None],
        on_up: Callable[[], None],
    ) -> None: ...
    def clear(self) -> None: ...


@dataclass
class FakeBackend:
    _toggle: tuple[KeyBinding, Callable[[], None]] | None = None
    _hold: tuple[KeyBinding, Callable[[], None], Callable[[], None]] | None = None
    history: list[str] = field(default_factory=list)

    def register_toggle(self, binding: KeyBinding, on_fire: Callable[[], None]) -> None:
        self._toggle = (binding, on_fire)
        self.history.append(f"toggle:{binding.vk}")

    def register_hold(
        self,
        binding: KeyBinding,
        on_down: Callable[[], None],
        on_up: Callable[[], None],
    ) -> None:
        self._hold = (binding, on_down, on_up)
        self.history.append(f"hold:{binding.vk}")

    def clear(self) -> None:
        self._toggle = None
        self._hold = None
        self.history.append("clear")

    # helpers used by tests to simulate the OS
    def fire_toggle(self) -> None:
        assert self._toggle is not None
        self._toggle[1]()

    def press_hold(self) -> None:
        assert self._hold is not None
        self._hold[1]()

    def release_hold(self) -> None:
        assert self._hold is not None
        self._hold[2]()


if sys.platform == "win32":  # pragma: no cover - integration only
    import threading

    from auto_clicker.win32 import hooks, hotkey

    _HOTKEY_ID = 0xB010

    @dataclass
    class Win32Backend:
        _hotkey_registered: bool = False
        _hook: hooks.HookHandle | None = None
        _hook_callback: Callable[[int, int], bool] | None = None
        _lock: threading.Lock = field(default_factory=threading.Lock)

        def register_toggle(self, binding: KeyBinding, on_fire: Callable[[], None]) -> None:
            self.clear()
            hotkey.register_hotkey(None, _HOTKEY_ID, binding.modifiers, binding.vk)
            self._hotkey_registered = True
            self._toggle_cb = on_fire  # pumped by Qt filter

        def register_hold(
            self,
            binding: KeyBinding,
            on_down: Callable[[], None],
            on_up: Callable[[], None],
        ) -> None:
            self.clear()

            down_msgs = {hooks.WM_KEYDOWN, hooks.WM_SYSKEYDOWN}
            up_msgs = {hooks.WM_KEYUP, hooks.WM_SYSKEYUP}
            holding = {"v": False}

            def _on_event(vk: int, msg: int) -> bool:
                if vk != binding.vk:
                    return False
                if msg in down_msgs and not holding["v"]:
                    holding["v"] = True
                    on_down()
                elif msg in up_msgs and holding["v"]:
                    holding["v"] = False
                    on_up()
                return False

            self._hook_callback = _on_event
            self._hook = hooks.install_keyboard_hook(_on_event)

        def clear(self) -> None:
            if self._hotkey_registered:
                try:
                    hotkey.unregister_hotkey(None, _HOTKEY_ID)
                finally:
                    self._hotkey_registered = False
            if self._hook is not None:
                self._hook.unhook()
                self._hook = None
            self._hook_callback = None

        def on_wm_hotkey(self, hotkey_id: int) -> None:
            if hotkey_id == _HOTKEY_ID and getattr(self, "_toggle_cb", None):
                self._toggle_cb()
