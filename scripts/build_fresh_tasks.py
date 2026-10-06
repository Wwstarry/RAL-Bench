"""Construct interface-anchored Fresh-50 tasks from pinned source checkouts.

The builder selects a locally importable public module, records its public
functions/classes/constants, and writes independent black-box suites.  It does
not copy or execute upstream tests as benchmark oracles.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
FRESH = ROOT / "fresh"
CACHE = FRESH / "cache"
TASKS = FRESH / "tasks"
TESTS = FRESH / "tests"
MANIFEST = FRESH / "manifest.json"

SKIP_PARTS = {".git", "tests", "test", "examples", "benchmarks", ".venv", "venv"}
SKIP_STEMS = {
    "setup", "conftest", "noxfile", "run_tests", "check", "verify", "build_exe",
    "check_dist", "check_aoti", "check_package", "check_distribution", "configure_local",
    "export_results", "gen_examples", "gen_session_fixtures", "make_demo", "make_fixtures",
    "embed_skills", "command_family", "build_fixture", "changelog", "main",
}


def public_surface(path: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return [], {}
    symbols: list[dict[str, str]] = []
    constants: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            if isinstance(node, ast.ClassDef):
                signature = "class"
            else:
                args = [a.arg for a in node.args.posonlyargs + node.args.args]
                if node.args.vararg:
                    args.append("*" + node.args.vararg.arg)
                args.extend(a.arg for a in node.args.kwonlyargs)
                if node.args.kwarg:
                    args.append("**" + node.args.kwarg.arg)
                signature = "(" + ", ".join(args) + ")"
            symbols.append({"name": node.name, "kind": kind, "signature": signature})
        elif path.name == "__init__.py" and isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                if not name.startswith("_"):
                    symbols.append({"name": name, "kind": "object", "signature": ""})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, (str, int, float, bool, type(None))):
                for target in targets:
                    if isinstance(target, ast.Name) and target.id.isupper() and not target.id.startswith("_"):
                        constants[target.id] = value.value
    return symbols[:16], dict(list(constants.items())[:8])


def candidates(repo: Path) -> list[tuple[Path, str, Path]]:
    found: list[tuple[int, Path, str, Path]] = []
    for source in repo.rglob("*.py"):
        rel = source.relative_to(repo)
        if len(rel.parts) > 7 or any(part.lower() in SKIP_PARTS for part in rel.parts):
            continue
        if source.name.startswith("_") and source.name != "__init__.py":
            continue
        if source.stem in SKIP_STEMS or source.stem.startswith(("check_", "gen_", "make_", "build_")):
            continue
        symbols, constants = public_surface(source)
        if not symbols and not constants:
            continue
        if source.name == "__init__.py":
            package_dir = source.parent
            module = package_dir.name
            module_root = package_dir.parent
            score = 0
        else:
            package_dir = source.parent
            while package_dir != repo and (package_dir.parent / package_dir.name / "__init__.py").exists():
                package_dir = package_dir.parent
            if (source.parent / "__init__.py").exists():
                top = source.parent
                while top.parent != repo and (top.parent / "__init__.py").exists():
                    top = top.parent
                module_root = top.parent
                module = ".".join(source.relative_to(module_root).with_suffix("").parts)
            else:
                module_root = source.parent
                module = source.stem
            score = 1 if (source.parent / "__init__.py").exists() else 20
        found.append((score + len(rel.parts), module_root, module, source))
    found.sort(key=lambda item: (item[0], item[2]))
    unique: list[tuple[Path, str, Path]] = []
    seen: set[tuple[str, str]] = set()
    for _, module_root, module, source in found:
        key = (str(module_root), module)
        if key not in seen:
            unique.append((module_root, module, source))
            seen.add(key)
    return unique


def importable(repo: Path, module_root: Path, module: str) -> tuple[bool, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(module_root.resolve())
    env["PYTHONUTF8"] = "1"
    code = f"import importlib; importlib.import_module({module!r})"
    try:
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=repo, env=env,
            text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=12,
        )
    except subprocess.TimeoutExpired:
        return False, "import timeout"
    tail = (result.stdout or "").strip().splitlines()
    return result.returncode == 0, (tail[-1][:240] if tail else "")


def select_interface(repo: Path) -> dict[str, Any]:
    failures: list[str] = []
    for module_root, module, source in candidates(repo):
        ok, error = importable(repo, module_root, module)
        if not ok:
            failures.append(f"{module}: {error}")
            continue
        symbols, constants = public_surface(source)
        return {
            "module": module,
            "module_root": module_root.relative_to(repo).as_posix() or ".",
            "source_file": source.relative_to(repo).as_posix(),
            "symbols": symbols,
            "constants": constants,
        }
    raise RuntimeError("no locally importable public module; " + "; ".join(failures[:5]))


TEST_TEMPLATE = '''import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = {module!r}
MODULE_ROOT = {module_root!r}
SYMBOLS = {symbols!r}
CONSTANTS = {constants!r}


def load_module():
    repo = Path(os.environ["RACB_REPO_ROOT"]).resolve()
    root = repo if MODULE_ROOT == "." else repo / MODULE_ROOT
    sys.path.insert(0, str(root))
    return importlib.import_module(MODULE)


{body}
'''


SUITE_BODIES = {
    "functional": '''def test_public_module_imports():
    assert load_module().__name__ == MODULE


@pytest.mark.parametrize("spec", SYMBOLS)
def test_declared_public_symbol(spec):
    value = getattr(load_module(), spec["name"])
    if spec["kind"] == "class":
        assert inspect.isclass(value)
    elif spec["kind"] == "function":
        assert callable(value)
    else:
        assert value is not None


@pytest.mark.parametrize("name, expected", list(CONSTANTS.items()))
def test_public_literal_constant(name, expected):
    assert getattr(load_module(), name) == expected
''',
    "robustness": '''def test_repeated_import_is_stable():
    first = load_module()
    assert importlib.import_module(MODULE) is first


def test_missing_public_name_raises_attribute_error():
    with pytest.raises(AttributeError):
        getattr(load_module(), "__ral_bench_missing_public_name__")


@pytest.mark.parametrize("spec", SYMBOLS)
def test_public_callables_are_introspectable(spec):
    value = getattr(load_module(), spec["name"])
    if spec["kind"] == "function":
        inspect.signature(value)
''',
    "efficiency": '''def test_repeated_import_lookup_is_bounded():
    start = time.perf_counter()
    module = load_module()
    for _ in range(2000):
        for spec in SYMBOLS[:8]:
            getattr(module, spec["name"])
    assert time.perf_counter() - start < 10.0
''',
    "resource": '''def test_public_surface_is_finite():
    module = load_module()
    names = dir(module)
    assert MODULE.split(".")[-1] in module.__name__
    assert len(names) < 10000
''',
}


def description(record: dict[str, Any], interface: dict[str, Any]) -> str:
    names = [item["name"] for item in interface["symbols"]] + list(interface["constants"])
    return (
        f"Implement a Python repository compatible with the documented public interface of "
        f"{record['repository']}. The repository must provide importable module "
        f"`{interface['module']}` at `{interface['source_file']}` and expose the declared public "
        f"names: {', '.join(names) or '(module import only)'}. Imports must be deterministic, "
        "unknown attributes must raise AttributeError, and public callables must support Python "
        "signature introspection. No network service may be required by these tested behaviors."
    )


def build_one(record: dict[str, Any], force: bool = False) -> dict[str, Any]:
    task_id = record["task_id"]
    repo = CACHE / task_id
    existing = TASKS / task_id / f"{task_id}.yaml"
    if existing.is_file() and not force:
        task = yaml.safe_load(existing.read_text(encoding="utf-8")) or {}
        if (task.get("curation") or {}).get("semantic_cases"):
            return {"task_id": task_id, "status": "curated-preserved", "interface": (task.get("curation") or {}).get("interface", {})}
    interface = select_interface(repo)
    test_dir = TESTS / task_id
    test_dir.mkdir(parents=True, exist_ok=True)
    suites: dict[str, str] = {}
    for kind, body in SUITE_BODIES.items():
        path = test_dir / f"{kind}_test.py"
        path.write_text(TEST_TEMPLATE.format(**interface, body=body), encoding="utf-8")
        suites[kind] = f"./fresh/tests/{task_id}/{kind}_test.py"
    suites["security"] = "./tests/_generic/security_test.py"
    suites["maintainability"] = "./tests/_generic/maintainability_test.py"
    contract_lines = [
        "PUBLIC SURFACE (no implementation bodies)",
        f"Import: import {interface['module']}",
        f"Required path: {interface['source_file']}",
    ]
    for item in interface["symbols"]:
        contract_lines.append(f"- {item['kind']} {item['name']}{item['signature'] if item['kind'] == 'function' else ''}")
    for name, value in interface["constants"].items():
        contract_lines.append(f"- constant {name} = {value!r}")
    task = {
        "task_id": task_id,
        "domain": "fresh",
        "difficulty": "medium",
        "description": description(record, interface),
        "api_contract": "\n".join(contract_lines) + "\n",
        "interfaces": {"type": "LIB", "language": "python", "entry_point": interface["source_file"]},
        "reference_repository": f"./fresh/cache/{task_id}",
        "generated_repository": f"./fresh/generation/{task_id}",
        "package": {"name": interface["module"].split(".")[0], "root_dir": interface["module_root"]},
        "test_suite": suites,
        "suite_timeouts_s": {"default": 30},
        "baseline_metrics": {},
        "provenance": {
            "repository": record["repository"], "source_url": record["source_url"],
            "created_at": record["created_at"], "pinned_commit": record["pinned_commit"],
        },
        "curation": {"oracle_source": "public package surface; upstream tests not used", "interface": interface},
    }
    task_dir = TASKS / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    task_path = task_dir / f"{task_id}.yaml"
    task_path.write_text(yaml.safe_dump(task, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    return {"task_id": task_id, "status": "constructed", "interface": interface}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=FRESH / "task_construction_report.json")
    parser.add_argument("--force", action="store_true", help="overwrite manually curated tasks")
    args = parser.parse_args()
    records = json.loads(MANIFEST.read_text(encoding="utf-8"))["repositories"]
    report: list[dict[str, Any]] = []
    for index, record in enumerate(records, 1):
        try:
            row = build_one(record, force=args.force)
            print(f"[{index:02d}/50] PASS {record['task_id']} -> {row['interface']['module']}")
        except Exception as exc:
            row = {"task_id": record["task_id"], "status": "failed", "error": str(exc)}
            print(f"[{index:02d}/50] FAIL {record['task_id']}: {exc}")
        report.append(row)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    passed = sum(row["status"] in {"constructed", "curated-preserved"} for row in report)
    print(f"Constructed {passed}/50 Fresh tasks")
    return 0 if passed == 50 else 1


if __name__ == "__main__":
    raise SystemExit(main())
