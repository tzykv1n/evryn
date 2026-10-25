# EVRYN Phase 1.13 Document and Deliverable Consistency Audit
**Project:** EVRYN — Temporal Causal Knowledge Graph Synthesis  
**Scope:** Factual, Numerical, and Methodological Reconciliation Across Monograph, Presentation, and Codebase  
**Date:** October 25, 2026  
**Auditor:** Scientific Integrity & Evaluation Audit  

---

## 1. Audit Overview

To ensure complete rigor and eliminate discrepancies between the comprehensive research monograph (`phase1_report/main.pdf`), the executive presentation (`Temporal_Causal_Knowledge_Phase1_Presentation.pdf`), the experiment manifests, and the underlying codebase, an exhaustive 7-point reconciliation audit was conducted.

---

## 2. Itemized Reconciliation Matrix

### Item 1: Phase 1 Acceptance and Milestone Status
- **Initial Discrepancy:** Presentation Slide 6 historically asserted that *"all three objectives are fully delivered and verified"*, whereas the Monograph Abstract and Section 5.7 explicitly classified Phase 1 as formally **In Progress** because held-out Cross-Page Macro-F1 ($0.2637$ on Locked Test, $0.3262$ on External V2) had not yet met the formal pre-registered acceptance criterion ($F_1^{\text{cross}} \ge 0.50$).
- **Reconciliation Action:** Synchronized Slide 6 and Slide 40 of the presentation. Slide 6 now accurately states:
  > *"Stage 1–5 extraction architecture, provenance grounding (100%), and UI workspace fully delivered; benchmark evaluation in progress with Cross-Page F1 progressing toward the 0.50 acceptance threshold."*
- **Audit Verdict:** **RECONCILED & CONSISTENT.**

---

### Item 2: Real-Paper Benchmark Split Composition
- **Initial Discrepancy:** Monograph Section 5.2 and Presentation Slide 22 listed duplicated PMCID strings across partitions (e.g. PMC2829055 appeared under Dev and External, while PMC2774163 appeared under Train and Dev).
- **Authoritative Source:** `data/real_papers/split_manifest.json` (20 full open-access biomedical PMC articles).
- **Reconciliation Action:** Updated Monograph Section 5.2 and Presentation Slide 22 to match the exact canonical disjoint partitions:
  - **Train (4 Papers):** PMC2651894, PMC2682197, PMC2714965, PMC2774163
  - **Development (8 Papers):** PMC1804205, PMC1874608, PMC1913099, PMC2148011, PMC2248602, PMC2276722, PMC2374880, PMC2430206
  - **Locked Test (4 Papers):** PMC2565068, PMC2581603, PMC2593050, PMC2639726
  - **External Validation (4 Papers):** PMC2816692, PMC2829055, PMC2858072, PMC2885601
- **Audit Verdict:** **RECONCILED & DISJOINT.**

---

### Item 3: Direct Relation Micro Counts (TP, FP, FN)
- **Initial Discrepancy:** Multiple drafts mixed Phase 1.6 baseline micro counts with Phase 1.10 and Phase 1.12 numbers.
- **Authoritative Benchmark Execution:** Direct macro and micro evaluation on canonical Benchmark V2 gold annotations.
- **Reconciled Numerical Table (Synchronized in Monograph Table 5.1 & Presentation Slide 24):**

| Benchmark Partition | Direct Macro F1 | 95% Bootstrap CI | Micro TP | Micro FP | Micro FN | Precision | Recall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train (4 papers)** | 0.4750 | [0.2449, 0.7051] | 12 | 20 | 7 | 0.3750 | 0.6316 |
| **Development (8 papers)** | **0.6551** | [0.5218, 0.7712] | 29 | 26 | 7 | 0.5273 | 0.8056 |
| **Locked Test (4 papers)** | **0.5654** | [0.3809, 0.7300] | 15 | 15 | 6 | 0.5000 | 0.7143 |
| **External V1 (4 papers)** | 0.2380 | [0.0811, 0.4074] | 7 | 54 | 13 | 0.1148 | 0.3500 |
| **External V2 (4 papers)** | **0.4808** | [0.2941, 0.6471] | 11 | 15 | 9 | 0.4231 | 0.5500 |

- **Audit Verdict:** **RECONCILED & 100% MATHEMATICALLY SYNCHRONIZED.**

---

### Item 4: Cross-Page Transitive Macro F1 and Confidence Intervals
- **Initial Discrepancy:** Older slide decks omitted bootstrap confidence intervals and reported single-paper approximations.
- **Reconciled Values (Synchronized in Monograph Table 5.2 & Presentation Slide 29):**
  - **Train:** $F_1 = 0.2120$, $95\%\;\text{CI} = [0.0000, 0.4239]$, $\text{TP} = 2$, $\text{FP} = 10$
  - **Development:** $F_1 = 0.4589$, $95\%\;\text{CI} = [0.2585, 0.6519]$, $\text{TP} = 9$, $\text{FP} = 12$
  - **Locked Test:** $F_1 = 0.2637$, $95\%\;\text{CI} = [0.0769, 0.4176]$, $\text{TP} = 4$, $\text{FP} = 11$
  - **External V2:** $F_1 = 0.3262$, $95\%\;\text{CI} = [0.2857, 0.3714]$, $\text{TP} = 5$, $\text{FP} = 7$
- **Audit Verdict:** **RECONCILED & CONSISTENT.**

---

### Item 5: Error Taxonomy & False Negative / False Positive Census
- **Initial Discrepancy:** Presentation Slide 33 cited obsolete preliminary error counts (48 False Negatives / 104 False Positives from Phase 1.6).
- **Authoritative Source:** Final Benchmark V2 error population analysis across the 20-paper corpus.
- **Reconciled Census (Synchronized in Monograph Section 5.5 & Presentation Slide 33):**
  - **Total Ground-Truth Errors:** $29$ False Negatives (FN) and $76$ False Positives (FP)
  - **False Negative Categorization:**
    - Complex coordinate clauses & passive inversions: $11$ ($37.9\%$)
    - Distant multi-paragraph transitive hops: $9$ ($31.0\%$)
    - Nominalized causal verbs in table footnotes / captions: $6$ ($20.7\%$)
    - Novel acronyms absent from biomedical gazetteer: $3$ ($10.4\%$)
  - **False Positive Categorization:**
    - Non-causal correlational / co-occurrence statements: $34$ ($44.7\%$)
    - Experimental conditions / assay reagent interactions: $23$ ($30.3\%$)
    - Subordinate condition / hypothetical clauses: $12$ ($15.8\%$)
    - Species homology mismatch: $7$ ($9.2\%$)
- **Audit Verdict:** **RECONCILED & CONSISTENT.**

---

### Item 6: Structural Graph Match and Provenance Grounding Rate
- **Initial Discrepancy:** Minor rounding differences in structural identity percentages between text and figures.
- **Reconciled Values (Synchronized in Monograph Section 5.4 & Presentation Slide 30):**
  - **Provenance Grounding Rate:** **100.0%** (every extracted causal assertion is traceable to verified character bounding boxes; zero hallucinated provenance coordinates).
  - **Exact Structural Subgraph Match:** **44.30%** (Dev) $\mid$ **30.19%** (Locked Test).
- **Audit Verdict:** **RECONCILED & CONSISTENT.**

---

### Item 7: Acceptance Thresholds and Forward Plan
- **Verification:** All deliverables consistently state that Phase 1 acceptance requires:
  1. Complete 5-stage NLP-to-Graph extraction pipeline with verified UI. (Satisfied)
  2. 100% character-level provenance grounding rate. (Satisfied)
  3. Real-paper benchmark cross-page macro $F_1 \ge 0.50$. (In progress: Dev reaches $0.4589$, Test at $0.2637$, Ext V2 at $0.3262$).
- **Audit Verdict:** **UNANIMOUS ACROSS ALL DOCUMENTS.**
