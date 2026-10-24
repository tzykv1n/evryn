# EVRYN Phase 1.6: Post-Phase-1.5 Comprehensive Error Inventory

**Date:** 2026-10-24  
**Author:** EVRYN Lead Research & Engineering Team  
**Scope:** Complete failure analysis across all 20 benchmark papers (Train: 4, Dev: 8, Locked Test: 4, External Generalization: 4) on Benchmark V2 Authenticated and Benchmark V1 Baseline.

---

## 1. Executive Summary & Inventory Statistics

A full census of extraction discrepancies on the post-Phase-1.5 frozen baseline reveals:

- **Total Gold Direct Relations:** 91 (Train: 19, Dev: 36, Locked Test: 21, External: 20)
- **Total False Negatives (FN):** 48 (52.7% of all gold relations)
- **Total False Positives (FP):** 106 across all splits
- **Distribution of Errors by Split (Benchmark V2):**
  - **Train (4 papers):** 12 FN, 18 FP (Direct Macro-F1: 0.3306)
  - **Dev (8 papers):** 13 FN, 35 FP (Direct Macro-F1: 0.5007)
  - **Locked Test (4 papers):** 10 FN, 36 FP (Direct Macro-F1: 0.3374)
  - **External (4 papers):** 13 FN, 17 FP (Direct Macro-F1: 0.3244)

---

## 2. Actionable Error Taxonomy & Frequency Breakdown

### 2.1 False Negative Failure Categories (Total: 48)

| Failure Category | Frequency | % of FNs | Affected Papers | Root Cause Diagnosis |
|---|---|---|---|---|
| **Cross-Sentence Discourse / Missing Single-Sentence Co-occurrence** | 28 | 58.3% | PMC2651894, PMC2682197, PMC2714965, PMC2774163, PMC1913099, PMC2358977, PMC2581603, PMC2593050, PMC2816692, PMC2829055, PMC2858072, PMC2885601 | The gold relation's source and target entities do not co-occur in any single sentence in the PMC XML text. Ground truth was established via multi-paragraph scientific discourse or experimental tables. |
| **Missing Syntactic Triggers & Prepositional Frames** | 12 | 25.0% | PMC2651894, PMC2682197, PMC2774163, PMC1804205, PMC2242835, PMC2358977, PMC2430206, PMC2829055, PMC2885601 | Specialized causal locutions (*"fine tunes expression of"*, *"was restored upon complementation"*, *"is deficient in binding"*, *"modulates biofilm via"*) absent from regex dictionary. |
| **Direction Reversal Masking** | 5 | 10.4% | PMC2714965, PMC2358977, PMC1804205, PMC2885601 | A valid extraction was made from text, but assigned the opposite causal direction ($Effect \to Cause$), generating both an FN and an FP. |
| **Entity Canonicalization & Non-ASCII Gaps** | 3 | 6.3% | PMC2651894, PMC2774163, PMC2593050 | Greek characters (`σE` for `sigmaE`, `ΔvicK` for `VicK`) or compound suffix mismatch (`biofilm formation` vs `Biofilm`) prevented entity alignment. |

### 2.2 False Positive Failure Categories (Total: 106)

| Failure Category | Frequency | % of FPs | Affected Papers | Root Cause Diagnosis |
|---|---|---|---|---|
| **Spurious Co-occurrence / Unconstrained Association** | 54 | 50.9% | PMC2651894, PMC2682197, PMC2565068, PMC2593050, PMC2639726, PMC2816692, PMC2829055 | Unconnected entities appearing across complex compound sentences without direct causative dependency. |
| **Cross-Page / Indirect Gold Predicted Directly** | 28 | 26.4% | PMC2651894, PMC2774163, PMC1804205, PMC1874608, PMC1913099, PMC2242835, PMC2266911, PMC2565068, PMC2816692, PMC2829055 | The predicted relation is biologically true and present in the benchmark's `cross_page_edges`, but penalized as an FP in direct edge evaluation. |
| **Direction Reversals ($Effect \to Cause$)** | 24 | 22.7% | PMC2651894, PMC2682197, PMC2714965, PMC2774163, PMC1804205, PMC1874608, PMC1913099, PMC1974823, PMC2242835, PMC2266911, PMC2358977, PMC2565068, PMC2858072, PMC2885601 | Forward parser inverted passive complementation (*"virulence restored by X"* $\to$ `Virulence -> X`) or violated terminal phenotype invariants. |

---

## 3. Detailed Per-Split Error Inventory (Benchmark V2)

### 3.1 Training Split (4 Papers)

#### False Negatives (12)
1. **PMC2651894** (`RseA -> sigmaE`): Discourse across sections; Greek `σE` character in text.
2. **PMC2651894** (`sigmaE -> RpoE`): Co-occurs as *"effect of σE (rpoE)"*; appositive structure.
3. **PMC2651894** (`RpoE -> SsrB`): Text: *"RpoE is involved in fine-tuning the expression of a subset of SsrB-regulated genes"*; trigger *"fine-tuning"* unextracted.
4. **PMC2682197** (`ATP-Binding -> Bacillary Growth`): Cross-sentence discourse.
5. **PMC2682197** (`Bacillary Growth -> Persistent Infection`): Cross-sentence discourse.
6. **PMC2682197** (`Persistent Infection -> Virulence`): Complex discourse sentence.
7. **PMC2714965** (`cheB1 -> Chemotaxis`): Text: *"the main player in chemotaxis... including cheB1"*; predicative nominative syntax.
8. **PMC2714965** (`PMN Infiltration -> Host Survival`): Cross-sentence discourse.
9. **PMC2774163** (`GacS -> cyclic-di-GMP`): Cross-sentence discourse.
10. **PMC2774163** (`cyclic-di-GMP -> Biofilm`): Text: *"cyclic-di-GMP... modulate biofilm formation"*; length exceeded 160 chars and `"Biofilm Formation"` did not canonicalize to `"Biofilm"`.
11. **PMC2774163** (`Type III Secretion -> Virulence`): Cross-sentence discourse.
12. **PMC2774163** (`Biofilm -> Virulence`): Multi-sentence discourse.

#### False Positives (18)
1. **PMC2651894** (`SsrB -> Virulence`): True cross-page relation predicted directly from abstract.
2. **PMC2651894** (`Virulence -> SsrB`): Direction reversal; terminal phenotype as cause.
3. **PMC2651894** (`RpoE -> SseB`): Direct prediction of cross-page cascade.
4. **PMC2651894** (`SPI-2 -> RpoE`): Reversal of transcriptional cascade.
5. **PMC2682197** (`Rv2623 -> ATP`): Binding interaction treated as forward upregulation.
6. **PMC2682197** (`ATP -> Persistent Infection`): Text: *"ATP-dependent signaling... promotes persistent infection"*.
7. **PMC2714965** (`Virulence -> cheB2`): Direction reversal from *"virulence was restored in the complemented cheB2 mutant"*.
8. **PMC2774163** (`Virulence -> GacS`): Direction reversal; terminal phenotype as cause.
9. **PMC2774163** (`GacS -> Biofilm`): True cross-page gold relation predicted directly.

---

### 3.2 Development Split (8 Papers)

#### Key False Negatives (13)
1. **PMC1804205** (`PmrA -> PmrD`): Text: *"pmrD expression was dependent on PmrA"*; extracted in reverse (`PmrD -> PmrA`).
2. **PMC1913099** (`Adherence -> Streptolysin O`): Multi-sentence discourse.
3. **PMC1913099** (`SpeB -> Host Colonization`): Cross-sentence discourse.
4. **PMC1974823** (`Mfa1 -> Short Fimbriae`): Structural assembly description without explicit causal trigger.
5. **PMC1974823** (`Short Fimbriae -> Biofilm`): Text mentions *"biofilm formation"*; canonicalizer missed mapping to `"Biofilm"`.
6. **PMC2242835** (`EspA -> ESX-1`): Cross-sentence discourse.
7. **PMC2266911** (`AHL -> LuxR`): Text describes *"AHL-binding domain of LuxR"*; receptor-ligand binding.
8. **PMC2266911** (`Biofilm Formation -> Virulence`): Multi-sentence discourse.
9. **PMC2358977** (`89K -> SalK`): Cross-sentence genomic island annotation.
10. **PMC2358977** (`SalR -> PMN Resistance`): Multi-sentence discourse.
11. **PMC2358977** (`PMN Resistance -> Virulence`): Cross-sentence discourse.
12. **PMC2430206** (`GraRS -> GraR`): Regulatory autophosphorylation syntax.
13. **PMC2430206** (`dltA -> LL-37`): Susceptibility assay discourse.

#### Key False Positives (35)
1. **PMC1804205** (`PmrA -> Polymyxin B`): True cross-page edge predicted directly.
2. **PMC1804205** (`Acid pH -> PmrA`): True cross-page edge predicted directly.
3. **PMC1874608** (`Mlc -> SPI1`, `HilD -> SPI1`, `HilA -> Type III Secretion`): True cross-page regulatory edges predicted from summary sentences.
4. **PMC1913099** (`Adherence -> Host Colonization`): True cross-page gold relation.
5. **PMC2358977** (`Virulence -> SalK`, `Virulence -> SalR`): Direction reversals from *"virulence was restored upon reintroduction of salK and salR"*.

---

### 3.3 Locked Test Split (4 Papers)

#### Key Observations (10 FN, 36 FP)
- **PMC2565068:** 6/6 direct edges recovered (100% Direct Recall); 6 FPs were true cross-page relations.
- **PMC2581603:** 4 FNs due to multi-sentence discourse describing extracellular DNA cation chelation.
- **PMC2593050:** Greek `Δ` prefix (`ΔvicK`) prevented canonical entity detection, triggering filter fallback explosion (19 FPs).
- **PMC2639726:** 3/5 direct edges recovered; 4 FPs from terminal phenotype reversals (`Virulence -> SPI-2`, `Virulence -> SlyA`).

---

### 3.4 External Generalization Split (4 Papers)

#### Key Observations (13 FN, 17 FP)
- **PMC2816692:** 2/5 direct edges recovered; 3 FPs were true cross-page relations (`SrcA -> Effector Translocation`, `SseL -> Effector Translocation`).
- **PMC2829055:** 2/5 direct edges recovered; environmental temperature and flea vector relations accurately captured.
- **PMC2858072:** `BvrR/BvrS -> Virulence` extracted directly.
- **PMC2885601:** `Virulence -> Mac` direction reversal from complementation syntax (*"virulence restored by complementation with Mac"*).

---

## 4. Benchmark Version Comparison (V1 Baseline vs V2 Authenticated)

| Metric | Benchmark V1 Baseline | Benchmark V2 Authenticated | Discrepancy Cause |
|---|---|---|---|
| **External Direct F1** | 0.2335 [0.0769, 0.3788] | **0.3244** [0.2273, 0.4103] | PMC2816692 legacy Anthrax annotations in V1 replaced by authenticated Salmonella SrcA XML text in V2. |
| **External Direct FPs**| 58 | **17** | 41 spurious FPs eliminated by aligning gold annotations with genuine XML text. |
| **External Cross F1** | 0.1458 [0.0000, 0.2917] | **0.2458** [0.0833, 0.3667] | Authenticated cross-page chains in PMC2816692 match model extractions. |
| **Train/Dev/Locked** | Identical | Identical | Annotations for first 16 papers are identical in V1 and V2. |
