import re
import unicodedata


def slugify(
    text,
    allow_unicode=False,
    max_length=None,
    word_boundary=False,
    separator='-',
    regex_pattern=None,
    stopwords=None,
    lowercase=True,
    replacements=None,
    **kwargs
):
    """
    Convert a string to a slug.
    
    Args:
        text: The text to slugify
        allow_unicode: If True, preserve unicode characters in output
        max_length: Maximum length of the slug
        word_boundary: If True, truncate at word boundaries
        separator: Character to use as separator (default: '-')
        regex_pattern: Custom regex pattern to filter characters
        stopwords: List/set of words to remove from slug
        lowercase: If True, convert to lowercase (default: True)
        replacements: List of tuples (old, new) for custom replacements
        **kwargs: Additional arguments (ignored for compatibility)
    
    Returns:
        A slugified string
    """
    if text is None:
        return ''
    
    # Convert to string
    text = str(text)
    
    # Apply custom replacements first if provided
    if replacements:
        for old, new in replacements:
            text = text.replace(old, new)
    
    # Normalize unicode
    if not allow_unicode:
        # Try to transliterate to ASCII
        # NFKD decomposition separates characters into base + combining marks
        text = unicodedata.normalize('NFKD', text)
        # Encode to ASCII, ignoring characters that can't be represented
        text = text.encode('ascii', 'ignore').decode('ascii')
    else:
        # Normalize to NFC for consistent unicode representation
        text = unicodedata.normalize('NFC', text)
    
    # Apply lowercase if requested
    if lowercase:
        text = text.lower()
    
    # Apply custom regex pattern if provided
    if regex_pattern:
        text = re.sub(regex_pattern, '', text)
    
    # Replace various punctuation and whitespace with separator
    # This handles spaces, underscores, and common punctuation
    if allow_unicode:
        # For unicode, be more conservative - keep unicode letters and numbers
        # Replace non-word characters (except unicode letters/numbers) with separator
        text = re.sub(r'[^\w\s-]', separator, text, flags=re.UNICODE)
        text = re.sub(r'[\s_]+', separator, text)
    else:
        # For ASCII-only mode
        # Replace non-alphanumeric characters with separator
        text = re.sub(r'[^\w\s-]', separator, text)
        text = re.sub(r'[\s_]+', separator, text)
    
    # Handle stopwords
    if stopwords:
        # Split by separator to get words
        words = text.split(separator)
        # Filter out stopwords (case-insensitive comparison)
        stopwords_lower = set(w.lower() for w in stopwords)
        words = [w for w in words if w.lower() not in stopwords_lower]
        text = separator.join(words)
    
    # Collapse multiple separators into one
    separator_pattern = re.escape(separator) + '+'
    text = re.sub(separator_pattern, separator, text)
    
    # Remove leading/trailing separators
    text = text.strip(separator)
    
    # Apply max_length truncation
    if max_length is not None and len(text) > max_length:
        if word_boundary:
            # Truncate at word boundary
            text = text[:max_length]
            # Find the last separator within the truncated text
            last_sep = text.rfind(separator)
            if last_sep > 0:
                text = text[:last_sep]
            # Remove trailing separator if any
            text = text.rstrip(separator)
        else:
            # Simple truncation
            text = text[:max_length]
            # Remove trailing separator if truncation cut in the middle
            text = text.rstrip(separator)
    
    return text