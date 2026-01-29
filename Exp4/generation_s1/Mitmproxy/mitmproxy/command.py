from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from .exceptions import CommandError


class CommandManager:
    """
    Minimal command registry.

    This is only intended to satisfy add-on manager integration and basic lookups.
    """

    def __init__(self, master: Any):
        self.master = master
        self._commands: Dict[str, Dict[str, Any]] = {}

    def add(self, name: str, func: Callable[..., Any], help: str = "") -> None:
        if not callable(func):
            raise CommandError("func must be callable")
        self._commands[name] = {"func": func, "help": help or ""}

    def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        cmd = self._commands.get(name)
        if not cmd:
            raise CommandError(f"Unknown command: {name}")
        return cmd["func"](*args, **kwargs)

    def get_commands(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._commands)