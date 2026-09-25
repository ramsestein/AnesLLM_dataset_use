# Benchmark design

This document describes what the AnesLLM benchmark asks of a model, what its answers are
compared against, and which systems were evaluated. How the dataset itself was built is
described in [../dataset/docs/dataset_design.md](../dataset/docs/dataset_design.md).

## 1. Task

Each item is an intraoperative **decision window** from the `test` split of the AnesLLM
dataset (149 cases, 3,457 windows; 3,424 after excluding vasopressor windows, see §4).
The model receives the state of the patient at the decision point and must choose **one**
action:

| Letter | Action |
|---|---|
| a | `increase_hypnotic` |
| b | `reduce_hypnotic` |
| c | `increase_opioid` |
| d | `reduce_opioid` |
| e | `no_action` |

The model sees only information available **before** the decision. The window is rendered as a
short clinical case in English (see [evaluation_protocol.md](evaluation_protocol.md) §2):
patient and surgery, monitoring type, current vital signs (HR, MAP, SpO₂, EtCO₂, BIS), recent
trends, drug effect-site concentrations (propofol, remifentanil), sevoflurane/MAC, ventilator
settings, preoperative labs and a text summary of the actions taken so far in the case.
Direct identifiers are never included in the prompt.

## 2. References

Every window carries three reference answers:

- **`result_real`** — the action the anesthesiologist actually performed in the operating
  room. It is the reference for human behaviour. The clinician had information that is not in
  the data (the patient, the surgical field, events in the room).
- **`result_1`** — the consensus action: top-1 prediction of a LightGBM model trained to
  predict `result_real` from the window, using case-grouped out-of-fold predictions (the case
  being scored is never in the training folds). It estimates the modal action of the clinician
  population in that state.
- **`result_aux`** — the second most likely consensus action.

Because several actions are often clinically acceptable, the benchmark does not assume a single
correct answer. Results are reported against all three references (strict, consensus,
plausible; see [metrics.md](metrics.md)).

## 3. Human reference zone

The agreement between the real clinician and the consensus is used as the **human reference
zone**: 0.570 against `result_1` and 0.816 against {`result_1`, `result_aux`}. It is computed
on the full test set, where the clinician had all five options and full information.

It is **not** an upper bound in the strict sense. It indicates where human decisions score
when placed in this benchmark, and is used as the reference zone in the figures (also for the
hypnotic-only subgroup, where models have only three options).

## 4. Exclusions

Windows in which any reference (`result_real`, `result_1` or `result_aux`) is `vasopressor` are
excluded from all analyses, because vasopressors are not among the options offered to the
models (33 windows; `src/llm/filter_vasopressor.py`).

## 5. Hypnotic-only subgroup

The deterministic controllers only act on the hypnotic. To compare them with the LLMs on equal
terms, a subgroup is defined with the windows where **no** reference is an opioid or a
vasopressor (555 windows; class distribution: 357 `no_action`, 131 `reduce_hypnotic`,
67 `increase_hypnotic`).

- LLMs and classifiers are re-run on this subgroup with a **3-option prompt**
  (`increase_hypnotic`, `reduce_hypnotic`, `no_action`), the same action space as the
  controllers.
- The subgroup is selected using the reference labels. It is a device for a fair comparison,
  not a deployment scenario.
- With three options, "plausible" (top-2) is close to saturation; strict and consensus accuracy
  are the informative metrics there.

## 6. Systems evaluated

### 6.1 LLMs (11)

| Model | Provider / backend |
|---|---|
| `gpt-4o`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-6-sol` | OpenAI API |
| `claude-haiku-4-5-20251001`, `claude-opus-4-8` | Anthropic API |
| `gemini-3.1-pro-preview`, `gemini-3.1-flash-lite` | Google Gemini API |
| `deepseek-v4-pro`, DeepSeek V4.1 Flash (`deepseek-flash` in the result files) | DeepSeek API |
| `medgemma:27b` | Local, via Ollama |

Temperature and verified reasoning behaviour per model are listed in
[evaluation_protocol.md](evaluation_protocol.md) §4.

### 6.2 Structured classifiers (2)

- **`laya`** — local "System 1" engine (`laya` package, checkpoint `convaiinnovations/laya`).
- **`jev`** — hosted "System One" API (`thejevai.com`).

Both receive the same rendered case and a choice question over the same actions. Their
training data are not publicly documented, so prior exposure to VitalDB cannot be excluded
(see [limitations.md](limitations.md)).

### 6.3 Deterministic controllers (4)

`rules` (clinical thresholds), `pid` (BIS PID), `clads` (gradient with dead-zone) and `fuzzy`
(Mamdani fuzzy logic). They act on the hypnotic only and are evaluated on the hypnotic-only
subgroup. Details: [../src/determinist/README.md](../src/determinist/README.md). An MPC
controller was implemented as a functional stub and is **not** part of the reported results.

## 7. External human review

Three anesthesiologists external to the source hospital reviewed 298 windows. For each window
and each action proposed by a set of policies (including the real clinician's action), each
reviewer independently judged whether the action was **appropriate** (yes/no), blind to the
source of the action and with the same information given to the models.

This review is reported as characterisation (inter-rater agreement, appropriateness of each
reference). It was **not** used to select the consensus model. Only 13 of the 298 reviewed
windows belong to the test split, so model-level appropriateness is preliminary.
See [metrics.md](metrics.md) §8.
