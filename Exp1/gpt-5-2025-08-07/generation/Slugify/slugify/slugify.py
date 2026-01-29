import re
import unicodedata
from typing import Iterable, List, Optional, Sequence, Tuple, Union


Replacement = Union[Sequence[Tuple[str, str]], dict]


def _apply_replacements(text: str, replacements: Optional[Replacement]) -> str:
    if not replacements:
        return text
    if isinstance(replacements, dict):
        items = replacements.items()
    else:
        items = replacements
    for old, new in items:
        # ensure strings
        old = str(old)
        new = str(new)
        if not old:
            continue
        text = text.replace(old, new)
    return text


def _normalize_text(
    text: str, allow_unicode: bool, lowercase: bool
) -> str:
    if allow_unicode:
        # NFKC to compose characters and canonicalize forms
        text = unicodedata.normalize("NFKC", text)
    else:
        # NFKD then ASCII-encode to strip accents and non-ascii
        text = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    if lowercase:
        text = text.lower()
    return text


def _collapse_to_separator(text: str, separator: str) -> str:
    # Replace any run of non-word characters or underscores with the separator.
    # \W matches anything other than letters, digits, and underscore; we add
    # underscore to ensure it is treated as a separator as well.
    # Use UNICODE semantics by default in Python 3.
    text = re.sub(r"[\W_]+", separator, text, flags=re.UNICODE)
    # Trim leading/trailing separators
    if separator:
        text = text.strip(separator)
    else:
        # If separator is empty string, nothing to strip; also collapse may have
        # produced empty strings between tokens, but joining will handle later.
        text = text.strip()
    return text


def _remove_stopwords(slug: str, stopwords: Optional[Iterable[str]], separator: str) -> str:
    if not stopwords or slug == "":
        return slug
    try:
        stop_set = {s.casefold() for s in stopwords}
    except TypeError:
        # stopwords not iterable
        return slug
    # split by the exact separator
    if separator:
        parts = slug.split(separator)
    else:
        # If separator is empty string, splitting is ambiguous; fallback to
        # splitting on whitespace.
        parts = slug.split()
    filtered: List[str] = []
    for token in parts:
        if not token:
            continue
        if token.casefold() in stop_set:
            continue
        filtered.append(token)
    if separator:
        return separator.join(filtered)
    else:
        return "".join(filtered)


def _truncate(slug: str, max_length: Optional[int], word_boundary: bool, separator: str) -> str:
    if max_length is None:
        return slug
    try:
        max_len = int(max_length)
    except (TypeError, ValueError):
        return slug
    if max_len < 0:
        return ""
    if len(slug) <= max_len:
        return slug
    if not word_boundary:
        trimmed = slug[:max_len]
        if separator:
            trimmed = trimmed.strip(separator)
        else:
            trimmed = trimmed.strip()
        return trimmed
    # word boundary: try to cut at the last separator not exceeding max_len
    if separator:
        cut = slug.rfind(separator, 0, max_len)
    else:
        # if separator is empty, there's no boundary concept; fallback to direct cut
        cut = -1
    if cut == -1:
        trimmed = slug[:max_len]
    else:
        trimmed = slug[:cut]
    if separator:
        trimmed = trimmed.strip(separator)
    else:
        trimmed = trimmed.strip()
    return trimmed


def slugify(
    text: Optional[object],
    allow_unicode: bool = False,
    max_length: Optional[int] = None,
    word_boundary: bool = False,
    separator: str = "-",
    regex_pattern: Optional[Union[str, "re.Pattern[str]"]] = None,
    stopwords: Optional[Iterable[str]] = None,
    lowercase: bool = True,
    replacements: Optional[Replacement] = None,
    **kwargs,
) -> str:
    """
    Create a slug from given text.

    Parameters:
    - text: input text to slugify.
    - allow_unicode: if True, preserve unicode letters/digits; otherwise, try to
      convert to ASCII and drop others.
    - max_length: if provided, limit the length of the resulting slug.
    - word_boundary: if True and max_length is set, truncate at the last complete
      word that fits within max_length (uses the separator as the boundary).
    - separator: string used to separate words in the slug (default "-").
    - regex_pattern: optional regex pattern; characters matching this pattern
      are removed before separator normalization.
    - stopwords: iterable of words to exclude from the slug.
    - lowercase: whether to lowercase the result automatically.
    - replacements: optional dict or sequence of (old, new) pairs applied before
      other processing.

    Returns:
    - A slug string.
    """
    if text is None:
        return ""
    # Convert to string early
    value = str(text)

    # Apply user replacements first
    value = _apply_replacements(value, replacements)

    # Normalize unicode/ASCII and lowercase if requested
    value = _normalize_text(value, allow_unicode=allow_unicode, lowercase=lowercase)

    # Remove characters according to custom regex_pattern if provided
    if regex_pattern:
        pattern = re.compile(regex_pattern) if isinstance(regex_pattern, str) else regex_pattern
        value = pattern.sub("", value)

    # Normalize any remaining punctuation/whitespace to the chosen separator
    sep = str(separator)
    value = _collapse_to_separator(value, sep)

    # Remove stopwords if provided
    value = _remove_stopwords(value, stopwords, sep)

    # Remove any accidental multiple separators after stopwords removal
    if sep:
        if len(sep) == 1:
            # Efficient collapse for single-char separators
            multi_sep_pattern = re.escape(sep) + r"{2,}"
            value = re.sub(multi_sep_pattern, sep, value)
        else:
            # For multi-character separators, collapse repeated occurrences
            # e.g., "word||word" with "||" as separator.
            value = re.sub("(" + re.escape(sep) + r"){2,}", sep, value)
        value = value.strip(sep)
    else:
        value = value.strip()

    # Truncate by max_length with optional word boundary control
    value = _truncate(value, max_length, word_boundary, sep)

    return value