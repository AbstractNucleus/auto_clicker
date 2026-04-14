from __future__ import annotations

from typing import Protocol

from auto_clicker.engine.config import Button, ClickAction


class ClickSource(Protocol):
    def next(self) -> ClickAction | None: ...


class UniformSource:
    def __init__(self, button: Button, move_to: tuple[int, int] | None) -> None:
        self._action = ClickAction(button=button, move_to=move_to)

    def next(self) -> ClickAction | None:
        return self._action
