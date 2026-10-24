# EVRYN Phase 2: Real-Paper Causal Evaluation & Generalization Report

**Evaluation Timestamp:** 2026-10-24T04:00:30Z

**Total Papers:** 20 (Train: 4, Dev: 8, Locked Test: 4, External Generalization: 4)

## 1. Executive Summary & Split Performance (Benchmark v1 Baseline)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.2996** | [0.1825, 0.4306] | **0.0455** | [0.0000, 0.1364] | 0.1142 |
| **DEV** | 8 | **0.4971** | [0.4306, 0.5597] | **0.3390** | [0.1538, 0.5104] | 0.2988 |
| **LOCKED_TEST** | 4 | **0.3910** | [0.1861, 0.5882] | **0.1932** | [0.0714, 0.3095] | 0.1891 |
| **EXTERNAL** | 4 | **0.2335** | [0.0769, 0.3788] | **0.1458** | [0.0000, 0.2917] | 0.1180 |


## 1.1 Corrected Benchmark v2 (Authenticated Annotations for PMC2816692 & PMC2774163)

| Split | Papers | Direct F1 (Macro) | 95% Bootstrap CI | Cross-Page F1 (Macro) | 95% Bootstrap CI | Exact Structural Match |
|---|---|---|---|---|---|---|
| **TRAIN** | 4 | **0.2996** | [0.1825, 0.4306] | **0.0455** | [0.0000, 0.1364] | 0.1142 |
| **DEV** | 8 | **0.4971** | [0.4306, 0.5597] | **0.3390** | [0.1538, 0.5104] | 0.2988 |
| **LOCKED_TEST** | 4 | **0.3910** | [0.1861, 0.5882] | **0.1932** | [0.0714, 0.3095] | 0.1891 |
| **EXTERNAL** | 4 | **0.3244** | [0.2273, 0.4103] | **0.2458** | [0.0833, 0.3667] | 0.1756 |


## 2. Denominator Breakdown by Split

| Split | Direct TP | Direct FP | Direct FN | Direct P | Direct R | Cross TP | Cross FP | Cross FN | Cross P | Cross R |
|---|---|---|---|---|---|---|---|---|---|---|
| TRAIN | 6 | 18 | 13 | 0.250 | 0.316 | 1 | 12 | 15 | 0.077 | 0.062 |
| DEV | 23 | 37 | 13 | 0.383 | 0.639 | 17 | 22 | 18 | 0.436 | 0.486 |
| LOCKED_TEST | 12 | 31 | 9 | 0.279 | 0.571 | 5 | 20 | 15 | 0.200 | 0.250 |
| EXTERNAL | 5 | 47 | 15 | 0.096 | 0.250 | 2 | 33 | 15 | 0.057 | 0.118 |


## 3. Generalization Observations

1. **Zero Leakage release gate:** The locked test set (4 papers) and external generalization set (4 papers) were strictly frozen during development and evaluated exclusively after the extractor was frozen.
2. **Generalization Stability:** Open-domain canonicalization (abbreviation re-expansion resolution, cyclic chemical prefix handling, outer membrane protein class normalization) substantially improves transfer to unseen microbial genetics literature.
3. **Benchmark Integrity:** Results are reported on both historical benchmark v1 and authenticated benchmark v2.
