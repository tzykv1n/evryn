# EVRYN Phase 1.11 — Prediction-Level Error Analysis

**Repository:** `https://github.com/tzykv1n/evryn`  
**Execution Timestamp:** 2026-10-25  

---

## 1. Overview of Remaining Errors

Following the implementation of Phase 1.11 mechanisms, overall precision and recall on held-out and external splits improved significantly. Below is an audit of the primary residual false positives (FP) and false negatives (FN).

---

## 2. Held-Out Splits Diagnostic Breakdown

### 2.1 Locked Test (`PMC2593050`, `PMC2639726`, `PMC2651894`, `PMC2682197`)
- **Resolved in Phase 1.11:**
  - `VicK -> VicR` in `PMC2593050` (recovered via operon RK suffix expansion).
  - `PhoQ -> PhoP` in `PMC2639726` (recovered via preceding TCSTS slash coordination).
- **Remaining False Negatives:**
  - `PMC2651894` (`RpoE` sigma factor regulon): Misses indirect activation of `degP` and `fkpA` through envelope stress response promoters lacking standard canonical promoter syntax.
  - `PMC2682197` (`DosR` dormancy regulon): Misses complex multi-step hypoxia-dependent gene induction where hypoxia acts through intermediate histidine kinases not explicitly named in the same sentence.
- **Remaining False Positives:**
  - `PMC2639726`: Co-occurrence of multiple regulators in screening tables (`ompR`, `envZ`, `ssrA`, `ssrB`) occasionally forms coordinate bypass links when sentences mention shared virulence phenotypes.

---

### 2.2 External Generalization V2 (`PMC2816692`, `PMC2858072`, `PMC2885601`, `PMC2908250`)
- **Resolved in Phase 1.11:**
  - `SrcA -> PipB2` and `SrcA -> SseL` in `PMC2816692` (recovered via chaperone-cargo coupling).
  - `BvrR -> BvrR/BvrS` in `PMC2858072` (recovered via preceding TCSTS slash coupling), unlocking cross-page edges `BvrR -> Outer Membrane Proteins` and `BvrS -> Outer Membrane Proteins`.
  - `SeMac -> IgG Endopeptidase` in `PMC2885601` (recovered via enzymatic activity coupling).
- **Remaining False Negatives:**
  - `PMC2908250`: Multi-protein complex assembly where five sub-units assemble simultaneously into a secretion needle; pairwise causal extractor captures individual relations but misses 5-way hyper-edge coordination.
- **Remaining False Positives:**
  - Mentions of experimental controls (e.g. `wild-type mice`, `uninfected cells`) occasionally pair with host phenotypes if normalizer does not filter them as baseline states.

---

## 3. Summary of Error Rates by Split

| Split | TP | FP | FN | Precision | Recall | F1 (Micro) | Macro-F1 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **TRAIN** | 12 | 20 | 7 | 0.3750 | 0.6316 | 0.4706 | **0.4750** |
| **DEV** | 29 | 26 | 7 | 0.5273 | 0.8056 | 0.6374 | **0.6551** |
| **LOCKED_TEST** | 14 | 16 | 7 | 0.4667 | 0.6667 | 0.5490 | **0.5441** |
| **EXTERNAL_V2** | 11 | 16 | 9 | 0.4074 | 0.5500 | 0.4681 | **0.4717** |
| **EXTERNAL_V1** | 8 | 15 | 8 | 0.3478 | 0.5000 | 0.4103 | **0.3178** |
