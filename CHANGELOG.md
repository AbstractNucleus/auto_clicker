# Changelog

Notable changes are documented here. Format roughly follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-16

Initial release.

### Added
- Click engine with cadence up to 100 CPS via QPC-based scheduler and sleep-then-spin waiting (`timeBeginPeriod(1)`).
- `ClickSource` / `ClickSink` / `StopCondition` protocols with built-in `UniformSource`, `SendInputSink`, `RecordingSink`, `DurationLimit`, `ClickLimit`.
- Global hotkey support (F1 to F12) with toggle and hold modes, via `RegisterHotKey` and low-level keyboard hooks.
- PySide6 single-window UI: CPS, mouse button, cursor mode (follow or fixed point), trigger mode, hotkey picker, optional duration and click-count limits, state indicator.
- qdarktheme styling with stylesheet fallback.
- 30 tests, ~98% coverage on engine and hotkeys layers.

### Fixed
- UI resets to idle when a stop condition (`DurationLimit` or `ClickLimit`) ends a run on its own. Previously you had to toggle manually.

[Unreleased]: https://github.com/AbstractNucleus/auto_clicker/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/AbstractNucleus/auto_clicker/releases/tag/v0.1.0
