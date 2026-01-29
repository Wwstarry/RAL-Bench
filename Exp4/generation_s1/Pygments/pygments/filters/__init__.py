from __future__ import annotations

from typing import Iterable, Iterator, List, Optional, Tuple

from pygments.token import TokenType


class Filter:
    def __init__(self, **options):
        self.options = dict(options)

    def filter(self, lexer, stream: Iterable[Tuple[TokenType, str]]):
        yield from stream


def apply_filters(
    stream: Iterable[Tuple[TokenType, str]],
    filters: Optional[List[Filter]],
    lexer=None,
) -> Iterator[Tuple[TokenType, str]]:
    if not filters:
        yield from stream
        return
    cur = stream
    for f in filters:
        cur = f.filter(lexer, cur)
    yield from cur