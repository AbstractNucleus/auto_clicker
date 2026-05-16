# auto_clicker

Windows autoclicker. Python 3.13, PySide6.

Features:

- Up to 100 CPS using a `QueryPerformanceCounter` scheduler with `timeBeginPeriod(1)` and sleep-then-spin waiting.
- Global hotkeys (F1 to F12) in toggle or hold mode, via `RegisterHotKey` and low-level keyboard hooks.
- Follow-cursor or fixed-point click target. Left, right, or middle button.
- Optional duration and click-count stop conditions.
- Qt is confined to the UI layer; the engine has no Qt dependency.

Windows only. Uses `SendInput`, `RegisterHotKey`, `WH_KEYBOARD_LL`, `WH_MOUSE_LL`, and QPC.

## Install and run

Needs [uv](https://docs.astral.sh/uv/) and Python 3.13.

```powershell
uv sync
uv run python -m auto_clicker
```

After `uv sync` the console script is also on the path:

```powershell
uv run auto-clicker
```

## Usage

1. Launch the app. A small window opens.
2. Set clicks per second, mouse button, cursor mode (follow or fixed point), and trigger mode (toggle or hold).
3. Pick a hotkey (F1 to F12). Default is F6.
4. Optionally enable a duration limit and/or a click-count limit.
5. Press the hotkey (or click START) to begin. In toggle mode, press again to stop. In hold mode, clicks fire while you hold the key.

For fixed-point mode, click Capture next to the cursor mode and then click where you want the clicks to land.

## Development

```powershell
uv sync
uv run pytest
uv run pytest --cov
uv run ruff check
uv run ruff format
```

## Build a standalone exe

```powershell
uv sync
uv run pyinstaller --onefile --windowed --name auto_clicker src/auto_clicker/__main__.py
```

The single-file build lands at `dist/auto_clicker.exe` (~46 MB). The first launch is slower than subsequent ones because PyInstaller unpacks the bundle to a temp dir. Prebuilt binaries for tagged releases are attached to the [GitHub Releases](https://github.com/AbstractNucleus/auto_clicker/releases).

Layout:

| Layer | Contents |
|---|---|
| `src/auto_clicker/win32/` | `ctypes` bindings for `SendInput`, `RegisterHotKey`, hooks, QPC timing |
| `src/auto_clicker/engine/` | Scheduler, click engine, sources, sinks, stop conditions. No Qt. |
| `src/auto_clicker/hotkeys/` | Hotkey controller with a pluggable backend (fake for tests, Win32 for real) |
| `src/auto_clicker/ui/` | PySide6 main window, widgets, dark theme |

UI and `win32/` are excluded from coverage. They depend on the Windows event loop and aren't worth simulating in CI. Engine and hotkeys are covered.

## Disclaimer

Meant for legitimate uses: testing, accessibility, automating your own software, and similar workflows where automated input is allowed.

Plenty of online services and games forbid automated input under their terms of service or anti-cheat rules. Don't use this to violate any service's terms, gain an advantage in competitive play, or get around anti-cheat. That's on you.

## License

[MIT](LICENSE), 2026 Noel Kleen.
