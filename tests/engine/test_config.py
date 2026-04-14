from __future__ import annotations

import dataclasses

import pytest

from auto_clicker.engine.config import (
    Button,
    ClickAction,
    ClickConfig,
    CursorMode,
    FixedPoint,
    FollowCursor,
    TriggerMode,
)


def test_click_config_is_frozen():
    cfg = ClickConfig(cps=10, button=Button.LEFT, cursor_mode=FollowCursor(), trigger_mode=TriggerMode.TOGGLE)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.cps = 20  # type: ignore[misc]


def test_click_config_rejects_out_of_range_cps():
    with pytest.raises(ValueError, match="cps must be in 1..100"):
        ClickConfig(cps=0, button=Button.LEFT, cursor_mode=FollowCursor(), trigger_mode=TriggerMode.TOGGLE)
    with pytest.raises(ValueError, match="cps must be in 1..100"):
        ClickConfig(cps=101, button=Button.LEFT, cursor_mode=FollowCursor(), trigger_mode=TriggerMode.TOGGLE)


def test_fixed_point_is_cursor_mode():
    fp = FixedPoint(x=100, y=200)
    assert isinstance(fp, CursorMode)
    assert (fp.x, fp.y) == (100, 200)


def test_follow_cursor_is_cursor_mode():
    assert isinstance(FollowCursor(), CursorMode)


def test_click_action_defaults():
    action = ClickAction(button=Button.LEFT)
    assert action.move_to is None


def test_click_action_with_move_target():
    action = ClickAction(button=Button.RIGHT, move_to=(10, 20))
    assert action.move_to == (10, 20)
