# Reproducibility

## 1. Environment

- Python 3.10 or later.
- `pip install -r requirements.txt` (numpy, matplotlib). The rest of the harness uses only the
  standard library.
- Optional, only to re-run `laya`: the `laya` package and PyTorch (GPU recommended).
- Optional, only to re-run MedGemma: a local [Ollama](https://ollama.com) server with
  `medgemma:27b` pulled.

## 2. API keys

Copy `.env.example` to `.env` and fill in only the providers you will use:

| Variable | Used by |
|---|---|
| `OPENAI_API_KEY` | GPT models |
| `CLAUDE_API_KEY` | Claude models |
| `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | Gemini models |
| `DEEPSEEK_API_KEY` | DeepSeek models |
| `OLLAMA_URL` | local Ollama endpoint (default `http://localhost:11434/api/generate`) |
| `JEV_API_KEY` | `jev` classifier |

`.env` is git-ignored. Never commit keys.

## 3. Data

The dataset is not included in this repository. Download it from Zenodo ([link_zenodo]) or
PhysioNet ([link_physionet]) and place the per-case files as:

```
dataset/data/
├── dev/    case<caseid>.jsonl
├── train/  case<caseid>.jsonl
└── test/   case<caseid>.jsonl
```

`dataset/reports/split_manifest.csv` (included in the repository) provides the split and
difficulty label of each case. Only `test` is needed to reproduce the benchmark.

## 4. Reproducing the analysis from the released predictions

All model predictions are included in `results/test_all.csv` and
`results/consistency_all.csv`. To recompute every table and figure without calling any API
(the dataset is still required for red flags, floors and ordering):

```bash
python src/analyze.py            # → results/analysis/*.csv, report.md, results/img/
python src/analyze_noopioid.py   # → results/analysis/no_opioid_*, subgroup figures
```

`analyze_noopioid.py` reads the per-model subgroup outputs in
`results/data_results/<model>_noopioid/`, which are produced by step 5 below.

## 5. Re-running the full benchmark

Run from the repository root, in this order:

```bash
# 1. LLMs: self-consistency run (100 windows, 3 repeats, seed 42)
python src/llm/run_consistency.py

# 2. LLMs: full test run (1 repeat)
python src/llm/run_full.py

# 3. Classifiers (full run and consistency run)
python src/classification/eval.py --model jev  --split test
python src/classification/eval.py --model laya --split test
python src/classification/eval.py --model jev  --split test --limit 100 --repeats 3 --seed 42
python src/classification/eval.py --model laya --split test --limit 100 --repeats 3 --seed 42

# 4. Deterministic controllers
python src/determinist/run_all.py

# 5. Hypnotic-only subgroup with the 3-option prompt (LLMs + classifiers)
python src/run_noopioid.py

# 6. Consolidate, exclude vasopressor windows, analyse
python src/llm/consolidate.py
python src/llm/filter_vasopressor.py
python src/analyze.py
python src/analyze_noopioid.py
```

A single model can be run directly, e.g.:

```bash
python src/llm/eval.py --model gpt-5.4 --backend openai --split test --workers 8 --resume
```

`--resume` skips windows already saved, so interrupted runs can be continued.

Raw per-model outputs go to `results/data_results/<model>/` (git-ignored). API models may
change over time: results obtained later with the same identifiers are not guaranteed to be
identical.

## 6. Output files

| File | Content |
|---|---|
| `results/test_all.csv` | one row per model × window: letter, predicted action, correctness vs `result_real`, raw response, the three references |
| `results/consistency_all.csv` | same for the 3-repeat run, with the three letters and the consistency score |
| `results/analysis/report.md` | full benchmark report |
| `results/analysis/no_opioid_report.md` | hypnotic-only subgroup report |
| `metrics_summary.csv` | strict / consensus / plausible / weighted per model |
| `ceilings_floors.csv` | human reference zone and floors |
| `classification.csv` | balanced accuracy, macro-F1, κ, intervention index |
| `confusion_<model>.csv` | confusion matrix vs `result_real` |
| `error_taxonomy.csv` | error categories per model |
| `red_flags.csv`, `human_red_flags.csv` | red-flag rates for models and for the references |
| `bootstrap_ci.csv` | case-clustered 95 % CIs |
| `paired_mcnemar.csv` | pairwise McNemar p-values |
| `difficulty.csv` | accuracy by difficulty |
| `consistency_quadrants.csv` | self-consistency analysis |
| `model_agreement.csv` | inter-model agreement and ensemble |
| `no_opioid_subgroup.csv`, `no_opioid_subgroup_meta.csv` | subgroup results and floors |
| `reviewers_agreement.csv`, `reviewers_appropriateness.csv` | external review analysis |

(All `*.csv` above live in `results/analysis/`.)
