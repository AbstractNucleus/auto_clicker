from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Button(Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class TriggerMode(Enum):
    TOGGLE = "toggle"
    HOLD = "hold"


class CursorMode:
    """Marker base. Concrete: FollowCursor, FixedPoint."""


@dataclass(frozen=True, slots=True)
class FollowCursor(CursorMode):
    pass


@dataclass(frozen=True, slots=True)
class FixedPoint(CursorMode):
    x: int
    y: int


@dataclass(frozen=True, slots=True)
class ClickAction:
    button: Button
    move_to: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True)
class ClickConfig:
    cps: int
    button: Button
    cursor_mode: CursorMode
    trigger_mode: TriggerMode

    def __post_init__(self) -> None:
        if not 1 <= self.cps <= 100:
            raise ValueError("cps must be in 1..100")
