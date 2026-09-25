# AnesLLM benchmark — evaluating LLMs on real intraoperative anesthesia decisions

This repository contains the evaluation harness, baselines, analysis code and results of the
**AnesLLM benchmark**: a benchmark that asks language models to choose the next anesthetic
adjustment (hypnotic / opioid / no action) in real intraoperative situations, and compares their
choices with what anesthesiologists actually did.

- **Dataset:** [link_zenodo] · PhysioNet: [link_physionet]
- **Paper:** [link_paper]
- **Source data:** decision windows derived from [VitalDB](https://vitaldb.net)
  (Seoul National University Hospital).

> The dataset itself is **not** distributed in this repository. Download it from Zenodo or
> PhysioNet and place it as described in [docs/reproducibility.md](docs/reproducibility.md).

## What the benchmark measures

Each test item is a *decision window*: everything observable during the 10 minutes before an
anesthetic decision (patient and surgery, preoperative labs, vital signs and trends, drug
effect-site concentrations, ventilator settings and a summary of the actions taken so far). The
model must choose one of five actions:

`increase_hypnotic` · `reduce_hypnotic` · `increase_opioid` · `reduce_opioid` · `no_action`

Answers are scored against three references:

| Reference | What it is |
|---|---|
| `result_real` | the action the anesthesiologist actually took in the operating room |
| `result_1` | consensus action: top-1 of a LightGBM model trained on the actions of all clinicians in the cohort (case-grouped out-of-fold) |
| `result_aux` | second most likely consensus action |

In anesthesia there is often more than one acceptable action, so results are reported as
**strict** (= `result_real`), **consensus** (= `result_1`) and **plausible**
(∈ {`result_1`, `result_aux`}), together with a **human reference zone** (how often the real
clinician agrees with the consensus), trivial **floors**, and a physiology-based **safety**
analysis (red flags). See [docs/metrics.md](docs/metrics.md).

## Models evaluated

11 LLMs (GPT-4o, GPT-5.4, GPT-5.4 mini, GPT-6 Sol, Claude Haiku 4.5, Claude Opus 4.8,
Gemini 3.1 Pro, Gemini 3.1 Flash-Lite, DeepSeek V4 Pro, DeepSeek V4.1 Flash, MedGemma 27B),
2 third-party structured classifiers (`jev`, `laya`) and 4 deterministic anesthesia controllers
(`rules`, `pid`, `clads`, `fuzzy`). Configuration per model (backend, temperature, verified
reasoning) is in [docs/evaluation_protocol.md](docs/evaluation_protocol.md).

## Key results (test split, 3,424 windows, 149 cases)

| | consensus | plausible |
|---|---|---|
| Human reference zone (real clinician vs consensus) | 0.570 | 0.816 |
| Best LLM | 0.327 (GPT-5.4) | 0.541 (DeepSeek V4.1 Flash) |
| Floor: always `no_action` (strict) | 0.271 | — |
| Floor: repeat previous action (strict) | 0.325 | — |

- LLMs remain far from the human reference zone.
- In the hypnotic-only subgroup (3-option prompt, same action space as the controllers), the
  best recent LLMs match the deterministic controllers, and **all systems score below the
  trivial "always `no_action`" floor** (0.643 strict).
- The four models with the lowest red-flag rates are the four that reason (GPT-6 Sol,
  DeepSeek V4.1 Flash, DeepSeek V4 Pro, Gemini 3.1 Pro), all below the clinician's own rate
  (0.032).

Full tables: [results/analysis/report.md](results/analysis/report.md) and
[results/analysis/no_opioid_report.md](results/analysis/no_opioid_report.md).

## Repository layout

```
src/
├── llm/                 # LLM harness: prompts, API backends, runners, consolidation
├── classification/      # jev / laya structured classifiers
├── determinist/         # deterministic controllers (rules, PID, CLADS, fuzzy)
├── analyze.py           # full analysis → results/analysis/report.md
├── run_noopioid.py      # 3-option evaluation of the hypnotic-only subgroup
└── analyze_noopioid.py  # subgroup analysis → results/analysis/no_opioid_report.md
dataset/
├── docs/                # dataset documentation (design, overview, audit, loading guide)
└── reports/             # data dictionary, split manifest, audits, strategy tables
results/
├── test_all.csv         # all predictions, one row per model × window
├── consistency_all.csv  # 3-repeat self-consistency run (100 windows, seed 42)
├── analysis/            # metric tables (CSV) and reports (Markdown)
└── img/                 # figures
docs/                    # benchmark documentation (this repo)
```

## Documentation

| Document | Content |
|---|---|
| [docs/benchmark_design.md](docs/benchmark_design.md) | Task, references, human reference zone, subgroup, models and baselines |
| [docs/evaluation_protocol.md](docs/evaluation_protocol.md) | Prompts, case rendering, parsing, API settings, reasoning verification, consistency run |
| [docs/metrics.md](docs/metrics.md) | Definition of every metric and statistical procedure |
| [docs/reproducibility.md](docs/reproducibility.md) | Setup, data placement, run order, map of output files |
| [docs/limitations.md](docs/limitations.md) | Known limitations and design decisions |
| [dataset/docs/](dataset/docs/) | How the dataset was built and audited |

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env            # add the API keys you need
# place the dataset under dataset/data/{dev,train,test}/  (see docs/reproducibility.md)
python src/analyze.py           # recomputes all tables from results/*.csv
```

Re-running the models requires API access and is described step by step in
[docs/reproducibility.md](docs/reproducibility.md).

## Ethics

The study was conducted as an *in silico* development and evaluation study on the public,
de-identified VitalDB dataset.

## License

Code: [LICENSE_CODE] (see [LICENSE](LICENSE)). The dataset is distributed separately under the
terms stated on Zenodo/PhysioNet, which must be compatible with the VitalDB data license.
