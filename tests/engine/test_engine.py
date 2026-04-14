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
