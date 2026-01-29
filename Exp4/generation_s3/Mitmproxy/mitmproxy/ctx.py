from __future__ import annotations

"""
Minimal context module.

The real mitmproxy provides a global context object (ctx) for addons.
Here we provide a tiny compatible surface to avoid import errors.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class _Log:
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass

    def warn(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass


@dataclass
class _Ctx:
    master: Optional[Any] = None
    options: Optional[Any] = None
    log: _Log = _Log()


ctx = _Ctx()