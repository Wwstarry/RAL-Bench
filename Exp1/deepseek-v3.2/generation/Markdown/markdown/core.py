"""
Core Markdown processor.
"""

import re
import codecs
from typing import Optional, Dict, Any, List, Tuple, Union

class Markdown:
    """Convert Markdown to HTML."""
    
    def __init__(self, **kwargs):
        """Initialize the Markdown processor."""
        self.reset()
        
    def reset(self):
        """Reset the processor's internal state."""
        self.html = []
        self._in_code_block = False
        self._in_blockquote = False
        self._list_stack = []
        
    def convert(self, text: str) -> str:
        """Convert Markdown text to HTML."""
        self.reset()
        lines = text.splitlines(keepends=True)
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
                
            # Check for code block
            if line.startswith('    ') or line.startswith('\t'):
                self._handle_code_block(lines, i)
                # Skip processed lines
                i = self._skip_code_block(lines, i)
                continue
                
            # Check for fenced code block
            if line.strip().startswith('```'):
                self._handle_fenced_code_block(lines, i)
                i = self._skip_fenced_code_block(lines, i)
                continue
                
            # Check for heading
            if line.lstrip().startswith('#'):
                self._handle_heading(line)
                i += 1
                continue
                
            # Check for blockquote
            if line.lstrip().startswith('>'):
                self._handle_blockquote(line)
                i += 1
                continue
                
            # Check for list items
            list_match = self._match_list_item(line)
            if list_match:
                self._handle_list_item(line, list_match)
                i += 1
                continue
                
            # Handle paragraph
            self._handle_paragraph(lines, i)
            i = self._skip_paragraph(lines, i)
            
        # Close any open lists
        while self._list_stack:
            self.html.append('</{}>'.format(self._list_stack.pop()))
            
        return ''.join(self.html)
    
    def _handle_code_block(self, lines: List[str], start: int) -> None:
        """Handle indented code block."""
        self.html.append('<pre><code>')
        i = start
        while i < len(lines) and (lines[i].startswith('    ') or lines[i].startswith('\t')):
            # Remove indentation (4 spaces or 1 tab)
            line = lines[i]
            if line.startswith('    '):
                line = line[4:]
            elif line.startswith('\t'):
                line = line[1:]
            # Escape HTML special characters
            line = self._escape_html(line)
            self.html.append(line)
            i += 1
        self.html.append('</code></pre>\n')
        
    def _skip_code_block(self, lines: List[str], start: int) -> int:
        """Skip over code block lines."""
        i = start
        while i < len(lines) and (lines[i].startswith('    ') or lines[i].startswith('\t')):
            i += 1
        return i
        
    def _handle_fenced_code_block(self, lines: List[str], start: int) -> None:
        """Handle fenced code block."""
        self.html.append('<pre><code>')
        i = start + 1  # Skip opening fence
        while i < len(lines) and not lines[i].strip().startswith('```'):
            # Escape HTML special characters
            line = self._escape_html(lines[i])
            self.html.append(line)
            i += 1
        self.html.append('</code></pre>\n')
        
    def _skip_fenced_code_block(self, lines: List[str], start: int) -> int:
        """Skip over fenced code block lines."""
        i = start + 1
        while i < len(lines) and not lines[i].strip().startswith('```'):
            i += 1
        return i + 1  # Skip closing fence
        
    def _handle_heading(self, line: str) -> None:
        """Handle ATX-style heading."""
        line = line.lstrip()
        level = 0
        while level < len(line) and line[level] == '#':
            level += 1
            
        if level > 6:
            level = 6
            
        content = line[level:].strip()
        content = self._process_inline(content)
        self.html.append('<h{}>{}</h{}>\n'.format(level, content, level))
        
    def _handle_blockquote(self, line: str) -> None:
        """Handle blockquote."""
        content = line.lstrip()[1:].strip()  # Remove '>'
        content = self._process_inline(content)
        self.html.append('<blockquote><p>{}</p></blockquote>\n'.format(content))
        
    def _match_list_item(self, line: str) -> Optional[Tuple[str, str]]:
        """Match list item patterns."""
        line = line.lstrip()
        
        # Unordered list
        if line.startswith(('- ', '+ ', '* ')):
            return ('ul', line[2:].strip())
            
        # Ordered list
        match = re.match(r'^(\d+)\.\s+(.*)', line)
        if match:
            return ('ol', match.group(2))
            
        return None
        
    def _handle_list_item(self, line: str, match: Tuple[str, str]) -> None:
        """Handle list item."""
        list_type, content = match
        content = self._process_inline(content)
        
        # Check if we need to start a new list
        if not self._list_stack or self._list_stack[-1] != list_type:
            self.html.append('<{}>'.format(list_type))
            self._list_stack.append(list_type)
            
        self.html.append('<li>{}</li>'.format(content))
        
    def _handle_paragraph(self, lines: List[str], start: int) -> None:
        """Handle paragraph."""
        paragraph_lines = []
        i = start
        
        while i < len(lines) and lines[i].strip():
            # Skip list items, headings, etc.
            if (self._match_list_item(lines[i]) or 
                lines[i].lstrip().startswith('#') or
                lines[i].lstrip().startswith('>') or
                lines[i].startswith('    ') or
                lines[i].startswith('\t') or
                lines[i].strip().startswith('```')):
                break
                
            paragraph_lines.append(lines[i].rstrip())
            i += 1
            
        if paragraph_lines:
            content = ' '.join(paragraph_lines)
            content = self._process_inline(content)
            self.html.append('<p>{}</p>\n'.format(content))
            
    def _skip_paragraph(self, lines: List[str], start: int) -> int:
        """Skip over paragraph lines."""
        i = start
        while i < len(lines) and lines[i].strip():
            # Skip list items, headings, etc.
            if (self._match_list_item(lines[i]) or 
                lines[i].lstrip().startswith('#') or
                lines[i].lstrip().startswith('>') or
                lines[i].startswith('    ') or
                lines[i].startswith('\t') or
                lines[i].strip().startswith('```')):
                break
            i += 1
        return i
        
    def _process_inline(self, text: str) -> str:
        """Process inline Markdown syntax."""
        # Escape HTML special characters first
        text = self._escape_html(text)
        
        # Handle code spans
        text = self._process_code_spans(text)
        
        # Handle emphasis and strong emphasis
        text = self._process_emphasis(text)
        
        # Handle links and images
        text = self._process_links(text)
        text = self._process_images(text)
        
        return text
        
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#39;'))
                    
    def _process_code_spans(self, text: str) -> str:
        """Process inline code spans."""
        # Find backtick pairs
        pattern = r'`([^`]+)`'
        
        def replace_code(match):
            code = match.group(1)
            # Don't escape HTML inside code spans
            return '<code>{}</code>'.format(code)
            
        return re.sub(pattern, replace_code, text)
        
    def _process_emphasis(self, text: str) -> str:
        """Process emphasis and strong emphasis."""
        # Handle strong emphasis first (** or __)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
        
        # Handle emphasis (* or _)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
        
        return text
        
    def _process_links(self, text: str) -> str:
        """Process links."""
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        def replace_link(match):
            link_text = match.group(1)
            url = match.group(2)
            return '<a href="{}">{}</a>'.format(url, link_text)
            
        return re.sub(pattern, replace_link, text)
        
    def _process_images(self, text: str) -> str:
        """Process images."""
        pattern = r'!\[([^\]]+)\]\(([^)]+)\)'
        
        def replace_image(match):
            alt_text = match.group(1)
            url = match.group(2)
            return '<img src="{}" alt="{}">'.format(url, alt_text)
            
        return re.sub(pattern, replace_image, text)


def markdown(text: str, **kwargs) -> str:
    """
    Convert Markdown text to HTML.
    
    Args:
        text: Markdown text to convert
        **kwargs: Additional options (ignored in this implementation)
        
    Returns:
        HTML string
    """
    md = Markdown(**kwargs)
    return md.convert(text)


def markdownFromFile(**kwargs) -> Optional[str]:
    """
    Convert Markdown from a file to HTML.
    
    Supported kwargs:
        input: Input filename
        output: Output filename (optional)
        encoding: File encoding (default: 'utf-8')
        
    Returns:
        HTML string if output is not specified, None otherwise
    """
    input_file = kwargs.get('input')
    output_file = kwargs.get('output')
    encoding = kwargs.get('encoding', 'utf-8')
    
    if not input_file:
        raise ValueError("Input file must be specified")
        
    # Read input file
    with codecs.open(input_file, 'r', encoding=encoding) as f:
        text = f.read()
        
    # Convert to HTML
    html = markdown(text, **kwargs)
    
    # Write to output file if specified
    if output_file:
        with codecs.open(output_file, 'w', encoding=encoding) as f:
            f.write(html)
        return None
        
    return html