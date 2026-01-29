"""
A **very** small, self-contained Markdown-to-HTML converter that supports
just enough features for the educational test-suite that accompanies this
repository.

Supported block-level elements
------------------------------
* ATX headings (``#`` .. ``######``)
* Paragraphs (separated by blank lines)
* Block quotes (``>``)
* Fenced code blocks (````` .. `````)
* Indented code blocks (4-space / tab)
* Ordered & unordered lists (single-line items)

Supported inline elements
-------------------------
* ``*em*`` and ``_em_``
* ``**strong**`` and ``__strong__``
* ``[link text](url)``
* ``![alt text](url)``
* Inline code: `` `code` ``

Anything not explicitly supported is passed through as plain text with HTML
characters escaped.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import List


def _escape_html(text: str) -> str:
    """
    Escape *text* for literal HTML output.

    We rely on :pymod:`html` for correctness.
    """
    return html.escape(text, quote=False)


# --------------------------------------------------------------------------- #
# Inline parsing utilities
# --------------------------------------------------------------------------- #


_INLINE_CODE_RE = re.compile(r"(?s)`([^`]+)`")
_STRONG_RE = re.compile(r"(\*\*|__)(.+?)\1")
_EM_RE = re.compile(r"(\*|_)([^*_]+?)\1")
_LINK_RE = re.compile(r"\[([^\]]+?)\]\(([^)]+?)\)")
_IMAGE_RE = re.compile(r"!\[([^\]]*?)\]\(([^)]+?)\)")


def _process_inline(text: str) -> str:
    """
    Apply inline-level Markdown transformations and return HTML.

    We purposefully keep this *very* small and not 100% spec-compliant,
    but sufficiently close for the bundled tests.
    """
    # Step 1: isolate inline code so that we do **not** alter its content.
    placeholders: List[str] = []
    placeholder_fmt = "\u0000{:03d}\u0000"

    def _code_sub(match: re.Match) -> str:
        code = _escape_html(match.group(1))
        placeholders.append(f"<code>{code}</code>")
        return placeholder_fmt.format(len(placeholders) - 1)

    text = _INLINE_CODE_RE.sub(_code_sub, text)

    # Step 2: escape everything (excluding our placeholders which do not
    # contain characters that are touched by html.escape).
    text = _escape_html(text)

    # Step 3: images & links (order matters: images first to avoid matching as links)
    text = _IMAGE_RE.sub(r'<img alt="\1" src="\2" />', text)
    text = _LINK_RE.sub(r'<a href="\2">\1</a>', text)

    # Step 4: strong and emphasis
    text = _STRONG_RE.sub(r"<strong>\2</strong>", text)
    text = _EM_RE.sub(r"<em>\2</em>", text)

    # Step 5: restore code placeholders
    def _restore_placeholders(m: re.Match) -> str:
        idx = int(m.group(1))
        return placeholders[idx]

    text = re.sub(r"\u0000(\d{3})\u0000", _restore_placeholders, text)
    return text


# --------------------------------------------------------------------------- #
# Block parsing
# --------------------------------------------------------------------------- #


@dataclass
class Markdown:
    """
    Minimal stand-in replacement for **markdown.Markdown** from the reference
    implementation.
    """

    def reset(self) -> None:
        """Reset any per-document state (currently a no-op)."""
        pass

    # --------------------------------------------------------------------- #

    def convert(self, text: str) -> str:
        """
        Convert *text* (Markdown) to HTML and return it.

        The implementation is intentionally simple and only supports a subset
        of the full Markdown syntax.
        """
        self.reset()
        if not text:
            return ""

        # Normalize line endings and split into list for easier processing.
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        html_lines: List[str] = []
        i = 0
        total = len(lines)

        while i < total:
            line = lines[i]

            # Skip blank lines
            if not line.strip():
                i += 1
                continue

            # -------------------------------------------------- fenced code block
            if line.lstrip().startswith("```"):
                fence = line.lstrip()
                fence_marker = fence[:3]  # assume ```
                i += 1
                code_content: List[str] = []
                while i < total and not lines[i].lstrip().startswith(fence_marker):
                    code_content.append(lines[i])
                    i += 1
                # Skip closing fence
                if i < total:
                    i += 1
                code_text = "\n".join(code_content)
                html_lines.append(f"<pre><code>{_escape_html(code_text)}</code></pre>")
                continue

            # -------------------------------------------------- indented code block
            if line.startswith("    ") or line.startswith("\t"):
                code_content: List[str] = []
                while i < total and (lines[i].startswith("    ") or lines[i].startswith("\t")):
                    code_content.append(lines[i][4:] if lines[i].startswith("    ") else lines[i].lstrip("\t"))
                    i += 1
                code_text = "\n".join(code_content)
                html_lines.append(f"<pre><code>{_escape_html(code_text)}</code></pre>")
                continue

            # -------------------------------------------------- heading (ATX)
            m = re.match(r"(#{1,6})\s*(.+?)\s*#*\s*$", line)
            if m:
                level = len(m.group(1))
                content = _process_inline(m.group(2).strip())
                html_lines.append(f"<h{level}>{content}</h{level}>")
                i += 1
                continue

            # -------------------------------------------------- blockquote
            if line.lstrip().startswith(">"):
                quote_lines: List[str] = []
                while i < total and lines[i].lstrip().startswith(">"):
                    # Remove leading '>' and one optional space.
                    stripped = lines[i].lstrip()[1:]
                    if stripped.startswith(" "):
                        stripped = stripped[1:]
                    quote_lines.append(stripped)
                    i += 1
                # Recursively convert the inside of the blockquote.
                inner_html = self.convert("\n".join(quote_lines))
                html_lines.append(f"<blockquote>\n{inner_html}\n</blockquote>")
                continue

            # -------------------------------------------------- list (ordered / unordered)
            list_match = re.match(r"\s*([*+\-]|\d+\.)\s+(.*)", line)
            if list_match:
                ordered = list_match.group(1).endswith(".")
                tag = "ol" if ordered else "ul"
                items: List[str] = []
                while i < total:
                    m2 = re.match(r"\s*([*+\-]|\d+\.)\s+(.*)", lines[i])
                    if not m2:
                        break
                    curr_ordered = m2.group(1).endswith(".")
                    if curr_ordered != ordered:
                        break
                    item_text = m2.group(2)
                    items.append(_process_inline(item_text))
                    i += 1
                li_html = "".join(f"<li>{item}</li>" for item in items)
                html_lines.append(f"<{tag}>\n{li_html}\n</{tag}>")
                continue

            # -------------------------------------------------- paragraph
            para_lines: List[str] = []
            while i < total and lines[i].strip():
                # Stop paragraph if next line is starting a block element
                potential = lines[i]
                if (
                    re.match(r"(#{1,6})\s", potential)
                    or potential.lstrip().startswith((">", "```"))
                    or re.match(r"\s*([*+\-]|\d+\.)\s+", potential)
                    or potential.startswith("    ")
                    or potential.startswith("\t")
                ):
                    # But only break if we're at start (which we are)
                    if para_lines:
                        break
                para_lines.append(lines[i])
                i += 1
            para_text = " ".join(l.strip() for l in para_lines)
            html_lines.append(f"<p>{_process_inline(para_text)}</p>")

        # Join with newline to make human-readable output (insignificant in HTML)
        return "\n".join(html_lines)


# Expose convenience wrapper consistent with original API
def markdown(text: str, **kwargs):
    return Markdown(**kwargs).convert(text)