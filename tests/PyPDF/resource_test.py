from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("PYPDF_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "pypdf"
else:
    REPO_ROOT = ROOT / "generation" / "PyPDF"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pypdf import PdfReader, PdfWriter  # type: ignore  # noqa: E402


def _create_large_pdf(path: Path, num_pages: int) -> None:
    """Create a larger PDF document to exercise memory usage."""
    writer = PdfWriter()
    for i in range(num_pages):
        if i == 0:
            writer.add_blank_page(width=400, height=400)
        else:
            writer.add_blank_page()
    with path.open("wb") as fp:
        writer.write(fp)


def test_large_document_split_and_merge(tmp_path: Path) -> None:
    """Integration test that splits and merges a larger PDF document."""
    src = tmp_path / "large.pdf"
    part1 = tmp_path / "part1.pdf"
    part2 = tmp_path / "part2.pdf"
    merged = tmp_path / "merged.pdf"

    _create_large_pdf(src, num_pages=30)

    reader = PdfReader(str(src))
    assert len(reader.pages) == 30

    # Split into two parts (first 10 pages, last 20 pages).
    writer1 = PdfWriter()
    for i in range(10):
        writer1.add_page(reader.pages[i])
    with part1.open("wb") as fp:
        writer1.write(fp)

    writer2 = PdfWriter()
    for i in range(10, 30):
        writer2.add_page(reader.pages[i])
    with part2.open("wb") as fp:
        writer2.write(fp)

    # Merge them back into a single document.
    merged_writer = PdfWriter()
    for path in (part1, part2):
        r = PdfReader(str(path))
        for page in r.pages:
            merged_writer.add_page(page)
    with merged.open("wb") as fp:
        merged_writer.write(fp)

    merged_reader = PdfReader(str(merged))
    assert len(merged_reader.pages) == 30
