"""
Shared runtime state for the stub sqlmap-like tool.

Exposes:
- cmdLineOptions: parsed command-line options (argparse namespace)
- conf: configuration container (attribute-accessible dict)
- kb: knowledge base container (attribute-accessible dict)
"""

from typing import Any


class AttribDict(dict):
    """
    Minimal attribute-accessible dict.
    """
    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError as ex:
            raise AttributeError(item) from ex

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def __delattr__(self, item: str) -> None:
        try:
            del self[item]
        except KeyError as ex:
            raise AttributeError(item) from ex


# Global runtime containers
cmdLineOptions = None  # will be set by lib.parse.cmdline.cmdLineParser
conf = AttribDict()
kb = AttribDict()