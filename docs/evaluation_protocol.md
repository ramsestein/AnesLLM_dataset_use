# Evaluation protocol

How each model was queried and how its answer was turned into an action. Code:
`src/llm/eval.py` (LLMs), `src/classification/eval.py` (jev, laya),
`src/determinist/` (controllers).

## 1. Prompts

Two prompts are used, both in `src/llm/`:

- **`prompt.txt`** — full benchmark, 5 options (a–e).
- **`prompt_no_opioid.txt`** — hypnotic-only subgroup, 3 options
  (a `increase_hypnotic`, b `reduce_hypnotic`, c `no_action`).

Both ask the model to act as an anesthesiologist, decide **based only on the information
given**, and answer with a single letter. The option order is fixed.

## 2. Case rendering

`render_case()` in `src/llm/eval.py` converts a window into a short English clinical case:

- patient (age, sex, weight, height, BMI, ASA), procedure and context, elective/emergency,
  diagnosis, department, monitoring type;
- **current vitals** from the lower-case fields `hr_current`, `map_current`, `spo2_current`,
  `etco2_current`, `bis_current` (coverage > 97 %; the upper-case `*_current` fields are
  arterial-line instantaneous values and are missing in NIBP cases);
- recent trends (HR, MAP, BIS, SpO₂, EtCO₂);
- propofol and remifentanil effect-site concentrations, expired sevoflurane, MAC;
- ventilator settings (FiO₂, PEEP, tidal volume, respiratory rate);
- preoperative labs (Hb, Hct, platelets, WBC, Na, K, glucose, creatinine, lactate, pH, HCO₃, BE);
- `history_summary`: a text summary of the actions taken so far in the case.

Missing values are omitted rather than shown as null. Identifiers are never rendered.

> Note: an earlier version of the harness rendered the upper-case vital fields, which left HR
> and MAP missing in about a third of the windows. All reported results use the corrected
> rendering.

## 3. Answer parsing

`parse_letter()` accepts a bare letter, a leading letter (`"c)"`, `"c -"`), explicit patterns
(`answer: c`, `option c`) or a bold final letter, and restricts matches to the letters valid
for the prompt (`abcde` or `abc`). Output caps start at 16 tokens and increase
(16 → 64 → 256 → 1024) only if no letter is obtained. Up to three attempts are made for empty
responses or transient errors. Responses that are not a clean letter are counted and reported.

## 4. Model configuration

Temperature 0 was used whenever the API accepted it. Reasoning was **not** set explicitly; each
model ran with its API's default behaviour. Whether reasoning actually occurred was verified
empirically by reading the reasoning-token counters returned by each API
(`src/verify_reasoning.py`).

| Model | Backend | Temperature | Reasoning (verified) |
|---|---|---|---|
| gpt-4o | OpenAI | 0 | no |
| gpt-5.4 | OpenAI | 0 | no |
| gpt-5.4-mini | OpenAI | 0 | no |
| gpt-6-sol | OpenAI | default (0 not accepted) | yes (~34 tokens) |
| claude-haiku-4-5-20251001 | Anthropic | 0 | no (thinking disabled) |
| claude-opus-4-8 | Anthropic | default (0 not accepted) | no (thinking disabled) |
| gemini-3.1-pro-preview | Gemini | 0 | yes (~224 tokens) |
| gemini-3.1-flash-lite | Gemini | 0 | no |
| deepseek-v4-pro | DeepSeek | 0 | yes (~358 tokens) |
| DeepSeek V4.1 Flash | DeepSeek | 0 | yes (~467 tokens) |
| medgemma:27b | Ollama (local) | 0 | no |
| jev, laya | classifiers | N/A | N/A |
| rules, pid, clads, fuzzy | deterministic | N/A | N/A |

Model identifiers are the API names used at evaluation time ([EVALUATION_DATES]).

## 5. Runs

| Run | Windows | Repeats | Script |
|---|---|---|---|
| Full evaluation | all test windows | 1 | `src/llm/run_full.py` |
| Self-consistency | 100 test windows sampled with seed 42 (before vasopressor exclusion) | 3 | `src/llm/run_consistency.py` |
| Hypnotic-only subgroup | 555 windows, 3-option prompt | 1 | `src/run_noopioid.py` |

In the consistency run the predicted action is the majority letter of the three answers.

## 6. Deterministic controllers

Controllers read the same window fields (lower-case vitals and trends), are run in
chronological order within each case and reset their internal state between cases. They are
fully reproducible (consistency = 1 by construction). See
[../src/determinist/README.md](../src/determinist/README.md).

## 7. Consolidation

`src/llm/consolidate.py` merges all per-model outputs (`results/data_results/<model>/`) with the
three references into `results/test_all.csv` and `results/consistency_all.csv`.
`src/llm/filter_vasopressor.py` then removes vasopressor windows from both files.
