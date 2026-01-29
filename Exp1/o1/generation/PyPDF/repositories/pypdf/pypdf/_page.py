"""
Implements the PageObject class for pypdf.
"""

class PageObject:
    """
    Represents a single PDF page.
    Provides rotate(angle), rotation, and placeholders for content.
    """

    def __init__(self, mediabox=None, contents=b"", rotation=0):
        """
        Initialize a page object with given media box, content stream, and rotation.
        mediabox: [xmin, ymin, xmax, ymax]
        contents: raw PDF content stream as bytes
        rotation: integer degrees
        """
        if mediabox is None:
            # Default to standard letter size
            self.mediabox = [0, 0, 612, 792]
        else:
            self.mediabox = list(mediabox)
        self.contents = contents
        self._rotation = rotation

    @property
    def rotation(self):
        """
        Returns the effective rotation in degrees.
        """
        return self._rotation

    def rotate(self, angle):
        """
        Rotates the page by the specified angle (in degrees).
        The angle must be a multiple of 90.
        """
        # Ensure angle is multiple of 90 in a naive manner
        # Adjust rotation accordingly
        if angle % 90 != 0:
            raise ValueError("Rotation angle must be a multiple of 90.")
        self._rotation = (self._rotation + angle) % 360