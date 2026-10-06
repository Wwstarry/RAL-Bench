"""S3: explicit planning followed by one repository-generation pass."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from openai import OpenAI

from .measure_generated import run_all_tests

ROOT = Path(__file__).resolve().parents[1]
FILE_BLOCK_RE = re.compile(r"<file:name=(?P<name>[^>]+)>\s*(?P<content>.*?)\s*</file>", re.DOTALL)
PLAN_RE = re.compile(r"<plan>\s*(?P<content>.*?)\s*</plan>", re.DOTALL)


def load_task(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def call_model(prompt: str, model: str) -> str:
    kwargs: Dict[str, Any] = {}
    if os.environ.get("OPENAI_BASE_URL"):
        kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
    if os.environ.get("OPENAI_API_KEY"):
        kwargs["api_key"] = os.environ["OPENAI_API_KEY"]
    response = OpenAI(**kwargs).chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful code generator."},
            {"role": "user", "content": prompt},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def context(task: Dict[str, Any]) -> str:
    files = "\n".join(
        f"- {item['path']}" for item in task.get("files", []) if isinstance(item, dict) and item.get("path")
    )
    return f"[Task]\n{task.get('description', '').strip()}\n\n[Public surface]\n{task.get('api_contract', '').strip()}\n\n[Required files]\n{files}"


def plan_prompt(task: Dict[str, Any]) -> str:
    return f"""Plan a complete Python repository before implementation.

{context(task)}

Cover layout, public APIs, cross-file behavior, edge cases, dependencies, and acceptance checks. Return only <plan>...</plan>.
"""


def generation_prompt(task: Dict[str, Any], plan: str) -> str:
    return f"""Generate the complete Python repository according to this explicit plan.

{context(task)}

[Plan]
{plan}

Return only complete files as <file:name=relative/path>...</file> blocks.
"""


def write_blocks(root: Path, raw: str) -> None:
    blocks: List[Tuple[str, str]] = [
        (match.group("name").strip(), match.group("content")) for match in FILE_BLOCK_RE.finditer(raw)
    ]
    if not blocks:
        raise ValueError("Generation response contained no file blocks")
    root = root.resolve()
    for name, content in blocks:
        rel = Path(name.lstrip("/\\"))
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"Unsafe model output path: {name}")
        destination = (root / rel).resolve()
        if root not in destination.parents:
            raise ValueError(f"Unsafe model output path: {name}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--model", default=os.environ.get("RACB_MODEL", "gpt-4o-mini"))
    parser.add_argument("--skip-generation", action="store_true")
    parser.add_argument("--generated-root", default="generation_s3")
    parser.add_argument("--results-root", default="results_s3")
    args = parser.parse_args()

    task_file = args.task.resolve()
    task = load_task(task_file)
    project = task_file.parent.name
    generated_repo = (ROOT / args.generated_root / project).resolve()
    generated_repo.mkdir(parents=True, exist_ok=True)

    if not args.skip_generation:
        raw_plan = call_model(plan_prompt(task), args.model)
        match = PLAN_RE.search(raw_plan)
        if not match:
            raise ValueError("Planning response did not contain a <plan> block")
        plan = match.group("content").strip()
        write_blocks(generated_repo, call_model(generation_prompt(task, plan), args.model))

    result_file = (ROOT / args.results_root / f"{project}_results.yaml").resolve()
    run_all_tests(task_file, generated_repo, result_file)


if __name__ == "__main__":
    main()
