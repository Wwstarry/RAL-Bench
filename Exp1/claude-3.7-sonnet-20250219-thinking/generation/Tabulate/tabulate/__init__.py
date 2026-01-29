"""
Pretty-print tabular data.
"""

from tabulate.core import tabulate
from tabulate.formats import simple_separated_format, _table_formats

__version__ = "0.8.9"
__all__ = ['tabulate', 'simple_separated_format']

# Export table formats
plain = _table_formats["plain"]
simple = _table_formats["simple"]
grid = _table_formats["grid"]
fancy_grid = _table_formats["fancy_grid"]
pipe = _table_formats["pipe"]
orgtbl = _table_formats["orgtbl"]
rst = _table_formats["rst"]
mediawiki = _table_formats["mediawiki"]
html = _table_formats["html"]
latex = _table_formats["latex"]
latex_raw = _table_formats["latex_raw"]
latex_booktabs = _table_formats["latex_booktabs"]
tsv = _table_formats["tsv"]
csv = _table_formats["csv"]

# Add formats to __all__
__all__.extend([
    "plain", "simple", "grid", "fancy_grid", "pipe", "orgtbl", "rst", 
    "mediawiki", "html", "latex", "latex_raw", "latex_booktabs", "tsv", "csv"
])