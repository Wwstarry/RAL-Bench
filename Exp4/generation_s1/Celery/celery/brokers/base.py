from __future__ import annotations

from typing import Callable, Optional


class BaseBroker:
    def __init__(self, dispatch: Optional[Callable[[dict], None]] = None) -> None:
        self.dispatch = dispatch

    def publish(self, message: dict) -> None:
        raise NotImplementedError