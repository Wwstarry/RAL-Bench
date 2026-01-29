"""
PDF Page object implementation.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pypdf.reader import PdfReader


class PageObject:
    """
    Represents a single page in a PDF document.
    """
    
    def __init__(self, reader: Optional['PdfReader'], page_dict: Dict[bytes, Any], obj_num: int = 0):
        """
        Initialize a PageObject.
        
        Args:
            reader: The PdfReader this page belongs to
            page_dict: The page dictionary
            obj_num: The object number
        """
        self._reader = reader
        self._page_dict = page_dict
        self._obj_num = obj_num
        self._rotation_angle = 0
        
        # Extract rotation from page dict if present
        if b'/Rotate' in page_dict:
            rotate_val = page_dict[b'/Rotate']
            if isinstance(rotate_val, bytes):
                try:
                    self._rotation_angle = int(rotate_val)
                except ValueError:
                    self._rotation_angle = 0
            elif isinstance(rotate_val, int):
                self._rotation_angle = rotate_val
    
    def rotate(self, angle: int) -> 'PageObject':
        """
        Rotate the page by the given angle.
        
        Args:
            angle: Rotation angle in degrees (must be multiple of 90)
            
        Returns:
            Self for chaining
        """
        self._rotation_angle = (self._rotation_angle + angle) % 360
        return self
    
    @property
    def rotation(self) -> int:
        """Get the current rotation angle in degrees."""
        return self._rotation_angle
    
    def get_contents(self) -> Optional[bytes]:
        """Get the page content stream."""
        if b'/Contents' in self._page_dict:
            contents_ref = self._page_dict[b'/Contents']
            if self._reader:
                return self._reader._resolve_object(contents_ref)
        return None
    
    @property
    def mediabox(self) -> Optional[Any]:
        """Get the MediaBox of the page."""
        return self._page_dict.get(b'/MediaBox')
    
    @property
    def page_dict(self) -> Dict[bytes, Any]:
        """Get the underlying page dictionary."""
        return self._page_dict
    
    @property
    def obj_num(self) -> int:
        """Get the object number."""
        return self._obj_num