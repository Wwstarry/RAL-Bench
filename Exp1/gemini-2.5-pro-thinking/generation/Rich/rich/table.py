import textwrap
from .console import _strip_ansi, Text, Segment

class Column:
    def __init__(self, header="", justify="left", width=None):
        self.header = header
        self.justify = justify
        self.width = width

class Row:
    pass

class Table:
    def __init__(self, *headers, title=None, box='ASCII', show_header=True, padding=(0, 1)):
        self.title = title
        self.columns = [Column(h) for h in headers]
        self.rows = []
        self.box_chars = {
            'ASCII': {'top_left': '+', 'top_right': '+', 'bottom_left': '+', 'bottom_right': '+',
                      'horizontal': '-', 'vertical': '|', 'intersection': '+', 'header_separator': '+'},
        }[box]
        self.show_header = show_header
        self.padding = padding

    def add_column(self, header="", **kwargs):
        self.columns.append(Column(header, **kwargs))

    def add_row(self, *items):
        self.rows.append(list(items))

    def _calculate_column_widths(self, max_width):
        num_cols = len(self.columns)
        if num_cols == 0:
            return []
        
        available_width = max_width - (num_cols + 1) - (num_cols * (self.padding[0] + self.padding[1]))
        
        base_width = available_width // num_cols
        remainder = available_width % num_cols
        
        widths = [base_width] * num_cols
        for i in range(remainder):
            widths[i] += 1
        return widths

    def __rich_console__(self, console, options):
        if not self.columns:
            return

        widths = self._calculate_column_widths(options.width)
        pad_left, pad_right = self.padding

        def render_border(left, sep, right, pad_char):
            parts = [pad_char * (w + pad_left + pad_right) for w in widths]
            return left + sep.join(parts) + right

        # Top border
        yield Segment(render_border(self.box_chars['top_left'], self.box_chars['intersection'], self.box_chars['top_right'], self.box_chars['horizontal']))

        # Header
        if self.show_header:
            header_cells = [[col.header] for col in self.columns]
            for line in self._render_row(header_cells, widths):
                yield line
            
            # Header separator
            yield Segment(render_border(self.box_chars['intersection'], self.box_chars['intersection'], self.box_chars['intersection'], self.box_chars['horizontal']))

        # Rows
        for i, row in enumerate(self.rows):
            row_cells = []
            for item in row:
                text = str(item) if not isinstance(item, Text) else str(item)
                text = _strip_ansi(text)
                row_cells.append(text.splitlines() or [""])
            
            for line in self._render_row(row_cells, widths):
                yield line
            
            if i < len(self.rows) - 1:
                 yield Segment(render_border(self.box_chars['intersection'], self.box_chars['intersection'], self.box_chars['intersection'], self.box_chars['horizontal']))


        # Bottom border
        yield Segment(render_border(self.box_chars['bottom_left'], self.box_chars['intersection'], self.box_chars['bottom_right'], self.box_chars['horizontal']))

    def _render_row(self, row_cells, widths):
        pad_left, pad_right = self.padding
        row_cell_lines = []
        max_lines = 0
        for i, cell_lines in enumerate(row_cells):
            col_width = widths[i]
            wrapped_lines = []
            for line in cell_lines:
                wrapped = textwrap.wrap(line, width=col_width) if col_width > 0 else [line]
                wrapped_lines.extend(wrapped or [""])
            row_cell_lines.append(wrapped_lines)
            max_lines = max(max_lines, len(wrapped_lines))

        for lines in row_cell_lines:
            lines.extend([""] * (max_lines - len(lines)))

        for line_num in range(max_lines):
            line_str = self.box_chars['vertical']
            for i, lines in enumerate(row_cell_lines):
                col = self.columns[i]
                width = widths[i]
                text = lines[line_num]
                
                if col.justify == 'right':
                    text = text.rjust(width)
                elif col.justify == 'center':
                    text = text.center(width)
                else: # left
                    text = text.ljust(width)
                
                line_str += ' ' * pad_left + text + ' ' * pad_right + self.box_chars['vertical']
            yield Segment(line_str)