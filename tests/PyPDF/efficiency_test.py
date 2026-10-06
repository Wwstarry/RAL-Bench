from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import List

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


def _create_pdf_with_pages(path: Path, num_pages: int) -> None:
    """Create a PDF with the given number of blank pages."""
    writer = PdfWriter()
    for i in range(num_pages):
        if i == 0:
            writer.add_blank_page(width=300, height=300)
        else:
            writer.add_blank_page()
    with path.open("wb") as fp:
        writer.write(fp)


def _build_corpus(tmp_dir: Path) -> list[Path]:
    """Build a small corpus of PDF files for performance testing."""
    pdf_paths: List[Path] = []
    for i in range(10):
        path = tmp_dir / f"doc_{i}.pdf"
        _create_pdf_with_pages(path, num_pages=5 + (i % 3))
        pdf_paths.append(path)
    return pdf_paths


def run_pypdf_performance_benchmark(tmp_dir: Path) -> dict[str, float]:
    """Run a basic performance benchmark over a synthetic PDF corpus."""
    pdf_paths = _build_corpus(tmp_dir)

    total_pages = 0
    t0 = time.perf_counter()

    # For each PDF, read it, then copy its pages into a new writer and write out.
    for path in pdf_paths:
        reader = PdfReader(str(path))
        total_pages += len(reader.pages)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        out_path = tmp_dir / f"copy_{path.name}"
        with out_path.open("wb") as fp:
            writer.write(fp)

    t1 = time.perf_counter()
    total_time = t1 - t0

    return {
        "num_documents": float(len(pdf_paths)),
        "total_pages": float(total_pages),
        "total_time_seconds": float(total_time),
        "pages_per_second": float(total_pages / total_time) if total_time > 0 else 0.0,
    }


def test_pypdf_performance_smoke(tmp_path: Path) -> None:
    """Smoke test to ensure that the performance benchmark runs successfully."""
    metrics = run_pypdf_performance_benchmark(tmp_path)
    assert metrics["num_documents"] > 0
    assert metrics["total_pages"] > 0
    assert metrics["total_time_seconds"] > 0.0
    assert metrics["pages_per_second"] > 0.0
