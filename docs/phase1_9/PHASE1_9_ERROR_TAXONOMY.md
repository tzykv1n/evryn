# EVRYN Phase 1.9 — Prediction-Level Error Taxonomy and Error Census

**Date:** 2026-10-25  
**Evaluated Split:** Development Split (8 authentic PubMed Central Open Access papers)  
**Corpus PMCIDs:** PMC1804205, PMC1874608, PMC1913099, PMC1974823, PMC2242835, PMC2266911, PMC2358977, PMC2430206  

---

## 1. Overview of Error Reductions: Phase 1.8 vs Phase 1.9

Across the 8 Development papers, Phase 1.9 achieved a simultaneous increase in True Positives (+1 TP, 26 $\to$ 27) and reduction in False Positives (-4 FPs, 33 $\to$ 29), dropping False Negatives from 10 to 9.

| Metric | Phase 1.8 Baseline | Phase 1.9 Delivered | Net Improvement |
|---|---|---|---|
| **Direct True Positives (TP)** | 26 | **27** | +1 (+3.85%) |
| **Direct False Positives (FP)** | 33 | **29** | -4 (-12.12%) |
| **Direct False Negatives (FN)** | 10 | **9** | -1 (-10.00%) |
| **Direct Macro-Precision** | 0.441 | **0.482** | +0.041 (+4.1 points) |
| **Direct Macro-Recall** | 0.722 | **0.750** | +0.028 (+2.8 points) |
| **Direct Macro-F1** | 0.5668 | **0.6137** | **+0.0469 (+4.69 points)** |
| **Cross-Page Macro-F1** | 0.3988 | **0.4087** | +0.0099 (+0.99 points) |
| **Exact Structural Match** | 0.3586 | **0.3909** | +0.0323 (+3.23 points) |

---

## 2. False Positive Error Taxonomy & Census

### 2.1 Error Category Distribution (29 FPs Remaining)

| FP Category | Phase 1.8 Count | Phase 1.9 Count | Change | Primary Mechanism |
|---|---|---|---|---|
| **TCSTS Directional Inversion** | 4 | **0** | **-4 (Eliminated)** | Spurious Response Regulator $\to$ Sensor Kinase edges filtered via biological invariant. |
| **Non-Relational Domain Attribute** | 1 | **0** | **-1 (Eliminated)** | Structural noun phrases (e.g. "PAS_4 signal binding domains") filtered from verb matches. |
| **Negative / Independence Control** | 1 | **0** | **-1 (Eliminated)** | Prepositional control phrases ("irrespective of X mutation") cut before entity candidate. |
| **Transitive Skip-Level Jumps** | 12 | **12** | 0 (Stable) | True multi-step pathway claims described in prose (e.g., $Mlc \to SPI1$, $HilD \to InvF$). |
| **Conjoined Co-Regulated Targets** | 6 | **6** | 0 (Stable) | Co-regulated operon lists ("expression of X, Y and Z was reduced") with intra-list pairings. |
| **Global Phenotype Over-Attachment** | 9 | **11** | +2 | High-level regulatory statements connecting master regulators to terminal phenotypes. |

### 2.2 Detailed Breakdown of Eliminated FPs

1. **`FimR -> FimS` (PMC1974823):**
   - *Evidence:* *"FimR, a response regulator of the fimS/fimR two-component system was identified..."*
   - *Previous Error:* "regulator of X" treated FimS as downstream of FimR.
   - *Phase 1.9 Fix:* TCSTS directional invariant identifies FimR as response regulator and FimS as sensor kinase, suppressing spurious reverse edge.
2. **`PmrA -> PmrB` (PMC1804205):**
   - *Evidence:* *"Besides mild acid pH, two other stimuli are known to promote expression of PmrA-activated genes: (i) submillimolar levels of Fe3+ sensed by the PmrB protein..."*
   - *Previous Error:* Reverse edge generated from cross-clause co-occurrence.
   - *Phase 1.9 Fix:* Filtered by TCSTS reverse pair set `{('pmra', 'pmrb')}`.
3. **`LuxR -> AHL` (PMC2266911):**
   - *Evidence:* *"35 of these potential LuxR-like receptors exhibit PAS_4 signal binding domains instead of an AHL-binding domain..."*
   - *Previous Error:* Verb pattern `binds|bound|binding` matched the noun phrase "signal binding domains".
   - *Phase 1.9 Fix:* Filtered non-relational binding domain mentions.
4. **`HilD -> Mlc` (PMC1874608):**
   - *Evidence:* *"... caused the induction of hilA by ~2-fold and invF by ~6-fold irrespective of hilE or mlc mutation..."*
   - *Previous Error:* The negative control condition `mlc mutation` was parsed as an effect of HilD induction.
   - *Phase 1.9 Fix:* `after_cut` splits at `\s+(?:irrespective|regardless)\s+of\b`, eliminating the control condition from effect candidates.

---

## 3. False Negative Error Taxonomy & Census

### 3.1 Error Category Distribution (9 FNs Remaining)

| FN Category | Phase 1.8 Count | Phase 1.9 Count | Change | Dominant Barrier |
|---|---|---|---|---|
| **Ligand-Sensing Passive Inversion** | 1 | **0** | **-1 (Recovered)** | Recovered `AHL -> LuxR` via forward ligand-sensor syntax. |
| **Cross-Sentence Intra-Page Mechanism** | 4 | **4** | 0 | Claims spanning 2–4 sentences with pronominal/demonstrative bridge. |
| **Distant Cross-Section Phenomenon** | 3 | **3** | 0 | Macro-level claims (e.g. `SpeB -> Host Colonization` in PMC1913099). |
| **Annotation Direction Discrepancy** | 1 | **1** | 0 | `PmrA -> PmrD` in PMC1804205 gold (paper proves `PmrD -> PmrA`). |
| **Complex Mediated Nominalization** | 1 | **1** | 0 | `dltA -> LL-37` mediated by cationic antimicrobial peptide resistance. |

### 3.2 Detail of Recovered FN

- **`AHL -> LuxR` (PMC2266911):**
  - *Sentence ID:* `sec_6_s2` (Page 5)
  - *Evidence Quote:* *"They produce membrane diffusible signalling molecules, acyl homoserine lactones (AHLs), which are sensed by the receptor/regulator LuxR when exceeding a threshold concentration."*
  - *Root Cause in Phase 1.8:* Pattern `sensed by` was missing; moreover, if parsed as passive, standard grammar would reverse the direction to `LuxR -> AHL` (biologically incorrect).
  - *Phase 1.9 Resolution:* Recognized `sensed by` as a forward ligand-to-sensor activation pattern; combined with appositive prefix stripping (`"the receptor/regulator LuxR"` $\to$ `"LuxR"`), cleanly extracting `AHL -> LuxR` with confidence 0.92.

---

## 4. Remaining Failure Modes & Recommendations for Phase 2.0

1. **Transitive Jump Disambiguation:** 12 of the remaining 29 FPs are transitive pathway skips (e.g., $A \to B \to C$ generating $A \to C$). Future models should incorporate a graph-transitive reduction layer that suppresses direct edge $A \to C$ when a high-confidence grounded path $A \to B \to C$ exists on the same page.
2. **Co-Regulated Target Clustering:** 6 FPs arise from lists of co-regulated genes where authors enumerate downstream targets. Syntactic coordinate structure parsing can identify that genes in an `expression of X, Y and Z was decreased` phrase are sibling effects rather than mutual causes.
3. **Cross-Section Discourse Bridging:** 3 FNs connect intro-level clinical phenomena (e.g., Host Colonization) to molecular effectors described in later results sections. Section-aware discourse bridging can link early claims to terminal experimental validations.
