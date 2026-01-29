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
    Slugify a given text.
    """
    if text is None:
        return ""

    # Ensure text is a string
    text = str(text)

    # Replacements
    if replacements:
        for old, new in replacements:
            text = text.replace(old, new)

    # Normalize
    if allow_unicode:
        text = unicodedata.normalize('NFKC', text)
    else:
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')

    # Lowercase
    if lowercase:
        text = text.lower()

    # Regex filtering
    if regex_pattern is None:
        if allow_unicode:
            pattern = r'[^\w\s-]'
        else:
            pattern = r'[^\w\s-]'
    else:
        pattern = regex_pattern

    # Remove unwanted characters
    text = re.sub(pattern, '', text)

    # Collapse whitespace and separators
    if separator:
        sep_esc = re.escape(separator)
        text = re.sub(r'[\s' + sep_esc + r']+', separator, text)
        text = text.strip(separator)
    else:
        text = re.sub(r'\s+', '', text)

    # Stopwords
    if stopwords:
        if separator:
            words = text.split(separator)
            if lowercase:
                stopwords_lower = {s.lower() for s in stopwords}
                words = [w for w in words if w not in stopwords_lower]
            else:
                stopwords_set = set(stopwords)
                words = [w for w in words if w not in stopwords_set]
            text = separator.join(words)

    # Max length
    if max_length is not None and max_length > 0:
        if len(text) > max_length:
            text = text[:max_length]
            
            if separator:
                text = text.strip(separator)
                
            if word_boundary and separator:
                splits = text.rsplit(separator, 1)
                if len(splits) == 2:
                    text = splits[0]

    return text