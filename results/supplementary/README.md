# Material suplementario — AnesLLM

Índice de materiales suplementarios. Cada ítem es autocontenido dentro de esta carpeta.

| Ítem | Descripción | Ficheros |
|---|---|---|
| **S1** | Instrucciones completas (cinco y tres opciones) y un ejemplo de caso presentado al modelo | `S01_prompt_example/` (`prompt_5_options.txt`, `prompt_3_options.txt`, `example_case.md`) |
| **S2** | Identificadores de modelo, proveedor, temperatura, razonamiento verificado y fechas de evaluación | `S02_model_registry.csv` |
| **S3** | Diccionario de datos (292 variables) | `S03_data_dictionary.csv` |
| **S4** | Resultados de la auditoría: integridad, fuga, plausibilidad numérica, deriva, ausentes y k-anonimato | `S04_audit/` (`audit_report.md`, `split_integrity.csv`, `output_consistency.csv`, `leakage.csv`, `numeric_sanity.csv`, `train_test_drift.csv`, `missingness.csv`, `coverage_by_variable.csv`, `k_anonymity.csv`) |
| **S5** | Calidad de clasificación, matrices de confusión y tipos de error por sistema | `S05_classification/` (`classification.csv`, `error_taxonomy.csv`, `confusion_*.csv`) |
| **S6** | Rendimiento por dificultad | `S06_difficulty.csv` |
| **S7** | Consistencia entre repeticiones y acuerdo entre modelos | `S07_consistency/` (`consistency_quadrants.csv`, `model_agreement.csv`) |
| **S8** | Revisión externa: acuerdo entre revisores y aprobación de cada referencia y estrategia | `S08_external_review/` (`reviewers_agreement.csv`, `reviewers_appropriateness.csv`, `human_concordance_redo.csv`) |
| **S9** | Comparaciones por pares (McNemar, con corrección de multiplicidad Holm-Bonferroni y Benjamini-Hochberg) | `S09_paired_mcnemar.csv` |
| **S10** | Descripción de los controladores deterministas y de sus parámetros | `S10_deterministic_controllers/` (`README.md`, `clinical_params.json`, `policies/*.py`) |
| **S11** | Lista de verificación TRIPOD-LLM | `S11_TRIPOD_LLM.md` |

## Notas

- **S2** reúne el registro de los 18 sistemas evaluados (12 LLM + 2 clasificadores + 4 controladores deterministas). El campo *razonamiento* proviene de `src/verify_reasoning.py` (verificación empírica de tokens de pensamiento).
- **S4** incluye el k-anonimato a nivel de ventana (dos escenarios: solo demografía vs. demografía + vitales), calculado redondeando las variables cuantitativas a enteros. Los identificadores directos `pt_caseid`/`pt_subjectid` están presentes y deben eliminarse antes de cualquier liberación pública.
- **S5** cubre los sistemas no deterministas (LLM y clasificadores); los controladores deterministas se describen en S10.
- **S8** corresponde a la revisión externa corregida: el juicio real de los revisores es la columna `appropriate`, no `valid_actions` (control interno de la herramienta).

Generado el 2026-09-28.
