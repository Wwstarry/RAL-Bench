import argparse
import subprocess
import yaml
import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
RESULTS_DIR = ROOT / "results"


def find_all_tasks():
    return sorted(TASKS_DIR.glob("*/**/*.yaml"))


def run_single_task(task_yaml: Path, model_name: str, skip_generation: bool) -> bool:
    cmd = [
        "python",
        "-m",
        "evaluation.run_benchmark",
        "--task",
        str(task_yaml),
    ]

    if skip_generation:
        cmd.append("--skip-generation")

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


def load_result_or_default(project: str) -> dict:
    result_file = RESULTS_DIR / f"{project}_results.yaml"
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


def main(model_name: str, skip_generation: bool):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    suffix = "eval_only" if skip_generation else "gen_and_eval"
    csv_path = RESULTS_DIR / f"{model_name}__{suffix}.csv"

    fieldnames = [
        "model",
        "mode",
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
        mode_str = "eval_only" if skip_generation else "gen_and_eval"
        print(f"\n=== Running {project} ({mode_str}) ===")

        run_single_task(task_yaml, model_name, skip_generation)

        result = load_result_or_default(project)

        # ✅ FIX: subscores may be stored separately (e.g. non_functional_subscores)
        scores = result.get("scores", {}) or {}
        nf_sub = result.get("non_functional_subscores", {}) or {}

        # Prefer explicit non_functional_subscores; fallback to scores
        def get_sub(k: str) -> float:
            if k in nf_sub:
                return _f(nf_sub.get(k), 0.0)
            return _f(scores.get(k), 0.0)

        rows.append({
            "model": model_name,
            "mode": mode_str,
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

    print(f"\nAll results written to: {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--skip-generation", action="store_true")
    args = parser.parse_args()
    main(args.model, args.skip_generation)
