from typing import Dict, Any

_TABLE_FORMATS: Dict[str, Dict[str, Any]] = {
    "plain": {
        "edge": ("", ""),
        "sep": " ",
        "padding": 1,
    },
    "simple": {
        "edge": ("", ""),
        "sep": " ",
        "padding": 1,
        "header": {"edge": ("", ""), "sep": " "},
        "top": {"edge": ("-", "-"), "sep": "-"},
        "bottom": {"edge": ("", ""), "sep": " "},
    },
    "grid": {
        "edge": ("|", "|"),
        "sep": "|",
        "padding": 1,
        "header": {"edge": ("|", "|"), "sep": "|"},
        "top": {"edge": ("+", "+"), "sep": "+", "sep_char": "-"},
        "mid": {"edge": ("+", "+"), "sep": "+", "sep_char": "-"},
        "bottom": {"edge": ("+", "+"), "sep": "+", "sep_char": "-"},
    },
    "pipe": {
        "edge": ("|", "|"),
        "sep": "|",
        "padding": 1,
        "header": {"edge": ("|", "|"), "sep": "|"},
        "top": {"edge": ("|", "|"), "sep": "|", "sep_char": "-"},
    },
    "html": {
        "edge": ("<tr><td>", "</td></tr>"),
        "sep": "</td><td>",
        "padding": 0,
    },
    "tsv": {
        "edge": ("", ""),
        "sep": "\t",
        "padding": 0,
    },
    "csv": {
        "edge": ("", ""),
        "sep": ",",
        "padding": 0,
    },
}

_FORMAT_ALIASES: Dict[str, str] = {
    "psql": "pipe",
    "presto": "pipe",
    "pretty": "grid",
    "fancy_grid": "grid",
    "github": "grid",
    "mediawiki": "grid",
    "moinmoin": "grid",
    "jira": "grid",
    "textile": "grid",
    "html5": "html",
    "latex": "grid",
    "latex_raw": "grid",
    "latex_booktabs": "grid",
    "orgtbl": "pipe",
    "rst": "simple",
}