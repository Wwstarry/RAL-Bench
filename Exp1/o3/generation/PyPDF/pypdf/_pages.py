"""
An immutable sequence wrapper around a list of PageObject instances.

Required because the real `pypdf.PdfReader.pages` behaves like a list-like
object that supports ``len()``, indexing and iteration but does not allow item
assignment.
"""
from __future__ import annotations

from typing import Iterator, List

from ._page import PageObject


class _Pages:
    def __init__(self, pages: List[PageObject]):
        self._pages = list(pages)

    def __len__(self) -> int:
        return len(self._pages)

    def __getitem__(self, item):
        return self._pages[item]

    def __iter__(self) -> Iterator[PageObject]:
        return iter(self._pages)

    # Real pypdf supports .__repr__
    def __repr__(self) -> str:  # pragma: no cover
        return f"<pypdf._Pages len={len(self)}>"