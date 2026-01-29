import re
import codecs
from typing import Optional, Dict, Any, List

class Markdown:
    """
    A Markdown converter class.
    """
    
    def __init__(self, **kwargs):
        self.reset()
        self.options = kwargs
    
    def reset(self):
        """Reset the instance state for processing a new document."""
        self.html = []
        self.in_blockquote = False
        self.in_list = False
        self.in_code_block = False
        self.in_paragraph = False
    
    def convert(self, text: str) -> str:
        """
        Convert markdown text to HTML.
        
        Args:
            text: Markdown text as a Unicode string
            
        Returns:
            HTML as a Unicode string
        """
        self.reset()
        lines = text.split('\n')
        self._parse_lines(lines)
        return ''.join(self.html)
    
    def _parse_lines(self, lines: List[str]):
        i = 0
        while i < len(lines):
            line = lines[i].rstrip('\r\n')
            
            # Handle code blocks first
            if self._is_code_block(line):
                i = self._parse_code_block(lines, i)
                continue
            
            # Handle blockquotes
            if line.startswith('>'):
                i = self._parse_blockquote(lines, i)
                continue
            
            # Handle headings
            heading_match = self._parse_heading(line)
            if heading_match:
                self._end_paragraph()
                level, content = heading_match
                self.html.append(f'<h{level}>{self._parse_inline(content)}</h{level}>\n')
                i += 1
                continue
            
            # Handle lists
            if self._is_list_item(line):
                i = self._parse_list(lines, i)
                continue
            
            # Handle horizontal rules
            if self._is_hr(line):
                self._end_paragraph()
                self.html.append('<hr />\n')
                i += 1
                continue
            
            # Handle empty lines (end paragraphs)
            if not line.strip():
                self._end_paragraph()
                i += 1
                continue
            
            # Handle regular paragraphs
            if not self.in_paragraph:
                self.html.append('<p>')
                self.in_paragraph = True
            else:
                self.html.append(' ')
            
            self.html.append(self._parse_inline(line))
            i += 1
        
        self._end_paragraph()
    
    def _is_code_block(self, line: str) -> bool:
        """Check if line starts a code block."""
        return line.startswith('    ') or line.startswith('\t')
    
    def _parse_code_block(self, lines: List[str], start_idx: int) -> int:
        """Parse a code block."""
        self._end_paragraph()
        self.html.append('<pre><code>')
        
        i = start_idx
        while i < len(lines):
            line = lines[i]
            if not self._is_code_block(line) and line.strip():
                break
            
            # Remove leading 4 spaces or 1 tab
            if line.startswith('    '):
                content = line[4:]
            elif line.startswith('\t'):
                content = line[1:]
            else:
                content = line
            
            if content:
                self.html.append(self._escape_html(content))
            self.html.append('\n')
            i += 1
        
        self.html.append('</code></pre>\n')
        return i
    
    def _parse_blockquote(self, lines: List[str], start_idx: int) -> int:
        """Parse a blockquote."""
        self._end_paragraph()
        self.html.append('<blockquote>\n')
        
        i = start_idx
        quote_lines = []
        
        while i < len(lines):
            line = lines[i]
            if line.startswith('>'):
                # Remove '> ' or '>'
                content = line[1:].lstrip()
                quote_lines.append(content)
                i += 1
            else:
                break
        
        # Parse the content of the blockquote
        temp_md = Markdown()
        quote_content = temp_md.convert('\n'.join(quote_lines))
        self.html.append(quote_content)
        self.html.append('</blockquote>\n')
        return i
    
    def _parse_heading(self, line: str) -> Optional[tuple]:
        """Parse ATX-style headings."""
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            content = match.group(2).rstrip('#').strip()
            return (level, content)
        return None
    
    def _is_list_item(self, line: str) -> bool:
        """Check if line is a list item."""
        return (re.match(r'^[\*\+\-]\s+', line) or 
                re.match(r'^\d+\.\s+', line))
    
    def _parse_list(self, lines: List[str], start_idx: int) -> int:
        """Parse a list."""
        self._end_paragraph()
        
        i = start_idx
        list_items = []
        current_item = []
        list_type = 'ul' if re.match(r'^[\*\+\-]\s+', lines[i]) else 'ol'
        
        while i < len(lines):
            line = lines[i]
            if self._is_list_item(line):
                if current_item:
                    list_items.append('\n'.join(current_item))
                    current_item = []
                
                # Remove list marker
                if re.match(r'^[\*\+\-]\s+', line):
                    content = re.sub(r'^[\*\+\-]\s+', '', line, count=1)
                else:
                    content = re.sub(r'^\d+\.\s+', '', line, count=1)
                current_item.append(content)
            elif line.strip() and (line.startswith(' ') or line.startswith('\t')):
                # Continuation line
                current_item.append(line.lstrip())
            elif not line.strip():
                # Empty line within list item
                current_item.append('')
            else:
                break
            i += 1
        
        if current_item:
            list_items.append('\n'.join(current_item))
        
        self.html.append(f'<{list_type}>\n')
        for item in list_items:
            temp_md = Markdown()
            item_html = temp_md.convert(item).strip()
            if item_html.startswith('<p>') and item_html.endswith('</p>'):
                item_html = item_html[3:-4]
            self.html.append(f'<li>{item_html}</li>\n')
        self.html.append(f'</{list_type}>\n')
        
        return i
    
    def _is_hr(self, line: str) -> bool:
        """Check if line is a horizontal rule."""
        return re.match(r'^[\*\-_]{3,}\s*$', line)
    
    def _end_paragraph(self):
        """End the current paragraph if one is open."""
        if self.in_paragraph:
            self.html.append('</p>\n')
            self.in_paragraph = False
    
    def _parse_inline(self, text: str) -> str:
        """Parse inline Markdown elements."""
        # Escape HTML special characters first
        text = self._escape_html(text)
        
        # Parse inline code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # Parse emphasis and strong emphasis
        text = self._parse_emphasis(text, '**', 'strong')
        text = self._parse_emphasis(text, '__', 'strong')
        text = self._parse_emphasis(text, '*', 'em')
        text = self._parse_emphasis(text, '_', 'em')
        
        # Parse links
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" />', text)
        text = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        
        return text
    
    def _parse_emphasis(self, text: str, marker: str, tag: str) -> str:
        """Parse emphasis markers."""
        # Simple approach - find pairs of markers
        parts = text.split(marker)
        result = []
        in_emphasis = False
        
        for i, part in enumerate(parts):
            if i % 2 == 0:
                result.append(part)
            else:
                result.append(f'<{tag}>{part}</{tag}>')
        
        return ''.join(result)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if self.in_code_block:
            return text
        
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text


def markdown(text: str, **kwargs) -> str:
    """
    Convert markdown text to HTML.
    
    Args:
        text: Markdown text as a Unicode string
        **kwargs: Additional options for the Markdown processor
        
    Returns:
        HTML as a Unicode string
    """
    md = Markdown(**kwargs)
    return md.convert(text)


def markdownFromFile(input: Optional[str] = None, output: Optional[str] = None, 
                    encoding: str = 'utf-8', **kwargs) -> Optional[str]:
    """
    Convert markdown file to HTML.
    
    Args:
        input: Input file path
        output: Output file path (optional)
        encoding: File encoding
        **kwargs: Additional options for the Markdown processor
        
    Returns:
        HTML as string if output is None, otherwise None
    """
    if input is None:
        raise ValueError("Input file path is required")
    
    with codecs.open(input, 'r', encoding=encoding) as f:
        text = f.read()
    
    html = markdown(text, **kwargs)
    
    if output:
        with codecs.open(output, 'w', encoding=encoding) as f:
            f.write(html)
        return None
    else:
        return html