from .text import Text

class Column:
    def __init__(self, header="", style=None, justify="left", width=None):
        self.header = header
        self.style = style or {}
        self.justify = justify
        self.width = width  # Optional fixed width

class Row:
    def __init__(self, *cells):
        self.cells = cells

class Table:
    def __init__(self, *columns, show_header=True, show_lines=False, padding=(0,1), border_style=None):
        self.columns = list(columns)
        self.rows = []
        self.show_header = show_header
        self.show_lines = show_lines
        self.padding = padding  # (top_bottom, left_right)
        self.border_style = border_style or {}

    def add_column(self, header="", style=None, justify="left", width=None):
        col = Column(header, style, justify, width)
        self.columns.append(col)

    def add_row(self, *cells):
        self.rows.append(Row(*cells))

    def _measure_column_widths(self):
        widths = []
        for col_i, col in enumerate(self.columns):
            max_width = 0
            # Header width
            header_text = str(col.header)
            max_width = max(max_width, len(header_text))
            # Rows width
            for row in self.rows:
                if col_i < len(row.cells):
                    cell = row.cells[col_i]
                    cell_text = str(cell)
                    max_width = max(max_width, len(cell_text))
            if col.width is not None:
                max_width = max(max_width, col.width)
            widths.append(max_width)
        return widths

    def __str__(self):
        return self.render()

    def render(self):
        # Render the table as a string with borders and padding
        widths = self._measure_column_widths()
        pad_tb, pad_lr = self.padding

        # Build horizontal border lines
        def hline(left, mid, right, fill):
            line = left
            for i, w in enumerate(widths):
                line += fill * (w + pad_lr * 2)
                if i < len(widths) - 1:
                    line += mid
            line += right
            return line

        top_line = hline("┌", "┬", "┐", "─")
        header_sep = hline("├", "┼", "┤", "─")
        bottom_line = hline("└", "┴", "┘", "─")

        lines = [top_line]

        # Header
        if self.show_header:
            header_cells = []
            for i, col in enumerate(self.columns):
                content = str(col.header)
                content = content.ljust(widths[i]) if col.justify == "left" else \
                          content.rjust(widths[i]) if col.justify == "right" else \
                          content.center(widths[i])
                padded = " " * pad_lr + content + " " * pad_lr
                header_cells.append(padded)
            header_line = "│" + "│".join(header_cells) + "│"
            lines.append(header_line)
            lines.append(header_sep)

        # Rows
        for row_i, row in enumerate(self.rows):
            row_cells = []
            for i, col in enumerate(self.columns):
                cell = row.cells[i] if i < len(row.cells) else ""
                content = str(cell)
                content = content.ljust(widths[i]) if col.justify == "left" else \
                          content.rjust(widths[i]) if col.justify == "right" else \
                          content.center(widths[i])
                padded = " " * pad_lr + content + " " * pad_lr
                row_cells.append(padded)
            row_line = "│" + "│".join(row_cells) + "│"
            lines.append(row_line)
            if self.show_lines and row_i < len(self.rows) - 1:
                lines.append(header_sep)

        lines.append(bottom_line)
        return "\n".join(lines)