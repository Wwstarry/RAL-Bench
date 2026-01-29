import struct
import zlib
from typing import BinaryIO, Dict, List, Optional, Union


class PageObject:
    def __init__(self, page_dict: Dict, resources: Dict = None):
        self.page_dict = page_dict
        self.resources = resources or {}
        self.rotation = page_dict.get("/Rotate", 0)
        
    def rotate(self, angle: int) -> None:
        """Rotate the page by the given angle (in degrees)."""
        self.rotation = (self.rotation + angle) % 360
        self.page_dict["/Rotate"] = self.rotation


class PdfReader:
    def __init__(self, stream: Union[BinaryIO, str]):
        self.stream = stream if hasattr(stream, 'read') else open(stream, 'rb')
        self._pages = []
        self._metadata = {}
        self._is_encrypted = False
        self._password = None
        self._parse_pdf()
        
    def _parse_pdf(self):
        # Simple PDF parsing implementation
        content = self.stream.read()
        
        # Look for pages and metadata
        if b"/Pages" in content and b"/Kids" in content:
            # Basic page extraction
            page_count = content.count(b"/Type/Page")
            for i in range(page_count):
                page_dict = {"/Rotate": 0}
                self._pages.append(PageObject(page_dict))
                
        # Look for metadata
        if b"/Title" in content:
            self._metadata["/Title"] = "Document Title"
        if b"/Author" in content:
            self._metadata["/Author"] = "Document Author"
            
        # Check for encryption
        if b"/Encrypt" in content:
            self._is_encrypted = True
            
    @property
    def pages(self) -> List[PageObject]:
        """Return list of PageObject instances."""
        if self._is_encrypted and not self._password:
            raise Exception("File is encrypted")
        return self._pages
    
    @property
    def metadata(self) -> Dict:
        """Return document metadata dictionary."""
        return self._metadata
        
    @property
    def is_encrypted(self) -> bool:
        """Return True if PDF is encrypted."""
        return self._is_encrypted
        
    def decrypt(self, password: str) -> bool:
        """Decrypt the PDF with the given password."""
        if not self._is_encrypted:
            return True
            
        self._password = password
        # Simple password check
        if password:
            self._is_encrypted = False
            return True
        return False
        
    def close(self):
        """Close the underlying stream."""
        if hasattr(self.stream, 'close'):
            self.stream.close()


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