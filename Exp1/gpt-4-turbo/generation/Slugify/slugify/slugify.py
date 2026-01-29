import re
import unicodedata

DEFAULT_REGEX_PATTERN = r'[^\w\s-]'
DEFAULT_SEPARATOR = '-'

def _normalize_unicode(text, allow_unicode):
    if allow_unicode:
        # NFKC normalization preserves unicode characters
        return unicodedata.normalize('NFKC', text)
    else:
        # NFKD normalization, then encode to ASCII and decode back
        text = unicodedata.normalize('NFKD', text)
        return text.encode('ascii', 'ignore').decode('ascii')

def _apply_replacements(text, replacements):
    if not replacements:
        return text
    for old, new in replacements:
        text = text.replace(old, new)
    return text

def _remove_stopwords(words, stopwords):
    if not stopwords:
        return words
    stopwords_set = set(sw.lower() for sw in stopwords)
    return [w for w in words if w.lower() not in stopwords_set]

def slugify(
    text,
    allow_unicode=False,
    max_length=None,
    word_boundary=False,
    separator=DEFAULT_SEPARATOR,
    regex_pattern=None,
    stopwords=None,
    lowercase=True,
    replacements=None,
    **kwargs
):
    """
    Generate a slug for the given text.

    Args:
        text (str): Input text.
        allow_unicode (bool): Allow unicode characters in output.
        max_length (int or None): Maximum length of slug.
        word_boundary (bool): Truncate at word boundary if True.
        separator (str): Separator character.
        regex_pattern (str or None): Custom regex pattern for filtering.
        stopwords (list or None): Words to remove from slug.
        lowercase (bool): Lowercase output.
        replacements (list of (str, str) or None): Custom replacements.
        **kwargs: Ignored, for compatibility.

    Returns:
        str: Slugified string.
    """
    if not isinstance(text, str):
        text = str(text)

    # Apply replacements
    text = _apply_replacements(text, replacements)

    # Normalize unicode
    text = _normalize_unicode(text, allow_unicode)

    # Remove unwanted characters using regex
    pattern = regex_pattern if regex_pattern is not None else DEFAULT_REGEX_PATTERN
    text = re.sub(pattern, '', text)

    # Replace whitespace and repeated separators with single separator
    # First, collapse whitespace to single space
    text = re.sub(r'\s+', ' ', text)
    # Then, replace spaces and underscores with separator
    text = re.sub(r'[ _]+', separator, text)

    # Remove leading/trailing separators
    text = text.strip(separator)

    # Lowercase if required
    if lowercase:
        text = text.lower()

    # Split into words for stopwords and word_boundary
    words = text.split(separator) if text else []

    # Remove stopwords
    words = _remove_stopwords(words, stopwords)

    # Remove empty words
    words = [w for w in words if w]

    # Rejoin
    slug = separator.join(words)

    # Truncate if needed
    if max_length is not None and max_length > 0:
        if len(slug) > max_length:
            if word_boundary:
                # Truncate at word boundary
                truncated = []
                total = 0
                for w in words:
                    part = w if truncated == [] else separator + w
                    if total + len(part) > max_length:
                        break
                    truncated.append(w)
                    total += len(part)
                slug = separator.join(truncated)
            else:
                slug = slug[:max_length]
                # Remove trailing separator if cut in the middle
                slug = slug.rstrip(separator)

    return slug