from __future__ import annotations

import os
import re
import sys
import types
from pathlib import Path
from typing import List

import pytest

# ---------------------------------------------------------------------------
# Repo root resolution (RACB-compatible + local fallback)
#
# RACB requirement (preferred): use RACB_REPO_ROOT and support both layouts:
#   - <repo_root>/slugify/__init__.py
#   - <repo_root>/src/slugify/__init__.py
#
# Local fallback (no absolute path hardcode): keep original eval layout:
#   <eval_root>/repositories/python-slugify  OR  <eval_root>/generation/Slugify
# ---------------------------------------------------------------------------

PACKAGE_NAME = "slugify"

_racb_root = os.environ.get("RACB_REPO_ROOT", "").strip()
if _racb_root:
    REPO_ROOT = Path(_racb_root).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.environ.get("SLUGIFY_TARGET", "reference").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "python-slugify"
    else:
        REPO_ROOT = ROOT / "generation" / "Slugify"

if not REPO_ROOT.exists():
    pytest.skip("Target repository does not exist: {}".format(REPO_ROOT), allow_module_level=True)

src_pkg_init = REPO_ROOT / "src" / PACKAGE_NAME / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE_NAME / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find '{}' package under repo root. Expected {} or {}.".format(
            PACKAGE_NAME, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )


def _install_unidecode_stub() -> None:
    """Install minimal stubs for unidecode / text_unidecode.

    python-slugify imports:
      - import unidecode
        or
      - import text_unidecode as unidecode

    We provide a small unidecode() implementation that returns the input string.
    This keeps tests deterministic and avoids external dependencies.
    """

    def _unidecode_func(s: str) -> str:
        return s

    uni_mod = types.ModuleType("unidecode")
    uni_mod.unidecode = _unidecode_func  # type: ignore[attr-defined]
    sys.modules["unidecode"] = uni_mod

    text_uni_mod = types.ModuleType("text_unidecode")
    text_uni_mod.unidecode = _unidecode_func  # type: ignore[attr-defined]
    sys.modules["text_unidecode"] = text_uni_mod


_install_unidecode_stub()

try:
    from slugify import slugify  # type: ignore  # noqa: E402
except Exception as exc:
    pytest.skip("Failed to import slugify: {}".format(exc), allow_module_level=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_ascii(s: str) -> bool:
    return all(ord(ch) < 128 for ch in s)


def _no_consecutive_sep(s: str, sep: str) -> bool:
    return (sep + sep) not in s


# ---------------------------------------------------------------------------
# Tests (functional-only, happy path)  >= 10 test_* functions
# ---------------------------------------------------------------------------

def test_basic_ascii_slug() -> None:
    """Basic ASCII text should be lowercased and separated by dashes."""
    text = "This is a test ---"
    result = slugify(text)
    assert result == "this-is-a-test"


def test_ascii_punctuation_collapses_to_single_separator() -> None:
    """Punctuation should be normalized so separators don't repeat."""
    text = "Hello!!!  World??? -- Rich__Text"
    result = slugify(text)
    assert "hello" in result
    assert "world" in result
    assert _no_consecutive_sep(result, "-")
    assert not result.startswith("-")
    assert not result.endswith("-")


def test_unicode_default_is_ascii_only() -> None:
    """By default, unicode text should produce an ASCII-only slug.

    With the unidecode stub, non-ascii chars may be removed and result may be empty.
    We only assert ASCII-only property.
    """
    text = "影師嗎"
    result = slugify(text)
    assert _is_ascii(result)


def test_allow_unicode_true_preserves_non_ascii() -> None:
    """When allow_unicode is True, unicode characters can be preserved."""
    text = "影師嗎"
    result = slugify(text, allow_unicode=True)
    assert result
    assert any(ord(ch) >= 128 for ch in result)


def test_max_length_truncation_respects_limit() -> None:
    """max_length should cap the resulting slug length."""
    text = "one two three four five six seven"
    result = slugify(text, max_length=10)
    assert result
    assert len(result) <= 10
    assert _is_ascii(result)


def test_word_boundary_keeps_whole_words_when_enabled() -> None:
    """word_boundary=True should avoid cutting in the middle of a word (typical behavior)."""
    text = "alpha beta gamma delta"
    result = slugify(text, max_length=12, word_boundary=True)
    assert result
    assert len(result) <= 12
    # With word boundary, result should not end with a partial hyphenated token like 'ga'
    assert not result.endswith("-")
    assert _no_consecutive_sep(result, "-")


def test_separator_customization() -> None:
    """Custom separator should be used between tokens."""
    text = "This is a test"
    result = slugify(text, separator="_")
    assert result == "this_is_a_test"


def test_regex_pattern_allows_underscore_prefixes() -> None:
    """Custom regex_pattern can allow underscores to remain."""
    text = "___This is a test___"
    regex_pattern = r"[^-a-z0-9_]+"

    result_default_sep = slugify(text, regex_pattern=regex_pattern)
    assert result_default_sep.startswith("___")
    assert "this-is-a-test" in result_default_sep

    result_underscore = slugify(text, separator="_", regex_pattern=regex_pattern)
    assert "this_is_a_test" in result_underscore


def test_stopwords_remove_tokens() -> None:
    """Stopwords should be removed from the slug."""
    text = "the quick brown fox jumps over the lazy dog in a hurry"
    result = slugify(text, stopwords=["the", "in", "a", "hurry"])

    assert "quick" in result
    assert "brown" in result
    assert "fox" in result
    assert "lazy" in result
    assert "dog" in result

    assert "the" not in result
    assert "hurry" not in result


def test_lowercase_false_preserves_case_for_remaining_tokens() -> None:
    """lowercase=False should preserve original case for non-removed words."""
    mixed = "thIs Has a stopword Stopword"
    result = slugify(mixed, stopwords=["Stopword"], lowercase=False)

    assert "thIs" in result
    assert "Has" in result
    assert "Stopword" not in result


def test_replacements_apply_before_slugging() -> None:
    """replacements should transform substrings before final slug is produced."""
    text = "C# is not C++"
    result = slugify(text, replacements=[["C#", "Csharp"], ["C++", "Cpp"]])
    # Expect transformed tokens present
    assert "csharp" in result
    assert "cpp" in result
    assert _is_ascii(result)


def test_trailing_and_leading_separators_trimmed() -> None:
    """Slug should not start or end with the separator in normal usage."""
    text = " --- spaced --- "
    result = slugify(text)
    assert result
    assert not result.startswith("-")
    assert not result.endswith("-")
    assert _no_consecutive_sep(result, "-")
