import io
import os
import struct
import re
import hashlib
import time
import random
import warnings
from typing import Dict, List, Union, BinaryIO, Optional, Any, Tuple, Set

class PageObject:
    """PDF page object that represents a single page in a PDF file."""
    
    def __init__(self, data=None, pdf=None, index=None):
        self._data = data or {}
        self._pdf = pdf
        self._index = index
        self._content = b""
        
    def rotate(self, angle: int):
        """Rotate the page by the given angle in degrees.
        
        Args:
            angle: Rotation angle in degrees. Positive for clockwise.
        
        Returns:
            The PageObject instance (self).
        """
        current = self.rotation
        new_angle = (current + angle) % 360
        self._data["/Rotate"] = new_angle
        return self
        
    @property
    def rotation(self) -> int:
        """Gets the current rotation of the page in degrees."""
        if "/Rotate" in self._data:
            return self._data["/Rotate"]
        return 0

    @property
    def mediabox(self) -> List[float]:
        """Returns the media box of the page."""
        if "/MediaBox" in self._data:
            return self._data["/MediaBox"]
        return [0, 0, 612, 792]  # Default US Letter size


class PdfReader:
    """Class for reading PDF files."""
    
    def __init__(self, path_or_file):
        self._stream = None
        self._pages = []
        self._encrypted = False
        self._password = None
        self._metadata = {}
        
        # Handle string path or file-like object
        if isinstance(path_or_file, str):
            self._stream = open(path_or_file, "rb")
            self._parse_pdf()
            self._stream.close()
        else:
            # Assume it's a file-like object
            self._stream = path_or_file
            self._parse_pdf()

    def _parse_pdf(self):
        """Parse the PDF file to extract pages and metadata."""
        # In a real implementation, this would parse the PDF structure
        # For simplicity, we'll just read the file and extract basic info
        
        data = self._stream.read()
        
        # Check if file is encrypted (simplified detection)
        if b"/Encrypt" in data:
            self._encrypted = True
        
        # Extract some basic metadata (simplified)
        info_match = re.search(b"/Info\s+(\d+)\s+\d+\s+R", data)
        if info_match:
            # Simple metadata extraction
            title_match = re.search(b"/Title\s*\((.*?)\)", data)
            if title_match:
                self._metadata["/Title"] = title_match.group(1).decode("utf-8", errors="ignore")
                
            author_match = re.search(b"/Author\s*\((.*?)\)", data)
            if author_match:
                self._metadata["/Author"] = author_match.group(1).decode("utf-8", errors="ignore")
        
        # Count pages (simplified)
        page_count = len(re.findall(b"/Type\s*/Page[^s]", data))
        if page_count == 0:
            # Fallback method
            page_count = data.count(b"/Contents") or 1
        
        # Create page objects
        for i in range(page_count):
            # Create page with basic data
            page_data = {
                "/Type": "/Page",
                "/MediaBox": [0, 0, 612, 792],  # Default letter size
            }
            
            # Extract rotation if present
            rotation_match = re.search(b"/Rotate\s+(\d+)", data)
            if rotation_match:
                page_data["/Rotate"] = int(rotation_match.group(1))
                
            self._pages.append(PageObject(page_data, self, i))

    @property
    def pages(self):
        """Get the list of pages in the document."""
        return self._pages
    
    @property
    def is_encrypted(self):
        """Returns True if the PDF is encrypted, False otherwise."""
        return self._encrypted
    
    def decrypt(self, password):
        """Try to decrypt the PDF with the given password.
        
        Args:
            password: The password to try.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self._encrypted:
            return True
            
        # In a real implementation, this would decrypt the document
        # For simplicity, we'll just store the password and assume it works
        self._password = password
        return True
        
    @property
    def metadata(self):
        """Get the metadata of the PDF."""
        return self._metadata


class PdfWriter:
    """Class for creating or modifying PDF files."""
    
    def __init__(self):
        self._pages = []
        self._metadata = {}
        self._encryption = None
    
    def add_page(self, page):
        """Add a page to the PDF.
        
        Args:
            page: A PageObject to add to the PDF.
            
        Returns:
            The PdfWriter instance (self).
        """
        self._pages.append(page)
        return self
    
    def add_blank_page(self, width=612, height=792):
        """Add a blank page to the PDF.
        
        Args:
            width: The width of the page in points.
            height: The height of the page in points.
            
        Returns:
            The PdfWriter instance (self).
        """
        page_data = {
            "/Type": "/Page",
            "/MediaBox": [0, 0, width, height],
        }
        self._pages.append(PageObject(page_data))
        return self
    
    def add_metadata(self, metadata_dict):
        """Add metadata to the PDF.
        
        Args:
            metadata_dict: A dictionary of metadata entries.
            
        Returns:
            The PdfWriter instance (self).
        """
        self._metadata.update(metadata_dict)
        return self
    
    def encrypt(self, user_password, owner_password=None, 
                use_128bit=True, permissions_flag=0):
        """Encrypt the PDF.
        
        Args:
            user_password: The user password.
            owner_password: The owner password. If not provided, the user_password is used.
            use_128bit: Whether to use 128-bit encryption.
            permissions_flag: Permission flags for the PDF.
            
        Returns:
            The PdfWriter instance (self).
        """
        if owner_password is None:
            owner_password = user_password
            
        self._encryption = {
            "user_password": user_password,
            "owner_password": owner_password,
            "use_128bit": use_128bit,
            "permissions": permissions_flag
        }
        return self
    
    def write(self, stream):
        """Write the PDF to a stream.
        
        Args:
            stream: A file-like object to write the PDF to.
        """
        # In a real implementation, this would write a proper PDF structure
        # For simplicity, we'll create a very basic PDF
        
        # Check if we're working with a file path
        if isinstance(stream, str):
            with open(stream, "wb") as f:
                self._write_pdf(f)
        else:
            # Assume it's a file-like object
            self._write_pdf(stream)
    
    def _write_pdf(self, stream):
        """Write the PDF content to the given stream."""
        # PDF header
        stream.write(b"%PDF-1.7\n")
        
        # Objects
        object_positions = {}
        
        # Object 1: Catalog
        object_positions[1] = stream.tell()
        stream.write(b"1 0 obj\n")
        stream.write(b"<<\n")
        stream.write(b"/Type /Catalog\n")
        stream.write(b"/Pages 2 0 R\n")
        stream.write(b">>\n")
        stream.write(b"endobj\n\n")
        
        # Object 2: Pages
        object_positions[2] = stream.tell()
        stream.write(b"2 0 obj\n")
        stream.write(b"<<\n")
        stream.write(b"/Type /Pages\n")
        stream.write(b"/Count " + str(len(self._pages)).encode() + b"\n")
        kids = [f"{3 + i} 0 R" for i in range(len(self._pages))]
        stream.write(b"/Kids [" + " ".join(kids).encode() + b"]\n")
        stream.write(b">>\n")
        stream.write(b"endobj\n\n")
        
        # Objects 3+: Page objects
        for i, page in enumerate(self._pages):
            obj_id = 3 + i
            object_positions[obj_id] = stream.tell()
            stream.write(f"{obj_id} 0 obj\n".encode())
            stream.write(b"<<\n")
            stream.write(b"/Type /Page\n")
            stream.write(b"/Parent 2 0 R\n")
            
            # Media box
            mediabox = page.mediabox
            stream.write(f"/MediaBox [{mediabox[0]} {mediabox[1]} {mediabox[2]} {mediabox[3]}]\n".encode())
            
            # Rotation
            if page.rotation != 0:
                stream.write(f"/Rotate {page.rotation}\n".encode())
            
            # Content (empty for blank pages)
            stream.write(b"/Contents " + f"{obj_id + len(self._pages)} 0 R".encode() + b"\n")
            
            stream.write(b">>\n")
            stream.write(b"endobj\n\n")
        
        # Content streams for each page
        for i in range(len(self._pages)):
            obj_id = 3 + len(self._pages) + i
            object_positions[obj_id] = stream.tell()
            stream.write(f"{obj_id} 0 obj\n".encode())
            stream.write(b"<<\n")
            stream.write(b"/Length 0\n")
            stream.write(b">>\n")
            stream.write(b"stream\n")
            stream.write(b"\nendstream\n")
            stream.write(b"endobj\n\n")
        
        # Info object with metadata
        info_obj_id = 3 + (2 * len(self._pages))
        if self._metadata:
            object_positions[info_obj_id] = stream.tell()
            stream.write(f"{info_obj_id} 0 obj\n".encode())
            stream.write(b"<<\n")
            
            for key, value in self._metadata.items():
                safe_value = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                stream.write(f"{key} ({safe_value})\n".encode())
                
            stream.write(b">>\n")
            stream.write(b"endobj\n\n")
        
        # Encryption dictionary
        encrypt_obj_id = None
        if self._encryption:
            encrypt_obj_id = info_obj_id + 1
            object_positions[encrypt_obj_id] = stream.tell()
            stream.write(f"{encrypt_obj_id} 0 obj\n".encode())
            stream.write(b"<<\n")
            stream.write(b"/Filter /Standard\n")
            if self._encryption["use_128bit"]:
                stream.write(b"/V 2\n")
                stream.write(b"/Length 128\n")
            else:
                stream.write(b"/V 1\n")
            stream.write(b"/R 3\n")  # Revision 3
            
            # In a real implementation, these would be properly computed encryption values
            stream.write(b"/O <" + hashlib.md5(self._encryption["owner_password"].encode()).hexdigest().upper().encode() + b">\n")
            stream.write(b"/U <" + hashlib.md5(self._encryption["user_password"].encode()).hexdigest().upper().encode() + b">\n")
            stream.write(b"/P " + str(self._encryption["permissions"]).encode() + b"\n")
            
            stream.write(b">>\n")
            stream.write(b"endobj\n\n")
        
        # Cross-reference table
        xref_offset = stream.tell()
        stream.write(b"xref\n")
        stream.write(b"0 " + str(len(object_positions) + 1).encode() + b"\n")
        stream.write(b"0000000000 65535 f \n")
        
        for obj_id in range(1, max(object_positions.keys()) + 1):
            if obj_id in object_positions:
                pos = object_positions[obj_id]
                stream.write(f"{pos:010d} 00000 n \n".encode())
            else:
                stream.write(b"0000000000 00000 f \n")
        
        # Trailer
        stream.write(b"trailer\n")
        stream.write(b"<<\n")
        stream.write(b"/Size " + str(len(object_positions) + 1).encode() + b"\n")
        stream.write(b"/Root 1 0 R\n")
        
        if self._metadata:
            stream.write(f"/Info {info_obj_id} 0 R\n".encode())
            
        if self._encryption:
            stream.write(f"/Encrypt {encrypt_obj_id} 0 R\n".encode())
            
        # Document ID for encryption
        if self._encryption:
            doc_id = hashlib.md5(str(time.time()).encode()).hexdigest()
            stream.write(b"/ID [<" + doc_id.encode() + b"> <" + doc_id.encode() + b">]\n")
            
        stream.write(b">>\n")
        stream.write(b"startxref\n")
        stream.write(str(xref_offset).encode() + b"\n")
        stream.write(b"%%EOF\n")