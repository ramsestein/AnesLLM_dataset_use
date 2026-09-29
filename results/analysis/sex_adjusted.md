# Sex-adjusted models (GEE, case-clustered) — AnesLLM

Logistic GEE (exchangeable working correlation, robust SE), clustered by case. Sex effect is female vs male (`sex_F`). Outcome 1: any contraindicated action (red flag). Outcome 2: consensus accuracy (prediction = `result_1`). Predictors as described in `src/sex_adjusted.py`; ASA unknown imputed to 2; MAP/BIS/HR values ≤ 0 treated as missing (complete-case). Surgery categories with < 10 cases are merged into `Other/rare` to avoid separation.

Complete-case windows: 3088.

## 1. Contraindicated action: sex effect (adjusted)

| system | n | events | sex OR (F vs M) | 95 % CI | p |
|---|---|---|---|---|---|
| haiku-4.5 | 3088 | 261 | 1.231 | [0.894, 1.696] | 0.2035 |
| opus-4.8 | 3088 | 262 | 0.995 | [0.698, 1.418] | 0.9773 |
| opus-5.5 * | 3088 | 29 | 463.025 | [0.753, 284577.243] | 0.061 |
| deepseek-4.1-flash * | 3088 | 43 | 2.841 | [0.924, 8.742] | 0.0685 |
| deepseek-v4-pro | 3088 | 65 | 2.234 | [1.029, 4.85] | 0.0421 |
| gemini-3.1-flash-lite | 3088 | 526 | 1.157 | [0.845, 1.585] | 0.3638 |
| gemini-3.1-pro-preview | 3088 | 91 | 1.134 | [0.638, 2.016] | 0.6686 |
| gpt-4o | 3088 | 304 | 0.897 | [0.599, 1.344] | 0.5979 |
| gpt-5.4 | 3088 | 115 | 1.289 | [0.796, 2.088] | 0.3018 |
| gpt-5.4-mini | 3088 | 361 | 0.974 | [0.698, 1.359] | 0.8746 |
| gpt-6-sol * | 3088 | 33 | 5.3 | [1.0, 28.097] | 0.05 |
| jev | 3088 | 250 | 1.013 | [0.676, 1.518] | 0.9497 |
| laya | 3088 | 137 | 0.849 | [0.44, 1.639] | 0.6261 |
| medgemma:27b | 3088 | 424 | 1.04 | [0.723, 1.494] | 0.8337 |
| anesthesiologist | 3088 | 100 | 1.123 | [0.609, 2.07] | 0.711 |

* marked rows: few contraindicated events (< 50) or extreme coefficients — estimates are unstable; read alongside the opportunity/behavior analysis (`sex_opportunity.md`).

## 2. Contraindicated action + anthropometry: sex effect

Same as §1 plus weight and height. If the sex effect shrinks here, anthropometry is the likely channel.

| system | n | events | sex OR (F vs M) | 95 % CI | p |
|---|---|---|---|---|---|
| haiku-4.5 | 3088 | 261 | 1.488 | [0.892, 2.48] | 0.1279 |
| opus-4.8 | 3088 | 262 | 1.204 | [0.697, 2.08] | 0.5045 |
| opus-5.5 * | 3088 | 29 | 1056.643 | [11.899, 93839.392] | 0.0024 |
| deepseek-4.1-flash * | 3088 | 43 | 2.201 | [0.508, 9.531] | 0.2916 |
| deepseek-v4-pro | 3088 | 65 | 1.261 | [0.379, 4.194] | 0.7058 |
| gemini-3.1-flash-lite | 3088 | 526 | 1.174 | [0.733, 1.883] | 0.5043 |
| gemini-3.1-pro-preview | 3088 | 91 | 1.078 | [0.463, 2.51] | 0.8613 |
| gpt-4o | 3088 | 304 | 0.799 | [0.435, 1.467] | 0.4694 |
| gpt-5.4 | 3088 | 115 | 1.555 | [0.734, 3.295] | 0.249 |
| gpt-5.4-mini | 3088 | 361 | 0.916 | [0.565, 1.483] | 0.7208 |
| gpt-6-sol * | 3088 | 33 | 9.89 | [0.748, 130.689] | 0.0819 |
| jev | 3088 | 250 | 1.484 | [0.829, 2.657] | 0.1839 |
| laya | 3088 | 137 | 0.887 | [0.345, 2.279] | 0.8036 |
| medgemma:27b | 3088 | 424 | 1.061 | [0.629, 1.789] | 0.8244 |
| anesthesiologist | 3088 | 100 | 1.934 | [0.826, 4.53] | 0.1288 |

## 3. Consensus accuracy: sex effect (adjusted)

| system | n | sex OR (F vs M) | 95 % CI | p |
|---|---|---|---|---|
| haiku-4.5 | 3088 | 0.911 | [0.597, 1.392] | 0.6678 |
| opus-4.8 | 3088 | 0.915 | [0.67, 1.249] | 0.5745 |
| opus-5.5 | 3088 | 0.996 | [0.697, 1.423] | 0.9838 |
| deepseek-4.1-flash | 3088 | 1.19 | [0.861, 1.646] | 0.2924 |
| deepseek-v4-pro | 3088 | 1.233 | [0.883, 1.721] | 0.218 |
| gemini-3.1-flash-lite | 3088 | 1.304 | [0.874, 1.945] | 0.1936 |
| gemini-3.1-pro-preview | 3088 | 1.313 | [0.929, 1.856] | 0.1235 |
| gpt-4o | 3088 | 1.577 | [1.047, 2.375] | 0.0293 |
| gpt-5.4 | 3088 | 0.97 | [0.702, 1.34] | 0.8522 |
| gpt-5.4-mini | 3088 | 1.259 | [0.847, 1.871] | 0.2553 |
| gpt-6-sol | 3088 | 0.97 | [0.692, 1.362] | 0.8621 |
| jev | 3088 | 0.988 | [0.627, 1.559] | 0.9598 |
| laya | 3088 | 0.927 | [0.625, 1.376] | 0.7074 |
| medgemma:27b | 3088 | 1.336 | [0.831, 2.146] | 0.2316 |
| anesthesiologist | 3088 | 1.206 | [0.909, 1.602] | 0.1946 |

## 4. Surgery type (keyword grouping, for reference)

| surgery type | cases |
|---|---|
| Other/rare | 39 |
| Colorectal | 32 |
| Others | 23 |
| Biliary/Pancreas | 21 |
| Breast | 15 |
| Transplantation | 12 |
