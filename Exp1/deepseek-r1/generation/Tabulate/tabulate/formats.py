class TableFormat:
    def __init__(self, lineabove, linebelowheader, linebetweenrows, linebelow,
                 headerrow, datarow, padding, with_header_hide):
        self.lineabove = lineabove
        self.linebelowheader = linebelowheader
        self.linebetweenrows = linebetweenrows
        self.linebelow = linebelow
        self.headerrow = headerrow
        self.datarow = datarow
        self.padding = padding
        self.with_header_hide = with_header_hide

PRESET_FORMATS = {
    "plain": TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=lambda headers, widths: [h.ljust(w) for h, w in zip(headers, widths)],
        datarow=lambda row, widths: [str(c).ljust(w) for c, w in zip(row, widths)],
        padding=1,
        with_header_hide=["lineabove", "linebelowheader", "linebelow"]
    ),
    "grid": TableFormat(
        lineabove=lambda widths: "+" + "+".join('-' * (w + 2) for w in widths) + "+",
        linebelowheader=lambda widths: "+" + "+".join('=' * (w + 2) for w in widths) + "+",
        linebetweenrows=lambda widths: "+" + "+".join('-' * (w + 2) for w in widths) + "+",
        linebelow=lambda widths: "+" + "+".join('-' * (w + 2) for w in widths) + "+",
        headerrow=lambda headers, widths: "| " + " | ".join(h.center(w) for h, w in zip(headers, widths)) + " |",
        datarow=lambda row, widths: "| " + " | ".join(str(c).ljust(w) for c, w in zip(row, widths)) + " |",
        padding=1,
        with_header_hide=[]
    ),
    "pipe": TableFormat(
        lineabove=lambda widths: "| " + " | ".join('-' * w for w in widths) + " |",
        linebelowheader=lambda widths: "| " + " | ".join('-' * w for w in widths) + " |",
        linebetweenrows=None,
        linebelow=lambda widths: "| " + " | ".join('-' * w for w in widths) + " |",
        headerrow=lambda headers, widths: "| " + " | ".join(h for h in headers) + " |",
        datarow=lambda row, widths: "| " + " | ".join(str(c) for c in row) + " |",
        padding=1,
        with_header_hide=["lineabove", "linebelowheader", "linebelow"]
    ),
    "html": TableFormat(
        lineabove=lambda widths: "<table>",
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=lambda widths: "</table>",
        headerrow=lambda headers, widths: "<tr><th>" + "</th><th>".join(headers) + "</th></tr>",
        datarow=lambda row, widths: "<tr><td>" + "</td><td>".join(str(c) for c in row) + "</td></tr>",
        padding=0,
        with_header_hide=["lineabove", "linebelow"]
    ),
    "tsv": TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=lambda headers, widths: "\t".join(headers),
        datarow=lambda row, widths: "\t".join(str(c) for c in row),
        padding=0,
        with_header_hide=[]
    ),
    "csv": TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=lambda headers, widths: ",".join(headers),
        datarow=lambda row, widths: ",".join(str(c) for c in row),
        padding=0,
        with_header_hide=[]
    )
}

def simple_separated_format(separator):
    return TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=lambda headers, widths: separator.join(headers),
        datarow=lambda row, widths: separator.join(str(c) for c in row),
        padding=0,
        with_header_hide=[]
    )