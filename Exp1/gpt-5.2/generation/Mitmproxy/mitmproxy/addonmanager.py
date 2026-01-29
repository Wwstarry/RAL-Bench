from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional


class Options:
    """
    Minimal options container.
    """
    def __init__(self, **kwargs: Any):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Command:
    name: str
    func: Callable[..., Any]
    help: str = ""


@dataclass
class AddonManager:
    """
    Minimal AddonManager.

    Supports registering addons and invoking lifecycle hooks if present.
    Provides a tiny command registry to satisfy typical surfaces.
    """
    options: Options = field(default_factory=Options)
    addons: List[Any] = field(default_factory=list)
    commands: Dict[str, Command] = field(default_factory=dict)

    def add(self, addon: Any) -> None:
        self.addons.append(addon)
        # call addon.load(manager) if present
        load = getattr(addon, "load", None)
        if callable(load):
            load(self)

    def remove(self, addon: Any) -> None:
        if addon in self.addons:
            self.addons.remove(addon)

    def trigger(self, event: str, *args: Any, **kwargs: Any) -> None:
        """
        Trigger an event on all addons by calling a method if it exists.
        """
        for a in list(self.addons):
            fn = getattr(a, event, None)
            if callable(fn):
                fn(*args, **kwargs)

    # Command integration (very small subset)
    def add_command(self, name: str, func: Callable[..., Any], help: str = "") -> None:
        self.commands[name] = Command(name=name, func=func, help=help)

    def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        if name not in self.commands:
            raise KeyError(f"Unknown command: {name}")
        return self.commands[name].func(*args, **kwargs)

    def iter_addons(self) -> Iterable[Any]:
        return iter(self.addons)