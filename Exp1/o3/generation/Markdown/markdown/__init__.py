"""
A very small subset implementation of the **Python-Markdown** public API.

The goal of this package is **compatibility** with the most common entry
points (`markdown`, `markdownFromFile`, and the `Markdown` class with a
`convert` method) that are required by the test-suite used in this
environment.

It is NOT intended to be a full drop-in replacement for the real
*Python-Markdown* library – only a minimal, pure-Python implementation that
is “good enough” for the unit-tests that accompany this coding challenge.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .core import Markdown as _Markdown

# Re-export the Markdown class so that users can do:
#     from markdown import Markdown
Markdown = _Markdown

###############################################################################
# Public convenience wrappers
###############################################################################


def markdown(text: str, **kwargs: Any) -> str:
    """
    Convert *text* (a Unicode string containing Markdown markup) to HTML.

    Parameters
    ----------
    text: str
        The Markdown source.
    **kwargs:
        Any keyword arguments accepted by ``markdown.Markdown`` constructor.

    Returns
    -------
    str
        A Unicode string containing the rendered HTML.
    """
    md = Markdown(**kwargs)
    return md.convert(text)


def markdownFromFile(
    *, input: str | Path, output: Optional[str | Path] = None, encoding: str = "utf-8", **kwargs: Any  # noqa: A002
) -> Optional[str]:
    """
    Read Markdown *input* from a file, convert it to HTML and either return the
    resulting HTML string or write it to *output* when given.

    Parameters
    ----------
    input:
        Path to the input file or a file-like object opened for reading text.
    output:
        Optional path or file-like object to write HTML into.  If *output* is
        omitted, the HTML string is returned instead.
    encoding:
        Text encoding used when *input* / *output* are paths rather than open
        file objects.
    **kwargs:
        Any keyword arguments forwarded to :pyclass:`markdown.Markdown`.

    Returns
    -------
    str | None
        The generated HTML if *output* is *None*.  Otherwise *None*.
    """
    # ------------------------------------------------------------------ helpers
    def _open_if_path(maybe_path, mode):
        if hasattr(maybe_path, "read") or hasattr(maybe_path, "write"):
            # Already a file-like object – leave untouched.
            return maybe_path, False
        fp = open(Path(maybe_path), mode, encoding=encoding)
        return fp, True

    # ------------------------------------------------------------------ input
    in_fp, close_in = _open_if_path(input, "r")
    try:
        source = in_fp.read()
    finally:
        if close_in:
            in_fp.close()

    html = markdown(source, **kwargs)

    # ------------------------------------------------------------------ output
    if output is None:
        return html

    out_fp, close_out = _open_if_path(output, "w")
    try:
        out_fp.write(html)
    finally:
        if close_out:
            out_fp.close()
    return None


# Re-export names the real project exposes at top-level.
__all__ = ["Markdown", "markdown", "markdownFromFile"]