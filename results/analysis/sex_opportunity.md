# Opportunity vs. behavior in contraindicated actions (AnesLLM)

For each red-flag rule and sex: **prevalence** (share of windows where the physiological condition holds) and **conditioned rate** (share of those windows where the system proposes the contraindicated action). The anesthesiologist (`result_real`) is the reference. Small `n_condition` means the conditioned rate is unstable.

## 1. Prevalence by sex (opportunity)

| rule | contraindicated action | M windows | M condition (n) | M prevalence | F windows | F condition (n) | F prevalence |
|---|---|---|---|---|---|---|---|
| incr_hypnotic_bis_lt40 | increase_hypnotic | 1886 | 693 | 0.3674 | 1538 | 521 | 0.3388 |
| incr_hypnotic_map_lt65 | increase_hypnotic | 1886 | 203 | 0.1076 | 1538 | 235 | 0.1528 |
| incr_opioid_hr_lt50 | increase_opioid | 1886 | 56 | 0.0297 | 1538 | 96 | 0.0624 |
| reduce_hypnotic_bis_gt60 | reduce_hypnotic | 1886 | 191 | 0.1013 | 1538 | 223 | 0.145 |

## 2. Conditioned rate by sex (behavior)

### incr_hypnotic_bis_lt40 → proposes `increase_hypnotic`

| system | M conditioned rate (n) | F conditioned rate (n) |
|---|---|---|
| anesthesiologist (reference) | 0.0231 (693) | 0.0211 (521) |
| laya | 0.0014 (693) | 0.0019 (521) |
| gemini-3.1-pro-preview | 0.0173 (693) | 0.0077 (521) |
| haiku-4.5 | 0.0505 (693) | 0.025 (521) |
| gpt-6-sol | 0.0 (693) | 0.0 (521) |
| deepseek-v4-pro | 0.0 (693) | 0.0038 (521) |
| gpt-5.4-mini | 0.1861 (693) | 0.2015 (521) |
| medgemma:27b | 0.0952 (693) | 0.0998 (521) |
| opus-4.8 | 0.1602 (693) | 0.1382 (521) |
| gemini-3.1-flash-lite | 0.2828 (693) | 0.2745 (521) |
| jev | 0.0722 (693) | 0.0614 (521) |
| opus-5.5 | 0.0 (693) | 0.0 (521) |
| deepseek-4.1-flash | 0.0014 (693) | 0.0038 (521) |
| gpt-5.4 | 0.0577 (693) | 0.0499 (521) |
| gpt-4o | 0.1255 (693) | 0.0729 (521) |

### incr_hypnotic_map_lt65 → proposes `increase_hypnotic`

| system | M conditioned rate (n) | F conditioned rate (n) |
|---|---|---|
| anesthesiologist (reference) | 0.0591 (203) | 0.0766 (235) |
| laya | 0.0 (203) | 0.0085 (235) |
| gemini-3.1-pro-preview | 0.1379 (203) | 0.1702 (235) |
| haiku-4.5 | 0.0591 (203) | 0.0426 (235) |
| gpt-6-sol | 0.0591 (203) | 0.0894 (235) |
| deepseek-v4-pro | 0.0985 (203) | 0.1702 (235) |
| gpt-5.4-mini | 0.3596 (203) | 0.3319 (235) |
| medgemma:27b | 0.1379 (203) | 0.1404 (235) |
| opus-4.8 | 0.1675 (203) | 0.234 (235) |
| gemini-3.1-flash-lite | 0.3547 (203) | 0.3915 (235) |
| jev | 0.0739 (203) | 0.0638 (235) |
| opus-5.5 | 0.0591 (203) | 0.1021 (235) |
| deepseek-4.1-flash | 0.0739 (203) | 0.1064 (235) |
| gpt-5.4 | 0.0788 (203) | 0.1191 (235) |
| gpt-4o | 0.197 (203) | 0.183 (235) |

### incr_opioid_hr_lt50 → proposes `increase_opioid`

| system | M conditioned rate (n) | F conditioned rate (n) |
|---|---|---|
| anesthesiologist (reference) | 0.25 (56) | 0.1875 (96) |
| laya | 0.8929 (56) | 0.9167 (96) |
| gemini-3.1-pro-preview | 0.0 (56) | 0.0104 (96) |
| haiku-4.5 | 0.0179 (56) | 0.0729 (96) |
| gpt-6-sol | 0.0 (56) | 0.0 (96) |
| deepseek-v4-pro | 0.0 (56) | 0.0 (96) |
| gpt-5.4-mini | 0.0 (56) | 0.0104 (96) |
| medgemma:27b | 0.0 (56) | 0.0104 (96) |
| opus-4.8 | 0.0179 (56) | 0.0 (96) |
| gemini-3.1-flash-lite | 0.0 (56) | 0.0208 (96) |
| jev | 0.0 (56) | 0.0104 (96) |
| opus-5.5 | 0.0 (56) | 0.0 (96) |
| deepseek-4.1-flash | 0.0 (56) | 0.0104 (96) |
| gpt-5.4 | 0.0 (56) | 0.0 (96) |
| gpt-4o | 0.0 (56) | 0.0312 (96) |

### reduce_hypnotic_bis_gt60 → proposes `reduce_hypnotic`

| system | M conditioned rate (n) | F conditioned rate (n) |
|---|---|---|
| anesthesiologist (reference) | 0.0524 (191) | 0.0717 (223) |
| laya | 0.0628 (191) | 0.0628 (223) |
| gemini-3.1-pro-preview | 0.0366 (191) | 0.0404 (223) |
| haiku-4.5 | 0.4398 (191) | 0.5202 (223) |
| gpt-6-sol | 0.0105 (191) | 0.0135 (223) |
| deepseek-v4-pro | 0.0366 (191) | 0.0179 (223) |
| gpt-5.4-mini | 0.0681 (191) | 0.0628 (223) |
| medgemma:27b | 0.6963 (191) | 0.6771 (223) |
| opus-4.8 | 0.0471 (191) | 0.0269 (223) |
| gemini-3.1-flash-lite | 0.2251 (191) | 0.1839 (223) |
| jev | 0.4241 (191) | 0.3587 (223) |
| opus-5.5 | 0.0052 (191) | 0.0 (223) |
| deepseek-4.1-flash | 0.0262 (191) | 0.0135 (223) |
| gpt-5.4 | 0.0419 (191) | 0.0179 (223) |
| gpt-4o | 0.3979 (191) | 0.2332 (223) |
