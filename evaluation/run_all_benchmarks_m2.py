import argparse
import subprocess
import yaml
import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"


def find_all_tasks():
    return sorted(TASKS_DIR.glob("*/**/*.yaml"))


def run_single_task(
    task_yaml: Path,
    model_name: str,
    skip_generation: bool,
    generated_root: str,
    results_root: str,
    no_patch: bool,
    auto_api_contract: bool,
) -> bool:
    cmd = [
        "python",
        "-m",
        "evaluation.run_benchmark_m2",
        "--task",
        str(task_yaml),
        "--generated-root",
        generated_root,
        "--results-root",
        results_root,
    ]

    if skip_generation:
        cmd.append("--skip-generation")
    if no_patch:
        cmd.append("--no-patch")
    if auto_api_contract:
        cmd.append("--auto-api-contract")

    env = os.environ.copy()
    env["RACB_MODEL"] = model_name

    try:
        subprocess.run(cmd, check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[WARN] Task failed: {task_yaml} (exit={e.returncode})")
        return False
    except KeyboardInterrupt:
        print("[WARN] Interrupted by user")
        return False


def load_result_or_default(project: str, results_dir: Path) -> dict:
    result_file = results_dir / f"{project}_results.yaml"
    if not result_file.exists():
        print(f"[WARN] Result file not found for {project}, using zero scores")
        return {
            "functional_score": 0.0,
            "non_functional_score": 0.0,
            "scores": {},
            "non_functional_subscores": {},
        }

    with open(result_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _f(x, default=0.0) -> float:
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--skip-generation", action="store_true")

    parser.add_argument("--generated-root", default="generation_m2")
    parser.add_argument("--results-root", default="results_m2")
    parser.add_argument("--no-patch", action="store_true", help="Disable the one-shot structural patch")
    parser.add_argument("--auto-api-contract", action="store_true")

    args = parser.parse_args()

    results_dir = (ROOT / args.results_root).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    suffix = "eval_only" if args.skip_generation else "gen_and_eval"
    patch_suffix = "no_patch" if args.no_patch else "one_patch"
    csv_path = results_dir / f"{args.model}__m2__{patch_suffix}__{suffix}.csv"

    fieldnames = [
        "model",
        "mode",
        "strategy",
        "project",
        "functional_score",
        "non_functional_score",
        "maintainability",
        "security",
        "robustness",
        "performance",
        "resource",
    ]

    rows = []

    for task_yaml in find_all_tasks():
        project = task_yaml.parent.name
        mode_str = "eval_only" if args.skip_generation else "gen_and_eval"
        print(f"\n=== Running {project} (M2 | {patch_suffix} | {mode_str}) ===")

        run_single_task(
            task_yaml,
            args.model,
            args.skip_generation,
            args.generated_root,
            args.results_root,
            args.no_patch,
            args.auto_api_contract,
        )

        result = load_result_or_default(project, results_dir)
        scores = result.get("scores", {}) or {}
        nf_sub = result.get("non_functional_subscores", {}) or {}

        def get_sub(k: str) -> float:
            if k in nf_sub:
                return _f(nf_sub.get(k), 0.0)
            return _f(scores.get(k), 0.0)

        rows.append({
            "model": args.model,
            "mode": mode_str,
            "strategy": "m2",
            "project": project,
            "functional_score": _f(result.get("functional_score"), 0.0),
            "non_functional_score": _f(result.get("non_functional_score"), 0.0),
            "maintainability": get_sub("maintainability"),
            "security": get_sub("security"),
            "robustness": get_sub("robustness"),
            "performance": get_sub("performance"),
            "resource": get_sub("resource"),
        })

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nAll M2 results written to: {csv_path}")


if __name__ == "__main__":
    main()
