# Supplementary material — AnesLLM

Index of supplementary materials. Each item is self-contained within this folder.

| Item | Description | Files |
|---|---|---|
| **S1** | Full instructions (five and three options) and an example case shown to the model | `S01_prompt_example/` (`prompt_5_options.txt`, `prompt_3_options.txt`, `example_case.md`) |
| **S2** | Model identifiers, provider, temperature, verified reasoning and evaluation dates | `S02_model_registry.csv` |
| **S3** | Data dictionary (292 variables) | `S03_data_dictionary.csv` |
| **S4** | Audit results: integrity, leakage, numeric plausibility, drift, missingness and k-anonymity | `S04_audit/` (`audit_report.md`, `split_integrity.csv`, `output_consistency.csv`, `leakage.csv`, `numeric_sanity.csv`, `train_test_drift.csv`, `missingness.csv`, `coverage_by_variable.csv`, `k_anonymity.csv`) |
| **S5** | Classification quality, confusion matrices and error types per system | `S05_classification/` (`classification.csv`, `error_taxonomy.csv`, `confusion_*.csv`) |
| **S6** | Performance by difficulty | `S06_difficulty.csv` |
| **S7** | Consistency across repeats and inter-model agreement | `S07_consistency/` (`consistency_quadrants.csv`, `model_agreement.csv`) |
| **S8** | External review: inter-rater agreement and approval of each reference and strategy | `S08_external_review/` (`reviewers_agreement.csv`, `reviewers_appropriateness.csv`, `human_concordance_redo.csv`) |
| **S9** | Pairwise comparisons (case-clustered McNemar: case-level sign permutation, with Holm-Bonferroni and Benjamini-Hochberg multiplicity correction) | `S09_paired_mcnemar.csv` |
| **S10** | Description of the deterministic controllers and their parameters | `S10_deterministic_controllers/` (`README.md`, `clinical_params.json`, `policies/*.py`) |
| **S11** | TRIPOD-LLM reporting checklist | `S11_TRIPOD_LLM.md` |
| **S12** | Sex and age subgroup analyses: per-sex performance and differences, sex-adjusted (GEE), sex counterfactual (analysis 3), sex opportunity, real actions by sex, and age profile | `S12_sex_age/` |

## Notes

- **S2** gathers the registry of the 18 evaluated systems (12 LLM + 2 classifiers + 4 deterministic controllers). The *reasoning* field comes from `src/verify_reasoning.py` (empirical verification of thinking tokens).
- **S4** includes window-level k-anonymity (two scenarios: demographics only vs. demographics + vitals), computed by rounding quantitative variables to integers. The direct identifiers `pt_caseid`/`pt_subjectid` are present and must be removed before any public release.
- **S5** covers the non-deterministic systems (LLMs and classifiers); the deterministic controllers are described in S10.
- **S8** corresponds to the corrected external review: the reviewers' actual judgment is the `appropriate` column, not `valid_actions` (an internal tooling control).

Generated on 2026-09-28.
