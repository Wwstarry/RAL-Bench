"""
Addon manager for mitmproxy options and commands integration.
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Option:
    """
    Represents a configurable option.
    """
    name: str
    typespec: type = str
    default: Any = ""
    help: str = ""
    choices: Optional[List[Any]] = None


class AddonManager:
    """
    Manages addons, options, and commands for mitmproxy.
    """
    
    def __init__(self):
        self.addons: List[Any] = []
        self.options: Dict[str, Option] = {}
        self.commands: Dict[str, Callable] = {}
    
    def add_addon(self, addon: Any) -> None:
        """
        Register an addon.
        """
        self.addons.append(addon)
    
    def remove_addon(self, addon: Any) -> None:
        """
        Unregister an addon.
        """
        if addon in self.addons:
            self.addons.remove(addon)
    
    def add_option(self, name: str, typespec: type, default: Any, help: str = "", 
                   choices: Optional[List[Any]] = None) -> None:
        """
        Register an option.
        """
        self.options[name] = Option(
            name=name,
            typespec=typespec,
            default=default,
            help=help,
            choices=choices
        )
    
    def add_command(self, name: str, func: Callable) -> None:
        """
        Register a command.
        """
        self.commands[name] = func
    
    def trigger(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Trigger a command or event.
        """
        if name in self.commands:
            return self.commands[name](*args, **kwargs)
        return None