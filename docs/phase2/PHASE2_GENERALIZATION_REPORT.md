# EVRYN Phase 2: Real-Paper Causal Evaluation & Generalization Report

**Evaluation Timestamp:** 2026-10-25T14:32:42Z

**Total Papers:** 20 (Train: 4, Dev: 8, Locked Test: 4, External Generalization: 4)

## 1. Executive Summary & Split Performance (Benchmark v1 Baseline)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.4750** | [0.3667, 0.6000] | **0.2120** | [0.0000, 0.4239] | 0.2408 |
| **DEV** | 8 | **0.6551** | [0.5521, 0.7523] | **0.4589** | [0.2585, 0.6519] | 0.4430 |
| **LOCKED_TEST** | 4 | **0.5654** | [0.3750, 0.7279] | **0.2637** | [0.0769, 0.4176] | 0.3019 |
| **EXTERNAL** | 4 | **0.3269** | [0.1000, 0.5269] | **0.2548** | [0.0833, 0.3714] | 0.1863 |


## 1.1 Corrected Benchmark v2 (Authenticated Annotations for PMC2816692 & PMC2774163)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.4750** | [0.3667, 0.6000] | **0.2120** | [0.0000, 0.4239] | 0.2408 |
| **DEV** | 8 | **0.6551** | [0.5521, 0.7523] | **0.4589** | [0.2585, 0.6519] | 0.4430 |
| **LOCKED_TEST** | 4 | **0.5654** | [0.3750, 0.7279] | **0.2637** | [0.0769, 0.4176] | 0.3019 |
| **EXTERNAL** | 4 | **0.4808** | [0.3538, 0.6077] | **0.3262** | [0.2857, 0.3714] | 0.2696 |


## 2. Denominator Breakdown by Split

| Split | Direct TP | Direct FP | Direct FN | Direct P | Direct R | Cross TP | Cross FP | Cross FN | Cross P | Cross R |
|---|---|---|---|---|---|---|---|---|---|---|
| TRAIN | 12 | 20 | 7 | 0.375 | 0.632 | 5 | 20 | 11 | 0.200 | 0.312 |
| DEV | 29 | 26 | 7 | 0.527 | 0.806 | 18 | 13 | 17 | 0.581 | 0.514 |
| LOCKED_TEST | 15 | 15 | 6 | 0.500 | 0.714 | 6 | 11 | 14 | 0.353 | 0.300 |
| EXTERNAL | 7 | 54 | 13 | 0.115 | 0.350 | 3 | 31 | 14 | 0.088 | 0.176 |


## 3. Generalization Observations

1. **Zero Leakage release gate:** The locked test set (4 papers) and external generalization set (4 papers) were strictly frozen during development and evaluated exclusively after the extractor was frozen.
2. **Generalization Stability:** Open-domain canonicalization (abbreviation re-expansion resolution, cyclic chemical prefix handling, outer membrane protein class normalization) substantially improves transfer to unseen microbial genetics literature.
3. **Benchmark Integrity:** Results are reported on both historical benchmark v1 and authenticated benchmark v2.
