from typing import List, Optional, Union
from .text import Text
from .console import Console

class Column:
    def __init__(self, header: str, justify: str = "left", style: str = ""):
        self.header = Text.from_markup(header) if isinstance(header, str) else header
        self.justify = justify
        self.style = style
        self._cells: List[Text] = []

class Table:
    def __init__(self, title: str = None, show_header: bool = True, show_lines: bool = False):
        self.title = title
        self.show_header = show_header
        self.show_lines = show_lines
        self.columns: List[Column] = []
        self.rows: List[List[Text]] = []
        self.border_style = "white"

    def add_column(self, header: str = "", justify: str = "left", style: str = ""):
        col = Column(header, justify, style)
        self.columns.append(col)

    def add_row(self, *renderables: Union[str, Text]):
        row_data = []
        for item in renderables:
            if isinstance(item, str):
                row_data.append(Text.from_markup(item))
            elif isinstance(item, Text):
                row_data.append(item)
            else:
                row_data.append(Text(str(item)))
        self.rows.append(row_data)

    def __rich_console__(self, console: Console, options):
        # Calculate widths
        col_widths = [len(col.header) for col in self.columns]
        
        for row in self.rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(cell))
        
        # Box drawing characters
        box = {
            "top_left": "┌", "top": "─", "top_mid": "┬", "top_right": "┐",
            "mid_left": "├", "mid": "─", "mid_mid": "┼", "mid_right": "┤",
            "bot_left": "└", "bot": "─", "bot_mid": "┴", "bot_right": "┘",
            "vert": "│"
        }

        def render_sep(left, mid, cross, right):
            parts = [left]
            for i, w in enumerate(col_widths):
                parts.append(mid * (w + 2))
                if i < len(col_widths) - 1:
                    parts.append(cross)
            parts.append(right)
            return "".join(parts) + "\n"

        def render_row(cells, is_header=False):
            line = [box["vert"]]
            for i, (cell, width) in enumerate(zip(cells, col_widths)):
                content = cell.plain
                # Padding
                pad_len = width - len(content)
                # Simple justification logic
                if is_header:
                    # Headers usually centered or left, keeping simple here
                    txt = f" {content}" + (" " * pad_len) + " "
                else:
                    txt = f" {content}" + (" " * pad_len) + " "
                
                # Apply style if needed (simplified)
                if is_header:
                    line.append(f"\033[1m{txt}\033[0m")
                else:
                    line.append(txt)
                
                line.append(box["vert"])
            return "".join(line) + "\n"

        # Top Border
        yield render_sep(box["top_left"], box["top"], box["top_mid"], box["top_right"])

        # Header
        if self.show_header:
            headers = [col.header for col in self.columns]
            yield render_row(headers, is_header=True)
            yield render_sep(box["mid_left"], box["mid"], box["mid_mid"], box["mid_right"])

        # Rows
        for i, row in enumerate(self.rows):
            # Pad row if missing columns
            while len(row) < len(self.columns):
                row.append(Text(""))
            yield render_row(row)
            if self.show_lines and i < len(self.rows) - 1:
                yield render_sep(box["mid_left"], box["mid"], box["mid_mid"], box["mid_right"])

        # Bottom Border
        yield render_sep(box["bot_left"], box["bot"], box["bot_mid"], box["bot_right"])