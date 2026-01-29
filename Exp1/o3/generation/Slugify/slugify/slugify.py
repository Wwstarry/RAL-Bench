"""
slugify.slugify
==============

A compact, pure-Python implementation of the most frequently used parts
of the `python-slugify` API.  It is **not** a full drop-in replacement,
but supports the flags exercised by the accompanying test-suite:

    * allow_unicode
    * max_length
    * word_boundary
    * separator
    * regex_pattern
    * stopwords
    * lowercase
    * replacements

The behaviour is intentionally aligned with the reference
`python-slugify` project where it matters for the tests while avoiding
external dependencies such as `Unidecode`.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Collection, Dict, Iterable, List, Pattern, Tuple


__all__ = ["slugify"]

# ---------------------------------------------------------------------------.
# Helper routines
# ---------------------------------------------------------------------------.


def _default_regex(allow_unicode: bool) -> Pattern[str]:
    """
    Return a compiled regular expression that matches *invalid* slug
    characters.  Characters matched by this pattern will be **removed**.
    """
    if allow_unicode:
        # Keep letters/numbers/underscore, whitespace and separator '-'.
        pattern = r"[^\w\s-]"
    else:
        # Same pattern – we have already stripped non ASCII chars when
        # ``allow_unicode`` is False, so this is sufficient.
        pattern = r"[^\w\s-]"
    return re.compile(pattern, flags=re.U)


def _apply_replacements(text: str, replacements: Iterable[Tuple[str, str]]) -> str:
    """
    Apply replacement tuples/dicts in the given order.
    """
    for old, new in replacements:
        if old:
            text = text.replace(old, new)
    return text


def _prepare_replacements(
    replacements: "None | Dict[str, str] | Iterable[Tuple[str, str]]"
) -> List[Tuple[str, str]]:
    """
    Normalise user supplied ``replacements`` to a list[tuple[str, str]].
    """
    if replacements is None:
        return []

    if isinstance(replacements, dict):
        return list(replacements.items())

    # Assume it is already an iterable of two-tuples
    prepared: List[Tuple[str, str]] = []
    for pair in replacements:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(
                "Each replacement must be a 2-tuple or you may provide "
                "a mapping of {old: new}."
            )
        prepared.append((pair[0], pair[1]))
    return prepared


def _truncate(
    slug: str, max_length: int, word_boundary: bool, separator: str
) -> str:
    """
    Truncate *slug* to *max_length* characters.

    If *word_boundary* is truthy we try to break on word separators
    instead of blindly cutting off in the middle of a word.
    """
    if max_length is None or max_length <= 0:
        return slug

    if len(slug) <= max_length:
        return slug

    if word_boundary:
        words = slug.split(separator)
        truncated = ""

        for word in words:
            if truncated:
                candidate = truncated + separator + word
            else:
                candidate = word

            if len(candidate) > max_length:
                break
            truncated = candidate

        if truncated:
            return truncated

    # Fallback: hard cut
    return slug[:max_length].rstrip(separator)


def slugify(  # noqa: C901 – complexity is acceptable for the task
    text: str | None,
    allow_unicode: bool = False,
    max_length: int | None = None,
    word_boundary: bool = False,
    separator: str = "-",
    regex_pattern: str | Pattern[str] | None = None,
    stopwords: Collection[str] | None = None,
    lowercase: bool = True,
    replacements: "None | Dict[str, str] | Iterable[Tuple[str, str]]" = None,
    **kwargs,
) -> str:
    """
    Make a slug from *text*.

    The set of options mirrors the subset required by the reference tests.
    All unrecognised *kwargs are ignored so that our implementation stays
    binary compatible with call-sites passing extra parameters supported
    by the full featured `python-slugify` library.
    """
    if text is None:
        return ""

    # -------------------------------------------------------------------.
    # 1. Apply user-supplied string replacements as early as possible.
    # -------------------------------------------------------------------.
    processed = _apply_replacements(text, _prepare_replacements(replacements))

    # -------------------------------------------------------------------.
    # 2. Unicode normalisation / transliteration.
    # -------------------------------------------------------------------.
    if allow_unicode:
        # Keep unicode – just normalise so that visually identical
        # characters end up with the same code points.
        processed = unicodedata.normalize("NFKC", processed)
    else:
        # Decompose combined chars and drop everything not representable
        # in ASCII.
        processed = (
            unicodedata.normalize("NFKD", processed)
            .encode("ascii", "ignore")
            .decode("ascii")
        )

    # -------------------------------------------------------------------.
    # 3. Lower-case if requested.
    # -------------------------------------------------------------------.
    if lowercase:
        processed = processed.lower()

    # -------------------------------------------------------------------.
    # 4. Stopwords removal (done on raw text prior to stripping punctuation
    #    so that we can match intuitive 'words').
    # -------------------------------------------------------------------.
    if stopwords:
        stop_set = {sw.lower() if lowercase else sw for sw in stopwords}
        words = processed.split()
        words = [w for w in words if (w.lower() if lowercase else w) not in stop_set]
        processed = " ".join(words)

    # -------------------------------------------------------------------.
    # 5. Strip invalid characters according to regex_pattern.
    # -------------------------------------------------------------------.
    if regex_pattern is None:
        regex = _default_regex(allow_unicode)
    else:
        regex = re.compile(regex_pattern, flags=re.U)
    processed = regex.sub("", processed)

    # -------------------------------------------------------------------.
    # 6. Replace any whitespace or repeated separators by single space
    #    (we'll swap them for `separator` later).
    # -------------------------------------------------------------------.
    processed = re.sub(r"[\s\-]+", " ", processed).strip()

    # -------------------------------------------------------------------.
    # 7. Collapse spaces into the requested separator.
    # -------------------------------------------------------------------.
    if processed:
        slug = re.sub(r"\s+", separator, processed)
    else:
        slug = ""

    # Ensure we don't leave repeated separators (may occur due to user-
    # supplied replacements that contain the separator).
    if slug and separator:
        sep_re = re.escape(separator)
        slug = re.sub(f"{sep_re}{{2,}}", separator, slug).strip(separator)

    # -------------------------------------------------------------------.
    # 8. Handle max_length / word_boundary truncation.
    # -------------------------------------------------------------------.
    if max_length is not None:
        slug = _truncate(slug, max_length, word_boundary, separator)

    return slug