from __future__ import annotations

import ast
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any


@dataclass
class ImportSpec:
    """Represents an import required by tests."""
    kind: str  # "import" or "from"
    module: str
    name: Optional[str] = None
    alias: Optional[str] = None


@dataclass
class AttrRequirement:
    """Represents an attribute chain requirement on a named object in test code."""
    base_name: str               # the symbol name used in test code (alias or imported name)
    attr_chain: List[str]        # e.g. ["hide"] or ["sun", "sunrise"] etc.
    file: str
    lineno: int


@dataclass
class PreflightSpec:
    imports: List[ImportSpec] = field(default_factory=list)
    attr_requirements: List[AttrRequirement] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)


def _safe_parse_python(path: Path) -> Optional[ast.AST]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1", errors="ignore")
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def _collect_imports_and_aliases(tree: ast.AST) -> Tuple[List[ImportSpec], Dict[str, Tuple[str, Optional[str]]]]:
    """
    Returns:
      - list of ImportSpec
      - symbol_table: mapping of local symbol name -> (module, imported_name)
        * For 'import a.b as x' => x -> ("a.b", None)  # module object
        * For 'from a.b import c as y' => y -> ("a.b", "c")  # object from module
        * For 'from a import b' => b -> ("a", "b")  # could be submodule or attribute
    """
    specs: List[ImportSpec] = []
    symbol_table: Dict[str, Tuple[str, Optional[str]]] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                asname = alias.asname or alias.name.split(".")[-1]
                specs.append(ImportSpec(kind="import", module=mod, alias=asname))
                symbol_table[asname] = (mod, None)

        elif isinstance(node, ast.ImportFrom):
            # ignore relative imports in tests; benchmark tests should be absolute
            if node.module is None:
                continue
            mod = node.module
            for alias in node.names:
                if alias.name == "*":
                    # We cannot preflight wildcard imports precisely; just ensure module imports.
                    specs.append(ImportSpec(kind="import", module=mod, alias=None))
                    continue
                asname = alias.asname or alias.name
                specs.append(ImportSpec(kind="from", module=mod, name=alias.name, alias=asname))
                symbol_table[asname] = (mod, alias.name)

    return specs, symbol_table


def _attr_chain_from_attribute(node: ast.Attribute) -> Optional[Tuple[str, List[str]]]:
    """
    Given an Attribute node, try to extract:
      base_name, chain
    Example:
      lsb.hide -> ("lsb", ["hide"])
      moon.phase -> ("moon", ["phase"])
      pkg.mod.func -> ("pkg", ["mod", "func"])  (only works if base is Name)
    """
    chain: List[str] = []
    cur: Any = node
    while isinstance(cur, ast.Attribute):
        chain.append(cur.attr)
        cur = cur.value

    if isinstance(cur, ast.Name):
        base = cur.id
        chain.reverse()
        return base, chain

    return None


def _collect_attr_requirements(tree: ast.AST, symbol_table: Dict[str, Tuple[str, Optional[str]]], file: str) -> List[AttrRequirement]:
    """
    Collect attribute requirements where the base is an imported symbol name.
    We only enforce module-level / imported-symbol-level attributes, not instance attributes.
    """
    reqs: List[AttrRequirement] = []
    imported_names: Set[str] = set(symbol_table.keys())

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            parsed = _attr_chain_from_attribute(node)
            if not parsed:
                continue
            base, chain = parsed
            if base in imported_names:
                reqs.append(AttrRequirement(base_name=base, attr_chain=chain, file=file, lineno=getattr(node, "lineno", 0)))

    return reqs


def build_preflight_spec_from_tests(test_paths: List[Path]) -> PreflightSpec:
    """
    Parse tests and build a preflight spec.
    """
    spec = PreflightSpec()

    for p in test_paths:
        if not p.exists() or not p.is_file():
            continue
        tree = _safe_parse_python(p)
        if tree is None:
            continue

        spec.source_files.append(str(p))
        imports, symbol_table = _collect_imports_and_aliases(tree)
        spec.imports.extend(imports)
        spec.attr_requirements.extend(_collect_attr_requirements(tree, symbol_table, file=str(p)))

    # de-dup imports (stable order)
    seen = set()
    unique_imports: List[ImportSpec] = []
    for s in spec.imports:
        key = (s.kind, s.module, s.name, s.alias)
        if key not in seen:
            seen.add(key)
            unique_imports.append(s)
    spec.imports = unique_imports

    return spec


def run_preflight(spec: PreflightSpec, repo_root: Path) -> Dict[str, Any]:
    """
    Execute preflight checks:
      1) Apply repo_root to sys.path (handles src/ layout)
      2) Execute imports required by tests
      3) Validate attribute chains on imported objects where detectable
    """
    errors: List[str] = []

    # Ensure import path: support src/ layout
    src = repo_root / "src"
    sys_path_entry = str(src if src.exists() else repo_root)

    # Avoid mutating global sys.path order too much; prepend if missing
    import sys
    if sys_path_entry not in sys.path:
        sys.path.insert(0, sys_path_entry)

    # 1) Perform imports and build object table for names used in tests
    objects: Dict[str, Any] = {}

    for imp in spec.imports:
        if imp.kind == "import":
            try:
                mod_obj = importlib.import_module(imp.module)
            except Exception as e:
                errors.append(f"Import failed: import {imp.module} -> {repr(e)}")
                continue
            if imp.alias:
                objects[imp.alias] = mod_obj

        elif imp.kind == "from":
            try:
                mod_obj = importlib.import_module(imp.module)
            except Exception as e:
                errors.append(f"Import failed: from {imp.module} import {imp.name} -> module import error: {repr(e)}")
                continue
            try:
                obj = getattr(mod_obj, imp.name or "")
            except Exception as e:
                errors.append(f"Missing symbol: from {imp.module} import {imp.name} -> getattr failed: {repr(e)}")
                continue
            if imp.alias:
                objects[imp.alias] = obj

    # 2) Validate attribute chains on imported objects (best-effort)
    # Only chains where base_name corresponds to imported alias/name
    for req in spec.attr_requirements:
        if req.base_name not in objects:
            # Could be introduced later via wildcard or dynamic assignment; do not hard-fail here.
            # The import checks above already validate the common cases.
            continue
        cur = objects[req.base_name]
        for attr in req.attr_chain:
            if not hasattr(cur, attr):
                errors.append(
                    f"Missing attribute: {req.base_name}.{'.'.join(req.attr_chain)} "
                    f"(failed at '{attr}') in {req.file}:{req.lineno}"
                )
                break
            cur = getattr(cur, attr)

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "details": {
            "repo_root": str(repo_root),
            "import_path_used": sys_path_entry,
            "sources": spec.source_files,
            "imports_checked": len(spec.imports),
            "attr_requirements_checked": len(spec.attr_requirements),
        },
    }
