# tabulate/formats.py

def simple_separated_format(separator="\t"):
    """
    Generate a simple separated table format function.
    """
    def format_table(rows, column_widths):
        return "\n".join(separator.join(row) for row in rows)
    return format_table

def plain_format(rows, column_widths):
    """
    Plain table format.
    """
    return "\n".join(" ".join(row) for row in rows)

def grid_format(rows, column_widths):
    """
    Grid table format.
    """
    horizontal_line = "+" + "+".join("-" * width for width in column_widths) + "+"
    formatted_rows = [horizontal_line]
    for row in rows:
        formatted_rows.append("|" + "|".join(row) + "|")
        formatted_rows.append(horizontal_line)
    return "\n".join(formatted_rows)

def pipe_format(rows, column_widths):
    """
    Pipe table format.
    """
    return "\n".join("| " + " | ".join(row) + " |" for row in rows)

def html_format(rows, column_widths):
    """
    HTML-like table format.
    """
    formatted_rows = ["<table>"]
    for row in rows:
        formatted_rows.append("  <tr>")
        for cell in row:
            formatted_rows.append(f"    <td>{cell}</td>")
        formatted_rows.append("  </tr>")
    formatted_rows.append("</table>")
    return "\n".join(formatted_rows)

PRESET_FORMATS = {
    "plain": plain_format,
    "grid": grid_format,
    "pipe": pipe_format,
    "html": html_format,
    "tsv": simple_separated_format("\t"),
    "csv": simple_separated_format(","),
}