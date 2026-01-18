from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from openai import OpenAI

# Robust import: supports BOTH
#   1) python -m evaluation.run_benchmark_m2
#   2) python evaluation/run_benchmark_m2.py
try:
    from .import_gate import (  # type: ignore
        collect_context_for_issues,
        format_gate_report,
        run_import_gate,
    )
except Exception:
    from import_gate import (  # type: ignore
        collect_context_for_issues,
        format_gate_report,
        run_import_gate,
    )

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


def build_prompt_from_task(task: Dict[str, Any], extra_rules: str = "") -> str:
    desc = (task.get("description") or "").strip()
    files = task.get("files", []) or []
    file_list = "\n".join([f"- {x.get('path')}" for x in files if isinstance(x, dict) and x.get("path")])

    api_contract = (task.get("api_contract") or "").strip()
    api_contract_block = f"\n\n[API CONTRACT]\n{api_contract}\n" if api_contract else ""

    prompt = f"""You are generating a Python repository.

[Task]
{desc}{api_contract_block}

[Required files]
{file_list}

[Structural requirements]
- Do not create empty modules. Every required module must contain real code.
- Ensure all internal imports resolve: imported modules exist and provide imported symbols.
- Ensure packages have __init__.py and re-export symbols when needed.
- Avoid circular imports; use local imports inside functions if necessary.
{extra_rules}

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
            {"role": "system", "content": "You are a careful software engineer and code generator."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return (resp.choices[0].message.content or "").strip()


def generate_code_with_model(task: Dict[str, Any], output_repo: Path, model: str) -> None:
    prompt = build_prompt_from_task(task)
    print("[M2] Calling model to generate repository code...")
    raw = call_model(prompt, model=model)
    save_text(output_repo / "_m2_raw_model_output.txt", raw)

    blocks = parse_file_blocks(raw)
    if not blocks:
        raise ValueError(f"Model output did not contain any <file:name=...> blocks. Saved: {output_repo / '_m2_raw_model_output.txt'}")

    for rel_path, content in blocks:
        rel_path = rel_path.lstrip("/\\")
        dst = output_repo / rel_path
        save_text(dst, content)
        print(f"Saved file: {dst}")


def build_structural_patch_prompt(task: Dict[str, Any], gate_report: str, file_context: str) -> str:
    desc = (task.get("description") or "").strip()
    files = task.get("files", []) or []
    file_list = "\n".join([f"- {x.get('path')}" for x in files if isinstance(x, dict) and x.get("path")])
    api_contract = (task.get("api_contract") or "").strip()
    api_contract_block = f"\n\n[API CONTRACT]\n{api_contract}\n" if api_contract else ""

    return f"""You are performing ONE structural patch to fix Python module/package dependency problems.

[Task]
{desc}{api_contract_block}

[Required files]
{file_list}

[Import gate report]
{gate_report}

[Problematic file context]
{file_context}

[Rules]
- This is a STRUCTURE-ONLY fix. Do not attempt to solve functional/semantic requirements beyond what is necessary to make imports consistent.
- Do not add new third-party dependencies.
- Allowed edits: create missing modules, fill empty modules with minimal real implementations (stubs) that satisfy imports, add __init__.py, add re-exports, adjust relative/absolute imports to match the repository layout, break import cycles via local imports.
- Output ONLY the files you changed, using <file:name=...> blocks.

[Output format]
Return ONLY raw text, no markdown.

<file:name=path/to/file.py>
... full file content ...
</file>
"""


def apply_patch_blocks(output_repo: Path, raw_patch: str) -> int:
    blocks = parse_file_blocks(raw_patch or "")
    if not blocks:
        return 0
    for rel_path, content in blocks:
        rel_path = rel_path.lstrip("/\\")
        dst = output_repo / rel_path
        save_text(dst, content)
        print(f"[M2] Patched file: {dst}")
    return len(blocks)


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, type=str, help="Path to task yaml")
    parser.add_argument("--model", default=os.environ.get("RACB_MODEL", "gpt-4o-mini"), type=str)
    parser.add_argument("--auto-api-contract", action="store_true", help="Auto extract API contract from reference repo")
    parser.add_argument("--skip-generation", action="store_true", help="Skip generation and evaluate existing repo")

    # 输出隔离（默认不覆盖 baseline）
    parser.add_argument("--generated-root", default="generation_m2", type=str)
    parser.add_argument("--results-root", default="results_m2", type=str)

    # Gate knobs
    parser.add_argument("--skip-cycle-check", action="store_true")
    parser.add_argument("--patch-on-gate-fail", action="store_true", default=True)
    parser.add_argument("--no-patch", action="store_true", help="Disable the one-shot structural patch")

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

    generated_repo = (ROOT / args.generated_root / project_name).resolve()
    _ensure_dir(generated_repo)

    # Stage-1: Generation
    if not args.skip_generation:
        generate_code_with_model(task, generated_repo, args.model)
    else:
        print(f"跳过代码生成，直接评估已存在的代码仓库: {generated_repo}")

    # Stage-2: Import gate
    required_files = [x.get("path") for x in (task.get("files") or []) if isinstance(x, dict) and x.get("path")]
    ok, issues = run_import_gate(
        generated_repo,
        required_files=required_files,
        cycle_check=(not args.skip_cycle_check),
    )
    gate_report = format_gate_report(issues)
    save_text(generated_repo / "_m2_gate_report_before.txt", gate_report)

    # Stage-3: One-shot structural patch (optional, only based on gate report + generated code context)
    if (not ok) and (not args.no_patch):
        print("[M2] Gate failed. Applying one-shot structural patch...")
        ctx = collect_context_for_issues(generated_repo, issues)
        save_text(generated_repo / "_m2_gate_context.txt", ctx)
        patch_prompt = build_structural_patch_prompt(task, gate_report, ctx)
        raw_patch = call_model(patch_prompt, model=args.model)
        save_text(generated_repo / "_m2_raw_patch_output.txt", raw_patch)
        n = apply_patch_blocks(generated_repo, raw_patch)
        save_text(generated_repo / "_m2_patch_applied.txt", f"patched_files={n}\n")

        ok2, issues2 = run_import_gate(
            generated_repo,
            required_files=required_files,
            cycle_check=(not args.skip_cycle_check),
        )
        save_text(generated_repo / "_m2_gate_report_after.txt", format_gate_report(issues2))
        if ok2:
            print("[M2] Gate passed after patch.")
        else:
            print("[M2] Gate still failing after patch. Proceeding to official evaluation anyway.")
    else:
        print("[M2] Gate passed (or patch disabled). Proceeding to official evaluation.")

    # Stage-4: Official evaluation (authoritative scoring)
    results_root = (ROOT / args.results_root).resolve()
    results_root.mkdir(parents=True, exist_ok=True)
    result_file = results_root / f"{project_name}_results.yaml"

    run_all_tests(task_file, generated_repo, result_file)
    print(f"Wrote results to: {result_file}")


if __name__ == "__main__":
    main()
