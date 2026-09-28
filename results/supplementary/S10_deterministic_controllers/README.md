# Deterministic baselines (anesthesia controllers)

Self-contained folder with the **4 deterministic models** used as the "non-LLM"
baseline in the AnesLLM benchmark. They answer one concrete question: *what
accuracy does a classic controller (clinical rules / PID / fuzzy logic) reach
versus the LLMs, on the same decision task?*

They use no language, generate no text and are 100% reproducible: same input →
same output, always.

## The 4 models

| Model | Type | Inspired by | Core idea |
|---|---|---|---|
| `rules` | Clinical threshold lookup | Liu 2006, Sakai 2000 | Reactive protocol: BIS/MAP out of band → fixed action |
| `pid` | BIS PID controller | Aubouin-Pairault 2023/2024 (PAS) | Tracks BIS setpoint = 50 with Kp/Ti/Td gains + anti-windup |
| `clads` | Gradient with dead-zone | Hemmerling (McSleepy/CLADS) | Adjusts propofol by integrated BIS error with dead-zone and hysteresis |
| `fuzzy` | Fuzzy logic (Mamdani) | Shieh 2006 | Fuzzifies BIS error and derivative, defuzzifies to an action |

All four control the **hypnotic** (propofol/BIS). They **do not emit opioid
actions**: their output space is the 3-option hypnotic set
(`increase_hypnotic` / `reduce_hypnotic` / `no_action`). A single safety gate
maps hypotension to `no_action` (see below).

## How we adapted them

The controllers come from `D:\anesllm\anesllm_bench\policies\` (an anesthesia
simulation project). We brought them into `src/determinist/policies/` and made
them **self-contained**:

1. **Copied the 4 policies** (`base.py`, `rule_policy.py`, `pid_policy.py`,
   `clads_policy.py`, `fuzzy_policy.py`) and `clinical_params.json` (clinical
   parameters as JSON).
2. **Import patch**: the policies used `from ..config import …` (the original
   project's package). Rewritten to `from config import …` so they work as flat
   modules inside `src/determinist/`.
3. **Action patch**: the original action space included `"vasopressor"`. Since
   the AnesLLM benchmark has no vasopressors (and those windows are excluded
   from the analysis), every `return "vasopressor"` became `return "no_action"`.
4. **Self-contained `config.py`**: loads the local `clinical_params.json` and
   exposes only the constants used (thresholds, rates, gains). No external
   dependencies.
5. **Shared safety gate** (see below): the controllers only emit
   hypnotic/`no_action`, matching the 3-option action space of the hypnotic-only
   subgroup.

## Shared architecture (`common.py`)

- `build_row(inp)`: maps the dataset input to the keys the policies expect.
  **Important**: the **lowercase** fields are used (`map_current`,
  `hr_current`, `bis_current`), because the uppercase variants (`MAP_current`,
  `HR_current`, …) are `null` in ~50% of windows (NIBP cases). Trends
  (`hr_trend`, `bis_trend`, `map_trend`) are also passed.
- `evaluate(policy_factory, name)`: runs the policy over the full test set,
  **resetting state on case change** (the stateful controllers — PID/CLADS —
  must not carry memory across patients).
- `apply_analgesia(action, row)`: safety gate described below.
- `write_test` / `write_consistency` / `compute_summary`: produce
  `results/data_results/<name>/test.jsonl` + `summary.json` and
  `<name>_repeats3/` with **the same format as the LLMs**, so the
  consolidation/analysis pipeline treats all models identically.

## Safety gate

The original controllers only act on BIS/propofol (hypnotic). We added a single
safety gate on top of the hypnotic decision:

1. `MAP < 65` → `no_action` (safety: hypotension, do not raise the hypnotic).
2. Otherwise, the hypnotic action of the policy is kept (or `no_action`).

The controllers **never** emit opioid actions; their action space is the
3-option hypnotic set (`increase_hypnotic` / `reduce_hypnotic` / `no_action`),
so they are compared on the hypnotic-only subgroup.

## How each controller works

### `rules` — clinical thresholds (reactive)
Evaluates in priority order and returns the first matching rule:
`MAP < 65` → `no_action`; `BIS > 65` → `increase_hypnotic`;
`BIS > 60` → `increase_hypnotic`; `BIS < 35` → `reduce_hypnotic`;
`BIS < 40` → `reduce_hypnotic`; otherwise `no_action`.
No memory, no integration.

### `pid` — robust BIS PID
Tracks `BIS = 50` with a discrete parallel-form PID: `Kp = 0.001`,
`Ti = 500 s`, `Td = 80 s`, derivative with low-pass filter (`τ = 50 s`) and
anti-windup (`±0.1`). The propofol increment is discretized to an action with a
10% relative threshold on the current rate. Safety layers: `MAP < 65` override
(`HR < 45` bradycardia safety).

### `clads` — gradient with dead-zone
Computes the integrated BIS error over the last window (trapezoid rule) and
decides with hysteresis: `BIS > setpoint + 5` → `increase_hypnotic` (extra boost
if `BIS > setpoint + 15`), `BIS < setpoint − 5` → `reduce_hypnotic`, else
`no_action`. Limits consecutive same-direction actions (`max_same = 3`) to avoid
runaway dosing.

### `fuzzy` — fuzzy logic (Mamdani)
Inputs: error `e = BIS − 50` and its derivative. Fuzzy sets for `e`
(NL/NM/NS/ZE/PS/PM/PL) and for `de/dt` (decreasing/stable/increasing), Mamdani
rule base and defuzzification. Output `≥ +1` → `increase_hypnotic`,
`≤ −1` → `reduce_hypnotic`, otherwise `no_action`.

## Running and integration

```powershell
python src/determinist/run_all.py            # evaluates all 4 (test + consistency)
python src/determinist/rules.py              # rules only (or pid/clads/fuzzy.py)
```

Each one writes `results/data_results/<name>/test.jsonl` + `summary.json` and
`<name>_repeats3/` (deterministic consistency = **1.0**). They are then
consolidated with the rest of the models (`src/llm/consolidate.py`) and enter
`src/analyze.py` as one more group.

## Reference results (strict accuracy, indicative)

| Model | Accuracy |
|---|---|
| `rules` | ~0.250 |
| `fuzzy` | ~0.228 |
| `clads` | ~0.224 |
| `pid` | ~0.157 |

They sit below the best LLM (~0.30) and far below the human ceiling (consensus
0.57 / plausible 0.82), but with **zero safety red flags** (raising hypnotic
with BIS<40 or MAP<65): safe by construction, at the cost of less accuracy.
