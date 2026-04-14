# Windows Autoclicker v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fast, dark-themed Windows autoclicker with 1–100 CPS accuracy, toggle/hold global hotkeys, fixed-point and follow-cursor modes, wired through a protocol-driven architecture that makes v0.2 features drop-in extensions.

**Architecture:** Four-layer Python package. `win32/` holds all ctypes (SendInput, timing, hotkeys, hooks). `engine/` is Qt-free: immutable `ClickConfig`, a `ClickSource` producing `ClickAction`s, a `ClickSink` delivering them, and a `StopCondition` list consulted each tick. A single engine thread runs a sleep-then-spin scheduler on `QueryPerformanceCounter`. `hotkeys/` wraps a pluggable backend (real vs fake). `ui/` is PySide6 + qdarktheme. `app.py` is the only file that imports all three subsystems.

**Tech Stack:** Python 3.13, PySide6, qdarktheme, ctypes, pytest, ruff, uv.

**Spec:** `docs/superpowers/specs/2026-04-14-autoclicker-design.md`

---

## File Structure

Created / modified files and their responsibilities:

```
auto_clicker/
├── pyproject.toml                          # uv-managed, deps, ruff+pytest config
├── README.md                               # short usage notes
├── src/auto_clicker/
│   ├── __init__.py                         # version
│   ├── __main__.py                         # python -m auto_clicker entrypoint
│   ├── app.py                              # composition root: UI + hotkey + engine
│   │
│   ├── win32/
│   │   ├── __init__.py
│   │   ├── timing.py                       # QPC, timeBeginPeriod lifecycle
│   │   ├── input.py                        # INPUT/MOUSEINPUT structs, SendInput
│   │   ├── hotkey.py                       # RegisterHotKey/UnregisterHotKey, WM_HOTKEY pump
│   │   └── hooks.py                        # WH_KEYBOARD_LL / WH_MOUSE_LL installers
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── config.py                       # Button, CursorMode, TriggerMode, ClickAction, ClickConfig
│   │   ├── sinks.py                        # ClickSink protocol, SendInputSink, RecordingSink
│   │   ├── sources.py                      # ClickSource protocol, UniformSource
│   │   ├── stops.py                        # StopCondition protocol, TickContext, DurationLimit, ClickLimit
│   │   ├── scheduler.py                    # _wait_until, Scheduler.run()
│   │   └── engine.py                       # ClickEngine thread wrapper, EngineBusyError
│   │
│   ├── hotkeys/
│   │   ├── __init__.py
│   │   ├── backend.py                      # HotkeyBackend protocol + FakeBackend + Win32Backend
│   │   └── controller.py                   # HotkeyController: signals, toggle/hold modes
│   │
│   └── ui/
│       ├── __init__.py
│       ├── theme.py                        # qdarktheme wiring + accent color
│       ├── widgets/
│       │   ├── __init__.py
│       │   ├── hotkey_edit.py              # key-capture field
│       │   └── point_capture.py            # "Pick point" button + WH_MOUSE_LL capture
│       └── main_window.py                  # QMainWindow assembly + state indicator
│
└── tests/
    ├── __init__.py
    ├── conftest.py                         # shared fixtures
    ├── engine/
    │   ├── __init__.py
    │   ├── test_config.py
    │   ├── test_sinks.py
    │   ├── test_sources.py
    │   ├── test_stops.py
    │   ├── test_scheduler.py               # cadence / jitter / drift
    │   └── test_engine.py                  # start/stop, busy, stop conditions
    └── hotkeys/
        ├── __init__.py
        └── test_controller.py
```

---

## Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/auto_clicker/__init__.py`
- Create: `src/auto_clicker/__main__.py` (stub)
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `.gitignore`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "auto_clicker"
version = "0.1.0"
description = "Windows autoclicker with precise cadence and global hotkeys."
requires-python = ">=3.13"
dependencies = [
    "PySide6>=6.7",
    "pyqtdarktheme-fork>=2.3.2; python_version>='3.13'",
]

[project.scripts]
auto-clicker = "auto_clicker.__main__:main"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.6",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/auto_clicker"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-ra --strict-markers"

[tool.coverage.run]
source = ["src/auto_clicker"]
omit = [
    "src/auto_clicker/ui/*",
    "src/auto_clicker/win32/*",
    "src/auto_clicker/__main__.py",
    "src/auto_clicker/app.py",
]

[tool.coverage.report]
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "\\.\\.\\."]
fail_under = 80

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM", "RUF"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["N802"]
```

Note: `pyqtdarktheme` on PyPI is unmaintained for 3.13 as of writing — the `-fork` alternative is the drop-in replacement. If installation fails, adjust to `qdarktheme` and fall back to manual stylesheet in Task 16.

- [ ] **Step 2: Write `.gitignore`**

```
__pycache__/
*.py[cod]
.venv/
.uv-cache/
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.idea/
.vscode/
```

- [ ] **Step 3: Write `README.md`**

```markdown
# auto_clicker

Windows autoclicker (v0.1). Python 3.13 + PySide6.

## Dev

```
uv sync
uv run pytest
uv run python -m auto_clicker
```
```

- [ ] **Step 4: Write `src/auto_clicker/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 5: Write stub `src/auto_clicker/__main__.py`**

```python
def main() -> None:
    raise SystemExit("auto_clicker entrypoint not wired yet")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Write `tests/__init__.py` (empty) and `tests/conftest.py`**

```python
# tests/conftest.py
import sys

import pytest


@pytest.fixture(autouse=True)
def _ensure_windows_only(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("windows_only") and sys.platform != "win32":
        pytest.skip("Windows-only test")
```

- [ ] **Step 7: Bootstrap venv and run sanity check**

Run: `uv sync && uv run pytest -q`
Expected: `no tests ran in 0.XXs` (no failures).

- [ ] **Step 8: Commit**

```bash
git init -b main
git add .
git commit -m "chore: project scaffold with uv, ruff, pytest"
```

---

## Task 2: win32.timing — QPC + timeBeginPeriod

**Files:**
- Create: `src/auto_clicker/win32/__init__.py` (empty)
- Create: `src/auto_clicker/win32/timing.py`

No unit tests in this task — ctypes struct definitions are excluded from coverage per spec §9.6. Real behavior is exercised through the scheduler tests in Task 9.

- [ ] **Step 1: Write `src/auto_clicker/win32/timing.py`**

```python
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
```

- [ ] **Step 2: Quick import smoke (Windows only)**

Run: `uv run python -c "from auto_clicker.win32 import timing; print(timing.query_performance_frequency())"`
Expected: prints a positive integer (e.g. `10000000`).

- [ ] **Step 3: Commit**

```bash
git add src/auto_clicker/win32
git commit -m "feat(win32): QPC and timeBeginPeriod wrappers"
```

---

## Task 3: win32.input — SendInput and mouse structs

**Files:**
- Create: `src/auto_clicker/win32/input.py`

- [ ] **Step 1: Write `src/auto_clicker/win32/input.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/auto_clicker/win32/input.py
git commit -m "feat(win32): INPUT structs and send_click via SendInput"
```

---

## Task 4: engine.config — immutable config and actions

**Files:**
- Create: `src/auto_clicker/engine/__init__.py` (empty)
- Create: `src/auto_clicker/engine/config.py`
- Create: `tests/engine/__init__.py` (empty)
- Create: `tests/engine/test_config.py`

- [ ] **Step 1: Write failing test `tests/engine/test_config.py`**

```python
from __future__ import annotations

import dataclasses

import pytest

from auto_clicker.engine.config import (
    Button,
    ClickAction,
    ClickConfig,
    CursorMode,
    FixedPoint,
    FollowCursor,
    TriggerMode,
)


def test_click_config_is_frozen():
    cfg = ClickConfig(cps=10, button=Button.LEFT, cursor_mode=FollowCursor(), trigger_mode=TriggerMode.TOGGLE)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.cps = 20  # type: ignore[misc]


def test_click_config_rejects_out_of_range_cps():
    with pytest.raises(ValueError, match="cps must be in 1..100"):
        ClickConfig(cps=0, button=Button.LEFT, cursor_mode=FollowCursor(), trigger_mode=TriggerMode.TOGGLE)
    with pytest.raises(ValueError, match="cps must be in 1..100"):
        ClickConfig(cps=101, button=Button.LEFT, cursor_mode=FollowCursor(), trigger_mode=TriggerMode.TOGGLE)


def test_fixed_point_is_cursor_mode():
    fp = FixedPoint(x=100, y=200)
    assert isinstance(fp, CursorMode)
    assert (fp.x, fp.y) == (100, 200)


def test_follow_cursor_is_cursor_mode():
    assert isinstance(FollowCursor(), CursorMode)


def test_click_action_defaults():
    action = ClickAction(button=Button.LEFT)
    assert action.move_to is None


def test_click_action_with_move_target():
    action = ClickAction(button=Button.RIGHT, move_to=(10, 20))
    assert action.move_to == (10, 20)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/engine/test_config.py -v`
Expected: ImportError / ModuleNotFoundError for `auto_clicker.engine.config`.

- [ ] **Step 3: Write `src/auto_clicker/engine/config.py`**

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Button(Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class TriggerMode(Enum):
    TOGGLE = "toggle"
    HOLD = "hold"


class CursorMode:
    """Marker base. Concrete: FollowCursor, FixedPoint."""


@dataclass(frozen=True, slots=True)
class FollowCursor(CursorMode):
    pass


@dataclass(frozen=True, slots=True)
class FixedPoint(CursorMode):
    x: int
    y: int


@dataclass(frozen=True, slots=True)
class ClickAction:
    button: Button
    move_to: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True)
class ClickConfig:
    cps: int
    button: Button
    cursor_mode: CursorMode
    trigger_mode: TriggerMode

    def __post_init__(self) -> None:
        if not 1 <= self.cps <= 100:
            raise ValueError("cps must be in 1..100")
```

- [ ] **Step 4: Run test to verify pass**

Run: `uv run pytest tests/engine/test_config.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/auto_clicker/engine/__init__.py src/auto_clicker/engine/config.py tests/engine
git commit -m "feat(engine): ClickConfig, ClickAction, cursor/trigger modes"
```

---

## Task 5: engine.sinks — ClickSink protocol + RecordingSink

**Files:**
- Create: `src/auto_clicker/engine/sinks.py`
- Create: `tests/engine/test_sinks.py`

`SendInputSink` is covered here but not unit-tested (real clicks would be fired). Its correctness is exercised through manual end-to-end in Task 17.

- [ ] **Step 1: Write failing test `tests/engine/test_sinks.py`**

```python
from __future__ import annotations

from auto_clicker.engine.config import Button, ClickAction
from auto_clicker.engine.sinks import RecordingSink


def test_recording_sink_captures_actions():
    sink = RecordingSink()
    a1 = ClickAction(button=Button.LEFT)
    a2 = ClickAction(button=Button.RIGHT, move_to=(5, 7))
    sink.fire(a1)
    sink.fire(a2)
    assert [a for _, a in sink.events] == [a1, a2]


def test_recording_sink_timestamps_are_monotonic():
    sink = RecordingSink()
    for _ in range(5):
        sink.fire(ClickAction(button=Button.LEFT))
    timestamps = [t for t, _ in sink.events]
    assert timestamps == sorted(timestamps)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/engine/test_sinks.py -v`
Expected: ImportError.

- [ ] **Step 3: Write `src/auto_clicker/engine/sinks.py`**

```python
from __future__ import annotations

import sys
from typing import Protocol

from auto_clicker.engine.config import Button, ClickAction


class ClickSink(Protocol):
    def fire(self, action: ClickAction) -> None: ...


class RecordingSink:
    def __init__(self) -> None:
        self.events: list[tuple[int, ClickAction]] = []

    def fire(self, action: ClickAction) -> None:
        from auto_clicker.engine.scheduler import monotonic_ticks

        self.events.append((monotonic_ticks(), action))


if sys.platform == "win32":
    from auto_clicker.win32.input import MouseEventFlag, send_click

    _DOWN_UP: dict[Button, tuple[int, int]] = {
        Button.LEFT: (int(MouseEventFlag.LEFTDOWN), int(MouseEventFlag.LEFTUP)),
        Button.RIGHT: (int(MouseEventFlag.RIGHTDOWN), int(MouseEventFlag.RIGHTUP)),
        Button.MIDDLE: (int(MouseEventFlag.MIDDLEDOWN), int(MouseEventFlag.MIDDLEUP)),
    }

    class SendInputSink:
        def fire(self, action: ClickAction) -> None:
            down, up = _DOWN_UP[action.button]
            send_click(down, up, move_to=action.move_to)
```

Note: `RecordingSink` imports `monotonic_ticks` lazily to avoid pulling Windows-only `QueryPerformanceCounter` on non-Windows CI during import. We'll define it in Task 8.

- [ ] **Step 4: Commit (tests still red — `monotonic_ticks` missing)**

```bash
git add src/auto_clicker/engine/sinks.py tests/engine/test_sinks.py
git commit -m "feat(engine): ClickSink protocol + RecordingSink + SendInputSink"
```

---

## Task 6: engine.sources — ClickSource protocol + UniformSource

**Files:**
- Create: `src/auto_clicker/engine/sources.py`
- Create: `tests/engine/test_sources.py`

- [ ] **Step 1: Write failing test `tests/engine/test_sources.py`**

```python
from __future__ import annotations

from auto_clicker.engine.config import Button
from auto_clicker.engine.sources import UniformSource


def test_uniform_source_never_exhausts():
    src = UniformSource(button=Button.LEFT, move_to=None)
    for _ in range(1000):
        action = src.next()
        assert action is not None
        assert action.button == Button.LEFT
        assert action.move_to is None


def test_uniform_source_emits_fixed_point_move():
    src = UniformSource(button=Button.RIGHT, move_to=(100, 200))
    action = src.next()
    assert action is not None
    assert action.button == Button.RIGHT
    assert action.move_to == (100, 200)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/engine/test_sources.py -v`
Expected: ImportError.

- [ ] **Step 3: Write `src/auto_clicker/engine/sources.py`**

```python
from __future__ import annotations

from typing import Protocol

from auto_clicker.engine.config import Button, ClickAction


class ClickSource(Protocol):
    def next(self) -> ClickAction | None: ...


class UniformSource:
    def __init__(self, button: Button, move_to: tuple[int, int] | None) -> None:
        self._action = ClickAction(button=button, move_to=move_to)

    def next(self) -> ClickAction | None:
        return self._action
```

- [ ] **Step 4: Run test to verify pass**

Run: `uv run pytest tests/engine/test_sources.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/auto_clicker/engine/sources.py tests/engine/test_sources.py
git commit -m "feat(engine): ClickSource protocol + UniformSource"
```

---

## Task 7: engine.stops — StopCondition + TickContext + built-ins

**Files:**
- Create: `src/auto_clicker/engine/stops.py`
- Create: `tests/engine/test_stops.py`

- [ ] **Step 1: Write failing test `tests/engine/test_stops.py`**

```python
from __future__ import annotations

from auto_clicker.engine.stops import ClickLimit, DurationLimit, TickContext


def test_duration_limit_triggers_after_deadline():
    stop = DurationLimit(seconds=2.0)
    ctx_before = TickContext(click_count=0, elapsed_seconds=1.99)
    ctx_after = TickContext(click_count=0, elapsed_seconds=2.01)
    assert stop.should_stop(ctx_before) is False
    assert stop.should_stop(ctx_after) is True


def test_duration_limit_at_exact_boundary_stops():
    stop = DurationLimit(seconds=1.0)
    assert stop.should_stop(TickContext(click_count=0, elapsed_seconds=1.0)) is True


def test_click_limit_triggers_after_count():
    stop = ClickLimit(count=3)
    assert stop.should_stop(TickContext(click_count=0, elapsed_seconds=0.0)) is False
    assert stop.should_stop(TickContext(click_count=2, elapsed_seconds=0.0)) is False
    assert stop.should_stop(TickContext(click_count=3, elapsed_seconds=0.0)) is True
    assert stop.should_stop(TickContext(click_count=100, elapsed_seconds=0.0)) is True


def test_duration_limit_rejects_non_positive():
    import pytest

    with pytest.raises(ValueError):
        DurationLimit(seconds=0)
    with pytest.raises(ValueError):
        DurationLimit(seconds=-1)


def test_click_limit_rejects_non_positive():
    import pytest

    with pytest.raises(ValueError):
        ClickLimit(count=0)
    with pytest.raises(ValueError):
        ClickLimit(count=-5)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/engine/test_stops.py -v`
Expected: ImportError.

- [ ] **Step 3: Write `src/auto_clicker/engine/stops.py`**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TickContext:
    click_count: int
    elapsed_seconds: float


class StopCondition(Protocol):
    def should_stop(self, ctx: TickContext) -> bool: ...


@dataclass(frozen=True, slots=True)
class DurationLimit:
    seconds: float

    def __post_init__(self) -> None:
        if self.seconds <= 0:
            raise ValueError("seconds must be positive")

    def should_stop(self, ctx: TickContext) -> bool:
        return ctx.elapsed_seconds >= self.seconds


@dataclass(frozen=True, slots=True)
class ClickLimit:
    count: int

    def __post_init__(self) -> None:
        if self.count <= 0:
            raise ValueError("count must be positive")

    def should_stop(self, ctx: TickContext) -> bool:
        return ctx.click_count >= self.count
```

- [ ] **Step 4: Run test to verify pass**

Run: `uv run pytest tests/engine/test_stops.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/auto_clicker/engine/stops.py tests/engine/test_stops.py
git commit -m "feat(engine): StopCondition protocol + DurationLimit + ClickLimit"
```

---

## Task 8: engine.scheduler — precise wait loop

**Files:**
- Create: `src/auto_clicker/engine/scheduler.py`
- Create: `tests/engine/test_scheduler.py`

The scheduler is the single perf-critical piece. Tests exercise the real `QueryPerformanceCounter` with `RecordingSink` (no real clicks fired). Tests are marked `windows_only` per §9.1 and skipped on other platforms.

- [ ] **Step 1: Write failing test `tests/engine/test_scheduler.py`**

```python
from __future__ import annotations

import sys

import pytest

from auto_clicker.engine.config import Button, ClickConfig, FollowCursor, TriggerMode
from auto_clicker.engine.scheduler import Scheduler
from auto_clicker.engine.sinks import RecordingSink
from auto_clicker.engine.sources import UniformSource
from auto_clicker.engine.stops import ClickLimit

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="scheduler requires QPC")


def _run_and_collect(cps: int, target_clicks: int) -> list[int]:
    sink = RecordingSink()
    source = UniformSource(button=Button.LEFT, move_to=None)
    config = ClickConfig(cps=cps, button=Button.LEFT, cursor_mode=FollowCursor(), trigger_mode=TriggerMode.TOGGLE)
    scheduler = Scheduler(sink=sink)
    scheduler.run(config=config, source=source, stops=[ClickLimit(count=target_clicks)])
    return [ts for ts, _ in sink.events]


def test_average_cadence_within_one_percent_at_50_cps():
    from auto_clicker.engine.scheduler import ticks_per_second

    freq = ticks_per_second()
    stamps = _run_and_collect(cps=50, target_clicks=100)
    assert len(stamps) == 100
    duration = (stamps[-1] - stamps[0]) / freq
    expected = 99 / 50  # 99 intervals
    assert abs(duration - expected) / expected < 0.01


def test_per_click_jitter_p99_within_one_percent_at_100_cps():
    from auto_clicker.engine.scheduler import ticks_per_second

    freq = ticks_per_second()
    stamps = _run_and_collect(cps=100, target_clicks=500)
    intervals_ms = [(stamps[i + 1] - stamps[i]) * 1000 / freq for i in range(len(stamps) - 1)]
    intervals_ms.sort()
    p99 = intervals_ms[int(len(intervals_ms) * 0.99)]
    assert abs(p99 - 10.0) / 10.0 < 0.01, f"p99={p99}ms"


def test_no_drift_over_long_run_at_20_cps():
    from auto_clicker.engine.scheduler import ticks_per_second

    freq = ticks_per_second()
    stamps = _run_and_collect(cps=20, target_clicks=200)  # 10s
    duration = (stamps[-1] - stamps[0]) / freq
    expected = 199 / 20
    assert abs(duration - expected) / expected < 0.01
```

Note: spec §9.1 mentions 1000 clicks at 20 CPS (50s). That's too slow for a tight CI loop — I dropped it to 200 clicks/10s while preserving the drift signal. If wall-clock drift ever shows up as a regression, bump this back to 1000.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/engine/test_scheduler.py -v`
Expected: ImportError.

- [ ] **Step 3: Write `src/auto_clicker/engine/scheduler.py`**

```python
from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass

from auto_clicker.engine.config import ClickConfig
from auto_clicker.engine.sinks import ClickSink
from auto_clicker.engine.sources import ClickSource
from auto_clicker.engine.stops import StopCondition, TickContext

if sys.platform == "win32":
    from auto_clicker.win32.timing import (
        begin_timer_period,
        query_performance_counter,
        query_performance_frequency,
    )

    def monotonic_ticks() -> int:
        return query_performance_counter()

    def ticks_per_second() -> int:
        return query_performance_frequency()

else:  # pragma: no cover - CI convenience
    _FAKE_FREQ = 10_000_000

    def monotonic_ticks() -> int:
        return time.perf_counter_ns() * _FAKE_FREQ // 1_000_000_000

    def ticks_per_second() -> int:
        return _FAKE_FREQ

    def begin_timer_period() -> None:
        return None


@dataclass
class Scheduler:
    sink: ClickSink
    _stop_flag: threading.Event = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self._stop_flag is None:
            self._stop_flag = threading.Event()

    def request_stop(self) -> None:
        self._stop_flag.set()

    def run(
        self,
        config: ClickConfig,
        source: ClickSource,
        stops: list[StopCondition],
    ) -> None:
        begin_timer_period()
        self._stop_flag.clear()

        freq = ticks_per_second()
        interval_ticks = freq // config.cps
        start_tick = monotonic_ticks()
        next_tick = start_tick + interval_ticks
        click_count = 0

        while not self._stop_flag.is_set():
            now = monotonic_ticks()
            ctx = TickContext(
                click_count=click_count,
                elapsed_seconds=(now - start_tick) / freq,
            )
            if any(s.should_stop(ctx) for s in stops):
                return

            action = source.next()
            if action is None:
                return

            self._wait_until(next_tick, freq)
            self.sink.fire(action)
            click_count += 1
            next_tick += interval_ticks

    @staticmethod
    def _wait_until(target_tick: int, freq: int) -> None:
        spin_margin = freq // 1000  # 1 ms
        while True:
            now = monotonic_ticks()
            remaining = target_tick - now
            if remaining <= 0:
                return
            if remaining > spin_margin:
                sleep_ms = (remaining - spin_margin) * 1000 // freq
                if sleep_ms > 0:
                    time.sleep(sleep_ms / 1000)
```

- [ ] **Step 4: Run all engine tests (sinks test now resolves)**

Run: `uv run pytest tests/engine -v`
Expected: all pass on Windows; scheduler tests skip elsewhere.

- [ ] **Step 5: Commit**

```bash
git add src/auto_clicker/engine/scheduler.py tests/engine/test_scheduler.py
git commit -m "feat(engine): precise sleep-then-spin Scheduler over QPC"
```

---

## Task 9: engine.engine — thread wrapper + lifecycle

**Files:**
- Create: `src/auto_clicker/engine/engine.py`
- Create: `tests/engine/test_engine.py`

- [ ] **Step 1: Write failing test `tests/engine/test_engine.py`**

```python
from __future__ import annotations

import sys
import time

import pytest

from auto_clicker.engine.config import Button, ClickConfig, FollowCursor, TriggerMode
from auto_clicker.engine.engine import ClickEngine, EngineBusyError
from auto_clicker.engine.sinks import RecordingSink
from auto_clicker.engine.stops import ClickLimit, DurationLimit

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="engine relies on QPC scheduler")


def _cfg(cps: int = 50) -> ClickConfig:
    return ClickConfig(cps=cps, button=Button.LEFT, cursor_mode=FollowCursor(), trigger_mode=TriggerMode.TOGGLE)


def test_engine_start_then_stop_records_clicks():
    sink = RecordingSink()
    engine = ClickEngine(sink=sink)
    engine.start(config=_cfg(50), stops=[DurationLimit(seconds=0.5)])
    engine.wait_until_idle(timeout=2.0)
    assert 20 <= len(sink.events) <= 30


def test_click_limit_stops_after_exact_count():
    sink = RecordingSink()
    engine = ClickEngine(sink=sink)
    engine.start(config=_cfg(50), stops=[ClickLimit(count=10)])
    engine.wait_until_idle(timeout=2.0)
    assert len(sink.events) == 10


def test_start_start_raises_while_running():
    sink = RecordingSink()
    engine = ClickEngine(sink=sink)
    engine.start(config=_cfg(20), stops=[DurationLimit(seconds=1.0)])
    try:
        with pytest.raises(EngineBusyError):
            engine.start(config=_cfg(20), stops=[DurationLimit(seconds=0.1)])
    finally:
        engine.stop()
        engine.wait_until_idle(timeout=2.0)


def test_stop_is_quick_within_one_interval():
    sink = RecordingSink()
    engine = ClickEngine(sink=sink)
    engine.start(config=_cfg(10), stops=[DurationLimit(seconds=10.0)])
    time.sleep(0.3)
    t0 = time.perf_counter()
    engine.stop()
    engine.wait_until_idle(timeout=1.0)
    assert time.perf_counter() - t0 < 0.2


def test_thread_is_reused_across_runs():
    sink = RecordingSink()
    engine = ClickEngine(sink=sink)
    engine.start(config=_cfg(50), stops=[ClickLimit(count=5)])
    engine.wait_until_idle(timeout=1.0)
    first_thread = engine._thread
    engine.start(config=_cfg(50), stops=[ClickLimit(count=5)])
    engine.wait_until_idle(timeout=1.0)
    assert engine._thread is first_thread
    engine.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/engine/test_engine.py -v`
Expected: ImportError.

- [ ] **Step 3: Write `src/auto_clicker/engine/engine.py`**

```python
from __future__ import annotations

import threading
from dataclasses import dataclass, field

from auto_clicker.engine.config import ClickConfig, FixedPoint
from auto_clicker.engine.scheduler import Scheduler
from auto_clicker.engine.sinks import ClickSink
from auto_clicker.engine.sources import UniformSource
from auto_clicker.engine.stops import StopCondition


class EngineBusyError(RuntimeError):
    pass


@dataclass
class _Command:
    config: ClickConfig
    stops: list[StopCondition]


@dataclass
class ClickEngine:
    sink: ClickSink
    _scheduler: Scheduler = field(init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    _cmd: _Command | None = field(default=None, init=False)
    _cmd_ready: threading.Event = field(default_factory=threading.Event, init=False)
    _idle: threading.Event = field(default_factory=threading.Event, init=False)
    _shutdown: bool = field(default=False, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        self._scheduler = Scheduler(sink=self.sink)
        self._idle.set()

    def start(self, config: ClickConfig, stops: list[StopCondition]) -> None:
        with self._lock:
            if not self._idle.is_set():
                raise EngineBusyError("engine already running")
            self._cmd = _Command(config=config, stops=list(stops))
            self._idle.clear()
            if self._thread is None:
                self._thread = threading.Thread(target=self._loop, name="ClickEngine", daemon=True)
                self._thread.start()
            self._cmd_ready.set()

    def stop(self) -> None:
        self._scheduler.request_stop()

    def wait_until_idle(self, timeout: float | None = None) -> bool:
        return self._idle.wait(timeout=timeout)

    def shutdown(self) -> None:
        with self._lock:
            self._shutdown = True
            self._scheduler.request_stop()
            self._cmd_ready.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _loop(self) -> None:
        while True:
            self._cmd_ready.wait()
            self._cmd_ready.clear()
            if self._shutdown:
                return
            cmd = self._cmd
            self._cmd = None
            assert cmd is not None
            try:
                source = UniformSource(
                    button=cmd.config.button,
                    move_to=(cmd.config.cursor_mode.x, cmd.config.cursor_mode.y)
                    if isinstance(cmd.config.cursor_mode, FixedPoint)
                    else None,
                )
                self._scheduler.run(config=cmd.config, source=source, stops=cmd.stops)
            finally:
                self._idle.set()
```

- [ ] **Step 4: Run engine tests**

Run: `uv run pytest tests/engine/test_engine.py -v`
Expected: 5 passed on Windows.

- [ ] **Step 5: Run full engine suite with coverage**

Run: `uv run pytest tests/engine --cov=src/auto_clicker/engine --cov-report=term-missing`
Expected: pass, ≥80% coverage on engine modules.

- [ ] **Step 6: Commit**

```bash
git add src/auto_clicker/engine/engine.py tests/engine/test_engine.py
git commit -m "feat(engine): ClickEngine thread wrapper with reusable worker thread"
```

---

## Task 10: win32.hotkey — RegisterHotKey + WM_HOTKEY polling

**Files:**
- Create: `src/auto_clicker/win32/hotkey.py`

This module is thin ctypes plumbing. Behavior is exercised via the `HotkeyController` tests (with fake backend) and manual verification.

- [ ] **Step 1: Write `src/auto_clicker/win32/hotkey.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/auto_clicker/win32/hotkey.py
git commit -m "feat(win32): RegisterHotKey / UnregisterHotKey bindings"
```

---

## Task 11: win32.hooks — low-level keyboard + mouse hooks

**Files:**
- Create: `src/auto_clicker/win32/hooks.py`

- [ ] **Step 1: Write `src/auto_clicker/win32/hooks.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/auto_clicker/win32/hooks.py
git commit -m "feat(win32): WH_KEYBOARD_LL and WH_MOUSE_LL installers"
```

---

## Task 12: hotkeys.backend — pluggable backend + fake

**Files:**
- Create: `src/auto_clicker/hotkeys/__init__.py` (empty)
- Create: `src/auto_clicker/hotkeys/backend.py`

- [ ] **Step 1: Write `src/auto_clicker/hotkeys/backend.py`**

```python
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
    import ctypes
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
```

- [ ] **Step 2: Commit**

```bash
git add src/auto_clicker/hotkeys
git commit -m "feat(hotkeys): pluggable HotkeyBackend protocol + FakeBackend + Win32Backend"
```

---

## Task 13: hotkeys.controller — orchestration layer

**Files:**
- Create: `src/auto_clicker/hotkeys/controller.py`
- Create: `tests/hotkeys/__init__.py` (empty)
- Create: `tests/hotkeys/test_controller.py`

The controller emits callbacks (not Qt signals) so it stays Qt-free and testable. The UI layer will adapt these into Qt signals.

- [ ] **Step 1: Write failing test `tests/hotkeys/test_controller.py`**

```python
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
    assert backend.history == ["toggle:117", "clear", "toggle:118"]


def test_switching_modes_reregisters():
    backend = FakeBackend()
    ctrl, _ = _controller(backend)
    ctrl.set_binding(KeyBinding(vk=0x75), TriggerMode.TOGGLE)
    ctrl.set_binding(KeyBinding(vk=0x75), TriggerMode.HOLD)
    assert backend.history == ["toggle:117", "clear", "hold:117"]


def test_clear_removes_everything():
    backend = FakeBackend()
    ctrl, _ = _controller(backend)
    ctrl.set_binding(KeyBinding(vk=0x75), TriggerMode.TOGGLE)
    ctrl.clear()
    assert backend.history[-1] == "clear"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/hotkeys/test_controller.py -v`
Expected: ImportError.

- [ ] **Step 3: Write `src/auto_clicker/hotkeys/controller.py`**

```python
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
```

- [ ] **Step 4: Run test to verify pass**

Run: `uv run pytest tests/hotkeys -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/auto_clicker/hotkeys/controller.py tests/hotkeys
git commit -m "feat(hotkeys): HotkeyController with toggle/hold modes and rebinding"
```

---

## Task 14: ui.theme — qdarktheme setup

**Files:**
- Create: `src/auto_clicker/ui/__init__.py` (empty)
- Create: `src/auto_clicker/ui/theme.py`

- [ ] **Step 1: Write `src/auto_clicker/ui/theme.py`**

```python
from __future__ import annotations

from PySide6.QtWidgets import QApplication

ACCENT = "#5EC8D6"


def apply_theme(app: QApplication) -> None:
    try:
        import qdarktheme  # type: ignore[import-not-found]

        qdarktheme.setup_theme("dark", custom_colors={"primary": ACCENT})
    except ImportError:
        app.setStyleSheet(_FALLBACK_DARK)


_FALLBACK_DARK = """
    QWidget { background-color: #1e1e1e; color: #e0e0e0; }
    QPushButton { background-color: #2d2d2d; border: 1px solid #3a3a3a; padding: 6px 12px; }
    QPushButton:hover { background-color: #383838; }
    QPushButton#primary { background-color: #5EC8D6; color: #1e1e1e; font-weight: 600; }
    QLineEdit, QSpinBox { background-color: #2d2d2d; border: 1px solid #3a3a3a; padding: 4px; }
    QRadioButton, QCheckBox { spacing: 8px; }
"""
```

- [ ] **Step 2: Commit**

```bash
git add src/auto_clicker/ui/__init__.py src/auto_clicker/ui/theme.py
git commit -m "feat(ui): qdarktheme wiring with stylesheet fallback"
```

---

## Task 15: ui.widgets — HotkeyEdit and PointCapture

**Files:**
- Create: `src/auto_clicker/ui/widgets/__init__.py` (empty)
- Create: `src/auto_clicker/ui/widgets/hotkey_edit.py`
- Create: `src/auto_clicker/ui/widgets/point_capture.py`

- [ ] **Step 1: Write `src/auto_clicker/ui/widgets/hotkey_edit.py`**

```python
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from auto_clicker.hotkeys.backend import KeyBinding

_VK_MAP = {
    Qt.Key.Key_F1: 0x70, Qt.Key.Key_F2: 0x71, Qt.Key.Key_F3: 0x72, Qt.Key.Key_F4: 0x73,
    Qt.Key.Key_F5: 0x74, Qt.Key.Key_F6: 0x75, Qt.Key.Key_F7: 0x76, Qt.Key.Key_F8: 0x77,
    Qt.Key.Key_F9: 0x78, Qt.Key.Key_F10: 0x79, Qt.Key.Key_F11: 0x7A, Qt.Key.Key_F12: 0x7B,
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
```

- [ ] **Step 2: Write `src/auto_clicker/ui/widgets/point_capture.py`**

```python
from __future__ import annotations

import sys

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from auto_clicker.engine.config import FixedPoint


class PointCapture(QWidget):
    captured = Signal(object)  # FixedPoint

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._button = QPushButton("Pick point")
        self._label = QLabel("—")
        self._button.clicked.connect(self._arm)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._button)
        layout.addWidget(self._label, 1)
        self._hook = None  # type: ignore[assignment]

    def _arm(self) -> None:
        if sys.platform != "win32":
            self._label.setText("Windows only")
            return
        from auto_clicker.win32 import hooks

        self._button.setText("Click anywhere…")

        def on_event(msg: int, x: int, y: int) -> bool:
            if msg == hooks.WM_LBUTTONDOWN:
                self._finish(x, y)
                return True
            return False

        self._hook = hooks.install_mouse_hook(on_event)

    def _finish(self, x: int, y: int) -> None:
        if self._hook is not None:
            self._hook.unhook()
            self._hook = None
        self._button.setText("Pick point")
        self._label.setText(f"Fixed at {x}, {y}")
        self.captured.emit(FixedPoint(x=x, y=y))
```

- [ ] **Step 3: Commit**

```bash
git add src/auto_clicker/ui/widgets
git commit -m "feat(ui): HotkeyEdit and PointCapture widgets"
```

---

## Task 16: ui.main_window — single window assembly

**Files:**
- Create: `src/auto_clicker/ui/main_window.py`

- [ ] **Step 1: Write `src/auto_clicker/ui/main_window.py`**

```python
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
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
```

- [ ] **Step 2: Commit**

```bash
git add src/auto_clicker/ui/main_window.py
git commit -m "feat(ui): MainWindow assembly with config form + state indicator"
```

---

## Task 17: app.py + __main__ — composition root

**Files:**
- Modify: `src/auto_clicker/__main__.py`
- Create: `src/auto_clicker/app.py`

- [ ] **Step 1: Write `src/auto_clicker/app.py`**

```python
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

        msg = ctypes.cast(int(message), ctypes.POINTER(ctypes.c_byte * 48))
        # Decode MSG struct manually: hwnd, message, wParam, lParam, time, pt
        raw = ctypes.string_at(int(message), 48)
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
```

- [ ] **Step 2: Overwrite `src/auto_clicker/__main__.py`**

```python
from __future__ import annotations

from auto_clicker.app import main


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest --cov --cov-report=term-missing`
Expected: all tests pass; coverage on `engine/` and `hotkeys/` ≥ 80%.

- [ ] **Step 4: Manual smoke run**

Run: `uv run python -m auto_clicker`
Manual verification checklist:
- [ ] Window opens with dark theme.
- [ ] `● Idle` indicator visible.
- [ ] Press F6 → indicator turns green, start button shows `STOP`, clicks land in a scratch text editor.
- [ ] Press F6 again → returns to Idle.
- [ ] Change CPS to 50 while idle, toggle again → cadence visibly faster.
- [ ] Switch to Hold mode, hold F6 → clicks while held, stops on release.
- [ ] Click "Pick point", then click somewhere → label shows "Fixed at X, Y"; next start clicks that point regardless of cursor location.
- [ ] Enable `Duration` = 2 seconds → run stops itself after ~2s.
- [ ] Enable `Click count` = 25 → run stops after 25 clicks.
- [ ] Change hotkey from F6 to F7 → new key works, old does not.

If any item fails, file a bug and fix before declaring v0.1 done.

- [ ] **Step 5: Commit**

```bash
git add src/auto_clicker/app.py src/auto_clicker/__main__.py
git commit -m "feat: wire UI, hotkey controller, and engine in composition root"
```

---

## Task 18: Final verification and polish

**Files:** none (verification only)

- [ ] **Step 1: Run lint**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: clean.

- [ ] **Step 2: Run full coverage**

Run: `uv run pytest --cov --cov-report=term-missing --cov-fail-under=80`
Expected: pass.

- [ ] **Step 3: Verify spec §9 acceptance criteria one more time**

- [ ] 100 clicks @ 50 CPS: avg duration within ±1% of 2.0s (scheduler test).
- [ ] 500 clicks @ 100 CPS: p99 interval within ±1% of 10ms (scheduler test).
- [ ] No cumulative drift at 20 CPS (scheduler test).
- [ ] `DurationLimit` stops within one tick of deadline (engine test).
- [ ] `ClickLimit` stops after exactly N clicks (engine test).
- [ ] Start → stop → start reuses the worker thread (engine test).
- [ ] `EngineBusyError` raised when re-starting during a run (engine test).
- [ ] Hotkey toggle/hold/rebind signal flow verified via fake backend (controller tests).

- [ ] **Step 4: Commit any polish fixes**

```bash
git add -u
git commit -m "chore: final polish for v0.1"
```

---

## Plan Self-Review Notes

- **Spec coverage:** §1 goals (1–100 CPS, toggle/hold, fixed/follow, L/R/M, dark theme, single window) → Tasks 4, 9, 15, 16. §3 boundaries → Tasks 2–13 enforce the layering (`engine/` has no Qt, `win32/` isolates ctypes). §5 seams (`StopCondition`, `ClickSource`, `ClickSink`) → Tasks 5, 6, 7 define the protocols with built-ins; v0.2 features drop in as new implementations. §6 scheduler internals → Task 8 mirrors spec code exactly (sleep-then-spin, `next_tick += interval_ticks`, `SPIN_MARGIN_TICKS`). §7 hotkey controller (toggle via `RegisterHotKey`, hold via `WH_KEYBOARD_LL`, pick-point via `WH_MOUSE_LL`, runtime rebinding) → Tasks 10–13, 15. §8 UI layout → Task 16 covers all labeled controls + state indicator + disable-while-running. §9 tests → Tasks 4–9, 13 produce the suite; §9.1 clarification noted in Task 8 (reduced drift test from 1000→200 clicks for CI speed). §11 build order → Tasks 2–17 follow it.
- **Deferred v0.2 items** (system tray, light-mode toggle, script/pattern sources, stop-on-focus-loss, etc.) explicitly not implemented — per spec §1 non-goals. Extension seams are in place.
- **Placeholder scan:** No "TBD" / "handle edge cases" steps. Every code step has complete code. Every test step has the assertions. Commands include expected output.
- **Type consistency:** `ClickConfig`, `ClickAction`, `FixedPoint`, `FollowCursor`, `Button`, `TriggerMode`, `KeyBinding`, `TickContext`, `HotkeyController` method names (`set_binding`, `clear`, `mark_idle`) used consistently across Tasks 4–17. `monotonic_ticks` / `ticks_per_second` defined in Task 8 are referenced by the lazy import in Task 5's `RecordingSink` — intentional forward reference, noted in Task 5 step 4.

---
