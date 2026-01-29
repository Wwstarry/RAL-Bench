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
    Generate an ASCII-only slug or a unicode slug from the given text.

    Parameters
    ----------
    text : str
        Text to slugify.
    allow_unicode : bool, optional
        Whether to allow unicode characters in the slug. Defaults to False.
    max_length : int or None, optional
        Maximum length of the slug. If set, slug will be truncated.
    word_boundary : bool, optional
        If True and max_length is set, truncate at the last separator before max_length.
    separator : str, optional
        Separator character to use in the slug. Defaults to '-'.
    regex_pattern : str or None, optional
        Custom regex pattern to filter characters. Defaults to None.
    stopwords : iterable or None, optional
        Words to exclude from the slug. Defaults to None.
    lowercase : bool, optional
        Whether to lowercase the slug. Defaults to True.
    replacements : dict or None, optional
        Custom replacements to apply before slugification. Defaults to None.
    **kwargs
        Additional keyword arguments (ignored).

    Returns
    -------
    str
        The slugified string.
    """
    if not isinstance(text, str):
        text = str(text)

    # Apply custom replacements first
    if replacements:
        for search, replace in replacements.items():
            text = text.replace(search, replace)

    # Normalize whitespace and separators
    # Replace all whitespace and punctuation with separator
    # We will build a regex pattern for characters to replace by separator

    # Default regex pattern to keep letters, numbers, and allowed unicode if allow_unicode
    if regex_pattern is not None:
        pattern = re.compile(regex_pattern)
    else:
        if allow_unicode:
            # Keep letters, numbers, marks, connector punctuations, and dash punctuations
            # Unicode categories: L (letter), N (number), M (mark), Pc (connector punct), Pd (dash punct)
            # We will remove anything not matching these categories or separator
            # But we will normalize spaces and punctuation to separator later
            # So here we just remove unwanted characters
            pattern = re.compile(r'[^\w\s\p{L}\p{N}\p{M}\p{Pc}\p{Pd}]', re.UNICODE)
            # Python's re does not support \p{} syntax, so we need to do differently
            # Instead, we will remove characters that are not letters, numbers, marks, connector punct, dash punct, whitespace
            # We'll do this by filtering characters manually below
            pass
        else:
            # ASCII only: keep a-z, A-Z, 0-9, whitespace and separator
            # We will remove anything not ascii letter, digit, whitespace or separator
            # But we will normalize punctuation to separator later
            pattern = None

    # Normalize unicode to NFKD form
    text = unicodedata.normalize('NFKD', text)

    # Remove accents if not allow_unicode
    if not allow_unicode:
        # Encode to ASCII bytes, ignore errors, decode back to str
        text = text.encode('ascii', 'ignore').decode('ascii')

    # Lowercase if requested
    if lowercase:
        text = text.lower()

    # Remove stopwords if any
    if stopwords:
        # Build a set of stopwords in lowercase if lowercase is True
        stopwords_set = set(word.lower() if lowercase else word for word in stopwords)
        # Split text into words by whitespace
        words = text.split()
        # Filter out stopwords
        words = [w for w in words if w not in stopwords_set]
        text = ' '.join(words)

    # Replace all whitespace and punctuation with separator
    # We consider whitespace and all punctuation characters as separator candidates

    # Define a function to replace runs of whitespace or punctuation with separator
    def replace_separators(s):
        # We will replace any run of characters that are not alphanumeric or allowed unicode letters/numbers with separator
        # For allow_unicode, keep letters and numbers, marks, connector punctuations, dash punctuations
        # For ASCII, keep a-z, 0-9 only

        if allow_unicode:
            # We will keep characters that are letters, numbers, marks, connector punctuations, dash punctuations
            # For others, replace with separator
            result = []
            prev_was_sep = False
            for ch in s:
                cat = unicodedata.category(ch)
                if (
                    cat.startswith('L') or  # Letter
                    cat.startswith('N') or  # Number
                    cat.startswith('M') or  # Mark
                    cat == 'Pc' or          # Connector punctuation
                    cat == 'Pd'             # Dash punctuation
                ):
                    result.append(ch)
                    prev_was_sep = False
                else:
                    if not prev_was_sep:
                        result.append(separator)
                        prev_was_sep = True
            return ''.join(result)
        else:
            # ASCII only: keep a-z, 0-9
            # Replace anything else with separator
            result = []
            prev_was_sep = False
            for ch in s:
                if ch.isalnum():
                    result.append(ch)
                    prev_was_sep = False
                else:
                    if not prev_was_sep:
                        result.append(separator)
                        prev_was_sep = True
            return ''.join(result)

    text = replace_separators(text)

    # Remove leading and trailing separators
    text = text.strip(separator)

    # Remove multiple separators in a row
    text = re.sub(r'{0}+'.format(re.escape(separator)), separator, text)

    # Apply regex_pattern filtering if provided (overrides default filtering)
    if regex_pattern is not None:
        # Keep only characters matching regex_pattern
        # We will keep characters that match regex_pattern, remove others
        regex = re.compile(regex_pattern)
        filtered = []
        for ch in text:
            if regex.match(ch):
                filtered.append(ch)
            else:
                filtered.append(separator)
        text = ''.join(filtered)
        # Remove multiple separators again
        text = re.sub(r'{0}+'.format(re.escape(separator)), separator, text)
        text = text.strip(separator)

    # Truncate to max_length if set
    if max_length is not None and len(text) > max_length:
        if word_boundary:
            # Truncate at last separator before max_length
            truncated = text[:max_length]
            last_sep = truncated.rfind(separator)
            if last_sep == -1:
                # No separator found, truncate hard
                text = truncated
            else:
                text = truncated[:last_sep]
        else:
            text = text[:max_length]

        # Remove trailing separator if any after truncation
        text = text.rstrip(separator)

    return text