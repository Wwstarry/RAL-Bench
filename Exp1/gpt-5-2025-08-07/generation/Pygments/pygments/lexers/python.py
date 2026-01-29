import io
import tokenize as py_tokenize
import token as py_token
import keyword as py_keyword

from ..token import Token, Keyword, Name, String, Number, Operator, Punctuation, Comment, Text, Whitespace

class PythonLexer:
    """
    Minimal Python lexer using the stdlib tokenizer to achieve reasonable compatibility.
    """

    name = "Python"
    aliases = ["python", "py"]
    filenames = ["*.py"]

    def __init__(self, **options):
        self.options = options

    def get_tokens(self, code):
        # tokenize requires bytes
        if not isinstance(code, bytes):
            b = code.encode("utf-8")
        else:
            b = code
        readline = io.BytesIO(b).readline
        try:
            for tok in py_tokenize.tokenize(readline):
                tok_type = tok.type
                tok_str = tok.string
                # The first token can be ENCODING; skip it
                if tok_type == py_tokenize.ENCODING:
                    continue
                if tok_type in (py_tokenize.NEWLINE, py_tokenize.NL):
                    yield (Text, tok_str)
                    continue
                if tok_type == py_tokenize.INDENT or tok_type == py_tokenize.DEDENT:
                    yield (Whitespace, tok_str)
                    continue
                if tok_type == py_token.NAME:
                    if py_keyword.iskeyword(tok_str):
                        yield (Keyword, tok_str)
                    else:
                        yield (Name, tok_str)
                    continue
                if tok_type == py_token.NUMBER:
                    yield (Number, tok_str)
                    continue
                if tok_type == py_token.STRING:
                    # detect docstring by position? keep simple
                    yield (String, tok_str)
                    continue
                if tok_type == py_token.OP:
                    # decide punctuation vs operator
                    if tok_str in (",", ":", ";", ".", "(", ")", "[", "]", "{", "}"):
                        yield (Punctuation, tok_str)
                    else:
                        yield (Operator, tok_str)
                    continue
                if tok_type == py_tokenize.COMMENT:
                    yield (Comment, tok_str)
                    continue
                if tok_type == py_tokenize.ENDMARKER:
                    continue
                # fallback
                yield (Text, tok_str)
        except Exception as e:
            # On tokenize errors, emit the rest as Error
            yield (Token.Error, str(e))