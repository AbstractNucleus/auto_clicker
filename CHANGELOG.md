# Changelog

All notable changes to this project are documented here. The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-16

Initial release.

### Added
- Click engine with precise cadence up to 100 CPS via QPC-based scheduler and sleep-then-spin waiting (`timeBeginPeriod(1)`).
- `ClickSource` / `ClickSink` / `StopCondition` protocols with built-in `UniformSource`, `SendInputSink`, `RecordingSink`, `DurationLimit`, `ClickLimit`.
- Global hotkey support (F1–F12) with toggle and hold modes, using `RegisterHotKey` and low-level keyboard hooks.
- PySide6 single-window UI: CPS, mouse button, cursor mode (follow / fixed point), trigger mode, hotkey picker, optional duration and click-count limits, state indicator.
- qdarktheme styling with stylesheet fallback.
- 30 tests, ~98% coverage on engine + hotkeys layers.

### Fixed
- UI now resets to idle when a stop condition (`DurationLimit` / `ClickLimit`) ends a run on its own. Previously the user had to toggle manually.

[Unreleased]: https://github.com/AbstractNucleus/auto_clicker/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/AbstractNucleus/auto_clicker/releases/tag/v0.1.0
