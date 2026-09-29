# Analysis 3 — Sex counterfactual (results)

Design frozen in `docs/analysis3_design.md` (commit `cea58bb`).

## 1. Primary (pooled, 5 models, primary windows)

| quantity | value |
|---|---|
| primary windows (MAP < 65) | 354 |
| (window, model) pairs | 1770 |
| b (female increase_hypnotic, male not) | 25 |
| c (male increase_hypnotic, female not) | 11 |
| discordant pairs (b + c) | 36 |
| pooled paired OR (Σb/Σc) | 2.2727 |
| 95 % CI (case-clustered bootstrap, 1,000) | [1.0000, 5.8333] |
| net statistic T = b − c | 14 |
| sign permutation p (two-sided, +1, 10,000) | 0.059694 |

## 2. Per model (exact McNemar + Holm, primary windows)

| model | b | c | OR | McNemar (exact) | Holm |
|---|---|---|---|---|---|
| claude-opus-5-5 | 1 | 0 | inf | 1.000000 | 1.000000 |
| gpt-6-sol | 2 | 0 | inf | 0.500000 | 1.000000 |
| gemini-3.1-pro-preview | 7 | 3 | 2.3333 | 0.343750 | 1.000000 |
| deepseek-v4-pro | 6 | 6 | 1.0000 | 1.000000 | 1.000000 |
| deepseek-flash | 9 | 2 | 4.5000 | 0.065430 | 0.327148 |

## 3. Other secondary metrics

### 3.1 primary windows

| model | version | n | contraindicated | consensus acc |
|---|---|---|---|---|
| claude-opus-5-5 | F | 354 | 0.0819 | 0.2401 |
| claude-opus-5-5 | M | 354 | 0.0791 | 0.2203 |
| gpt-6-sol | F | 354 | 0.0819 | 0.2175 |
| gpt-6-sol | M | 354 | 0.0819 | 0.1977 |
| gemini-3.1-pro-preview | F | 354 | 0.1469 | 0.1808 |
| gemini-3.1-pro-preview | M | 354 | 0.1299 | 0.1949 |
| deepseek-v4-pro | F | 354 | 0.1186 | 0.1921 |
| deepseek-v4-pro | M | 354 | 0.1130 | 0.2147 |
| deepseek-flash | F | 354 | 0.0791 | 0.2429 |
| deepseek-flash | M | 354 | 0.0593 | 0.2542 |

Action change rate (pair, primary):

| model | n pairs | changed | change rate |
|---|---|---|---|
| claude-opus-5-5 | 354 | 27 | 0.0763 |
| gpt-6-sol | 354 | 32 | 0.0904 |
| gemini-3.1-pro-preview | 354 | 54 | 0.1525 |
| deepseek-v4-pro | 354 | 51 | 0.1441 |
| deepseek-flash | 354 | 76 | 0.2147 |

Direction matrix, pooled over models (primary; rows = female, columns = male):

| female \ male | increase_hypnotic | reduce_hypnotic | increase_opioid | reduce_opioid | no_action |
|---|---|---|---|---|---|
| increase_hypnotic | 145 | 1 | 2 | 10 | 12 |
| reduce_hypnotic | 1 | 882 | 1 | 47 | 32 |
| increase_opioid | 2 | 3 | 21 | 2 | 4 |
| reduce_opioid | 2 | 58 | 1 | 285 | 12 |
| no_action | 6 | 28 | 1 | 15 | 197 |

### 3.2 secondary windows

| model | version | n | contraindicated | consensus acc |
|---|---|---|---|---|
| claude-opus-5-5 | F | 300 | 0.0000 | 0.3333 |
| claude-opus-5-5 | M | 300 | 0.0000 | 0.3267 |
| gpt-6-sol | F | 300 | 0.0000 | 0.3000 |
| gpt-6-sol | M | 300 | 0.0033 | 0.2833 |
| gemini-3.1-pro-preview | F | 300 | 0.0133 | 0.2400 |
| gemini-3.1-pro-preview | M | 300 | 0.0200 | 0.2133 |
| deepseek-v4-pro | F | 300 | 0.0067 | 0.2267 |
| deepseek-v4-pro | M | 300 | 0.0067 | 0.2233 |
| deepseek-flash | F | 300 | 0.0100 | 0.3133 |
| deepseek-flash | M | 300 | 0.0067 | 0.2700 |

Action change rate (pair, secondary):

| model | n pairs | changed | change rate |
|---|---|---|---|
| claude-opus-5-5 | 300 | 16 | 0.0533 |
| gpt-6-sol | 300 | 27 | 0.0900 |
| gemini-3.1-pro-preview | 300 | 60 | 0.2000 |
| deepseek-v4-pro | 300 | 57 | 0.1900 |
| deepseek-flash | 300 | 78 | 0.2600 |

Direction matrix, pooled over models (secondary; rows = female, columns = male):

| female \ male | increase_hypnotic | reduce_hypnotic | increase_opioid | reduce_opioid | no_action |
|---|---|---|---|---|---|
| increase_hypnotic | 197 | 1 | 12 | 2 | 19 |
| reduce_hypnotic | 5 | 447 | 14 | 4 | 26 |
| increase_opioid | 9 | 6 | 149 | 1 | 24 |
| reduce_opioid | 2 | 12 | 1 | 49 | 6 |
| no_action | 20 | 35 | 28 | 11 | 420 |

## 4. Neutral summary

In the 354 primary windows (MAP < 65), pooling the 5 models (1770 pairs), the female version proposed increase_hypnotic while the male version did not in 25 pairs, and the opposite occurred in 11 pairs. The pooled paired odds ratio is Σb/Σc = 2.2727 (95 % CI [1.0000, 5.8333]). The per-case sign permutation test (10,000 permutations, two-sided, +1 correction) gave p = 0.059694. Per-model exact McNemar p-values and Holm-adjusted p-values are reported above; excluded pairs per model were 0.
