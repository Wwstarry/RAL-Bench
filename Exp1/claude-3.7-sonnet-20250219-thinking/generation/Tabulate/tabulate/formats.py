"""
Table format definitions.
"""

def simple_separated_format(separator):
    """Create a simple table format with separator between columns."""
    return {
        "lineabove": None,
        "linebelowheader": None,
        "linebetweenrows": None,
        "linebelow": None,
        "headerrow": simple_separated_row(separator),
        "datarow": simple_separated_row(separator),
        "padding": 1,
        "with_header_hide": None,
    }


def simple_separated_row(separator):
    """Create a simple row format with separator between columns."""
    return lambda row, _: separator.join(row)


# Table format definitions
_table_formats = {
    "plain": {
        "lineabove": None,
        "linebelowheader": None,
        "linebetweenrows": None,
        "linebelow": None,
        "headerrow": simple_separated_row("  "),
        "datarow": simple_separated_row("  "),
        "padding": 0,
        "with_header_hide": None,
    },
    "simple": {
        "lineabove": None,
        "linebelowheader": ["-", "-", "+", "-"],
        "linebetweenrows": None,
        "linebelow": None,
        "headerrow": simple_separated_row("  "),
        "datarow": simple_separated_row("  "),
        "padding": 1,
        "with_header_hide": None,
    },
    "grid": {
        "lineabove": ["+", "-", "+", "-"],
        "linebelowheader": ["+", "=", "+", "="],
        "linebetweenrows": ["+", "-", "+", "-"],
        "linebelow": ["+", "-", "+", "-"],
        "headerrow": lambda row, widths: "|" + "|".join(row) + "|",
        "datarow": lambda row, widths: "|" + "|".join(row) + "|",
        "padding": 1,
        "with_header_hide": None,
    },
    "fancy_grid": {
        "lineabove": ["╒", "═", "╤", "═"],
        "linebelowheader": ["╞", "═", "╪", "═"],
        "linebetweenrows": ["├", "─", "┼", "─"],
        "linebelow": ["╘", "═", "╧", "═"],
        "headerrow": lambda row, widths: "│" + "│".join(row) + "│",
        "datarow": lambda row, widths: "│" + "│".join(row) + "│",
        "padding": 1,
        "with_header_hide": None,
    },
    "pipe": {
        "lineabove": None,
        "linebelowheader": ["|", "-", "|", "-"],
        "linebetweenrows": None,
        "linebelow": None,
        "headerrow": lambda row, widths: "|" + "|".join(row) + "|",
        "datarow": lambda row, widths: "|" + "|".join(row) + "|",
        "padding": 1,
        "with_header_hide": None,
    },
    "orgtbl": {
        "lineabove": None,
        "linebelowheader": ["-", "-", "+", "-"],
        "linebetweenrows": None,
        "linebelow": None,
        "headerrow": lambda row, widths: "|" + "|".join(row) + "|",
        "datarow": lambda row, widths: "|" + "|".join(row) + "|",
        "padding": 1,
        "with_header_hide": None,
    },
    "rst": {
        "lineabove": ["=", "=", " ", "="],
        "linebelowheader": ["=", "=", " ", "="],
        "linebetweenrows": None,
        "linebelow": ["=", "=", " ", "="],
        "headerrow": simple_separated_row("  "),
        "datarow": simple_separated_row("  "),
        "padding": 0,
        "with_header_hide": ["lineabove"],
    },
    "mediawiki": {
        "lineabove": ["{| class=\"wikitable\" style=\"text-align: left;\"", "", "", ""],
        "linebelowheader": ["|-", "", "", ""],
        "linebetweenrows": ["|-", "", "", ""],
        "linebelow": ["|}", "", "", ""],
        "headerrow": lambda row, widths: "!" + "!!".join(row),
        "datarow": lambda row, widths: "|" + "||".join(row),
        "padding": 1,
        "with_header_hide": None,
    },
    "html": {
        "lineabove": ["<table>", "", "", ""],
        "linebelowheader": ["</thead><tbody>", "", "", ""],
        "linebetweenrows": None,
        "linebelow": ["</tbody></table>", "", "", ""],
        "headerrow": lambda row, widths: "<thead><tr><th>" + "</th><th>".join(row) + "</th></tr>",
        "datarow": lambda row, widths: "<tr><td>" + "</td><td>".join(row) + "</td></tr>",
        "padding": 0,
        "with_header_hide": None,
    },
    "latex": {
        "lineabove": ["\\begin{tabular}{", "l", "|", "l"},
        "linebelowheader": ["\\hline", "", "", ""],
        "linebetweenrows": None,
        "linebelow": ["\\end{tabular}", "", "", ""],
        "headerrow": lambda row, widths: " & ".join(row) + " \\\\",
        "datarow": lambda row, widths: " & ".join(row) + " \\\\",
        "padding": 1,
        "with_header_hide": None,
    },
    "latex_raw": {
        "lineabove": ["\\begin{tabular}{", "l", "|", "l"},
        "linebelowheader": ["\\hline", "", "", ""],
        "linebetweenrows": None,
        "linebelow": ["\\end{tabular}", "", "", ""],
        "headerrow": lambda row, widths: " & ".join(row) + " \\\\",
        "datarow": lambda row, widths: " & ".join(row) + " \\\\",
        "padding": 1,
        "with_header_hide": None,
    },
    "latex_booktabs": {
        "lineabove": ["\\begin{tabular}{", "l", "", "l"},
        "linebelowheader": ["\\midrule", "", "", ""],
        "linebetweenrows": None,
        "linebelow": ["\\bottomrule\n\\end{tabular}", "", "", ""],
        "headerrow": lambda row, widths: " & ".join(row) + " \\\\\n\\toprule",
        "datarow": lambda row, widths: " & ".join(row) + " \\\\",
        "padding": 1,
        "with_header_hide": None,
    },
    "tsv": simple_separated_format("\t"),
    "csv": simple_separated_format(","),
}