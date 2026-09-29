# S1. Example case shown to the model

- window_id: `case1001_w13979` · case_id: `1001`
- result_real: `reduce_hypnotic` · result_1: `reduce_opioid` · result_aux: `increase_hypnotic`

The exact text the model sees (the `{case}` variable in the prompt):

```text
A 69-year-old male (62.8 kg, 166.5 cm, BMI 22.7, ASA 2) patient is undergoing Endovascular aneurysmal repair (Vascular, Open, General), elective.
Diagnosis: Aneurysm, abdominal aorta.
Department: General surgery.
Monitoring: arterial line.
Current vitals: HR 87.6 bpm, MAP 89.1 mmHg, SpO2 100 %, EtCO2 36 mmHg, BIS 66.3.
Recent trends: HR rising, MAP falling, BIS rising, SpO2 rising, EtCO2 rising.
Drugs: propofol effect-site concentration 3.5, remifentanil effect-site concentration 4.99, MAC 0.
Ventilator: FiO2 40, PEEP 0, tidal volume 0.36, respiratory rate 16.
Preoperative labs: hb 11.7 g/dL, hct 35.9 %, plt 352 K/uL, wbc 8.15 K/uL, na 140 mEq/L, k 4.4 mEq/L, gluc 132 mg/dL, cr 1.11 mg/dL, lac 1.1 mmol/L, ph 7.39, hco3 29.7 mEq/L.
Recent course: Patient: age=69.0, sex=M, height=166.5, weight=62.8, bmi=22.7, asa=2.0, department=General surgery, opname=Endovascular aneurysmal repair. Comorbidities: HTN. Start of anesthesia.
```

Response options (5-option prompt):
a) increase_hypnotic · b) reduce_hypnotic · c) increase_opioid · d) reduce_opioid · e) no_action

Response options (3-option prompt, no-opioid subgroup):
a) increase_hypnotic · b) reduce_hypnotic · c) no_action