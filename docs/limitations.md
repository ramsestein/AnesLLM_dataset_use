# Limitations and design decisions

## Reference answers

- **No single correct action.** Several actions are often clinically acceptable. The benchmark
  therefore reports strict, consensus and plausible accuracy; none of them is an absolute
  measure of clinical correctness.
- **The real clinician had more information.** `result_real` was decided with the patient in
  front of the anesthesiologist. Part of the gap between models and the human reference zone
  may be due to information that is not in the data.
- **The consensus is a model.** `result_1` and `result_aux` come from a supervised LightGBM
  model (case-grouped out-of-fold). It was selected for its agreement with the real action, not
  for agreement with external reviewers.
- **Single-center source.** All cases come from one hospital (Seoul National University
  Hospital, via VitalDB); practice patterns may differ elsewhere.

## Evaluation setup

- **Reasoning was not controlled.** Each model ran with its API's default behaviour; reasoning
  was verified afterwards (4 of 11 LLMs reasoned). Differences associated with reasoning are
  confounded with model recency.
- **Temperature** was 0 except for GPT-6 Sol and Claude Opus 4.8, whose APIs do not accept it.
- **Single run** of the full benchmark per model; run-to-run variability is estimated only on
  the 100-window consistency sample.
- **API models change.** Results correspond to the model versions available at evaluation
  time.
- **Text-only input.** Waveforms and time series are summarised as current values and trends.

## Subgroup and baselines

- The hypnotic-only subgroup is **selected using the reference labels**. It is a fair
  comparison device, not a deployment scenario.
- The deterministic controllers act only on the hypnotic and are evaluated only on that
  subgroup. The MPC controller was a functional stub and is excluded.
- **`jev` and `laya`**: third-party classifiers whose training data are not documented; prior
  exposure to VitalDB cannot be ruled out.

## Safety analysis

- Red flags are four physiology-based rules on the current values. They capture clearly
  contraindicated actions only, not the full range of unsafe decisions.

## External review

- The review covers 298 windows, only 13 of them in the test split; model-level
  appropriateness is preliminary.
- Reviewers judged the actions proposed by a fixed set of policies; a model action outside that
  set cannot be scored.
- [RENDER_VERSION_NOTE: state which case rendering the reviewers saw.]

## Data

- VitalDB is de-identified at source, but concrete vital signs make most windows unique
  (k = 1 at window level). Direct identifiers (`pt_caseid`, `pt_subjectid`) are removed in the
  released dataset.
