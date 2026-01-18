from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from openai import OpenAI

# 复用原评测逻辑（不改 measure_generated.py）
try:
    from .measure_generated import run_all_tests  # type: ignore
except Exception:
    from measure_generated import run_all_tests  # type: ignore


ROOT = Path(__file__).resolve().parents[1]

FILE_BLOCK_RE = re.compile(
    r"<file:name=(?P<name>[^>]+)>\s*(?P<content>.*?)\s*</file>",
    re.DOTALL | re.MULTILINE,
)

CONTRACT_BLOCK_RE = re.compile(
    r"<contract>\s*(?P<content>.*?)\s*</contract>",
    re.DOTALL | re.MULTILINE,
)


def load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_file_blocks(raw: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for m in FILE_BLOCK_RE.finditer(raw or ""):
        name = (m.group("name") or "").strip()
        content = m.group("content") or ""
        if name:
            out.append((name, content))
    return out


def parse_contract(raw: str) -> str:
    """
    优先解析 <contract>...</contract>。
    如果模型没按要求输出标签，则降级用 raw 的全文（strip）。
    """
    raw = raw or ""
    m = CONTRACT_BLOCK_RE.search(raw)
    if not m:
        return raw.strip()
    return (m.group("content") or "").strip()


def build_contract_prompt(task: Dict[str, Any]) -> str:
    desc = (task.get("description") or "").strip()
    files = task.get("files", []) or []
    file_list = "\n".join([f"- {x.get('path')}" for x in files if isinstance(x, dict) and x.get("path")])

    api_contract = (task.get("api_contract") or "").strip()
    api_contract_block = f"\n\n[API CONTRACT]\n{api_contract}\n" if api_contract else ""

    return f"""You are analyzing requirements for a Python repository.

[Task]
{desc}{api_contract_block}

[Required files]
{file_list}

[Goal]
Derive a structured contract that is actionable for code generation and aligned with tests.

[Output format]
Return ONLY raw text, no markdown. Put everything inside exactly one block:

<contract>
... content ...
</contract>

[Contract checklist]
Inside <contract>, include (in order):

1) Repository layout (what packages/modules/files must exist)
2) Public API surface (modules/classes/functions and key signatures)
3) Behavioral contract (I/O, invariants, edge cases, error handling)
4) Acceptance checklist (verifiable bullets, map to test intent)
5) Non-goals / constraints (what NOT to do; no external services unless required)
"""


def build_code_prompt(task: Dict[str, Any], derived_contract: str) -> str:
    desc = (task.get("description") or "").strip()
    files = task.get("files", []) or []
    file_list = "\n".join([f"- {x.get('path')}" for x in files if isinstance(x, dict) and x.get("path")])

    api_contract = (task.get("api_contract") or "").strip()
    api_contract_block = f"\n\n[API CONTRACT]\n{api_contract}\n" if api_contract else ""

    derived_contract = (derived_contract or "").strip()
    derived_block = f"\n\n[DERIVED CONTRACT]\n{derived_contract}\n" if derived_contract else ""

    return f"""You are generating a Python repository.

[Task]
{desc}{api_contract_block}{derived_block}

[Required files]
{file_list}

[Output format]
Return ONLY raw text, no markdown. Use one or more blocks like:

<file:name=path/to/file.py>
# file content here
</file>

Each <file:...> block MUST contain the complete content of that file.
"""


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

    return extract_api_contract_text(reference_repo=ref_repo_path, package_name=pkg)


def generate_m4(task: Dict[str, Any], output_repo: Path, model: str) -> None:
    """
    M4 两阶段：
      Stage-1: 产出结构化契约（contract）
      Stage-2: 将 contract 注入 prompt，产出文件块（<file:name=...>）
    """
    _ensure_dir(output_repo)

    # Stage-1: contract
    print("[M4] Stage-1: generating derived contract...")
    p1 = build_contract_prompt(task)
    raw_contract = call_model(p1, model=model)
    contract = parse_contract(raw_contract)

    save_text(output_repo / "_m4_contract_raw.txt", raw_contract)
    save_text(output_repo / "_m4_contract.txt", contract)

    # Stage-2: code
    print("[M4] Stage-2: generating repository code with derived contract...")
    p2 = build_code_prompt(task, contract)
    raw_code = call_model(p2, model=model)

    save_text(output_repo / "_m4_raw_model_output.txt", raw_code)

    blocks = parse_file_blocks(raw_code)
    if not blocks:
        raise ValueError(
            "Model output did not contain any <file:name=...> blocks. "
            f"Saved raw output to: {output_repo / '_m4_raw_model_output.txt'}"
        )

    for rel_path, content in blocks:
        rel_path = rel_path.lstrip("/\\")
        dst = output_repo / rel_path
        save_text(dst, content)
        print(f"Saved file: {dst}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, type=str, help="Path to task yaml")
    parser.add_argument("--model", default=os.environ.get("RACB_MODEL", "gpt-4o-mini"), type=str)
    parser.add_argument("--auto-api-contract", action="store_true", help="Auto extract API contract from reference repo")
    parser.add_argument("--skip-generation", action="store_true", help="Skip generation and evaluate existing repo")

    # 输出隔离（默认不覆盖 baseline）
    parser.add_argument("--generated-root", default="generation_m4", type=str, help="Root dir for generated repos (default: generation_m4)")
    parser.add_argument("--results-root", default="results_m4", type=str, help="Root dir for results (default: results_m4)")

    # 如你确实想沿用 YAML 里的 generated_repository（会覆盖），可显式打开
    parser.add_argument("--use-task-generated-repo", action="store_true", help="Use task['generated_repository'] path (may overwrite baseline)")

    args = parser.parse_args()

    task_file = Path(args.task).resolve()
    task = load_yaml(task_file)
    project_name = task_file.parent.name

    if args.auto_api_contract:
        contract = try_extract_api_contract(task)
        if contract:
            task["api_contract"] = contract
            pkg_name = (task.get("package") or {}).get("name")
            print(f"[INFO] Auto-extracted api_contract from reference repository (package='{pkg_name}').")

    # 生成目录：默认隔离到 generation_m4/<Project>
    if args.use_task_generated_repo:
        generated_repo = (ROOT / Path(task.get("generated_repository", f"./generation/{project_name}"))).resolve()
    else:
        generated_repo = (ROOT / args.generated_root / project_name).resolve()

    _ensure_dir(generated_repo)

    # Generation
    if not args.skip_generation:
        generate_m4(task, generated_repo, args.model)
    else:
        print(f"跳过代码生成，直接评估已存在的代码仓库: {generated_repo}")

    # Evaluation：结果隔离到 results_m4/<Project>_results.yaml（不覆盖 baseline）
    results_root = (ROOT / args.results_root).resolve()
    results_root.mkdir(parents=True, exist_ok=True)
    result_file = results_root / f"{project_name}_results.yaml"

    run_all_tests(task_file, generated_repo, result_file)
    print(f"Wrote results to: {result_file}")


if __name__ == "__main__":
    main()
