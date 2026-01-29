from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Args:
    """
    Encapsulates rendering options expected by the tests.

    The reference project uses argparse; this object is a lightweight container.
    """

    width: int = 50
    stacked: bool = False
    different_scale: bool = False
    no_labels: bool = False
    format: str = "{:<5.2f}"
    suffix: str = ""
    vertical: bool = False
    histogram: bool = False
    no_values: bool = False
    color: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    title: Optional[str] = None

    def __post_init__(self):
        try:
            self.width = int(self.width)
        except Exception:
            self.width = 50
        if self.width < 1:
            self.width = 1

        # Normalize colors to list (or None)
        if self.color is not None and not isinstance(self.color, list):
            # Accept single string
            self.color = [str(self.color)]