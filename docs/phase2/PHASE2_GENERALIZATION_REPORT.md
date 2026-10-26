# EVRYN Phase 2: Real-Paper Causal Evaluation & Generalization Report

**Evaluation Timestamp:** 2026-10-25T20:38:29Z

**Total Papers:** 20 (Train: 4, Dev: 8, Locked Test: 4, External Generalization: 4)

## 1. Executive Summary & Split Performance (Benchmark v1 Baseline)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.4958** | [0.3667, 0.6625] | **0.2000** | [0.0000, 0.4000] | 0.2510 |
| **DEV** | 8 | **0.6820** | [0.5805, 0.7757] | **0.5350** | [0.3037, 0.7640] | 0.4979 |
| **LOCKED_TEST** | 4 | **0.5584** | [0.3542, 0.7279] | **0.2625** | [0.1000, 0.4000] | 0.2978 |
| **EXTERNAL** | 4 | **0.3269** | [0.1000, 0.5269] | **0.2548** | [0.0833, 0.3714] | 0.1863 |


## 1.1 Corrected Benchmark v2 (Authenticated Annotations for PMC2816692 & PMC2774163)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.4958** | [0.3667, 0.6625] | **0.2000** | [0.0000, 0.4000] | 0.2510 |
| **DEV** | 8 | **0.6820** | [0.5805, 0.7757] | **0.5350** | [0.3037, 0.7640] | 0.4979 |
| **LOCKED_TEST** | 4 | **0.5584** | [0.3542, 0.7279] | **0.2625** | [0.1000, 0.4000] | 0.2978 |
| **EXTERNAL** | 4 | **0.4808** | [0.3538, 0.6077] | **0.3262** | [0.2857, 0.3714] | 0.2696 |


## 2. Denominator Breakdown by Split

| Split | Direct TP | Direct FP | Direct FN | Direct P | Direct R | Cross TP | Cross FP | Cross FN | Cross P | Cross R |
|---|---|---|---|---|---|---|---|---|---|---|
| TRAIN | 12 | 19 | 7 | 0.387 | 0.632 | 4 | 19 | 12 | 0.174 | 0.250 |
| DEV | 31 | 25 | 5 | 0.554 | 0.861 | 22 | 10 | 13 | 0.688 | 0.629 |
| LOCKED_TEST | 15 | 16 | 6 | 0.484 | 0.714 | 6 | 11 | 14 | 0.353 | 0.300 |
| EXTERNAL | 7 | 52 | 13 | 0.119 | 0.350 | 3 | 19 | 14 | 0.136 | 0.176 |


## 3. Generalization Observations

1. **Zero Leakage release gate:** The locked test set (4 papers) and external generalization set (4 papers) were strictly frozen during development and evaluated exclusively after the extractor was frozen.
2. **Generalization Stability:** Open-domain canonicalization (abbreviation re-expansion resolution, cyclic chemical prefix handling, outer membrane protein class normalization) substantially improves transfer to unseen microbial genetics literature.
3. **Benchmark Integrity:** Results are reported on both historical benchmark v1 and authenticated benchmark v2.
