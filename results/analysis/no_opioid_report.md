# AnesLLM No-opioid Subgroup Analysis (3-option prompt)

- Windows: **555**
- Human ceiling (approx general): accuracy 0.82 · safety 0.968
- Class distribution: {'reduce_hypnotic': 131, 'no_action': 357, 'increase_hypnotic': 67}

## 1. Accuracy

| model | strict | consensus | plausible | harmful rate |
|---|---|---|---|---|
| gpt-5.4 | 0.505 | 0.541 | 0.894 | 0.056 |
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
| gpt-4o | 0.276 | 0.146 | 0.762 | 0.095 |
| laya | 0.175 | 0.135 | 0.357 | 0.416 |
| *always no_action (floor)* | 0.643 | — | — | 0.000 |
| *previous action (floor)* | 0.560 | — | — | 0.000 |
| *random expected (floor)* | 0.484 | — | — | 0.000 |

## 2. Red flags (harmful action rate)

| model | harmful rate |
|---|---|
| rules | 0.000 |
| clads | 0.000 |
| fuzzy | 0.000 |
| deepseek-4.1-flash | 0.002 |
| gpt-6-sol | 0.002 |
| gemini-3.1-pro-preview | 0.007 |
| deepseek-v4-pro | 0.009 |
| pid | 0.016 |
| gpt-5.4 | 0.056 |
| haiku-4.5 | 0.077 |
| opus-4.8 | 0.090 |
| jev | 0.092 |
| gpt-4o | 0.095 |
| gpt-5.4-mini | 0.144 |
| gemini-3.1-flash-lite | 0.164 |
| medgemma:27b | 0.200 |
| laya | 0.416 |
