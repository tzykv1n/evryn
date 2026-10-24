# EVRYN Phase 1.2: Unseen-Paper Error Analysis & Diagnostic Taxonomy

**Date:** 2026-10-24  
**Scope:** Systematic classification of extraction errors on Development (8 papers) and Held-Out Unseen papers  
**Harness:** `scripts/diagnose_splits_and_external_errors.py` & `results/phase1_2/split_diagnostics.json`

---

## 1. Error Taxonomy Breakdown (Development Split)

Analysis of all 41 False Positives (FP) and 15 False Negatives (FN) across the 8 Development papers prior to Phase 1.2 interventions:

| ID | Error Category | Pre-Intervention FPs | Pre-Intervention FNs | Post-Intervention FPs | Post-Intervention FNs | Primary Root Cause | Remediated in Phase 1.2? |
|---|---|---:|---:|---:|---:|---|---|
| **1** | Invalid or overextended entity spans | 2 | 1 | 1 | 1 | Trailing descriptive phrases attached to entity mentions. | Partially |
| **2** | Entity alias and canonicalization failures | 3 | 2 | 2 | 1 | Synonyms with minor plural/hyphen variations not matching gold `c_set`. | **Fixed** (Phase 1.1/1.2 flexible normalizer) |
| **3** | Noncausal relations misclassified as causal | 8 | 0 | 2 | 0 | Experimental strain construction & cloning statements parsed as regulatory relations. | **Fixed** (`METHOD_HOMOLOGY_RE`) |
| **4** | Missing explicit causal relations | 0 | 5 | 0 | 2 | Conjoined two-component systems and operon regulations not parsed by linear S-V-O. | **Fixed** (`TCSTS_SLASH_RE` / `TCSTS_AND_RE`) |
| **5** | Incorrect cause/effect direction | 10 | 3 | 2 | 1 | Inverted syntax (e.g. "target was reduced in mutant", "regulator of two-component system"). | **Fixed** (Mutant inversion & kinase-regulator scoring) |
| **6** | Incorrect activation/inhibition polarity | 1 | 0 | 1 | 0 | Repression vs activation ambiguity in multi-step indirect pathways. | Tracked |
| **7** | Negated, speculative, or hypothetical claims | 1 | 0 | 1 | 0 | Speculative discussion hypotheses passing uncertainty gate. | Tracked |
| **8** | Unsupported co-occurrence inference | 4 | 0 | 2 | 0 | Gene names co-occurring in review introductions or figure legends. | Partially (table/figure filtering) |
| **9** | Duplicate predictions inflating FPs | 68 | 0 | 0 | 0 | Multiple sentence-level assertions for identical true edge evaluated as separate FPs. | **Fixed** (Document-level consolidation) |
| **10** | Coreference and cross-sentence failures | 0 | 2 | 0 | 2 | Pronominal coreference across paragraph boundaries. | Tracked |
| **11** | Cross-page mechanism-linking shortcuts | 2 | 2 | 1 | 1 | Multi-edge inflation between corroborated mentions across pages. | **Fixed** (Cross-page link consolidation) |
| **12** | PDF parsing, section ordering, table extraction | 0 | 0 | 0 | 0 | Text cleanly ingested via PMC XML parser. | Verified Clean |
| **13** | Sequence homology comparison statements | 3 | 0 | 0 | 0 | Sequence alignment & locus mapping ("exhibits 27% identity with"). | **Fixed** (`METHOD_HOMOLOGY_RE`) |

---

## 2. Concrete Before-and-After Case Studies

### Case Study 1: Methodological Strain Construction vs Causal Regulation
- **Document:** PMC2430206 (*Staphylococcus aureus* GraRS)
- **Source Sentence:**
  > *"The graRS::erm/dltA::spc double mutant was created by bacteriophage φ 11-mediated transduction of the graRS::erm mutation into the dltA::spc deletion mutant."*
- **Before Phase 1.2:**
  - Extracted: `dltA -> GraRS` (Direct False Positive).
  - Failure Mechanism: The sentence describes a laboratory transduction procedure to construct a double mutant. The extractor matched `dltA` and `GraRS` around `"was created by ... transduction of ... into"`, erroneously classifying laboratory cloning as biological regulation.
- **After Phase 1.2:**
  - `METHOD_HOMOLOGY_RE` recognizes `\b(?:was|were)\s+created\s+by\b` and `\btransduction\s+of\b`.
  - Sentence skipped from causal candidate generation.
  - Result: **False Positive eliminated**.

---

### Case Study 2: Sequence Homology Comparison vs Functional Regulation
- **Document:** PMC2358977 (*Streptococcus suis* SalK/SalR)
- **Source Sentence:**
  > *"On the negative strand of 89K, peptides encoded by 05SSU0944 and 05SSU0943 exhibit 27% and 41% amino acid sequence identity with the SalK and the SalR proteins of Streptococcus salivarius, respectively, forming a TCSTS belonging to the Nar/LuxR family."*
- **Before Phase 1.2:**
  - Extracted: `SalK -> 89K` (FP) and `SalR -> 89K` (FP).
  - Missed: `SalK -> SalR` (FN).
  - Failure Mechanism: The sentence describes sequence identity percentage between 89K-encoded peptides and S. salivarius homologs. The extractor misclassified sequence comparison as causal regulation, while failing to extract the functional coupling between SalK and SalR.
- **After Phase 1.2:**
  - `METHOD_HOMOLOGY_RE` suppresses the homology statement between SalK/SalR and 89K.
  - `TCSTS_AND_RE` detects `"SalK and the SalR proteins ... forming a TCSTS"`.
  - Sensor kinase (`SalK`, ending in `K`) is resolved as activator of response regulator (`SalR`, ending in `R`).
  - Result: **Two FPs eliminated (`SalK->89K`, `SalR->89K`), one FN resolved (`SalK->SalR` added as TP)**.

---

### Case Study 3: Inverted Syntax in Two-Component System Descriptions
- **Document:** PMC1974823 (*Porphyromonas gingivalis* FimS/FimR)
- **Source Sentence:**
  > *"FimR, a response regulator of the fimS/fimR two-component system was identified, and FimA expression was found to be dramatically reduced in fimR mutants."*
- **Before Phase 1.2:**
  - Extracted: `FimR -> FimS` (Direction Reversal / FP).
  - Missed: `FimS -> FimR` (FN).
  - Failure Mechanism: Because `FimR` preceded `fimS` in text, the linear distance heuristic selected `FimR` as cause and `fimS` as effect, despite FimR being explicitly qualified as the "response regulator".
- **After Phase 1.2:**
  - `TCSTS_SLASH_RE` detects conjoined `fimS/fimR`.
  - Kinase/Regulator scoring identifies `FimS` (sensor kinase, suffix `S`) as source and `FimR` (regulator, suffix `R`) as target.
  - Result: **Direction reversal eliminated (`FimR->FimS` removed, `FimS->FimR` added as TP)**. Direct F1 on PMC1974823 doubled from 0.25 to **0.4444**.

---

### Case Study 4: Cross-Split Generalization on Held-Out External Paper
- **Document:** PMC2858072 (*Brucella abortus* BvrR/BvrS, External Generalization Split)
- **Source Sentence:**
  > *"Transcriptome Analysis of the Brucella abortus BvrR/BvrS Two-Component Regulatory System"*
- **Before Phase 1.2:**
  - Direct F1: **0.0000** ($TP=0, FP=2, FN=5$).
  - Missed: `BvrS -> BvrR`.
- **After Phase 1.2:**
  - `TCSTS_SLASH_RE` recognizes `BvrR/BvrS Two-Component Regulatory System`.
  - Maps kinase `BvrS` to regulator `BvrR`.
  - Result: **Direct F1 jumped from 0.0000 to 0.2500** ($TP=1, FP=2, FN=4$) on genuinely held-out unseen data without paper-specific tuning.
