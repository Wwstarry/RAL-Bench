import re
import io

def markdown(text, **kwargs):
    """
    Convert a Markdown string to HTML and return the HTML as a Unicode string.
    """
    md = Markdown(**kwargs)
    return md.convert(text)

def markdownFromFile(**kwargs):
    """
    Convert Markdown text from a file to HTML and return the HTML as a Unicode string.
    Accepts file-related keyword arguments such as 'input' (file path),
    'encoding' (text encoding), etc.
    """
    input_file = kwargs.get('input', None)
    output = io.StringIO()
    encoding = kwargs.get('encoding', 'utf-8')

    if not input_file:
        raise ValueError("No input file specified for markdownFromFile")

    # Read file
    with io.open(input_file, 'r', encoding=encoding) as f:
        text = f.read()

    # Convert
    html = markdown(text, **kwargs)
    output.write(html)
    return output.getvalue()

class Markdown:
    """
    A Markdown class that can be used to convert text multiple times.
    """
    def __init__(self, **kwargs):
        self.reset()

    def reset(self):
        """
        Reset any state so that this instance can be reused for a new document.
        """
        pass

    def convert(self, text):
        """
        Convert the given Markdown text to HTML and return it as a Unicode string.
        """
        if not isinstance(text, str):
            # Ensure text is a Unicode string in Python 3
            text = str(text, 'utf-8', errors='replace')
        # Process blocks
        blocks = self._parse_blocks(text)
        # Convert blocks to HTML
        html = self._render_blocks(blocks)
        return html

    # -- BLOCK PARSING -----------------------------------------------------

    def _parse_blocks(self, text):
        """
        Parse text into a list of blocks with a simple state machine approach.
        Returns a list of block structures, each describing a piece of content.
        """
        lines = text.split('\n')
        blocks = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip blank lines quickly
            if not line.strip():
                i += 1
                continue

            # Check for fenced code block start
            m_fence = re.match(r'^(?P<fence>`{3,}|~{3,})(?P<info>.*)$', line.strip())
            if m_fence:
                fence_seq = m_fence.group('fence')
                code_lines, fence_end_idx = self._consume_fenced_code(lines, i, fence_seq)
                blocks.append({
                    'type': 'code',
                    'text': '\n'.join(code_lines)
                })
                i = fence_end_idx
                continue

            # Check for indented code block (4 spaces or 1 tab)
            if self._is_indented_code(line):
                code_lines, code_block_end = self._consume_indented_code(lines, i)
                blocks.append({
                    'type': 'code',
                    'text': '\n'.join(code_lines)
                })
                i = code_block_end
                continue

            # Check for heading (#, ##, ###, etc.)
            m_heading = re.match(r'^(?P<level>#{1,6})\s+(?P<content>.*)$', line)
            if m_heading:
                level = len(m_heading.group('level'))
                content = m_heading.group('content').strip()
                blocks.append({
                    'type': 'heading',
                    'level': level,
                    'text': content
                })
                i += 1
                continue

            # Check for blockquote
            if line.strip().startswith('>'):
                bq_lines, bq_end = self._consume_blockquote(lines, i)
                # Recursively parse the lines inside the blockquote
                inner_blocks = self._parse_blocks('\n'.join(bq_lines))
                blocks.append({
                    'type': 'blockquote',
                    'blocks': inner_blocks
                })
                i = bq_end
                continue

            # Check for list (unordered or ordered)
            m_ul = re.match(r'^\s*([*\-+])\s+(.*)$', line)
            m_ol = re.match(r'^\s*(\d+\.)\s+(.*)$', line)
            if m_ul or m_ol:
                list_block, list_end = self._consume_list(lines, i)
                blocks.append(list_block)
                i = list_end
                continue

            # Otherwise, treat as paragraph
            p_lines, p_end = self._consume_paragraph(lines, i)
            blocks.append({
                'type': 'paragraph',
                'text': '\n'.join(p_lines)
            })
            i = p_end

        return blocks

    def _consume_fenced_code(self, lines, start_idx, fence_seq):
        """
        Consume lines until a matching fence is found, return (code_lines, new_index).
        """
        code_lines = []
        i = start_idx + 1
        while i < len(lines):
            line = lines[i]
            # Check for fence close
            if re.match(r'^' + fence_seq + r'\s*$', line.strip()):
                return (code_lines, i + 1)
            code_lines.append(line)
            i += 1
        return (code_lines, i)

    def _is_indented_code(self, line):
        """
        Check if a line is an indented code line (4 spaces or a tab).
        """
        if line.startswith('    '):
            return True
        # Some tests might accept tab as well
        if line.startswith('\t'):
            return True
        return False

    def _consume_indented_code(self, lines, start_idx):
        """
        Consume consecutive indented lines as code.
        """
        code_lines = []
        i = start_idx
        while i < len(lines):
            line = lines[i]
            if self._is_indented_code(line):
                # Strip the first 4 spaces or 1 tab
                if line.startswith('    '):
                    code_lines.append(line[4:])
                elif line.startswith('\t'):
                    code_lines.append(line[1:])
                else:
                    code_lines.append(line)
                i += 1
            else:
                break
        return (code_lines, i)

    def _consume_blockquote(self, lines, start_idx):
        """
        Collect consecutive lines that start with '>' into a blockquote.
        """
        bq_lines = []
        i = start_idx
        while i < len(lines):
            line = lines[i]
            if not line.strip().startswith('>'):
                break
            # Remove leading '>'
            # Some lines may have multiple '>' for nested quotes, but let's do one level here
            stripped = re.sub(r'^\s*> ?', '', line)
            bq_lines.append(stripped)
            i += 1
        return (bq_lines, i)

    def _consume_list(self, lines, start_idx):
        """
        Consume consecutive lines that form a single list (either UL or OL).
        Return ({'type': 'ul'/'ol', 'items': [...]}, new_index).
        """
        # Detect if it's UL or OL from the first match
        is_ordered = False
        m_ol = re.match(r'^\s*(\d+\.)\s+.*$', lines[start_idx])
        if m_ol:
            is_ordered = True

        items = []
        i = start_idx
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                # blank line => end of list
                break
            # Check if still matching list item
            if is_ordered:
                match_item = re.match(r'^\s*(\d+\.)\s+(.*)$', line)
            else:
                match_item = re.match(r'^\s*([*\-+])\s+(.*)$', line)
            if not match_item:
                break
            content = match_item.group(2)
            # Collect item lines including subsequent indented lines
            item_lines, new_i = self._consume_list_item(lines, i, is_ordered)
            items.append('\n'.join(item_lines))
            i = new_i

        list_block = {
            'type': 'ol' if is_ordered else 'ul',
            'items': items
        }
        return (list_block, i)

    def _consume_list_item(self, lines, start_idx, is_ordered):
        """
        Collect lines belonging to a single list item.
        Return (list_of_item_lines, new_index).
        """
        item_lines = []
        # The first line is known to match the bullet/number
        line = lines[start_idx]
        if is_ordered:
            match_item = re.match(r'^\s*(\d+\.)\s+(.*)$', line)
        else:
            match_item = re.match(r'^\s*([*\-+])\s+(.*)$', line)
        item_content = match_item.group(2)
        item_lines.append(item_content)
        i = start_idx + 1

        # Now gather any subsequent indented lines as part of this item
        while i < len(lines):
            # Indent means belongs to this item
            if re.match(r'^\s{2,}.*$', lines[i]) and not self._is_list_start(lines[i]):
                item_lines.append(lines[i].strip())
                i += 1
            else:
                break

        return (item_lines, i)

    def _is_list_start(self, line):
        """
        Check if line starts a new list item in either UL or OL form.
        """
        if re.match(r'^\s*[*\-+]\s+', line):
            return True
        if re.match(r'^\s*\d+\.\s+', line):
            return True
        return False

    def _consume_paragraph(self, lines, start_idx):
        """
        Consume consecutive non-blank, non-special lines as a paragraph.
        """
        p_lines = []
        i = start_idx
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                break
            if self._is_indented_code(line):
                break
            # Check if a new block-like line starts
            if re.match(r'^(#{1,6})\s', line.strip()):
                break
            if re.match(r'^(?P<fence>`{3,}|~{3,})', line.strip()):
                break
            if line.strip().startswith('>'):
                break
            if self._is_list_start(line):
                break
            p_lines.append(line)
            i += 1
        return (p_lines, i)

    # -- BLOCK RENDERING ---------------------------------------------------

    def _render_blocks(self, blocks):
        """
        Render the list of block structures into an HTML string.
        """
        html_lines = []
        for block in blocks:
            if block['type'] == 'heading':
                level = block['level']
                text = self._render_inlines(block['text'])
                html_lines.append(f"<h{level}>{text}</h{level}>")
            elif block['type'] == 'paragraph':
                text = self._render_inlines(block['text'])
                html_lines.append(f"<p>{text}</p>")
            elif block['type'] == 'code':
                # Escape content but do not parse inlines
                code_escaped = self._escape_html(block['text'])
                html_lines.append(f"<pre><code>{code_escaped}</code></pre>")
            elif block['type'] == 'blockquote':
                # Render sub-blocks
                inner_html = self._render_blocks(block['blocks'])
                # We do not add <p> inside blockquotes for each line, we rely on sub-blocks
                html_lines.append(f"<blockquote>\n{inner_html}\n</blockquote>")
            elif block['type'] == 'ul':
                ul_content = []
                for item in block['items']:
                    li_rendered = self._render_inlines(item)
                    ul_content.append(f"<li>{li_rendered}</li>")
                html_lines.append("<ul>\n" + "\n".join(ul_content) + "\n</ul>")
            elif block['type'] == 'ol':
                ol_content = []
                for item in block['items']:
                    li_rendered = self._render_inlines(item)
                    ol_content.append(f"<li>{li_rendered}</li>")
                html_lines.append("<ol>\n" + "\n".join(ol_content) + "\n</ol>")
        return "\n".join(html_lines)

    # -- INLINE PARSING ----------------------------------------------------

    def _render_inlines(self, text):
        """
        Parse and render inline elements: code, bold, italic, links, images, etc.
        Also escape HTML where appropriate.
        """

        # First, store inline code blocks in placeholders
        code_spans = []
        def code_repl(m):
            code_text = m.group(1)
            code_spans.append(code_text)
            return f"\u0000CODE{len(code_spans)-1}\u0000"

        text = re.sub(r'`([^`]+)`', code_repl, text)

        # Next, parse images: ![alt](url)
        def image_repl(m):
            alt = m.group(1)
            url = m.group(2)
            alt_esc = self._escape_html(alt)
            url_esc = self._escape_html(url, quote=True)
            return f'<img src="{url_esc}" alt="{alt_esc}" />'

        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', image_repl, text)

        # Next, parse links: [text](url)
        def link_repl(m):
            label = m.group(1)
            url = m.group(2)
            label_rendered = self._escape_html(label)
            url_esc = self._escape_html(url, quote=True)
            return f'<a href="{url_esc}">{label_rendered}</a>'

        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_repl, text)

        # Next, parse strong emphasis with ** or __
        def strong_repl(m):
            content = m.group(2)
            content_rendered = self._render_inlines(content)  # might have nested inline
            return f'<strong>{content_rendered}</strong>'

        text = re.sub(r'(\*\*|__)(.+?)\1', strong_repl, text)

        # Then, parse emphasis with * or _
        def em_repl(m):
            content = m.group(2)
            content_rendered = self._render_inlines(content)  # handle nested
            return f'<em>{content_rendered}</em>'

        text = re.sub(r'(\*|_)(.+?)\1', em_repl, text)

        # Escape remaining HTML special chars (outside code)
        text = self._escape_html(text)

        # Restore code spans (they should keep original text unescaped)
        # We'll wrap them with <code>...</code>, with no escaping
        def restore_code(m):
            index = int(m.group(1))
            code_raw = code_spans[index]
            return f"<code>{self._escape_html(code_raw, in_code=True)}</code>"

        text = re.sub(r'\u0000CODE(\d+)\u0000', restore_code, text)

        return text

    def _escape_html(self, text, quote=False, in_code=False):
        """
        Escape HTML special characters <, &, and optionally quotes.
        If in_code=True, we still escape ampersand and < in code blocks
        to match typical Markdown HTML escaping for code.
        """
        # Typically we escape & first, then <. Quotation marks if needed.
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        if quote:
            text = text.replace('"', '&quot;')
        return text