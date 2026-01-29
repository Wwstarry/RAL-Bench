def simple_separated_format(separator=" "):
    def fmt(rows, header, col_widths):
        lines = []
        if header:
            lines.append(separator.join(header))
        for row in rows:
            lines.append(separator.join(row))
        return "\n".join(lines)
    return fmt

def _plain_format(rows, header, col_widths):
    lines = []
    if header:
        lines.append(" ".join(header))
    for row in rows:
        lines.append(" ".join(row))
    return "\n".join(lines)

def _grid_format(rows, header, col_widths):
    # e.g.
    # +-----+-----+
    # | foo | bar |
    # +-----+-----+
    # | ... | ... |
    # +-----+-----+
    def border():
        return "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    def row_line(row):
        return "| " + " | ".join(row) + " |"
    lines = []
    lines.append(border())
    if header:
        lines.append(row_line(header))
        lines.append(border())
    for row in rows:
        lines.append(row_line(row))
        lines.append(border())
    return "\n".join(lines)

def _pipe_format(rows, header, col_widths):
    # e.g.
    # | foo | bar |
    # |------|-----|
    # | ... | ... |
    def sep_line():
        return "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
    def row_line(row):
        return "| " + " | ".join(row) + " |"
    lines = []
    if header:
        lines.append(row_line(header))
        lines.append(sep_line())
    for row in rows:
        lines.append(row_line(row))
    return "\n".join(lines)

def _html_format(rows, header, col_widths):
    lines = []
    lines.append("<table>")
    if header:
        lines.append("  <thead>")
        lines.append("    <tr>" + "".join(f"<th>{cell}</th>" for cell in header) + "</tr>")
        lines.append("  </thead>")
    lines.append("  <tbody>")
    for row in rows:
        lines.append("    <tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    lines.append("  </tbody>")
    lines.append("</table>")
    return "\n".join(lines)

def _tsv_format(rows, header, col_widths):
    lines = []
    if header:
        lines.append("\t".join(header))
    for row in rows:
        lines.append("\t".join(row))
    return "\n".join(lines)

def _csv_format(rows, header, col_widths):
    import csv
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    if header:
        writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().rstrip("\r\n")

TABLE_FORMATS = {
    "plain": _plain_format,
    "simple": simple_separated_format(" "),
    "grid": _grid_format,
    "pipe": _pipe_format,
    "html": _html_format,
    "tsv": _tsv_format,
    "csv": _csv_format,
}