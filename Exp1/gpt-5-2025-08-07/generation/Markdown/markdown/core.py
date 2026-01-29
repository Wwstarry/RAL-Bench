import io
import os
import re
from typing import List, Tuple, Optional


def escape_html(text: str) -> str:
    """Escape HTML special characters in text."""
    # Order matters: escape & first
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def escape_attr(value: str) -> str:
    """Escape string for use in HTML attribute value."""
    value = escape_html(value)
    value = value.replace('"', "&quot;")
    return value


class Markdown:
    """
    Minimal Markdown processor supporting core features used by tests:
    - ATX headings (#, ##, ...)
    - Paragraphs
    - Emphasis and strong emphasis (*, **, _, __)
    - Inline code (`code`)
    - Fenced (``` or ~~~) and indented code blocks
    - Unordered lists (-, +, *)
    - Ordered lists (1.)
    - Blockquotes (>)
    - Links [text](url)
    - Images ![alt](url)
    """

    def __init__(self, *args, **kwargs):
        # Accept common kwargs to be API-compatible; ignore most for this minimal implementation
        self.extensions = kwargs.get("extensions", []) or []
        self.extension_configs = kwargs.get("extension_configs", {}) or {}
        self.output_format = kwargs.get("output_format", "xhtml")
        # Track any per-conversion state if needed
        self.reset()

    def reset(self):
        """Reset internal state to allow reuse of the instance for multiple conversions."""
        self._placeholders = {}
        self._placeholder_order = []

    def convert(self, text: str) -> str:
        """Convert Markdown text to HTML."""
        if text is None:
            text = ""
        # Normalize line endings to \n
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        self.reset()
        html = self._parse_blocks(text.split("\n"))
        # Ensure a Unicode string is returned
        return html

    # --------------- Block-level parsing ---------------

    def _parse_blocks(self, lines: List[str]) -> str:
        out = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]

            # Skip blank lines
            if line.strip() == "":
                i += 1
                continue

            # Fenced code block: ``` or ~~~
            fence = self._starts_fence(line)
            if fence:
                fence_char, fence_len = fence
                code_lines, i = self._collect_fenced_code(lines, i, fence_char, fence_len)
                out.append(self._render_code_block("\n".join(code_lines)))
                continue

            # Blockquote
            if line.lstrip().startswith(">"):
                bq_lines, i = self._collect_blockquote(lines, i)
                # Recursively parse inner content
                inner_html = self._parse_blocks(bq_lines)
                out.append(f"<blockquote>\n{inner_html}</blockquote>\n")
                continue

            # Unordered list
            if self._is_ul_item(line):
                items, i = self._collect_list(lines, i, ordered=False)
                out.append(self._render_list(items, ordered=False))
                continue

            # Ordered list
            if self._is_ol_item(line):
                items, i = self._collect_list(lines, i, ordered=True)
                out.append(self._render_list(items, ordered=True))
                continue

            # Heading
            if self._is_atx_heading(line):
                level, text = self._parse_atx_heading(line)
                out.append(self._render_heading(level, text))
                i += 1
                continue

            # Indented code block
            if self._is_indented_code(line):
                code_lines, i = self._collect_indented_code(lines, i)
                out.append(self._render_code_block("\n".join(code_lines)))
                continue

            # Paragraph: collect until blank or other block
            para_lines = [line]
            i += 1
            while i < n:
                next_line = lines[i]
                if next_line.strip() == "":
                    i += 1
                    break
                # Stop if next line starts a new block (heading, list, quote, fence, indented code)
                if self._starts_fence(next_line) or self._is_ul_item(next_line) or self._is_ol_item(next_line) or self._is_atx_heading(next_line) or next_line.lstrip().startswith(">") or self._is_indented_code(next_line):
                    break
                para_lines.append(next_line)
                i += 1
            out.append(self._render_paragraph(" ".join([l.strip() for l in para_lines])))
        return "".join(out)

    def _render_heading(self, level: int, text: str) -> str:
        inline = self._parse_inline(text)
        return f"<h{level}>{inline}</h{level}>\n"

    def _render_paragraph(self, text: str) -> str:
        inline = self._parse_inline(text)
        return f"<p>{inline}</p>\n"

    def _render_list(self, items: List[str], ordered: bool) -> str:
        tag = "ol" if ordered else "ul"
        out = [f"<{tag}>\n"]
        for item in items:
            inline = self._parse_inline(item)
            out.append(f"<li>{inline}</li>\n")
        out.append(f"</{tag}>\n")
        return "".join(out)

    def _render_code_block(self, code: str) -> str:
        # Escape content within code block to display literal characters
        escaped = escape_html(code)
        return f"<pre><code>{escaped}\n</code></pre>\n"

    def _starts_fence(self, line: str) -> Optional[Tuple[str, int]]:
        m = re.match(r'^([`~]{3,})\s*.*$', line)
        if m:
            fence_str = m.group(1)
            return fence_str[0], len(fence_str)
        return None

    def _collect_fenced_code(self, lines: List[str], start: int, fence_char: str, fence_len: int) -> Tuple[List[str], int]:
        code_lines = []
        i = start + 1
        n = len(lines)
        closing_pattern = re.compile(r'^' + re.escape(fence_char) + r'{' + str(fence_len) + r',}\s*$')
        while i < n:
            line = lines[i]
            if closing_pattern.match(line):
                i += 1
                break
            code_lines.append(line)
            i += 1
        return code_lines, i

    def _collect_blockquote(self, lines: List[str], start: int) -> Tuple[List[str], int]:
        """
        Collect contiguous blockquote lines. Remove one leading '>' and optional following space.
        """
        collected = []
        i = start
        n = len(lines)
        while i < n:
            line = lines[i]
            if not line.lstrip().startswith(">"):
                break
            # Remove first '>' and one optional space after
            # Keep remaining exactly as is
            stripped = line.lstrip()
            if stripped.startswith(">"):
                inner = stripped[1:]
                if inner.startswith(" "):
                    inner = inner[1:]
                collected.append(inner)
            else:
                collected.append(line)
            i += 1
        return collected, i

    def _is_ul_item(self, line: str) -> bool:
        return re.match(r'^\s*([-+*])\s+.+$', line) is not None

    def _is_ol_item(self, line: str) -> bool:
        return re.match(r'^\s*\d+\.\s+.+$', line) is not None

    def _collect_list(self, lines: List[str], start: int, ordered: bool) -> Tuple[List[str], int]:
        items = []
        i = start
        n = len(lines)
        pattern_ul = re.compile(r'^\s*([-+*])\s+(.+)$')
        pattern_ol = re.compile(r'^\s*(\d+)\.\s+(.+)$')
        while i < n:
            line = lines[i]
            if line.strip() == "":
                i += 1
                # Blank line ends the list
                break
            m = (pattern_ol.match(line) if ordered else pattern_ul.match(line))
            if not m:
                break
            content = m.group(2)
            items.append(content.strip())
            i += 1
        return items, i

    def _is_atx_heading(self, line: str) -> bool:
        return re.match(r'^\s*#{1,6}\s+.*$', line) is not None

    def _parse_atx_heading(self, line: str) -> Tuple[int, str]:
        m = re.match(r'^\s*(#{1,6})\s+(.*)$', line)
        hashes = m.group(1)
        text = m.group(2) if m else line.strip()
        # Strip optional trailing hashes
        text = re.sub(r'\s+#+\s*$', '', text).strip()
        return len(hashes), text

    def _is_indented_code(self, line: str) -> bool:
        # At least 4 leading spaces or a tab
        return (len(line) - len(line.lstrip(" ")) >= 4) or (line.startswith("\t"))

    def _collect_indented_code(self, lines: List[str], start: int) -> Tuple[List[str], int]:
        code_lines = []
        i = start
        n = len(lines)
        while i < n:
            line = lines[i]
            if line.strip() == "":
                # Keep blank lines inside code block
                code_lines.append("")
                i += 1
                continue
            if not self._is_indented_code(line):
                break
            # Remove one level of indentation (4 spaces or one tab)
            if line.startswith("\t"):
                code_lines.append(line[1:])
            else:
                code_lines.append(line[4:])
            i += 1
        return code_lines, i

    # --------------- Inline parsing ---------------

    def _parse_inline(self, text: str) -> str:
        """
        Parse inline Markdown: code spans, links, images, strong/emphasis, and escape HTML.
        Strategy:
        - Replace inline code, links, and images with placeholders storing their final HTML.
        - Escape remaining text.
        - Apply strong/emphasis replacements.
        - Substitute placeholders back to HTML.
        """
        s = text if text is not None else ""
        self._placeholders = {}
        self._placeholder_order = []

        # Inline code spans
        s = self._replace_with_placeholders(s, r'`([^`]+)`', self._make_code_span)

        # Images: ![alt](url)
        s = self._replace_with_placeholders(s, r'!\[([^\]]*)\]\(([^)]+)\)', self._make_image)

        # Links: [text](url)
        s = self._replace_with_placeholders(s, r'\[([^\]]+)\]\(([^)]+)\)', self._make_link)

        # Escape remaining normal text
        s = escape_html(s)

        # Strong emphasis: **text** or __text__
        s = re.sub(r'\*\*([^*]+)\*\*', lambda m: f"<strong>{m.group(1)}</strong>", s)
        s = re.sub(r'__([^_]+)__', lambda m: f"<strong>{m.group(1)}</strong>", s)

        # Emphasis: *text* or _text_ (avoid catching already-strong)
        s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', lambda m: f"<em>{m.group(1)}</em>", s)
        s = re.sub(r'(?<!_)_([^_]+)_(?!_)', lambda m: f"<em>{m.group(1)}</em>", s)

        # Restore placeholders
        s = self._restore_placeholders(s)
        return s

    def _replace_with_placeholders(self, s: str, pattern: str, builder):
        def repl(m):
            html = builder(m)
            key = f"MDPH_{len(self._placeholder_order)}_X"
            self._placeholders[key] = html
            self._placeholder_order.append(key)
            return key
        return re.sub(pattern, repl, s)

    def _restore_placeholders(self, s: str) -> str:
        # Replace each placeholder token with stored HTML
        for key in self._placeholder_order:
            s = s.replace(key, self._placeholders.get(key, ""))
        return s

    # Builders for placeholders
    def _make_code_span(self, m) -> str:
        content = m.group(1)
        return f"<code>{escape_html(content)}</code>"

    def _make_image(self, m) -> str:
        alt = m.group(1)
        url = m.group(2)
        alt_attr = escape_attr(alt)
        src_attr = escape_attr(url)
        if self.output_format == "html5":
            return f'<img alt="{alt_attr}" src="{src_attr}">'
        else:
            return f'<img alt="{alt_attr}" src="{src_attr}" />'

    def _make_link(self, m) -> str:
        text = m.group(1)
        url = m.group(2)
        href = escape_attr(url)
        # Escape link text; we do not recursively parse emphasis within links in this minimal implementation
        inner = escape_html(text)
        return f'<a href="{href}">{inner}</a>'


# --------------- Top-level functions ---------------

def markdown(text: str, **kwargs) -> str:
    """
    Convert text (a Unicode string) containing Markdown into HTML.

    Usage:
        html = markdown(markdown_text, output_format='xhtml')
    """
    md = Markdown(**kwargs)
    return md.convert(text)


def markdownFromFile(**kwargs) -> str:
    """
    Convert Markdown from a file to HTML.

    Recognized kwargs:
        - input: path to input file (required)
        - output: optional path to output file; if provided, writes and returns the HTML
        - encoding: input/output file encoding (default 'utf-8')
        - All other kwargs are passed through to Markdown(...)
    """
    input_path = kwargs.pop("input", None)
    output_path = kwargs.pop("output", None)
    encoding = kwargs.pop("encoding", "utf-8")

    if input_path is None:
        raise TypeError("markdownFromFile() missing required keyword argument: 'input'")

    with io.open(input_path, "r", encoding=encoding) as f:
        text = f.read()

    html = markdown(text, **kwargs)

    if output_path:
        # Ensure parent directory exists
        parent = os.path.dirname(os.path.abspath(output_path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent)
        with io.open(output_path, "w", encoding=encoding) as out:
            out.write(html)
    return html