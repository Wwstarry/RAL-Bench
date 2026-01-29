from typing import Any, Callable, Dict

class Query:
    """
    Helper for building query functions.
    Example:
        Query().status == "open"
    """
    def __init__(self, path=None):
        self._path = path or []

    def __getattr__(self, item):
        return Query(self._path + [item])

    def _extract(self, doc: Dict):
        val = doc
        for p in self._path:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                return None
        return val

    def __eq__(self, other):
        return lambda doc: self._extract(doc) == other

    def __ne__(self, other):
        return lambda doc: self._extract(doc) != other

    def __lt__(self, other):
        return lambda doc: self._extract(doc) < other

    def __le__(self, other):
        return lambda doc: self._extract(doc) <= other

    def __gt__(self, other):
        return lambda doc: self._extract(doc) > other

    def __ge__(self, other):
        return lambda doc: self._extract(doc) >= other

    def exists(self):
        return lambda doc: self._extract(doc) is not None

    def matches(self, func):
        return lambda doc: func(self._extract(doc))

    # Logical AND/OR/NOT
    def __and__(self, other):
        return lambda doc: self(doc) and other(doc)

    def __or__(self, other):
        return lambda doc: self(doc) or other(doc)

    def __call__(self, doc):
        return bool(self._extract(doc))