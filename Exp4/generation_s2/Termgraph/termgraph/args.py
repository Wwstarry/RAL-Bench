from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass
class Args:
    """
    Options container resembling the core args used by termgraph.

    Only a subset is implemented, but attributes exist to match the reference
    API used in tests.
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
    color: Optional[str] = None
    labels: Optional[Sequence[str]] = None
    title: Optional[str] = None

    # Some termgraph variants support these; keep for compatibility.
    start: int = 0
    end: int = -1

    def __post_init__(self) -> None:
        try:
            self.width = int(self.width)
        except Exception:
            self.width = 50
        if self.width <= 0:
            self.width = 50
        if self.format is None:
            self.format = "{:<5.2f}"
        if self.suffix is None:
            self.suffix = ""