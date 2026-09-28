# EVRYN Scientific Discovery Master Report

Generated: 2026-09-28 14:26:03

## 1. Discovered Relation Families

| Family | Polarity | Count | Description |
| :--- | :---: | :---: | :--- |
| **Positive Regulation** | 1 | 2 | Increases, activates, enhances, or upregulates the target process or quantity |
| **Causal Production / Genesis** | 1 | 5 | Directly creates, generates, synthesizes, produces, or triggers the target entity |
| **Synergistic Co-Action / Joint Causation** | 1 | 1 | Multiple sources act conjunctively or nonlinearly to generate an effect |

## 2. Future Relation Forecasts

* **p53 mutation + kras activation -> metastatic invasiveness** (SYNERGISTIC_CO_ACTION, year 2029)
  * Probability: 0.801 (95% CI (0.751, 0.851))
  * Rationale: Higher-Order Synergy Hypothesis: 'p53 mutation' (conf 0.89) and 'kras activation' (conf 0.89) both independently regulate 'metastatic invasiveness'. High probability of joint synergy {p53 mutation, kras activation} -> metastatic invasiveness.

* **vegf upregulation -> tumor metastasis** (CAUSAL_PRODUCTION, year 2028)
  * Probability: 0.676 (95% CI (0.651, 0.702))
  * Rationale: Transitive discovery via bridge entity 'angiogenesis': 'vegf upregulation' -> 'angiogenesis' (conf 0.95) and 'angiogenesis' -> 'tumor metastasis' (conf 0.89) with mean evidence velocity +0.000/yr

* **nicotine -> addiction reinforcement** (CAUSAL_PRODUCTION, year 2028)
  * Probability: 0.641 (95% CI (0.612, 0.669))
  * Rationale: Transitive discovery via bridge entity 'dopamine release': 'nicotine' -> 'dopamine release' (conf 0.91) and 'dopamine release' -> 'addiction reinforcement' (conf 0.88) with mean evidence velocity +0.000/yr

## 3. Generated Scientific Hypotheses

### Contradiction Resolution: 'p53 mutation->cellular proliferation' (`hyp_contra_seq_0003`)
**Plausibility**: 0.820 | **Type**: `CONTRADICTION_RESOLUTION`

> Hypothesis of context-dependent bifurcation for relation 'p53 mutation->cellular proliferation' exhibiting conflicting causal polarities.

**Reasoning Chain**:
1. Temporal sequence for 'p53 mutation->cellular proliferation' exhibits simultaneous positive and negative/confounded evidence reports.
1. Suggests presence of an unmeasured latent modifier or cell-type specific regulatory switch.
1. First observed in 2020 with 2 total observations.

### Emerging Link Prediction: p53 mutation + kras activation -> metastatic invasiveness (`hyp_fc_fc_8c5de2c`)
**Plausibility**: 0.801 | **Type**: `TEMPORAL_EXTRAPOLATION`

> Predicted future causal link: p53 mutation + kras activation -> metastatic invasiveness (SYNERGISTIC_CO_ACTION) by 2029.

**Reasoning Chain**:
1. Higher-Order Synergy Hypothesis: 'p53 mutation' (conf 0.89) and 'kras activation' (conf 0.89) both independently regulate 'metastatic invasiveness'. High probability of joint synergy {p53 mutation, kras activation} -> metastatic invasiveness.
1. Calibrated path confidence: 0.801 within 95% CI [0.751, 0.851].
1. Forecast horizon targeted for year 2029.

### Cross-Domain Analogy: biomedicine -> neuroscience (`hyp_trans_ana_5ce2fd`)
**Plausibility**: 0.790 | **Type**: `CROSS_DOMAIN_TRANSFER`

> Cross-domain structural transfer: biomedicine motif (p53 mutation -> cellular proliferation) transfers to neuroscience (nicotine -> dopamine release).

**Reasoning Chain**:
1. Structural isomorphism score: 0.780
1. Mechanism match score: 0.800
1. Structural Cross-Domain Transfer: Motif 'linear_cascade' in biomedicine (p53 mutation -> cellular proliferation) maps structurally to neuroscience (nicotine -> dopamine release). Predicts parallel mechanism conservation under CAUSAL_PRODUCTION dynamics.

### Cross-Domain Analogy: biomedicine -> neuroscience (`hyp_trans_ana_57ae6c`)
**Plausibility**: 0.790 | **Type**: `CROSS_DOMAIN_TRANSFER`

> Cross-domain structural transfer: biomedicine motif (p53 mutation -> cellular proliferation) transfers to neuroscience (dopamine release -> addiction reinforcement).

**Reasoning Chain**:
1. Structural isomorphism score: 0.780
1. Mechanism match score: 0.800
1. Structural Cross-Domain Transfer: Motif 'linear_cascade' in biomedicine (p53 mutation -> cellular proliferation) maps structurally to neuroscience (dopamine release -> addiction reinforcement). Predicts parallel mechanism conservation under CAUSAL_PRODUCTION dynamics.

### Cross-Domain Analogy: biomedicine -> neuroscience (`hyp_trans_ana_5ce2fd`)
**Plausibility**: 0.790 | **Type**: `CROSS_DOMAIN_TRANSFER`

> Cross-domain structural transfer: biomedicine motif (p53 mutation -> cellular proliferation) transfers to neuroscience (nicotine -> dopamine release).

**Reasoning Chain**:
1. Structural isomorphism score: 0.780
1. Mechanism match score: 0.800
1. Structural Cross-Domain Transfer: Motif 'linear_cascade' in biomedicine (p53 mutation -> cellular proliferation) maps structurally to neuroscience (nicotine -> dopamine release). Predicts parallel mechanism conservation under CAUSAL_PRODUCTION dynamics.

### Higher-Order Synergy: {avian influenza A, secondary bacterial infection} (`hyp_ho_4ce784f276`)
**Plausibility**: 0.740 | **Type**: `HIGHER_ORDER_SYNERGY`

> Synergistic co-action {avian influenza A, secondary bacterial infection} exhibits joint causal interaction beyond independent additive effects.

**Reasoning Chain**:
1. Linguistic co-occurrence identified nominal coordination in text: 'Co-infection of avian influenza A and secondary bacterial infection triggers severe pneumo...'
1. Entities 'avian influenza A' and 'secondary bacterial infection' co-regulate downstream outcome.
1. Partial Information Decomposition (PID) candidate test flags potential non-zero synergistic information gain.

### Higher-Order Synergy: {chronic inflammation, epigenetic silencing} (`hyp_ho_134ed7f93b`)
**Plausibility**: 0.740 | **Type**: `HIGHER_ORDER_SYNERGY`

> Synergistic co-action {chronic inflammation, epigenetic silencing} exhibits joint causal interaction beyond independent additive effects.

**Reasoning Chain**:
1. Linguistic co-occurrence identified nominal coordination in text: 'Combined chronic inflammation and epigenetic silencing jointly accelerate oncogenesis....'
1. Entities 'chronic inflammation' and 'epigenetic silencing' co-regulate downstream outcome.
1. Partial Information Decomposition (PID) candidate test flags potential non-zero synergistic information gain.

### Emerging Link Prediction: vegf upregulation -> tumor metastasis (`hyp_fc_fc_c9b832d`)
**Plausibility**: 0.676 | **Type**: `TEMPORAL_EXTRAPOLATION`

> Predicted future causal link: vegf upregulation -> tumor metastasis (CAUSAL_PRODUCTION) by 2028.

**Reasoning Chain**:
1. Transitive discovery via bridge entity 'angiogenesis': 'vegf upregulation' -> 'angiogenesis' (conf 0.95) and 'angiogenesis' -> 'tumor metastasis' (conf 0.89) with mean evidence velocity +0.000/yr
1. Calibrated path confidence: 0.676 within 95% CI [0.651, 0.702].
1. Forecast horizon targeted for year 2028.

### Emerging Link Prediction: nicotine -> addiction reinforcement (`hyp_fc_fc_8da31e1`)
**Plausibility**: 0.641 | **Type**: `TEMPORAL_EXTRAPOLATION`

> Predicted future causal link: nicotine -> addiction reinforcement (CAUSAL_PRODUCTION) by 2028.

**Reasoning Chain**:
1. Transitive discovery via bridge entity 'dopamine release': 'nicotine' -> 'dopamine release' (conf 0.91) and 'dopamine release' -> 'addiction reinforcement' (conf 0.88) with mean evidence velocity +0.000/yr
1. Calibrated path confidence: 0.641 within 95% CI [0.612, 0.669].
1. Forecast horizon targeted for year 2028.

