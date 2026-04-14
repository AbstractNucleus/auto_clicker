from __future__ import annotations

import ctypes
import threading
from collections.abc import Callable
from ctypes import wintypes

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

WM_LBUTTONDOWN = 0x0201
WM_RBUTTONDOWN = 0x0204
WM_MBUTTONDOWN = 0x0207


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt_x", wintypes.LONG),
        ("pt_y", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(wintypes.LPARAM, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

_user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
_user32.SetWindowsHookExW.restype = wintypes.HHOOK
_user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
_user32.UnhookWindowsHookEx.restype = wintypes.BOOL
_user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
_user32.CallNextHookEx.restype = wintypes.LPARAM
_kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
_kernel32.GetModuleHandleW.restype = wintypes.HMODULE


class HookHandle:
    def __init__(self, handle: int, proc: HOOKPROC) -> None:
        self._handle = handle
        self._proc = proc  # keep alive

    def unhook(self) -> None:
        if self._handle:
            _user32.UnhookWindowsHookEx(self._handle)
            self._handle = 0


_lock = threading.Lock()


def install_keyboard_hook(
    on_event: Callable[[int, int], bool],  # (vk_code, wm_msg) -> True to swallow
) -> HookHandle:
    def _proc(n_code: int, w_param: int, l_param: int) -> int:
        if n_code >= 0:
            data = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            try:
                swallow = on_event(data.vkCode, w_param)
            except Exception:
                swallow = False
            if swallow:
                return 1
        return _user32.CallNextHookEx(None, n_code, w_param, l_param)

    proc = HOOKPROC(_proc)
    with _lock:
        handle = _user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, proc, _kernel32.GetModuleHandleW(None), 0
        )
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    return HookHandle(handle, proc)


def install_mouse_hook(
    on_event: Callable[[int, int, int], bool],  # (wm_msg, x, y) -> True to swallow
) -> HookHandle:
    def _proc(n_code: int, w_param: int, l_param: int) -> int:
        if n_code >= 0:
            data = ctypes.cast(l_param, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            try:
                swallow = on_event(w_param, data.pt_x, data.pt_y)
            except Exception:
                swallow = False
            if swallow:
                return 1
        return _user32.CallNextHookEx(None, n_code, w_param, l_param)

    proc = HOOKPROC(_proc)
    with _lock:
        handle = _user32.SetWindowsHookExW(
            WH_MOUSE_LL, proc, _kernel32.GetModuleHandleW(None), 0
        )
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    return HookHandle(handle, proc)
