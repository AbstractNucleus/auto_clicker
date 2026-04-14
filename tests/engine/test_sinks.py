from __future__ import annotations

from auto_clicker.engine.config import Button, ClickAction
from auto_clicker.engine.sinks import RecordingSink


def test_recording_sink_captures_actions():
    sink = RecordingSink()
    a1 = ClickAction(button=Button.LEFT)
    a2 = ClickAction(button=Button.RIGHT, move_to=(5, 7))
    sink.fire(a1)
    sink.fire(a2)
    assert [a for _, a in sink.events] == [a1, a2]


def test_recording_sink_timestamps_are_monotonic():
    sink = RecordingSink()
    for _ in range(5):
        sink.fire(ClickAction(button=Button.LEFT))
    timestamps = [t for t, _ in sink.events]
    assert timestamps == sorted(timestamps)
