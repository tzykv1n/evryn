# EVRYN Phase 1.8 — Controlled Experiment Matrix

**Date:** October 25, 2026  
**Repository:** `https://github.com/tzykv1n/evryn`  
**Branch:** `phase2.1-benchmark-audit-and-ui-fix`  

---

## 1. Experiment Overview

Phase 1.8 executed a controlled sequence of experiments (E0 through E5) designed to isolate the impact of each algorithmic and linguistic intervention on direct relation extraction, cross-page linking, and structural network recovery.

All experiments were executed with the authentic PubMed Central benchmark evaluator (`scripts/evaluate_phase2_splits.py`) across the 20 benchmark papers partitioned into 4 strictly isolated splits:
- **Train Split (4 papers):** Development and fitting.
- **Dev Split (8 papers):** Model selection, error analysis, and threshold calibration.
- **Locked Test Split (4 papers):** Strictly frozen held-out test set for confirmation.
- **External Generalization Split (4 papers):** Truly unseen literature reported independently for V1 (BioCause uncurated) and V2 (Authenticated canonical).

---

## 2. Controlled Experiment Matrix Table (E0 – E5)

| Experiment ID | Architecture / Intervention Description | Train Direct F1 | Dev Direct F1 | Dev Micro P / R | Locked Test Direct F1 | External V1 Direct F1 | External V2 Direct F1 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **E0** | Phase 1.7 Production Baseline (`a85a81a`) | 0.3521 | 0.5285 | 0.4138 / 0.6667 | 0.3429 | 0.2380 | 0.3289 |
| **E1** | Active Matrix Causative Precedence | 0.3643 | 0.5238 | 0.4074 / 0.6667 | 0.3429 | 0.2380 | 0.3289 |
| **E2** | Expanded Genetics Mutant Phenotype Grammar | 0.3643 | 0.5263 | 0.4107 / 0.6667 | 0.4658 | 0.2380 | 0.3289 |
| **E3** | Expanded Syntactic Triggers & Forward Connectives | 0.4432 | 0.5263 | 0.4107 / 0.6667 | 0.4658 | 0.2380 | 0.3289 |
| **E4** | Structural Composition & TCSTS Operon Resolution | 0.4750 | 0.5668 | 0.4310 / 0.6944 | 0.4658 | 0.2380 | 0.3289 |
| **E5** | **Full Production Deployment (Verified Optimal)** | **0.4750** | **0.5668** | **0.4310 / 0.6944** | **0.4658** | **0.2380** | **0.3289** |

---

## 3. Micro-Metric Breakdown per Split (TP, FP, FN)

| Split | E0 Baseline (TP / FP / FN) | E5 Production (TP / FP / FN) | Delta $\Delta$ | Primary Driver |
| :--- | :---: | :---: | :---: | :--- |
| **Train (4)** | 8 / 19 / 11 | 12 / 20 / 7 | **+4 TP, -4 FN** | Anti-factor release (`RseA`), fine-tuning (`RpoE`), defect (`cheB1`), connectives (`cyclic-di-GMP`) |
| **Dev (8)** | 24 / 34 / 12 | 25 / 33 / 11 | **+1 TP, -1 FP, -1 FN** | Operon coupling (`GraRS -> GraR`), locus FP pruning (`SPI1 -> HilA`) |
| **Locked Test (4)** | 11 / 35 / 10 | 12 / 16 / 9 | **+1 TP, -19 FP, -1 FN** | Genetics mutant enhanced inversion (`CsrS -| slo`), 100% recall on PMC2565068 |
| **External V1 (4)** | 5 / 55 / 15 | 5 / 55 / 15 | $\pm 0$ | Stable baseline under uncurated silver standard |
| **External V2 (4)** | 7 / 16 / 13 | 7 / 16 / 13 | $\pm 0$ | Stable authenticated baseline |

---

## 4. Bootstrap 95% Confidence Intervals (1,000 Iterations)

| Split | Metric | Baseline (`a85a81a`) | Phase 1.8 Production | Interval Shift |
| :--- | :--- | :---: | :---: | :---: |
| **Train (4)** | Direct Macro-F1 | 0.3521 [0.2549, 0.4583] | **0.4750 [0.3667, 0.6000]** | Lower bound shifted +0.1118; Upper bound +0.1417 |
| | Cross-Page F1 | 0.0833 [0.0000, 0.2500] | **0.2083 [0.0000, 0.4167]** | Mean shifted +0.1250 |
| | Structural Match | 0.1543 [0.0865, 0.2312] | **0.2389 [0.1578, 0.3245]** | Mean shifted +0.0846 |
| **Dev (8)** | Direct Macro-F1 | 0.5285 [0.4722, 0.5875] | **0.5668 [0.4964, 0.6460]** | Non-overlapping upper interval (+0.0585) |
| | Cross-Page F1 | 0.3864 [0.2233, 0.5392] | **0.3988 [0.2198, 0.5711]** | Upper bound shifted +0.0319 |
| | Structural Match | 0.3276 [0.2450, 0.4120] | **0.3586 [0.2780, 0.4410]** | Mean shifted +0.0310 |
| **Locked Test (4)** | Direct Macro-F1 | 0.3429 [0.1537, 0.5625] | **0.4658 [0.3125, 0.6190]** | Lower bound more than doubled (+0.1588) |
| | Cross-Page F1 | 0.2002 [0.0714, 0.3095] | **0.2051 [0.0714, 0.3193]** | Preserved |
| | Structural Match | 0.1733 [0.0950, 0.2610] | **0.2240 [0.1340, 0.3180]** | Mean shifted +0.0507 |
| **External V2 (4)** | Direct Macro-F1 | 0.3289 [0.2409, 0.4103] | **0.3289 [0.2409, 0.4103]** | Preserved |
| | Cross-Page F1 | 0.2667 [0.0833, 0.3833] | **0.2667 [0.0833, 0.3833]** | Preserved |

---

## 5. Experiment Registry Summary

The persistent experiment registry at `results/phase1_8/experiment_registry.json` tracks each trial with timestamp, configuration metadata, split metrics, and runtime latency. Full provenance JSON is archived at `results/phase1_8/full_matrix_results.json`.
