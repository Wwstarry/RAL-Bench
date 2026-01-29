from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class Args:
    width: int = 50
    stacked: bool = False
    different_scale: bool = False
    no_labels: bool = False
    format: str = "{:<5.2f}"
    suffix: str = ""
    vertical: bool = False
    histogram: bool = False
    no_values: bool = False
    color: Any = None
    labels: Optional[List[str]] = None
    title: Optional[str] = None

    def __init__(
        self,
        width: int = 50,
        stacked: bool = False,
        different_scale: bool = False,
        no_labels: bool = False,
        format: str = "{:<5.2f}",
        suffix: str = "",
        vertical: bool = False,
        histogram: bool = False,
        no_values: bool = False,
        color: Any = None,
        labels: Optional[List[str]] = None,
        title: Optional[str] = None,
    ):
        self.width = width
        self.stacked = stacked
        self.different_scale = different_scale
        self.no_labels = no_labels
        self.format = format
        self.suffix = suffix
        self.vertical = vertical
        self.histogram = histogram
        self.no_values = no_values
        self.color = color
        self.labels = labels
        self.title = title