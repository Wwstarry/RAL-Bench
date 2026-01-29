"""
Slugify module
"""

import re
import unicodedata
import sys
from typing import Optional, List, Tuple, Dict, Any, Union

# Default stopwords - common English words to remove
DEFAULT_STOPWORDS = frozenset([
    'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to',
    'from', 'by', 'in', 'of', 'off', 'with', 'as', 'into', 'onto', 'upon'
])

# Common character replacements
DEFAULT_REPLACEMENTS = [
    ('&', ' and '),
    ('+', ' plus '),
    ('%', ' percent '),
    ('@', ' at '),
    ('©', ' copyright '),
    ('®', ' registered '),
    ('™', ' trademark '),
]

# Unicode character transliterations
UNICODE_TRANSLITERATIONS = {
    # Latin characters with diacritics
    'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A',
    'Æ': 'AE', 'Ç': 'C', 'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
    'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I', 'Ð': 'D', 'Ñ': 'N',
    'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O', 'Ø': 'O',
    'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U', 'Ý': 'Y', 'Þ': 'TH',
    'ß': 'ss', 'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
    'å': 'a', 'æ': 'ae', 'ç': 'c', 'è': 'e', 'é': 'e', 'ê': 'e',
    'ë': 'e', 'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i', 'ð': 'd',
    'ñ': 'n', 'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
    'ø': 'o', 'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u', 'ý': 'y',
    'þ': 'th', 'ÿ': 'y',
    
    # Greek characters
    'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z',
    'η': 'h', 'θ': 'th', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm',
    'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's',
    'τ': 't', 'υ': 'y', 'φ': 'ph', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
    'ά': 'a', 'έ': 'e', 'ί': 'i', 'ό': 'o', 'ύ': 'y', 'ή': 'h',
    'ώ': 'o', 'ς': 's',
    
    # Cyrillic characters
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
    'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
    'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
    'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
    'э': 'e', 'ю': 'yu', 'я': 'ya',
    
    # Other common symbols
    '№': ' number ', '°': ' degrees ', '€': ' euro ', '£': ' pound ',
    '$': ' dollar ', '¥': ' yen ', '¢': ' cent ', '§': ' section ',
    '¶': ' paragraph ', '†': ' dagger ', '‡': ' double dagger ',
    '•': ' bullet ', '·': ' dot ', '…': ' ellipsis ', '–': ' dash ',
    '—': ' dash ', '―': ' dash ', '‗': ' underscore ', '′': ' prime ',
    '″': ' double prime ', '‴': ' triple prime ', '‵': ' backprime ',
    '‹': ' less than ', '›': ' greater than ', '«': ' left guillemet ',
    '»': ' right guillemet ', '‐': ' hyphen ', '‑': ' non-breaking hyphen ',
    '‒': ' figure dash ', '―': ' horizontal bar ', '‖': ' double vertical line ',
    '‗': ' low line ', '‘': ' left single quotation mark ',
    '’': ' right single quotation mark ', '‚': ' single low-9 quotation mark ',
    '‛': ' single high-reversed-9 quotation mark ', '“': ' left double quotation mark ',
    '”': ' right double quotation mark ', '„': ' double low-9 quotation mark ',
    '‟': ' double high-reversed-9 quotation mark ', '†': ' dagger ',
    '‡': ' double dagger ', '•': ' bullet ', '‣': ' triangular bullet ',
    '․': ' one dot leader ', '‥': ' two dot leader ', '…': ' horizontal ellipsis ',
    '‧': ' hyphenation point ', '‰': ' per mille ', '‱': ' per ten thousand ',
    '′': ' prime ', '″': ' double prime ', '‴': ' triple prime ',
    '‵': ' reversed prime ', '‶': ' reversed double prime ',
    '‷': ' reversed triple prime ', '‸': ' caret ', '‹': ' single left-pointing angle quotation mark ',
    '›': ' single right-pointing angle quotation mark ', '※': ' reference mark ',
    '‼': ' double exclamation mark ', '‽': ' interrobang ', '‾': ' overline ',
    '⁀': ' caret insertion point ', '⁁': ' caret insertion point ',
    '⁂': ' asterism ', '⁃': ' hyphen bullet ', '⁄': ' fraction slash ',
    '⁅': ' left square bracket with quill ', '⁆': ' right square bracket with quill ',
    '⁇': ' double question mark ', '⁈': ' question exclamation mark ',
    '⁉': ' exclamation question mark ', '⁊': ' turned ampersand ',
    '⁋': ' reversed pilcrow sign ', '⁌': ' black leftwards bullet ',
    '⁍': ' black rightwards bullet ', '⁎': ' low asterisk ',
    '⁏': ' reversed semicolon ', '⁐': ' close up ', '⁑': ' two asterisks aligned vertically ',
    '⁒': ' commercial minus sign ', '⁓': ' swung dash ', '⁔': ' inverted undertie ',
    '⁕': ' flower punctuation mark ', '⁖': ' three dot punctuation ',
    '⁗': ' quadruple prime ', '⁘': ' four dot punctuation ', '⁙': ' five dot punctuation ',
    '⁚': ' two dot punctuation ', '⁛': ' four dot mark ', '⁜': ' dotted cross ',
    '⁝': ' tricolon ', '⁞': ' vertical four dots ',
}


def _transliterate_char(char: str, allow_unicode: bool = False) -> str:
    """Transliterate a single character to ASCII if possible."""
    if allow_unicode:
        return char
    
    # Try to find a direct transliteration
    if char in UNICODE_TRANSLITERATIONS:
        return UNICODE_TRANSLITERATIONS[char]
    
    # Try to decompose and remove diacritics
    try:
        # Normalize to NFKD form (decompose characters with diacritics)
        normalized = unicodedata.normalize('NFKD', char)
        # Remove combining characters (diacritics)
        stripped = ''.join(c for c in normalized if not unicodedata.combining(c))
        if stripped and stripped.isascii():
            return stripped
    except:
        pass
    
    # If we can't transliterate, return empty string for non-ASCII
    if not char.isascii():
        return ''
    
    return char


def _apply_replacements(text: str, replacements: Optional[List[Tuple[str, str]]] = None) -> str:
    """Apply custom character replacements."""
    if replacements is None:
        replacements = DEFAULT_REPLACEMENTS
    
    for old, new in replacements:
        text = text.replace(old, new)
    
    return text


def _remove_stopwords(words: List[str], stopwords: Optional[List[str]] = None) -> List[str]:
    """Remove stopwords from the list of words."""
    if stopwords is None:
        stopwords = DEFAULT_STOPWORDS
    elif isinstance(stopwords, (list, tuple, set)):
        stopwords = frozenset(stopwords)
    
    return [word for word in words if word.lower() not in stopwords]


def _truncate_slug(slug: str, max_length: Optional[int] = None, 
                   word_boundary: bool = False, separator: str = '-') -> str:
    """Truncate slug to max_length, respecting word boundaries if requested."""
    if max_length is None or len(slug) <= max_length:
        return slug
    
    if not word_boundary:
        return slug[:max_length]
    
    # Find the last separator before max_length
    truncated = slug[:max_length]
    last_separator = truncated.rfind(separator)
    
    if last_separator > 0:
        return truncated[:last_separator]
    
    # If no separator found, just truncate
    return truncated


def slugify(
    text: str,
    allow_unicode: bool = False,
    max_length: Optional[int] = None,
    word_boundary: bool = False,
    separator: str = '-',
    regex_pattern: Optional[str] = None,
    stopwords: Optional[List[str]] = None,
    lowercase: bool = True,
    replacements: Optional[List[Tuple[str, str]]] = None,
    **kwargs: Any
) -> str:
    """
    Convert a string to a URL-friendly slug.
    
    Args:
        text: The text to convert to a slug.
        allow_unicode: If True, allows Unicode characters in the slug.
        max_length: Maximum length of the slug.
        word_boundary: If True, truncate at word boundaries when max_length is exceeded.
        separator: Character to use as word separator.
        regex_pattern: Custom regex pattern for character filtering.
        stopwords: List of words to remove from the slug.
        lowercase: If True, convert to lowercase.
        replacements: List of (old, new) character replacements.
        **kwargs: Additional keyword arguments (ignored for compatibility).
    
    Returns:
        A URL-friendly slug string.
    """
    if text is None:
        return ''
    
    # Convert to string if not already
    text = str(text)
    
    # Apply custom replacements
    text = _apply_replacements(text, replacements)
    
    # Transliterate characters
    transliterated_chars = []
    for char in text:
        transliterated = _transliterate_char(char, allow_unicode)
        transliterated_chars.append(transliterated)
    
    text = ''.join(transliterated_chars)
    
    # Apply custom regex pattern if provided
    if regex_pattern is not None:
        text = re.sub(regex_pattern, '', text)
    
    # Convert to lowercase if requested
    if lowercase:
        text = text.lower()
    
    # Replace non-alphanumeric characters with separator
    # Keep alphanumeric characters and the separator itself
    pattern = r'[^\w\s' + re.escape(separator) + ']'
    text = re.sub(pattern, ' ', text)
    
    # Replace whitespace with separator
    text = re.sub(r'\s+', separator, text.strip())
    
    # Remove leading/trailing separators
    text = text.strip(separator)
    
    # Split into words for stopword removal
    words = [word for word in text.split(separator) if word]
    
    # Remove stopwords
    if stopwords is not None:
        words = _remove_stopwords(words, stopwords)
    
    # Join words back with separator
    slug = separator.join(words)
    
    # Truncate if needed
    if max_length is not None:
        slug = _truncate_slug(slug, max_length, word_boundary, separator)
    
    return slug