from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional


class AddonManagerError(Exception):
    pass


@dataclass
class AddonManager:
    """
    Minimal addon manager.

    Real mitmproxy provides event dispatch, option integration, and command registration.
    For this kata we implement:
      - add()/remove()
      - trigger(event_name, *args, **kwargs)
      - simple command registry
    """
    addons: List[Any] = field(default_factory=list)
    commands: Dict[str, Callable[..., Any]] = field(default_factory=dict)

    def add(self, *addons: Any) -> None:
        for a in addons:
            if a in self.addons:
                continue
            self.addons.append(a)
            self._maybe_call(a, "load", self)

    def remove(self, addon: Any) -> None:
        if addon in self.addons:
            self._maybe_call(addon, "done")
            self.addons.remove(addon)

    def clear(self) -> None:
        for a in list(self.addons):
            self.remove(a)

    def _maybe_call(self, addon: Any, name: str, *args: Any, **kwargs: Any) -> None:
        fn = getattr(addon, name, None)
        if callable(fn):
            fn(*args, **kwargs)

    def trigger(self, event: str, *args: Any, **kwargs: Any) -> None:
        """
        Dispatch an event to all addons. Missing handlers are ignored.
        """
        for a in list(self.addons):
            self._maybe_call(a, event, *args, **kwargs)

    # --- command support (very small subset) ---

    def register_command(self, name: str, func: Callable[..., Any]) -> None:
        if not name or not isinstance(name, str):
            raise AddonManagerError("command name must be a non-empty string")
        if name in self.commands:
            raise AddonManagerError(f"command already registered: {name}")
        self.commands[name] = func

    def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        if name not in self.commands:
            raise AddonManagerError(f"unknown command: {name}")
        return self.commands[name](*args, **kwargs)