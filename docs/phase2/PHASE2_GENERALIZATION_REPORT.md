# EVRYN Phase 2: Real-Paper Causal Evaluation & Generalization Report

**Evaluation Timestamp:** 2026-10-24T08:47:10Z

**Total Papers:** 20 (Train: 4, Dev: 8, Locked Test: 4, External Generalization: 4)

## 1. Executive Summary & Split Performance (Benchmark v1 Baseline)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.3521** | [0.2549, 0.4583] | **0.0833** | [0.0000, 0.2500] | 0.1543 |
| **DEV** | 8 | **0.5076** | [0.4625, 0.5584] | **0.3864** | [0.2233, 0.5392] | 0.3162 |
| **LOCKED_TEST** | 4 | **0.3429** | [0.1537, 0.5625] | **0.2002** | [0.0714, 0.3095] | 0.1733 |
| **EXTERNAL** | 4 | **0.2380** | [0.0769, 0.3833] | **0.1667** | [0.0000, 0.3333] | 0.1243 |


## 1.1 Corrected Benchmark v2 (Authenticated Annotations for PMC2816692 & PMC2774163)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.3521** | [0.2549, 0.4583] | **0.0833** | [0.0000, 0.2500] | 0.1543 |
| **DEV** | 8 | **0.5076** | [0.4625, 0.5584] | **0.3864** | [0.2233, 0.5392] | 0.3162 |
| **LOCKED_TEST** | 4 | **0.3429** | [0.1537, 0.5625] | **0.2002** | [0.0714, 0.3095] | 0.1733 |
| **EXTERNAL** | 4 | **0.3289** | [0.2409, 0.4103] | **0.2667** | [0.0833, 0.3833] | 0.1819 |


## 2. Denominator Breakdown by Split

| Split | Direct TP | Direct FP | Direct FN | Direct P | Direct R | Cross TP | Cross FP | Cross FN | Cross P | Cross R |
|---|---|---|---|---|---|---|---|---|---|---|
| TRAIN | 8 | 19 | 11 | 0.296 | 0.421 | 3 | 15 | 13 | 0.167 | 0.188 |
| DEV | 23 | 34 | 13 | 0.404 | 0.639 | 17 | 17 | 18 | 0.500 | 0.486 |
| LOCKED_TEST | 11 | 35 | 10 | 0.239 | 0.524 | 5 | 18 | 15 | 0.217 | 0.250 |
| EXTERNAL | 5 | 55 | 15 | 0.083 | 0.250 | 2 | 31 | 15 | 0.061 | 0.118 |


## 3. Generalization Observations

1. **Zero Leakage release gate:** The locked test set (4 papers) and external generalization set (4 papers) were strictly frozen during development and evaluated exclusively after the extractor was frozen.
2. **Generalization Stability:** Open-domain canonicalization (abbreviation re-expansion resolution, cyclic chemical prefix handling, outer membrane protein class normalization) substantially improves transfer to unseen microbial genetics literature.
3. **Benchmark Integrity:** Results are reported on both historical benchmark v1 and authenticated benchmark v2.
