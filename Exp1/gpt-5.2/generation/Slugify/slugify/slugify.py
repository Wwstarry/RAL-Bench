import re
import unicodedata
from typing import Iterable, List, Optional, Sequence, Tuple, Union


_DEFAULT_DISALLOWED_PATTERN = re.compile(r"[^\w\s-]", re.UNICODE)


def _to_str(text):
    if text is None:
        return ""
    if isinstance(text, bytes):
        return text.decode("utf-8", "ignore")
    return str(text)


def _apply_replacements(text: str, replacements: Optional[Sequence[Tuple[str, str]]]) -> str:
    if not replacements:
        return text
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _ascii_transliterate(text: str) -> str:
    # Use NFKD to decompose accents, then drop non-ascii bytes.
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _compile_pattern(regex_pattern: Optional[Union[str, re.Pattern]]) -> Optional[re.Pattern]:
    if regex_pattern is None:
        return None
    if isinstance(regex_pattern, re.Pattern):
        return regex_pattern
    return re.compile(regex_pattern, re.UNICODE)


def _normalize_separators(text: str, separator: str) -> str:
    # Convert any runs of whitespace/dashes/underscores to separator later.
    # Here we just standardize obvious separators to spaces so the regex below
    # can unify them.
    text = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212]+", "-", text)  # unicode dashes -> hyphen
    return text


def _split_words(text: str) -> List[str]:
    # Extract "word" chunks. \w includes letters/digits/underscore in Unicode.
    # Keep it simple: split on whitespace after cleaning.
    parts = text.split()
    return [p for p in parts if p]


def _truncate(slug: str, max_length: int, word_boundary: bool, separator: str) -> str:
    if max_length is None or max_length <= 0:
        return slug
    if len(slug) <= max_length:
        return slug
    if not word_boundary:
        return slug[:max_length].rstrip(separator)
    # Cut at a separator boundary at or before max_length
    cut = slug[:max_length]
    if separator in cut:
        cut = cut.rsplit(separator, 1)[0]
    return cut.rstrip(separator)


def slugify(
    text,
    allow_unicode: bool = False,
    max_length: Optional[int] = None,
    word_boundary: bool = False,
    separator: str = "-",
    regex_pattern: Optional[Union[str, re.Pattern]] = None,
    stopwords: Optional[Iterable[str]] = None,
    lowercase: bool = True,
    replacements: Optional[Sequence[Tuple[str, str]]] = None,
    **kwargs,
) -> str:
    """
    Slugify a text.

    This is a minimal implementation intended to be API-compatible with the
    core parts of python-slugify as used by the test suite.
    """
    text = _to_str(text)

    # Apply user replacements early (matches typical library behavior).
    text = _apply_replacements(text, replacements)

    text = _normalize_separators(text, separator)

    if lowercase:
        text = text.lower()

    if not allow_unicode:
        text = _ascii_transliterate(text)
    else:
        # Normalize to NFC for stable output while keeping unicode
        text = unicodedata.normalize("NFC", text)

    pattern = _compile_pattern(regex_pattern)
    if pattern is None:
        # Remove disallowed punctuation except word chars, whitespace, underscore and dash.
        text = _DEFAULT_DISALLOWED_PATTERN.sub(" ", text)
    else:
        # Custom filtering: remove anything matching the pattern (typical usage in slugify).
        text = pattern.sub(" ", text)

    # Convert underscores to spaces; keep hyphens as separators too.
    text = text.replace("_", " ")

    # Collapse whitespace and hyphens into single separators:
    # First, turn any hyphen runs into spaces so we unify them.
    text = re.sub(r"[-\s]+", " ", text, flags=re.UNICODE).strip()

    # Stopword filtering
    if stopwords:
        sw = {(_to_str(w).lower() if lowercase else _to_str(w)) for w in stopwords}
        words = _split_words(text)
        words = [w for w in words if (w.lower() if lowercase else w) not in sw]
    else:
        words = _split_words(text)

    # Join with desired separator
    slug = separator.join(words)

    # Ensure no duplicate separators (in case of empty words etc.)
    if separator:
        slug = re.sub(re.escape(separator) + r"{2,}", separator, slug).strip(separator)

    # Truncate
    if max_length is not None:
        try:
            ml = int(max_length)
        except Exception:
            ml = None
        if ml is not None:
            slug = _truncate(slug, ml, bool(word_boundary), separator)

    return slug