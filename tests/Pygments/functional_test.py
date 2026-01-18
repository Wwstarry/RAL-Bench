from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Decide whether to test the reference repo or a generated repo.
target = os.environ.get("PYGMENTS_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "pygments"
else:
    REPO_ROOT = ROOT / "generation" / "Pygments"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pygments  # type: ignore  # noqa: E402
from pygments import highlight  # type: ignore  # noqa: E402
from pygments.lexers import PythonLexer, get_lexer_by_name  # type: ignore  # noqa: E402
from pygments.formatters import HtmlFormatter  # type: ignore  # noqa: E402
from pygments.token import Token  # type: ignore  # noqa: E402


def test_basic_lex_python_code() -> None:
    """Lexing a simple Python snippet should produce non-empty tokens."""
    code = 'def add(a, b):\n    return a + b\n'
    lexer = PythonLexer()

    tokens = list(pygments.lex(code, lexer))
    assert tokens, "Expected non-empty token stream"

    # There should be at least one name and one keyword.
    token_types = {t for (t, _v) in tokens}
    assert any(t in token_types for t in (Token.Name, Token.Name.Function))
    assert any(t in token_types for t in (Token.Keyword,))


def test_highlight_to_html() -> None:
    """Highlight Python code to HTML using the HTML formatter."""
    code = 'for i in range(3):\n    print(i)\n'
    html = highlight(code, PythonLexer(), HtmlFormatter())

    # Should look like HTML and contain the original code content.
    assert "<span" in html
    assert "print" in html
    assert "range" in html
    # HTML should contain at least one CSS class from the default style.
    assert "class=" in html


def test_get_lexer_by_name_and_aliases() -> None:
    """get_lexer_by_name should work for multiple language names and aliases."""
    py_lexer = get_lexer_by_name("python")
    assert isinstance(py_lexer, PythonLexer)

    json_lexer = get_lexer_by_name("json")
    assert json_lexer.name.lower().startswith("json")

    # Aliases should work as well (e.g., 'py' for Python, if defined).
    try:
        alias_lexer = get_lexer_by_name("py")
    except Exception:
        pytest.skip("This Pygments version does not define 'py' alias for Python")
    else:
        # Either it is a Python lexer or something clearly related to Python.
        assert "python" in alias_lexer.name.lower()


def test_html_formatter_css_generation(tmp_path: Path) -> None:
    """HTML formatter should be able to generate CSS definitions."""
    formatter = HtmlFormatter()
    css = formatter.get_style_defs(".highlight")
    assert ".highlight" in css
    assert "background" in css or "color" in css

    # Optionally write CSS to a file to simulate real-world usage.
    css_path = tmp_path / "pygments.css"
    css_path.write_text(css, encoding="utf-8")
    assert css_path.exists()
    assert css_path.stat().st_size > 0
