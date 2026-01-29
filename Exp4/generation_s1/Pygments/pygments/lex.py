from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, Tuple

from pygments.filters import apply_filters
from pygments.token import Text, TokenType
from pygments.util import ensure_str


class Lexer:
    name = ""
    aliases: List[str] = []
    filenames: List[str] = []
    mimetypes: List[str] = []

    def __init__(self, **options):
        self.options: Dict = dict(options)
        self.filters: List = []

    def add_filter(self, filter_, **options):
        if isinstance(filter_, str):
            raise NotImplementedError("String-named filters are not supported in this minimal implementation.")
        self.filters.append(filter_(**options))

    def get_tokens(self, text: str) -> Iterable[Tuple[TokenType, str]]:
        yield Text, text


def lex(code, lexer: Lexer) -> Iterator[Tuple[TokenType, str]]:
    text = ensure_str(code)
    stream = lexer.get_tokens(text)
    stream = apply_filters(stream, getattr(lexer, "filters", None), lexer=lexer)
    return iter(stream)