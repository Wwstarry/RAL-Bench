import ast
import os
from pathlib import Path
from typing import Iterable, List, Tuple, Dict, Any

REPO_ROOT_ENV = "RACB_REPO_ROOT"
PKG_NAME_ENV = "RACB_PACKAGE_NAME"

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "venv",
    ".venv",
    "env",
    "build",
    "dist",
    "site-packages",
    "tests",
}


def _repo_root() -> Path:
    v = os.environ.get(REPO_ROOT_ENV, "").strip()
    if not v:
        # Fallback to project root if not provided
        return Path(__file__).resolve().parents[2]
    return Path(v).resolve()


def _scan_root(repo_root: Path) -> Path:
    pkg = os.environ.get(PKG_NAME_ENV, "").strip()
    if pkg:
        cand = (repo_root / pkg).resolve()
        if cand.exists() and cand.is_dir():
            return cand
    return repo_root


def _iter_py_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        parts = set(p.parts)
        if any(x in parts for x in EXCLUDE_DIRS):
            continue
        # Skip huge generated caches if any
        if p.name.endswith(".pyi"):
            continue
        yield p


def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _count_loc(text: str) -> int:
    loc = 0
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        loc += 1
    return loc


def _get_call_name(node: ast.AST) -> str:
    # Returns dotted call name like "os.system" or "subprocess.run"
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _get_call_name(node.value)
        if base:
            return f"{base}.{node.attr}"
        return node.attr
    return ""


def _kw_bool(kwargs: List[ast.keyword], name: str) -> bool:
    for kw in kwargs:
        if kw.arg == name:
            v = kw.value
            if isinstance(v, ast.Constant) and isinstance(v.value, bool):
                return bool(v.value)
            # handle NameConstant (py<3.8) not needed, but safe
    return False


class _SecurityVisitor(ast.NodeVisitor):
    """
    Count high-risk patterns:
      - eval(...)
      - exec(...)
      - os.system(...)
      - subprocess.* with shell=True (run/call/check_output/Popen/...)
      - pickle.loads / pickle.load / pickle.Unpickler / dill.loads/load (if present)
    """
    def __init__(self) -> None:
        self.high_risk_count = 0
        self.imports: Dict[str, str] = {}  # local_name -> module name

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            name = alias.name  # e.g., "os", "subprocess", "pickle"
            asname = alias.asname or name.split(".")[-1]
            self.imports[asname] = name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        mod = node.module or ""
        for alias in node.names:
            asname = alias.asname or alias.name
            # map imported symbol to module.symbol (approx)
            self.imports[asname] = f"{mod}.{alias.name}" if mod else alias.name
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        fn = _get_call_name(node.func)

        # Resolve simple aliases: if call is "system(...)" but imported as "from os import system"
        if fn in self.imports:
            fn = self.imports[fn]

        # eval / exec
        if fn in {"eval", "exec"}:
            self.high_risk_count += 1
            return self.generic_visit(node)

        # os.system
        if fn == "os.system":
            self.high_risk_count += 1
            return self.generic_visit(node)

        # subprocess.* with shell=True
        if fn.startswith("subprocess."):
            if _kw_bool(list(node.keywords or []), "shell"):
                self.high_risk_count += 1
                return self.generic_visit(node)

        # pickle / dill / cloudpickle loads/load
        if fn in {
            "pickle.loads",
            "pickle.load",
            "pickle.Unpickler",
            "dill.loads",
            "dill.load",
            "cloudpickle.loads",
            "cloudpickle.load",
        }:
            self.high_risk_count += 1
            return self.generic_visit(node)

        self.generic_visit(node)


def _analyze_file(path: Path) -> Tuple[int, int]:
    """
    Return (high_risk_count, loc)
    """
    text = _read_text(path)
    if not text.strip():
        return (0, 0)
    loc = _count_loc(text)
    try:
        tree = ast.parse(text)
    except Exception:
        # If parse fails, don't penalize as "security finding"; just count LOC
        return (0, loc)

    v = _SecurityVisitor()
    v.visit(tree)
    return (v.high_risk_count, loc)


def test_security_high_risk_count_metric() -> None:
    repo = _repo_root()
    root = _scan_root(repo)

    files = list(_iter_py_files(root))
    high = 0
    total_loc = 0

    for f in files:
        h, loc = _analyze_file(f)
        high += h
        total_loc += loc

    # Single comparable metric: high_risk_count (lower is better)
    print(f"SECURITY_METRICS high_risk_count={float(high)} files_scanned={float(len(files))} total_loc={float(total_loc)}")

    # Always pass: this is a metric-collection test (scored in runner)
    assert True
