# CForge

> A unified benchmark and evaluation framework for **C** code generation that jointly measures **functional correctness** (`pass@k`) and **memory safety** (`MSC`, `MSC-pass@k`).

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![HF Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20Dataset-cannhy%2FCForge-yellow)](https://huggingface.co/datasets/cannhy/CForge)

CForge is a unified C code-generation benchmark with a sandboxed evaluator that compiles each generation with `gcc`, runs the test cases, and (in parallel) audits memory behaviour with `valgrind`. CForge is organised into four difficulty tiers:

| Tier | # Problems | Test cases (mean) | I/O type |
|---|---|---|---|
| **CForge-Introductory** | 164 | 6.95 | call-based |
| **CForge-Easy** | 500 | 3.68 | call-based |
| **CForge-Medium** | 5,000 | 21.20 | mostly stdin/stdout |
| **CForge-Hard** | 1,055 | 26.78 | mixed (call & stdin/stdout) |

---

## Table of Contents

- [Highlights](#highlights)
- [Repository Layout](#repository-layout)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Adding a New Model](#adding-a-new-model)
- [Datasets](#datasets)
- [Evaluation Metrics](#evaluation-metrics)
- [Reproducing the Paper Figures](#reproducing-the-paper-figures)
- [Dataset Construction Pipeline](#dataset-construction-pipeline)
- [Citation](#citation)
- [License](#license)

---

## Highlights

- **Two-axis evaluation** — every generation is graded on both functional correctness (`pass@k`) and memory safety (`MSC`, `MSC-pass@k`). A program is counted as fully passing only when it both passes the test cases and exhibits no `valgrind` memory errors.
- **Streaming, crash-resilient generation** — each sample (one of the *n* completions for a problem) is written to disk **immediately** after it returns from the API, so an interrupted run can be resumed without losing any work.
- **Per-sample resume** — re-running the same command continues from exactly where the previous run stopped, even mid-problem (e.g. resume the missing 7 of 10 samples).
- **Pluggable runners** — first-class support for OpenAI-compatible APIs (DeepSeek, Doubao/Volcengine Ark, Luban-Proxy) and local vLLM. Adding a new endpoint takes ~30 LOC.
- **Sandboxed C executor** — each test case is compiled and executed in a separate `spawn` subprocess with stderr redirection, avoiding `glibc` aborts polluting the parent log; `valgrind` runs in a parallel sibling process.
- **Reproducible figures and stats** — every table and plot in the paper has a corresponding script under `scripts/`.

---

## Repository Layout

```
.
├── evaluate/                       # Inference + evaluation pipeline
│   ├── benchmarks/                 # Loaders for the four CForge tiers (HF + local fallback)
│   ├── prompts/                    # Prompt templates per LLM family + few-shot examples
│   ├── runner/                     # API runners: deepseek / doubao / luban / vllm
│   ├── evaluation/                 # gcc + valgrind sandbox, pass@k & MSC metrics
│   ├── utils/                      # Path helpers, code extraction, scenario routing
│   ├── generate_evaluate.py        # Main entry: generate + evaluate end-to-end
│   ├── custom_evaluate.py          # Evaluate an existing generations file
│   ├── llm_styles.py               # Model registry (name → prompt style + runner)
│   └── parser.py                   # CLI arguments
├── iteration_translation/          # Pipeline used to build the four CForge tiers
│   ├── pipeline.py                 # Translation driver (Introductory / Easy / Hard)
│   ├── pipeline_lcb.py             # Translation driver (Medium)
│   ├── few_shots.py / template.py  # Few-shot translation prompts
│   ├── upload2hf.py                # Push curated jsonl to HuggingFace
│   └── config/                     # Model + dataset configuration
├── train/                          # GRPO/PPO training scripts (uses verl/)
├── verl/                           # Vendored verl trainer (reference; can be replaced)
├── scripts/                        # Helper scripts: dataset stats, plots, img→pdf
├── CForge_data/                    # CForge dataset loader (HF dataset script + local jsonl mirror)
├── pics/  pics_pdf/                # Paper figures (raw + PDF-converted)
├── output/                         # Per-(model × benchmark) generations & evaluation logs
├── res.csv                         # Aggregated results table
├── train.sh                        # Example RL training command
└── requirements.txt
```

---

## Installation

### Prerequisites

- **Python ≥ 3.10**
- **GCC** (with the standard C library headers) — used to compile each generated program
- **Valgrind** — used for memory-safety auditing (`brew install valgrind` on macOS / `apt install valgrind` on Linux)
- (Optional) **CUDA + vLLM** if you want to run local open-source models

### From source

```bash
git clone https://github.com/<your-org>/CForge.git
cd CForge
pip install -r requirements.txt
```

### Verify the toolchain

```bash
gcc --version
valgrind --version
```

If `valgrind` is missing the evaluator will print a warning and skip the safety axis (still report `pass@k`).

---

## Quick Start

### 1. Generate **and** evaluate in one command

```bash
python -m evaluate.generate_evaluate \
    --benchmark medium \
    --model Qwen3.5-122B-A10B \
    --luban_model_name Qwen3.5-122B-A10B \
    --n 10 \
    --temperature 0.2 \
    --max_tokens 2048 \
    --multiprocess 20 \
    --evaluate
```

What happens:

1. Loads the **CForge-Medium** split (downloads from [`cannhy/CForge`](https://huggingface.co/datasets/cannhy/CForge) on HuggingFace; falls back to the local mirror at `CForge_data/` if offline).
2. Spawns 20 concurrent worker threads; for each problem, schedules `n=10` independent API calls.
3. **Every sample is appended to disk the moment it completes** (`output/<model>/<tier>/...jsonl`).
4. After generation finishes, runs `gcc + test cases` and `valgrind` in parallel for every sample.
5. Reports `pass@1 / pass@5 / pass@10`, `mem_safe`, `MSC-pass@1`, …

### 2. Evaluate an existing generations file

```bash
python -m evaluate.custom_evaluate \
    --benchmark medium \
    --model Qwen3.5-122B-A10B \
    --custom_output_file output/Qwen3.5-122B-A10B/medium/zero_shot_10_0.2.jsonl
```

### 3. Resume an interrupted run

Just re-run the same `generate_evaluate` command. It will:

- Read the existing `*.jsonl` and detect any problem with fewer than `--n` non-empty completions.
- Only request the **missing** samples for those problems.
- Skip evaluation for problems already in `*_eval_all.jsonl`.

### Common arguments

| Flag | Default | Meaning |
|---|---|---|
| `--benchmark` | `medium` | One of `introductory`, `easy`, `medium`, `hard` |
| `--model` | `Qwen2.5-Coder-7B` | Key in `evaluate/llm_styles.py` (selects prompt style + runner) |
| `--luban_model_name` | (Luban default) | Actual model id forwarded to the Luban proxy |
| `--n` | `10` | Number of completions per problem |
| `--multiprocess` | `10` | Concurrent worker threads (API runners are IO-bound; 20–50 is usually safe) |
| `--temperature` | `0.2` | Sampling temperature |
| `--n_shot` | `0` | Few-shot examples to prepend |
| `--evaluate` | off | Run sandbox evaluation right after generation |
| `--continue_existing` | on | Resume from existing `*.jsonl` |
| `--is_test_correctness` | on | Run pass@k evaluation |
| `--is_test_safety` | on | Run valgrind MSC evaluation |
| `--num_process_evaluate` | `120` | Subprocess workers for sandbox evaluation |

---

## Adding a New Model

1. **Pick a runner**:
   - OpenAI-compatible HTTP API → use `LMStyle.LubanAPI` / `LMStyle.DeepSeekAPI` / `LMStyle.OpenAIChat`.
   - Local weights with vLLM → use `LMStyle.VllmAI` (or any subclass that builds chat prompts).
2. **Register in `evaluate/llm_styles.py`**:

    ```python
    LanguageModel(
        "MyOrg-Coder-13B",        # model_name (CLI --model)
        "MyOrg-Coder-13B",        # short repr used for output paths
        LMStyle.LubanAPI,         # which runner to dispatch to
        datetime(2025, 4, 1),
        link="https://...",
    ),
    ```

3. (Optional) If you need a custom prompt template, add a branch in `evaluate/prompts/code_generation.py`.

That's it — all CLI flags work automatically.

---

## Datasets

CForge is published on the HuggingFace Hub:
👉 **[`cannhy/CForge`](https://huggingface.co/datasets/cannhy/CForge)**

```python
from datasets import load_dataset

# config can be one of: introductory / easy / medium / hard
ds = load_dataset("cannhy/CForge", "medium", split="test")
print(len(ds), ds[0])
```

A local mirror with the same layout is also bundled in `CForge_data/`
(loaded automatically when offline, via `CForge_data/CForge.py`).

| Tier | # Problems | Test cases (mean) | I/O type |
|---|---|---|---|
| **CForge-Introductory** | 164 | 6.95 | call-based |
| **CForge-Easy** | 500 | 3.68 | call-based |
| **CForge-Medium** | 5,000 | 21.20 | mostly stdin/stdout |
| **CForge-Hard** | 1,055 | 26.78 | mixed (call & stdin/stdout) |

To regenerate the statistics table:

```bash
python scripts/dataset_stats.py
```

---

## Evaluation Metrics

For each generation we record:

- **`passed`** — boolean, all test cases produce the expected output.
- **`mem_safe`** — float ∈ [0, 1], `1 / (1 + Σ cap(c))` over valgrind error categories `c`. In the paper we further binarise this to `1.0` ⇔ no errors at all.
- **`msc_correct`** — `passed AND (mem_safe == 1.0)`.

These are aggregated with the unbiased `pass@k` estimator (Chen et al., 2021):

- **`pass@k`** — based on `passed`.
- **`mem_safe`** (mean) — overall fraction of generations that are memory-safe.
- **`MSC-pass@k`** — based on `msc_correct`; the joint metric reported in our paper.

See `evaluate/evaluation/metric_utils.py` for the implementation.

---

## Dataset Construction Pipeline

The translation pipeline used to build CForge lives under `iteration_translation/`. Configure your translator model in `iteration_translation/config/config.yaml`, then:

```bash
python -m iteration_translation.pipeline       # Introductory / Easy / Hard
python -m iteration_translation.pipeline_lcb   # Mediumto HuggingFace
```

Each example is translated with a configurable few-shot prompt, then verified by the same sandbox before being kept.

---

## Citation

If you use CForge or any code in this repository, please cite:

```bibtex

```

---

## License

This project is licensed under the **Apache License 2.0** — see [LICENSE](LICENSE) for details.

The vendored `verl/` directory retains its own license (see `verl/LICENSE`).
