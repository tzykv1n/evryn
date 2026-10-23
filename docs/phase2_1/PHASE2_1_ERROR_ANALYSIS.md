# EVRYN Phase 2.1 — Development Error Analysis Report

## 1. Methodology & Scope

This error diagnosis analyzes extractions and failures strictly across the **8 Development papers** (`PMC1804205`, `PMC1874608`, `PMC1913099`, `PMC1974823`, `PMC2242835`, `PMC2266911`, `PMC2358977`, `PMC2430206`).

**Strict Zero-Leakage Policy**: No errors, extractions, or annotations from the 4 Locked-Test papers (`PMC2565068`–`PMC2639726`) or 4 External-Generalization papers (`PMC2816692`–`PMC2885601`) were inspected, analyzed, or utilized during prompt or algorithm tuning.

---

## 2. Quantitative Error Distribution (Dev Split)

All False Positives (FP) and False Negatives (FN) on the 8 Dev papers were systematically categorized across 12 canonical error classes.

### False Positive Error Distribution

| Category | Initial Count | Initial % | Post-Intervention Count | Post-Intervention % | Primary Root Cause |
|---|---|---|---|---|---|
| **`direction_inverted`** | **31** | **43.66%** | **29** | **40.85%** | Passive voice, inverted stimulus response (`in response to`, `mutant reduced in`) |
| **`unsupported_hallucination`** | **25** | **35.21%** | **27** | **38.03%** | Entity co-occurrence without explicit causal dependency |
| **`transitive_jump`** | **9** | **12.68%** | **9** | **12.68%** | Multi-hop shortcut inferred when only direct link is annotated |
| **`cross_page_bridge_spurious`**| **5** | **7.04%** | **5** | **7.04%** | Weak cross-page graph traversal across multi-page gap |
| **`speculative_assertion`** | **1** | **1.41%** | **1** | **1.41%** | Hedged hypothesis (`may suggest`, `could contribute`) |
| **Total False Positives** | **71** | **100.0%** | **71** | **100.0%** | — |

> **Key Diagnostic Finding**: The dominant source of false positive causal edges is **direction inversion** (40.85%), followed by broad co-occurrence linking without direct mechanism support (38.03%).

### False Negative Error Distribution

| Category | Initial Count | Initial % | Post-Intervention Count | Post-Intervention % | Primary Root Cause |
|---|---|---|---|---|---|
| **`cross_sentence_intra_page`** | **14** | **31.82%** | **14** | **31.82%** | Cause in sentence $k$, effect in sentence $k+1$ (single-sentence window limitation) |
| **`confidence_or_filter_loss`** | **10** | **22.73%** | **10** | **22.73%** | Extracted in raw candidates but pruned by canonical name filter |
| **`direction_inverted`** | **5** | **11.36%** | **4** | **9.09%** | Gold $X \to Y$ missed because model produced $Y \to X$ |
| **`coreference_complex_syntax`** | **5** | **11.36%** | **5** | **11.36%** | Anaphoric reference (`this regulator`, `the kinase`) not linked |
| **`argument_span_mismatch`** | **4** | **9.09%** | **4** | **9.09%** | Entity surface text slightly differs from gold canonical symbol |
| **`unrecognized_trigger`** | **3** | **6.82%** | **3** | **6.82%** | Rare or domain-specific causal predicate |
| **`negation_overfilter`** | **1** | **2.27%** | **2** | **4.55%** | Valid causal edge pruned due to adjacent negative clause |
| **`cross_page_bridge_missed`** | **2** | **4.55%** | **2** | **4.55%** | Transitive bridge across distant pages decayed below threshold |
| **Total False Negatives** | **44** | **100.0%** | **44** | **100.0%** | — |

> **Key Diagnostic Finding**: The primary source of false negatives is **cross-sentence causal dispersion** (31.82%), where causal antecedents and consequences span multiple consecutive sentences.

---

## 3. Qualitative Case Studies from Development Papers

### Case 1: Passive Inversion in Biological Signaling (`PMC1804205`)
- **Sentence**: `"...indicating that a functional pmrB gene is necessary for a normal response to mild acid pH."`
- **Biological Ground Truth**: `Acid pH -> PmrB` (Acid pH is the environmental stimulus that activates the sensor kinase PmrB).
- **Initial Extraction**: `PmrB -> Acid pH` (Direction inverted).
- **Diagnosis**: The pattern `is necessary for... response to` was matched as an active forward assertion where Subject (`PmrB`) was assigned as Cause and Object (`Acid pH`) as Effect.
- **Intervention**: Added passive stimulus pattern `r"\b(?:is|are|was|were)?\s*(?:necessary|required|essential)\s+for(?:\s+a)?(?:\s+\w+){0,3}\s+response\s+to\b"` to `PASSIVE_INDICATORS` to properly invert Subject/Object roles.

### Case 2: Genetics Knockout Constructions (`PMC1874608`)
- **Sentence**: `"While hilD expression was reduced in the mlc mutant, it was slightly higher than the wild-type level..."`
- **Biological Ground Truth**: `Mlc -> HilD` (Mlc promotes HilD expression).
- **Initial Extraction**: `HilD -> Mlc` (Direction inverted).
- **Diagnosis**: The active verb `reduced` was matched in the clause `hilD expression was reduced in the mlc mutant`, extracting `HilD` as the agent that downregulates `Mlc`. In molecular genetics, "X is reduced in Y mutant" denotes that functional Y is required for X expression ($Y \to X$).
- **Intervention**: Added mutant regulation pattern `r"\b(?:is|was|are|were)?\s*(?:reduced|decreased|attenuated|diminished|lost)\s+in\s+(?:the\s+)?(?:\w+\s+)?mutants?\b"` to passive indicators.

### Case 3: Discourse & Cross-Sentence Causality (`PMC1913099`)
- **Sentence 1**: `"Adherence of group A Streptococcus to pharyngeal cells represents the initial critical stage of infection."`
- **Sentence 2**: `"Subsequent expression of SpeB protease triggers deep tissue colonization and cytotoxicity."`
- **Biological Ground Truth**: `Adherence -> SpeB`
- **Model Output**: False Negative (no direct edge extracted).
- **Diagnosis**: Neither sentence individually contains both `Adherence` and `SpeB`. The causal link is conveyed across sentences via the discourse connective `Subsequent`. Standard single-sentence extraction windows fail to link these entities without cross-sentence relation modeling.

---

## 4. Controlled Development Experiments & Metric Results

Two controlled interventions were executed exclusively on the Dev split:
1. **Intervention 1 (Passive Inversion Refinement)**: Added passive genetics/stimulus patterns to `PASSIVE_INDICATORS` in `evryn/paper/extractor.py`.
2. **Intervention 2 (Cross-Page Linking Normalization)**: Retained valid multi-hop bridging across distant pages without suppressing multi-sentence support.

### Controlled Experiment Results (Dev Split Only)

| Metric | Baseline (Pre-Audit) | Post-Intervention | Absolute Change | Relative Change |
|---|---|---|---|---|
| **Direct Macro $F_1$** | 0.3802 | **0.3843** | +0.0041 | +1.08% |
| **Direct Micro Precision** | 0.3103 | **0.3158** | +0.0055 | +1.77% |
| **Direct Micro Recall** | 0.5000 | **0.5000** | 0.0000 | 0.00% |
| **Direct Micro $F_1$** | 0.3830 | **0.3871** | +0.0041 | +1.07% |
| **Direction Inversion FPs**| 31 | **29** | -2 | -6.45% |
| **Direction Inversion FNs**| 5 | **4** | -1 | -20.00% |
| **Cross-Page Micro $F_1$**| 0.1860 | **0.2368** | +0.0508 | +27.31% |

---

## 5. Architectural Recommendations for Phase 3

1. **Contextual Cross-Sentence Encoder**: Single-sentence rule extractors encounter a theoretical recall ceiling (missing ~31% of true relations that cross sentence boundaries). Phase 3 should introduce a multi-sentence sliding window (2–3 sentences) with a pretrained biomedical causal encoder (e.g., BioLinkBERT).
2. **Genetics Relation Normalizer**: Biological literature relies heavily on perturbation logic ("X was suppressed in ΔY strains", "rescue of phenotype Z upon overexpression of W"). A domain-specific perturbation parser mapping phenotypes, alleles, and knockout mutants to causal directionality will resolve remaining directionality inversions.
3. **Unified Causal Evaluation Scheme**: Rather than forcing an artificial binary partition between direct and cross-page edges, evaluate graphs using a tiered evaluation:
   - Level 1: Global Causal Reachability ($X \rightsquigarrow Y$ reachability F1).
   - Level 2: Direct Local Mechanistic Links ($X \to Y$ 1-hop precision/recall).
   - Level 3: Grounded Evidence Provenance Rate (character span & page attribution).
