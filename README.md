# auto_clicker

A precise Windows autoclicker with global hotkeys, written in Python 3.13 + PySide6.

- Cadence up to **100 CPS** via a `QueryPerformanceCounter`-based scheduler with `timeBeginPeriod(1)` and sleep-then-spin waiting
- **Global hotkeys** (F1–F12) in toggle or hold mode via `RegisterHotKey` and low-level keyboard hooks
- **Follow cursor** or **fixed point** modes, left/right/middle button
- Optional **duration** and **click-count** stop conditions
- Qt-free engine core (Qt confined to the UI layer) — easy to test, easy to swap UIs

> **Windows only.** Uses Win32 APIs (`SendInput`, `RegisterHotKey`, `WH_KEYBOARD_LL`, `WH_MOUSE_LL`, QPC). There is no macOS or Linux build.

## Install & run

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13.

```powershell
uv sync
uv run python -m auto_clicker
```

Or after `uv sync`, the entry point script is also available:

```powershell
uv run auto-clicker
```

## Usage

1. Launch the app — a small fixed-width window appears.
2. Set **clicks per second**, **mouse button**, **cursor mode** (follow or fixed point), and **trigger mode** (toggle or hold).
3. Pick a **hotkey** (F1–F12). Default is **F6**.
4. Optionally enable **duration** and/or **click-count** limits.
5. Press the hotkey (or click **START**) to begin. In toggle mode, press again to stop; in hold mode, clicks fire while the key is held.

To capture a fixed point, click **Capture** next to the cursor mode and then click anywhere on screen.

## Development

```powershell
uv sync
uv run pytest             # 30 tests
uv run pytest --cov       # ~98% coverage on engine + hotkeys
uv run ruff check
uv run ruff format
```

The codebase is organized into four layers:

| Layer | What's in it |
|---|---|
| `src/auto_clicker/win32/` | `ctypes` bindings: `SendInput`, `RegisterHotKey`, hooks, QPC timing |
| `src/auto_clicker/engine/` | Qt-free scheduler, click engine, sources, sinks, stop conditions |
| `src/auto_clicker/hotkeys/` | Pluggable backend (fake for tests, Win32 for the real thing) |
| `src/auto_clicker/ui/` | PySide6 main window, widgets, dark theme |

UI and `win32/` are excluded from coverage (they're driven by the Windows event loop and not unit-testable in CI). Engine and hotkeys are fully covered.

## Disclaimer

This tool is provided for legitimate uses: testing, accessibility, automation of your own software, and similar workflows where automated input is permitted.

**Many online services, multiplayer games, and platforms prohibit automated input under their Terms of Service or anti-cheat policies.** Using this software to violate any service's ToS, gain unfair advantage in competitive play, or circumvent anti-cheat systems is **not** a supported use case. You are solely responsible for ensuring your use complies with all applicable terms, policies, and laws.

## License

[MIT](LICENSE) © 2026 Noel Kleen
