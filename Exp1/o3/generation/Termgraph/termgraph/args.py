"""
A very small helper that mimics the :class:`argparse.Namespace` object used by
``termgraph``.  The goal is *not* to re-implement the full CLI but to expose a
plain-old Python objekt that the charts can inspect for options that the tests
expect.
"""
from __future__ import annotations


class Args:
    """
    Container object used by the charts.  The constructor accepts keyword
    arguments only so that callers can be explicit.  Every attribute has a sane
    default value that resembles the original ``termgraph`` defaults.
    """

    def __init__(
        self,
        *,
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
        title: str | None = None,
    ):
        # Rendering options ---------------------------------------------------
        self.width = int(width)
        self.stacked = bool(stacked)
        self.different_scale = bool(different_scale)
        self.no_labels = bool(no_labels)
        self.format = str(format or "{:.2f}")
        self.suffix = str(suffix)
        self.vertical = bool(vertical)          # *not* implemented, kept for API
        self.histogram = bool(histogram)        # *not* implemented, kept for API
        self.no_values = bool(no_values)
        # Cosmetic / advanced options -----------------------------------------
        # The reference implementation may provide complex colour handling – we
        # stick to monochrome but keep the attribute around so tests that only
        # *set* it continue to work.
        self.color = color
        self.labels = labels
        self.title = title

    # The reference repository sometimes treats the object like a mutable
    # namespace.  Therefore we do *not* make it frozen or provide __slots__.

    # A convenience representation – it helps debugging but is not required.
    def __repr__(self) -> str:  # pragma: no cover
        attrs = (
            "width",
            "stacked",
            "different_scale",
            "no_labels",
            "format",
            "suffix",
            "vertical",
            "histogram",
            "no_values",
            "color",
            "labels",
            "title",
        )
        parts = ", ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"{self.__class__.__name__}({parts})"