import re
import unicodedata
from typing import Optional, Set, List, Dict, Any


def _remove_accents(text: str) -> str:
    """Remove accents from unicode characters."""
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')


def _transliterate(text: str) -> str:
    """Basic transliteration of common unicode characters to ASCII equivalents."""
    replacements = {
        'ä': 'a', 'ö': 'o', 'ü': 'u', 'ß': 'ss',
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u',
        'ý': 'y', 'ỳ': 'y', 'ŷ': 'y', 'ÿ': 'y',
        'ç': 'c', 'č': 'c', 'ć': 'c',
        'ñ': 'n', 'ń': 'n',
        'š': 's', 'ś': 's',
        'ž': 'z', 'ź': 'z',
        'đ': 'd',
        'ł': 'l',
        'ø': 'o',
        'æ': 'ae',
        'œ': 'oe',
    }
    
    result = []
    for char in text:
        if char in replacements:
            result.append(replacements[char])
        else:
            result.append(char)
    return ''.join(result)


def slugify(
    text: str,
    allow_unicode: bool = False,
    max_length: Optional[int] = None,
    word_boundary: bool = False,
    separator: str = '-',
    regex_pattern: Optional[str] = None,
    stopwords: Optional[Set[str]] = None,
    lowercase: bool = True,
    replacements: Optional[List[tuple]] = None,
    **kwargs: Any
) -> str:
    """
    Convert a string to a slug.
    
    Args:
        text: The text to slugify
        allow_unicode: If True, allow non-ASCII characters in output
        max_length: Maximum length of the slug
        word_boundary: If True, truncate at word boundary when using max_length
        separator: Character to use as separator (default: '-')
        regex_pattern: Custom regex pattern for filtering characters
        stopwords: Set of words to remove from the slug
        lowercase: If True, convert to lowercase (default: True)
        replacements: List of (old, new) tuples for custom replacements
        **kwargs: Additional keyword arguments (ignored)
    
    Returns:
        The slugified string
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Apply custom replacements first
    if replacements:
        for old, new in replacements:
            text = text.replace(old, new)
    
    # Lowercase if requested
    if lowercase:
        text = text.lower()
    
    # Handle unicode
    if not allow_unicode:
        # Try to transliterate first
        text = _transliterate(text)
        # Remove remaining accents
        text = _remove_accents(text)
        # Remove any remaining non-ASCII characters
        text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Apply custom regex pattern if provided
    if regex_pattern:
        text = re.sub(regex_pattern, '', text)
    else:
        # Default: keep alphanumeric, unicode letters/numbers, and separator
        if allow_unicode:
            # Keep unicode letters and numbers
            text = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE)
        else:
            # Keep only ASCII alphanumeric
            text = re.sub(r'[^a-z0-9\s-]', '', text)
    
    # Replace whitespace and multiple separators with single separator
    text = re.sub(r'\s+', separator, text)
    text = re.sub(r'[' + re.escape(separator) + r']+', separator, text)
    
    # Strip separator from start and end
    text = text.strip(separator)
    
    # Remove stopwords
    if stopwords:
        words = text.split(separator)
        words = [w for w in words if w.lower() not in stopwords]
        text = separator.join(words)
    
    # Handle max_length with optional word_boundary
    if max_length:
        if word_boundary:
            # Truncate at word boundary
            if len(text) > max_length:
                # Find the last separator before max_length
                truncated = text[:max_length]
                last_sep = truncated.rfind(separator)
                if last_sep > 0:
                    text = truncated[:last_sep]
                else:
                    text = truncated
        else:
            # Simple truncation
            text = text[:max_length]
    
    # Strip separator again in case truncation left trailing separator
    text = text.strip(separator)
    
    return text