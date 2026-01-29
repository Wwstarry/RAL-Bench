"""Utilities for Mailpile."""
import re
import string
import hashlib
import base64
import time
from typing import Any, Dict, List, Optional, Union
from email.utils import parsedate_to_datetime

class CleanText:
    """Text cleaning utilities."""
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in text."""
        if not text:
            return ""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        return text.strip()
        
    @staticmethod
    def remove_control_chars(text: str) -> str:
        """Remove control characters from text."""
        if not text:
            return ""
        # Keep tab, newline, carriage return
        control_chars = ''.join(chr(i) for i in range(32) 
                              if chr(i) not in '\t\n\r')
        translator = str.maketrans('', '', control_chars)
        return text.translate(translator)
        
    @staticmethod
    def safe_unicode(text: Any, encoding: str = 'utf-8') -> str:
        """Convert input to safe unicode string."""
        if text is None:
            return ""
        if isinstance(text, str):
            return text
        if isinstance(text, bytes):
            try:
                return text.decode(encoding, errors='replace')
            except (UnicodeDecodeError, LookupError):
                return text.decode('utf-8', errors='replace')
        return str(text)
        
    @staticmethod
    def truncate(text: str, length: int, ellipsis: str = "...") -> str:
        """Truncate text to specified length."""
        if len(text) <= length:
            return text
        return text[:max(0, length - len(ellipsis))] + ellipsis

class Base36:
    """Base36 encoding/decoding utilities."""
    
    ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    @staticmethod
    def encode(number: int) -> str:
        """Encode integer to base36 string."""
        if not isinstance(number, int):
            raise TypeError("Number must be an integer")
        if number < 0:
            raise ValueError("Number must be non-negative")
            
        if number == 0:
            return '0'
            
        chars = []
        while number > 0:
            number, remainder = divmod(number, 36)
            chars.append(Base36.ALPHABET[remainder])
        return ''.join(reversed(chars))
        
    @staticmethod
    def decode(text: str) -> int:
        """Decode base36 string to integer."""
        if not text:
            raise ValueError("Empty string cannot be decoded")
            
        text = text.upper()
        result = 0
        for char in text:
            if char not in Base36.ALPHABET:
                raise ValueError(f"Invalid base36 character: {char}")
            result = result * 36 + Base36.ALPHABET.index(char)
        return result

class Helpers:
    """General helper functions."""
    
    @staticmethod
    def get_timestamp() -> int:
        """Get current timestamp as integer."""
        return int(time.time())
        
    @staticmethod
    def parse_date(date_str: str) -> Optional[int]:
        """Parse date string to timestamp."""
        try:
            dt = parsedate_to_datetime(date_str)
            return int(dt.timestamp())
        except (TypeError, ValueError):
            return None
            
    @staticmethod
    def md5_hash(data: str) -> str:
        """Calculate MD5 hash of data."""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
        
    @staticmethod
    def b64encode(data: str) -> str:
        """Base64 encode string."""
        return base64.b64encode(data.encode('utf-8')).decode('ascii')
        
    @staticmethod
    def b64decode(data: str) -> str:
        """Base64 decode string."""
        return base64.b64decode(data).decode('utf-8')
        
    @staticmethod
    def safe_get(dictionary: Dict, key: Any, default: Any = None) -> Any:
        """Safely get value from dictionary with nested key support."""
        if not isinstance(dictionary, dict):
            return default
            
        keys = key.split('.') if isinstance(key, str) else key
        current = dictionary
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current
        
    @staticmethod
    def chunk_list(lst: List, size: int) -> List[List]:
        """Split list into chunks of specified size."""
        return [lst[i:i + size] for i in range(0, len(lst), size)]