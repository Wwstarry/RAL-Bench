from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


_COMMENT_RE = re.compile(r"(?m)#.*$")


@dataclass
class ModuleInfo:
    """Lightweight static summary for one Python module file."""

    module: str
    file_path: Path
    provides: Set[str]
    internal_imports: Set[str]
    syntax_error: Optional[str] = None


@dataclass
class GateIssue:
    kind: str
    message: str
    file_path: Optional[Path] = None
    detail: Optional[str] = None


def _is_probably_stdlib(mod0: str) -> bool:
    """A small heuristic list to reduce false-positives."""
    # Keep intentionally small; M2 is not a dependency resolver (that's M3).
    return mod0 in {
        "os",
        "sys",
        "re",
        "json",
        "math",
        "time",
        "pathlib",
        "typing",
        "dataclasses",
        "collections",
        "itertools",
        "functools",
        "logging",
        "subprocess",
        "threading",
        "asyncio",
        "http",
        "urllib",
        "email",
        "hashlib",
        "base64",
        "statistics",
        "decimal",
        "fractions",
        "unittest",
        "doctest",
        "importlib",
        "argparse",
        "pickle",
        "csv",
        "xml",
    }


def _candidate_roots(repo_root: Path) -> List[Path]:
    roots = [repo_root]
    src = repo_root / "src"
    if src.is_dir():
        roots.append(src)
    return roots


def _path_to_module(base: Path, file_path: Path) -> str:
    rel = file_path.relative_to(base)
    parts = list(rel.parts)
    if not parts:
        return ""
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join([p for p in parts if p and p not in {".", ".."}])


def _iter_py_files(repo_root: Path) -> Iterable[Path]:
    for p in repo_root.rglob("*.py"):
        if any(seg in {"__pycache__", ".pytest_cache", ".git"} for seg in p.parts):
            continue
        yield p


def build_module_map(repo_root: Path) -> Dict[str, Path]:
    """Map module name -> file path.

    Supports both "flat" layout and "src" layout: files under repo_root/src
    are mapped as top-level modules.
    """
    out: Dict[str, Path] = {}
    roots = _candidate_roots(repo_root)
    for base in roots:
        for f in _iter_py_files(base):
            mod = _path_to_module(base, f)
            if not mod:
                continue
            # Prefer src/ mapping if there is a conflict.
            if mod not in out or str(base).endswith(str(repo_root / "src")):
                out[mod] = f
    return out


def _module_text_is_empty(text: str, tree: Optional[ast.Module]) -> bool:
    # Remove comments and whitespace.
    stripped = _COMMENT_RE.sub("", text or "").strip()
    if not stripped:
        return True

    # If AST exists, check for docstring-only or docstring+pass.
    if tree is None:
        return False
    body = list(tree.body or [])
    if not body:
        return True
    def _is_doc(n: ast.AST) -> bool:
        return isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant) and isinstance(getattr(getattr(n, "value", None), "value", None), str)
    def _is_pass(n: ast.AST) -> bool:
        return isinstance(n, ast.Pass)
    if all(_is_doc(n) or _is_pass(n) for n in body):
        return True
    return False


def _collect_provides(tree: ast.Module) -> Set[str]:
    provides: Set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            provides.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    provides.add(t.id)
        elif isinstance(node, ast.AnnAssign):
            t = node.target
            if isinstance(t, ast.Name):
                provides.add(t.id)
        elif isinstance(node, ast.ImportFrom):
            # from x import y as z  => exposes z at module level
            for a in node.names:
                if a.name == "*":
                    continue
                provides.add(a.asname or a.name)
        elif isinstance(node, ast.Import):
            # import x.y as z => exposes z or x at module level
            for a in node.names:
                name = a.asname or (a.name.split(".")[0] if a.name else "")
                if name:
                    provides.add(name)
    return provides


def _resolve_from_import(current_mod: str, node: ast.ImportFrom) -> Optional[str]:
    # Absolute import.
    if node.level == 0:
        return node.module or None

    # Relative import.
    parts = current_mod.split(".")
    # If current_mod is a package module (i.e. __init__), it already matches package.
    # Our module naming for __init__.py is the package name, so it's fine.
    up = node.level
    if up > len(parts):
        return None
    base = parts[:-up]
    if node.module:
        base += node.module.split(".")
    return ".".join([p for p in base if p]) or None


def analyze_modules(repo_root: Path) -> Tuple[Dict[str, ModuleInfo], List[GateIssue], Dict[str, Path]]:
    module_map = build_module_map(repo_root)
    internal_roots = {m.split(".")[0] for m in module_map.keys() if m}

    infos: Dict[str, ModuleInfo] = {}
    issues: List[GateIssue] = []

    # Parse each module.
    for mod, path in module_map.items():
        text = ""
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""

        tree: Optional[ast.Module] = None
        syntax_err: Optional[str] = None
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as e:
            syntax_err = f"SyntaxError: {e.msg} (line {e.lineno})"
            issues.append(GateIssue(kind="syntax_error", message=f"{mod} has syntax error: {syntax_err}", file_path=path))
        except Exception as e:
            syntax_err = f"ParseError: {e}"
            issues.append(GateIssue(kind="syntax_error", message=f"{mod} parse failed: {syntax_err}", file_path=path))

        provides: Set[str] = set()
        internal_imports: Set[str] = set()
        if tree is not None:
            provides = _collect_provides(tree)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        name = a.name or ""
                        if not name:
                            continue
                        # Determine internal-ness.
                        root0 = name.split(".")[0]
                        if root0 in internal_roots and not _is_probably_stdlib(root0):
                            # use full module if possible
                            internal_imports.add(name)
                elif isinstance(node, ast.ImportFrom):
                    base = _resolve_from_import(mod, node)
                    if not base:
                        continue
                    root0 = base.split(".")[0]
                    if root0 in internal_roots and not _is_probably_stdlib(root0):
                        internal_imports.add(base)

        infos[mod] = ModuleInfo(module=mod, file_path=path, provides=provides, internal_imports=internal_imports, syntax_error=syntax_err)

        if _module_text_is_empty(text, tree):
            issues.append(GateIssue(kind="empty_module", message=f"{mod} appears empty or docstring-only", file_path=path))

    return infos, issues, module_map


def _ensure_init_packages(module_map: Dict[str, Path], repo_root: Path) -> List[GateIssue]:
    issues: List[GateIssue] = []
    # For any module 'a.b.c', ensure packages 'a' and 'a.b' have __init__.py
    for mod in list(module_map.keys()):
        parts = mod.split(".")
        for i in range(1, len(parts)):
            pkg = ".".join(parts[:i])
            if pkg in module_map:
                continue
            # Try locate directory to create __init__.py
            # Prefer src layout if repo_root/src exists and contains the dir.
            candidates = [repo_root / Path(*parts[:i]), repo_root / "src" / Path(*parts[:i])]
            for d in candidates:
                if d.is_dir():
                    init_py = d / "__init__.py"
                    issues.append(GateIssue(kind="missing_init", message=f"Missing package initializer for '{pkg}': {init_py}", file_path=init_py))
                    break
    return issues


def _tarjan_scc(graph: Dict[str, Set[str]]) -> List[List[str]]:
    index = 0
    stack: List[str] = []
    indices: Dict[str, int] = {}
    lowlink: Dict[str, int] = {}
    onstack: Set[str] = set()
    sccs: List[List[str]] = []

    def strongconnect(v: str) -> None:
        nonlocal index
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        onstack.add(v)

        for w in graph.get(v, set()):
            if w not in indices:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in onstack:
                lowlink[v] = min(lowlink[v], indices[w])

        if lowlink[v] == indices[v]:
            comp: List[str] = []
            while True:
                w = stack.pop()
                onstack.remove(w)
                comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    for v in graph.keys():
        if v not in indices:
            strongconnect(v)

    return sccs


def run_import_gate(
    repo_root: Path,
    required_files: Optional[List[str]] = None,
    cycle_check: bool = True,
) -> Tuple[bool, List[GateIssue]]:
    """Return (ok, issues).

    This gate is designed to catch *structural* breakages before official tests:
    - missing internal modules
    - empty modules
    - missing symbols for internal from-import
    - missing __init__.py for packages
    - syntax errors
    """
    infos, issues, module_map = analyze_modules(repo_root)

    # Required files existence check (from task YAML).
    for rf in required_files or []:
        p = (repo_root / rf.lstrip("/\\")).resolve()
        if not p.exists():
            issues.append(GateIssue(kind="missing_required_file", message=f"Missing required file: {rf}", file_path=p))
        else:
            if p.suffix == ".py":
                try:
                    txt = p.read_text(encoding="utf-8")
                except Exception:
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                try:
                    t = ast.parse(txt)
                except Exception:
                    t = None
                if _module_text_is_empty(txt, t):
                    issues.append(GateIssue(kind="empty_required_file", message=f"Required python file appears empty: {rf}", file_path=p))

    # Build internal roots again.
    internal_roots = {m.split(".")[0] for m in module_map.keys() if m}

    # Missing modules / missing symbols.
    for mod, info in infos.items():
        # Verify each internal import target exists.
        for target in info.internal_imports:
            root0 = target.split(".")[0]
            if root0 not in internal_roots:
                continue

            # Find the deepest existing module prefix.
            if target in module_map:
                continue

            # If importing 'a.b.c', allow that only 'a.b.c' missing but maybe 'a.b' exists? No.
            issues.append(GateIssue(kind="missing_module", message=f"{mod} imports missing internal module: {target}", file_path=info.file_path))

        # For from-import symbol checks, re-parse just top-level to find ImportFrom.
        try:
            text = info.file_path.read_text(encoding="utf-8")
        except Exception:
            text = info.file_path.read_text(encoding="utf-8", errors="ignore")

        try:
            tree = ast.parse(text)
        except Exception:
            continue

        for node in tree.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            base = _resolve_from_import(mod, node)
            if not base:
                continue
            root0 = base.split(".")[0]
            # only check internal modules
            if root0 not in internal_roots or _is_probably_stdlib(root0):
                continue
            if base not in infos:
                # missing module already captured
                continue
            prov = infos[base].provides
            for a in node.names:
                if a.name == "*":
                    continue
                sym = a.name
                if sym not in prov:
                    issues.append(GateIssue(
                        kind="missing_symbol",
                        message=f"{mod}: from {base} import {sym} but {base} does not provide '{sym}'",
                        file_path=info.file_path,
                    ))

    # Missing __init__.py for packages.
    issues.extend(_ensure_init_packages(module_map, repo_root))

    # Cycle detection (heuristic).
    if cycle_check:
        graph: Dict[str, Set[str]] = {m: set() for m in infos.keys()}
        for m, info in infos.items():
            for t in info.internal_imports:
                if t in infos:
                    graph[m].add(t)
        sccs = _tarjan_scc(graph)
        for comp in sccs:
            if len(comp) >= 2:
                issues.append(GateIssue(kind="import_cycle", message=f"Potential import cycle among: {', '.join(sorted(comp))}"))

    ok = len(issues) == 0
    return ok, issues


def format_gate_report(issues: List[GateIssue], max_items: int = 200) -> str:
    if not issues:
        return "[M2] Import gate: OK (no issues).\n"

    lines: List[str] = [f"[M2] Import gate: FAIL ({len(issues)} issues)\n"]
    for i, it in enumerate(issues[:max_items], start=1):
        loc = f" @ {it.file_path}" if it.file_path else ""
        lines.append(f"{i:03d}. [{it.kind}] {it.message}{loc}")
        if it.detail:
            lines.append(f"      {it.detail}")
    if len(issues) > max_items:
        lines.append(f"... truncated, showing first {max_items} issues ...")
    lines.append("")
    return "\n".join(lines)


def collect_context_for_issues(repo_root: Path, issues: List[GateIssue], per_file_chars: int = 1600) -> str:
    """Attach small snippets of problematic files to help a single structural patch."""
    paths: List[Path] = []
    for it in issues:
        if it.file_path and it.file_path.suffix == ".py":
            # it.file_path may point to non-existing (__init__.py missing)
            if it.file_path.exists():
                paths.append(it.file_path)
    # unique
    seen: Set[Path] = set()
    uniq: List[Path] = []
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        uniq.append(p)

    chunks: List[str] = []
    for p in uniq[:25]:
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        if len(txt) > per_file_chars:
            txt = txt[:per_file_chars] + "\n... (truncated) ...\n"
        rel = p.relative_to(repo_root)
        chunks.append(f"<file_context path={rel.as_posix()}>\n{txt}\n</file_context>")
    return "\n\n".join(chunks)
