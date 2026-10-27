# EVRYN Phase 2.2: Systematic Three-Way Causal Extraction Comparison Report

**Date:** 2026-10-27 03:24:04Z  
**Prompt Version:** `v2.2.0`  
**Systems Evaluated:**
1. **System A — Repaired Rule-Based NLP Baseline** (`nlp_baseline`)
2. **System B — LLM-Only Candidate Extraction** (`llm_only`)
3. **System C — Hybrid LLM + Deterministic Validation** (`hybrid`)

## DEV Split Evaluation Summary

| System | Macro Direct F1 (95% CI) | Micro Direct P / R / F1 | Macro Cross-Page F1 (95% CI) | Direction Acc | False Transitive Jumps | Exact Struct Match | Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **System A (NLP Baseline)** | 0.6657 [0.5695, 0.7589] | 0.534 / 0.861 / 0.660 | 0.5350 [0.3037, 0.7640] | 100.0% | 10 | 0.4891 | 5.06s |
| **System B (LLM Only)** | 0.1625 [0.1298, 0.2032] | 0.075 / 0.556 / 0.132 | 0.2580 [0.1290, 0.3907] | 100.0% | 55 | 0.1027 | 0.19s |
| **System C (Hybrid LLM + Validation)** | 0.1531 [0.0323, 0.2697] | 0.164 / 0.306 / 0.214 | 0.2149 [0.0577, 0.3910] | 50.0% | 27 | 0.1051 | 1.03s |

## LOCKED_TEST Split Evaluation Summary

| System | Macro Direct F1 (95% CI) | Micro Direct P / R / F1 | Macro Cross-Page F1 (95% CI) | Direction Acc | False Transitive Jumps | Exact Struct Match | Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **System A (NLP Baseline)** | 0.5696 [0.3875, 0.7279] | 0.432 / 0.762 / 0.552 | 0.2625 [0.1000, 0.4000] | 100.0% | 11 | 0.3020 | 2.37s |
| **System B (LLM Only)** | 0.1928 [0.1267, 0.2487] | 0.085 / 0.476 / 0.144 | 0.3431 [0.2361, 0.4500] | 100.0% | 17 | 0.1302 | 0.08s |
| **System C (Hybrid LLM + Validation)** | 0.2136 [0.0714, 0.3095] | 0.238 / 0.238 / 0.238 | 0.0000 [0.0000, 0.0000] | 75.0% | 2 | 0.0743 | 0.79s |

## Per-Paper Direct & Cross-Page Breakdown (Development Split)

| PMCID | Paper Title | System | Direct (TP / FP / FN) | Direct F1 | Cross-Page (TP / FP / FN) | Cross F1 |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `PMC1804205` | Acid pH activation of the PmrA/PmrB... | nlp_baseline | 5 / 5 / 0 | **0.6667** | 5 / 4 / 0 | **0.7143** |
| `PMC1874608` | Mlc regulation of Salmonella pathog... | nlp_baseline | 5 / 8 / 0 | **0.5556** | 4 / 4 / 1 | **0.6154** |
| `PMC1913099` | Novel Algorithms Reveal Streptococc... | nlp_baseline | 2 / 2 / 2 | **0.5000** | 0 / 1 / 3 | **0.0000** |
| `PMC1974823` | Porphyromonas gingivalis short fimb... | nlp_baseline | 4 / 3 / 0 | **0.7273** | 5 / 0 / 0 | **1.0000** |
| `PMC2242835` | Control of M. tuberculosis ESAT-6 S... | nlp_baseline | 3 / 5 / 1 | **0.5000** | 4 / 1 / 1 | **0.8000** |
| `PMC2266911` | Comparative analysis of the Photorh... | nlp_baseline | 3 / 2 / 1 | **0.6667** | 0 / 0 / 3 | **0.0000** |
| `PMC2358977` | SalK/SalR, a Two-Component Signal T... | nlp_baseline | 5 / 1 / 0 | **0.9091** | 3 / 0 / 2 | **0.7500** |
| `PMC2430206` | The GraRS regulatory system control... | nlp_baseline | 4 / 1 / 1 | **0.8000** | 1 / 0 / 3 | **0.4000** |
| `PMC1804205` | Acid pH activation of the PmrA/PmrB... | llm_only | 5 / 75 / 0 | **0.1176** | 5 / 27 / 0 | **0.2703** |
| `PMC1874608` | Mlc regulation of Salmonella pathog... | llm_only | 4 / 68 / 1 | **0.1039** | 3 / 12 / 2 | **0.3000** |
| `PMC1913099` | Novel Algorithms Reveal Streptococc... | llm_only | 1 / 2 / 3 | **0.2857** | 0 / 0 / 3 | **0.0000** |
| `PMC1974823` | Porphyromonas gingivalis short fimb... | llm_only | 2 / 17 / 2 | **0.1739** | 1 / 5 / 4 | **0.1818** |
| `PMC2242835` | Control of M. tuberculosis ESAT-6 S... | llm_only | 2 / 22 / 2 | **0.1429** | 1 / 2 / 4 | **0.2500** |
| `PMC2266911` | Comparative analysis of the Photorh... | llm_only | 1 / 6 / 3 | **0.1818** | 0 / 1 / 3 | **0.0000** |
| `PMC2358977` | SalK/SalR, a Two-Component Signal T... | llm_only | 3 / 42 / 2 | **0.1200** | 3 / 5 / 2 | **0.4615** |
| `PMC2430206` | The GraRS regulatory system control... | llm_only | 2 / 16 / 3 | **0.1739** | 3 / 3 / 1 | **0.6000** |
| `PMC1804205` | Acid pH activation of the PmrA/PmrB... | hybrid | 3 / 20 / 2 | **0.2143** | 4 / 22 / 1 | **0.2581** |
| `PMC1874608` | Mlc regulation of Salmonella pathog... | hybrid | 4 / 22 / 1 | **0.2581** | 3 / 5 / 2 | **0.4615** |
| `PMC1913099` | Novel Algorithms Reveal Streptococc... | hybrid | 0 / 1 / 4 | **0.0000** | 0 / 0 / 3 | **0.0000** |
| `PMC1974823` | Porphyromonas gingivalis short fimb... | hybrid | 2 / 3 / 2 | **0.4444** | 1 / 0 / 4 | **0.3333** |
| `PMC2242835` | Control of M. tuberculosis ESAT-6 S... | hybrid | 0 / 1 / 4 | **0.0000** | 0 / 0 / 5 | **0.0000** |
| `PMC2266911` | Comparative analysis of the Photorh... | hybrid | 0 / 3 / 4 | **0.0000** | 0 / 0 / 3 | **0.0000** |
| `PMC2358977` | SalK/SalR, a Two-Component Signal T... | hybrid | 0 / 0 / 5 | **0.0000** | 0 / 0 / 5 | **0.0000** |
| `PMC2430206` | The GraRS regulatory system control... | hybrid | 2 / 6 / 3 | **0.3077** | 2 / 0 / 2 | **0.6667** |
