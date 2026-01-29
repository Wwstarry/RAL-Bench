from __future__ import annotations

from typing import Any, List, Optional

from .options import Options


class AddonManager:
    """
    Minimal addon manager: keeps addons and triggers named hooks.
    """

    def __init__(self, master: Any):
        self.master = master
        self.options: Options = getattr(master, "options", Options())
        self._addons: List[Any] = []

    def add(self, *addons: Any) -> None:
        for a in addons:
            if a in self._addons:
                continue
            self._addons.append(a)

    def remove(self, addon: Any) -> None:
        if addon in self._addons:
            self._addons.remove(addon)

    def clear(self) -> None:
        self._addons.clear()

    def trigger(self, event: str, *args: Any, **kwargs: Any) -> None:
        for a in list(self._addons):
            func = getattr(a, event, None)
            if callable(func):
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    # store for debugging; re-raise to fail fast.
                    setattr(self.master, "last_exception", e)
                    raise

    def register_option(
        self,
        name: str,
        default: Any,
        help: str = "",
        typespec: Optional[type] = None,
    ) -> None:
        self.options.add_option(name=name, default=default, typespec=typespec, help=help)

    def __iter__(self):
        return iter(self._addons)

    def __len__(self) -> int:
        return len(self._addons)