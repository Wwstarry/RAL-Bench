# RAL-Bench

RAL-Bench is an **application-level** benchmark that asks a simple but under-explored question:

> **Can current LLMs generate application-level repositories that satisfy functional correctness *and* non-functional quality?**

### Construction pipeline
![Construction pipeline](pic/construction_pipeline.png)

### Evaluation pipeline
![Evaluation pipeline](pic\evaluation_pipline.png)

---

## What this repository provides (Contributions)

This repository contains the full artifact for RAL-Bench, including reference projects, task configs, system tests, and the end-to-end evaluation pipeline.

**Core contributions:**
- We define application-level repository generation as a benchmark setting where a model generates a complete repository from a concise natural-language requirement and an expected public module/package surface. The generated repository is evaluated through installation, import, execution, and black-box system tests.
- We present RAL-Bench, a benchmark built from real GitHub projects with reference-validated executable tests. It measures tested functional behavior and reports separate non-functional quality signals, including maintainability, security risk, robustness, efficiency, and resource usage.
- We evaluate 16 frontier LLMs under a controlled zero-shot, single-turn setting. The results show that functional behavior remains the main bottleneck, and that per-dimension non-functional scores reveal additional differences among generated repositories.

---


## Repository structure

The repository is organized around **(1) benchmark construction & execution**, **(2) task/test assets**, and **(3) experiment outputs**.

```
RAL-Bench/
├── 📂 Exp1/                 # RQ1: generated applications + evaluation artifacts/results
├── 📂 Exp2/                 # RQ2: evaluation artifacts/results
├── 📂 Exp4/                 # RQ4: evaluation artifacts/results
├── 📂 evaluation/            # Core pipeline: build benchmark + run end-to-end evaluation
├── 📂 repositories/          # Reference repositories (ground-truth code snapshots)
├── 📂 results/               # Results produced during evaluation runs (reports/logs/json/csv, etc.)
├── 📂 tasks/                 # Task configs + reference (baseline) values for non-functional metrics
├── 📂 tests/                 # System tests for all tasks (functional + non-functional)
├── 📂 scripts/               # Helper scripts (data prep / analysis / plotting / utilities)
├── 📂 tmp_perf/              # Temporary artifacts for performance measurement (cache/intermediate)
├── 📂 tmp_resource/          # Temporary artifacts for resource measurement (cache/intermediate)
├── 📂 .venv/                 # Local virtual environment
└── 📂 .converted/            # Local conversion/intermediate folder
```

### 📂 Key directories

- 📂 **`Exp1/`**  
  Stores **all applications generated for RQ1** and the **evaluation-produced artifacts** (e.g., per-run logs, intermediate files, per-task outputs).  
  This folder preserves *exact rerunnable* experimental traces for the RQ1 setting.

- 📂 **`evaluation/`**  
  The **main implementation** of the benchmark: constructing the benchmark view, executing end-to-end system tests, collecting metrics, and producing final scores/results.

- 📂 **`repositories/`**  
  Contains the **reference (ground-truth) code repositories**, typically pinned/snapshotted for reproducibility.

- 📂 **`results/`**  
  Stores **outputs generated during evaluation runs**, typically aggregated or summarized artifacts (e.g., final reports, consolidated CSV/JSON, and global logs).

- 📂 **`tasks/`**  
  Holds **per-task configurations** and the **reference values** used for non-functional metric baselines.

- 📂 **`tests/`**  
  All **system tests** for the tasks, including functional correctness tests and non-functional checks.


## Quickstart (2 steps)


### 1) Set API environment variables (PowerShell)
```powershell
$env:OPENAI_API_KEY="your_api_key"
$env:OPENAI_BASE_URL="your_base_url"
```

### 2) Run all benchmarks for a model
```powershell
python -m evaluation.run_all_benchmarks --model <model>
```

