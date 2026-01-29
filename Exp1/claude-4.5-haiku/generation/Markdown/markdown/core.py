"""
Core Markdown conversion functionality.
"""

import re
import os
from typing import Optional, List, Dict, Any


class Markdown:
    """
    Main Markdown class for converting Markdown text to HTML.
    """

    def __init__(self, **kwargs):
        """
        Initialize a Markdown instance.
        
        Args:
            extensions: List of extension names to use
            extension_configs: Dict of extension configurations
            output_format: Output format (default: 'xhtml')
            tab_length: Number of spaces per tab (default: 4)
        """
        self.extensions = kwargs.get('extensions', [])
        self.extension_configs = kwargs.get('extension_configs', {})
        self.output_format = kwargs.get('output_format', 'xhtml')
        self.tab_length = kwargs.get('tab_length', 4)
        self.reset()

    def reset(self):
        """Reset the Markdown instance for processing a new document."""
        self.lines = []
        self.blocks = []

    def convert(self, text: str) -> str:
        """
        Convert Markdown text to HTML.
        
        Args:
            text: Markdown text to convert
            
        Returns:
            HTML string
        """
        self.reset()
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Parse and convert
        html = self._parse(text)
        return html

    def _parse(self, text: str) -> str:
        """Parse Markdown text and return HTML."""
        lines = text.split('\n')
        blocks = self._split_blocks(lines)
        html_parts = []
        
        for block in blocks:
            html_parts.append(self._process_block(block))
        
        return '\n'.join(html_parts)

    def _split_blocks(self, lines: List[str]) -> List[List[str]]:
        """Split lines into logical blocks."""
        blocks = []
        current_block = []
        in_code_block = False
        fence_char = None
        
        for line in lines:
            # Check for fenced code blocks
            if line.strip().startswith('```') or line.strip().startswith('~~~'):
                fence = line.strip()[:3]
                if not in_code_block:
                    if current_block and current_block[-1].strip():
                        blocks.append(current_block)
                        current_block = []
                    in_code_block = True
                    fence_char = fence
                    current_block.append(line)
                elif fence == fence_char:
                    current_block.append(line)
                    blocks.append(current_block)
                    current_block = []
                    in_code_block = False
                    fence_char = None
                else:
                    current_block.append(line)
            elif in_code_block:
                current_block.append(line)
            elif not line.strip():
                # Blank line - end current block if non-empty
                if current_block and any(l.strip() for l in current_block):
                    blocks.append(current_block)
                    current_block = []
            else:
                current_block.append(line)
        
        if current_block and any(l.strip() for l in current_block):
            blocks.append(current_block)
        
        return blocks

    def _process_block(self, block: List[str]) -> str:
        """Process a single block and return HTML."""
        if not block:
            return ''
        
        text = '\n'.join(block)
        stripped = text.strip()
        
        if not stripped:
            return ''
        
        # Check for fenced code block
        if stripped.startswith('```') or stripped.startswith('~~~'):
            return self._process_fenced_code(block)
        
        # Check for indented code block
        if block[0].startswith('    ') or block[0].startswith('\t'):
            return self._process_indented_code(block)
        
        # Check for heading
        if stripped.startswith('#'):
            return self._process_heading(stripped)
        
        # Check for blockquote
        if stripped.startswith('>'):
            return self._process_blockquote(block)
        
        # Check for unordered list
        if self._is_unordered_list(block):
            return self._process_unordered_list(block)
        
        # Check for ordered list
        if self._is_ordered_list(block):
            return self._process_ordered_list(block)
        
        # Default to paragraph
        return self._process_paragraph(text)

    def _process_heading(self, text: str) -> str:
        """Process ATX-style heading."""
        match = re.match(r'^(#{1,6})\s+(.+?)(?:\s+#+)?$', text)
        if match:
            level = len(match.group(1))
            content = match.group(2).strip()
            content = self._process_inline(content)
            return f'<h{level}>{content}</h{level}>'
        return ''

    def _process_paragraph(self, text: str) -> str:
        """Process paragraph block."""
        text = text.strip()
        if not text:
            return ''
        content = self._process_inline(text)
        return f'<p>{content}</p>'

    def _process_blockquote(self, block: List[str]) -> str:
        """Process blockquote."""
        lines = []
        for line in block:
            if line.startswith('>'):
                lines.append(line[1:].lstrip())
            else:
                lines.append(line)
        
        content = '\n'.join(lines).strip()
        # Recursively process blockquote content
        inner_blocks = self._split_blocks(content.split('\n'))
        inner_html = '\n'.join(self._process_block(b) for b in inner_blocks)
        return f'<blockquote>\n{inner_html}\n</blockquote>'

    def _process_fenced_code(self, block: List[str]) -> str:
        """Process fenced code block."""
        lines = block[1:-1]  # Skip fence markers
        code = '\n'.join(lines)
        code = self._escape_html(code)
        return f'<pre><code>{code}</code></pre>'

    def _process_indented_code(self, block: List[str]) -> str:
        """Process indented code block."""
        lines = []
        for line in block:
            if line.startswith('    '):
                lines.append(line[4:])
            elif line.startswith('\t'):
                lines.append(line[1:])
            else:
                lines.append(line)
        
        code = '\n'.join(lines).rstrip()
        code = self._escape_html(code)
        return f'<pre><code>{code}</code></pre>'

    def _is_unordered_list(self, block: List[str]) -> bool:
        """Check if block is an unordered list."""
        for line in block:
            stripped = line.lstrip()
            if stripped and not re.match(r'^[-+*]\s+', stripped):
                return False
        return any(re.match(r'^[-+*]\s+', line.lstrip()) for line in block)

    def _is_ordered_list(self, block: List[str]) -> bool:
        """Check if block is an ordered list."""
        for line in block:
            stripped = line.lstrip()
            if stripped and not re.match(r'^\d+\.\s+', stripped):
                return False
        return any(re.match(r'^\d+\.\s+', line.lstrip()) for line in block)

    def _process_unordered_list(self, block: List[str]) -> str:
        """Process unordered list."""
        items = []
        for line in block:
            match = re.match(r'^([-+*])\s+(.+)$', line.lstrip())
            if match:
                content = match.group(2)
                content = self._process_inline(content)
                items.append(f'<li>{content}</li>')
        
        if items:
            return '<ul>\n' + '\n'.join(items) + '\n</ul>'
        return ''

    def _process_ordered_list(self, block: List[str]) -> str:
        """Process ordered list."""
        items = []
        for line in block:
            match = re.match(r'^\d+\.\s+(.+)$', line.lstrip())
            if match:
                content = match.group(1)
                content = self._process_inline(content)
                items.append(f'<li>{content}</li>')
        
        if items:
            return '<ol>\n' + '\n'.join(items) + '\n</ol>'
        return ''

    def _process_inline(self, text: str) -> str:
        """Process inline elements."""
        # Process in order: code, links/images, emphasis
        text = self._process_inline_code(text)
        text = self._process_links_and_images(text)
        text = self._process_emphasis(text)
        text = self._escape_html_outside_code(text)
        return text

    def _process_inline_code(self, text: str) -> str:
        """Process inline code (backticks)."""
        def replace_code(match):
            code = match.group(1)
            code = self._escape_html(code)
            return f'<code>{code}</code>'
        
        # Match backticks, handling escaped backticks
        text = re.sub(r'`([^`]+)`', replace_code, text)
        return text

    def _process_links_and_images(self, text: str) -> str:
        """Process links and images."""
        # Images: ![alt](url)
        text = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            lambda m: f'<img alt="{self._escape_html(m.group(1))}" src="{self._escape_html(m.group(2))}" />',
            text
        )
        
        # Links: [text](url)
        text = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            lambda m: f'<a href="{self._escape_html(m.group(2))}">{self._process_inline(m.group(1))}</a>',
            text
        )
        
        return text

    def _process_emphasis(self, text: str) -> str:
        """Process emphasis and strong emphasis."""
        # Strong emphasis: **text** or __text__
        text = re.sub(
            r'\*\*([^\*]+)\*\*',
            lambda m: f'<strong>{self._process_inline(m.group(1))}</strong>',
            text
        )
        text = re.sub(
            r'__([^_]+)__',
            lambda m: f'<strong>{self._process_inline(m.group(1))}</strong>',
            text
        )
        
        # Emphasis: *text* or _text_
        text = re.sub(
            r'\*([^\*]+)\*',
            lambda m: f'<em>{self._process_inline(m.group(1))}</em>',
            text
        )
        text = re.sub(
            r'_([^_]+)_',
            lambda m: f'<em>{self._process_inline(m.group(1))}</em>',
            text
        )
        
        return text

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        return text

    def _escape_html_outside_code(self, text: str) -> str:
        """Escape HTML in text, but preserve it in code tags."""
        # Split by code tags to avoid escaping inside them
        parts = re.split(r'(<code>.*?</code>)', text, flags=re.DOTALL)
        result = []
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Not inside code tag
                part = self._escape_html(part)
            result.append(part)
        return ''.join(result)


def markdown(text: str, **kwargs) -> str:
    """
    Convert Markdown text to HTML.
    
    Args:
        text: Markdown text to convert
        **kwargs: Additional options (extensions, etc.)
        
    Returns:
        HTML string
    """
    md = Markdown(**kwargs)
    return md.convert(text)


def markdownFromFile(**kwargs) -> str:
    """
    Convert Markdown from a file to HTML.
    
    Args:
        input: File path to read from
        output: File path to write to (optional)
        encoding: File encoding (default: 'utf-8')
        **kwargs: Additional options passed to markdown()
        
    Returns:
        HTML string (or None if output file is specified)
    """
    input_file = kwargs.get('input')
    output_file = kwargs.get('output')
    encoding = kwargs.get('encoding', 'utf-8')
    
    if not input_file:
        raise ValueError("input parameter is required")
    
    # Read input file
    with open(input_file, 'r', encoding=encoding) as f:
        text = f.read()
    
    # Convert
    html = markdown(text, **{k: v for k, v in kwargs.items() 
                             if k not in ('input', 'output', 'encoding')})
    
    # Write output if specified
    if output_file:
        with open(output_file, 'w', encoding=encoding) as f:
            f.write(html)
        return None
    
    return html