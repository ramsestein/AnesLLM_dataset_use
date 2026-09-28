# Cohort characteristics by partition (Table 1)

Case-level characteristics (age, sex, ASA, surgery type, anesthesia duration, windows per case) and window-level characteristics (monitoring, real action), per split.

| Characteristic | train (n=2,994 cases) | dev (n=25 cases) | test (n=149 cases) |
|---|---|---|---|
| Windows, n | 80,933 | 423 | 3,457 |
| Age, years, mean ± SD | 57.8 ± 14.4 | 56.1 ± 11.2 | 57.4 ± 14.4 |
| Sex, F, n (%) | 1,484 (49.6%) | 15 (60.0%) | 74 (49.7%) |
| Sex, M, n (%) | 1,510 (50.4%) | 10 (40.0%) | 75 (50.3%) |
| ASA 1, n (%) | 712 (23.8%) | 12 (48.0%) | 42 (28.2%) |
| ASA 2, n (%) | 1,824 (60.9%) | 12 (48.0%) | 77 (51.7%) |
| ASA 3, n (%) | 381 (12.7%) | 0 (0.0%) | 22 (14.8%) |
| ASA 4, n (%) | 12 (0.4%) | 0 (0.0%) | 1 (0.7%) |
| ASA 6, n (%) | 8 (0.3%) | 0 (0.0%) | 1 (0.7%) |
| unknown, n (%) | 57 (1.9%) | 1 (4.0%) | 6 (4.0%) |
| Surgery type, Colorectal, n (%) | 463 (15.5%) | 2 (8.0%) | 36 (24.2%) |
| Surgery type, Others, n (%) | 414 (13.8%) | 3 (12.0%) | 18 (12.1%) |
| Surgery type, Minor resection, n (%) | 413 (13.8%) | 0 (0.0%) | 11 (7.4%) |
| Surgery type, Biliary/Pancreas, n (%) | 351 (11.7%) | 5 (20.0%) | 21 (14.1%) |
| Surgery type, Major resection, n (%) | 330 (11.0%) | 0 (0.0%) | 8 (5.4%) |
| Surgery type, Breast, n (%) | 268 (9.0%) | 2 (8.0%) | 16 (10.7%) |
| Surgery type, Transplantation, n (%) | 199 (6.6%) | 0 (0.0%) | 12 (8.1%) |
| Surgery type, Thyroid, n (%) | 194 (6.5%) | 9 (36.0%) | 9 (6.0%) |
| Surgery type, Hepatic, n (%) | 170 (5.7%) | 0 (0.0%) | 7 (4.7%) |
| Surgery type, Vascular, n (%) | 130 (4.3%) | 4 (16.0%) | 8 (5.4%) |
| Surgery type, Stomach, n (%) | 62 (2.1%) | 0 (0.0%) | 3 (2.0%) |
| Anesthesia duration, h, mean ± SD | 3.40 ± 1.91 | 2.06 ± 0.70 | 2.95 ± 1.90 |
| Windows per case, mean ± SD | 27.0 ± 16.1 | 16.9 ± 8.2 | 23.2 ± 15.0 |
| Monitoring, ART, n (%) | 59,668 (73.7%) | 46 (10.9%) | 1,882 (54.4%) |
| Monitoring, NIBP, n (%) | 21,255 (26.3%) | 377 (89.1%) | 1,575 (45.6%) |
| Monitoring, NONE, n (%) | 10 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| result_real, increase_hypnotic, n (%) | 6,452 (8.0%) | 39 (9.2%) | 291 (8.4%) |
| result_real, reduce_hypnotic, n (%) | 9,710 (12.0%) | 62 (14.7%) | 459 (13.3%) |
| result_real, increase_opioid, n (%) | 19,691 (24.3%) | 115 (27.2%) | 824 (23.8%) |
| result_real, reduce_opioid, n (%) | 22,470 (27.8%) | 122 (28.8%) | 940 (27.2%) |
| result_real, no_action, n (%) | 22,610 (27.9%) | 85 (20.1%) | 943 (27.3%) |

*Note: anesthesia duration = pt_aneend − pt_anestart, clipped to [0, 24] h to exclude 81 windows with out-of-range timestamps. ASA VI (n small) = organ donors. `monitoring_type` and `result_real` are window-level; the rest are case-level.*
