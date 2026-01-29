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
    Generate a slug for the given text.

    :param text: Input text to slugify.
    :param allow_unicode: If True, non-ASCII characters are preserved.
    :param max_length: If set, truncate the slug to this length.
    :param word_boundary: If True, truncation will occur at the nearest word boundary.
    :param separator: Character used to separate words in the slug.
    :param regex_pattern: A custom pattern (regex) used to replace matched chars with the separator.
    :param stopwords: A list or set of words to remove from the slug.
    :param lowercase: If True, convert the slug to lowercase.
    :param replacements: A list of (old, new) string replacement pairs to apply prior to slugification.
    :param kwargs: Extra arguments (ignored for compatibility).
    :return: Slug string.
    """

    if not isinstance(text, str):
        text = str(text)

    # Apply any custom text replacements
    if replacements:
        for old, new in replacements:
            text = text.replace(old, new)

    # Transliterate to ASCII if not allowing unicode
    if not allow_unicode:
        # Normalize and remove accents/diacritics, then remove any remaining non-ASCII
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')

    # Optionally lowercase
    if lowercase:
        text = text.lower()

    # Remove stopwords if given
    if stopwords:
        # Split on whitespace to remove words
        words = text.split()
        words = [w for w in words if w not in stopwords]
        text = ' '.join(words)

    # Apply regex pattern if supplied
    if regex_pattern:
        # Replace each match with separator
        text = re.sub(regex_pattern, separator, text)
    else:
        # Default pattern: replace any char not word char, not whitespace, not dash with separator
        # If unicode is allowed, \w can include some unicode letters
        if allow_unicode:
            pattern = r'[^\w\s-]'
        else:
            # If not allowing unicode, we've already removed/converted non-ASCII
            pattern = r'[^a-zA-Z0-9\s-]'
        text = re.sub(pattern, separator, text)

    # Replace all kinds of whitespace with the separator
    text = re.sub(r'[\s]+', separator, text)

    # Remove multiple separators
    sep_re = re.escape(separator)
    text = re.sub(r'{0}+'.format(sep_re), separator, text)

    # Strip leading/trailing separator
    text = text.strip(separator)

    # Handle max_length constraint
    if max_length is not None and len(text) > max_length:
        if word_boundary:
            # Find the last separator before or at max_length
            truncated = text[:max_length]
            cut_point = truncated.rfind(separator)
            if cut_point > 0:
                text = truncated[:cut_point]
            else:
                # No separator found, just cut at max_length
                text = truncated
        else:
            text = text[:max_length]

    return text