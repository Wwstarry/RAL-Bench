"""
Generic maintainability test (reference-measurable).

This test is designed to:
- Work on Python 3.9+ (no direct ast.Match reference).
- Scan the repository under RACB_REPO_ROOT.
- Compute a Maintainability Index-like metric per file and report:
    MAINT_METRICS mi_min=... files_scanned=... total_loc=... max_cc=...
- Always remain lightweight and deterministic.

Environment variables:
- RACB_REPO_ROOT: absolute path to the repo root to scan (set by benchmark runner).
- RACB_PACKAGE_NAME: optional package name to focus scanning (not required).

Notes:
- MI implementation is a practical approximation inspired by Radon/VS-style MI:
    MI = max(0, (171 - 5.2*ln(V) - 0.23*CC - 16.2*ln(LOC)) * 100 / 171)
  where V is Halstead Volume (approximated), CC is cyclomatic complexity (approx),
  LOC is non-empty, non-comment lines.
- We deliberately clamp V and LOC to avoid log(0) and keep metrics stable.
"""

from __future__ import annotations

import ast
import io
import math
import os
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

REPO_ROOT_ENV = "RACB_REPO_ROOT"
PKG_NAME_ENV = "RACB_PACKAGE_NAME"


# ----------------------------
# Helpers: file collection
# ----------------------------

def _repo_root() -> Path:
    val = os.environ.get(REPO_ROOT_ENV)
    if not val:
        # Fallback: project root two levels up from tests/_generic
        return Path(__file__).resolve().parents[2]
    return Path(val).resolve()


def _should_skip_dir(p: Path) -> bool:
    name = p.name.lower()
    return name in {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "dist",
        "build",
    }


def _iter_py_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        # prune dirs in-place
        dirnames[:] = [dn for dn in dirnames if not _should_skip_dir(d / dn)]
        for fn in filenames:
            if fn.endswith(".py"):
                yield (d / fn)


def _read_text(path: Path) -> str:
    # Be robust to encoding issues in repos.
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""


# ----------------------------
# LOC
# ----------------------------

def _count_loc(src: str) -> int:
    """
    Count LOC as non-empty, non-comment lines (roughly).
    This is stable and avoids requiring a full lexer for comments.
    """
    loc = 0
    for line in src.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        loc += 1
    return loc


# ----------------------------
# Cyclomatic Complexity (approx)
# ----------------------------

_BRANCH_NODE_TYPES: Tuple[type, ...] = (
    ast.If,
    ast.For,
    ast.While,
    ast.Try,
    ast.With,
    ast.AsyncWith,
    ast.IfExp,
    ast.ExceptHandler,
    ast.BoolOp,
    ast.comprehension,
)

# Python 3.10+ structural pattern matching nodes (guarded for 3.9)
_AST_MATCH = getattr(ast, "Match", None)
_AST_MATCH_CASE = getattr(ast, "match_case", None) or getattr(ast, "MatchCase", None)

_BRANCH_NODE_TYPES_DYNAMIC: List[type] = list(_BRANCH_NODE_TYPES)
if _AST_MATCH is not None:
    _BRANCH_NODE_TYPES_DYNAMIC.append(_AST_MATCH)
if _AST_MATCH_CASE is not None:
    _BRANCH_NODE_TYPES_DYNAMIC.append(_AST_MATCH_CASE)

BRANCH_NODES: Tuple[type, ...] = tuple(_BRANCH_NODE_TYPES_DYNAMIC)


class _Cyclomatic(ast.NodeVisitor):
    """
    Very lightweight cyclomatic complexity estimator.

    Rules (approx):
    - Start at 1 per function/lambda/module.
    - +1 for each branch node encountered.
    - + (len(values)-1) for BoolOp (and/or chains), since these add decision points.
    """

    def __init__(self) -> None:
        self.cc = 1

    def generic_visit(self, node: ast.AST) -> None:
        if isinstance(node, ast.BoolOp):
            # and/or chain adds decisions
            try:
                self.cc += max(0, len(getattr(node, "values", [])) - 1)
            except Exception:
                self.cc += 1
        elif isinstance(node, BRANCH_NODES):
            # Base +1 for branch constructs
            self.cc += 1
        super().generic_visit(node)


def _function_complexities(tree: ast.AST) -> List[int]:
    """
    Compute complexity per function-like node; if none, treat module as one unit.
    """
    ccs: List[int] = []

    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            v = _Cyclomatic()
            v.visit(n)
            ccs.append(int(v.cc))

    if not ccs:
        v = _Cyclomatic()
        v.visit(tree)
        ccs.append(int(v.cc))

    return ccs


# ----------------------------
# Halstead Volume (approx) via tokenize
# ----------------------------

_OPERATOR_TOKENS = {
    tokenize.OP,
}

_KEYWORD_OPERATORS = {
    # treat some keywords as operators for Halstead-ish accounting
    "and", "or", "not", "is", "in",
    "if", "else", "elif", "for", "while",
    "try", "except", "finally", "with", "as",
    "return", "yield", "raise", "assert",
    "break", "continue", "pass",
    "import", "from",
    "lambda",
}

def _halstead_volume(src: str) -> float:
    """
    Approximate Halstead volume from token stream:
    - operators: OP tokens + selected keywords
    - operands: NAME, NUMBER, STRING (excluding keywords counted as operators)
    """
    try:
        tokgen = tokenize.generate_tokens(io.StringIO(src).readline)
    except Exception:
        return 0.0

    distinct_ops: set = set()
    distinct_operands: set = set()
    N1 = 0  # total operators
    N2 = 0  # total operands

    for tok in tokgen:
        ttype = tok.type
        tstr = tok.string

        if ttype in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT):
            continue
        if ttype == tokenize.COMMENT:
            continue
        if ttype == tokenize.ENCODING:
            continue
        if ttype == tokenize.ENDMARKER:
            continue

        if ttype == tokenize.NAME:
            if tstr in _KEYWORD_OPERATORS:
                distinct_ops.add(tstr)
                N1 += 1
            else:
                distinct_operands.add(tstr)
                N2 += 1
            continue

        if ttype in _OPERATOR_TOKENS:
            distinct_ops.add(tstr)
            N1 += 1
            continue

        if ttype in (tokenize.NUMBER, tokenize.STRING):
            distinct_operands.add(ttype)  # coarser: token type instead of full literal
            N2 += 1
            continue

        # Everything else: ignore, or treat conservatively as operand
        # (We ignore to keep noise low.)

    n = len(distinct_ops) + len(distinct_operands)  # vocabulary
    N = N1 + N2  # length
    if n <= 1 or N <= 0:
        return 0.0

    return float(N) * math.log2(float(n))


# ----------------------------
# Maintainability Index (approx)
# ----------------------------

def _maintainability_index(loc: int, cc: float, volume: float) -> float:
    """
    MI approximation in [0,100].

    MI = max(0, (171 - 5.2*ln(V) - 0.23*CC - 16.2*ln(LOC)) * 100 / 171)
    """
    # Clamp to avoid log(0) and ensure stability
    loc_c = max(1.0, float(loc))
    vol_c = max(1.0, float(volume))
    cc_c = max(0.0, float(cc))

    mi = (171.0 - 5.2 * math.log(vol_c) - 0.23 * cc_c - 16.2 * math.log(loc_c)) * 100.0 / 171.0
    if math.isnan(mi) or math.isinf(mi):
        return 0.0
    return float(max(0.0, min(100.0, mi)))


# ----------------------------
# Scan + aggregate
# ----------------------------

@dataclass
class FileMetrics:
    path: Path
    loc: int
    max_cc: int
    avg_cc: float
    volume: float
    mi: float


def _scan_repo(root: Path) -> Tuple[List[FileMetrics], Dict[str, float]]:
    files: List[FileMetrics] = []
    total_loc = 0
    max_cc_global = 0

    for f in _iter_py_files(root):
        src = _read_text(f)
        if not src.strip():
            continue

        loc = _count_loc(src)
        if loc <= 0:
            continue

        try:
            tree = ast.parse(src)
        except Exception:
            # If parse fails, treat as worst maintainability for this file
            # but still count LOC so repo size is not hidden.
            total_loc += loc
            files.append(FileMetrics(path=f, loc=loc, max_cc=0, avg_cc=0.0, volume=0.0, mi=0.0))
            continue

        ccs = _function_complexities(tree)
        max_cc = max(ccs) if ccs else 1
        avg_cc = float(sum(ccs) / len(ccs)) if ccs else 1.0

        vol = _halstead_volume(src)
        mi = _maintainability_index(loc=loc, cc=avg_cc, volume=vol)

        total_loc += loc
        max_cc_global = max(max_cc_global, int(max_cc))

        files.append(
            FileMetrics(
                path=f,
                loc=loc,
                max_cc=int(max_cc),
                avg_cc=float(avg_cc),
                volume=float(vol),
                mi=float(mi),
            )
        )

    summary = {
        "files_scanned": float(len(files)),
        "total_loc": float(total_loc),
        "max_cc": float(max_cc_global),
        "mi_min": float(min((fm.mi for fm in files), default=0.0)),
    }
    return files, summary


# ----------------------------
# Pytest entry
# ----------------------------

def test_maintainability_metrics_smoke() -> None:
    root = _repo_root()

    # Optionally focus on a package subdir if provided and exists; otherwise scan repo root.
    pkg = os.environ.get(PKG_NAME_ENV, "").strip()
    scan_root = root
    if pkg:
        cand = root / pkg
        if cand.exists() and cand.is_dir():
            scan_root = cand

    files, summary = _scan_repo(scan_root)

    # Print in a single line for easy parsing by measure_reference/measure_generated
    print(
        "MAINT_METRICS "
        f"mi_min={summary['mi_min']:.4f} "
        f"files_scanned={summary['files_scanned']:.1f} "
        f"total_loc={summary['total_loc']:.1f} "
        f"max_cc={summary['max_cc']:.1f}"
    )

    # Keep as a smoke test: must scan at least one python file in real repos.
    assert summary["files_scanned"] >= 1.0, f"No python files scanned under: {scan_root}"
