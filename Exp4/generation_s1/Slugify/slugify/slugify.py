import re
import unicodedata
from typing import Iterable, Optional, Sequence, Tuple, Any


# A tiny built-in transliteration supplement for some common characters that
# do not decompose nicely under NFKD->ASCII(ignore).
_EXTRA_TRANSLITERATION = {
    "ß": "ss",
    "ẞ": "SS",
    "æ": "ae",
    "Æ": "AE",
    "ø": "o",
    "Ø": "O",
    "đ": "d",
    "Đ": "D",
    "ł": "l",
    "Ł": "L",
    "ð": "d",
    "Ð": "D",
    "þ": "th",
    "Þ": "Th",
    "œ": "oe",
    "Œ": "OE",
}


def _to_str(text: Any) -> str:
    if text is None:
        return ""
    return str(text)


def _apply_replacements(text: str, replacements: Optional[Iterable[Tuple[str, str]]]) -> str:
    if not replacements:
        return text
    for pair in replacements:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            # Ignore malformed entries for compatibility robustness.
            continue
        src, dst = pair
        text = text.replace(str(src), str(dst))
    return text


def _ascii_transliterate(text: str) -> str:
    if not text:
        return ""
    # Pre-map common characters that aren't handled well by NFKD ASCII ignore.
    # Do this before normalization so the mapping isn't lost.
    if any(ch in _EXTRA_TRANSLITERATION for ch in text):
        text = "".join(_EXTRA_TRANSLITERATION.get(ch, ch) for ch in text)

    # NFKD decomposes accents; ASCII ignore drops remaining non-ascii.
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text


def _normalize_unicode(text: str, allow_unicode: bool) -> str:
    if allow_unicode:
        # Preserve unicode but normalize compatibility forms.
        text = unicodedata.normalize("NFKC", text)
        return text
    return _ascii_transliterate(text)


def _filter_with_regex_pattern(text: str, regex_pattern: Optional[str]) -> str:
    if not regex_pattern:
        return text
    try:
        rx = re.compile(regex_pattern)
    except re.error:
        # If an invalid regex is provided, ignore it for robustness.
        return text
    return rx.sub("", text)


def _chars_to_tokens(text: str, allow_unicode: bool) -> Sequence[str]:
    """
    Convert text to a list of word tokens by turning non-alphanumeric
    characters into whitespace and splitting.
    """
    if not text:
        return []

    out_chars = []
    for ch in text:
        # Keep only letters/numbers. Treat combining marks as separators/removable.
        cat = unicodedata.category(ch)
        if (cat.startswith("L") or cat.startswith("N")):
            out_chars.append(ch)
        else:
            # Convert any non-letter/number to a space boundary.
            out_chars.append(" ")

    cleaned = "".join(out_chars)
    # Collapse whitespace and split.
    return [t for t in cleaned.split() if t]


def _apply_stopwords(tokens: Sequence[str], stopwords: Optional[Iterable[str]], lowercase: bool) -> Sequence[str]:
    if not stopwords:
        return list(tokens)

    # Reference behavior is effectively case-insensitive for typical usage.
    sw = {str(s).casefold() for s in stopwords if s is not None}

    if not sw:
        return list(tokens)

    kept = []
    for tok in tokens:
        key = tok.casefold()
        if key in sw:
            continue
        kept.append(tok)
    return kept


def _coerce_separator(separator: str) -> str:
    sep = "-" if separator is None else str(separator)
    # Avoid whitespace separators (ambiguous in slug output) and empty separators.
    if not sep or any(ch.isspace() for ch in sep):
        return "-"
    return sep


def _truncate(slug: str, max_length: Optional[int], word_boundary: bool, separator: str) -> str:
    if max_length is None:
        return slug

    try:
        ml = int(max_length)
    except (TypeError, ValueError):
        return slug

    if ml <= 0:
        return ""

    if len(slug) <= ml:
        return slug

    if not word_boundary:
        cut = slug[:ml]
        # Strip trailing separator(s) if we cut on a boundary.
        while cut.endswith(separator):
            cut = cut[: -len(separator)]
        return cut

    # Word boundary truncation: don't cut within a token.
    prefix = slug[:ml]
    if separator not in prefix:
        # First token longer than max_length: strict word boundary => empty.
        return ""
    cut = prefix.rsplit(separator, 1)[0]
    while cut.endswith(separator):
        cut = cut[: -len(separator)]
    return cut


def slugify(
    text: Any,
    allow_unicode: bool = False,
    max_length: Optional[int] = None,
    word_boundary: bool = False,
    separator: str = "-",
    regex_pattern: Optional[str] = None,
    stopwords: Optional[Iterable[str]] = None,
    lowercase: bool = True,
    replacements: Optional[Iterable[Tuple[str, str]]] = None,
    **kwargs,
) -> str:
    """
    Generate a URL-friendly slug.

    This is a pure-Python implementation intended to be compatible with the
    core API of `python-slugify` as used by the benchmark tests.
    Unknown kwargs are accepted and ignored for compatibility.
    """
    _ = kwargs  # intentionally ignored

    s = _to_str(text)
    if not s:
        return ""

    sep = _coerce_separator(separator)

    # Pre replacements (string-level).
    s = _apply_replacements(s, replacements)

    # Unicode normalization / ASCII transliteration.
    s = _normalize_unicode(s, allow_unicode=allow_unicode)

    # Optional regex-based pre-filtering.
    s = _filter_with_regex_pattern(s, regex_pattern)

    # Case folding (do after normalization/transliteration).
    if lowercase:
        s = s.lower()

    # Tokenize by mapping punctuation/whitespace to boundaries.
    tokens = _chars_to_tokens(s, allow_unicode=allow_unicode)

    # Remove stopwords after tokenization.
    tokens = _apply_stopwords(tokens, stopwords, lowercase=lowercase)

    if not tokens:
        return ""

    out = sep.join(tokens)

    # Apply max length truncation rules.
    out = _truncate(out, max_length=max_length, word_boundary=word_boundary, separator=sep)

    return out