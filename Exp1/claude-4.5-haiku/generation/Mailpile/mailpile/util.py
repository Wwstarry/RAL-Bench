"""Utilities for Mailpile core library."""

import re
import unicodedata
from typing import Optional, Union


class CleanText:
    """Utilities for cleaning and normalizing text."""
    
    # Regex patterns
    WHITESPACE_RE = re.compile(r'\s+')
    CONTROL_CHARS_RE = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]')
    
    @staticmethod
    def clean_whitespace(text: str, collapse: bool = True) -> str:
        """
        Clean whitespace from text.
        
        Args:
            text: Input text
            collapse: Whether to collapse multiple spaces to single space
            
        Returns:
            Cleaned text
        """
        if collapse:
            text = CleanText.WHITESPACE_RE.sub(' ', text)
        text = text.strip()
        return text
    
    @staticmethod
    def remove_control_chars(text: str) -> str:
        """
        Remove control characters from text.
        
        Args:
            text: Input text
            
        Returns:
            Text without control characters
        """
        return CleanText.CONTROL_CHARS_RE.sub('', text)
    
    @staticmethod
    def normalize_unicode(text: str, form: str = 'NFC') -> str:
        """
        Normalize unicode text.
        
        Args:
            text: Input text
            form: Normalization form (NFC, NFD, NFKC, NFKD)
            
        Returns:
            Normalized text
        """
        return unicodedata.normalize(form, text)
    
    @staticmethod
    def sanitize(text: str, remove_control: bool = True,
                 normalize: bool = True, collapse_ws: bool = True) -> str:
        """
        Sanitize text by applying multiple cleaning operations.
        
        Args:
            text: Input text
            remove_control: Remove control characters
            normalize: Normalize unicode
            collapse_ws: Collapse whitespace
            
        Returns:
            Sanitized text
        """
        if normalize:
            text = CleanText.normalize_unicode(text)
        if remove_control:
            text = CleanText.remove_control_chars(text)
        if collapse_ws:
            text = CleanText.clean_whitespace(text, collapse=True)
        return text


class Base36:
    """Base36 encoding and decoding utilities."""
    
    ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyz'
    
    @staticmethod
    def encode(num: int) -> str:
        """
        Encode integer to base36 string.
        
        Args:
            num: Integer to encode
            
        Returns:
            Base36 encoded string
        """
        if num == 0:
            return '0'
        
        digits = []
        negative = num < 0
        num = abs(num)
        
        while num:
            digits.append(Base36.ALPHABET[num % 36])
            num //= 36
        
        result = ''.join(reversed(digits))
        return '-' + result if negative else result
    
    @staticmethod
    def decode(text: str) -> int:
        """
        Decode base36 string to integer.
        
        Args:
            text: Base36 encoded string
            
        Returns:
            Decoded integer
        """
        text = text.lower().strip()
        negative = text.startswith('-')
        if negative:
            text = text[1:]
        
        result = 0
        for char in text:
            if char not in Base36.ALPHABET:
                raise ValueError(f"Invalid base36 character: {char}")
            result = result * 36 + Base36.ALPHABET.index(char)
        
        return -result if negative else result


def slugify(text: str, separator: str = '-') -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: Input text
        separator: Separator character
        
    Returns:
        Slugified text
    """
    text = CleanText.normalize_unicode(text, form='NFKD')
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).lower()
    text = re.sub(r'[-\s]+', separator, text)
    return text.strip(separator)


def truncate(text: str, length: int, suffix: str = '...') -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Input text
        length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def safe_int(value: Union[str, int, float], default: int = 0) -> int:
    """
    Safely convert value to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default