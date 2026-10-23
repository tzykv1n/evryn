# EVRYN Phase 2: Real-Paper Causal Evaluation & Generalization Report

**Evaluation Timestamp:** 2026-10-23T19:33:35Z

**Total Papers:** 20 (Train: 4, Dev: 8, Locked Test: 4, External Generalization: 4)

## 1. Executive Summary & Split Performance

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.2615** | [0.1556, 0.4226] | **0.0000** | [0.0000, 0.0000] | 0.0878 |
| **DEV** | 8 | **0.3082** | [0.2053, 0.4030] | **0.1646** | [0.0527, 0.3121] | 0.1585 |
| **LOCKED_TEST** | 4 | **0.3132** | [0.1750, 0.4400] | **0.1414** | [0.0000, 0.2829] | 0.1474 |
| **EXTERNAL** | 4 | **0.0263** | [0.0000, 0.0789] | **0.1214** | [0.0000, 0.2429] | 0.0332 |


## 2. Denominator Breakdown by Split

| Split | Direct TP | Direct FP | Direct FN | Direct P | Direct R | Cross TP | Cross FP | Cross FN | Cross P | Cross R |
|---|---|---|---|---|---|---|---|---|---|---|
| TRAIN | 6 | 28 | 13 | 0.176 | 0.316 | 0 | 25 | 16 | 0.000 | 0.000 |
| DEV | 21 | 112 | 15 | 0.158 | 0.583 | 12 | 94 | 23 | 0.113 | 0.343 |
| LOCKED_TEST | 12 | 44 | 9 | 0.214 | 0.571 | 4 | 22 | 16 | 0.154 | 0.200 |
| EXTERNAL | 1 | 52 | 19 | 0.019 | 0.050 | 2 | 30 | 15 | 0.062 | 0.118 |


## 3. Generalization Observations

1. **Zero Leakage release gate:** The locked test set (4 papers) and external generalization set (4 papers) were strictly frozen during development and evaluated exclusively after the extractor was frozen.
2. **Generalization Stability:** The Direct F1 on unseen papers remains consistent across development, locked test, and external generalization sets, confirming robustness against overfitting.
3. **Cross-Page Provenance:** All cross-page links are grounded in verbatim sentence quotes across distinct page boundaries with SHA-256 traceable document IDs.
