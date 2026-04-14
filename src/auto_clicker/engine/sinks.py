from __future__ import annotations

import sys
from typing import Protocol

from auto_clicker.engine.config import Button, ClickAction


class ClickSink(Protocol):
    def fire(self, action: ClickAction) -> None: ...


class RecordingSink:
    def __init__(self) -> None:
        self.events: list[tuple[int, ClickAction]] = []

    def fire(self, action: ClickAction) -> None:
        from auto_clicker.engine.scheduler import monotonic_ticks

        self.events.append((monotonic_ticks(), action))


if sys.platform == "win32":
    from auto_clicker.win32.input import MouseEventFlag, send_click

    _DOWN_UP: dict[Button, tuple[int, int]] = {
        Button.LEFT: (int(MouseEventFlag.LEFTDOWN), int(MouseEventFlag.LEFTUP)),
        Button.RIGHT: (int(MouseEventFlag.RIGHTDOWN), int(MouseEventFlag.RIGHTUP)),
        Button.MIDDLE: (int(MouseEventFlag.MIDDLEDOWN), int(MouseEventFlag.MIDDLEUP)),
    }

    class SendInputSink:
        def fire(self, action: ClickAction) -> None:
            down, up = _DOWN_UP[action.button]
            send_click(down, up, move_to=action.move_to)
