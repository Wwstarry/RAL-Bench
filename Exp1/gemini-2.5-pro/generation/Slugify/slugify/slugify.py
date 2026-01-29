import re
import unicodedata

def slugify(text, allow_unicode=False, max_length=None, word_boundary=False,
            separator='-', regex_pattern=None, stopwords=None,
            lowercase=True, replacements=None, **kwargs):
    """
    Generate a slug for a given text.

    This function is designed to be API-compatible with the core features of
    the python-slugify library.

    Args:
        text (str): The text to slugify.
        allow_unicode (bool): If True, allows unicode characters in the slug.
                              Defaults to False.
        max_length (int, optional): The maximum length of the output slug.
                                    If None, there is no limit. Defaults to None.
        word_boundary (bool): If True and max_length is set, truncates the slug
                              at the last full word. Defaults to False.
        separator (str): The separator to use between words. Defaults to '-'.
        regex_pattern (str, optional): A custom regex pattern for characters to
                                       remove. Defaults to None.
        stopwords (iterable, optional): A list or set of words to remove from
                                        the slug. Defaults to None.
        lowercase (bool): If True, converts the slug to lowercase. Defaults to True.
        replacements (list of tuples, optional): A list of (from, to) tuples
                                                 for custom string replacements.
                                                 Defaults to None.
        **kwargs: Catches any other keyword arguments for compatibility.

    Returns:
        str: The generated slug.
    """
    if text is None:
        return ""

    # 1. Initial conversions and replacements
    text = str(text)

    if replacements:
        for old, new in replacements:
            text = text.replace(old, new)

    # 2. Unicode normalization
    text = unicodedata.normalize('NFKD', text)
    if not allow_unicode:
        text = text.encode('ascii', 'ignore').decode('ascii')

    if lowercase:
        text = text.lower()

    # 3. Character filtering and separator consolidation
    # The default pattern [^\w\s-] removes anything that's not a word character,
    # whitespace, or a hyphen.
    # Custom regex_pattern is used to remove characters.
    text = re.sub(regex_pattern or r'[^\w\s-]', '', text).strip()

    # Condense whitespace and hyphens into a single separator
    slug = re.sub(r'[-\s]+', separator, text)

    # 4. Stopword removal
    if stopwords:
        words = slug.split(separator)
        # Filter out empty strings that can occur with leading/trailing separators
        # and the stopwords themselves.
        filtered_words = [w for w in words if w and w not in stopwords]
        slug = separator.join(filtered_words)

    # 5. Truncation
    if max_length and len(slug) > max_length:
        if word_boundary:
            # Truncate to max_length to get a starting point
            truncated_slug = slug[:max_length]
            # Find the last separator in the truncated string
            last_separator_index = truncated_slug.rfind(separator)
            # Truncate at the separator if found and it's not the first character
            if last_separator_index > 0:
                slug = truncated_slug[:last_separator_index]
            else:
                # If no separator, hard truncate (already done by [:max_length])
                slug = truncated_slug
        else:
            # Hard truncate
            slug = slug[:max_length]

    # 6. Final cleanup
    # In case truncation or other operations leave a trailing separator
    slug = slug.strip(separator)

    return slug