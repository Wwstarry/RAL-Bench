"""
Table format definitions and utilities.
"""

# TableFormat namedtuple-like class
class TableFormat:
    def __init__(self, name, lineabove, linebelow, lineafter, linebetweenheader,
                 linebetweenrows, headerrow, datarow, padding, with_header_hide=None):
        self.name = name
        self.lineabove = lineabove
        self.linebelow = linebelow
        self.lineafter = lineafter
        self.linebetweenheader = linebetweenheader
        self.linebetweenrows = linebetweenrows
        self.headerrow = headerrow
        self.datarow = datarow
        self.padding = padding
        self.with_header_hide = with_header_hide or []


def simple_separated_format(separator):
    """Create a simple separated format with the given separator."""
    return TableFormat(
        name="custom",
        lineabove="",
        linebelow="",
        lineafter="",
        linebetweenheader="",
        linebetweenrows="",
        headerrow="{name}" + separator,
        datarow="{name}" + separator,
        padding=0,
    )


# Predefined formats
_FORMATS = {}


def _register_format(fmt):
    _FORMATS[fmt.name] = fmt
    return fmt


_register_format(TableFormat(
    name="plain",
    lineabove="",
    linebelow="",
    lineafter="",
    linebetweenheader="",
    linebetweenrows="",
    headerrow="{name}",
    datarow="{name}",
    padding=0,
))

_register_format(TableFormat(
    name="simple",
    lineabove="{above}",
    linebelow="{below}",
    lineafter="{below}",
    linebetweenheader="{below}",
    linebetweenrows="",
    headerrow="{name}",
    datarow="{name}",
    padding=0,
))

_register_format(TableFormat(
    name="grid",
    lineabove="+-{above}-+",
    linebelow="+-{below}-+",
    lineafter="+-{below}-+",
    linebetweenheader="+-{below}-+",
    linebetweenrows="",
    headerrow="| {name} |",
    datarow="| {name} |",
    padding=1,
))

_register_format(TableFormat(
    name="pipe",
    lineabove="",
    linebelow="",
    lineafter="",
    linebetweenheader="|{below}|",
    linebetweenrows="",
    headerrow="| {name} |",
    datarow="| {name} |",
    padding=1,
))

_register_format(TableFormat(
    name="orgtbl",
    lineabove="",
    linebelow="",
    lineafter="",
    linebetweenheader="|-{below}-|",
    linebetweenrows="",
    headerrow="| {name} |",
    datarow="| {name} |",
    padding=1,
))

_register_format(TableFormat(
    name="rst",
    lineabove="={above}=",
    linebelow="={below}=",
    lineafter="={below}=",
    linebetweenheader="={below}=",
    linebetweenrows="",
    headerrow="{name}",
    datarow="{name}",
    padding=1,
))

_register_format(TableFormat(
    name="mediawiki",
    lineabove="{|",
    linebelow="|}",
    lineafter="",
    linebetweenheader="",
    linebetweenrows="",
    headerrow="! {name}",
    datarow="| {name}",
    padding=1,
))

_register_format(TableFormat(
    name="html",
    lineabove="<table>",
    linebelow="</table>",
    lineafter="",
    linebetweenheader="",
    linebetweenrows="",
    headerrow="<tr><th>{name}</th></tr>",
    datarow="<tr><td>{name}</td></tr>",
    padding=0,
))

_register_format(TableFormat(
    name="latex",
    lineabove="\\begin{tabular}{cols}",
    linebelow="\\end{tabular}",
    lineafter="",
    linebetweenheader="\\hline",
    linebetweenrows="",
    headerrow="{name}",
    datarow="{name}",
    padding=1,
))

_register_format(TableFormat(
    name="latex_raw",
    lineabove="\\begin{tabular}{cols}",
    linebelow="\\end{tabular}",
    lineafter="",
    linebetweenheader="\\hline",
    linebetweenrows="",
    headerrow="{name}",
    datarow="{name}",
    padding=1,
))

_register_format(TableFormat(
    name="tsv",
    lineabove="",
    linebelow="",
    lineafter="",
    linebetweenheader="",
    linebetweenrows="",
    headerrow="{name}\t",
    datarow="{name}\t",
    padding=0,
))

_register_format(TableFormat(
    name="csv",
    lineabove="",
    linebelow="",
    lineafter="",
    linebetweenheader="",
    linebetweenrows="",
    headerrow="{name},",
    datarow="{name},",
    padding=0,
))

_register_format(TableFormat(
    name="jira",
    lineabove="",
    linebelow="",
    lineafter="",
    linebetweenheader="",
    linebetweenrows="",
    headerrow="|| {name} ||",
    datarow="| {name} |",
    padding=1,
))

_register_format(TableFormat(
    name="presto",
    lineabove="",
    linebelow="",
    lineafter="",
    linebetweenheader="|{below}|",
    linebetweenrows="",
    headerrow="| {name} |",
    datarow="| {name} |",
    padding=1,
))

_register_format(TableFormat(
    name="psql",
    lineabove="+-{above}-+",
    linebelow="+-{below}-+",
    lineafter="+-{below}-+",
    linebetweenheader="+-{below}-+",
    linebetweenrows="",
    headerrow="| {name} |",
    datarow="| {name} |",
    padding=1,
))

_register_format(TableFormat(
    name="youtrack",
    lineabove="",
    linebelow="",
    lineafter="",
    linebetweenheader="",
    linebetweenrows="",
    headerrow="|| {name} ||",
    datarow="| {name} |",
    padding=1,
))

_register_format(TableFormat(
    name="pretty",
    lineabove="+-{above}-+",
    linebelow="+-{below}-+",
    lineafter="+-{below}-+",
    linebetweenheader="+-{below}-+",
    linebetweenrows="",
    headerrow="| {name} |",
    datarow="| {name} |",
    padding=1,
))

_register_format(TableFormat(
    name="fancy_grid",
    lineabove="╒═{above}═╕",
    linebelow="╘═{below}═╛",
    lineafter="╘═{below}═╛",
    linebetweenheader="╞═{below}═╡",
    linebetweenrows="",
    headerrow="│ {name} │",
    datarow="│ {name} │",
    padding=1,
))

_register_format(TableFormat(
    name="mixed_outline",
    lineabove="+-{above}-+",
    linebelow="+-{below}-+",
    lineafter="+-{below}-+",
    linebetweenheader="+-{below}-+",
    linebetweenrows="",
    headerrow="| {name} |",
    datarow="| {name} |",
    padding=1,
))

_register_format(TableFormat(
    name="mixed_grid",
    lineabove="+-{above}-+",
    linebelow="+-{below}-+",
    lineafter="+-{below}-+",
    linebetweenheader="+-{below}-+",
    linebetweenrows="+-{below}-+",
    headerrow="| {name} |",
    datarow="| {name} |",
    padding=1,
))

_register_format(TableFormat(
    name="double_outline",
    lineabove="╔═{above}═╗",
    linebelow="╚═{below}═╝",
    lineafter="╚═{below}═╝",
    linebetweenheader="╠═{below}═╣",
    linebetweenrows="",
    headerrow="║ {name} ║",
    datarow="║ {name} ║",
    padding=1,
))


def get_named_table_format(name):
    """Get a table format by name."""
    if name not in _FORMATS:
        raise ValueError(f"Unknown table format: {name}")
    return _FORMATS[name]


def list_formats():
    """List all available table formats."""
    return sorted(_FORMATS.keys())