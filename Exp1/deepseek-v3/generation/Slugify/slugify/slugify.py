import re
import unicodedata
from typing import Optional, List, Union, Pattern

# Common stopwords for various languages
DEFAULT_STOPWORDS = {
    'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 'of', 'on', 
    'or', 'the', 'to', 'with'
}

# Basic transliteration table for common characters
TRANSLITERATION_MAP = {
    # Latin extended
    'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A',
    'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
    'Æ': 'AE', 'æ': 'ae',
    'Ç': 'C', 'ç': 'c',
    'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
    'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
    'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
    'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
    'Ñ': 'N', 'ñ': 'n',
    'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O', 'Ø': 'O',
    'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o', 'ø': 'o',
    'Œ': 'OE', 'œ': 'oe',
    'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
    'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
    'Ý': 'Y', 'ÿ': 'y', 'ý': 'y',
    'ß': 'ss',
    
    # Cyrillic
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    
    # Greek
    'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'E',
    'Θ': 'Th', 'Ι': 'I', 'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X',
    'Ο': 'O', 'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y', 'Φ': 'Ph',
    'Χ': 'Ch', 'Ψ': 'Ps', 'Ω': 'O',
    'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'e',
    'θ': 'th', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x',
    'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'τ': 't', 'υ': 'y', 'φ': 'ph',
    'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
}

def slugify(
    text: str,
    allow_unicode: bool = False,
    max_length: Optional[int] = None,
    word_boundary: bool = False,
    separator: str = '-',
    regex_pattern: Optional[Pattern] = None,
    stopwords: Optional[List[str]] = None,
    lowercase: bool = True,
    replacements: Optional[List[List[str]]] = None,
    **kwargs
) -> str:
    """
    Convert text to a URL-friendly slug.
    
    Args:
        text: Input text to slugify
        allow_unicode: Allow unicode characters in the slug
        max_length: Maximum length of the slug
        word_boundary: Truncate at word boundary when max_length is reached
        separator: Separator character (default: '-')
        regex_pattern: Custom regex pattern for character filtering
        stopwords: List of words to remove from the slug
        lowercase: Convert to lowercase (default: True)
        replacements: List of [pattern, replacement] pairs for custom replacements
        **kwargs: Additional arguments (ignored for compatibility)
    
    Returns:
        Slugified string
    """
    if text is None:
        return ""
    
    # Apply custom replacements first
    if replacements:
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
    
    # Normalize unicode
    text = unicodedata.normalize('NFKC', str(text))
    
    # Handle unicode characters
    if allow_unicode:
        # Keep unicode characters, remove unwanted ones
        text = re.sub(r'[^\w\s\-_]', '', text, flags=re.UNICODE)
    else:
        # Transliterate unicode characters to ASCII
        text = _transliterate_unicode(text)
        # Remove non-ASCII characters
        text = re.sub(r'[^\w\s\-]', '', text)
    
    # Convert to lowercase if requested
    if lowercase:
        text = text.lower()
    
    # Remove stopwords
    if stopwords is not None:
        text = _remove_stopwords(text, stopwords)
    
    # Apply custom regex pattern if provided
    if regex_pattern is not None:
        text = regex_pattern.sub('', text)
    
    # Replace whitespace and punctuation with separator
    text = re.sub(r'[-\s]+', separator, text.strip())
    
    # Remove leading/trailing separators
    text = text.strip(separator)
    
    # Handle max_length with word boundary if requested
    if max_length and len(text) > max_length:
        if word_boundary:
            text = _truncate_at_word_boundary(text, max_length, separator)
        else:
            text = text[:max_length].rstrip(separator)
    
    return text

def _transliterate_unicode(text: str) -> str:
    """Transliterate unicode characters to ASCII equivalents."""
    result = []
    for char in text:
        if char in TRANSLITERATION_MAP:
            result.append(TRANSLITERATION_MAP[char])
        elif ord(char) < 128:
            result.append(char)
        else:
            # Try unicode decomposition
            try:
                decomposed = unicodedata.normalize('NFKD', char)
                # Keep only ASCII characters from decomposition
                ascii_chars = ''.join(c for c in decomposed if ord(c) < 128)
                result.append(ascii_chars if ascii_chars else '')
            except:
                result.append('')
    return ''.join(result)

def _remove_stopwords(text: str, stopwords: List[str]) -> str:
    """Remove stopwords from text."""
    if not stopwords:
        return text
    
    # Create a pattern that matches stopwords as whole words
    stopword_pattern = r'\b(' + '|'.join(re.escape(word) for word in stopwords) + r')\b'
    return re.sub(stopword_pattern, '', text, flags=re.IGNORECASE)

def _truncate_at_word_boundary(text: str, max_length: int, separator: str) -> str:
    """Truncate text at word boundary."""
    if len(text) <= max_length:
        return text
    
    # Find the last separator before max_length
    truncated = text[:max_length]
    last_separator_pos = truncated.rfind(separator)
    
    if last_separator_pos > 0:
        return truncated[:last_separator_pos]
    else:
        # No separator found, truncate at max_length
        return truncated.rstrip(separator)