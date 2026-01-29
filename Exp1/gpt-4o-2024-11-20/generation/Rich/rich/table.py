# rich/table.py

class Column:
    def __init__(self, header, width=None, align="left"):
        self.header = header
        self.width = width
        self.align = align

class Row:
    def __init__(self, cells):
        self.cells = cells

class Table:
    def __init__(self, columns=None, border=True, padding=1):
        self.columns = columns or []
        self.rows = []
        self.border = border
        self.padding = padding

    def add_column(self, header, width=None, align="left"):
        self.columns.append(Column(header, width, align))

    def add_row(self, *cells):
        self.rows.append(Row(cells))

    def render(self):
        # Calculate column widths
        column_widths = [
            max(len(str(row.cells[i])) for row in self.rows) if col.width is None else col.width
            for i, col in enumerate(self.columns)
        ]

        # Render header
        header = " | ".join(
            col.header.ljust(column_widths[i]) if col.align == "left" else col.header.rjust(column_widths[i])
            for i, col in enumerate(self.columns)
        )
        border_line = "-" * len(header) if self.border else ""

        # Render rows
        rows = []
        for row in self.rows:
            rows.append(
                " | ".join(
                    str(row.cells[i]).ljust(column_widths[i]) if self.columns[i].align == "left" else str(row.cells[i]).rjust(column_widths[i])
                    for i in range(len(self.columns))
                )
            )

        # Combine all parts
        output = []
        if self.border:
            output.append(border_line)
        output.append(header)
        if self.border:
            output.append(border_line)
        output.extend(rows)
        if self.border:
            output.append(border_line)

        return "\n".join(output)