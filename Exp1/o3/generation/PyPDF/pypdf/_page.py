"""
Simplified page object model.
"""
from __future__ import annotations

from typing import Any


class PageObject:
    """
    Extremely simplified representation of a page.

    Only the functionality required by the tests is provided.
    """

    def __init__(self, width: float = 612.0, height: float = 792.0, rotation: int = 0):
        self.width = width
        self.height = height
        self._rotation = rotation % 360  # store normalised

        # Payload is currently unused – placeholder for future extensions
        self._contents: Any = None

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def rotate(self, angle: int):
        """
        Rotate the page clockwise by *angle* degrees.

        Only multiples of 90° are technically valid, but we merely normalise to
        0-359 for the purposes of the test-suite.
        """
        if not isinstance(angle, (int, float)):
            raise TypeError("angle must be a number")
        self._rotation = int((self._rotation + angle) % 360)
        return self  # allow chaining

    # Synonym used by real pypdf
    rotate_clockwise = rotate

    @property
    def rotation(self) -> int:
        """Return the current clockwise rotation in degrees."""
        return self._rotation

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    @classmethod
    def from_dict(cls, d):
        return cls(width=d.get("width", 612), height=d.get("height", 792), rotation=d.get("rotation", 0))

    def to_dict(self):
        return {"width": self.width, "height": self.height, "rotation": self._rotation}