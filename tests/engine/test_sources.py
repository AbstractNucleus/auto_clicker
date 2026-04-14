from __future__ import annotations

from auto_clicker.engine.config import Button
from auto_clicker.engine.sources import UniformSource


def test_uniform_source_never_exhausts():
    src = UniformSource(button=Button.LEFT, move_to=None)
    for _ in range(1000):
        action = src.next()
        assert action is not None
        assert action.button == Button.LEFT
        assert action.move_to is None


def test_uniform_source_emits_fixed_point_move():
    src = UniformSource(button=Button.RIGHT, move_to=(100, 200))
    action = src.next()
    assert action is not None
    assert action.button == Button.RIGHT
    assert action.move_to == (100, 200)
