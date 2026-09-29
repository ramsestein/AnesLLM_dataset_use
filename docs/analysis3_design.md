# Analysis 3 — Sex counterfactual (design fixed before execution)

> Design document fixed **before** running the experiment. Any change of method must be
> reflected here and in its own commit.

## 1. Objective

Isolate the effect of the sex **word** in the prompt ("male" vs "female"), keeping the rest of
the case identical. If changing the sex changes the model's decision, the effect is
attributable to mentioning the sex, not to real differences in the patient.

## 2. Windows

- **Primary**: the 438 test windows with `MAP < 65` in the post-vasopressor-exclusion test set
  (3,424 windows), where the signal from the previous analysis is.
- **Secondary**: 300 random windows (seed to be fixed), drawn from the **non-excluded** cases
  and **disjoint** from the primary windows, for the general change rate and consensus accuracy.

## 3. Exclusions

Exclude cases whose procedure (`pt_opname`) or diagnosis (`pt_dx`) is sex-specific (breast,
gynecology, prostate, testicle…), because there the swap produces an incoherent case ("male
with hysterectomy").

**Counts (test, post-vasopressor set):**

| Quantity | n |
|---|---|
| Test cases | 149 |
| Total windows | 3,424 |
| Sex-specific cases | 22 |
| Windows lost to exclusion | 412 |
| Windows with MAP < 65 (total) | 438 |
| … of which in excluded cases | 84 |
| **Usable primary windows** | **354** |

*Note: the raw test folder (3,457 windows) has 447 with MAP < 65; the remaining 9 are
vasopressor windows excluded from the analysis.*

**Manual review of the 22 excluded cases:** 20 breast (mastectomy/breast-conserving surgery,
including two `Excision`/`Wide excision` with a breast diagnosis and one `Hemihepatectomy` for
breast-carcinoma metastasis), 1 prostate (`Radical prostatectomy`) and 1 Fournier's gangrene
(`case6180`, dx "Fournier's gangrene, male", perineum/scrotum). **No false positives and no
obvious misses** (no TURP, hysterectomy, orchiectomy or gynecology in test).

Sex-specificity criterion (keywords over `pt_opname` + `pt_dx`, lowercase):
`breast, mastect, prostate, hysterect, oophor, salping, myomect, uterus, uterine, ovary,
ovarian, endometr, cervix, vagin, vulv, tubal, testicular, testis, scrot, penis, fournier,
turp, transurethral, orchi, orchid, vasect, circumcis, perineal`.

> Use `cervix` (uterine cervix) and **not** `cervical`, which in this dataset is almost always
> neck cervical (cervical spine, cervical lymph node dissection, thyroid) and would cause
> false positives. In test, `cervical` triggers no case, so the count does not change.

## 4. Arms

1. A **"male"** and a **"female"** version of the same case, run together and in **random
   order** (same seed), so run-to-run variability affects both equally.
2. **Optional**: a third, sex-neutral arm ("a 54-year-old patient") to test whether the word
   matters in itself, not just the direction of the sex.

## 5. Models

- **Primary (the 5 that reason)**: `deepseek-v4-pro`, `deepseek-flash`,
  `gemini-3.1-pro-preview`, `gpt-6-sol`, `claude-opus-5-5`.
- **No-reasoning contrast (optional)**: `opus-4-8`, `gpt-5.4`.

## 6. Results

### Primary (pooled, all 5 models)
In the 354 usable windows with `MAP < 65`: the overall effect of the version ("female" vs
"male") on the proportion of "increase_hypnotic", combining the 5 models and **stratified by
model** — **Mantel-Haenszel** (each window as a paired stratum) or **conditional logistic
regression with the window as the stratum**. Power rationale: `opus-5-5` proposes
"increase_hypnotic" in ≈ 8 % of these windows (~28 per arm), few discordant pairs; a
per-model McNemar would only detect a large effect.

### Secondary (per model)
**Exact McNemar per model** on the same windows, with **Holm** correction across the 5 models.

### Other secondary metrics
- Proportion of **any contraindicated action** (red flag) by version.
- Proportion of windows where the **action changes** between versions and the **direction** of
  the change.
- **Consensus accuracy** by version.

## 7. Estimated cost

| Configuration | Calls |
|---|---|
| 740 windows × 2 versions × 5 models | ≈ 7,400 |
| + neutral arm | ≈ 11,000 |

## 8. Caveats to declare

- **Weight and height do not change**: the swap isolates the word, not a real patient of the
  other sex. Any observed difference is not equivalent to clinical disparity.
- With 149 cases, some windows share a case; inference must be case-clustered when comparing
  rates between versions beyond the paired McNemar.
- **Sex appears only in the case header** ("N-year-old male/female", in `render_case`).
  Checked on the generated cases: the only leak outside the header is `case6180` ("Fournier's
  gangrene, male" in `pt_dx`), which is sex-specific and excluded. After exclusion, no
  remaining case contains "male / female / woman / she / her / his" outside the header.

## 9. Relation to the adjusted analysis (GEE)

The GEE of contraindicated actions **adding weight and height** (see `sex_adjusted.md` §2) is
informative only for `deepseek-v4-pro`: its sex effect (OR 2.23, p = 0.042) **disappears** when
adjusting for anthropometry (OR 1.26, p = 0.71). For `opus-5-5` (29 events) and `gpt-6-sol`
(33 events) the GEE is marked unstable and **cannot say anything**, for or against the channel.

For those two, an adjusted estimate would require **penalized (Firth) logistic regression** or
a **reduced model** (`sex + MAP + BIS + weight`); even so, with ~29 events it will remain
fragile. Analysis 3 remains the **only way** to answer for `opus-5-5` and `gpt-6-sol`.

Consistency with the counterfactual: since in the swapped case weight and height are **not
touched**, if the channel is anthropometry analysis 3 will come out **null**; if it is the
word, it will come out **positive**.

## 10. Decisions to fix before executing

- [ ] Seed and exact procedure for randomizing the arm order.
- [ ] Final n: 354 primary + 300 disjoint secondary (from non-excluded cases).
- [ ] Fix the primary pooled analysis (Mantel-Haenszel vs conditional logistic regression with
      the window as the stratum) before executing.
- [ ] Include or not the neutral arm and the 2 no-reasoning models.
- [ ] Definitive exclusion keyword list (manual review of the 22 cases already done).
- [ ] Reuse the existing prompt (`src/llm/prompt.txt`) or create one with the sex injected,
      ensuring sex appears only in the header.
