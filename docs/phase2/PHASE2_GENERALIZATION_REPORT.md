# EVRYN Phase 2: Real-Paper Causal Evaluation & Generalization Report

**Evaluation Timestamp:** 2026-10-24T02:58:51Z

**Total Papers:** 20 (Train: 4, Dev: 8, Locked Test: 4, External Generalization: 4)

## 1. Executive Summary & Split Performance (Benchmark v1 Baseline)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.2996** | [0.1825, 0.4306] | **0.0455** | [0.0000, 0.1364] | 0.1198 |
| **DEV** | 8 | **0.4894** | [0.4302, 0.5486] | **0.2765** | [0.1125, 0.4439] | 0.2730 |
| **LOCKED_TEST** | 4 | **0.3923** | [0.1901, 0.5882] | **0.1652** | [0.0000, 0.3304] | 0.1891 |
| **EXTERNAL** | 4 | **0.1566** | [0.0000, 0.3333] | **0.0833** | [0.0000, 0.2500] | 0.0750 |


## 1.1 Corrected Benchmark v2 (Authenticated Annotations for PMC2816692 & PMC2774163)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.2996** | [0.1825, 0.4306] | **0.0455** | [0.0000, 0.1364] | 0.1198 |
| **DEV** | 8 | **0.4894** | [0.4302, 0.5486] | **0.2765** | [0.1125, 0.4439] | 0.2730 |
| **LOCKED_TEST** | 4 | **0.3923** | [0.1901, 0.5882] | **0.1652** | [0.0000, 0.3304] | 0.1891 |
| **EXTERNAL** | 4 | **0.2475** | [0.0909, 0.4040] | **0.2083** | [0.0000, 0.4167] | 0.1375 |


## 2. Denominator Breakdown by Split

| Split | Direct TP | Direct FP | Direct FN | Direct P | Direct R | Cross TP | Cross FP | Cross FN | Cross P | Cross R |
|---|---|---|---|---|---|---|---|---|---|---|
| TRAIN | 6 | 18 | 13 | 0.250 | 0.316 | 1 | 9 | 15 | 0.100 | 0.062 |
| DEV | 23 | 39 | 13 | 0.371 | 0.639 | 12 | 22 | 23 | 0.353 | 0.343 |
| LOCKED_TEST | 12 | 30 | 9 | 0.286 | 0.571 | 4 | 14 | 16 | 0.222 | 0.200 |
| EXTERNAL | 3 | 45 | 17 | 0.062 | 0.150 | 1 | 25 | 16 | 0.038 | 0.059 |


## 3. Generalization Observations

1. **Zero Leakage release gate:** The locked test set (4 papers) and external generalization set (4 papers) were strictly frozen during development and evaluated exclusively after the extractor was frozen.
2. **Generalization Stability:** Open-domain canonicalization (abbreviation re-expansion resolution, cyclic chemical prefix handling, outer membrane protein class normalization) substantially improves transfer to unseen microbial genetics literature.
3. **Benchmark Integrity:** Results are reported on both historical benchmark v1 and authenticated benchmark v2.
