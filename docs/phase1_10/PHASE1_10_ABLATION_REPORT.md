# EVRYN Phase 1.10 — Controlled Ablation Report

**Repository:** `https://github.com/tzykv1n/evryn`  
**Branch:** `phase2.1-benchmark-audit-and-ui-fix`  
**Execution Timestamp:** 2026-10-25  
**Data Artifact:** `results/phase1_10/ablation_results.json`

---

## 1. Overview and Experimental Protocol

Phase 1.10 evaluated five isolated configurations to measure the exact marginal contribution of each extraction and gating mechanism across all benchmark splits:

- **A0 (Phase 1.9 Baseline):** Production system at commit `96799d7`.
- **A1 (+ Strict TCSTS Syntax):** Elimination of unanchored comma matches in `TCSTS_AND_RE`.
- **A2 (+ Locus Encoding):** Extraction of genomic pathogenicity island encoding relations (`enable_locus_encoding_inference=True`).
- **A3 (+ Resistance Defect):** Extraction of mutant phenotype resistance defects (`enable_phenotype_defect_inference=True`).
- **A4 (Full Phase 1.10):** Speculative clause and coordinate sibling validation (`enable_speculation_and_sibling_validation=True`).

All evaluations were executed without data contamination, holding the Train, Locked Test, and External splits frozen.

---

## 2. Quantitative Ablation Progression

| Configuration ID | Description | Dev Macro-F1 | Locked Test F1 | Train F1 | External V2 F1 | Dev TP / FP / FN | Net Dev $\Delta$ |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **A0** | Phase 1.9 Baseline | 0.6137 | 0.4658 | 0.4750 | 0.3289 | 27 / 29 / 9 | Baseline |
| **A1** | + Strict TCSTS Syntax | 0.6164 | 0.4756 | 0.4750 | 0.3289 | 27 / 28 / 9 | $+0.0027$ |
| **A2** | + Locus Encoding | 0.6330 | 0.4756 | 0.4750 | 0.3289 | 28 / 28 / 8 | $+0.0166$ |
| **A3** | + Resistance Defect | 0.6467 | 0.4756 | 0.4750 | 0.3289 | 29 / 28 / 7 | $+0.0137$ |
| **A4** | **Full Phase 1.10** | **0.6551** | **0.4756** | **0.4750** | **0.3289** | **29 / 26 / 7** | **$+0.0414$** |

---

## 3. Analysis of Individual Components

### 3.1 A1: Strict TCSTS Syntax
- **Dev F1:** 0.6137 $\to$ 0.6164 (+0.0027). FP reduced by 1 in PMC1874608 (`InvF -> HilA`).
- **Locked Test F1:** 0.4658 $\to$ 0.4756 (+0.0098). FP reduced by 1 from 16 to 15.
- **Key Takeaway:** Resolves spurious edge fabrication from coordinate gene lists that previously masqueraded as two-component signal transduction systems.

### 3.2 A2: Locus Encoding
- **Dev F1:** 0.6164 $\to$ 0.6330 (+0.0166). Recovers `89K -> SalK` in PMC2358977.
- **TP / FN:** True Positives increase from 27 to 28; False Negatives drop from 9 to 8.
- **Key Takeaway:** Corrects historical over-suppression of genomic locus encoding relationships in pathogenicity islands.

### 3.3 A3: Mutant Resistance Defect
- **Dev F1:** 0.6330 $\to$ 0.6467 (+0.0137). Recovers `SalR -> PMN Resistance` in PMC2358977.
- **TP / FN:** True Positives increase from 28 to 29; False Negatives drop from 8 to 7.
- **Key Takeaway:** Successfully extracts causal phenotypic capabilities from loss-of-function mutant prose (`"less able to resist killing"`).

### 3.4 A4: Speculation and Coordinate Sibling Gating
- **Dev F1:** 0.6467 $\to$ 0.6551 (+0.0084). Eliminates 2 residual false positives (`Mlc -> HilA`, `HilD -> SPI1`).
- **TP / FP / FN:** Dev FPs drop to 26 with 29 TPs intact.
- **Key Takeaway:** Strict filtering of speculative assertions (`"we speculated that..."`) prevents hypothetical conjectures from entering the factual knowledge graph.
