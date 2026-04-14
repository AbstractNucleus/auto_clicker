from __future__ import annotations

import ctypes
from ctypes import wintypes
from enum import IntFlag

_user32 = ctypes.WinDLL("user32", use_last_error=True)

INPUT_MOUSE = 0


class MouseEventFlag(IntFlag):
    MOVE = 0x0001
    LEFTDOWN = 0x0002
    LEFTUP = 0x0004
    RIGHTDOWN = 0x0008
    RIGHTUP = 0x0010
    MIDDLEDOWN = 0x0020
    MIDDLEUP = 0x0040
    ABSOLUTE = 0x8000


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT), ("hi", _HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTunion)]


_user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
_user32.SendInput.restype = wintypes.UINT

_SCREEN_ABS_MAX = 65535


def _screen_metrics() -> tuple[int, int]:
    SM_CXSCREEN, SM_CYSCREEN = 0, 1
    return (
        _user32.GetSystemMetrics(SM_CXSCREEN),
        _user32.GetSystemMetrics(SM_CYSCREEN),
    )


def _to_absolute(x: int, y: int) -> tuple[int, int]:
    w, h = _screen_metrics()
    if w <= 0 or h <= 0:
        raise OSError("GetSystemMetrics returned non-positive screen size")
    return (x * _SCREEN_ABS_MAX // (w - 1), y * _SCREEN_ABS_MAX // (h - 1))


def _mouse_input(flags: int, dx: int = 0, dy: int = 0) -> INPUT:
    event = INPUT()
    event.type = INPUT_MOUSE
    event.mi = _MOUSEINPUT(
        dx=dx, dy=dy, mouseData=0, dwFlags=flags, time=0, dwExtraInfo=None
    )
    return event


def send_click(down_flag: int, up_flag: int, move_to: tuple[int, int] | None = None) -> None:
    events: list[INPUT] = []
    if move_to is not None:
        ax, ay = _to_absolute(*move_to)
        events.append(
            _mouse_input(
                int(MouseEventFlag.MOVE | MouseEventFlag.ABSOLUTE),
                dx=ax,
                dy=ay,
            )
        )
    events.append(_mouse_input(down_flag))
    events.append(_mouse_input(up_flag))

    arr = (INPUT * len(events))(*events)
    sent = _user32.SendInput(len(events), arr, ctypes.sizeof(INPUT))
    if sent != len(events):
        raise ctypes.WinError(ctypes.get_last_error())
