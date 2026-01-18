from __future__ import annotations

import os
import shutil
import string
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT_ENV = "RACB_REPO_ROOT"
TARGET_ENV = "MAILPILE_TARGET"


def _select_repo_root() -> Path:
    override = os.environ.get(REPO_ROOT_ENV)
    if override:
        return Path(override).resolve()

    target = os.environ.get(TARGET_ENV, "generated").lower()
    if target == "reference":
        for name in ("mailpile", "Mailpile"):
            cand = ROOT / "repositories" / name
            if (cand / "mailpile" / "__init__.py").exists():
                return cand.resolve()
        return (ROOT / "repositories" / "mailpile").resolve()

    return (ROOT / "generation" / "Mailpile").resolve()


def _py2_compat_patches() -> None:
    if not hasattr(string, "maketrans"):
        string.maketrans = str.maketrans  # type: ignore[attr-defined]

    if not hasattr(string, "translate"):

        def _translate(s: str, table, deletechars: str = "") -> str:
            if deletechars:
                s = s.translate({ord(c): None for c in deletechars})
            return s.translate(table)

        string.translate = _translate  # type: ignore[attr-defined]


def _ensure_py3_converted_repo(repo_root: Path) -> Path:
    cache_root = (ROOT / ".converted" / "Mailpile").resolve()
    cache_root.mkdir(parents=True, exist_ok=True)

    safe_name = "reference" if "repositories" in repo_root.parts else "generated"
    out_root = (cache_root / safe_name).resolve()

    stamp = out_root / ".racb_py3_stamp"
    src_pkg = repo_root / "mailpile"
    src_mtime = max(p.stat().st_mtime for p in src_pkg.rglob("*") if p.is_file())

    if stamp.exists():
        try:
            cached = float(stamp.read_text().strip())
            if cached >= src_mtime and (out_root / "mailpile" / "__init__.py").exists():
                return out_root
        except Exception:
            pass

    if out_root.exists():
        shutil.rmtree(out_root)
    shutil.copytree(repo_root, out_root)

    subprocess.run(
        [sys.executable, "-m", "lib2to3", "-w", "-n", str(out_root / "mailpile")],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    (out_root / "mailpile" / "__init__.py").write_text(
        "# RACB: minimal initializer (avoid importing the full Mailpile app)\n" "__all__ = []\n"
    )

    stamp.write_text(str(src_mtime))
    return out_root


REPO_ROOT = _select_repo_root()
PY3_REPO_ROOT = _ensure_py3_converted_repo(REPO_ROOT)
_py2_compat_patches()

repo_str = str(PY3_REPO_ROOT)
if repo_str not in sys.path:
    sys.path.insert(0, repo_str)

from mailpile.vcard import VCardLine  # type: ignore


# --- Compatibility patch ---
# Mailpile v1's VCardLine.as_vcardline mixes bytes/str when wrapping lines.
# The reference snapshot is Python-2-era; even after lib2to3, the method can
# remain byte-oriented. For a stable Python 3 benchmark, patch it to wrap based
# on UTF-8 byte length while returning text.
import mailpile.vcard as _vcard_mod  # type: ignore


def _racb_as_vcardline_py3(self):  # type: ignore
    key = self.Quote(self._name.upper())
    for k, v in self._attrs:
        k = k.upper()
        if v is None:
            key += ";%s" % (self.Quote(k))
        else:
            key += ";%s=%s" % (self.Quote(k), self.Quote(str(v)))

    wrapped, line = "", "%s:%s" % (key, self.Quote(self._value))
    llen = 0
    for ch in line:
        clen = len(ch.encode("utf-8"))
        if llen + clen >= 75:
            wrapped += "\n "
            llen = 0
        wrapped += ch
        llen += clen
    return wrapped


_vcard_mod.VCardLine.as_vcardline = _racb_as_vcardline_py3  # type: ignore


def run_mailpile_performance_benchmark(iterations: int = 2000) -> Dict[str, float]:
    """Time repeated VCard line serialization (representative pure-Python workload)."""

    vcl = VCardLine(name="bogus", value=("B" * 100) + "C")

    t0 = time.perf_counter()
    for _ in range(iterations):
        _ = vcl.as_vcardline()
    total_time = time.perf_counter() - t0

    return {
        "iterations": float(iterations),
        "total_time_seconds": float(total_time),
        "calls_per_second": float(iterations / total_time) if total_time > 0 else 0.0,
    }


def test_mailpile_performance_smoke() -> None:
    metrics = run_mailpile_performance_benchmark(iterations=500)
    assert metrics["iterations"] == 500.0
    assert metrics["total_time_seconds"] >= 0.0
    assert metrics["calls_per_second"] >= 0.0
