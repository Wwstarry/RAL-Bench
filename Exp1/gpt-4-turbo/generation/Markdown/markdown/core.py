import re
import html
import io

# --- Utility functions ---

def _escape(text):
    """Escape HTML-sensitive characters except inside code spans/blocks."""
    return html.escape(text, quote=False)

def _unescape(text):
    """Unescape HTML entities."""
    return html.unescape(text)

def _escape_except_code(text, code_spans):
    """Escape all except code spans."""
    result = []
    last = 0
    for start, end in code_spans:
        result.append(_escape(text[last:start]))
        result.append(text[start:end])  # code span, do not escape
        last = end
    result.append(_escape(text[last:]))
    return ''.join(result)

def _find_code_spans(text):
    """Find all inline code spans in text, return list of (start, end) indices."""
    spans = []
    for m in re.finditer(r'(`+)([^`]*?)\1', text):
        spans.append((m.start(), m.end()))
    return spans

def _strip(s):
    return s.strip()

# --- Block-level parsing ---

class Markdown:
    def __init__(self, **kwargs):
        self.reset()
        self.options = kwargs

    def reset(self):
        self._html = []
        self._in_list = False
        self._list_type = None
        self._in_blockquote = False
        self._blockquote_level = 0
        self._in_codeblock = False
        self._codeblock_fence = None
        self._codeblock_lines = []
        self._in_paragraph = False
        self._buffer = []
        self._last_was_blank = True

    def convert(self, text):
        self.reset()
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            # Handle fenced code block start/end
            fence_match = re.match(r'^([`~]{3,})(.*)$', line)
            if fence_match:
                fence = fence_match.group(1)
                if not self._in_codeblock:
                    self._in_codeblock = True
                    self._codeblock_fence = fence
                    self._codeblock_lines = []
                    i += 1
                    continue
                elif self._in_codeblock and fence == self._codeblock_fence:
                    self._html.append('<pre><code>{}</code></pre>'.format(
                        ''.join(self._codeblock_lines)
                    ))
                    self._in_codeblock = False
                    self._codeblock_fence = None
                    self._codeblock_lines = []
                    i += 1
                    continue
            if self._in_codeblock:
                self._codeblock_lines.append(line + '\n')
                i += 1
                continue

            # Indented code block (4 spaces or tab)
            if re.match(r'^( {4}|\t)', line):
                if not self._in_codeblock:
                    self._in_codeblock = True
                    self._codeblock_fence = None
                    self._codeblock_lines = []
                self._codeblock_lines.append(line[4:] if line.startswith('    ') else line.lstrip('\t'))
                self._codeblock_lines.append('\n')
                i += 1
                # Check next line for end of indented code block
                if i < len(lines):
                    next_line = lines[i]
                    if not re.match(r'^( {4}|\t)', next_line):
                        self._html.append('<pre><code>{}</code></pre>'.format(
                            ''.join(self._codeblock_lines)
                        ))
                        self._in_codeblock = False
                        self._codeblock_fence = None
                        self._codeblock_lines = []
                else:
                    self._html.append('<pre><code>{}</code></pre>'.format(
                        ''.join(self._codeblock_lines)
                    ))
                    self._in_codeblock = False
                    self._codeblock_fence = None
                    self._codeblock_lines = []
                continue

            # Blank line
            if line.strip() == '':
                if self._in_paragraph:
                    self._html.append('<p>{}</p>'.format(self._render_inline(' '.join(self._buffer))))
                    self._buffer = []
                    self._in_paragraph = False
                self._last_was_blank = True
                i += 1
                continue

            # ATX headings
            heading_match = re.match(r'^(#{1,6})\s+(.*)', line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2).strip()
                self._html.append('<h{lvl}>{txt}</h{lvl}>'.format(
                    lvl=level,
                    txt=self._render_inline(content)
                ))
                self._last_was_blank = False
                i += 1
                continue

            # Blockquote
            blockquote_match = re.match(r'^(>+)\s?(.*)', line)
            if blockquote_match:
                level = len(blockquote_match.group(1))
                content = blockquote_match.group(2)
                # Collect consecutive blockquote lines
                block_lines = [content]
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    m = re.match(r'^(>+)\s?(.*)', next_line)
                    if m:
                        block_lines.append(m.group(2))
                        j += 1
                    elif next_line.strip() == '':
                        block_lines.append('')
                        j += 1
                    else:
                        break
                block_html = self._render_inline('\n'.join(block_lines))
                for _ in range(level):
                    block_html = '<blockquote>{}</blockquote>'.format(block_html)
                self._html.append(block_html)
                i = j
                self._last_was_blank = False
                continue

            # Unordered list
            ul_match = re.match(r'^(\s*)([*+-])\s+(.*)', line)
            if ul_match:
                indent = len(ul_match.group(1))
                items = []
                j = i
                while j < len(lines):
                    m = re.match(r'^(\s*)([*+-])\s+(.*)', lines[j])
                    if m:
                        items.append(self._render_inline(m.group(3)))
                        j += 1
                    else:
                        break
                self._html.append('<ul>{}</ul>'.format(
                    ''.join('<li>{}</li>'.format(item) for item in items)
                ))
                i = j
                self._last_was_blank = False
                continue

            # Ordered list
            ol_match = re.match(r'^(\s*)(\d+)\.\s+(.*)', line)
            if ol_match:
                indent = len(ol_match.group(1))
                items = []
                j = i
                while j < len(lines):
                    m = re.match(r'^(\s*)(\d+)\.\s+(.*)', lines[j])
                    if m:
                        items.append(self._render_inline(m.group(3)))
                        j += 1
                    else:
                        break
                self._html.append('<ol>{}</ol>'.format(
                    ''.join('<li>{}</li>'.format(item) for item in items)
                ))
                i = j
                self._last_was_blank = False
                continue

            # Paragraph
            if not self._in_paragraph:
                self._buffer = [line.strip()]
                self._in_paragraph = True
            else:
                self._buffer.append(line.strip())
            self._last_was_blank = False
            i += 1

        # End of document: flush paragraph
        if self._in_paragraph:
            self._html.append('<p>{}</p>'.format(self._render_inline(' '.join(self._buffer))))
            self._buffer = []
            self._in_paragraph = False

        return ''.join(self._html)

    # --- Inline-level parsing ---
    def _render_inline(self, text):
        # Find code spans first
        code_spans = []
        for m in re.finditer(r'(`+)([^`]*?)\1', text):
            code_spans.append((m.start(), m.end()))
        # Escape everything except code spans
        result = []
        last = 0
        for start, end in code_spans:
            # Escape text before code span
            result.append(_escape(text[last:start]))
            # Code span: wrap in <code>, do not escape
            code_content = text[start:end]
            code_inner = re.match(r'`+([^`]*)`+', code_content)
            code_text = code_inner.group(1) if code_inner else code_content
            result.append('<code>{}</code>'.format(code_text))
            last = end
        result.append(_escape(text[last:]))

        text = ''.join(result)

        # Images ![alt](url)
        text = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            lambda m: '<img alt="{}" src="{}" />'.format(
                _escape(m.group(1)), _escape(m.group(2))
            ),
            text
        )

        # Links [text](url)
        text = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            lambda m: '<a href="{}">{}</a>'.format(
                _escape(m.group(2)), _escape(m.group(1))
            ),
            text
        )

        # Strong emphasis: **text** or __text__
        text = re.sub(
            r'(\*\*|__)(.+?)\1',
            lambda m: '<strong>{}</strong>'.format(m.group(2)),
            text
        )

        # Emphasis: *text* or _text_
        text = re.sub(
            r'(\*|_)([^*_]+?)\1',
            lambda m: '<em>{}</em>'.format(m.group(2)),
            text
        )

        return text

def markdown(text, **kwargs):
    """Convert Markdown text to HTML."""
    md = Markdown(**kwargs)
    return md.convert(text)

def markdownFromFile(**kwargs):
    """Convert Markdown from file to HTML."""
    input = kwargs.get('input')
    encoding = kwargs.get('encoding', 'utf-8')
    if hasattr(input, 'read'):
        text = input.read()
        if isinstance(text, bytes):
            text = text.decode(encoding)
    else:
        with io.open(input, encoding=encoding) as f:
            text = f.read()
    return markdown(text, **kwargs)