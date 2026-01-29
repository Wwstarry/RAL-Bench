from ._reader import PageObject, PdfReader
from typing import BinaryIO, Dict, List


class PdfWriter:
    def __init__(self):
        self._pages = []
        self._metadata = {}
        self._encrypted = False
        self._password = None
        
    def add_page(self, page: PageObject) -> None:
        """Add a page to the PDF."""
        self._pages.append(page)
        
    def add_blank_page(self, width: float = 612, height: float = 792) -> PageObject:
        """Add a blank page with the given dimensions."""
        page_dict = {
            "/Rotate": 0,
            "/MediaBox": [0, 0, width, height]
        }
        page = PageObject(page_dict)
        self._pages.append(page)
        return page
        
    def encrypt(self, password: str) -> None:
        """Encrypt the PDF with the given password."""
        self._encrypted = True
        self._password = password
        
    def add_metadata(self, metadata: Dict) -> None:
        """Add metadata to the PDF."""
        self._metadata.update(metadata)
        
    def write(self, stream: BinaryIO) -> None:
        """Write the PDF to the given stream."""
        # Generate simple PDF content
        content = b"%PDF-1.4\n"
        
        # Add metadata if present
        if self._metadata:
            metadata_str = " ".join(f"/{k[1:]} ({v})" for k, v in self._metadata.items())
            content += b"<<" + metadata_str.encode() + b">>\n"
            
        # Add pages
        for i, page in enumerate(self._pages):
            page_content = f"<< /Type /Page /Rotate {page.rotation} >>"
            content += page_content.encode() + b"\n"
            
        # Add encryption marker if encrypted
        if self._encrypted:
            content += b"<< /Encrypt >>\n"
            
        content += b"%%EOF"
        stream.write(content)
        
    @property
    def pages(self) -> List[PageObject]:
        """Return list of pages in the writer."""
        return self._pages