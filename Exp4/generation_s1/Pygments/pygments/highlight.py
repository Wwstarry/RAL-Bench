from __future__ import annotations

import io

from pygments.lex import lex


def highlight(code, lexer, formatter) -> str:
    tokensource = lex(code, lexer)
    buf = io.StringIO()
    rv = formatter.format(tokensource, buf)
    if rv is not None:
        return rv
    return buf.getvalue()