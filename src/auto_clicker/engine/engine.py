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
