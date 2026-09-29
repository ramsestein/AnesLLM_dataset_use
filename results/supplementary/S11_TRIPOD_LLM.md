# S11. TRIPOD-LLM reporting checklist

Estudio: **AnesLLM** — benchmark de soporte a la decisión anestésica con modelos de lenguaje.

Checklist adaptado de TRIPOD+AI / TRIPOD-LLM. Estado por ítem: **Sí** (reportado), **No** (no aplica / no se hizo), **Parcial**, o **—** (no reportado / pendiente). La columna "Dónde" apunta al material de este repositorio.

## A. Título y resumen

| # | Ítem | Estado | Dónde |
|---|---|---|---|
| 1 | El título/abstract identifica que es un modelo de IA (LLM) y la tarea clínica | Sí | `README.md`, `results/analysis/report.md` |
| 2 | Se declara el objetivo (benchmark de decisión anestésica) y la población (quirófano, VitalDB) | Sí | `dataset/docs/dataset_design.md` §1–2 |

## B. Introducción

| # | Ítem | Estado | Dónde |
|---|---|---|---|
| 3 | Contexto clínico y justificación | Sí | `dataset/docs/dataset_design.md`, `dataset_overview.md` |
| 4 | Objetivo del estudio (comparar modelos sobre la tarea) | Sí | `results/analysis/report.md` |

## C. Métodos — datos

| # | Ítem | Estado | Dónde |
|---|---|---|---|
| 5 | Fuente de datos (VitalDB, SNUH) | Sí | `dataset/docs/dataset_design.md` §1 |
| 6 | Definición de la ventana de decisión (10 min vitales / 20 min historial) | Sí | `dataset/docs/dataset_design.md` §2 |
| 7 | Vocabulario de acciones (5 clases + vasopressor como opción) | Sí | `dataset_overview.md` |
| 8 | Criterios de inclusión/exclusión y curación de casos | Sí | `dataset/docs/audit_report.md` §1–9 |
| 9 | Splits (train/dev/test) y cómo se estratificó | Sí | `dataset_overview.md`, `split_manifest.csv` |
| 10 | Tamaño de la muestra y justificación (84 813 ventanas, 3 168 casos; partición de prueba: 149 casos / 3 424 ventanas, precisión ≈ ±0.02) | Sí | `dataset_overview.md`, `metrics.md` §6 |
| 11 | Variables de entrada (280 campos) y diccionario | Sí | `S03_data_dictionary.csv` |
| 12 | Ground truth (result_real) y referencias alternativas (result_1/result_aux) | Sí | `evaluation_guide.md` §2–3 |
| 13 | Ausentes y su tratamiento | Sí | `S04_audit/missingness.csv`, `coverage_by_variable.csv` |
| 14 | Fuga de información (auditoría) | Sí | `S04_audit/leakage.csv` |
| 15 | Privacidad / k-anonimato | Parcial | `S04_audit/k_anonymity.csv` (identificadores directos presentes: `pt_caseid`, `pt_subjectid`) |

## D. Métodos — modelos

| # | Ítem | Estado | Dónde |
|---|---|---|---|
| 16 | Identificadores de modelo, proveedor y versión | Sí | `S02_model_registry.csv` |
| 17 | Prompt completo (instrucciones) | Sí | `S01_prompt_example/prompt_5_options.txt`, `prompt_3_options.txt` |
| 18 | Ejemplo del caso presentado al modelo | Sí | `S01_prompt_example/example_case.md` |
| 19 | Temperatura y parámetros de muestreo | Sí | `S02_model_registry.csv` |
| 20 | Razonamiento verificado (tokens de thinking) | Sí | `S02_model_registry.csv` (método: `src/verify_reasoning.py`) |
| 21 | Ajuste fino / adaptación al dominio | No | Los modelos se usan off-the-shelf, sin fine-tuning |
| 22 | Fechas de evaluación | Sí | `S02_model_registry.csv` |
| 23 | Modelos deterministas y clasificadores como baselines | Sí | `S10_deterministic_controllers/` |
| 24 | Reproducibilidad (código) | Sí | `src/` (harness de evaluación) |

## E. Métodos — evaluación

| # | Ítem | Estado | Dónde |
|---|---|---|---|
| 25 | Métricas principales (strict/consensus/plausible) | Sí | `results/analysis/report.md` §1 |
| 26 | Métricas de clasificación (balanced acc, macro-F1, κ) | Sí | `S05_classification/classification.csv` |
| 27 | Matrices de confusión | Sí | `S05_classification/confusion_*.csv` |
| 28 | Taxonomía de errores | Sí | `S05_classification/error_taxonomy.csv` |
| 29 | Red flags (acciones potencialmente dañinas) | Sí | `results/analysis/report.md` §5, `red_flags.csv` |
| 30 | Rendimiento por dificultad | Sí | `S06_difficulty.csv` |
| 31 | Consistencia entre repeticiones | Sí | `S07_consistency/consistency_quadrants.csv` |
| 32 | Acuerdo entre modelos | Sí | `S07_consistency/model_agreement.csv` |
| 33 | Comparaciones por pares (McNemar agrupado por caso, con corrección de multiplicidad) | Sí | `S09_paired_mcnemar.csv` |
| 34 | Incertidumbre (IC por bootstrap) | Sí | `results/analysis/bootstrap_ci.csv`, `no_opioid_subgroup_ci.csv` |
| 35 | Revisión clínica por 3 anestesistas (coautores, no independientes) | Sí | `S08_external_review/` (298 ventanas) |
| 36 | Subgrupos (no-opioide) | Sí | `results/analysis/no_opioid_report.md` |

## F. Resultados

| # | Ítem | Estado | Dónde |
|---|---|---|---|
| 37 | Rendimiento por modelo y por referencia | Sí | `results/analysis/report.md` §1 |
| 38 | Techo humano y suelos | Sí | `results/analysis/report.md` §2 |
| 39 | Resultados de la validación externa | Sí | `S08_external_review/` |

## G. Discusión y otra información

| # | Ítem | Estado | Dónde |
|---|---|---|---|
| 40 | Limitaciones | Parcial | `dataset/docs/` y notas de `report.md` |
| 41 | Implicaciones y uso previsto (soporte a la decisión, no autonomía) | Parcial | `README.md` |
| 42 | Disponibilidad de código y datos | Parcial | código en `src/`; datos bajo licencia VitalDB |
| 43 | Financiación / conflictos | Pendiente | Declarar por los autores |
| 44 | Registro del estudio | Pendiente | Declarar si se registró (p. ej. OSF) |

*Nota: los ítems marcados "Pendiente" o "Parcial" quedan pendientes de completar para la publicación.*
