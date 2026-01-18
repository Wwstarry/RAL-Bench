from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import pytest

# ---------------------------------------------------------------------------
# Repo root resolution (RACB-compatible + local fallback)
#
# RACB requirement (preferred): use RACB_REPO_ROOT and support both layouts:
#   - <repo_root>/pypdf/__init__.py
#   - <repo_root>/src/pypdf/__init__.py
#
# Local fallback (no absolute path hardcode): keep original eval layout:
#   <eval_root>/repositories/pypdf  OR  <eval_root>/generation/PyPDF
# ---------------------------------------------------------------------------

PACKAGE_NAME = "pypdf"

_racb_root = os.environ.get("RACB_REPO_ROOT", "").strip()
if _racb_root:
    REPO_ROOT = Path(_racb_root).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.environ.get("PYPDF_TARGET", "reference").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "pypdf"
    else:
        REPO_ROOT = ROOT / "generation" / "PyPDF"

if not REPO_ROOT.exists():
    pytest.skip(
        "Target repository does not exist: {}".format(REPO_ROOT),
        allow_module_level=True,
    )

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

try:
    from pypdf import PdfReader, PdfWriter  # type: ignore  # noqa: E402
except Exception as exc:
    pytest.skip(
        "Failed to import pypdf from {}: {}".format(REPO_ROOT, exc),
        allow_module_level=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_simple_pdf(path: Path, num_pages: int = 1) -> None:
    """Create a simple PDF with the given number of blank pages."""
    writer = PdfWriter()
    # The first add_blank_page call requires explicit dimensions.
    for i in range(num_pages):
        if i == 0:
            writer.add_blank_page(width=200, height=200)
        else:
            writer.add_blank_page()
    with path.open("wb") as fp:
        writer.write(fp)


def _page_rotation(page) -> int:
    """Return page rotation as int degrees in a cross-version manner."""
    # Newer pypdf: PageObject.rotation (property)
    rot = getattr(page, "rotation", None)
    if rot is not None:
        try:
            return int(rot)
        except Exception:
            pass
    # Some versions expose /Rotate in page dictionary
    try:
        return int(page.get("/Rotate", 0))
    except Exception:
        return 0


def _page_size(page) -> Tuple[float, float]:
    """Return (width, height) using mediabox in a cross-version manner."""
    # mediabox may be RectangleObject with width/height props
    mb = getattr(page, "mediabox", None) or getattr(page, "mediaBox", None)
    if mb is None:
        return (0.0, 0.0)

    w = getattr(mb, "width", None)
    h = getattr(mb, "height", None)
    if w is not None and h is not None:
        return (float(w), float(h))

    # Fallback: lower_left / upper_right coordinates
    try:
        ll = mb.lower_left
        ur = mb.upper_right
        return (float(ur[0] - ll[0]), float(ur[1] - ll[1]))
    except Exception:
        return (0.0, 0.0)


def _write_pdf_with_pages(src_paths: List[Path], out_path: Path) -> None:
    writer = PdfWriter()
    for src in src_paths:
        reader = PdfReader(str(src))
        for page in reader.pages:
            writer.add_page(page)
    with out_path.open("wb") as fp:
        writer.write(fp)


# ---------------------------------------------------------------------------
# Tests (functional-only, happy path)  >= 10 test_* functions
# ---------------------------------------------------------------------------

def test_create_and_read_blank_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "simple.pdf"
    _create_simple_pdf(pdf_path, num_pages=3)

    reader = PdfReader(str(pdf_path))
    assert len(reader.pages) == 3


def test_blank_page_has_expected_size(tmp_path: Path) -> None:
    """The first blank page should have the width/height we set."""
    pdf_path = tmp_path / "size.pdf"
    _create_simple_pdf(pdf_path, num_pages=1)

    reader = PdfReader(str(pdf_path))
    page = reader.pages[0]
    w, h = _page_size(page)

    assert w > 0 and h > 0
    assert int(round(w)) == 200
    assert int(round(h)) == 200


def test_merge_two_pdfs(tmp_path: Path) -> None:
    pdf1 = tmp_path / "p1.pdf"
    pdf2 = tmp_path / "p2.pdf"
    merged = tmp_path / "merged.pdf"

    _create_simple_pdf(pdf1, num_pages=1)
    _create_simple_pdf(pdf2, num_pages=2)

    _write_pdf_with_pages([pdf1, pdf2], merged)

    merged_reader = PdfReader(str(merged))
    assert len(merged_reader.pages) == 3


def test_writer_add_page_preserves_page_count(tmp_path: Path) -> None:
    """Add pages from a reader into a writer and verify count is preserved."""
    src = tmp_path / "src.pdf"
    dst = tmp_path / "dst.pdf"
    _create_simple_pdf(src, num_pages=4)

    reader = PdfReader(str(src))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    with dst.open("wb") as fp:
        writer.write(fp)

    reader2 = PdfReader(str(dst))
    assert len(reader2.pages) == 4


def test_rotate_page(tmp_path: Path) -> None:
    src = tmp_path / "src.pdf"
    rotated = tmp_path / "rotated.pdf"
    _create_simple_pdf(src, num_pages=1)

    reader = PdfReader(str(src))
    page = reader.pages[0]
    page.rotate(90)  # Rotate clockwise by 90 degrees.

    writer = PdfWriter()
    writer.add_page(page)
    with rotated.open("wb") as fp:
        writer.write(fp)

    rotated_reader = PdfReader(str(rotated))
    new_page = rotated_reader.pages[0]
    rotation = _page_rotation(new_page)
    assert rotation % 360 == 90


def test_rotate_preserves_page_size(tmp_path: Path) -> None:
    """Rotating a blank page should keep a valid mediabox size."""
    src = tmp_path / "src_size.pdf"
    rotated = tmp_path / "rot_size.pdf"
    _create_simple_pdf(src, num_pages=1)

    reader = PdfReader(str(src))
    page = reader.pages[0]
    w0, h0 = _page_size(page)

    page.rotate(180)
    writer = PdfWriter()
    writer.add_page(page)
    with rotated.open("wb") as fp:
        writer.write(fp)

    reader2 = PdfReader(str(rotated))
    page2 = reader2.pages[0]
    w1, h1 = _page_size(page2)

    assert int(round(w0)) == int(round(w1))
    assert int(round(h0)) == int(round(h1))


def test_encrypt_and_decrypt(tmp_path: Path) -> None:
    src = tmp_path / "plain.pdf"
    enc = tmp_path / "encrypted.pdf"
    _create_simple_pdf(src, num_pages=2)

    reader = PdfReader(str(src))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("secret-password")

    with enc.open("wb") as fp:
        writer.write(fp)

    enc_reader = PdfReader(str(enc))
    assert enc_reader.is_encrypted

    result = enc_reader.decrypt("secret-password")
    assert result  # non-zero / True on success
    assert len(enc_reader.pages) == len(reader.pages)


def test_encrypted_pdf_allows_page_access_after_decrypt(tmp_path: Path) -> None:
    """After decrypting, basic page access should succeed and page size is valid."""
    src = tmp_path / "plain2.pdf"
    enc = tmp_path / "encrypted2.pdf"
    _create_simple_pdf(src, num_pages=1)

    reader = PdfReader(str(src))
    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    writer.encrypt("pw")

    with enc.open("wb") as fp:
        writer.write(fp)

    enc_reader = PdfReader(str(enc))
    assert enc_reader.is_encrypted
    assert enc_reader.decrypt("pw")

    page = enc_reader.pages[0]
    w, h = _page_size(page)
    assert w > 0 and h > 0


def test_metadata_roundtrip(tmp_path: Path) -> None:
    src = tmp_path / "src.pdf"
    dst = tmp_path / "meta.pdf"
    _create_simple_pdf(src, num_pages=1)

    reader = PdfReader(str(src))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    writer.add_metadata(
        {
            "/Title": "PyPDF Benchmark Document",
            "/Author": "RealAppCodeBench",
        }
    )

    with dst.open("wb") as fp:
        writer.write(fp)

    reader2 = PdfReader(str(dst))
    meta = reader2.metadata
    assert meta is not None
    assert meta.get("/Title") == "PyPDF Benchmark Document"
    assert meta.get("/Author") == "RealAppCodeBench"


def test_metadata_multiple_fields_roundtrip(tmp_path: Path) -> None:
    """Add several info dict fields and ensure they can be read back."""
    src = tmp_path / "src_info.pdf"
    dst = tmp_path / "info.pdf"
    _create_simple_pdf(src, num_pages=1)

    reader = PdfReader(str(src))
    writer = PdfWriter()
    writer.add_page(reader.pages[0])

    writer.add_metadata(
        {
            "/Title": "Doc Title",
            "/Author": "Author Name",
            "/Subject": "Subject Line",
            "/Producer": "PyPDF",
        }
    )

    with dst.open("wb") as fp:
        writer.write(fp)

    reader2 = PdfReader(str(dst))
    meta = reader2.metadata
    assert meta is not None
    assert meta.get("/Title") == "Doc Title"
    assert meta.get("/Author") == "Author Name"
    assert meta.get("/Subject") == "Subject Line"
    assert meta.get("/Producer") == "PyPDF"


def test_append_pages_via_writer_append_pages_from_reader(tmp_path: Path) -> None:
    """If append_pages_from_reader exists, use it to concatenate PDFs."""
    if not hasattr(PdfWriter, "append_pages_from_reader"):
        pytest.skip("PdfWriter.append_pages_from_reader is not available")

    p1 = tmp_path / "a.pdf"
    p2 = tmp_path / "b.pdf"
    out = tmp_path / "out.pdf"
    _create_simple_pdf(p1, num_pages=2)
    _create_simple_pdf(p2, num_pages=3)

    w = PdfWriter()
    r1 = PdfReader(str(p1))
    r2 = PdfReader(str(p2))
    w.append_pages_from_reader(r1)
    w.append_pages_from_reader(r2)

    with out.open("wb") as fp:
        w.write(fp)

    r_out = PdfReader(str(out))
    assert len(r_out.pages) == 5


def test_clone_document_by_writing_reader_pages(tmp_path: Path) -> None:
    """Clone a document by copying pages and verify page count matches."""
    src = tmp_path / "orig.pdf"
    dst = tmp_path / "clone.pdf"
    _create_simple_pdf(src, num_pages=3)

    reader = PdfReader(str(src))
    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)

    with dst.open("wb") as fp:
        writer.write(fp)

    reader2 = PdfReader(str(dst))
    assert len(reader2.pages) == 3
