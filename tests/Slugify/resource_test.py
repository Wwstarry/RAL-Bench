from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("SLUGIFY_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "python-slugify"
else:
    REPO_ROOT = ROOT / "generation" / "Slugify"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _install_unidecode_stub() -> None:
    """Install minimal stubs for unidecode / text_unidecode."""
    def _unidecode_func(s: str) -> str:
        return s

    uni_mod = types.ModuleType("unidecode")
    uni_mod.unidecode = _unidecode_func  # type: ignore[attr-defined]
    sys.modules["unidecode"] = uni_mod

    text_uni_mod = types.ModuleType("text_unidecode")
    text_uni_mod.unidecode = _unidecode_func  # type: ignore[attr-defined]
    sys.modules["text_unidecode"] = text_uni_mod


_install_unidecode_stub()

from slugify import slugify  # type: ignore  # noqa: E402


def _build_slug_index(
    names: Iterable[str],
    allow_unicode: bool = False,
) -> dict[str, list[str]]:
    """Build a slug index from a list of names."""
    index: dict[str, list[str]] = {}
    for name in names:
        s = slugify(name, allow_unicode=allow_unicode)
        index.setdefault(s, []).append(name)
    return index


def test_slug_index_for_filenames() -> None:
    """Integration-style test: build a slug index for a set of filenames."""
    filenames = [
        "My Document.txt",
        "My Document (final).txt",
        "Résumé 2025.pdf",
        "影師嗎.png",
        "project-plan_v1.0.docx",
        "project plan v1.0.docx",
        "C'est déjà l'été.md",
        "10 | 20 %.csv",
        "README",
        "README (copy).md",
    ]

    index = _build_slug_index(filenames)
    assert index

    # All slugs should be non-empty and lowercase ASCII by default.
    for slug, originals in index.items():
        assert slug
        assert slug == slug.lower()
        assert all(ord(ch) < 128 for ch in slug)
        assert len(originals) >= 1

    # We should have different slugs for obviously distinct files.
    assert len(index) >= 3

    # Variants of the same logical name should map to related slugs.
    doc_slugs = {slug for slug in index if slug.startswith("my-document")}
    assert doc_slugs  # At least one variant.

    readme_slugs = {slug for slug in index if slug.startswith("readme")}
    assert readme_slugs


def test_slug_index_allow_unicode() -> None:
    """When allow_unicode is True, non-ASCII characters may be preserved."""
    texts = [
        "影師嗎",
        "i love 影師嗎",
        "ナルト 疾風伝",
        "Компьютер",
    ]

    index = _build_slug_index(texts, allow_unicode=True)
    assert index

    # At least one slug should contain non-ASCII characters.
    has_unicode = any(
        any(ord(ch) >= 128 for ch in slug) for slug in index.keys()
    )
    assert has_unicode

    # When allow_unicode is True, basic ASCII-only text should still be slugified.
    ascii_index = _build_slug_index(["This is a test"], allow_unicode=True)
    assert "this-is-a-test" in ascii_index
