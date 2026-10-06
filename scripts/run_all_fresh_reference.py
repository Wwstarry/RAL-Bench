"""Validate all Fresh-50 references and freeze their six-suite baselines."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def validate(task_path: Path) -> dict[str, Any]:
    task = yaml.safe_load(task_path.read_text(encoding="utf-8")) or {}
    command = [
        sys.executable, "-m", "evaluation.measure_reference", str(task_path),
        "--target-env", "RAL_FRESH_TARGET", "--reference-value", "reference",
    ]
    result = subprocess.run(
        command, cwd=ROOT, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=240,
    )
    passed = result.returncode == 0
    return {
        "task_id": task.get("task_id", task_path.parent.name),
        "passed": passed,
        "returncode": result.returncode,
        "output_tail": "" if passed else "\n".join((result.stdout or "").splitlines()[-30:]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    paths = sorted((ROOT / "fresh" / "tasks").glob("*/*.yaml"))
    if len(paths) != 50:
        raise RuntimeError(f"expected 50 Fresh task files, found {len(paths)}")
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        jobs = {executor.submit(validate, path): path for path in paths}
        for job in as_completed(jobs):
            row = job.result()
            rows.append(row)
            state = "PASS" if row["passed"] else "FAIL"
            print(f"[{len(rows):02d}/50] {state} {row['task_id']}", flush=True)
    rows.sort(key=lambda row: row["task_id"])
    report = {
        "benchmark": "RAL-Bench Fresh-50",
        "checked": len(rows),
        "passed": sum(row["passed"] for row in rows),
        "failed": sum(not row["passed"] for row in rows),
        "tasks": rows,
    }
    path = ROOT / "fresh" / "reference_validation_report.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if report["failed"] == 0:
        manifest_path = ROOT / "fresh" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["construction_status"] = "interface-validated"
        manifest["semantic_review_complete"] = False
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(f"Fresh reference validation: {report['passed']}/50 passed")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
