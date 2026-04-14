from __future__ import annotations

import ctypes
from ctypes import wintypes
from enum import IntFlag

_user32 = ctypes.WinDLL("user32", use_last_error=True)

WM_HOTKEY = 0x0312


class HotkeyModifier(IntFlag):
    NONE = 0x0000
    ALT = 0x0001
    CTRL = 0x0002
    SHIFT = 0x0004
    WIN = 0x0008
    NOREPEAT = 0x4000


_user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
_user32.RegisterHotKey.restype = wintypes.BOOL
_user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.UnregisterHotKey.restype = wintypes.BOOL


def register_hotkey(hwnd: int | None, hotkey_id: int, modifiers: int, vk: int) -> None:
    hwnd_val = wintypes.HWND(hwnd) if hwnd is not None else None
    if not _user32.RegisterHotKey(hwnd_val, hotkey_id, modifiers | int(HotkeyModifier.NOREPEAT), vk):
        raise ctypes.WinError(ctypes.get_last_error())


def unregister_hotkey(hwnd: int | None, hotkey_id: int) -> None:
    hwnd_val = wintypes.HWND(hwnd) if hwnd is not None else None
    if not _user32.UnregisterHotKey(hwnd_val, hotkey_id):
        raise ctypes.WinError(ctypes.get_last_error())
