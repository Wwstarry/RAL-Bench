from dataclasses import dataclass, field
from typing import List, Optional, Union


ColorSpec = Union[int, str]  # allow either ANSI numeric codes or color names


@dataclass
class Args:
    """
    Encapsulates rendering options.

    width: maximum width of bars (number of characters)
    stacked: render stacked bars when True, else grouped/standard bars
    different_scale: use per-series scale rather than a global scale
    no_labels: do not print labels on the left
    format: numeric format spec; supports either format spec (e.g. ".2f")
            or full format string (e.g. "{:.2f}")
    suffix: string appended to formatted numbers
    vertical: vertical rendering mode (not implemented; reserved)
    histogram: histogram rendering mode (not implemented; reserved)
    no_values: do not print numeric values
    color: list of color specs applied per series (ANSI names or codes)
    labels: generic flag used by some callers; kept for compatibility
    title: optional chart title printed at top
    """

    width: int = 50
    stacked: bool = False
    different_scale: bool = False
    no_labels: bool = False
    format: Optional[str] = None
    suffix: str = ""
    vertical: bool = False
    histogram: bool = False
    no_values: bool = False
    color: Optional[List[ColorSpec]] = field(default_factory=list)
    labels: bool = True
    title: Optional[str] = None