from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from openai import OpenAI

# Robust import: supports BOTH
#   1) python -m evaluation.run_benchmark
#   2) python evaluation/run_benchmark.py
try:
    from .measure_generated import run_all_tests  # type: ignore
except Exception:
    from measure_generated import run_all_tests  # type: ignore


ROOT = Path(__file__).resolve().parents[1]

FILE_BLOCK_RE = re.compile(
    r"<file:name=(?P<name>[^>]+)>\s*(?P<content>.*?)\s*</file>",
    re.DOTALL | re.MULTILINE,
)


def load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _ensure_empty_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_file_blocks(raw: str) -> List[Tuple[str, str]]:
    """
    Expect one or more:
      <file:name=path/to/file.py>
      ...
      </file>
    Return list of (relative_path, content).
    """
    out: List[Tuple[str, str]] = []
    for m in FILE_BLOCK_RE.finditer(raw):
        name = (m.group("name") or "").strip()
        content = m.group("content") or ""
        if name:
            out.append((name, content))
    return out


def build_prompt_from_task(task: Dict[str, Any]) -> str:
    desc = task.get("description", "") or ""
    files = task.get("files", []) or []
    file_list = "\n".join([f"- {x.get('path')}" for x in files if isinstance(x, dict) and x.get("path")])

    api_contract = task.get("api_contract", "") or ""
    api_contract_block = ""
    if api_contract.strip():
        api_contract_block = "\n\n[API CONTRACT]\n" + api_contract.strip() + "\n"

    prompt = f"""You are generating a Python repository.

[Task]
{desc.strip()}
{api_contract_block}

[Required files]
{file_list}

[Output format]
Return ONLY raw text, no markdown. Use one or more blocks like:

<file:name=path/to/file.py>
# file content here
</file>

Each <file:...> block MUST contain the complete content of that file.
"""
    return prompt


def call_model(prompt: str, model: str) -> str:
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("openai_base_url")
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("openai_api_key")

    client_kwargs: Dict[str, Any] = {}
    if base_url:
        client_kwargs["base_url"] = base_url
    if api_key:
        client_kwargs["api_key"] = api_key

    client = OpenAI(**client_kwargs)

    print("Using API configuration:")
    print(f"  Base URL: {base_url or '(default)'}")
    print(f"  Model: {model}")

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful code generator."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return (resp.choices[0].message.content or "").strip()


def generate_code_with_model(task: Dict[str, Any], output_repo: Path, model: str) -> None:
    prompt = build_prompt_from_task(task)
    print("Calling model to generate repository code...")
    raw = call_model(prompt, model=model)

    blocks = parse_file_blocks(raw)
    if not blocks:
        debug_file = output_repo / "_raw_model_output.txt"
        save_text(debug_file, raw)
        raise ValueError(f"Model output did not contain any <file:name=...> blocks. Saved: {debug_file}")

    for rel_path, content in blocks:
        rel_path = rel_path.lstrip("/\\")
        dst = output_repo / rel_path
        save_text(dst, content)
        print(f"Saved file: {dst}")


def try_extract_api_contract(task: Dict[str, Any]) -> Optional[str]:
    try:
        from api_contract_extractor import extract_api_contract_text
    except Exception:
        return None

    ref_repo = task.get("reference_repository")
    pkg = (task.get("package") or {}).get("name")
    if not ref_repo or not pkg:
        return None

    ref_repo_path = (
        (ROOT / Path(str(ref_repo))).resolve()
        if not Path(str(ref_repo)).is_absolute()
        else Path(str(ref_repo)).resolve()
    )

    contract = extract_api_contract_text(
        reference_repo=ref_repo_path,
        package_name=pkg,
    )
    return contract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, type=str, help="Path to task yaml")
    parser.add_argument("--model", default=os.environ.get("RACB_MODEL", "gpt-4o-mini"), type=str)
    parser.add_argument("--auto-api-contract", action="store_true", help="Auto extract API contract from reference repo")
    parser.add_argument("--skip-generation", action="store_true", help="Skip code generation and evaluate existing generated repo")

    args = parser.parse_args()

    task_file = Path(args.task).resolve()
    task = load_yaml(task_file)

    project_name = task_file.parent.name
    generated_repo = (ROOT / Path(task.get("generated_repository", f"./generation/{project_name}"))).resolve()

    _ensure_empty_dir(generated_repo)

    if args.auto_api_contract:
        contract = try_extract_api_contract(task)
        if contract:
            task["api_contract"] = contract
            pkg_name = (task.get("package") or {}).get("name")
            print(f"[INFO] Auto-extracted api_contract from reference repository (package='{pkg_name}').")

    # Generation
    if not args.skip_generation:
        generate_code_with_model(task, generated_repo, args.model)
    else:
        print(f"跳过代码生成，直接评估已存在的代码仓库: {generated_repo}")

    # Evaluation (authoritative scoring/printing is inside run_all_tests)
    result_file = ROOT / f"results/{project_name}_results.yaml"
    result_file.parent.mkdir(parents=True, exist_ok=True)

    run_all_tests(task_file, generated_repo, result_file)

    # Do NOT re-compute / re-print scores here to avoid duplicate/conflicting output.
    # Only keep a single definitive output source (measure_generated.py).
    print(f"Wrote results to: {result_file}")


if __name__ == "__main__":
    main()
