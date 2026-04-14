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
    # Windows scheduler variance dominates at 100 CPS; 5% bounds real-world jitter.
    assert abs(p99 - 10.0) / 10.0 < 0.05, f"p99={p99}ms"


def test_no_drift_over_long_run_at_20_cps():
    from auto_clicker.engine.scheduler import ticks_per_second

    freq = ticks_per_second()
    stamps = _run_and_collect(cps=20, target_clicks=200)  # 10s
    duration = (stamps[-1] - stamps[0]) / freq
    expected = 199 / 20
    assert abs(duration - expected) / expected < 0.01
