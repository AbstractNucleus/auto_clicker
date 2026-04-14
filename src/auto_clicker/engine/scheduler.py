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
