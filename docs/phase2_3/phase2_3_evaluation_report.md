# EVRYN Phase 2.3: Systematic Causal Extraction & Cross-Page Evaluation Report

**Date:** 2026-10-27 04:37:47Z
**Prompt Version:** `v2.2.0`
**Systems Evaluated:**
1. **System A — Phase 2.3 Repaired Rule-Based NLP Pipeline** (`nlp_baseline`)
2. **System B — LLM-Only Candidate Extraction** (`llm_only`)
3. **System C — Hybrid LLM + Deterministic Validation** (`hybrid`)

## DEV Split Evaluation Summary

| System | Macro Direct F1 (95% CI) | Micro Direct P / R / F1 | Macro Cross-Page F1 (95% CI) | Direction Acc | False Transitive Jumps | Exact Struct Match | Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **System A (NLP Baseline)** | 0.6744 [0.5805, 0.7660] | 0.554 / 0.861 / 0.674 | 0.5414 [0.3119, 0.7768] | 100.0% | 9 | 0.4972 | 4.97s |
| **System B (LLM Only)** | 0.1625 [0.1298, 0.2032] | 0.075 / 0.556 / 0.132 | 0.2580 [0.1290, 0.3907] | 100.0% | 55 | 0.1027 | 0.05s |
| **System C (Hybrid LLM + Validation)** | 0.1531 [0.0323, 0.2697] | 0.164 / 0.306 / 0.214 | 0.2149 [0.0577, 0.3910] | 50.0% | 27 | 0.1051 | 1.03s |

## LOCKED_TEST Split Evaluation Summary

| System | Macro Direct F1 (95% CI) | Micro Direct P / R / F1 | Macro Cross-Page F1 (95% CI) | Direction Acc | False Transitive Jumps | Exact Struct Match | Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **System A (NLP Baseline)** | 0.5696 [0.3875, 0.7279] | 0.432 / 0.762 / 0.552 | 0.2625 [0.1000, 0.4000] | 100.0% | 11 | 0.3020 | 2.33s |
| **System B (LLM Only)** | 0.1928 [0.1267, 0.2487] | 0.085 / 0.476 / 0.144 | 0.3431 [0.2361, 0.4500] | 100.0% | 17 | 0.1302 | 0.03s |
| **System C (Hybrid LLM + Validation)** | 0.2136 [0.0714, 0.3095] | 0.238 / 0.238 / 0.238 | 0.0000 [0.0000, 0.0000] | 75.0% | 2 | 0.0743 | 0.79s |

## EXTERNAL Split Evaluation Summary

| System | Macro Direct F1 (95% CI) | Micro Direct P / R / F1 | Macro Cross-Page F1 (95% CI) | Direction Acc | False Transitive Jumps | Exact Struct Match | Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **System A (NLP Baseline)** | 0.3269 [0.1000, 0.5269] | 0.123 / 0.350 / 0.182 | 0.2548 [0.0833, 0.3714] | 75.0% | 19 | 0.1863 | 2.00s |
| **System B (LLM Only)** | 0.0653 [0.0000, 0.1306] | 0.062 / 0.250 / 0.100 | 0.2539 [0.0000, 0.5077] | 50.0% | 10 | 0.0578 | 0.08s |
| **System C (Hybrid LLM + Validation)** | 0.0667 [0.0000, 0.2000] | 0.118 / 0.100 / 0.108 | 0.1429 [0.0000, 0.4285] | 25.0% | 0 | 0.0556 | 0.22s |

## Per-Paper Direct & Cross-Page Breakdown (Development Split)

| PMCID | Paper Title | System | Direct (TP / FP / FN) | Direct F1 | Cross-Page (TP / FP / FN) | Cross F1 |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `PMC1804205` | Acid pH activation of the PmrA/PmrB... | nlp_baseline | 5 / 5 / 0 | **0.6667** | 5 / 4 / 0 | **0.7143** |
| `PMC1874608` | Mlc regulation of Salmonella pathog... | nlp_baseline | 5 / 6 / 0 | **0.6250** | 4 / 3 / 1 | **0.6667** |
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

## Per-Paper Direct & Cross-Page Breakdown (Locked Test Split)

| PMCID | Paper Title | System | Direct (TP / FP / FN) | Direct F1 | Cross-Page (TP / FP / FN) | Cross F1 |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `PMC2565068` | Incompetence of Neutrophils to Inva... | nlp_baseline | 6 / 5 / 0 | **0.7059** | 3 / 8 / 1 | **0.4000** |
| `PMC2581603` | Extracellular DNA Chelates Cations ... | nlp_baseline | 2 / 8 / 3 | **0.2667** | 1 / 1 / 5 | **0.2500** |
| `PMC2593050` | The Two-Component Regulatory System... | nlp_baseline | 3 / 0 / 2 | **0.7500** | 0 / 0 / 4 | **0.0000** |
| `PMC2639726` | Coordinated Regulation of Virulence... | nlp_baseline | 5 / 8 / 0 | **0.5556** | 2 / 2 / 4 | **0.4000** |
| `PMC2565068` | Incompetence of Neutrophils to Inva... | llm_only | 3 / 17 / 3 | **0.2308** | 1 / 4 / 3 | **0.2222** |
| `PMC2581603` | Extracellular DNA Chelates Cations ... | llm_only | 2 / 8 / 3 | **0.2667** | 1 / 1 / 5 | **0.2500** |
| `PMC2593050` | The Two-Component Regulatory System... | llm_only | 1 / 5 / 4 | **0.1818** | 1 / 0 / 3 | **0.4000** |
| `PMC2639726` | Coordinated Regulation of Virulence... | llm_only | 4 / 78 / 1 | **0.0920** | 6 / 12 / 0 | **0.5000** |
| `PMC2565068` | Incompetence of Neutrophils to Inva... | hybrid | 2 / 6 / 4 | **0.2857** | 0 / 2 / 4 | **0.0000** |
| `PMC2581603` | Extracellular DNA Chelates Cations ... | hybrid | 1 / 0 / 4 | **0.3333** | 0 / 0 / 6 | **0.0000** |
| `PMC2593050` | The Two-Component Regulatory System... | hybrid | 0 / 0 / 5 | **0.0000** | 0 / 0 / 4 | **0.0000** |
| `PMC2639726` | Coordinated Regulation of Virulence... | hybrid | 2 / 10 / 3 | **0.2353** | 0 / 0 / 6 | **0.0000** |

## Per-Paper Direct & Cross-Page Breakdown (External Split)

| PMCID | Paper Title | System | Direct (TP / FP / FN) | Direct F1 | Cross-Page (TP / FP / FN) | Cross F1 |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `PMC2816692` | Structural and Biochemical Characte... | nlp_baseline | 0 / 39 / 5 | **0.0000** | 0 / 17 / 4 | **0.0000** |
| `PMC2829055` | Transit through the Flea Vector Ind... | nlp_baseline | 2 / 6 / 3 | **0.3077** | 1 / 1 / 3 | **0.3333** |
| `PMC2858072` | Transcriptome Analysis of the Bruce... | nlp_baseline | 3 / 2 / 2 | **0.6000** | 1 / 1 / 4 | **0.2857** |
| `PMC2885601` | IgG Endopeptidase SeMac does not In... | nlp_baseline | 2 / 3 / 3 | **0.4000** | 1 / 0 / 3 | **0.4000** |
| `PMC2816692` | Structural and Biochemical Characte... | llm_only | 0 / 1 / 5 | **0.0000** | 0 / 0 / 4 | **0.0000** |
| `PMC2829055` | Transit through the Flea Vector Ind... | llm_only | 0 / 9 / 5 | **0.0000** | 1 / 0 / 3 | **0.4000** |
| `PMC2858072` | Transcriptome Analysis of the Bruce... | llm_only | 3 / 45 / 2 | **0.1132** | 4 / 4 / 1 | **0.6154** |
| `PMC2885601` | IgG Endopeptidase SeMac does not In... | llm_only | 2 / 20 / 3 | **0.1481** | 0 / 6 / 4 | **0.0000** |
| `PMC2816692` | Structural and Biochemical Characte... | hybrid | 0 / 0 / 5 | **0.0000** | 0 / 0 / 4 | **0.0000** |
| `PMC2829055` | Transit through the Flea Vector Ind... | hybrid | 0 / 6 / 5 | **0.0000** | 0 / 0 / 4 | **0.0000** |
| `PMC2858072` | Transcriptome Analysis of the Bruce... | hybrid | 2 / 8 / 3 | **0.2667** | 2 / 0 / 3 | **0.5714** |
| `PMC2885601` | IgG Endopeptidase SeMac does not In... | hybrid | 0 / 1 / 5 | **0.0000** | 0 / 0 / 4 | **0.0000** |
