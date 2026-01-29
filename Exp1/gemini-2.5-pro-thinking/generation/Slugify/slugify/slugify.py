import re
import unicodedata

def slugify(text, allow_unicode=False, max_length=None, word_boundary=False,
            separator='-', regex_pattern=None, stopwords=None, lowercase=True,
            replacements=None, **kwargs):
    """
    Generate a slug for a given text.

    This is a pure Python implementation that aims for API compatibility with
    the core features of the python-slugify library.

    :param text: The text to slugify.
    :param allow_unicode: If True, preserves non-ASCII characters.
    :param max_length: If set, truncates the slug to this length.
    :param word_boundary: If True, truncates at a word boundary (separator).
    :param separator: The separator character.
    :param regex_pattern: A custom regex pattern for character filtering.
    :param stopwords: A list of words to remove from the slug.
    :param lowercase: If True, converts the slug to lowercase.
    :param replacements: A list of [('old', 'new'), ...] string replacements.
    :param kwargs: Catches unused arguments for API compatibility.
    :return: The generated slug string.
    """
    text = str(text)

    # 1. Unicode to ASCII transliteration
    if not allow_unicode:
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')

    # 2. Custom replacements
    if replacements:
        for old, new in replacements:
            text = text.replace(old, new)

    # 3. Lowercasing
    if lowercase:
        text = text.lower()

    # 4. Filtering characters
    # If a custom regex is provided, use it to remove characters.
    # Otherwise, use a default pattern to remove invalid characters.
    if regex_pattern:
        text = re.sub(regex_pattern, '', text)
    else:
        # Default: remove characters that are not alphanumeric, whitespace, or hyphens.
        # \w in Python 3's re module handles unicode characters correctly.
        text = re.sub(r'[^\w\s-]', '', text)

    # 5. Collapse whitespace and repeated separators, and strip leading/trailing separators
    text = re.sub(r'[-\s]+', separator, text).strip(separator)

    # 6. Stopword removal
    if stopwords:
        words = text.split(separator)
        # Use a set for efficient lookup.
        # If the main text is lowercased, stopwords should be too for matching.
        if lowercase:
            stopwords_set = {s.lower() for s in stopwords}
        else:
            stopwords_set = set(stopwords)
        words = [w for w in words if w and w not in stopwords_set]
        text = separator.join(words)

    # 7. Truncation
    if max_length and len(text) > max_length:
        if word_boundary:
            # Truncate to max_length first
            truncated_text = text[:max_length]
            # Find the last separator in the truncated string
            last_sep_index = truncated_text.rfind(separator)
            # If a separator is found and it's not at the beginning, truncate there
            if last_sep_index > 0:
                text = truncated_text[:last_sep_index]
            else:
                # If no separator, or it's at the start, hard truncate
                text = truncated_text
        else:
            text = text[:max_length]

    # Final strip of separators that might be left by truncation
    text = text.strip(separator)

    return text