# AnesLLM Benchmark Analysis (18 models)

- Windows (test, vasopressor excluded): **3424**
- **Human ceiling** (consensus vs result_1): 0.570 · (plausible {result_1, result_aux}): 0.816
- Floors: always no_action 0.271 · previous action 0.325 · random 0.230

## 1. Accuracy against each reference

| model | strict (result_real) | consensus (result_1) | plausible {1,aux} | weighted |
|---|--|--|--|--|
| deepseek-flash | 0.299 | 0.322 | 0.543 | 0.234 |
| gpt-5.4 | 0.269 | 0.318 | 0.489 | 0.221 |
| gpt-6-sol | 0.284 | 0.296 | 0.498 | 0.214 |
| rules | 0.250 | 0.287 | 0.436 | 0.200 |
| claude-opus-4-8 | 0.252 | 0.286 | 0.454 | 0.203 |
| jev | 0.240 | 0.275 | 0.430 | 0.196 |
| gpt-5.4-mini | 0.253 | 0.271 | 0.474 | 0.203 |
| deepseek-v4-pro | 0.261 | 0.263 | 0.485 | 0.196 |
| gemini-3.1-pro-preview | 0.259 | 0.259 | 0.452 | 0.187 |
| fuzzy | 0.228 | 0.246 | 0.409 | 0.176 |
| clads | 0.224 | 0.240 | 0.398 | 0.171 |
| claude-haiku-4-5-20251001 | 0.220 | 0.234 | 0.416 | 0.177 |
| mpc | 0.201 | 0.225 | 0.362 | 0.154 |
| laya | 0.235 | 0.221 | 0.520 | 0.190 |
| gemini-3.1-flash-lite | 0.189 | 0.177 | 0.364 | 0.134 |
| gpt-4o | 0.189 | 0.169 | 0.367 | 0.133 |
| medgemma:27b | 0.178 | 0.161 | 0.386 | 0.137 |
| pid | 0.157 | 0.136 | 0.290 | 0.102 |

## 3. Classification quality

| model | balanced acc | macro-F1 | Cohen κ | intervention index |
|---|---|---|---|---|
| deepseek-flash | 0.325 | 0.292 | 0.123 | 1.01 |
| gpt-6-sol | 0.329 | 0.270 | 0.121 | 0.95 |
| deepseek-v4-pro | 0.324 | 0.257 | 0.107 | 1.14 |
| gpt-5.4-mini | 0.290 | 0.249 | 0.085 | 1.10 |
| gpt-5.4 | 0.302 | 0.245 | 0.097 | 0.86 |
| gemini-3.1-pro-preview | 0.330 | 0.239 | 0.108 | 1.03 |
| claude-opus-4-8 | 0.298 | 0.232 | 0.086 | 0.89 |
| jev | 0.236 | 0.197 | 0.048 | 0.80 |
| claude-haiku-4-5-20251001 | 0.228 | 0.194 | 0.034 | 1.04 |
| rules | 0.271 | 0.191 | 0.052 | 0.59 |
| fuzzy | 0.277 | 0.185 | 0.048 | 0.77 |
| clads | 0.274 | 0.184 | 0.045 | 0.78 |
| gemini-3.1-flash-lite | 0.289 | 0.173 | 0.066 | 1.27 |
| gpt-4o | 0.269 | 0.165 | 0.052 | 1.27 |
| mpc | 0.245 | 0.159 | 0.023 | 0.76 |
| medgemma:27b | 0.221 | 0.141 | 0.016 | 1.35 |
| pid | 0.222 | 0.133 | -0.007 | 1.00 |
| laya | 0.200 | 0.105 | -0.001 | 1.36 |

## 4. Error taxonomy (proportion of windows)

| model | opposite direction | wrong drug | over-intervention | under-treatment | other |
|---|---|---|---|---|---|
| clads | 0.024 | 0.148 | 0.157 | 0.318 | 0.130 |
| claude-haiku-4-5-20251001 | 0.091 | 0.180 | 0.197 | 0.171 | 0.141 |
| claude-opus-4-8 | 0.052 | 0.157 | 0.165 | 0.244 | 0.130 |
| deepseek-flash | 0.076 | 0.154 | 0.183 | 0.176 | 0.112 |
| deepseek-v4-pro | 0.066 | 0.196 | 0.212 | 0.113 | 0.152 |
| fuzzy | 0.020 | 0.152 | 0.153 | 0.324 | 0.124 |
| gemini-3.1-flash-lite | 0.074 | 0.250 | 0.245 | 0.046 | 0.196 |
| gemini-3.1-pro-preview | 0.043 | 0.201 | 0.188 | 0.166 | 0.143 |
| gpt-4o | 0.080 | 0.240 | 0.253 | 0.053 | 0.185 |
| gpt-5.4 | 0.051 | 0.163 | 0.148 | 0.253 | 0.116 |
| gpt-5.4-mini | 0.126 | 0.161 | 0.199 | 0.127 | 0.133 |
| gpt-6-sol | 0.043 | 0.171 | 0.171 | 0.206 | 0.124 |
| jev | 0.069 | 0.157 | 0.140 | 0.287 | 0.107 |
| laya | 0.262 | 0.091 | 0.268 | 0.005 | 0.140 |
| medgemma:27b | 0.133 | 0.232 | 0.265 | 0.010 | 0.182 |
| mpc | 0.039 | 0.138 | 0.158 | 0.333 | 0.131 |
| pid | 0.054 | 0.184 | 0.218 | 0.220 | 0.167 |
| rules | 0.015 | 0.116 | 0.114 | 0.412 | 0.093 |

## 5. Reliability (case-clustered bootstrap, 95% CI)

| model | consensus (CI) | plausible (CI) |
|---|---|---|
| deepseek-flash | 0.322 [0.302, 0.340] | 0.543 [0.522, 0.563] |
| gpt-5.4 | 0.318 [0.300, 0.337] | 0.489 [0.468, 0.513] |
| gpt-6-sol | 0.296 [0.277, 0.315] | 0.498 [0.474, 0.522] |
| rules | 0.287 [0.262, 0.314] | 0.436 [0.408, 0.467] |
| claude-opus-4-8 | 0.286 [0.267, 0.306] | 0.454 [0.432, 0.477] |
| jev | 0.275 [0.255, 0.296] | 0.430 [0.405, 0.453] |
| gpt-5.4-mini | 0.271 [0.253, 0.289] | 0.474 [0.452, 0.497] |
| deepseek-v4-pro | 0.263 [0.245, 0.281] | 0.485 [0.466, 0.508] |
| gemini-3.1-pro-preview | 0.259 [0.238, 0.279] | 0.452 [0.429, 0.474] |
| fuzzy | 0.246 [0.222, 0.271] | 0.409 [0.382, 0.441] |
| clads | 0.240 [0.221, 0.261] | 0.398 [0.372, 0.428] |
| claude-haiku-4-5-20251001 | 0.234 [0.214, 0.255] | 0.416 [0.390, 0.442] |
| mpc | 0.225 [0.202, 0.249] | 0.362 [0.335, 0.388] |
| laya | 0.221 [0.202, 0.242] | 0.520 [0.491, 0.547] |
| gemini-3.1-flash-lite | 0.177 [0.160, 0.195] | 0.364 [0.341, 0.390] |
| gpt-4o | 0.169 [0.150, 0.188] | 0.367 [0.343, 0.393] |
| medgemma:27b | 0.161 [0.142, 0.179] | 0.386 [0.355, 0.419] |
| pid | 0.136 [0.116, 0.157] | 0.290 [0.266, 0.318] |

## 6. Consistency (3 repeats)

| model | Fleiss κ | error rate stable | error rate unstable |
|---|---|---|---|
| clads | 1.000 | 0.737 | — |
| claude-haiku-4-5-20251001 | 0.821 | 0.735 | 0.562 |
| claude-opus-4-8 | 0.926 | 0.659 | 0.750 |
| deepseek-flash | 0.765 | 0.644 | 0.769 |
| deepseek-v4-pro | 0.788 | 0.662 | 0.727 |
| fuzzy | 1.000 | 0.727 | — |
| gemini-3.1-flash-lite | 1.000 | 0.788 | — |
| gemini-3.1-pro-preview | 0.962 | 0.695 | 0.750 |
| gpt-4o | 0.909 | 0.867 | 0.778 |
| gpt-5.4 | 0.923 | 0.692 | 0.875 |
| gpt-5.4-mini | 0.782 | 0.707 | 0.792 |
| gpt-6-sol | 0.923 | 0.637 | 0.875 |
| jev | 0.830 | 0.699 | 0.875 |
| laya | 1.000 | 0.717 | — |
| medgemma:27b | 0.978 | 0.856 | 1.000 |
| mpc | 1.000 | 0.798 | — |
| pid | 1.000 | 0.818 | — |
| rules | 1.000 | 0.727 | — |

## 7. Inter-model agreement

- Fleiss κ (18 models): **0.180**
- Majority-vote ensemble: **0.258**
- Windows where all models fail: **533**

## 8. No-opioid subgroup (no opioid/vasopressor in any reference)

- Windows: **555** · human consensus 0.679 · plausible 0.942
- Class distribution: {'reduce_hypnotic': 131, 'no_action': 357, 'increase_hypnotic': 67}

| model | strict | consensus | plausible |
|---|---|---|---|
| rules | 0.477 | 0.499 | 0.946 |
| jev | 0.441 | 0.486 | 0.782 |
| gpt-5.4 | 0.434 | 0.431 | 0.813 |
| clads | 0.445 | 0.429 | 0.935 |
| mpc | 0.414 | 0.425 | 0.852 |
| fuzzy | 0.431 | 0.420 | 0.941 |
| claude-opus-4-8 | 0.404 | 0.393 | 0.775 |
| gpt-6-sol | 0.427 | 0.382 | 0.897 |
| deepseek-flash | 0.400 | 0.366 | 0.787 |
| gpt-5.4-mini | 0.315 | 0.330 | 0.618 |
| gemini-3.1-pro-preview | 0.409 | 0.323 | 0.868 |
| deepseek-v4-pro | 0.368 | 0.285 | 0.813 |
| claude-haiku-4-5-20251001 | 0.303 | 0.283 | 0.640 |
| pid | 0.305 | 0.249 | 0.789 |
| gemini-3.1-flash-lite | 0.268 | 0.187 | 0.710 |
| gpt-4o | 0.267 | 0.180 | 0.732 |
| medgemma:27b | 0.182 | 0.079 | 0.497 |
| laya | 0.020 | 0.014 | 0.041 |
