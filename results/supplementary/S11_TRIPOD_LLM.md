# S11. TRIPOD-LLM reporting checklist

Study: **AnesLLM** — a benchmark for anesthetic decision support with language models.

Checklist adapted from TRIPOD+AI / TRIPOD-LLM. Item status: **Yes** (reported), **No** (not applicable / not done), **Partial**, or **—** (not reported / pending). The "Where" column points to the material in this repository.

## A. Title and abstract

| # | Item | Status | Where |
|---|---|---|---|
| 1 | Title/abstract identifies it as an AI (LLM) model and the clinical task | Yes | `README.md`, `results/analysis/report.md` |
| 2 | Objective (anesthetic-decision benchmark) and population (operating room, VitalDB) declared | Yes | `dataset/docs/dataset_design.md` §1–2 |

## B. Introduction

| # | Item | Status | Where |
|---|---|---|---|
| 3 | Clinical context and rationale | Yes | `dataset/docs/dataset_design.md`, `dataset_overview.md` |
| 4 | Study objective (compare models on the task) | Yes | `results/analysis/report.md` |

## C. Methods — data

| # | Item | Status | Where |
|---|---|---|---|
| 5 | Data source (VitalDB, SNUH) | Yes | `dataset/docs/dataset_design.md` §1 |
| 6 | Definition of the decision window (10 min vitals / 20 min history) | Yes | `dataset/docs/dataset_design.md` §2 |
| 7 | Action vocabulary (5 classes + vasopressor as an option) | Yes | `dataset_overview.md` |
| 8 | Inclusion/exclusion criteria and case curation | Yes | `dataset/docs/audit_report.md` §1–9 |
| 9 | Splits (train/dev/test) and how stratification was done | Yes | `dataset_overview.md`, `split_manifest.csv` |
| 10 | Sample size and justification (84,813 windows, 3,168 cases; test partition: 149 cases / 3,424 windows, precision ≈ ±0.02) | Yes | `dataset_overview.md`, `metrics.md` §6 |
| 11 | Input variables (280 fields) and dictionary | Yes | `S03_data_dictionary.csv` |
| 12 | Ground truth (result_real) and alternative references (result_1/result_aux) | Yes | `evaluation_guide.md` §2–3 |
| 13 | Missing values and their handling | Yes | `S04_audit/missingness.csv`, `coverage_by_variable.csv` |
| 14 | Data leakage (audit) | Yes | `S04_audit/leakage.csv` |
| 15 | Privacy / k-anonymity | Partial | `S04_audit/k_anonymity.csv` (direct identifiers present: `pt_caseid`, `pt_subjectid`) |

## D. Methods — models

| # | Item | Status | Where |
|---|---|---|---|
| 16 | Model identifiers, provider and version | Yes | `S02_model_registry.csv` |
| 17 | Full prompt (instructions) | Yes | `S01_prompt_example/prompt_5_options.txt`, `prompt_3_options.txt` |
| 18 | Example of the case shown to the model | Yes | `S01_prompt_example/example_case.md` |
| 19 | Temperature and sampling parameters | Yes | `S02_model_registry.csv` |
| 20 | Verified reasoning (thinking tokens) | Yes | `S02_model_registry.csv` (method: `src/verify_reasoning.py`) |
| 21 | Fine-tuning / domain adaptation | No | Models used off-the-shelf, no fine-tuning |
| 22 | Evaluation dates | Yes | `S02_model_registry.csv` |
| 23 | Deterministic models and classifiers as baselines | Yes | `S10_deterministic_controllers/` |
| 24 | Reproducibility (code) | Yes | `src/` (evaluation harness) |

## E. Methods — evaluation

| # | Item | Status | Where |
|---|---|---|---|
| 25 | Main metrics (strict/consensus/plausible) | Yes | `results/analysis/report.md` §1 |
| 26 | Classification metrics (balanced acc, macro-F1, κ) | Yes | `S05_classification/classification.csv` |
| 27 | Confusion matrices | Yes | `S05_classification/confusion_*.csv` |
| 28 | Error taxonomy | Yes | `S05_classification/error_taxonomy.csv` |
| 29 | Red flags (potentially harmful actions) | Yes | `results/analysis/report.md` §5, `red_flags.csv` |
| 30 | Performance by difficulty | Yes | `S06_difficulty.csv` |
| 31 | Consistency across repeats | Yes | `S07_consistency/consistency_quadrants.csv` |
| 32 | Inter-model agreement | Yes | `S07_consistency/model_agreement.csv` |
| 33 | Pairwise comparisons (case-clustered McNemar, with multiplicity correction) | Yes | `S09_paired_mcnemar.csv` |
| 34 | Uncertainty (bootstrap CIs) | Yes | `results/analysis/bootstrap_ci.csv`, `no_opioid_subgroup_ci.csv` |
| 35 | Clinical review by 3 anesthesiologists (co-authors, not independent) | Yes | `S08_external_review/` (298 windows) |
| 36 | Subgroups (no-opioid) | Yes | `results/analysis/no_opioid_report.md` |

## F. Results

| # | Item | Status | Where |
|---|---|---|---|
| 37 | Performance per model and per reference | Yes | `results/analysis/report.md` §1 |
| 38 | Human ceiling and floors | Yes | `results/analysis/report.md` §2 |
| 39 | External validation results | Yes | `S08_external_review/` |

## G. Discussion and other information

| # | Item | Status | Where |
|---|---|---|---|
| 40 | Limitations | Partial | `dataset/docs/` and notes in `report.md` |
| 41 | Implications and intended use (decision support, not autonomy) | Partial | `README.md` |
| 42 | Availability of code and data | Partial | code in `src/`; data under VitalDB license |
| 43 | Funding / conflicts | Pending | To be declared by the authors |
| 44 | Study registration | Pending | Declare whether registered (e.g., OSF) |

*Note: items marked "Pending" or "Partial" remain to be completed for publication.*
