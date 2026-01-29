import pytest

from pygments import highlight, lex
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers.ini import IniLexer
from pygments.lexers.json import JsonLexer
from pygments.lexers.python import PythonLexer
from pygments.token import Comment, Keyword, Literal, Name, Number, Punctuation, Token, Text
from pygments.util import ClassNotFound


def test_token_hierarchy_and_repr():
    assert repr(Token) == "Token"
    assert repr(Token.Name.Function) == "Token.Name.Function"
    assert Token.Name.Function in Token.Name
    assert Token.Name in Token.Name is True
    assert not (Token.Name in Token.Name.Function)


def test_lex_preserves_input_roundtrip():
    code = "def foo(x):\n\t# c\n\treturn x+1\n"
    toks = list(lex(code, PythonLexer()))
    out = "".join(v for _, v in toks)
    assert out == code


def test_pythonlexer_def_class_decorator_comment_string_number():
    code = "@dec\ndef foo():\n    '''doc'''\n    x=1.5 # hi\n"
    toks = list(lex(code, PythonLexer()))
    # decorator name
    assert any(tt in Name.Decorator and v == "dec" for tt, v in toks)
    # def keyword and function name
    assert any(tt in Keyword and v == "def" for tt, v in toks)
    assert any(tt in Name.Function and v == "foo" for tt, v in toks)
    # docstring
    assert any(tt in Literal.String.Doc and "doc" in v for tt, v in toks)
    # number float
    assert any(tt in Number and v == "1.5" for tt, v in toks)
    # comment
    assert any(tt in Comment.Single and v.strip() == "# hi" for tt, v in toks)


def test_jsonlexer_basics():
    code = '{"a": true, "b": 1.2}\n'
    toks = list(lex(code, JsonLexer()))
    assert any(tt in Punctuation and v == "{" for tt, v in toks)
    assert any(tt in Literal.String.Double and v == '"a"' for tt, v in toks)
    assert any(tt in Keyword.Constant and v == "true" for tt, v in toks)
    assert any(tt in Number and v == "1.2" for tt, v in toks)
    assert "".join(v for _, v in toks) == code


def test_inilexer_basics():
    code = "[sec]\nkey=value ;c\n"
    toks = list(lex(code, IniLexer()))
    assert any(tt in Name.Namespace and v == "sec" for tt, v in toks)
    assert any(tt in Name.Attribute and v == "key" for tt, v in toks)
    assert any(tt in Comment.Single and v.strip() == ";c" for tt, v in toks)
    assert "".join(v for _, v in toks) == code


def test_get_lexer_by_name():
    assert isinstance(get_lexer_by_name("python"), PythonLexer)
    assert isinstance(get_lexer_by_name("JSON"), JsonLexer)
    assert isinstance(get_lexer_by_name("ini"), IniLexer)
    with pytest.raises(ClassNotFound):
        get_lexer_by_name("doesnotexist")


def test_htmlformatter_nowrap_and_classes_and_escape():
    code = "x = 1 < 2\n"
    html = highlight(code, PythonLexer(), HtmlFormatter(nowrap=True))
    assert "&lt;" in html
    # should contain a span for at least something (number or operator)
    assert "<span" in html
    assert "".join(v for _, v in lex(code, PythonLexer())) == code


def test_htmlformatter_full_and_style_defs_and_noclasses():
    fmt = HtmlFormatter(full=True, cssclass="highlight")
    html = highlight("def f():\n  return 1\n", PythonLexer(), fmt)
    assert "<html" in html.lower()
    assert "<style>" in html.lower()
    css = fmt.get_style_defs(".highlight")
    assert ".highlight" in css
    assert "tok-Keyword" in css or ".k" in css

    html2 = highlight("def f():\n", PythonLexer(), HtmlFormatter(nowrap=True, noclasses=True))
    assert 'style="' in html2
    assert 'class="' not in html2


def test_terminalformatter_plain_and_ansi():
    code = "def f():\n  return 1\n"
    out_plain = highlight(code, PythonLexer(), TerminalFormatter(ansi=False))
    assert out_plain == code

    out_ansi = highlight(code, PythonLexer(), TerminalFormatter(ansi=True))
    assert "\x1b[" in out_ansi
    assert out_ansi.endswith("\x1b[0m") or out_ansi.endswith("\x1b[0m" + "")