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


def run_single_task(task_yaml: Path, model_name: str, skip_generation: bool, skip_install: bool,
                    generated_root: str, results_root: str) -> bool:
    cmd = [
        "python",
        "-m",
        "evaluation.run_benchmark_m3",
        "--task",
        str(task_yaml),
        "--generated-root",
        generated_root,
        "--results-root",
        results_root,
    ]
    if skip_generation:
        cmd.append("--skip-generation")
    if skip_install:
        cmd.append("--skip-install")

    env = os.environ.copy()
    env["RACB_MODEL"] = model_name

    try:
        subprocess.run(cmd, check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[WARN] Task failed: {task_yaml} (exit={e.returncode})")
        return False


def load_result_or_default(project: str, results_dir: Path) -> dict:
    rf = results_dir / f"{project}_results.yaml"
    if not rf.exists():
        print(f"[WARN] Result file not found for {project}, using zero scores")
        return {"functional_score": 0.0, "non_functional_score": 0.0, "scores": {}, "non_functional_subscores": {}}
    with open(rf, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _f(x, default=0.0) -> float:
    try:
        return float(x) if x is not None else float(default)
    except Exception:
        return float(default)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--skip-generation", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--generated-root", default="generation_m3")
    parser.add_argument("--results-root", default="results_m3")
    args = parser.parse_args()

    results_dir = (ROOT / args.results_root).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    suffix = "eval_only" if args.skip_generation else "gen_and_eval"
    csv_path = results_dir / f"{args.model}__m3__{suffix}.csv"

    fieldnames = [
        "model", "mode", "strategy", "project",
        "functional_score", "non_functional_score",
        "maintainability", "security", "robustness", "performance", "resource",
    ]

    rows = []
    for task_yaml in find_all_tasks():
        project = task_yaml.parent.name
        mode_str = "eval_only" if args.skip_generation else "gen_and_eval"
        print(f"\n=== Running {project} (M3 | {mode_str}) ===")

        run_single_task(
            task_yaml,
            args.model,
            args.skip_generation,
            args.skip_install,
            args.generated_root,
            args.results_root,
        )

        result = load_result_or_default(project, results_dir)
        scores = result.get("scores", {}) or {}
        nf_sub = result.get("non_functional_subscores", {}) or {}

        def get_sub(k: str) -> float:
            return _f(nf_sub.get(k, scores.get(k, 0.0)), 0.0)

        rows.append({
            "model": args.model,
            "mode": mode_str,
            "strategy": "m3",
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
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"\nAll M3 results written to: {csv_path}")


if __name__ == "__main__":
    main()
