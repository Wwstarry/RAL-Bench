# -*- coding: utf-8 -*-
"""
Core implementation of the Markdown parser.
"""

import re
import html

class Markdown:
    """
    A pure Python Markdown to HTML converter.
    API-compatible with the core of Python-Markdown.
    """

    def __init__(self, **kwargs):
        """
        Creates a new Markdown instance.
        Keyword arguments are ignored for core compatibility.
        """
        self.reset()

    def reset(self):
        """
        Resets the state of the parser. As this implementation is stateless
        between convert() calls, this method is for API compatibility.
        It clears any stored state from a previous conversion.
        """
        self._code_placeholders = []
        return self

    def _store_code(self, m):
        """Callback for re.sub to store inline code and return a placeholder."""
        code = html.escape(m.group(1))
        placeholder = f"__CODE_PLACEHOLDER_{len(self._code_placeholders)}__"
        self._code_placeholders.append(f"<code>{code}</code>")
        return placeholder

    def _parse_inlines(self, text):
        """Processes inline Markdown syntax within a block of text."""
        # 1. Process inline code first to prevent its contents from being parsed.
        text = re.sub(r'`(.*?)`', self._store_code, text)

        # 2. Escape HTML-sensitive characters in the remaining text.
        text = html.escape(text, quote=False)

        # 3. Process images and links. Images must be processed before links.
        text = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img alt="\1" src="\2">', text)
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)

        # 4. Process strong and emphasis.
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)

        # 5. Restore inline code from placeholders.
        for i, code_html in enumerate(self._code_placeholders):
            text = text.replace(f"__CODE_PLACEHOLDER_{i}__", code_html)

        return text

    def _parse_fenced_code(self, lines, i):
        start_line = lines[i]
        fence = start_line.strip()[:3]
        i += 1
        code_lines = []
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith(fence):
                i += 1
                break
            code_lines.append(line)
            i += 1
        content = html.escape('\n'.join(code_lines))
        return f'<pre><code>{content}\n</code></pre>', i

    def _parse_indented_code(self, lines, i):
        code_lines = []
        while i < len(lines):
            line = lines[i]
            if line.strip() == '':
                code_lines.append('')
                i += 1
                continue
            if line.startswith(' ' * 4):
                code_lines.append(line[4:])
                i += 1
            elif line.startswith('\t'):
                code_lines.append(line[1:])
                i += 1
            else:
                break
        
        while code_lines and not code_lines[0].strip(): code_lines.pop(0)
        while code_lines and not code_lines[-1].strip(): code_lines.pop()

        content = html.escape('\n'.join(code_lines))
        return f'<pre><code>{content}\n</code></pre>', i

    def _parse_blockquote(self, lines, i):
        quote_lines = []
        while i < len(lines) and lines[i].startswith('>'):
            line = lines[i][1:]
            if line.startswith(' '):
                line = line[1:]
            quote_lines.append(line)
            i += 1
        
        inner_md = '\n'.join(quote_lines)
        # Create a new instance to parse blockquote content recursively
        md_instance = Markdown()
        inner_html = md_instance.convert(inner_md)
        return f'<blockquote>\n{inner_html}\n</blockquote>', i

    def _parse_list(self, lines, i):
        list_items_text = []
        list_type = 'ul'
        if re.match(r'^\s*\d+\.\s+', lines[i]):
            list_type = 'ol'

        while i < len(lines):
            line = lines[i]
            match = re.match(r'^\s*([*\-+]|\d+\.)\s+(.*)', line)
            if match:
                current_item_lines = [match.group(2)]
                i += 1
                while i < len(lines) and (lines[i].startswith(' ' * 2) or not lines[i].strip()):
                    if not lines[i].strip():
                        if i + 1 < len(lines) and lines[i+1].startswith(' ' * 2):
                             current_item_lines.append('')
                             i += 1
                        else:
                            break
                    else:
                        current_item_lines.append(lines[i].strip())
                        i += 1
                list_items_text.append('\n'.join(current_item_lines))
            else:
                break
        
        html_items = []
        for item_text in list_items_text:
            # Each list item's content is parsed for inlines.
            # A more advanced parser would handle nested blocks here.
            content = self._parse_inlines(item_text)
            html_items.append(f'<li>{content}</li>')

        return f'<{list_type}>\n' + '\n'.join(html_items) + f'\n</{list_type}>', i

    def _parse_paragraph(self, lines, i):
        para_lines = [lines[i]]
        i += 1
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                break
            if re.match(r'^(#{1,6}\s|>\s*|```|~~~|(\s*([*\-+]|\d+\.)\s))', line) or \
               line.startswith(' ' * 4) or line.startswith('\t'):
                break
            para_lines.append(line)
            i += 1
        
        content = self._parse_inlines(' '.join(l.strip() for l in para_lines))
        return f'<p>{content}</p>', i

    def convert(self, text):
        """Converts a Markdown string to HTML."""
        if not isinstance(text, str):
            return ""

        self.reset()
        
        lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        output_blocks = []
        i = 0
        
        while i < len(lines):
            line = lines[i]

            if not line.strip():
                i += 1
                continue

            if line.strip().startswith(('```', '~~~')):
                block, i = self._parse_fenced_code(lines, i)
                output_blocks.append(block)
                continue

            match = re.match(r'^(#{1,6})\s+(.*?)(\s+#*)?$', line)
            if match:
                level = len(match.group(1))
                content = self._parse_inlines(match.group(2).strip())
                output_blocks.append(f'<h{level}>{content}</h{level}>')
                i += 1
                continue

            if line.startswith('>'):
                block, i = self._parse_blockquote(lines, i)
                output_blocks.append(block)
                continue

            if re.match(r'^\s*([*\-+]|\d+\.)\s+', line):
                block, i = self._parse_list(lines, i)
                output_blocks.append(block)
                continue

            if line.startswith(' ' * 4) or line.startswith('\t'):
                block, i = self._parse_indented_code(lines, i)
                output_blocks.append(block)
                continue

            block, i = self._parse_paragraph(lines, i)
            output_blocks.append(block)

        return '\n'.join(output_blocks)


def markdown(text, **kwargs):
    """
    Converts a Markdown string to HTML.
    This is a shortcut function for the Markdown class.
    """
    md = Markdown(**kwargs)
    return md.convert(text)


def markdownFromFile(**kwargs):
    """
    Reads a Markdown file and converts it to HTML.
    """
    input_file = kwargs.get('input', None)
    output_file = kwargs.get('output', None)
    encoding = kwargs.get('encoding', 'utf-8')

    if not input_file:
        raise ValueError("markdownFromFile requires an 'input' keyword argument.")

    with open(input_file, 'r', encoding=encoding) as f:
        text = f.read()

    html_output = markdown(text, **kwargs)

    if output_file:
        with open(output_file, 'w', encoding=encoding) as f:
            f.write(html_output)
        return ""
    else:
        return html_output