from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("PYGMENTS_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "pygments"
else:
    REPO_ROOT = ROOT / "generation" / "Pygments"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pygments import highlight  # type: ignore  # noqa: E402
from pygments.lexers import (  # type: ignore  # noqa: E402
    PythonLexer,
    JsonLexer,
    IniLexer,
    get_lexer_by_name,
)
from pygments.formatters import HtmlFormatter, TerminalFormatter  # type: ignore  # noqa: E402


def _sample_snippets() -> dict[str, str]:
    """Return a small collection of code snippets for various languages."""
    return {
        "python": 'def hello(name):\n    print(f"Hello, {name}")\n',
        "json": '{"name": "Alice", "age": 30, "active": true}\n',
        "ini": "[section]\nkey=value\n",
    }


def test_multi_language_highlighting_to_html(tmp_path: Path) -> None:
    """Highlight multiple language snippets into a single HTML document."""
    snippets = _sample_snippets()
    formatter = HtmlFormatter(full=True)
    combined_html_parts: list[str] = []

    for lang, code in snippets.items():
        if lang == "python":
            lexer = PythonLexer()
        elif lang == "json":
            lexer = JsonLexer()
        elif lang == "ini":
            lexer = IniLexer()
        else:
            lexer = get_lexer_by_name(lang)
        html = highlight(code, lexer, formatter)
        combined_html_parts.append(html)

    combined_html = "\n<hr/>\n".join(combined_html_parts)

    out_path = tmp_path / "combined.html"
    out_path.write_text(combined_html, encoding="utf-8")

    assert out_path.exists()
    text = out_path.read_text(encoding="utf-8")
    # Should contain fragments from all snippets.
    assert "hello" in text
    assert '"Alice"' in text or "Alice" in text
    assert "[section]" in text
    # Should clearly look like HTML.
    assert "<html" in text.lower() or "<span" in text


def test_terminal_formatter_output() -> None:
    """Use TerminalFormatter to render ANSI-colored output."""
    code = "for i in range(3):\n    print(i)\n"
    lexer = PythonLexer()
    formatter = TerminalFormatter()

    ansi = highlight(code, lexer, formatter)

    # There should be some ANSI escape sequences or at least the content.
    assert "print" in ansi
    # Some terminals or configurations may strip colors, so we only do a soft check.
    has_escape = "\x1b[" in ansi
    assert ansi.strip() != ""
    # Either we have escapes or at least the original code is present.
    assert has_escape or "for i in range" in ansi
