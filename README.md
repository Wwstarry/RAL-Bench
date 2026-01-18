# RealAppCodeBench_Stegano

This benchmark example is built on top of the **original Stegano project**:

    https://github.com/cedricbonhomme/Stegano

## Directory structure

RealAppCodeBench_Stegano/
├── tasks/
│   └── Stegano/
│       └── stegano_lsb_image.yaml
├── repositories/
│   └── Stegano/
│       └── README.md   (you must clone the real repo here)
├── tests/
│   └── Stegano/
│       └── stegano_lsb_image/
│           ├── functional/
│           ├── performance/
│           ├── resource/
│           └── tests_sample_files/
├── evaluation/
│   ├── measure_reference_stegano.py
│   ├── evaluate_model_repo_stegano.py
│   └── run_benchmark_stegano.py
├── generation/
│   └── Stegano/
│       └── stegano_lsb_image/
└── README.md

## 0. Clone the original Stegano repository

From the project root:

```bash
cd repositories
git clone https://github.com/cedricbonhomme/Stegano.git
```

Then install dependencies:

```bash
cd Stegano
pip install .
pip install Pillow psutil pytest pyyaml openai
```

## 1. Measure baseline metrics

From the project root:

```bash
cd evaluation
python measure_reference_stegano.py
```

This uses the original `repositories/Stegano` implementation to measure
average hide/reveal time and resource usage and writes them into:

```text
tasks/Stegano/stegano_lsb_image.yaml
```

under `baseline_metrics`.

## 2. Run end-to-end benchmark with gpt-4o-mini

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="sk-..."
```

Then run:

```bash
cd evaluation
python run_benchmark_stegano.py
```

This will:

1. Read the task description from `tasks/Stegano/stegano_lsb_image.yaml`.
2. Call **gpt-4o-mini** via the OpenAI Python SDK to generate a new repository
   under `generation/Stegano/stegano_lsb_image/`.
3. Evaluate the generated implementation using `evaluate_model_repo_stegano.py`
   (functional + performance + resource, compared to baseline).
4. Save a JSON result at:

```text
generation/Stegano/stegano_lsb_image/result_stegano_lsb_image.json
```

## Notes

- `repositories/Stegano` holds the original GitHub project, unchanged.
- `tests/Stegano/...` holds benchmark-specific black-box tests for this task.
- `tasks/Stegano/...` is the machine-readable task definition (English, no redundancy).
