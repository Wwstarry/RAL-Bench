"""
Core markdown parser implementation.
"""

import re
import sys
import html
from textwrap import dedent
from io import StringIO

def markdown(text, **kwargs):
    """
    Convert markdown text to HTML.
    
    Args:
        text: Unicode string containing Markdown text
        **kwargs: Optional arguments to configure the parser
    
    Returns:
        Unicode string containing HTML
    """
    md = Markdown(**kwargs)
    return md.convert(text)


def markdownFromFile(**kwargs):
    """
    Convert markdown text from a file to HTML.
    
    Args:
        input: File object or string path to read from
        output: File object or string path to write to
        encoding: Encoding for I/O (default: 'utf-8')
        **kwargs: Same as the markdown() function
    """
    encoding = kwargs.pop('encoding', 'utf-8')
    
    # Handle input
    input_file = kwargs.pop('input', None)
    if input_file is None:
        input_file = sys.stdin
        input_text = input_file.read()
    elif isinstance(input_file, str):
        with open(input_file, 'r', encoding=encoding) as f:
            input_text = f.read()
    else:
        input_text = input_file.read()
    
    # Convert to HTML
    html_output = markdown(input_text, **kwargs)
    
    # Handle output
    output_file = kwargs.pop('output', None)
    if output_file is None:
        output_file = sys.stdout
        output_file.write(html_output)
    elif isinstance(output_file, str):
        with open(output_file, 'w', encoding=encoding) as f:
            f.write(html_output)
    else:
        output_file.write(html_output)


class Markdown:
    """
    Markdown parser class.
    """
    
    def __init__(self, **kwargs):
        self.reset()
        
        # Initialize configuration
        self.output_format = kwargs.get('output_format', 'xhtml')
        self.tab_length = kwargs.get('tab_length', 4)
        self.extensions = kwargs.get('extensions', [])

    def reset(self):
        """
        Resets all variables to allow converting a new document.
        """
        self.html_blocks = []
        
    def convert(self, text):
        """
        Convert markdown text to HTML.
        """
        if not text:
            return ""
        
        # Reset the parser state
        self.reset()
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Process document
        html = self._process_document(text)
        
        # Return the final HTML
        return html
        
    def _process_document(self, text):
        """Process an entire markdown document."""
        # Split document into blocks
        blocks = self._split_blocks(text)
        
        # Process each block
        for i, block in enumerate(blocks):
            html_block = self._process_block(block)
            self.html_blocks.append(html_block)
        
        # Join blocks with newlines
        return ''.join(self.html_blocks)
    
    def _split_blocks(self, text):
        """Split text into blocks separated by blank lines."""
        return re.split(r'\n\s*\n', text)
    
    def _process_block(self, block):
        """Process a single block of markdown."""
        block = block.strip()
        
        # ATX Headings (#, ##, etc.)
        if block.startswith('#'):
            match = re.match(r'^(#{1,6})\s+(.*?)(?:\s+#*)?$', block)
            if match:
                level = len(match.group(1))
                content = self._process_inline(match.group(2))
                return f"<h{level}>{content}</h{level}>\n"
        
        # Fenced code blocks
        if block.startswith('```') or block.startswith('~~~'):
            return self._process_fenced_code(block)
            
        # Indented code blocks
        if block.startswith('    ') or block.startswith('\t'):
            return self._process_indented_code(block)
            
        # Blockquotes
        if block.startswith('>'):
            return self._process_blockquote(block)
            
        # Unordered lists
        if re.match(r'^[*+-]\s', block):
            return self._process_list(block, ordered=False)
            
        # Ordered lists
        if re.match(r'^\d+\.\s', block):
            return self._process_list(block, ordered=True)
            
        # Default to paragraph
        return f"<p>{self._process_inline(block)}</p>\n"
    
    def _process_fenced_code(self, block):
        """Process fenced code blocks."""
        lines = block.split('\n')
        fence_char = lines[0][0]
        fence_length = len(lines[0].rstrip().lstrip(fence_char))
        
        # Find the closing fence
        content_lines = []
        for i, line in enumerate(lines[1:], 1):
            if line.startswith(fence_char * fence_length) and set(line.strip()) <= set(fence_char):
                break
            content_lines.append(line)
        
        code = '\n'.join(content_lines)
        return f"<pre><code>{html.escape(code)}</code></pre>\n"
    
    def _process_indented_code(self, block):
        """Process indented code blocks."""
        lines = block.split('\n')
        # Remove indent (4 spaces or 1 tab)
        code_lines = []
        for line in lines:
            if line.startswith('    '):
                code_lines.append(line[4:])
            elif line.startswith('\t'):
                code_lines.append(line[1:])
            else:
                code_lines.append(line)
        
        code = '\n'.join(code_lines)
        return f"<pre><code>{html.escape(code)}</code></pre>\n"
    
    def _process_blockquote(self, block):
        """Process blockquote blocks."""
        lines = block.split('\n')
        content_lines = []
        
        for line in lines:
            if line.startswith('> '):
                content_lines.append(line[2:])
            elif line.startswith('>'):
                content_lines.append(line[1:])
            else:
                content_lines.append(line)
        
        content = '\n'.join(content_lines)
        inner_html = self._process_document(content).strip()
        return f"<blockquote>\n{inner_html}\n</blockquote>\n"
    
    def _process_list(self, block, ordered=False):
        """Process ordered and unordered lists."""
        lines = block.split('\n')
        tag = 'ol' if ordered else 'ul'
        
        # Process list items
        html_output = f"<{tag}>\n"
        
        current_item = []
        for i, line in enumerate(lines):
            if (i == 0) or (ordered and re.match(r'^\d+\.\s', line)) or (not ordered and re.match(r'^[*+-]\s', line)):
                if current_item:  # Process the previous item
                    item_text = '\n'.join(current_item)
                    html_output += f"<li>{self._process_inline(item_text)}</li>\n"
                    current_item = []
                
                # Start new item, removing the marker
                if ordered:
                    content = re.sub(r'^\d+\.\s', '', line)
                else:
                    content = re.sub(r'^[*+-]\s', '', line)
                current_item.append(content)
            else:
                current_item.append(line)
        
        # Process the last item
        if current_item:
            item_text = '\n'.join(current_item)
            html_output += f"<li>{self._process_inline(item_text)}</li>\n"
        
        html_output += f"</{tag}>\n"
        return html_output
    
    def _process_inline(self, text):
        """Process inline markdown elements."""
        if not text:
            return ""
            
        # Escape HTML entities except for those in code spans
        code_spans = {}
        
        # Extract code spans first
        def _extract_code_spans(match):
            code = match.group(1)
            placeholder = f"CODE_SPAN_{len(code_spans)}"
            code_spans[placeholder] = code
            return f"`{placeholder}`"
            
        text = re.sub(r'`(.*?)`', _extract_code_spans, text)
        
        # Escape HTML in regular text
        text = html.escape(text)
        
        # Restore code spans with unescaped HTML
        def _restore_code_spans(match):
            placeholder = match.group(1)
            code = code_spans.get(placeholder, "")
            return f"<code>{html.escape(code)}</code>"
            
        text = re.sub(r'`(CODE_SPAN_\d+)`', _restore_code_spans, text)
        
        # Process links [text](url)
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        
        # Process images ![alt](url)
        text = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1">', text)
        
        # Process strong emphasis with **
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # Process strong emphasis with __
        text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
        
        # Process emphasis with *
        text = re.sub(r'\*(?!\*)(.*?)(?<!\*)\*', r'<em>\1</em>', text)
        
        # Process emphasis with _
        text = re.sub(r'_(?!_)(.*?)(?<!_)_', r'<em>\1</em>', text)
        
        return text