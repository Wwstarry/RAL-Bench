import argparse
import subprocess
import yaml
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"


def find_all_tasks():
    return sorted(TASKS_DIR.glob("*/**/*.yaml"))


def run_single_task(task_yaml: Path, model_name: str, skip_generation: bool,
                    generated_root: str, results_root: str,
                    agent_timeout_s: int, always_fix_once: bool) -> bool:
    cmd = [
        sys.executable,
        "-m",
        "evaluation.run_benchmark_s1",
        "--task",
        str(task_yaml),
        "--generated-root",
        generated_root,
        "--results-root",
        results_root,
        "--agent-timeout-s",
        str(agent_timeout_s),
    ]
    if skip_generation:
        cmd.append("--skip-generation")
    if always_fix_once:
        cmd.append("--always-fix-once")

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
    parser.add_argument("--generated-root", default="generation_s1")
    parser.add_argument("--results-root", default="results_s1")
    parser.add_argument("--agent-timeout-s", type=int, default=180)
    parser.add_argument("--always-fix-once", action="store_true")
    args = parser.parse_args()

    results_dir = (ROOT / args.results_root).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    suffix = "eval_only" if args.skip_generation else "gen_and_eval"
    csv_path = results_dir / f"{args.model}__s1__{suffix}.csv"

    fieldnames = [
        "model", "mode", "strategy", "project",
        "maintainability", "security", "robustness", "efficiency", "resource",
    ]

    rows = []
    for task_yaml in find_all_tasks():
        project = task_yaml.parent.name
        mode_str = "eval_only" if args.skip_generation else "gen_and_eval"
        print(f"\n=== Running {project} (M1 | {mode_str}) ===")

        run_single_task(
            task_yaml,
            args.model,
            args.skip_generation,
            args.generated_root,
            args.results_root,
            args.agent_timeout_s,
            args.always_fix_once,
        )

        result = load_result_or_default(project, results_dir)
        scores = result.get("scores", {}) or {}
        nf_sub = result.get("non_functional_subscores", {}) or {}

        def get_sub(k: str) -> float:
            return _f(nf_sub.get(k, scores.get(k, 0.0)), 0.0)

        rows.append({
            "model": args.model,
            "mode": mode_str,
            "strategy": "s1",
            "project": project,
            "functional_score": _f(result.get("functional_score"), 0.0),
            "maintainability": get_sub("maintainability"),
            "security": get_sub("security"),
            "robustness": get_sub("robustness"),
            "efficiency": get_sub("efficiency"),
            "resource": get_sub("resource"),
        })

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"\nAll M1 results written to: {csv_path}")


if __name__ == "__main__":
    main()
