"""
Core Markdown processor
"""

import re
import codecs
from typing import Optional, Dict, Any, List, Tuple, Union
import html

class Markdown:
    """Convert Markdown to HTML."""
    
    def __init__(self, **kwargs):
        """Initialize the Markdown processor."""
        self.reset()
        
    def reset(self):
        """Reset the processor state."""
        self._blocks: List[str] = []
        self._current_block: List[str] = []
        self._in_code_block = False
        self._in_blockquote = False
        self._list_stack: List[str] = []
        
    def convert(self, text: str) -> str:
        """Convert Markdown text to HTML."""
        self.reset()
        return self._process(text)
    
    def _process(self, text: str) -> str:
        """Main processing method."""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split into lines and process blocks
        lines = text.split('\n')
        html_blocks = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Check for code blocks (fenced with ``` or ~~~)
            if re.match(r'^```|^~~~', line):
                code_block = []
                i += 1
                while i < len(lines) and not re.match(r'^```|^~~~', lines[i]):
                    code_block.append(lines[i])
                    i += 1
                i += 1  # Skip closing fence
                html_blocks.append(f'<pre><code>{html.escape("\n".join(code_block))}</code></pre>')
                continue
            
            # Check for ATX headings (#, ##, etc.)
            heading_match = re.match(r'^(#{1,6})\s+(.*)', line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2).strip()
                html_blocks.append(f'<h{level}>{self._process_inline(content)}</h{level}>')
                i += 1
                continue
            
            # Check for blockquotes
            if line.startswith('>'):
                blockquote_lines = []
                while i < len(lines) and lines[i].startswith('>'):
                    blockquote_lines.append(lines[i][1:].strip())
                    i += 1
                content = self._process('\n'.join(blockquote_lines))
                html_blocks.append(f'<blockquote>{content}</blockquote>')
                continue
            
            # Check for unordered list items
            list_match = re.match(r'^(\s*)[-+*]\s+(.*)', line)
            if list_match:
                indent = len(list_match.group(1))
                content = list_match.group(2)
                list_items = []
                
                # Collect all items at this indentation level
                while i < len(lines) and re.match(r'^(\s*)[-+*]\s+', lines[i]):
                    current_match = re.match(r'^(\s*)[-+*]\s+(.*)', lines[i])
                    if len(current_match.group(1)) == indent:
                        list_items.append(self._process_inline(current_match.group(2)))
                        i += 1
                    else:
                        break
                
                html_blocks.append(f'<ul>\n' + '\n'.join(f'<li>{item}</li>' for item in list_items) + '\n</ul>')
                continue
            
            # Check for ordered list items
            ordered_match = re.match(r'^(\s*)\d+\.\s+(.*)', line)
            if ordered_match:
                indent = len(ordered_match.group(1))
                content = ordered_match.group(2)
                list_items = []
                
                # Collect all items at this indentation level
                while i < len(lines) and re.match(r'^(\s*)\d+\.\s+', lines[i]):
                    current_match = re.match(r'^(\s*)\d+\.\s+(.*)', lines[i])
                    if len(current_match.group(1)) == indent:
                        list_items.append(self._process_inline(current_match.group(2)))
                        i += 1
                    else:
                        break
                
                html_blocks.append(f'<ol>\n' + '\n'.join(f'<li>{item}</li>' for item in list_items) + '\n</ol>')
                continue
            
            # Check for code blocks (indented with 4 spaces or tab)
            if re.match(r'^ {4,}|\t', line):
                code_lines = []
                while i < len(lines) and (re.match(r'^ {4,}|\t', lines[i]) or not lines[i].strip()):
                    # Remove up to 4 spaces or 1 tab from start
                    if lines[i].startswith('    '):
                        code_lines.append(lines[i][4:])
                    elif lines[i].startswith('\t'):
                        code_lines.append(lines[i][1:])
                    else:
                        code_lines.append(lines[i])
                    i += 1
                # Remove trailing empty lines
                while code_lines and not code_lines[-1].strip():
                    code_lines.pop()
                html_blocks.append(f'<pre><code>{html.escape("\n".join(code_lines))}</code></pre>')
                continue
            
            # Regular paragraph
            paragraph_lines = []
            while i < len(lines) and lines[i].strip():
                paragraph_lines.append(lines[i])
                i += 1
            paragraph_text = ' '.join(paragraph_lines)
            html_blocks.append(f'<p>{self._process_inline(paragraph_text)}</p>')
        
        return '\n'.join(html_blocks)
    
    def _process_inline(self, text: str) -> str:
        """Process inline Markdown syntax."""
        # Escape HTML special characters first
        text = html.escape(text)
        
        # Process code spans (backticks)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # Process emphasis and strong emphasis
        # First handle strong (** or __)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
        
        # Then handle emphasis (* or _)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
        
        # Process links [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        
        # Process images ![alt](url)
        text = re.sub(r'!\[([^\]]+)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
        
        # Unescape code spans (they shouldn't have HTML entities)
        def unescape_code(match):
            return f'<code>{html.unescape(match.group(1))}</code>'
        
        text = re.sub(r'<code>([^<]+)</code>', unescape_code, text)
        
        return text


def markdown(text: str, **kwargs) -> str:
    """Convert Markdown text to HTML.
    
    Args:
        text: Markdown text to convert
        **kwargs: Additional options (ignored in this implementation)
        
    Returns:
        HTML string
    """
    processor = Markdown(**kwargs)
    return processor.convert(text)


def markdownFromFile(**kwargs) -> Optional[str]:
    """Convert Markdown file to HTML.
    
    Args:
        **kwargs: Must include 'input' or 'input_file' for input file path
                  and optionally 'output' or 'output_file' for output file path.
        
    Returns:
        HTML string if output file not specified, None otherwise
    """
    input_file = kwargs.get('input') or kwargs.get('input_file')
    output_file = kwargs.get('output') or kwargs.get('output_file')
    
    if not input_file:
        raise ValueError("Input file must be specified")
    
    # Read input file
    with codecs.open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Convert to HTML
    html_output = markdown(text, **kwargs)
    
    # Write to output file if specified
    if output_file:
        with codecs.open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_output)
        return None
    
    return html_output