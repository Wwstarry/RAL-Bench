"""Build reviewable public-surface summaries from the retained black-box suites.

The output is a construction aid: task authors must review it against the
reference documentation before freezing a benchmark version.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def module_from_import(node: ast.AST) -> list[tuple[str, str | None, str]]:
    found: list[tuple[str, str | None, str]] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            found.append((alias.name, None, alias.asname or alias.name.split(".")[0]))
    elif isinstance(node, ast.ImportFrom) and node.module:
        for alias in node.names:
            found.append((node.module, alias.name, alias.asname or alias.name))
    return found


def attribute_chain(node: ast.Attribute) -> tuple[str, list[str]] | None:
    parts: list[str] = []
    current: ast.AST = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    return current.id, list(reversed(parts))


def surface_for(task: dict[str, Any]) -> str:
    package = str((task.get("package") or {}).get("name") or "").strip()
    imports: set[str] = set()
    aliases: dict[str, str] = {}
    attributes: set[str] = set()

    suites = task.get("test_suite") or {}
    for kind in ("functional", "robustness", "efficiency", "resource"):
        value = suites.get(kind)
        if not value:
            continue
        values = value if isinstance(value, list) else [value]
        for suite_path in values:
            path = (ROOT / str(suite_path)).resolve()
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                for module, symbol, alias in module_from_import(node):
                    if module != package and not module.startswith(package + "."):
                        continue
                    aliases[alias] = f"{module}.{symbol}" if symbol else module
                    imports.add(f"from {module} import {symbol}" if symbol else f"import {module}")
            for node in ast.walk(tree):
                if not isinstance(node, ast.Attribute):
                    continue
                chain = attribute_chain(node)
                if chain and chain[0] in aliases:
                    attributes.add(".".join([aliases[chain[0]], *chain[1]]))

    if not imports:
        imports.add(f"import {package}")
    lines = [
        "PUBLIC SURFACE (reviewed benchmark input; no implementation bodies)",
        "",
        "Required import forms:",
        *[f"- {item}" for item in sorted(imports)],
    ]
    if attributes:
        lines.extend(["", "Referenced package attributes:", *[f"- {item}" for item in sorted(attributes)]])
    files = [item.get("path") for item in task.get("files", []) if isinstance(item, dict) and item.get("path")]
    if files:
        lines.extend(["", "Required module/file paths:", *[f"- {item}" for item in files]])
    return "\n".join(lines) + "\n"


def main() -> None:
    updated = 0
    for path in sorted((ROOT / "tasks").glob("*/*.yaml")):
        task = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if task.get("api_contract"):
            continue
        task["api_contract"] = surface_for(task)
        path.write_text(
            yaml.safe_dump(task, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )
        updated += 1
    print(f"Added public-surface summaries to {updated} tasks")


if __name__ == "__main__":
    main()
