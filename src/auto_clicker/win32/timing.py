from __future__ import annotations

import atexit
import ctypes
from ctypes import wintypes

_winmm = ctypes.WinDLL("winmm", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_winmm.timeBeginPeriod.argtypes = [wintypes.UINT]
_winmm.timeBeginPeriod.restype = wintypes.UINT
_winmm.timeEndPeriod.argtypes = [wintypes.UINT]
_winmm.timeEndPeriod.restype = wintypes.UINT

_kernel32.QueryPerformanceCounter.argtypes = [ctypes.POINTER(ctypes.c_int64)]
_kernel32.QueryPerformanceCounter.restype = wintypes.BOOL
_kernel32.QueryPerformanceFrequency.argtypes = [ctypes.POINTER(ctypes.c_int64)]
_kernel32.QueryPerformanceFrequency.restype = wintypes.BOOL

_TIMER_RESOLUTION_MS = 1
_timer_active = False


def query_performance_counter() -> int:
    value = ctypes.c_int64()
    if not _kernel32.QueryPerformanceCounter(ctypes.byref(value)):
        raise ctypes.WinError(ctypes.get_last_error())
    return value.value


def query_performance_frequency() -> int:
    value = ctypes.c_int64()
    if not _kernel32.QueryPerformanceFrequency(ctypes.byref(value)):
        raise ctypes.WinError(ctypes.get_last_error())
    return value.value


def begin_timer_period() -> None:
    global _timer_active
    if _timer_active:
        return
    if _winmm.timeBeginPeriod(_TIMER_RESOLUTION_MS) != 0:
        raise OSError("timeBeginPeriod(1) failed")
    _timer_active = True
    atexit.register(_end_timer_period)


def _end_timer_period() -> None:
    global _timer_active
    if not _timer_active:
        return
    _winmm.timeEndPeriod(_TIMER_RESOLUTION_MS)
    _timer_active = False
