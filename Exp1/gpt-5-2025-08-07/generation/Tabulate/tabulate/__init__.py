# Public API for the simplified tabulate-like library

from .core import tabulate, simple_separated_format
from .formats import AVAILABLE_FORMATS

__all__ = [
    "tabulate",
    "simple_separated_format",
    # expose common format names for discoverability
    "AVAILABLE_FORMATS",
]

# Common preset names mentioned in docs/tests
# (aliases for users/tests to check availability)
plain = "plain"
grid = "grid"
pipe = "pipe"
simple = "simple"
tsv = "tsv"
csv = "csv"
html = "html"