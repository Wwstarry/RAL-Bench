from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence


@dataclass
class Args:
    """
    Rendering options container compatible with the subset used by tests.
    """

    width: int = 50
    stacked: bool = False
    different_scale: bool = False
    no_labels: bool = False
    format: str = "{:.2f}"
    suffix: str = ""
    vertical: bool = False
    histogram: bool = False
    no_values: bool = False
    color: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    title: Optional[str] = None

    def __init__(
        self,
        width: int = 50,
        stacked: bool = False,
        different_scale: bool = False,
        no_labels: bool = False,
        format: str = "{:.2f}",
        suffix: str = "",
        vertical: bool = False,
        histogram: bool = False,
        no_values: bool = False,
        color=None,
        labels=None,
        title: Optional[str] = None,
    ):
        self.width = int(width) if width is not None else 50
        if self.width < 1:
            self.width = 1

        self.stacked = bool(stacked)
        self.different_scale = bool(different_scale)
        self.no_labels = bool(no_labels)
        self.format = format if format is not None else "{:.2f}"
        self.suffix = suffix if suffix is not None else ""
        self.vertical = bool(vertical)
        self.histogram = bool(histogram)
        self.no_values = bool(no_values)

        # Accept None, empty list, or string "None" etc.
        if color in (None, "", [], (), "None", "none", False):
            self.color = None
        else:
            self.color = list(color) if isinstance(color, (list, tuple)) else [str(color)]

        self.labels = list(labels) if labels is not None else None
        self.title = title