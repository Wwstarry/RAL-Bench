# RAL-Bench Fresh-50

This directory contains the auditable source-selection and interface-validation layers for the October 2026 fresh benchmark.

- `candidates.txt`: the reviewed set of exactly 50 public repositories.
- `manifest.json`: repositories that passed the source gate, including GitHub creation time and pinned commit.
- `validation_report.json`: per-check evidence for all candidates.
- `tasks/`: 50 generated task specifications with pinned provenance and six-suite baselines.
- `tests/`: per-task interface, robustness, efficiency, and resource suites.
- `reference_validation_report.json`: strict reference result; all six suites must return zero.
- `semantic_execution_report.json`: execution results for the documented normal/state/error cases.
- `semantic_review_report.json`: oracle-independent second-pass review of those cases and their evidence paths.
- `task_construction_report.json`: selected local public interface for every repository.

The cutoff is `2026-09-01T00:00:00Z` and is applied to GitHub's repository `created_at` field, not the last-push or last-update time.

Use Python 3.12. From the artifact root, run:

```powershell
python scripts/build_fresh_benchmark.py
python -m pip install -r fresh/requirements.txt
python scripts/build_fresh_tasks.py
python scripts/run_all_fresh_reference.py
```

Temporary pinned checkouts are written to ignored `fresh/cache/`.

Upstream tests are not used as benchmark oracles. The current manifest status is
`interface-validated`: all 50 references pass their six suites and have frozen
non-functional baselines. The semantic layer now contains documented normal,
state-transition, and boundary/error cases for all 50 tasks; the execution and
oracle-independent second pass are both 50/50. `semantic_review_complete` remains
false deliberately: the second pass is reproducible maintainer review, not a
claim of a separate external human reviewer. Promote that flag only after such a
review has been performed and recorded.
