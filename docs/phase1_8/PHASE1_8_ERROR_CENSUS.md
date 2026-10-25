# EVRYN Phase 1.8 — Diagnostic Error Census & Transition Audit

**Date:** October 25, 2026  
**Repository:** `https://github.com/tzykv1n/evryn`  
**Branch:** `phase2.1-benchmark-audit-and-ui-fix`  

---

## 1. Overview and Executive Census Summary

Following the Phase 1.7 deployment, an exhaustive diagnostic census was performed across all 20 authentic PubMed Central papers in the benchmark (`results/phase1_8/census_v2.json` and `census_v1.json`). 

Phase 1.8 implemented targeted NLP grammar and canonicalization interventions that substantially reduced both false negatives and false positives.

### High-Level Census Comparison (V2 Ground Truth)

| Metric | Phase 1.7 Baseline | Phase 1.8 Post-Intervention | Reduction | Percentage Change |
| :--- | :---: | :---: | :---: | :---: |
| **Total False Negatives (FN)** | 46 | **39** | **-7 FNs** | **-15.2%** |
| **Total False Positives (FP)** | 104 | **85** | **-19 FPs** | **-18.3%** |
| **Total Error Burden (FN + FP)** | 150 | **124** | **-26 Errors** | **-17.3%** |

---

## 2. False Negative Taxonomy Transition

| Category | Phase 1.7 Baseline Count | Phase 1.8 Post Count | Delta $\Delta$ | Key Mechanism Resolved |
| :--- | :---: | :---: | :---: | :--- |
| `missed_causal_trigger` | 14 | **10** | **-4** | Recovered `Mfa1 -> Short Fimbriae` ("made up of"), `cheB1 -> Chemotaxis` ("defect in"), `cyclic-di-GMP -> Biofilm` ("and thus"), and `RseA -> sigmaE` ("anti-sigma factor") |
| `entity_alias_or_canonicalization_failure` | 17 | **15** | **-2** | Resolved `GraRS -> GraR` via exact-match priority pass preventing plural stripping collision with TCSTS operon names |
| `incorrect_direction` | 5 | **4** | **-1** | Resolved passive construct override (`HilD -> hilA`) and mutant enhanced inversion (`CsrS -| slo`) |
| `cross_sentence_discourse` | 9 | **9** | $\pm 0$ | Multi-paragraph experimental deductions spanning disparate sections without lexical bridges |
| `negation_speculation_refutation` | 1 | **1** | $\pm 0$ | Refuted claim correctly rejected by conservative negation parser |
| **Total FNs** | **46** | **39** | **-7** | |

---

## 3. False Positive Taxonomy Transition

| Category | Phase 1.7 Baseline Count | Phase 1.8 Post Count | Delta $\Delta$ | Key Mechanism Resolved |
| :--- | :---: | :---: | :---: | :--- |
| `over_generated_or_spurious_relation` | 67 | **51** | **-16** | Eliminated spurious genomic locus relations (`SPI1 -> HilA`), pruned weak non-causal co-occurrences |
| `incorrect_direction` | 20 | **20** | $\pm 0$ | Backward edges flipped to forward true positives |
| `unsupported_association` | 9 | **8** | **-1** | Filtered associational co-occurrences without transitive predicates |
| `environmental_confounder` | 4 | **4** | $\pm 0$ | Bounded environmental variable constraints preserved |
| `genetic_complementation_and_rescue` | 4 | **2** | **-2** | Suppressed artificial plasmid complementation artifacts |
| **Total FPs** | **104** | **85** | **-19** | |

---

## 4. Key Error Case Studies Resolved in Phase 1.8

### Case 1: Passive Override of Active Matrix Predicate
- **Sentence:** *"Additionally, the over-expression of HilD from the plasmid pJB3 containing hilD gene under the control of a lac promoter caused the induction of hilA expression"* (`PMC1874608`)
- **Pre-Phase 1.8 Failure:** Passive indicator `under the control of` matched before matrix verb `caused`, extracting `hilA -> HilD` (backward).
- **Post-Phase 1.8 Resolution:** Active matrix causative verb precedence (`ACTIVE_MATRIX_CAUSATIVE_VERBS`) ensures `caused the induction of` governs the clause, correctly yielding `HilD -> hilA`.

### Case 2: Genetics Mutant Phenotype Inversion
- **Sentence:** *"slo expression was enhanced in the csrS mutant"* (`PMC2565068`)
- **Pre-Phase 1.8 Failure:** `enhanced` matched forward activation, extracting `slo -> csrS` (inverting both cause/effect and polarity).
- **Post-Phase 1.8 Resolution:** Expanded `COMPILED_GENETICS_MUTANT_UP` recognizes that elevated expression in a mutant implies negative regulation by the wild-type regulator, correctly yielding `CsrS -| slo`.

### Case 3: Structural Subunit Composition
- **Sentence:** *"The short (minor) fimbriae are made up of a 67 kDa protein (Mfa1)."* (`PMC1974823`)
- **Pre-Phase 1.8 Failure:** `made up of` was unmapped in passive syntactic indicators, dropping the structural subunit definition.
- **Post-Phase 1.8 Resolution:** Composition indicator `\b(?:made\s+up\s+of|composed\s+of|consists?\s+of)\b` maps subunit $Mfa1 \to \text{Short Fimbriae}$, lifting PMC1974823 F1 from 0.444 to **0.600**.

### Case 4: Operon vs. Response Regulator Canonicalization Collision
- **Sentence:** *"The graRS regulatory genes have recently been implicated in the control of D-alanylation..."* (`PMC2430206`)
- **Pre-Phase 1.8 Failure:** Plural stripping heuristic `rstrip("s")` stripped terminal `s` from `GraRS` and incorrectly collapsed `GraR` into `GraRS`.
- **Post-Phase 1.8 Resolution:** Exact-match priority pass prevents TCSTS operons ending in `rs` from colliding with response regulators ending in `r`, enabling TCSTS operon coupling (`GraRS -> GraR`) and lifting PMC2430206 F1 from 0.667 to **0.800**.

### Case 5: Pathogenicity Island Genomic Locus Confounder
- **Sentence:** *"Although many factors and a complex mechanism related to environmental stimuli are involved in the modulation of SPI1 genes, they are thought to converge on the activation of several transcriptional regulators encoded within SPI1, such as HilA..."* (`PMC1874608`)
- **Pre-Phase 1.8 Failure:** `encoded within` treated genomic locus `SPI1` as a causal upstream regulator of `HilA`, creating false positive `SPI1 -> HilA`.
- **Post-Phase 1.8 Resolution:** `ENCODED_WITHIN_LOCUS_RE` rejects genomic locus / island / operon encoding phrases as causal interaction edges, reducing PMC1874608 false positives from 14 to **13**.

---

## 5. Remaining Error Frontier

The remaining 39 false negatives across the 20-paper corpus fall into two primary categories:
1. **Distant Multi-Paragraph Scientific Inferences (9 cases, 23.1%):** Global deductions synthesized across separate Results subsections without local lexical triggers (e.g. `dltA -> LL-37` in PMC2430206 where the mechanism is established across 4 pages of assay results).
2. **Complex Entity Nominalizations & Compound Abbreviations (15 cases, 38.5%):** Non-standard multi-word biological entities requiring semantic ontology linking (e.g. `PMN Infiltration -> Host Survival`).
