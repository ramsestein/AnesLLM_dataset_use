# AnesLLM Benchmark Analysis (13 models)

- Windows (test, vasopressor excluded): **3424**
- **Human ceiling** (consensus vs result_1): 0.570 · (plausible {result_1, result_aux}): 0.816
- Floors: always no_action 0.271 · previous action 0.325 · random 0.230

## 1. Accuracy against each reference

| model | strict (result_real) | consensus (result_1) | plausible {1,aux} | weighted |
|---|--|--|--|--|
| gpt-5.4 | 0.271 | 0.327 | 0.484 | 0.225 |
| deepseek-flash | 0.287 | 0.312 | 0.541 | 0.230 |
| gpt-6-sol | 0.273 | 0.289 | 0.492 | 0.209 |
| jev | 0.246 | 0.285 | 0.437 | 0.202 |
| claude-opus-4-8 | 0.245 | 0.284 | 0.452 | 0.202 |
| gpt-5.4-mini | 0.236 | 0.263 | 0.449 | 0.195 |
| deepseek-v4-pro | 0.263 | 0.256 | 0.476 | 0.191 |
| gemini-3.1-pro-preview | 0.248 | 0.250 | 0.439 | 0.182 |
| claude-haiku-4-5-20251001 | 0.216 | 0.227 | 0.425 | 0.180 |
| laya | 0.232 | 0.222 | 0.518 | 0.188 |
| gpt-4o | 0.189 | 0.171 | 0.373 | 0.137 |
| gemini-3.1-flash-lite | 0.181 | 0.170 | 0.362 | 0.132 |
| medgemma:27b | 0.191 | 0.168 | 0.400 | 0.143 |

## 3. Classification quality

| model | balanced acc | macro-F1 | Cohen κ | intervention index |
|---|---|---|---|---|
| deepseek-flash | 0.311 | 0.282 | 0.106 | 1.00 |
| deepseek-v4-pro | 0.330 | 0.259 | 0.113 | 1.12 |
| gpt-6-sol | 0.316 | 0.257 | 0.104 | 0.93 |
| gpt-5.4 | 0.292 | 0.241 | 0.085 | 0.74 |
| claude-opus-4-8 | 0.293 | 0.228 | 0.079 | 0.90 |
| gpt-5.4-mini | 0.269 | 0.227 | 0.061 | 1.03 |
| gemini-3.1-pro-preview | 0.323 | 0.226 | 0.094 | 1.00 |
| jev | 0.236 | 0.200 | 0.046 | 0.75 |
| claude-haiku-4-5-20251001 | 0.212 | 0.185 | 0.022 | 1.03 |
| gemini-3.1-flash-lite | 0.282 | 0.162 | 0.058 | 1.28 |
| gpt-4o | 0.255 | 0.161 | 0.045 | 1.27 |
| medgemma:27b | 0.224 | 0.146 | 0.023 | 1.34 |
| laya | 0.198 | 0.100 | -0.004 | 1.36 |

## 4. Error taxonomy (proportion of windows)

| model | opposite direction | wrong drug | over-intervention | under-treatment | other |
|---|---|---|---|---|---|
| claude-haiku-4-5-20251001 | 0.105 | 0.173 | 0.197 | 0.178 | 0.131 |
| claude-opus-4-8 | 0.049 | 0.162 | 0.171 | 0.244 | 0.129 |
| deepseek-flash | 0.075 | 0.150 | 0.188 | 0.185 | 0.115 |
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

## 5. Reliability (case-clustered bootstrap, 95% CI)

| model | consensus (CI) | plausible (CI) |
|---|---|---|
| gpt-5.4 | 0.327 [0.308, 0.346] | 0.484 [0.462, 0.508] |
| deepseek-flash | 0.312 [0.295, 0.331] | 0.541 [0.523, 0.563] |
| gpt-6-sol | 0.289 [0.269, 0.307] | 0.492 [0.470, 0.519] |
| jev | 0.285 [0.263, 0.308] | 0.437 [0.410, 0.463] |
| claude-opus-4-8 | 0.284 [0.264, 0.305] | 0.452 [0.429, 0.476] |
| gpt-5.4-mini | 0.263 [0.245, 0.281] | 0.449 [0.427, 0.473] |
| deepseek-v4-pro | 0.256 [0.239, 0.275] | 0.476 [0.454, 0.501] |
| gemini-3.1-pro-preview | 0.250 [0.235, 0.268] | 0.439 [0.417, 0.466] |
| claude-haiku-4-5-20251001 | 0.227 [0.209, 0.249] | 0.425 [0.399, 0.452] |
| laya | 0.222 [0.202, 0.242] | 0.518 [0.490, 0.548] |
| gpt-4o | 0.171 [0.154, 0.189] | 0.373 [0.347, 0.401] |
| gemini-3.1-flash-lite | 0.170 [0.154, 0.189] | 0.362 [0.337, 0.386] |
| medgemma:27b | 0.168 [0.151, 0.186] | 0.400 [0.372, 0.431] |

## 6. Consistency (3 repeats)

| model | Fleiss κ | error rate stable | error rate unstable |
|---|---|---|---|
| claude-haiku-4-5-20251001 | 0.833 | 0.741 | 0.786 |
| claude-opus-4-8 | 0.954 | 0.723 | 0.800 |
| deepseek-flash | 0.717 | 0.687 | 0.688 |
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

## 7. Inter-model agreement

- Fleiss κ (13 models): **0.187**
- Majority-vote ensemble: **0.259**
- Windows where all models fail: **603**

## 8. No-opioid subgroup (no opioid/vasopressor in any reference)

- Windows: **555** · human consensus 0.679 · plausible 0.942
- Class distribution: {'reduce_hypnotic': 131, 'no_action': 357, 'increase_hypnotic': 67}

| model | strict | consensus | plausible |
|---|---|---|---|
| rules | 0.492 | 0.515 | 0.968 |
| jev | 0.443 | 0.510 | 0.777 |
| gpt-5.4 | 0.465 | 0.485 | 0.822 |
| clads | 0.449 | 0.427 | 0.957 |
| fuzzy | 0.436 | 0.427 | 0.962 |
| gpt-6-sol | 0.413 | 0.389 | 0.885 |
| claude-opus-4-8 | 0.371 | 0.353 | 0.762 |
| gpt-5.4-mini | 0.319 | 0.350 | 0.629 |
| deepseek-flash | 0.366 | 0.348 | 0.757 |
| gemini-3.1-pro-preview | 0.404 | 0.330 | 0.872 |
| pid | 0.371 | 0.312 | 0.906 |
| deepseek-v4-pro | 0.391 | 0.297 | 0.838 |
| claude-haiku-4-5-20251001 | 0.323 | 0.288 | 0.640 |
| gemini-3.1-flash-lite | 0.270 | 0.189 | 0.730 |
| gpt-4o | 0.277 | 0.162 | 0.732 |
| medgemma:27b | 0.182 | 0.077 | 0.501 |
| laya | 0.020 | 0.018 | 0.041 |
