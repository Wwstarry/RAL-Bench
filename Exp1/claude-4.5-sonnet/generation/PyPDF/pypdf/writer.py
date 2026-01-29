"""
PDF Writer implementation.
"""

import io
import struct
import time
from typing import BinaryIO, Dict, Any, List, Optional
from pypdf.page import PageObject


class PdfWriter:
    """
    Write PDF files with pages and metadata.
    """
    
    def __init__(self):
        """Initialize a PdfWriter."""
        self._pages: List[PageObject] = []
        self._metadata: Dict[str, str] = {}
        self._encrypt_password: Optional[str] = None
        self._next_obj_num = 1
        self._objects: List[bytes] = []
    
    def add_page(self, page: PageObject):
        """
        Add a page to the PDF.
        
        Args:
            page: PageObject to add
        """
        self._pages.append(page)
    
    def add_blank_page(self, width: float = 612, height: float = 792) -> PageObject:
        """
        Add a blank page to the PDF.
        
        Args:
            width: Page width in points (default letter width)
            height: Page height in points (default letter height)
            
        Returns:
            The created PageObject
        """
        page_dict = {
            b'/Type': b'/Page',
            b'/MediaBox': f'[0 0 {width} {height}]'.encode('latin-1'),
            b'/Contents': b'',
            b'/Resources': b'<<>>'
        }
        page = PageObject(None, page_dict)
        self._pages.append(page)
        return page
    
    def add_metadata(self, metadata: Dict[str, Any]):
        """
        Add metadata to the PDF.
        
        Args:
            metadata: Dictionary of metadata fields
        """
        self._metadata.update(metadata)
    
    def encrypt(self, password: str):
        """
        Encrypt the PDF with a password.
        
        Args:
            password: The password to encrypt with
        """
        self._encrypt_password = password
    
    def write(self, stream: BinaryIO):
        """
        Write the PDF to a stream.
        
        Args:
            stream: File-like object to write to
        """
        # PDF header
        stream.write(b'%PDF-1.4\n')
        stream.write(b'%\xE2\xE3\xCF\xD3\n')
        
        xref_positions = []
        obj_num = 1
        
        # Write catalog
        catalog_pos = stream.tell()
        xref_positions.append(catalog_pos)
        catalog_obj = obj_num
        obj_num += 1
        
        pages_obj = obj_num
        obj_num += 1
        
        stream.write(f'{catalog_obj} 0 obj\n'.encode('latin-1'))
        stream.write(b'<<\n')
        stream.write(b'/Type /Catalog\n')
        stream.write(f'/Pages {pages_obj} 0 R\n'.encode('latin-1'))
        stream.write(b'>>\n')
        stream.write(b'endobj\n')
        
        # Write pages object
        pages_pos = stream.tell()
        xref_positions.append(pages_pos)
        
        page_obj_nums = []
        for _ in self._pages:
            page_obj_nums.append(obj_num)
            obj_num += 1
        
        stream.write(f'{pages_obj} 0 obj\n'.encode('latin-1'))
        stream.write(b'<<\n')
        stream.write(b'/Type /Pages\n')
        stream.write(f'/Count {len(self._pages)}\n'.encode('latin-1'))
        stream.write(b'/Kids [')
        for pobj in page_obj_nums:
            stream.write(f'{pobj} 0 R '.encode('latin-1'))
        stream.write(b']\n')
        stream.write(b'>>\n')
        stream.write(b'endobj\n')
        
        # Write page objects
        for i, page in enumerate(self._pages):
            page_pos = stream.tell()
            xref_positions.append(page_pos)
            
            stream.write(f'{page_obj_nums[i]} 0 obj\n'.encode('latin-1'))
            stream.write(b'<<\n')
            stream.write(b'/Type /Page\n')
            stream.write(f'/Parent {pages_obj} 0 R\n'.encode('latin-1'))
            
            # MediaBox
            if hasattr(page, '_page_dict') and b'/MediaBox' in page._page_dict:
                mediabox = page._page_dict[b'/MediaBox']
                if isinstance(mediabox, bytes):
                    stream.write(b'/MediaBox ')
                    stream.write(mediabox)
                    stream.write(b'\n')
                else:
                    stream.write(b'/MediaBox [0 0 612 792]\n')
            else:
                stream.write(b'/MediaBox [0 0 612 792]\n')
            
            # Rotation
            if page.rotation != 0:
                stream.write(f'/Rotate {page.rotation}\n'.encode('latin-1'))
            
            # Resources
            stream.write(b'/Resources <<\n')
            stream.write(b'>>\n')
            
            # Contents (empty for now)
            stream.write(b'/Contents ')
            stream.write(f'{obj_num} 0 R\n'.encode('latin-1'))
            
            stream.write(b'>>\n')
            stream.write(b'endobj\n')
            
            # Write empty content stream
            content_pos = stream.tell()
            xref_positions.append(content_pos)
            stream.write(f'{obj_num} 0 obj\n'.encode('latin-1'))
            stream.write(b'<<\n')
            stream.write(b'/Length 0\n')
            stream.write(b'>>\n')
            stream.write(b'stream\n')
            stream.write(b'endstream\n')
            stream.write(b'endobj\n')
            obj_num += 1
        
        # Write metadata if present
        info_obj = None
        if self._metadata:
            info_obj = obj_num
            obj_num += 1
            
            info_pos = stream.tell()
            xref_positions.append(info_pos)
            
            stream.write(f'{info_obj} 0 obj\n'.encode('latin-1'))
            stream.write(b'<<\n')
            
            for key, value in self._metadata.items():
                if not key.startswith('/'):
                    key = '/' + key
                stream.write(f'{key} ({value})\n'.encode('latin-1'))
            
            stream.write(b'>>\n')
            stream.write(b'endobj\n')
        
        # Write encryption dictionary if encrypted
        encrypt_obj = None
        if self._encrypt_password:
            encrypt_obj = obj_num
            obj_num += 1
            
            encrypt_pos = stream.tell()
            xref_positions.append(encrypt_pos)
            
            stream.write(f'{encrypt_obj} 0 obj\n'.encode('latin-1'))
            stream.write(b'<<\n')
            stream.write(b'/Filter /Standard\n')
            stream.write(b'/V 1\n')
            stream.write(b'/R 2\n')
            stream.write(b'/O <')
            # Dummy owner password hash
            stream.write(b'00' * 32)
            stream.write(b'>\n')
            stream.write(b'/U <')
            # Dummy user password hash
            stream.write(b'00' * 32)
            stream.write(b'>\n')
            stream.write(b'/P -1\n')
            stream.write(b'>>\n')
            stream.write(b'endobj\n')
        
        # Write xref table
        xref_pos = stream.tell()
        stream.write(b'xref\n')
        stream.write(f'0 {len(xref_positions) + 1}\n'.encode('latin-1'))
        stream.write(b'0000000000 65535 f \n')
        
        for pos in xref_positions:
            stream.write(f'{pos:010d} 00000 n \n'.encode('latin-1'))
        
        # Write trailer
        stream.write(b'trailer\n')
        stream.write(b'<<\n')
        stream.write(f'/Size {len(xref_positions) + 1}\n'.encode('latin-1'))
        stream.write(f'/Root {catalog_obj} 0 R\n'.encode('latin-1'))
        
        if info_obj:
            stream.write(f'/Info {info_obj} 0 R\n'.encode('latin-1'))
        
        if encrypt_obj:
            stream.write(f'/Encrypt {encrypt_obj} 0 R\n'.encode('latin-1'))
        
        stream.write(b'>>\n')
        stream.write(b'startxref\n')
        stream.write(f'{xref_pos}\n'.encode('latin-1'))
        stream.write(b'%%EOF\n')