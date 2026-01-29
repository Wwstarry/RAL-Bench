import re

from ..token import Token, Keyword, Name, String, Number, Operator, Punctuation, Comment, Text, Whitespace

class JsonLexer:
    """
    Minimal JSON lexer. Supports comments (non-standard) starting with // or /* ... */.
    """

    name = "JSON"
    aliases = ["json"]
    filenames = ["*.json"]

    def __init__(self, **options):
        self.options = options

    def get_tokens(self, code):
        s = code
        pos = 0
        length = len(s)

        # regex patterns
        ws_re = re.compile(r"\s+")
        str_re = re.compile(r'"(\\.|[^"\\])*"')
        num_re = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")
        line_comment_re = re.compile(r"//.*")
        block_comment_re = re.compile(r"/\*.*?\*/", re.S)

        keywords = {
            "true": Keyword.Constant,
            "false": Keyword.Constant,
            "null": Keyword.Constant,
        }

        while pos < length:
            # whitespace
            m = ws_re.match(s, pos)
            if m:
                val = m.group(0)
                yield (Whitespace, val)
                pos = m.end()
                continue

            # comments
            m = block_comment_re.match(s, pos)
            if m:
                val = m.group(0)
                yield (Comment, val)
                pos = m.end()
                continue
            m = line_comment_re.match(s, pos)
            if m:
                val = m.group(0)
                yield (Comment, val)
                pos = m.end()
                continue

            # strings
            m = str_re.match(s, pos)
            if m:
                val = m.group(0)
                yield (String.Double, val)
                pos = m.end()
                continue

            # numbers
            m = num_re.match(s, pos)
            if m:
                val = m.group(0)
                # Decide float vs int
                if "." in val or "e" in val.lower():
                    yield (Number.Float, val)
                else:
                    yield (Number.Integer, val)
                pos = m.end()
                continue

            # punctuation
            ch = s[pos]
            if ch in "{},:[]":
                yield (Punctuation, ch)
                pos += 1
                continue

            # keywords
            for kw in ("true", "false", "null"):
                if s.startswith(kw, pos):
                    yield (keywords[kw], kw)
                    pos += len(kw)
                    break
            else:
                # unknown token
                yield (Text, ch)
                pos += 1