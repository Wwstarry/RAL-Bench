from .core import tabulate, simple_separated_format

def plain(tabular_data, headers=None, colalign=None):
    return tabulate(tabular_data, headers=headers, tablefmt="plain", colalign=colalign)

def grid(tabular_data, headers=None, colalign=None):
    return tabulate(tabular_data, headers=headers, tablefmt="grid", colalign=colalign)

def pipe(tabular_data, headers=None, colalign=None):
    return tabulate(tabular_data, headers=headers, tablefmt="pipe", colalign=colalign)

def html(tabular_data, headers=None, colalign=None):
    return tabulate(tabular_data, headers=headers, tablefmt="html", colalign=colalign)

def tsv(tabular_data, headers=None, colalign=None):
    return tabulate(tabular_data, headers=headers, tablefmt="tsv", colalign=colalign)

def csv(tabular_data, headers=None, colalign=None):
    return tabulate(tabular_data, headers=headers, tablefmt="csv", colalign=colalign)

_table_formats = {
    "plain": plain,
    "grid": grid,
    "pipe": pipe,
    "html": html,
    "tsv": tsv,
    "csv": csv,
}

FORMATS = list(_table_formats.keys())