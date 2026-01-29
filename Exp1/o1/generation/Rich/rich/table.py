from .text import Text
from .theme import Theme
from .console import parse_color_markup, strip_color_markup


class Column:
    """
    Represents a single column definition in a Table.
    """

    def __init__(self, header: str, style: str = None, width: int = None):
        self.header = header
        self.style = style
        self.width = width

    def __repr__(self):
        return f"Column({self.header!r}, style={self.style!r}, width={self.width!r})"


class Row:
    """
    Represents a single row of data in a Table.
    """

    def __init__(self, *cells):
        self.cells = list(cells)

    def __repr__(self):
        return f"Row({self.cells!r})"


class Table:
    """
    A minimal Table class with ASCII borders.
    """

    def __init__(self, title=None, show_header=True, show_border=True):
        self.title = title
        self.columns = []
        self.rows = []
        self.show_header = show_header
        self.show_border = show_border

    def add_column(self, header, style=None, width=None):
        column = Column(header, style=style, width=width)
        self.columns.append(column)

    def add_row(self, *cells):
        row = Row(*cells)
        self.rows.append(row)

    def __rich_console__(self, console):
        """
        Generate lines for console rendering.
        """
        # gather widths
        final_widths = []
        for i, col in enumerate(self.columns):
            max_content_width = len(strip_color_markup(col.header)) if self.show_header else 0
            for row in self.rows:
                if i < len(row.cells):
                    cell_text = strip_color_markup(str(row.cells[i]))
                    if len(cell_text) > max_content_width:
                        max_content_width = len(cell_text)
            if col.width is not None and col.width > max_content_width:
                max_content_width = col.width
            final_widths.append(max_content_width)

        lines = []
        # Title
        if self.title:
            lines.append(self.title)

        # Header
        if self.show_header:
            if self.show_border:
                top_border = "+"
                separator = "+"
                for w in final_widths:
                    top_border += "-" * (w + 2) + "+"
                lines.append(top_border)
            # Row of headers
            row_line = []
            for i, col in enumerate(self.columns):
                text_header = col.header
                padded = text_header + " " * (final_widths[i] - len(strip_color_markup(text_header)))
                if self.show_border:
                    row_line.append(f"| {padded} ")
                else:
                    row_line.append(padded)
            if self.show_border:
                row_line.append("|")
            lines.append("".join(row_line))

            if self.show_border:
                separator = "+"
                for w in final_widths:
                    separator += "-" * (w + 2) + "+"
                lines.append(separator)

        # Rows
        for row in self.rows:
            row_line = []
            for i, col in enumerate(self.columns):
                cell = row.cells[i] if i < len(row.cells) else ""
                cell_str = str(cell)
                # pad
                raw_cell_len = len(strip_color_markup(cell_str))
                pad_size = final_widths[i] - raw_cell_len
                padded = cell_str + (" " * pad_size)
                if self.show_border:
                    row_line.append(f"| {padded} ")
                else:
                    row_line.append(padded)
            if self.show_border and row_line:
                row_line.append("|")
            lines.append("".join(row_line))

        if self.show_border and self.columns:
            bottom_border = "+"
            for w in final_widths:
                bottom_border += "-" * (w + 2) + "+"
            lines.append(bottom_border)

        # parse color markup for lines
        rendered_lines = [parse_color_markup(line, console.theme) for line in lines]
        return rendered_lines