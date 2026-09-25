# AnesLLM Benchmark Analysis (13 models)

- Windows (test, vasopressor excluded): **3424**

## 1. Accuracy against each reference

| model | strict (result_real) | consensus (result_1) | plausible {1,aux} | weighted |
|---|--|--|--|--|
| gpt-5.4 | 0.271 | 0.327 | 0.484 | 0.225 |
| deepseek-4.1-flash | 0.287 | 0.312 | 0.541 | 0.230 |
| gpt-6-sol | 0.273 | 0.289 | 0.492 | 0.209 |
| jev | 0.246 | 0.285 | 0.437 | 0.202 |
| opus-4.8 | 0.245 | 0.284 | 0.452 | 0.202 |
| gpt-5.4-mini | 0.236 | 0.263 | 0.449 | 0.195 |
| deepseek-v4-pro | 0.263 | 0.256 | 0.476 | 0.191 |
| gemini-3.1-pro-preview | 0.248 | 0.250 | 0.439 | 0.182 |
| haiku-4.5 | 0.216 | 0.227 | 0.425 | 0.180 |
| laya | 0.232 | 0.222 | 0.518 | 0.188 |
| gpt-4o | 0.189 | 0.171 | 0.373 | 0.137 |
| gemini-3.1-flash-lite | 0.181 | 0.170 | 0.362 | 0.132 |
| medgemma:27b | 0.191 | 0.168 | 0.400 | 0.143 |

## 2. Ceiling and floors

| reference | metric | value |
|---|---|---|
| human reference zone (full information, 5 options) | consensus vs result_1 | 0.570 |
| human reference zone (full information, 5 options) | plausible {result_1, result_aux} | 0.816 |
| floor: always no_action | strict | 0.271 |
| floor: previous action | strict | 0.325 |
| floor: random expected | strict | 0.230 |

## 3. Classification quality

| model | balanced acc | macro-F1 | Cohen κ | intervention index |
|---|---|---|---|---|
| deepseek-4.1-flash | 0.311 | 0.282 | 0.106 | 1.00 |
| deepseek-v4-pro | 0.330 | 0.259 | 0.113 | 1.12 |
| gpt-6-sol | 0.316 | 0.257 | 0.104 | 0.93 |
| gpt-5.4 | 0.292 | 0.241 | 0.085 | 0.74 |
| opus-4.8 | 0.293 | 0.228 | 0.079 | 0.90 |
| gpt-5.4-mini | 0.269 | 0.227 | 0.061 | 1.03 |
| gemini-3.1-pro-preview | 0.323 | 0.226 | 0.094 | 1.00 |
| jev | 0.236 | 0.200 | 0.046 | 0.75 |
| haiku-4.5 | 0.212 | 0.185 | 0.022 | 1.03 |
| gemini-3.1-flash-lite | 0.282 | 0.162 | 0.058 | 1.28 |
| gpt-4o | 0.255 | 0.161 | 0.045 | 1.27 |
| medgemma:27b | 0.224 | 0.146 | 0.023 | 1.34 |
| laya | 0.198 | 0.100 | -0.004 | 1.36 |

## 4. Error taxonomy (proportion of windows)

| model | opposite direction | wrong drug | over-intervention | under-treatment | other |
|---|---|---|---|---|---|
| haiku-4.5 | 0.105 | 0.173 | 0.197 | 0.178 | 0.131 |
| opus-4.8 | 0.049 | 0.162 | 0.171 | 0.244 | 0.129 |
| deepseek-4.1-flash | 0.075 | 0.150 | 0.188 | 0.185 | 0.115 |
| deepseek-v4-pro | 0.055 | 0.199 | 0.210 | 0.121 | 0.152 |
| gemini-3.1-flash-lite | 0.078 | 0.250 | 0.249 | 0.044 | 0.199 |
| gemini-3.1-pro-preview | 0.039 | 0.196 | 0.190 | 0.190 | 0.137 |
| gpt-4o | 0.088 | 0.240 | 0.249 | 0.053 | 0.182 |
| gpt-5.4 | 0.042 | 0.139 | 0.133 | 0.322 | 0.093 |
| gpt-5.4-mini | 0.110 | 0.155 | 0.196 | 0.174 | 0.129 |
| gpt-6-sol | 0.043 | 0.176 | 0.171 | 0.218 | 0.120 |
| jev | 0.068 | 0.146 | 0.135 | 0.315 | 0.089 |
| laya | 0.260 | 0.093 | 0.268 | 0.006 | 0.142 |
| medgemma:27b | 0.130 | 0.221 | 0.264 | 0.014 | 0.180 |

## 5. Red flags (harmful action rate)

| model | harmful action rate |
|---|---|
| gpt-6-sol | 0.011 |
| deepseek-4.1-flash | 0.015 |
| deepseek-v4-pro | 0.021 |
| gemini-3.1-pro-preview | 0.029 |
| gpt-5.4 | 0.035 |
| laya | 0.049 |
| jev | 0.078 |
| haiku-4.5 | 0.080 |
| opus-4.8 | 0.080 |
| gpt-4o | 0.094 |
| gpt-5.4-mini | 0.112 |
| medgemma:27b | 0.130 |
| gemini-3.1-flash-lite | 0.162 |
| **human (result_real)** | 0.032 |

The clinician's own actions carry red flags at 0.032: GPT-6 Sol, DeepSeek V4.1 Flash, DeepSeek V4 Pro and Gemini 3.1 Pro generate fewer red flags than the anesthesiologist. This is expected: the clinician breaks the rules using information not present in the data, not by mistake.

## 6. Reliability (case-clustered bootstrap, 95% CI)

| model | consensus (CI) | plausible (CI) |
|---|---|---|
| gpt-5.4 | 0.327 [0.308, 0.346] | 0.484 [0.462, 0.508] |
| deepseek-4.1-flash | 0.312 [0.295, 0.331] | 0.541 [0.523, 0.563] |
| gpt-6-sol | 0.289 [0.269, 0.307] | 0.492 [0.470, 0.519] |
| jev | 0.285 [0.263, 0.308] | 0.437 [0.410, 0.463] |
| opus-4.8 | 0.284 [0.264, 0.305] | 0.452 [0.429, 0.476] |
| gpt-5.4-mini | 0.263 [0.245, 0.281] | 0.449 [0.427, 0.473] |
| deepseek-v4-pro | 0.256 [0.239, 0.275] | 0.476 [0.454, 0.501] |
| gemini-3.1-pro-preview | 0.250 [0.235, 0.268] | 0.439 [0.417, 0.466] |
| haiku-4.5 | 0.227 [0.209, 0.249] | 0.425 [0.399, 0.452] |
| laya | 0.222 [0.202, 0.242] | 0.518 [0.490, 0.548] |
| gpt-4o | 0.171 [0.154, 0.189] | 0.373 [0.347, 0.401] |
| gemini-3.1-flash-lite | 0.170 [0.154, 0.189] | 0.362 [0.337, 0.386] |
| medgemma:27b | 0.168 [0.151, 0.186] | 0.400 [0.372, 0.431] |

## 7. Consistency (3 repeats)

| model | Fleiss κ | error rate stable | error rate unstable |
|---|---|---|---|
| haiku-4.5 | 0.833 | 0.741 | 0.786 |
| opus-4.8 | 0.954 | 0.723 | 0.800 |
| deepseek-4.1-flash | 0.717 | 0.687 | 0.688 |
| deepseek-v4-pro | 0.774 | 0.770 | 0.760 |
| gemini-3.1-flash-lite | 1.000 | 0.818 | — |
| gemini-3.1-pro-preview | 0.904 | 0.775 | 0.800 |
| gpt-4o | 0.887 | 0.818 | 0.909 |
| gpt-5.4 | 0.922 | 0.692 | 0.625 |
| gpt-5.4-mini | 0.808 | 0.731 | 0.857 |
| gpt-6-sol | 0.889 | 0.713 | 0.583 |
| jev | 0.818 | 0.683 | 0.706 |
| laya | 1.000 | 0.727 | — |
| medgemma:27b | 0.977 | 0.804 | 1.000 |

## 8. Inter-model agreement

- Fleiss κ (13 models): **0.187**
- Majority-vote ensemble: **0.259**
- Windows where all models fail: **603**

## 9. No-opioid subgroup (3-option prompt)

Dedicated 3-option evaluation (see `no_opioid_report.md`).

| model | strict | consensus | plausible | harmful rate |
|---|---|---|---|---|
| gpt-5.4 | 0.504 | 0.540 | 0.894 | 0.056 |
| rules | 0.492 | 0.515 | 0.968 | 0.000 |
| deepseek-4.1-flash | 0.506 | 0.503 | 0.962 | 0.002 |
| haiku-4.5 | 0.465 | 0.499 | 0.818 | 0.077 |
| jev | 0.449 | 0.488 | 0.818 | 0.092 |
| gpt-5.4-mini | 0.431 | 0.479 | 0.760 | 0.144 |
| gpt-6-sol | 0.467 | 0.447 | 0.971 | 0.002 |
| clads | 0.449 | 0.427 | 0.957 | 0.000 |
| fuzzy | 0.436 | 0.427 | 0.962 | 0.000 |
| opus-4.8 | 0.431 | 0.416 | 0.823 | 0.090 |
| gemini-3.1-pro-preview | 0.452 | 0.411 | 0.948 | 0.007 |
| deepseek-v4-pro | 0.427 | 0.368 | 0.946 | 0.009 |
| pid | 0.371 | 0.312 | 0.906 | 0.016 |
| medgemma:27b | 0.337 | 0.290 | 0.677 | 0.200 |
| gemini-3.1-flash-lite | 0.292 | 0.195 | 0.741 | 0.164 |
| gpt-4o | 0.276 | 0.146 | 0.762 | 0.096 |
| laya | 0.175 | 0.135 | 0.357 | 0.416 |
| *always no_action (floor)* | 0.643 | — | — | 0.000 |
| *previous action (floor)* | 0.560 | — | — | — |
| *random expected (floor)* | 0.484 | — | — | — |

## 10. Human reviewers

### Inter-rater agreement

| metric | raters | value |
|---|---|---|
| percent_agreement | Carles vs Sandro | 0.764 |
| cohen_kappa | Carles vs Sandro | 0.469 |
| percent_agreement | Carles vs Yihao | 0.821 |
| cohen_kappa | Carles vs Yihao | 0.609 |
| percent_agreement | Sandro vs Yihao | 0.764 |
| cohen_kappa | Sandro vs Yihao | 0.467 |
| fleiss_kappa | all raters | 0.515 |

### Appropriateness by unit (majority approval, 298 review windows)

| unit | kind | n_windows | majority |
|---|---|---|---|
| result_real (is_gt) | reference | 298 | 0.245 |
| anesllm | policy | 298 | 0.463 |
| clads | policy | 298 | 0.664 |
| fuzzy | policy | 298 | 0.705 |
| llm_direct | policy | 298 | 0.607 |
| mpc | policy | 298 | 0.144 |
| pid | policy | 298 | 0.289 |
| rule | policy | 298 | 0.762 |
| result_1 | benchmark | 298 | 0.266 |
| result_aux | benchmark | 298 | 0.545 |

### Model-level appropriateness (preliminary, 13 review windows)

| model | n | majority |
|---|---|---|
| haiku-4.5 | 13 | 0.273 |
| opus-4.8 | 13 | 0.545 |
| deepseek-v4.1-flash | 13 | 0.625 |
| deepseek-v4-pro | 13 | 0.583 |
| gemini-3.1-flash-lite | 13 | 0.545 |
| gemini-3.1-pro-preview | 13 | 0.583 |
| gpt-4o | 13 | 0.545 |
| gpt-5.4 | 13 | 0.462 |
| gpt-5.4-mini | 13 | 0.600 |
| gpt-6-sol | 13 | 0.667 |
| jev | 13 | 0.583 |
| medgemma:27b | 13 | 0.200 |

## 11. Reasoning by model (verified with src/verify_reasoning.py)

| model | reasoning |
|---|---|
| clads | N/A (deterministic) |
| haiku-4.5 | no reasoning (thinking off) |
| opus-4.8 | no reasoning (thinking off) |
| deepseek-4.1-flash | reasoning (~467 tok) |
| deepseek-v4-pro | reasoning (~358 tok) |
| fuzzy | N/A (deterministic) |
| gemini-3.1-flash-lite | no reasoning |
| gemini-3.1-pro-preview | reasoning (~224 tok) |
| gpt-4o | no reasoning |
| gpt-5.4 | no reasoning |
| gpt-5.4-mini | no reasoning |
| gpt-6-sol | reasoning (~34 tok) |
| jev | N/A (classifier) |
| laya | N/A (classifier) |
| medgemma:27b | no reasoning |
| pid | N/A (deterministic) |
| rules | N/A (deterministic) |
