from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class FunctionSig:
    name: str
    args: List[str]


def _format_signature(fn: FunctionSig) -> str:
    return f"{fn.name}({', '.join(fn.args)})"


def _iter_py_files(pkg_root: Path) -> List[Path]:
    return [p for p in pkg_root.rglob("*.py") if p.is_file()]


def _module_name_from_path(pkg_root: Path, file_path: Path) -> str:
    rel = file_path.relative_to(pkg_root)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].replace(".py", "")
    if not parts:
        return pkg_root.name
    return pkg_root.name + "." + ".".join(parts)


def _extract_functions_from_ast(tree: ast.AST) -> List[FunctionSig]:
    out: List[FunctionSig] = []
    if not isinstance(tree, ast.Module):
        return out

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            args: List[str] = []
            for a in node.args.args:
                args.append(a.arg)
            if node.args.vararg:
                args.append("*" + node.args.vararg.arg)
            for a in node.args.kwonlyargs:
                args.append(a.arg)
            if node.args.kwarg:
                args.append("**" + node.args.kwarg.arg)
            out.append(FunctionSig(name=node.name, args=args))
    return out


def _extract_exports_from_init(tree: ast.AST) -> List[str]:
    exports: List[str] = []
    if not isinstance(tree, ast.Module):
        return exports

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            # Focus on relative imports; __init__.py re-exports often use these.
            if node.level and node.names:
                for alias in node.names:
                    if alias.name == "*":
                        exports.append("*")
                    else:
                        exports.append(alias.asname or alias.name)
    return exports


def _is_package_dir(d: Path) -> bool:
    return d.is_dir() and (d / "__init__.py").exists()


def _find_package_root(reference_repo: Path, package_name: Optional[str]) -> Path:
    """
    Support both layouts:
      - <repo>/<package_name>
      - <repo>/src/<package_name>
    If package_name is None or not found, attempt to infer by scanning common roots.
    """
    repo = reference_repo.resolve()

    # Common roots: repo/src then repo
    candidates_roots = []
    if (repo / "src").exists():
        candidates_roots.append(repo / "src")
    candidates_roots.append(repo)

    # 1) If package_name provided, try exact matches first
    if package_name:
        for root in candidates_roots:
            cand = (root / package_name).resolve()
            if _is_package_dir(cand):
                return cand

    # 2) Infer: find directories that look like Python packages
    package_dirs: List[Path] = []
    for root in candidates_roots:
        if not root.exists():
            continue
        for child in root.iterdir():
            if _is_package_dir(child):
                package_dirs.append(child)

    # If only one obvious package dir exists, pick it
    if len(package_dirs) == 1:
        return package_dirs[0].resolve()

    # If multiple, prefer one matching "package_name" case-insensitively
    if package_name:
        for d in package_dirs:
            if d.name.lower() == package_name.lower():
                return d.resolve()

    # Otherwise fail with a helpful error
    roots_str = ", ".join(str(r) for r in candidates_roots)
    found_str = ", ".join(d.name for d in package_dirs) if package_dirs else "(none)"
    raise FileNotFoundError(
        f"Package root not found. Searched roots: {roots_str}. "
        f"package_name={package_name!r}. Found package dirs: {found_str}"
    )


def extract_api_contract_text(reference_repo: Path, package_name: Optional[str] = None) -> str:
    """
    Extract a contract text from a reference repository using static AST parsing.

    reference_repo: path like <ROOT>/repositories/<Project>
    package_name: python package directory name (e.g., 'stegano', 'astral')
    """
    pkg_root = _find_package_root(reference_repo, package_name)

    exports_by_module: Dict[str, List[str]] = {}
    functions_by_module: Dict[str, List[FunctionSig]] = {}

    for py_file in _iter_py_files(pkg_root):
        try:
            src = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            src = py_file.read_text(encoding="latin-1", errors="ignore")

        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue

        module_name = _module_name_from_path(pkg_root, py_file)
        fns = _extract_functions_from_ast(tree)
        if fns:
            functions_by_module[module_name] = fns

        if py_file.name == "__init__.py":
            exports = _extract_exports_from_init(tree)
            if exports:
                exports_by_module[module_name] = exports

    lines: List[str] = []
    lines.append("API CONTRACT — AUTO-EXTRACTED FROM REFERENCE (STATIC AST)")
    lines.append("")
    lines.append(f"Reference repo: {reference_repo.resolve()}")
    lines.append(f"Package root: {pkg_root.resolve()}")
    lines.append("Rules:")
    lines.append("- Implement the same public modules/functions and package-level exports.")
    lines.append("- Missing exports or different names are considered failures.")
    lines.append("")

    if exports_by_module:
        lines.append("Package/module exports (from __init__.py):")
        for mod in sorted(exports_by_module.keys()):
            exports = ", ".join(sorted(set(exports_by_module[mod])))
            lines.append(f"- {mod} exports: {exports}")
        lines.append("")

    lines.append("Functions by module:")
    for mod in sorted(functions_by_module.keys()):
        lines.append(f"- {mod}:")
        for fn in sorted(functions_by_module[mod], key=lambda x: x.name):
            lines.append(f"    - {_format_signature(fn)}")
    lines.append("")

    lines.append("Important:")
    lines.append("- Tests may import from package-level modules; ensure __init__.py re-exports required symbols.")
    lines.append("- Support src/ layout if the project uses it.")
    return "\n".join(lines)
