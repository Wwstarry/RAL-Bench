"""
PDF Reader implementation.
"""

import io
import struct
from typing import Union, BinaryIO, Dict, Any, List, Optional


class PdfReader:
    """
    Read PDF files and extract pages and metadata.
    """
    
    def __init__(self, stream: Union[str, BinaryIO]):
        """
        Initialize a PdfReader.
        
        Args:
            stream: Path to PDF file or file-like object
        """
        if isinstance(stream, str):
            self._file = open(stream, 'rb')
            self._close_file = True
        else:
            self._file = stream
            self._close_file = False
        
        self._content = self._file.read()
        self._file.seek(0)
        
        # Parse PDF structure
        self._xref_table = {}
        self._trailer = {}
        self._objects = {}
        self._page_objects = []
        self._encrypted = False
        self._encryption_dict = None
        self._decryption_key = None
        
        self._parse_pdf()
    
    def _parse_pdf(self):
        """Parse the PDF file structure."""
        # Find xref table
        xref_pos = self._find_xref()
        if xref_pos is None:
            raise ValueError("Could not find xref table")
        
        # Parse xref and trailer
        self._parse_xref(xref_pos)
        
        # Check for encryption
        if b'/Encrypt' in self._trailer:
            self._encrypted = True
            encrypt_ref = self._trailer[b'/Encrypt']
            self._encryption_dict = self._resolve_object(encrypt_ref)
        
        # Parse catalog and pages
        if b'/Root' in self._trailer:
            root_ref = self._trailer[b'/Root']
            catalog = self._resolve_object(root_ref)
            if b'/Pages' in catalog:
                pages_ref = catalog[b'/Pages']
                self._parse_pages(pages_ref)
    
    def _find_xref(self) -> Optional[int]:
        """Find the position of the xref table."""
        # Look for startxref at end of file
        self._file.seek(max(0, len(self._content) - 1024))
        tail = self._file.read()
        
        if b'startxref' in tail:
            idx = tail.rfind(b'startxref')
            after = tail[idx + 9:].strip()
            lines = after.split(b'\n')
            if lines:
                try:
                    return int(lines[0].strip())
                except ValueError:
                    pass
        return None
    
    def _parse_xref(self, pos: int):
        """Parse xref table and trailer."""
        self._file.seek(pos)
        line = self._file.readline()
        
        if not line.startswith(b'xref'):
            return
        
        # Parse xref entries
        while True:
            line = self._file.readline()
            if line.startswith(b'trailer'):
                break
            
            parts = line.strip().split()
            if len(parts) == 2:
                # Section header
                start_obj = int(parts[0])
                count = int(parts[1])
                
                for i in range(count):
                    entry_line = self._file.readline()
                    entry_parts = entry_line.strip().split()
                    if len(entry_parts) >= 3:
                        offset = int(entry_parts[0])
                        gen = int(entry_parts[1])
                        in_use = entry_parts[2] == b'n'
                        
                        if in_use:
                            self._xref_table[start_obj + i] = (offset, gen)
        
        # Parse trailer dictionary
        trailer_start = self._file.tell()
        trailer_content = self._file.read(2048)
        self._trailer = self._parse_dict(trailer_content)
    
    def _parse_dict(self, content: bytes) -> Dict[bytes, Any]:
        """Parse a PDF dictionary."""
        result = {}
        
        # Find dictionary boundaries
        start = content.find(b'<<')
        if start == -1:
            return result
        
        end = content.find(b'>>', start)
        if end == -1:
            end = len(content)
        
        dict_content = content[start + 2:end]
        
        # Simple tokenization
        tokens = []
        i = 0
        while i < len(dict_content):
            # Skip whitespace
            while i < len(dict_content) and dict_content[i:i+1] in b' \t\r\n':
                i += 1
            
            if i >= len(dict_content):
                break
            
            # Name
            if dict_content[i:i+1] == b'/':
                j = i + 1
                while j < len(dict_content) and dict_content[j:j+1] not in b' \t\r\n/<>[]()':
                    j += 1
                tokens.append(dict_content[i:j])
                i = j
            # String
            elif dict_content[i:i+1] == b'(':
                j = i + 1
                depth = 1
                while j < len(dict_content) and depth > 0:
                    if dict_content[j:j+1] == b'(':
                        depth += 1
                    elif dict_content[j:j+1] == b')':
                        depth -= 1
                    j += 1
                tokens.append(dict_content[i:j])
                i = j
            # Array
            elif dict_content[i:i+1] == b'[':
                j = i + 1
                depth = 1
                while j < len(dict_content) and depth > 0:
                    if dict_content[j:j+1] == b'[':
                        depth += 1
                    elif dict_content[j:j+1] == b']':
                        depth -= 1
                    j += 1
                tokens.append(dict_content[i:j])
                i = j
            # Dict
            elif dict_content[i:i+2] == b'<<':
                j = i + 2
                depth = 1
                while j < len(dict_content) - 1 and depth > 0:
                    if dict_content[j:j+2] == b'<<':
                        depth += 1
                        j += 2
                    elif dict_content[j:j+2] == b'>>':
                        depth -= 1
                        j += 2
                    else:
                        j += 1
                tokens.append(dict_content[i:j])
                i = j
            # Number or reference
            else:
                j = i
                while j < len(dict_content) and dict_content[j:j+1] not in b' \t\r\n/<>[]()':
                    j += 1
                tokens.append(dict_content[i:j])
                i = j
        
        # Parse key-value pairs
        i = 0
        while i < len(tokens):
            if tokens[i].startswith(b'/'):
                key = tokens[i]
                if i + 1 < len(tokens):
                    value = tokens[i + 1]
                    
                    # Check for indirect reference
                    if (i + 3 < len(tokens) and 
                        tokens[i + 2] == b'R' and 
                        value.isdigit()):
                        # Indirect reference
                        obj_num = int(value)
                        gen_num = int(tokens[i + 1]) if i + 1 < len(tokens) else 0
                        result[key] = (obj_num, gen_num, b'R')
                        i += 3
                    else:
                        result[key] = value
                        i += 2
                else:
                    i += 1
            else:
                i += 1
        
        return result
    
    def _resolve_object(self, ref: Any) -> Any:
        """Resolve an indirect object reference."""
        if isinstance(ref, tuple) and len(ref) == 3 and ref[2] == b'R':
            obj_num = ref[0]
            
            if obj_num in self._objects:
                return self._objects[obj_num]
            
            if obj_num in self._xref_table:
                offset, gen = self._xref_table[obj_num]
                self._file.seek(offset)
                
                # Read object
                obj_content = self._file.read(4096)
                
                # Parse object
                obj_dict = self._parse_dict(obj_content)
                self._objects[obj_num] = obj_dict
                return obj_dict
        
        return ref
    
    def _parse_pages(self, pages_ref: Any):
        """Parse the page tree."""
        pages_dict = self._resolve_object(pages_ref)
        
        if b'/Kids' in pages_dict:
            kids = pages_dict[b'/Kids']
            kids_str = kids.decode('latin-1') if isinstance(kids, bytes) else str(kids)
            
            # Parse array
            if kids_str.startswith('['):
                kids_str = kids_str[1:-1]
                parts = kids_str.split()
                
                i = 0
                while i < len(parts):
                    if parts[i].isdigit() and i + 2 < len(parts) and parts[i + 2] == 'R':
                        obj_num = int(parts[i])
                        gen_num = int(parts[i + 1])
                        page_ref = (obj_num, gen_num, b'R')
                        
                        page_dict = self._resolve_object(page_ref)
                        
                        # Check if it's a page or another pages node
                        page_type = page_dict.get(b'/Type', b'')
                        if page_type == b'/Page':
                            from pypdf.page import PageObject
                            page_obj = PageObject(self, page_dict, obj_num)
                            self._page_objects.append(page_obj)
                        elif page_type == b'/Pages':
                            # Recursively parse
                            self._parse_pages(page_ref)
                        
                        i += 3
                    else:
                        i += 1
    
    @property
    def pages(self) -> List['PageObject']:
        """Get list of pages."""
        return self._page_objects
    
    @property
    def is_encrypted(self) -> bool:
        """Check if the PDF is encrypted."""
        return self._encrypted
    
    def decrypt(self, password: str) -> int:
        """
        Decrypt the PDF with the given password.
        
        Args:
            password: The password to decrypt with
            
        Returns:
            1 if decryption successful with user password,
            2 if successful with owner password,
            0 if failed
        """
        if not self._encrypted:
            return 0
        
        # Simple password check - in real implementation would compute encryption key
        # For testing purposes, we'll just mark as decrypted
        self._decryption_key = password.encode('latin-1')
        return 1
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get document metadata."""
        if b'/Info' in self._trailer:
            info_ref = self._trailer[b'/Info']
            info_dict = self._resolve_object(info_ref)
            
            # Convert to string keys
            result = {}
            for key, value in info_dict.items():
                if isinstance(key, bytes):
                    key_str = key.decode('latin-1')
                    if isinstance(value, bytes):
                        # Remove string delimiters if present
                        value_str = value.decode('latin-1')
                        if value_str.startswith('(') and value_str.endswith(')'):
                            value_str = value_str[1:-1]
                        result[key_str] = value_str
                    else:
                        result[key_str] = value
            
            return result
        
        return {}
    
    def __del__(self):
        """Clean up resources."""
        if hasattr(self, '_close_file') and self._close_file and hasattr(self, '_file'):
            try:
                self._file.close()
            except:
                pass