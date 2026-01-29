import re
import unicodedata


def slugify(text, allow_unicode=False, max_length=None, word_boundary=False,
            separator='-', regex_pattern=None, stopwords=None, lowercase=True,
            replacements=None, **kwargs):
    """
    Convert text to a slug.

    Parameters:
    - text: The string to convert
    - allow_unicode: Whether to allow non-ASCII characters in the slug
    - max_length: Maximum length of the slug
    - word_boundary: Whether to truncate at word boundaries when using max_length
    - separator: Character to replace whitespace and punctuation with
    - regex_pattern: Custom regex pattern to filter characters
    - stopwords: List of words to remove from the slug
    - lowercase: Whether to convert the slug to lowercase
    - replacements: Dictionary of {str: str} to replace before slugifying

    Returns:
    A slugified string.
    """
    if text is None:
        return ''

    text = str(text)

    # Apply custom replacements first if provided
    if replacements:
        for old, new in replacements.items():
            text = text.replace(old, new)

    # Convert to lowercase if requested
    if lowercase:
        text = text.lower()

    # Normalize unicode characters
    if allow_unicode:
        # For unicode mode, normalize but keep the characters
        text = unicodedata.normalize('NFKC', text)
    else:
        # Convert to ASCII, removing non-ASCII chars
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        text = ''.join([c for c in text if ord(c) < 128])

    # Remove stopwords if provided
    if stopwords:
        words = text.split()
        text = ' '.join(word for word in words if word.lower() not in stopwords)

    # Apply regex pattern for character filtering
    if regex_pattern:
        text = re.sub(regex_pattern, '', text)
    else:
        # Replace non-alphanumeric characters with spaces
        if allow_unicode:
            text = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE)
        else:
            text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)

    # Replace whitespace and repeated separators with a single separator
    text = re.sub(r'[-\s]+', separator, text.strip())
    
    # Remove leading/trailing separators
    text = text.strip(separator)

    # Truncate to max_length if specified
    if max_length and len(text) > max_length:
        if word_boundary and separator in text[:max_length]:
            # If word_boundary is True, truncate at the last word boundary
            # before or at max_length
            text = text[:max_length]
            if separator in text:
                text = text.rsplit(separator, 1)[0]
        else:
            # Simple truncation at max_length
            text = text[:max_length]

    return text