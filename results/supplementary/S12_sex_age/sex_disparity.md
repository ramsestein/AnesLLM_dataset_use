# Sex-disaggregated analysis (AnesLLM)

Test partition after vasopressor exclusion: 3424 windows, 149 cases — 1886 windows from male cases, 1538 from female cases.

Metrics per system and per sex: strict / consensus / plausible accuracy and the rate of contraindicated actions (red flags). The clinician row (`anesthesiologist`) uses `result_real`; its *strict* value is trivially 1.0 (it matches itself).

## 1. Real action by sex

| sex | action | n | % within sex |
|---|---|---|---|
| M | increase_hypnotic | 166 | 8.8 |
| M | reduce_hypnotic | 243 | 12.88 |
| M | increase_opioid | 419 | 22.22 |
| M | reduce_opioid | 514 | 27.25 |
| M | no_action | 544 | 28.84 |
| F | increase_hypnotic | 122 | 7.93 |
| F | reduce_hypnotic | 208 | 13.52 |
| F | increase_opioid | 403 | 26.2 |
| F | reduce_opioid | 420 | 27.31 |
| F | no_action | 385 | 25.03 |

Chi-square test of independence (2 × 5, case-level permutation, 10,000 permutations): χ² = 11.1696, df = 4, p = 0.2325. The anesthesiologist did not act differently by sex.

## 2. Performance by system × sex

| system | sex | n | strict | consensus | plausible | harmful |
|---|---|---|---|---|---|---|
| haiku-4.5 | M | 1886 | 0.2285 | 0.2397 | 0.4396 | 0.0689 |
| haiku-4.5 | F | 1538 | 0.1996 | 0.212 | 0.4064 | 0.0943 |
| opus-4.8 | M | 1886 | 0.2444 | 0.2752 | 0.4539 | 0.0795 |
| opus-4.8 | F | 1538 | 0.2458 | 0.2945 | 0.4499 | 0.0813 |
| opus-5.5 | M | 1886 | 0.3171 | 0.3542 | 0.5435 | 0.0069 |
| opus-5.5 | F | 1538 | 0.3017 | 0.3394 | 0.5208 | 0.0156 |
| deepseek-4.1-flash | M | 1886 | 0.29 | 0.3001 | 0.5361 | 0.0111 |
| deepseek-4.1-flash | F | 1538 | 0.2828 | 0.3264 | 0.5481 | 0.0195 |
| deepseek-v4-pro | M | 1886 | 0.2694 | 0.237 | 0.4613 | 0.0143 |
| deepseek-v4-pro | F | 1538 | 0.2562 | 0.2789 | 0.4941 | 0.0299 |
| gemini-3.1-flash-lite | M | 1886 | 0.185 | 0.1538 | 0.3499 | 0.1569 |
| gemini-3.1-flash-lite | F | 1538 | 0.1756 | 0.1905 | 0.3771 | 0.1678 |
| gemini-3.1-pro-preview | M | 1886 | 0.263 | 0.2375 | 0.4295 | 0.0249 |
| gemini-3.1-pro-preview | F | 1538 | 0.2302 | 0.2646 | 0.4506 | 0.0351 |
| gpt-4o | M | 1886 | 0.1856 | 0.1575 | 0.3674 | 0.105 |
| gpt-4o | F | 1538 | 0.1938 | 0.1873 | 0.3791 | 0.0813 |
| gpt-5.4 | M | 1886 | 0.2768 | 0.3266 | 0.4973 | 0.0334 |
| gpt-5.4 | F | 1538 | 0.2633 | 0.327 | 0.4681 | 0.0371 |
| gpt-5.4-mini | M | 1886 | 0.2397 | 0.2534 | 0.456 | 0.105 |
| gpt-5.4-mini | F | 1538 | 0.2321 | 0.2737 | 0.4408 | 0.1196 |
| gpt-6-sol | M | 1886 | 0.28 | 0.2858 | 0.492 | 0.0074 |
| gpt-6-sol | F | 1538 | 0.2646 | 0.2919 | 0.4922 | 0.0156 |
| jev | M | 1886 | 0.2349 | 0.2789 | 0.4401 | 0.0764 |
| jev | F | 1538 | 0.2607 | 0.2926 | 0.4324 | 0.0793 |
| laya | M | 1886 | 0.2121 | 0.2222 | 0.5228 | 0.0334 |
| laya | F | 1538 | 0.2562 | 0.2211 | 0.5117 | 0.0683 |
| medgemma:27b | M | 1886 | 0.1967 | 0.1585 | 0.4099 | 0.1166 |
| medgemma:27b | F | 1538 | 0.1834 | 0.1788 | 0.3882 | 0.1469 |
| anesthesiologist | M | 1886 | 1.0 | 0.571 | 0.8097 | 0.0265 |
| anesthesiologist | F | 1538 | 1.0 | 0.5683 | 0.8244 | 0.0397 |

## 3. Male − female difference (95 % CI, case-clustered bootstrap)

CIs not crossing 0 are marked with *.

| system | metric | M−F | 95 % CI |
|---|---|---|---|
| haiku-4.5 | strict | 0.0289 | [-0.0053, 0.0641] |
| haiku-4.5 | consensus | 0.0277 | [-0.0163, 0.0676] |
| haiku-4.5 | plausible | 0.0332 | [-0.0246, 0.089] |
| haiku-4.5 | harmful | -0.0253 | [-0.0558, 0.0004] |
| opus-4.8 | strict | -0.0013 | [-0.0403, 0.0375] |
| opus-4.8 | consensus | -0.0194 | [-0.0589, 0.022] |
| opus-4.8 | plausible | 0.0039 | [-0.0447, 0.0526] |
| opus-4.8 | harmful | -0.0017 | [-0.0321, 0.0293] |
| opus-5.5 | strict | 0.0154 | [-0.0237, 0.0562] |
| opus-5.5 | consensus | 0.0148 | [-0.0293, 0.0582] |
| opus-5.5 | plausible | 0.0227 | [-0.0246, 0.0702] |
| opus-5.5 | harmful | -0.0087 | [-0.018, -0.0009] * |
| deepseek-4.1-flash | strict | 0.0072 | [-0.0239, 0.0384] |
| deepseek-4.1-flash | consensus | -0.0263 | [-0.059, 0.0089] |
| deepseek-4.1-flash | plausible | -0.0121 | [-0.0533, 0.0303] |
| deepseek-4.1-flash | harmful | -0.0084 | [-0.0186, 0.0012] |
| deepseek-v4-pro | strict | 0.0132 | [-0.0151, 0.0419] |
| deepseek-v4-pro | consensus | -0.0419 | [-0.0745, -0.0098] * |
| deepseek-v4-pro | plausible | -0.0329 | [-0.0779, 0.0151] |
| deepseek-v4-pro | harmful | -0.0156 | [-0.0316, -0.0024] * |
| gemini-3.1-flash-lite | strict | 0.0095 | [-0.0202, 0.0384] |
| gemini-3.1-flash-lite | consensus | -0.0367 | [-0.0711, -0.004] * |
| gemini-3.1-flash-lite | plausible | -0.0272 | [-0.0709, 0.0237] |
| gemini-3.1-flash-lite | harmful | -0.0108 | [-0.0531, 0.0303] |
| gemini-3.1-pro-preview | strict | 0.0328 | [0.0011, 0.0648] * |
| gemini-3.1-pro-preview | consensus | -0.0271 | [-0.0582, 0.005] |
| gemini-3.1-pro-preview | plausible | -0.0211 | [-0.067, 0.0293] |
| gemini-3.1-pro-preview | harmful | -0.0102 | [-0.0268, 0.0031] |
| gpt-4o | strict | -0.0082 | [-0.0402, 0.0251] |
| gpt-4o | consensus | -0.0298 | [-0.0606, 0.0066] |
| gpt-4o | plausible | -0.0116 | [-0.0617, 0.0405] |
| gpt-4o | harmful | 0.0237 | [-0.0087, 0.0621] |
| gpt-5.4 | strict | 0.0134 | [-0.023, 0.0543] |
| gpt-5.4 | consensus | -0.0004 | [-0.0364, 0.0366] |
| gpt-5.4 | plausible | 0.0292 | [-0.0188, 0.0771] |
| gpt-5.4 | harmful | -0.0037 | [-0.0191, 0.0124] |
| gpt-5.4-mini | strict | 0.0075 | [-0.0268, 0.0391] |
| gpt-5.4-mini | consensus | -0.0203 | [-0.0569, 0.018] |
| gpt-5.4-mini | plausible | 0.0152 | [-0.034, 0.0619] |
| gpt-5.4-mini | harmful | -0.0147 | [-0.047, 0.0145] |
| gpt-6-sol | strict | 0.0153 | [-0.0164, 0.0484] |
| gpt-6-sol | consensus | -0.0061 | [-0.0429, 0.0323] |
| gpt-6-sol | plausible | -0.0002 | [-0.0495, 0.051] |
| gpt-6-sol | harmful | -0.0082 | [-0.0177, -0.0005] * |
| jev | strict | -0.0258 | [-0.0646, 0.014] |
| jev | consensus | -0.0137 | [-0.0609, 0.0333] |
| jev | plausible | 0.0077 | [-0.0417, 0.0609] |
| jev | harmful | -0.003 | [-0.0355, 0.0278] |
| laya | strict | -0.0441 | [-0.0791, -0.0078] * |
| laya | consensus | 0.0011 | [-0.041, 0.042] |
| laya | plausible | 0.0111 | [-0.0467, 0.0683] |
| laya | harmful | -0.0349 | [-0.0701, 0.0008] |
| medgemma:27b | strict | 0.0134 | [-0.0166, 0.0415] |
| medgemma:27b | consensus | -0.0203 | [-0.0568, 0.0134] |
| medgemma:27b | plausible | 0.0217 | [-0.0378, 0.0815] |
| medgemma:27b | harmful | -0.0303 | [-0.0762, 0.0172] |
| anesthesiologist | strict | 0.0 | [0.0, 0.0] |
| anesthesiologist | consensus | 0.0028 | [-0.0408, 0.0465] |
| anesthesiologist | plausible | -0.0148 | [-0.049, 0.0188] |
| anesthesiologist | harmful | -0.0132 | [-0.0316, 0.0041] |

## 4. Age by partition (STROBE)

| split | cases | min | median | max | <18 |
|---|---|---|---|---|---|
| train | 2994 | 6.0 | 59.0 | 92.0 | 10 |
| dev | 25 | 39.0 | 58.0 | 75.0 | 0 |
| test | 149 | 23.0 | 58.0 | 88.0 | 0 |
