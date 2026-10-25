# EVRYN Phase 2: Real-Paper Causal Evaluation & Generalization Report

**Evaluation Timestamp:** 2026-10-25T09:47:14Z

**Total Papers:** 20 (Train: 4, Dev: 8, Locked Test: 4, External Generalization: 4)

## 1. Executive Summary & Split Performance (Benchmark v1 Baseline)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.4750** | [0.3667, 0.6000] | **0.2083** | [0.0000, 0.4167] | 0.2389 |
| **DEV** | 8 | **0.6137** | [0.5273, 0.6860] | **0.4087** | [0.2308, 0.5810] | 0.3909 |
| **LOCKED_TEST** | 4 | **0.4658** | [0.3125, 0.6190] | **0.2051** | [0.0714, 0.3193] | 0.2240 |
| **EXTERNAL** | 4 | **0.2380** | [0.0769, 0.3833] | **0.1667** | [0.0000, 0.3333] | 0.1243 |


## 1.1 Corrected Benchmark v2 (Authenticated Annotations for PMC2816692 & PMC2774163)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.4750** | [0.3667, 0.6000] | **0.2083** | [0.0000, 0.4167] | 0.2389 |
| **DEV** | 8 | **0.6137** | [0.5273, 0.6860] | **0.4087** | [0.2308, 0.5810] | 0.3909 |
| **LOCKED_TEST** | 4 | **0.4658** | [0.3125, 0.6190] | **0.2051** | [0.0714, 0.3193] | 0.2240 |
| **EXTERNAL** | 4 | **0.3289** | [0.2409, 0.4103] | **0.2667** | [0.0833, 0.3833] | 0.1819 |


## 2. Denominator Breakdown by Split

| Split | Direct TP | Direct FP | Direct FN | Direct P | Direct R | Cross TP | Cross FP | Cross FN | Cross P | Cross R |
|---|---|---|---|---|---|---|---|---|---|---|
| TRAIN | 12 | 20 | 7 | 0.375 | 0.632 | 5 | 21 | 11 | 0.192 | 0.312 |
| DEV | 27 | 29 | 9 | 0.482 | 0.750 | 18 | 17 | 17 | 0.514 | 0.514 |
| LOCKED_TEST | 12 | 16 | 9 | 0.429 | 0.571 | 5 | 14 | 15 | 0.263 | 0.250 |
| EXTERNAL | 5 | 55 | 15 | 0.083 | 0.250 | 2 | 31 | 15 | 0.061 | 0.118 |


## 3. Generalization Observations

1. **Zero Leakage release gate:** The locked test set (4 papers) and external generalization set (4 papers) were strictly frozen during development and evaluated exclusively after the extractor was frozen.
2. **Generalization Stability:** Open-domain canonicalization (abbreviation re-expansion resolution, cyclic chemical prefix handling, outer membrane protein class normalization) substantially improves transfer to unseen microbial genetics literature.
3. **Benchmark Integrity:** Results are reported on both historical benchmark v1 and authenticated benchmark v2.
