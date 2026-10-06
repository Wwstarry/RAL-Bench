"""Gate Fresh-50 semantic evidence and second-pass review before release."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FRESH = ROOT / "fresh"


def main() -> int:
    tasks = sorted((FRESH / "tasks").glob("*/*.yaml"))
    assert len(tasks) == 50, f"expected 50 tasks, found {len(tasks)}"
    errors: list[str] = []
    for path in tasks:
        task = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        task_id = task.get("task_id", path.parent.name)
        curation = task.get("curation") or {}
        cases = curation.get("semantic_cases") or []
        if not cases:
            errors.append(f"{task_id}: no semantic cases")
            continue
        blob = json.dumps(cases, ensure_ascii=False).lower()
        evidence = any(key in blob for key in ("source", "evidence", "readme", "docs/"))
        if not evidence:
            errors.append(f"{task_id}: semantic cases have no public-document evidence")
        if not any(key in blob for key in ("boundary", "exception_boundary", "invalid", "error", "reject", "malformed", "covers")):
            errors.append(f"{task_id}: no explicit exceptional/boundary behavior")
        functional = (FRESH / "tests" / task_id / "functional_test.py").read_text(encoding="utf-8")
        robustness = (FRESH / "tests" / task_id / "robustness_test.py").read_text(encoding="utf-8")
        test_count = (functional + robustness).count("def test_")
        if test_count < 7:
            errors.append(f"{task_id}: semantic suites contain no additional behavior tests")

    review_path = FRESH / "semantic_review_report.json"
    if not review_path.is_file():
        errors.append("missing semantic_review_report.json")
    else:
        report = json.loads(review_path.read_text(encoding="utf-8"))
        reviews = report.get("tasks") or []
        if len(reviews) != 50 or any(row.get("status") != "passed" for row in reviews):
            errors.append("second-pass review is not 50/50 passed")

    if errors:
        print("Fresh semantic validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Fresh semantic validation passed: 50/50 documented cases and second-pass reviews")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
