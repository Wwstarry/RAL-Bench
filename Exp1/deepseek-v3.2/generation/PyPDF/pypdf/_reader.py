import io
import struct
import zlib
from typing import Union, BinaryIO, Dict, Any, Optional, List
from ._page import PageObject
from ._utils import (
    PdfFormatError,
    PdfReadError,
    read_object,
    write_object,
    PdfObject,
    PdfDict,
    PdfArray,
    PdfName,
    PdfString,
    PdfStream,
    PdfNull,
    PdfNumber,
    PdfBoolean,
    resolve_indirect,
    decode_pdf_string,
    parse_pdf_date,
    RC4_encrypt,
    ARC4_encrypt,
    compute_encryption_key,
    check_password,
    STANDARD_ENCRYPTION_PADDING,
    ENCRYPTION_ALGORITHMS,
    ID_LENGTH,
    PDF_HEADER,
    XREF_TABLE,
    XREF_STREAM,
    TRAILER,
    STARTXREF,
    OBJ,
    ENDOBJ,
    STREAM,
    ENDSTREAM,
    R,
)

class PdfReader:
    """Reads and parses a PDF file."""
    
    def __init__(self, stream: Union[str, BinaryIO, bytes, io.BytesIO]):
        """
        Initialize a PdfReader.
        
        Args:
            stream: A file path string, file-like object, or bytes.
        """
        self.stream = None
        self._data = None
        self._root = None
        self._pages = None
        self._info = None
        self._metadata = None
        self._encryption = None
        self._encrypt_dict = None
        self._password = None
        self._decrypted = False
        self._xref = {}
        self._trailer = None
        self._header_version = None
        
        if isinstance(stream, str):
            with open(stream, 'rb') as f:
                self._data = f.read()
        elif isinstance(stream, bytes):
            self._data = stream
        elif isinstance(stream, io.BytesIO):
            self._data = stream.getvalue()
        elif hasattr(stream, 'read'):
            self._data = stream.read()
        else:
            raise TypeError("stream must be a path string, bytes, or file-like object")
        
        self._parse()
    
    def _parse(self):
        """Parse the PDF data."""
        data = self._data
        
        # Check PDF header
        if not data.startswith(PDF_HEADER):
            raise PdfReadError("PDF starts with '%s', not '%s'" % (data[:8], PDF_HEADER))
        
        # Find startxref
        startxref_pos = data.rfind(STARTXREF)
        if startxref_pos == -1:
            raise PdfReadError("startxref not found")
        
        # Skip "startxref" and whitespace
        pos = startxref_pos + len(STARTXREF)
        while pos < len(data) and data[pos] in b' \t\n\r\f':
            pos += 1
        
        # Read startxref value
        startxref_str = b''
        while pos < len(data) and data[pos] in b'0123456789':
            startxref_str += bytes([data[pos]])
            pos += 1
        
        if not startxref_str:
            raise PdfReadError("startxref value not found")
        
        startxref = int(startxref_str)
        
        # Read xref and trailer
        self._read_xref(startxref)
        
        # Get root catalog
        if 'Root' not in self._trailer:
            raise PdfReadError("No Root entry in trailer")
        
        root_ref = self._trailer['Root']
        self._root = resolve_indirect(root_ref, self._xref)
        
        # Get info dict if present
        if 'Info' in self._trailer:
            info_ref = self._trailer['Info']
            self._info = resolve_indirect(info_ref, self._xref)
        
        # Check for encryption
        if 'Encrypt' in self._trailer:
            self._encrypt_dict = resolve_indirect(self._trailer['Encrypt'], self._xref)
            self._encryption = self._encrypt_dict.get('/Filter', PdfName('/Standard'))
    
    def _read_xref(self, startxref: int):
        """Read the cross-reference table or stream."""
        data = self._data
        pos = startxref
        
        # Check if it's an xref table or stream
        if data[pos:pos+4] == XREF_TABLE:
            self._read_xref_table(pos)
        else:
            # Assume xref stream
            self._read_xref_stream(pos)
    
    def _read_xref_table(self, pos: int):
        """Read a traditional xref table."""
        data = self._data
        
        # Skip "xref"
        pos += len(XREF_TABLE)
        
        # Skip whitespace
        while pos < len(data) and data[pos] in b' \t\n\r\f':
            pos += 1
        
        # Read subsections
        while True:
            # Read start object number
            start_str = b''
            while pos < len(data) and data[pos] in b'0123456789':
                start_str += bytes([data[pos]])
                pos += 1
            
            if not start_str:
                break
            
            # Skip whitespace
            while pos < len(data) and data[pos] in b' \t\n\r\f':
                pos += 1
            
            # Read count
            count_str = b''
            while pos < len(data) and data[pos] in b'0123456789':
                count_str += bytes([data[pos]])
                pos += 1
            
            if not count_str:
                raise PdfReadError("Invalid xref table")
            
            start = int(start_str)
            count = int(count_str)
            
            # Skip whitespace
            while pos < len(data) and data[pos] in b' \t\n\r\f':
                pos += 1
            
            # Read entries
            for i in range(count):
                # Read offset (10 bytes)
                offset_str = data[pos:pos+10]
                if len(offset_str) < 10:
                    raise PdfReadError("Invalid xref entry")
                
                # Skip whitespace
                pos += 10
                while pos < len(data) and data[pos] in b' \t\n\r\f':
                    pos += 1
                
                # Read generation (5 bytes)
                gen_str = data[pos:pos+5]
                if len(gen_str) < 5:
                    raise PdfReadError("Invalid xref entry")
                
                # Skip whitespace
                pos += 5
                while pos < len(data) and data[pos] in b' \t\n\r\f':
                    pos += 1
                
                # Read flag (1 byte)
                flag = data[pos]
                pos += 1
                
                # Skip whitespace
                while pos < len(data) and data[pos] in b' \t\n\r\f':
                    pos += 1
                
                if flag == ord('n'):
                    # In-use entry
                    offset = int(offset_str)
                    generation = int(gen_str)
                    self._xref[(start + i, generation)] = offset
                elif flag == ord('f'):
                    # Free entry
                    pass
                else:
                    raise PdfReadError("Invalid xref entry flag: %s" % chr(flag))
            
            # Skip whitespace
            while pos < len(data) and data[pos] in b' \t\n\r\f':
                pos += 1
        
        # Read trailer
        if data[pos:pos+len(TRAILER)] != TRAILER:
            raise PdfReadError("trailer not found after xref")
        
        pos += len(TRAILER)
        
        # Skip whitespace
        while pos < len(data) and data[pos] in b' \t\n\r\f':
            pos += 1
        
        # Parse trailer dictionary
        trailer_obj, pos = read_object(data, pos, self._xref)
        self._trailer = trailer_obj
    
    def _read_xref_stream(self, pos: int):
        """Read an xref stream."""
        data = self._data
        
        # Read the stream object
        stream_obj, _ = read_object(data, pos, {})
        
        if not isinstance(stream_obj, PdfStream):
            raise PdfReadError("Expected xref stream")
        
        # Get stream data
        stream_data = stream_obj.get_data()
        
        # Get fields
        w = stream_obj.get('/W', PdfArray([1, 2, 1]))
        if isinstance(w, PdfArray):
            w1 = w[0].value if isinstance(w[0], PdfNumber) else 1
            w2 = w[1].value if isinstance(w[1], PdfNumber) else 2
            w3 = w[2].value if isinstance(w[2], PdfNumber) else 1
        else:
            w1, w2, w3 = 1, 2, 1
        
        # Get index
        index = stream_obj.get('/Index', PdfArray([0, stream_obj.get('/Size', PdfNumber(0)).value]))
        if isinstance(index, PdfArray):
            indices = [index[i].value if isinstance(index[i], PdfNumber) else index[i] for i in range(len(index))]
        else:
            indices = [0, stream_obj.get('/Size', PdfNumber(0)).value]
        
        # Parse entries
        stream_pos = 0
        for i in range(0, len(indices), 2):
            start = indices[i]
            count = indices[i+1]
            
            for obj_num in range(start, start + count):
                # Read fields
                field1 = 0
                for j in range(w1):
                    field1 = (field1 << 8) | stream_data[stream_pos]
                    stream_pos += 1
                
                field2 = 0
                for j in range(w2):
                    field2 = (field2 << 8) | stream_data[stream_pos]
                    stream_pos += 1
                
                field3 = 0
                for j in range(w3):
                    field3 = (field3 << 8) | stream_data[stream_pos]
                    stream_pos += 1
                
                # Type 1: in-use object
                if field1 == 1:
                    self._xref[(obj_num, field3)] = field2
                # Type 2: compressed object
                elif field1 == 2:
                    # Store as (objstm_id, index_in_objstm)
                    self._xref[(obj_num, 0)] = (field2, field3)
        
        # Trailer is the stream dictionary
        self._trailer = stream_obj
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get document metadata."""
        if self._metadata is None:
            self._metadata = {}
            if self._info:
                for key, value in self._info.items():
                    if key.startswith('/'):
                        key = key[1:]
                    if isinstance(value, PdfString):
                        self._metadata[key] = decode_pdf_string(value)
                    elif isinstance(value, PdfName):
                        self._metadata[key] = value.value[1:]
                    elif isinstance(value, PdfNumber):
                        self._metadata[key] = value.value
                    elif isinstance(value, PdfBoolean):
                        self._metadata[key] = value.value
                    elif isinstance(value, PdfNull):
                        self._metadata[key] = None
        return self._metadata
    
    @property
    def is_encrypted(self) -> bool:
        """Check if the document is encrypted."""
        return self._encryption is not None
    
    def decrypt(self, password: str) -> bool:
        """
        Decrypt the PDF with the given password.
        
        Args:
            password: The password to decrypt with.
            
        Returns:
            True if decryption was successful.
        """
        if not self.is_encrypted:
            return True
        
        if self._decrypted:
            return True
        
        # Get encryption parameters
        encrypt_dict = self._encrypt_dict
        
        # Check password
        if check_password(password, encrypt_dict, self._trailer.get('/ID')):
            self._password = password
            self._decrypted = True
            return True
        
        return False
    
    @property
    def pages(self) -> List[PageObject]:
        """Get the pages of the document."""
        if self._pages is None:
            self._pages = []
            
            # Get pages tree
            if 'Pages' not in self._root:
                raise PdfReadError("No Pages entry in root")
            
            pages_tree = resolve_indirect(self._root['Pages'], self._xref)
            
            # Traverse pages tree
            self._extract_pages(pages_tree)
        
        return self._pages
    
    def _extract_pages(self, node: PdfObject):
        """Extract pages from a pages tree node."""
        if node.get('/Type') == PdfName('/Page'):
            # Leaf page
            page = PageObject(node, self)
            self._pages.append(page)
        elif node.get('/Type') == PdfName('/Pages'):
            # Intermediate node
            kids = node.get('/Kids', PdfArray([]))
            if isinstance(kids, PdfArray):
                for kid_ref in kids:
                    kid = resolve_indirect(kid_ref, self._xref)
                    self._extract_pages(kid)
    
    def _get_object(self, ref: tuple) -> PdfObject:
        """Get an object by reference."""
        if ref in self._xref:
            offset_or_info = self._xref[ref]
            
            if isinstance(offset_or_info, tuple):
                # Compressed object
                objstm_id, index = offset_or_info
                
                # Get object stream
                objstm_ref = (objstm_id, 0)
                if objstm_ref not in self._xref:
                    raise PdfReadError("Compressed object stream not found")
                
                objstm_offset = self._xref[objstm_ref]
                objstm_data = self._data
                
                # Read object stream
                obj_pos = objstm_offset
                
                # Skip object number and generation
                while obj_pos < len(objstm_data) and objstm_data[obj_pos] not in b'0123456789':
                    obj_pos += 1
                
                # Read object number
                obj_num_str = b''
                while obj_pos < len(objstm_data) and objstm_data[obj_pos] in b'0123456789':
                    obj_num_str += bytes([objstm_data[obj_pos]])
                    obj_pos += 1
                
                # Skip whitespace
                while obj_pos < len(objstm_data) and objstm_data[obj_pos] in b' \t\n\r\f':
                    obj_pos += 1
                
                # Read generation
                gen_str = b''
                while obj_pos < len(objstm_data) and objstm_data[obj_pos] in b'0123456789':
                    gen_str += bytes([objstm_data[obj_pos]])
                    obj_pos += 1
                
                # Skip whitespace
                while obj_pos < len(objstm_data) and objstm_data[obj_pos] in b' \t\n\r\f':
                    obj_pos += 1
                
                # Should be "obj"
                if objstm_data[obj_pos:obj_pos+3] != OBJ:
                    raise PdfReadError("Invalid object stream")
                
                obj_pos += 3
                
                # Skip whitespace
                while obj_pos < len(objstm_data) and objstm_data[obj_pos] in b' \t\n\r\f':
                    obj_pos += 1
                
                # Parse stream object
                stream_obj, obj_pos = read_object(objstm_data, obj_pos, {})
                
                if not isinstance(stream_obj, PdfStream):
                    raise PdfReadError("Expected object stream")
                
                # Get stream data
                stream_data = stream_obj.get_data()
                
                # Parse object indexes
                first = stream_obj.get('/First', PdfNumber(0)).value
                n = stream_obj.get('/N', PdfNumber(0)).value
                
                # Read object offsets
                offsets = []
                for i in range(n):
                    # Read object number
                    num_str = b''
                    while stream_data[i*2] in b'0123456789':
                        num_str += bytes([stream_data[i*2]])
                    
                    # Read offset
                    offset_str = b''
                    while stream_data[i*2+1] in b'0123456789':
                        offset_str += bytes([stream_data[i*2+1]])
                    
                    offsets.append((int(num_str), int(offset_str)))
                
                # Find and parse our object
                for obj_num, offset in offsets:
                    if obj_num == ref[0]:
                        obj_data = stream_data[first + offset:]
                        obj, _ = read_object(obj_data, 0, {})
                        return obj
                
                raise PdfReadError("Object not found in object stream")
            else:
                # Regular object
                offset = offset_or_info
                obj_data = self._data
                
                # Parse object
                obj, _ = read_object(obj_data, offset, self._xref)
                return obj
        
        raise PdfReadError("Object not found: %s" % str(ref))