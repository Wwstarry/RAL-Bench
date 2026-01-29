"""
PDF Page implementation.
"""

from typing import Any, Optional, Dict


class PageObject:
    """
    Represents a single page in a PDF document.
    """

    def __init__(self, page_dict: Dict[str, Any], reader: Optional[Any] = None):
        """
        Initialize a PageObject.

        Args:
            page_dict: The page dictionary.
            reader: The PdfReader instance (if any).
        """
        self._page_dict = page_dict
        self._reader = reader
        self._rotation = 0

    def rotate(self, angle: int) -> "PageObject":
        """
        Rotate the page by the given angle.

        Args:
            angle: The rotation angle in degrees (0, 90, 180, or 270).

        Returns:
            Self for method chaining.
        """
        # Normalize angle to 0-360 range
        angle = angle % 360
        self._rotation = angle
        return self

    @property
    def rotation(self) -> int:
        """Get the effective rotation angle in degrees."""
        return self._rotation

    def get_object(self) -> Dict[str, Any]:
        """Get the underlying page dictionary."""
        return self._page_dict