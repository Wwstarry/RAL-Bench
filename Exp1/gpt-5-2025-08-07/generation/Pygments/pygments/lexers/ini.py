import re
from ..token import Token, Keyword, Name, String, Number, Operator, Punctuation, Comment, Text, Whitespace

class IniLexer:
    """
    Minimal INI lexer. Supports sections, key-value pairs and comments.
    """

    name = "INI"
    aliases = ["ini", "cfg"]
    filenames = ["*.ini", "*.cfg"]

    def __init__(self, **options):
        self.options = options

    def get_tokens(self, code):
        for line in code.splitlines(keepends=True):
            # whitespace-only line
            if line.strip() == "":
                yield (Whitespace, line)
                continue

            # comment line
            if line.lstrip().startswith(("#", ";")):
                yield (Comment, line)
                continue

            # section header
            m = re.match(r"\s*\[([^\]]+)\]\s*(\r?\n)?", line)
            if m:
                yield (Punctuation, "[")
                yield (Name.Namespace, m.group(1))
                yield (Punctuation, "]")
                # emit trailing newline
                rest = line[m.end():]
                if rest:
                    yield (Text, rest)
                continue

            # key = value
            m = re.match(r"\s*([A-Za-z0-9_.-]+)\s*(=|:)\s*(.*?)(\r?\n)?$", line)
            if m:
                key = m.group(1)
                op = m.group(2)
                val = m.group(3)
                yield (Name.Attribute, key)
                yield (Operator, op)
                # value classification
                v = val.strip()
                if v.startswith('"') and v.endswith('"') or v.startswith("'") and v.endswith("'"):
                    yield (String, val)
                elif re.fullmatch(r"-?\d+", v or ""):
                    yield (Number.Integer, val)
                elif re.fullmatch(r"-?\d+\.\d+", v or ""):
                    yield (Number.Float, val)
                elif v.lower() in ("true", "false", "yes", "no", "on", "off"):
                    yield (Keyword.Constant, val)
                else:
                    yield (Text, val)
                # newline
                nl = m.group(4) or ""
                if nl:
                    yield (Text, nl)
                continue

            # fallback: emit as text
            yield (Text, line)