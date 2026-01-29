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

    Parameters:
        text (str): The input text to slugify.
        allow_unicode (bool): Whether to allow Unicode characters in the slug.
        max_length (int): Maximum length of the slug.
        word_boundary (bool): Ensure truncation happens at word boundaries.
        separator (str): Separator to use for the slug.
        regex_pattern (str): Custom regex pattern for filtering characters.
        stopwords (list): Words to exclude from the slug.
        lowercase (bool): Whether to convert the slug to lowercase.
        replacements (list): List of (search, replace) tuples for custom replacements.

    Returns:
        str: The generated slug.
    """
    if not isinstance(text, str):
        raise TypeError("Input text must be a string.")

    # Apply custom replacements if provided
    if replacements:
        for search, replace in replacements:
            text = text.replace(search, replace)

    # Normalize text to NFKD form for consistent processing
    if not allow_unicode:
        text = unicodedata.normalize('NFKD').encode('ascii', 'ignore').decode('ascii')
    else:
        text = unicodedata.normalize('NFKC', text)

    # Convert to lowercase if required
    if lowercase:
        text = text.lower()

    # Remove stopwords if provided
    if stopwords:
        words = text.split()
        text = ' '.join(word for word in words if word not in stopwords)

    # Apply custom regex pattern if provided
    if regex_pattern:
        text = re.sub(regex_pattern, '', text)
    else:
        # Default pattern: keep alphanumeric characters and separators
        text = re.sub(r'[^\w\s-]', '', text)

    # Replace whitespace and dashes with the separator
    text = re.sub(r'[-\s]+', separator, text).strip(separator)

    # Truncate to max_length if specified
    if max_length is not None and len(text) > max_length:
        if word_boundary:
            # Truncate at the nearest word boundary
            truncated = text[:max_length]
            if separator in truncated:
                text = truncated[:truncated.rfind(separator)]
            else:
                text = truncated
        else:
            # Truncate without considering word boundaries
            text = text[:max_length]

    return text