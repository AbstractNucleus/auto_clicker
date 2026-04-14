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
