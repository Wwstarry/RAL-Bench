import re
import html


class Markdown:
    def __init__(self, **kwargs):
        self.reset()

    def reset(self):
        self.html = []

    def convert(self, text):
        self.reset()
        lines = text.splitlines()
        self.lines = lines
        self.pos = 0
        self.length = len(lines)
        self.html = []
        while self.pos < self.length:
            if self._parse_blank_line():
                continue
            if self._parse_atx_heading():
                continue
            if self._parse_fenced_code_block():
                continue
            if self._parse_indented_code_block():
                continue
            if self._parse_blockquote():
                continue
            if self._parse_ordered_list():
                continue
            if self._parse_unordered_list():
                continue
            if self._parse_paragraph():
                continue
            # If none matched, advance to avoid infinite loop
            self.pos += 1
        return '\n'.join(self.html)

    def _parse_blank_line(self):
        if self.pos >= self.length:
            return False
        line = self.lines[self.pos]
        if line.strip() == '':
            self.pos += 1
            return True
        return False

    def _parse_atx_heading(self):
        line = self.lines[self.pos]
        m = re.match(r'^(#{1,6})\s*(.*?)\s*#*\s*$', line)
        if m:
            level = len(m.group(1))
            content = m.group(2)
            content = self._parse_inlines(content)
            self.html.append(f'<h{level}>{content}</h{level}>')
            self.pos += 1
            return True
        return False

    def _parse_fenced_code_block(self):
        line = self.lines[self.pos]
        m = re.match(r'^(`{3,}|~{3,})(.*)$', line)
        if not m:
            return False
        fence = m.group(1)
        lang = m.group(2).strip()
        self.pos += 1
        code_lines = []
        while self.pos < self.length:
            line = self.lines[self.pos]
            if line.startswith(fence):
                self.pos += 1
                break
            code_lines.append(line)
            self.pos += 1
        code = '\n'.join(code_lines)
        code_escaped = html.escape(code, quote=False)
        if lang:
            self.html.append(f'<pre><code class="language-{html.escape(lang)}">{code_escaped}\n</code></pre>')
        else:
            self.html.append(f'<pre><code>{code_escaped}\n</code></pre>')
        return True

    def _parse_indented_code_block(self):
        # Indented code block: lines indented by at least 4 spaces or 1 tab
        if self.pos >= self.length:
            return False
        line = self.lines[self.pos]
        if not (line.startswith('    ') or line.startswith('\t')):
            return False
        code_lines = []
        while self.pos < self.length:
            line = self.lines[self.pos]
            if line.startswith('    '):
                code_lines.append(line[4:])
            elif line.startswith('\t'):
                code_lines.append(line[1:])
            else:
                break
            self.pos += 1
        code = '\n'.join(code_lines)
        code_escaped = html.escape(code, quote=False)
        self.html.append(f'<pre><code>{code_escaped}\n</code></pre>')
        return True

    def _parse_blockquote(self):
        if self.pos >= self.length:
            return False
        line = self.lines[self.pos]
        if not line.lstrip().startswith('>'):
            return False
        bq_lines = []
        while self.pos < self.length:
            line = self.lines[self.pos]
            if line.lstrip().startswith('>'):
                # Remove leading '>' and one optional space after it
                content = line.lstrip()[1:]
                if content.startswith(' '):
                    content = content[1:]
                bq_lines.append(content)
                self.pos += 1
            elif line.strip() == '':
                # Blank lines inside blockquote are allowed
                bq_lines.append('')
                self.pos += 1
            else:
                break
        # Recursively parse the blockquote content
        inner_html = Markdown().convert('\n'.join(bq_lines))
        self.html.append(f'<blockquote>\n{inner_html}\n</blockquote>')
        return True

    def _parse_ordered_list(self):
        if self.pos >= self.length:
            return False
        line = self.lines[self.pos]
        m = re.match(r'^(\s*)(\d+)\.\s+(.*)$', line)
        if not m:
            return False
        indent = len(m.group(1))
        items = []
        while self.pos < self.length:
            line = self.lines[self.pos]
            m = re.match(r'^(\s*)(\d+)\.\s+(.*)$', line)
            if not m:
                break
            current_indent = len(m.group(1))
            if current_indent != indent:
                break
            item_lines = [m.group(3)]
            self.pos += 1
            # Collect continuation lines for this list item
            while self.pos < self.length:
                next_line = self.lines[self.pos]
                if next_line.strip() == '':
                    item_lines.append('')
                    self.pos += 1
                    continue
                # continuation lines must be indented more than list marker
                if len(next_line) > indent + 1 and (next_line.startswith(' ' * (indent + 1)) or next_line.startswith('\t')):
                    item_lines.append(next_line[indent + 1:] if next_line.startswith(' ' * (indent + 1)) else next_line[1:])
                    self.pos += 1
                else:
                    break
            item_text = '\n'.join(item_lines)
            item_html = Markdown().convert(item_text)
            items.append(f'<li>{item_html}</li>')
        if not items:
            return False
        self.html.append('<ol>')
        self.html.extend(items)
        self.html.append('</ol>')
        return True

    def _parse_unordered_list(self):
        if self.pos >= self.length:
            return False
        line = self.lines[self.pos]
        m = re.match(r'^(\s*)([-+*])\s+(.*)$', line)
        if not m:
            return False
        indent = len(m.group(1))
        items = []
        while self.pos < self.length:
            line = self.lines[self.pos]
            m = re.match(r'^(\s*)([-+*])\s+(.*)$', line)
            if not m:
                break
            current_indent = len(m.group(1))
            if current_indent != indent:
                break
            item_lines = [m.group(3)]
            self.pos += 1
            # Collect continuation lines for this list item
            while self.pos < self.length:
                next_line = self.lines[self.pos]
                if next_line.strip() == '':
                    item_lines.append('')
                    self.pos += 1
                    continue
                # continuation lines must be indented more than list marker
                if len(next_line) > indent + 1 and (next_line.startswith(' ' * (indent + 1)) or next_line.startswith('\t')):
                    item_lines.append(next_line[indent + 1:] if next_line.startswith(' ' * (indent + 1)) else next_line[1:])
                    self.pos += 1
                else:
                    break
            item_text = '\n'.join(item_lines)
            item_html = Markdown().convert(item_text)
            items.append(f'<li>{item_html}</li>')
        if not items:
            return False
        self.html.append('<ul>')
        self.html.extend(items)
        self.html.append('</ul>')
        return True

    def _parse_paragraph(self):
        if self.pos >= self.length:
            return False
        lines = []
        while self.pos < self.length:
            line = self.lines[self.pos]
            if line.strip() == '':
                break
            # Stop if next line is a block element start
            if (re.match(r'^(#{1,6})\s', line) or
                re.match(r'^(`{3,}|~{3,})', line) or
                re.match(r'^\s{4,}', line) or
                re.match(r'^\s*\d+\.\s+', line) or
                re.match(r'^\s*[-+*]\s+', line) or
                re.match(r'^\s*>', line)):
                break
            lines.append(line)
            self.pos += 1
        if not lines:
            return False
        text = '\n'.join(lines)
        text = self._parse_inlines(text)
        self.html.append(f'<p>{text}</p>')
        return True

    def _parse_inlines(self, text):
        # Escape &, <, > first
        text = html.escape(text, quote=False)

        # Inline code: `code`
        # We must preserve raw content inside backticks, no escaping inside
        # So we find all inline code spans and temporarily replace them
        code_spans = []
        def code_replacer(match):
            code_spans.append(match.group(1))
            return f"@@CODE{len(code_spans)-1}@@"
        text = re.sub(r'`([^`\n]+)`', code_replacer, text)

        # Links and images
        # ![alt](url)
        def image_replacer(match):
            alt = match.group(1)
            url = match.group(2)
            alt = alt.replace('"', '&quot;')
            url = url.replace('"', '&quot;')
            return f'<img src="{url}" alt="{alt}" />'
        text = re.sub(r'!\[([^\]]*?)\]\(([^)]+?)\)', image_replacer, text)

        # [text](url)
        def link_replacer(match):
            label = match.group(1)
            url = match.group(2)
            return f'<a href="{url}">{label}</a>'
        text = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', link_replacer, text)

        # Strong emphasis: **text** or __text__
        # Use non-greedy matching to avoid overmatching
        text = re.sub(r'(\*\*|__)(.+?)\1', r'<strong>\2</strong>', text)

        # Emphasis: *text* or _text_
        # Avoid matching inside strong tags by negative lookahead/lookbehind
        text = re.sub(r'(\*|_)([^*_]+?)\1', r'<em>\2</em>', text)

        # Restore inline code spans
        def restore_code(match):
            idx = int(match.group(1))
            code = code_spans[idx]
            code_escaped = html.escape(code, quote=False)
            return f'<code>{code_escaped}</code>'
        text = re.sub(r'@@CODE(\d+)@@', restore_code, text)

        return text


def markdown(text, **kwargs):
    md = Markdown(**kwargs)
    return md.convert(text)


def markdownFromFile(input=None, encoding='utf-8', **kwargs):
    if input is None:
        raise TypeError("markdownFromFile() missing required argument: 'input'")
    with open(input, encoding=encoding) as f:
        text = f.read()
    return markdown(text, **kwargs)