# Windows Autoclicker — v0.1 Design

**Date:** 2026-04-14
**Status:** Approved for planning
**Scope:** v0.1 MVP. v0.2 features called out as extension points only; not built now.

---

## 1. Goals and non-goals

### Goals

- Fast, extensible, dark-themed Windows autoclicker.
- Accurate click cadence: 1–100 CPS, average-over-run and per-click p99 within ±1% of target.
- Toggle and hold trigger modes via a global hotkey that works when the window is unfocused.
- Fixed-point and follow-cursor click modes.
- Left, right, middle mouse buttons.
- Single-window GUI, no installer, in-memory config only.
- Architecture shaped so every v0.2 feature slots in through a well-defined protocol.

### Non-goals (v0.1)

- CPS above 100. Relaxed cadence contract at very high rates is deferred.
- Click patterns / macros, scripting hooks, per-app profiles, save/load — all v0.2.
- System tray, installer, auto-update.
- Light theme toggle.
- Stop-on-monitor-change, stop-on-focus-loss, stop-on-pixel-color — v0.2, but the extension seam lands in v0.1.

---

## 2. Stack

- **Language / runtime:** Python 3.12.
- **GUI:** PySide6 + `qdarktheme`.
- **Win32 bindings:** `ctypes` (no `pywin32` dependency — we only need ~10 functions).
- **Tooling:** `uv` (package/env), `pytest` (tests), `ruff` (+ `ruff format`).
- **Distribution (later):** `pyinstaller` one-file build.

### Why Python + PySide6 for v0.1

- Iteration speed. `ctypes → SendInput` is the same bottleneck the Rust and C# paths hit — the Windows input queue is the rate limiter, not the language.
- PyInstaller one-file produces a single `.exe` that's acceptable until the tool has users.
- The only perf-sensitive module (`ClickEngine`) is pure Python + ctypes with zero Qt dependencies, so a future Rust port is a narrow, contained piece of work.

---

## 3. Architecture overview

Four components, each behind a narrow interface:

```
┌─────────────────────────────────────────────────┐
│  PySide6 UI (main thread, Qt event loop)        │
│  - config form, state display, capture button   │
└──────┬──────────────────────────────┬───────────┘
       │ settings (immutable snapshot)│ start/stop commands
       ▼                              ▼
┌─────────────────────┐    ┌──────────────────────┐
│ HotkeyController    │    │ ClickEngine          │
│ (main thread)       │    │ (dedicated thread)   │
│ - RegisterHotKey    │───▶│ - precise scheduler  │
│ - WH_KEYBOARD_LL    │    │ - ClickSink protocol │
│ (hold mode only)    │    │ - start/stop signal  │
└─────────────────────┘    └──────────┬───────────┘
                                      │ INPUT structs
                                      ▼
                           ┌──────────────────────┐
                           │ ClickSink (protocol) │
                           │ - SendInputSink      │
                           │ - RecordingSink(test)│
                           └──────────────────────┘
```

**Boundaries:**

- **ClickEngine** knows nothing about Qt. Pure Python + ctypes. Standalone-testable.
- **HotkeyController** owns all hotkey/hook plumbing. Emits abstract signals (`start_requested`, `stop_requested`, `hold_started`, `hold_ended`). UI and engine subscribe.
- **UI** owns config state, builds immutable `ClickConfig` snapshots, passes them to the engine. No direct Win32 calls from UI code.
- **ClickSink** is the injectable seam. Production uses `SendInputSink`; tests use `RecordingSink`.

The composition root is `app.py` — the only module that imports from all three subsystems.

---

## 4. Module layout

```
auto_clicker/
├── pyproject.toml              # uv-managed, Python 3.12
├── README.md
├── src/
│   └── auto_clicker/
│       ├── __init__.py
│       ├── __main__.py         # entry: python -m auto_clicker
│       ├── app.py              # wires UI + hotkey + engine
│       │
│       ├── engine/             # standalone, no Qt, no UI
│       │   ├── __init__.py
│       │   ├── config.py       # ClickConfig, ClickAction, enums
│       │   ├── scheduler.py    # precise sleep-then-spin loop
│       │   ├── engine.py       # ClickEngine thread wrapper
│       │   ├── sources.py      # ClickSource protocol + UniformSource
│       │   ├── stops.py        # StopCondition protocol + built-ins
│       │   └── sinks.py        # ClickSink protocol + Send/Recording sinks
│       │
│       ├── win32/              # thin ctypes wrappers, no app logic
│       │   ├── __init__.py
│       │   ├── input.py        # SendInput, INPUT/MOUSEINPUT
│       │   ├── timing.py       # timeBeginPeriod, QueryPerformanceCounter
│       │   ├── hotkey.py       # RegisterHotKey, WM_HOTKEY pump
│       │   └── hooks.py        # WH_KEYBOARD_LL, WH_MOUSE_LL
│       │
│       ├── hotkeys/
│       │   ├── __init__.py
│       │   └── controller.py   # HotkeyController (toggle + hold)
│       │
│       └── ui/
│           ├── __init__.py
│           ├── theme.py        # qdarktheme setup
│           ├── main_window.py  # single QMainWindow
│           └── widgets/        # HotkeyEdit, PointCapture, etc.
│
└── tests/
    ├── engine/
    │   ├── test_scheduler.py   # cadence accuracy (real QPC + RecordingSink)
    │   ├── test_engine.py      # start/stop, config snapshots
    │   ├── test_stops.py
    │   └── test_config.py
    ├── hotkeys/
    │   └── test_controller.py  # with fake Win32 backend
    └── conftest.py
```

### Why this shape

- `engine/` has zero Qt/UI imports — the Rust-port target.
- `win32/` is the only place ctypes lives. Other modules talk to Python objects.
- `hotkeys/` is its own package because v0.2 macro bindings extend it; keeping it separate avoids coupling to UI.
- `app.py` is the only file that touches all three subsystems.
- `tests/` mirrors `src/` structure. No `tests/ui/` in v0.1 — UI is manually verified; visual regression is overkill for one window.

---

## 5. Extensibility seams

Three protocols carry v0.2 features without core changes.

### 5.1 `StopCondition`

```python
class StopCondition(Protocol):
    def should_stop(self, ctx: TickContext) -> bool: ...
```

The engine evaluates every registered `StopCondition` before firing each click. Any returns `True` → engine stops gracefully.

**v0.1 built-ins:**

- `DurationLimit(seconds)` — stop after N seconds of wall time.
- `ClickLimit(count)` — stop after N clicks.

**v0.2 examples that drop in without core changes:**

- `StopOnMonitorChange` — capture starting monitor from `GetCursorPos()` on arm; stop when the cursor's monitor differs.
- `StopOnFocusLoss` — watch `GetForegroundWindow()`.
- `StopOnEscape` — low-level keyboard hook for Esc.
- `StopOnPixelColor` — `GetPixel` check.

### 5.2 `ClickSource`

```python
class ClickSource(Protocol):
    def next(self) -> ClickAction | None: ...  # None = exhausted
```

- v0.1: `UniformSource(button, cps)` — infinite stream of identical clicks at fixed cadence.
- v0.2: `PatternSource([...])` — scripted sequences with per-step delays.
- v0.2: `ScriptSource(user_fn)` — Python/Lua hook returns the next action.

The scheduler loop does not change between v0.1 and v0.2. Only the source changes.

### 5.3 `ClickSink`

Covered in §3. The same seam that makes testing easy also absorbs v0.2 delivery variants:

- `DirectXSink` — `SendInput` with scancode flags for games that filter synthesized input.
- `WindowMessageSink` — `PostMessage(WM_LBUTTONDOWN)` to a specific `hwnd` for background-window clicks.

### Mapping of v0.2 features to seams

| Feature | Seam |
|---------|------|
| Click patterns / macros | New `ClickSource` |
| Per-app profiles | Config layer; UI loads a different `ClickConfig` when target window matches |
| Lua/Python scripting | New `ClickSource` (`ScriptSource`) |
| Save/load profiles | Serialize `ClickConfig` (frozen dataclass, JSON-friendly) |
| Stop on monitor change | New `StopCondition` |
| Stop on focus loss | New `StopCondition` |
| Background-window clicks | New `ClickSink` (`WindowMessageSink`) |

---

## 6. Click engine internals

### 6.1 Thread model

- One engine thread, spawned lazily on first `start()`, reused across start/stop cycles. Parked on a wait condition when idle.
- Main thread submits immutable `ClickConfig` + `list[StopCondition]` via a thread-safe command queue.
- `timeBeginPeriod(1)` set when the engine thread starts; `timeEndPeriod(1)` called from an `atexit` handler. Not toggled per-run — thousands of toggles per session provide no benefit.
- Changing settings while running requires stop → rebuild snapshot → restart. No partial hot-reload in v0.1.

### 6.2 `ClickConfig`

```python
@dataclass(frozen=True, slots=True)
class ClickConfig:
    cps: int                          # 1..100
    button: Button                    # LEFT | RIGHT | MIDDLE
    cursor_mode: CursorMode           # FIXED(x, y) | FOLLOW
    trigger_mode: TriggerMode         # TOGGLE | HOLD
```

Frozen so it is safe to share across threads without locks.

### 6.3 Scheduler loop

```python
def run(self, config: ClickConfig, stops: list[StopCondition]) -> None:
    qpc_freq = query_performance_frequency()
    interval_ticks = qpc_freq // config.cps
    next_tick = query_performance_counter() + interval_ticks
    source = UniformSource(config.button, config.cps)

    while not self._stop_flag.is_set():
        ctx = TickContext(...)
        if any(s.should_stop(ctx) for s in stops):
            break

        action = source.next()
        if action is None:
            break

        self._wait_until(next_tick, qpc_freq)
        self._sink.fire(action)
        next_tick += interval_ticks


def _wait_until(self, target_qpc: int, freq: int) -> None:
    SPIN_MARGIN_TICKS = freq // 1000  # 1 ms in QPC ticks
    while True:
        now = query_performance_counter()
        remaining = target_qpc - now
        if remaining <= 0:
            return
        if remaining > SPIN_MARGIN_TICKS:
            sleep_ms = (remaining - SPIN_MARGIN_TICKS) * 1000 // freq
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000)
        # else: busy-spin until target
```

**Why this works:**

- `time.sleep` with `timeBeginPeriod(1)` active is accurate to ~1 ms but has jitter.
- We sleep conservatively until within 1 ms of target, then busy-spin on `QueryPerformanceCounter`. Spin cost: ~1 ms CPU per click × 100 CPS = 10% of one core at max CPS — acceptable.
- `next_tick += interval_ticks` (not `now + interval_ticks`) prevents cumulative drift: if one click fires late, the next aims for its original slot.

### 6.4 `ClickSink` implementations

```python
class SendInputSink:
    def fire(self, action: ClickAction) -> None:
        if action.move_to is not None:
            _send_mouse_move(action.move_to)   # MOUSEEVENTF_ABSOLUTE | MOVE
        _send_mouse_button(action.button, down=True)
        _send_mouse_button(action.button, down=False)


class RecordingSink:
    def __init__(self) -> None:
        self.events: list[tuple[int, ClickAction]] = []

    def fire(self, action: ClickAction) -> None:
        self.events.append((query_performance_counter(), action))
```

Button down + button up are packed into a single `SendInput` call with a 2-element `INPUT[]` array — Windows processes the pair atomically, closing the gap that some games use to detect synthesized input.

### 6.5 Cursor modes

- **Follow:** `action.move_to = None`. Engine emits only button events; click lands at the current cursor position.
- **Fixed:** `action.move_to = (x, y)`. Engine emits a move event with `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE` before the button pair.

---

## 7. Hotkey controller

- **Toggle mode:** `RegisterHotKey` on the main thread. A Qt-native message filter intercepts `WM_HOTKEY` and emits `start_requested` / `stop_requested` signals.
- **Hold mode:** `WH_KEYBOARD_LL` low-level keyboard hook. The hook filters for the configured key; press → `hold_started`, release → `hold_ended`. `RegisterHotKey` is not used in hold mode.
- Exactly one mechanism is active at a time. Switching modes in the UI unregisters the old one before registering the new one.
- Hotkey reconfiguration at runtime: UI calls `controller.set_binding(new_key)` → controller unregisters and re-registers in place. No restart required.
- **Click-to-capture for fixed-point mode:** separate `WH_MOUSE_LL` hook, armed transiently by the UI's "Pick point" button. First `WM_LBUTTONDOWN` captures `GetCursorPos()`, consumes the event (returns nonzero from the hook callback so it does not reach the target window), and unhooks.

---

## 8. UI layout

Single `QMainWindow`, qdarktheme applied before `QApplication.exec()`, compact (~360×480), resizable but everything fits without scrolling.

```
┌──────────────────────────────────────────────┐
│ Auto Clicker                            ─ □ ×│
├──────────────────────────────────────────────┤
│                                              │
│  Clicks per second       ┌─────┐             │
│                          │  10 │ ▲▼          │
│                          └─────┘             │
│                                              │
│  Mouse button            ◉ Left              │
│                          ○ Right             │
│                          ○ Middle            │
│                                              │
│  Cursor mode             ◉ Follow cursor     │
│                          ○ Fixed point       │
│                          [ Pick point ]  ─   │
│                                              │
│  Trigger mode            ◉ Toggle            │
│                          ○ Hold              │
│                                              │
│  Hotkey                  ┌──────────┐        │
│                          │ F6       │ change │
│                          └──────────┘        │
│                                              │
│  Stop after                                  │
│    ☐ Duration            ┌─────┐ seconds     │
│                          │  30 │             │
│                          └─────┘             │
│    ☐ Click count         ┌─────┐             │
│                          │ 100 │             │
│                          └─────┘             │
│                                              │
│  ──────────────────────────────────────────  │
│                                              │
│      ● Idle                                  │
│      [      START (F6)      ]                │
│                                              │
└──────────────────────────────────────────────┘
```

### Behavior

- **State indicator:** `● Idle` (gray) / `● Running` (green) / `● Armed` (amber, hold mode waiting for key press).
- **Pick point:** button becomes "Click anywhere…", cursor changes to crosshair, next physical click captures `(x, y)` and is displayed next to the button as "Fixed at 1820, 640".
- **Hotkey capture:** click "change" → field shows "Press a key…"; next keypress (captured via a transient `WH_KEYBOARD_LL`) is validated and stored. Esc cancels. Reserved keys (Enter, mouse buttons, already-bound system hotkeys) are rejected with an inline validation message.
- **Start button** duplicates the hotkey action for discoverability and testing.
- **Disabled while running:** CPS, button, mode, hotkey inputs disable when the engine is running. User stops first to change settings.
- **Stop conditions:** checkboxes toggle `DurationLimit` / `ClickLimit` in the list passed to the engine. v0.2 additions are new rows here with no plumbing changes.

### Theme

- `qdarktheme.setup_theme("dark")` at startup.
- Accent color `#5EC8D6` (muted cyan) for the Running indicator and primary button. Neutral grays elsewhere.
- No gradients, no shadows. Utility tool, opinionated but restrained.

### Out of scope for v0.1

- System tray.
- Menu bar, status bar, tabs.
- Any light-mode toggle.

---

## 9. Testing strategy

### 9.1 Scheduler accuracy tests

Real `QueryPerformanceCounter`, `RecordingSink` — no real clicks fired. CI runs on `windows-latest`.

1. **Average cadence.** 100 clicks at 50 CPS. Assert `abs(actual_duration - 2.0) / 2.0 < 0.01`.
2. **Per-click jitter.** 500 clicks at 100 CPS. Assert p99 of inter-click intervals within ±1% of 10 ms.
3. **No drift.** 1000 clicks at 20 CPS. Assert final timestamp within 1% of 50 s.

Target total runtime ~6 s across the suite.

### 9.2 Engine behavior tests

- `start()` from idle launches the thread and begins clicking.
- `stop()` stops cleanly within one interval.
- Start → stop → start cycles reuse the thread (no thread per run).
- Config changes while running are blocked at the UI layer (inputs disabled — §8). The engine API does not accept new `ClickConfig` while running; calls raise `EngineBusyError`. Test covers the raise.
- `StopCondition`s fire the expected stop.

### 9.3 Stop condition tests

- `DurationLimit` stops within one tick of deadline.
- `ClickLimit` stops after exactly N clicks.

### 9.4 Hotkey controller tests

- Use a fake Win32 backend (injected into `HotkeyController`) so tests do not register real hotkeys.
- Assert signal emission on simulated `WM_HOTKEY` / hook events.
- Assert re-registration when binding changes.

### 9.5 UI

- Manually verified for v0.1.
- No visual regression or Playwright — overkill for one window.

### 9.6 Coverage

- Target ≥80% line coverage on `engine/`, `hotkeys/`, `win32/` (non-trivial logic only — ctypes struct definitions are excluded).
- UI not included in coverage target.

---

## 10. Open questions

None. All design decisions resolved during brainstorming.

---

## 11. Build order

1. `win32/` — ctypes wrappers for `SendInput`, timing, hotkey, hooks. Smoke-test each in isolation.
2. `engine/` — config, sinks, sources, stops, scheduler, engine. Full test suite here before any UI work.
3. `hotkeys/` — controller with fake backend, then real backend.
4. `ui/` — theme + `MainWindow` + widgets. Manually wire to engine and hotkey controller in `app.py`.
5. End-to-end smoke: launch, toggle via F6 in a scratch text editor, verify clicks land.

This order keeps the GUI out of the critical path until the engine is proven.
