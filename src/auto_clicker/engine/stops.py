from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TickContext:
    click_count: int
    elapsed_seconds: float


class StopCondition(Protocol):
    def should_stop(self, ctx: TickContext) -> bool: ...


@dataclass(frozen=True, slots=True)
class DurationLimit:
    seconds: float

    def __post_init__(self) -> None:
        if self.seconds <= 0:
            raise ValueError("seconds must be positive")

    def should_stop(self, ctx: TickContext) -> bool:
        return ctx.elapsed_seconds >= self.seconds


@dataclass(frozen=True, slots=True)
class ClickLimit:
    count: int

    def __post_init__(self) -> None:
        if self.count <= 0:
            raise ValueError("count must be positive")

    def should_stop(self, ctx: TickContext) -> bool:
        return ctx.click_count >= self.count
