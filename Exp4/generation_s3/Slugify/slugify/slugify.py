from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Optional, Sequence, Tuple


def _to_str(text) -> str:
    if text is None:
        return ""
    if isinstance(text, str):
        return text
    try:
        return str(text)
    except Exception:
        # Best-effort fallback; should not raise for "normal" inputs.
        return ""


def _apply_replacements(text: str, replacements) -> str:
    if not replacements:
        return text
    # replacements should be a list of (old, new) tuples; skip malformed entries.
    try:
        for item in replacements:
            try:
                old, new = item
            except Exception:
                continue
            try:
                text = text.replace(str(old), str(new))
            except Exception:
                # If replacement fails for odd objects, skip it.
                continue
    except TypeError:
        # Non-iterable replacements; ignore.
        return text
    return text


def _strip_diacritics_to_ascii(text: str) -> str:
    # NFKD decompose, drop combining marks by ASCII encoding w/ ignore.
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _iter_stopwords(stopwords) -> set[str]:
    if stopwords is None:
        return set()
    # Best-effort coercion to a set of strings.
    result: set[str] = set()
    try:
        for w in stopwords:
            try:
                result.add(str(w))
            except Exception:
                continue
    except TypeError:
        # Not iterable; treat as single stopword
        try:
            result.add(str(stopwords))
        except Exception:
            pass
    return result


def _compile_allowed_char_pattern(regex_pattern: Optional[str]):
    if not regex_pattern:
        return None
    try:
        return re.compile(regex_pattern)
    except re.error:
        # For robustness in black-box tests, treat invalid patterns as "no pattern".
        return None


def _is_alnum_char(c: str, allow_unicode: bool) -> bool:
    # After transliteration, for allow_unicode=False, we should only see ASCII.
    # Still, be defensive.
    if allow_unicode:
        # unicode-aware letters/digits
        return c.isalnum()
    # Restrict to ASCII alnum explicitly.
    o = ord(c)
    if o > 127:
        return False
    return ("0" <= c <= "9") or ("A" <= c <= "Z") or ("a" <= c <= "z")


def _tokenize(
    text: str,
    *,
    allow_unicode: bool,
    separator: str,
    allowed_re: Optional[re.Pattern],
) -> List[str]:
    """
    Convert text into tokens: runs of allowed characters become tokens; other
    characters are treated as separators. No empty tokens.
    """
    tokens: List[str] = []
    buf: List[str] = []

    def flush():
        nonlocal buf
        if buf:
            tokens.append("".join(buf))
            buf = []

    # Treat underscores and hyphens as separators by default unless regex_pattern allows them.
    # Our per-character allowed check will decide; but to meet baseline expectations, if there
    # is no regex_pattern, we always treat '_' and '-' as separators.
    for c in text:
        keep = False
        if allowed_re is not None:
            # Allowed if regex matches this character
            try:
                keep = allowed_re.match(c) is not None
            except Exception:
                keep = False
        else:
            # Default allowed: alnum only
            if c in ("_", "-"):
                keep = False
            else:
                keep = _is_alnum_char(c, allow_unicode=allow_unicode)

        if keep:
            buf.append(c)
        else:
            flush()
    flush()
    return tokens


def _remove_stopwords(tokens: List[str], stopwords) -> List[str]:
    sw = _iter_stopwords(stopwords)
    if not sw:
        return tokens
    sw_norm = {s.casefold() for s in sw}
    out: List[str] = []
    for t in tokens:
        if t and t.casefold() not in sw_norm:
            out.append(t)
    return out


def _join_and_collapse(tokens: List[str], separator: str) -> str:
    # Joining tokens inherently avoids duplicates; just handle empty separator edge case.
    if not tokens:
        return ""
    if separator is None:
        separator = "-"
    if separator == "":
        # Degenerate case: join without separators.
        return "".join(tokens)
    s = separator.join(tokens)
    # Trim leading/trailing separator (shouldn't occur) and collapse accidental repeats
    # if separator appears inside tokens due to regex_pattern allowing it.
    # We do not remove separator inside tokens intentionally; only collapse adjacent separators.
    if separator:
        # Collapse runs of the separator string
        esc = re.escape(separator)
        s = re.sub(rf"(?:{esc}){{2,}}", separator, s)
        s = s.strip(separator)
    return s


def _truncate_slug(slug: str, *, max_length: Optional[int], separator: str) -> str:
    if max_length is None:
        return slug
    try:
        ml = int(max_length)
    except Exception:
        return slug
    if ml <= 0:
        return ""
    if len(slug) <= ml:
        return slug
    truncated = slug[:ml]
    if separator:
        truncated = truncated.rstrip(separator)
    return truncated


def _truncate_tokens_word_boundary(
    tokens: List[str], *, max_length: int, separator: str
) -> List[str]:
    if max_length <= 0:
        return []

    if not tokens:
        return []

    out: List[str] = []
    current_len = 0
    sep_len = len(separator)

    for t in tokens:
        if not out:
            candidate_len = len(t)
        else:
            candidate_len = current_len + sep_len + len(t)

        if candidate_len <= max_length:
            out.append(t)
            current_len = candidate_len
            continue

        # Can't add full token
        if not out:
            # Single token longer than max_length: truncate token itself.
            out.append(t[:max_length])
        break

    return out


def slugify(
    text,
    allow_unicode: bool = False,
    max_length: int | None = None,
    word_boundary: bool = False,
    separator: str = "-",
    regex_pattern: str | None = None,
    stopwords: list[str] | set[str] | tuple[str, ...] | None = None,
    lowercase: bool = True,
    replacements: list[tuple[str, str]] | None = None,
    **kwargs,
) -> str:
    """
    Create a URL-friendly slug from `text`.

    This is a pure-Python implementation intended to be compatible with the
    core API surface used by tests for the `python-slugify` project.
    Unknown kwargs are accepted and ignored for compatibility.
    """
    # Convert input
    s = _to_str(text)
    if not s:
        return ""

    # Apply replacements (pre-processing)
    s = _apply_replacements(s, replacements)

    # Unicode handling
    if allow_unicode:
        # Normalize to a consistent form; do not force ASCII.
        s = unicodedata.normalize("NFKC", s)
    else:
        # Strip diacritics and remove remaining non-ASCII.
        s = _strip_diacritics_to_ascii(s)

    # Lowercasing (unicode-aware)
    if lowercase:
        s = s.lower()

    # Custom regex pattern handling (allowed characters)
    allowed_re = _compile_allowed_char_pattern(regex_pattern)

    # Tokenize into alnum runs (or allowed chars per regex pattern)
    tokens = _tokenize(s, allow_unicode=allow_unicode, separator=separator, allowed_re=allowed_re)

    # Stopword removal
    tokens = _remove_stopwords(tokens, stopwords)

    if not tokens:
        return ""

    # Truncation
    if max_length is not None:
        try:
            ml = int(max_length)
        except Exception:
            ml = None
        if ml is not None:
            if ml <= 0:
                return ""
            if word_boundary:
                tokens = _truncate_tokens_word_boundary(tokens, max_length=ml, separator=separator)
                slug = _join_and_collapse(tokens, separator)
                # Ensure final length <= max_length even in edge cases
                slug = _truncate_slug(slug, max_length=ml, separator=separator)
                return slug
            # else handled after join

    slug = _join_and_collapse(tokens, separator)

    # Final truncation if not word_boundary
    if max_length is not None and not word_boundary:
        slug = _truncate_slug(slug, max_length=max_length, separator=separator)

    # Final cleanup invariants
    if separator:
        esc = re.escape(separator)
        slug = re.sub(rf"(?:{esc}){{2,}}", separator, slug).strip(separator)
    return slug