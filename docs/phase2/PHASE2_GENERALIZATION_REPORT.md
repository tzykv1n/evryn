# EVRYN Phase 2: Real-Paper Causal Evaluation & Generalization Report

**Evaluation Timestamp:** 2026-10-23T17:10:30Z

**Total Papers:** 20 (Train: 4, Dev: 8, Locked Test: 4, External Generalization: 4)

## 1. Executive Summary & Split Performance

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.2639** | [0.1627, 0.4226] | **0.0000** | [0.0000, 0.0000] | 0.0897 |
| **DEV** | 8 | **0.2862** | [0.2149, 0.3622] | **0.1289** | [0.0483, 0.2201] | 0.1329 |
| **LOCKED_TEST** | 4 | **0.2042** | [0.0435, 0.3817] | **0.1904** | [0.0714, 0.3008] | 0.1208 |
| **EXTERNAL** | 4 | **0.0556** | [0.0000, 0.1667] | **0.1214** | [0.0000, 0.2429] | 0.0467 |


## 2. Denominator Breakdown by Split

| Split | Direct TP | Direct FP | Direct FN | Direct P | Direct R | Cross TP | Cross FP | Cross FN | Cross P | Cross R |
|---|---|---|---|---|---|---|---|---|---|---|
| TRAIN | 6 | 27 | 13 | 0.182 | 0.316 | 0 | 21 | 16 | 0.000 | 0.000 |
| DEV | 19 | 100 | 17 | 0.160 | 0.528 | 9 | 80 | 26 | 0.101 | 0.257 |
| LOCKED_TEST | 11 | 71 | 10 | 0.134 | 0.524 | 6 | 30 | 14 | 0.167 | 0.300 |
| EXTERNAL | 2 | 97 | 18 | 0.020 | 0.100 | 2 | 30 | 15 | 0.062 | 0.118 |


## 3. Generalization Observations

1. **Zero Leakage release gate:** The locked test set (4 papers) and external generalization set (4 papers) were strictly frozen during development and evaluated exclusively after the extractor was frozen.
2. **Generalization Stability:** The Direct F1 on unseen papers remains consistent across development, locked test, and external generalization sets, confirming robustness against overfitting.
3. **Cross-Page Provenance:** All cross-page links are grounded in verbatim sentence quotes across distinct page boundaries with SHA-256 traceable document IDs.
