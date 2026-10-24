# EVRYN Phase 1.1: Extraction Reliability and External Generalization Research Report

**Date:** 2026-10-24  
**Author:** EVRYN Lead Research & Benchmarking Engineering Sprint  
**Active Branch:** `phase2.1-benchmark-audit-and-ui-fix`  
**Git Checkpoint Tag:** `checkpoint-phase1-sprint-19fedd4`  
**Evaluation Scope:** 20 authentic PubMed Central papers across 4 paper-disjoint splits:
- **Train:** 4 papers (PMC2651894, PMC2682197, PMC2714965, PMC2774163)
- **Dev:** 8 papers (PMC1804205, PMC1874608, PMC1913099, PMC1974823, PMC2242835, PMC2266911, PMC2358977, PMC2430206)
- **Locked Test:** 4 papers (PMC2565068, PMC2581603, PMC2593050, PMC2639726)
- **External Generalization:** 4 papers (PMC2816692, PMC2829055, PMC2858072, PMC2885601)

---

## 1. Executive Summary

This research sprint investigated and remediated the primary extraction failure modes of the EVRYN multi-page scientific causal relation extraction engine. Working strictly under a **zero-leakage split isolation protocol**, all failure analysis, ablation experiments, and heuristic parameter selections were performed exclusively on the **8 Development papers**. The held-out splits (**Locked Test** and **External Generalization**) were frozen and evaluated only once at the conclusion of development.

### Key Deliverables & Metric Improvements:
1. **Locked Test Generalization (Held-Out Confirmatory Release Gate):**
   - **Direct Causal F1:** Improved from **0.3132** (95% CI: [0.1750, 0.4400]) to **0.4021** (95% CI: [0.1901, 0.6176]), a **+28.4% relative gain**.
   - **Cross-Page F1:** Improved from **0.1414** (95% CI: [0.0000, 0.2829]) to **0.2078** (95% CI: [0.0000, 0.4156]), a **+47.0% relative gain**.
   - **Structural Match:** Improved from **0.1474** (95% CI: [0.0663, 0.2286]) to **0.2175** (95% CI: [0.1009, 0.3341]), a **+47.6% relative gain**.
2. **Development Split (8 Papers):**
   - **Direct Causal F1:** Improved from **0.3082** (95% CI: [0.2053, 0.4030]) to **0.4280** (95% CI: [0.3312, 0.5126]), a **+38.9% relative gain**.
   - **Cross-Page F1:** Improved from **0.1646** (95% CI: [0.0527, 0.3121]) to **0.2356** (95% CI: [0.0625, 0.4351]), a **+43.1% relative gain**.
   - **Structural Match:** Improved from **0.1585** (95% CI: [0.0980, 0.2336]) to **0.2360** (95% CI: [0.1673, 0.3047]), a **+48.9% relative gain**.
3. **Train Split Cross-Page F1 Resolution:**
   - Train Cross-Page F1 was previously reported as **0.0000**. Through cross-page transitive link calibration and duplicate direct assertion suppression, Train Cross-Page F1 increased to **0.0455** (Direct F1 increased from **0.2615** to **0.2996**).
4. **External Generalization Forensic Diagnosis:**
   - Completed a complete forensic audit (`docs/phase1_1/EXTERNAL_GENERALIZATION_AUDIT.md`) documenting that `PMC2816692` suffered from a ground truth XML corpus mismatch (Anthrax Lethal Factor curated gold vs *Salmonella* SrcA article XML). Under strict release gate rules, gold labels were frozen, and model-side consolidation improved external Direct F1 from **0.0263** to **0.0455**.
5. **System Invariants & UI Stability:**
   - Verified 221/221 passing unit and integration tests across the codebase.
   - Headless Playwright browser verification confirmed 0 console errors, clean session bulk management, and verified Examples tab operation.

---

## 2. Benchmark Comparison Tables

### Macro Metrics across All 4 Splits

| Split | Papers | Direct F1 (Baseline) | Direct F1 (Phase 1.1) | Cross-Page F1 (Baseline) | Cross-Page F1 (Phase 1.1) | Structural Match (Baseline) | Structural Match (Phase 1.1) |
|---|---|---|---|---|---|---|---|
| **Train** | 4 | 0.2615 [0.1556, 0.4226] | **0.2996** [0.1825, 0.4306] | 0.0000 [0.0000, 0.0000] | **0.0455** [0.0000, 0.1364] | 0.0878 [0.0461, 0.1486] | **0.1198** [0.0538, 0.1858] |
| **Dev** | 8 | 0.3082 [0.2053, 0.4030] | **0.4280** [0.3312, 0.5126] | 0.1646 [0.0527, 0.3121] | **0.2356** [0.0625, 0.4351] | 0.1585 [0.0980, 0.2336] | **0.2360** [0.1673, 0.3047] |
| **Locked Test** | 4 | 0.3132 [0.1750, 0.4400] | **0.4021** [0.1901, 0.6176] | 0.1414 [0.0000, 0.2829] | **0.2078** [0.0000, 0.4156] | 0.1474 [0.0663, 0.2286] | **0.2175** [0.1009, 0.3341] |
| **External** | 4 | 0.0263 [0.0000, 0.0789] | **0.0455** [0.0000, 0.1364] | 0.1214 [0.0000, 0.2429] | **0.0833** [0.0000, 0.2500] | 0.0332 [0.0000, 0.0664] | **0.0333** [0.0000, 0.0667] |

*All confidence intervals represent non-parametric bootstrap percentiles (95% CI, $n=1000$).*

---

## 3. Development-Only Controlled Experiments

All controlled experiments were formulated and validated strictly on the 8 Development papers:

### Experiment 1: Document-Level Assertion Deduplication
- **Hypothesis:** Multiple sentence-level assertions asserting the exact same causal edge (e.g. `(PmrB, PmrA)` extracted 8 times across PMC1804205) flood the prediction pool. Because the evaluator enforces 1-to-1 matching, 7 of those 8 extractions become false positives ($FP = \text{len}(\text{pred}) - TP$), reducing precision from 0.80+ to under 0.15.
- **Implementation:** In `PaperCausalExtractor.extract_assertions`, assertions are consolidated to the highest-confidence assertion per directed tuple `(cause_canonical, effect_canonical, is_negated)`.
- **Ablation Results on Dev Split:**
  - Sentence-level baseline: Direct F1 = 0.3082, Cross F1 = 0.1646, Structural Match = 0.1585
  - Page-level consolidation: Direct F1 = 0.3363, Cross F1 = 0.1646, Structural Match = 0.1666
  - Document-level consolidation: Direct F1 = **0.4179**, Cross F1 = **0.2138**, Structural Match = **0.2224**
- **Outcome:** Document-level consolidation adopted.

### Experiment 2: Genetics Mutant Inverted Syntax Recognition
- **Hypothesis:** Biological literature frequently reports causal mechanisms via mutant phenotypic reduction: `"<EFFECT> was dramatically reduced in the <CAUSE> mutant"`. The baseline extractor treated these as forward active relations, causing 24 direction reversal errors on Dev.
- **Implementation:** Added `COMPILED_GENETICS_MUTANT_DOWN` and `COMPILED_GENETICS_MUTANT_UP` patterns to `_match_relation` in `evryn/paper/extractor.py`. When a target gene is downregulated in a regulator mutant, the regulator is mapped as the causal activator (`inv_dir = BACKWARD`, `UPREGULATES`).
- **Results on Dev Split:** Direct F1 increased to **0.4230**, eliminating direction reversals in PMC1804205, PMC1874608, PMC1974823, and PMC2242835.
- **Outcome:** Pattern accepted.

### Experiment 3: Cross-Page Transitive Link Consolidation & Normalizer Flexibility
- **Hypothesis:** `CrossPageLinker` emitted multi-edges across all pairs of pages for corroborated assertions, causing false positive inflation in cross-page predictions. In addition, minor plural and hyphenation mismatches caused the evaluator's `c_set` filter to discard valid entities and fall back to noisy raw text.
- **Implementation:** `CrossPageLinker` deduplicates links to the single best link per `(source_entity, target_entity)` pair. `PaperEntityNormalizer` adds singular/plural and hyphen-flexible normalization for known entities.
- **Results on Dev Split:** Direct F1 reached **0.4280** (+38.9%), Cross F1 reached **0.2356** (+43.1%), and Structural Match reached **0.2360** (+48.9%).
- **Outcome:** Full pipeline verified and accepted.

---

## 4. Train Split Cross-Page F1 Investigation

### Diagnostic Analysis:
In Phase 2 baseline, Train split cross-page F1 was 0.0000 despite gold cross-page edges existing in all 4 Train papers:
- **PMC2651894:** 4 gold cross edges (`(RseA, RpoE)`, `(sigmaE, SseB)`, `(RpoE, Virulence)`, `(sigmaE, Virulence)`).
- **PMC2682197:** 5 gold cross edges.
- **PMC2714965:** 3 gold cross edges.
- **PMC2774163:** 4 gold cross edges.

### Root Cause:
1. **Combinatorial Path Pollution:** Direct assertions had duplicate entries across multiple pages, causing transitive path search in `CrossPageLinker` to produce 17 noisy cross-page candidates in PMC2682197, none of which linked to the phenotypic target `Bacillary Growth` or `Virulence`.
2. **Reversed Direct Edges:** In PMC2651894, `Virulence -> RpoE` was predicted instead of `RpoE -> Virulence`, which prevented downstream transitive chains from terminating at `Virulence`.

### Fix Impact:
With document-level assertion consolidation and mutant syntax inversion, the transitive graph cleanly connected `SPI-2 -> SseB` and `RpoE -> Virulence`, yielding a verified Train cross-page F1 of **0.0455**.

---

## 5. System Integrity & UI Verification

1. **Unit & Pipeline Regression Tests:**
   - 221 passed out of 221 tests in `tests/` (196.82s).
   - Sanity evaluators, causal discovery, continual stream, deep encoder, SCM, and examples services pass 100%.
2. **Headless Browser Verification:**
   - Script: `scripts/verify_session_and_textbox.js`
   - Verified that the query input box is cleanly hidden on the Examples tab and restored upon switching to Graph/Table views.
   - Verified bulk session management: 38 session checkboxes, master select-all toggle, and bulk deletion controls operate without error.
   - Script: `scripts/verify_browser_ui.js`
   - Verified PDF cards (20/20), Text passages (50/50), Multipage chains (30/30), Paper modal causal comparisons, and 'Test in Workspace' transitions.
   - Browser console errors: **0**.

---

## 6. Reproducibility Manifest

- **Repository Root:** `/home/tk/projects/evryn`
- **Active Branch:** `phase2.1-benchmark-audit-and-ui-fix`
- **Python Virtualenv:** `/home/tk/projects/flux-nlp/.venv/bin/python` (Python 3.14.7)
- **Node Environment:** v20.19.1
- **Evaluation Command:**
  ```bash
  cd /home/tk/projects/evryn
  /home/tk/projects/flux-nlp/.venv/bin/python scripts/evaluate_phase2_splits.py
  ```
- **Diagnostic Command:**
  ```bash
  cd /home/tk/projects/evryn
  /home/tk/projects/flux-nlp/.venv/bin/python scripts/diagnose_splits_and_external_errors.py
  ```
- **Regression Command:**
  ```bash
  cd /home/tk/projects/evryn
  /home/tk/projects/flux-nlp/.venv/bin/pytest tests/
  ```
- **UI Verification Commands:**
  ```bash
  node scripts/verify_session_and_textbox.js
  node scripts/verify_browser_ui.js
  ```
- **Generated Diagnostic Artifacts:**
  - `results/phase1_1/split_diagnostics.json`
  - `results/phase1_1/experiment_registry.json`
  - `docs/phase1_1/EXTERNAL_GENERALIZATION_AUDIT.md`
  - `docs/phase1_1/PHASE1_1_RESEARCH_REPORT.md`
  - `results/phase2/phase2_benchmark_results.json`
  - `docs/phase2/PHASE2_GENERALIZATION_REPORT.md`
  - `results/phase2/phase2_splits_comparison.png`
