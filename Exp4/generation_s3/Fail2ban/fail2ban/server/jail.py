from __future__ import annotations

from typing import List, Optional, Any


class Jail:
    """
    Minimal jail that coordinates a filter and actions.
    No banning, no daemon behavior; just offline matching.
    """

    def __init__(self, name: str, *, filter=None, actions=None, backend: str | None = None):
        self._name = str(name)
        self._filter = None
        self._actions: List[Any] = []
        self._backend = backend  # accepted for compatibility; ignored

        if filter is not None:
            self.setFilter(filter)
        if actions:
            for a in list(actions):
                self.addAction(a)

    def getName(self) -> str:
        return self._name

    def setFilter(self, filter_obj) -> None:
        self._filter = filter_obj

    def getFilter(self):
        return self._filter

    def addAction(self, action_obj) -> None:
        self._actions.append(action_obj)

    def getActions(self) -> list:
        return list(self._actions)

    def processLine(self, line: str) -> List[str]:
        """
        Return list of IP strings that the filter considers a failure for this line.
        No banning performed.
        """
        if self._filter is None:
            return []

        match_fn = getattr(self._filter, "matchLine", None)
        if callable(match_fn):
            try:
                res = match_fn(line)
            except Exception:
                # Keep deterministic, safe behavior: filter errors mean "no match".
                return []
            if res is None:
                return []
            return list(res)

        return []

    def findFailure(self, line: str) -> List[str]:
        return self.processLine(line)

    def __repr__(self) -> str:
        f = self._filter.__class__.__name__ if self._filter is not None else None
        return f"Jail(name={self._name!r}, filter={f!r}, actions={len(self._actions)}, backend={self._backend!r})"