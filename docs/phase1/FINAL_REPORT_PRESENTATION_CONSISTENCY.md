# EVRYN: Final Report and Presentation Consistency Matrix

**Audit Date:** 2026-10-24  
**Deliverables Audited:**
- **Research Report:** `docs/phase1/main.pdf` (from `phase1_report/main.tex`)
- **40-Slide Presentation:** `docs/phase1/Temporal_Causal_Knowledge_Phase1_Presentation.pdf` (from `phase1_presentation/Temporal_Causal_Knowledge_Phase1_Presentation.tex`)
- **Machine-Readable Baseline:** `docs/phase1/FINAL_BENCHMARK_COMPARISON.csv`

---

## 1. Cross-Deliverable Numerical Concordance Table

This table maps every material quantitative claim made in EVRYN Phase 1, its authoritative data source, and its exact location in both the Research Report and the 40-Slide Presentation.

| Empirical Metric / Finding | Authoritative Source | Report Location | Presentation Location | Consistency Verification |
| :--- | :--- | :--- | :--- | :---: |
| **Total Benchmark Papers (20)** | `data/real_papers/split_manifest.json` | Abstract (p. 4); Chap 5.2 (p. 23); Table 5.1 (p. 24) | Slide 21 (Title), Slide 22 (Breakdown) | **CONCORDANT (20)** |
| **Split Breakdown (4/8/4/4)** | `data/real_papers/split_manifest.json` | Chap 5.2 (p. 23); Table 5.1 (p. 24); Fig 5.1 | Slide 22 (Breakdown), Slide 24 (Fig 5.1) | **CONCORDANT (4/8/4/4)** |
| **Train Direct F1: 0.3521** | `phase1_6_benchmark_v2.json` (line 15) | Table 5.1 (p. 24); Fig 5.2 (p. 25) | Slide 26 (Fig 5.2), Slide 28 (Table) | **CONCORDANT (0.3521)** |
| **Train 95% CI: [0.2549, 0.4583]** | `phase1_6_benchmark_v2.json` (line 17) | Table 5.1 (p. 24) | Slide 28 (Table) | **CONCORDANT ([0.255, 0.458])** |
| **Train Cross F1: 0.0833** | `phase1_6_benchmark_v2.json` (line 19) | Table 5.1 (p. 24); Fig 5.2 (p. 25) | Slide 26 (Fig 5.2), Slide 29 (Table) | **CONCORDANT (0.0833)** |
| **Train Struct Match: 0.1543** | `phase1_6_benchmark_v2.json` (line 21) | Table 5.1 (p. 24); Fig 5.2 (p. 25) | Slide 26 (Fig 5.2), Slide 30 (Table) | **CONCORDANT (0.1543)** |
| **Train Micro: 8 TP / 19 FP / 11 FN**| `phase1_6_benchmark_v2.json` (line 26) | Table 5.1 (p. 24) | Slide 28 (P=0.2963, R=0.4211) | **CONCORDANT (8/19/11)** |
| **Dev Direct F1: 0.5076** | `phase1_6_benchmark_v2.json` (line 153) | Abstract (p. 4); Table 5.1 (p. 24); Fig 5.2 | Slide 26 (Fig 5.2), Slide 28 (Table) | **CONCORDANT (0.5076)** |
| **Dev 95% CI: [0.4625, 0.5584]** | `phase1_6_benchmark_v2.json` (line 155) | Table 5.1 (p. 24) | Slide 28 (Table) | **CONCORDANT ([0.463, 0.558])** |
| **Dev Cross F1: 0.3864** | `phase1_6_benchmark_v2.json` (line 157) | Table 5.1 (p. 24); Fig 5.2 (p. 25); Chap 5.7 | Slide 26 (Fig 5.2), Slide 29 (Table), Slide 39 | **CONCORDANT (0.3864)** |
| **Dev Struct Match: 0.3162** | `phase1_6_benchmark_v2.json` (line 159) | Table 5.1 (p. 24); Fig 5.2 (p. 25) | Slide 26 (Fig 5.2), Slide 30 (Table) | **CONCORDANT (0.3162)** |
| **Dev Micro: 23 TP / 34 FP / 13 FN**| `phase1_6_benchmark_v2.json` (line 164) | Table 5.1 (p. 24) | Slide 28 (P=0.4035, R=0.6389) | **CONCORDANT (23/34/13)** |
| **Locked Test Direct F1: 0.3429** | `phase1_6_benchmark_v2.json` (line 363) | Table 5.1 (p. 24); Fig 5.2 (p. 25) | Slide 26 (Fig 5.2), Slide 28 (Table) | **CONCORDANT (0.3429)** |
| **Locked 95% CI: [0.1537, 0.5625]**| `phase1_6_benchmark_v2.json` (line 365) | Table 5.1 (p. 24) | Slide 28 (Table) | **CONCORDANT ([0.154, 0.563])** |
| **Locked Test Cross F1: 0.2002** | `phase1_6_benchmark_v2.json` (line 367) | Table 5.1 (p. 24); Fig 5.2 (p. 25) | Slide 26 (Fig 5.2), Slide 29 (Table) | **CONCORDANT (0.2002)** |
| **Locked Struct Match: 0.1733** | `phase1_6_benchmark_v2.json` (line 369) | Table 5.1 (p. 24); Fig 5.2 (p. 25) | Slide 26 (Fig 5.2), Slide 30 (Table) | **CONCORDANT (0.1733)** |
| **Locked Micro: 11 TP / 35 FP / 10 FN**| `phase1_6_benchmark_v2.json` (line 374)| Table 5.1 (p. 24) | Slide 28 (P=0.2391, R=0.5238) | **CONCORDANT (11/35/10)** |
| **External V1 Direct F1: 0.2380** | `phase1_6_benchmark_v1.json` (line 492) | Table 5.1 (p. 24); Fig 5.2 (p. 25); Chap 5.4.1| Slide 23 (Text), Slide 26 (Fig), Slide 28 | **CONCORDANT (0.2380)** |
| **External V1 Micro: 5 TP / 55 FP / 15 FN**| `phase1_6_benchmark_v1.json` (line 503)| Table 5.1 (p. 24); Chap 5.4.1 (p. 25) | Slide 28 (P=0.0833, R=0.2500) | **CONCORDANT (5/55/15)** |
| **External V2 Direct F1: 0.3289** | `phase1_6_benchmark_v2.json` (line 492) | Abstract (p. 4); Table 5.1; Fig 5.2; Chap 5.4.1| Slide 23 (Text), Slide 26 (Fig), Slide 28 | **CONCORDANT (0.3289)** |
| **External V2 95% CI: [0.2409, 0.4103]**| `phase1_6_benchmark_v2.json` (line 494)| Table 5.1 (p. 24) | Slide 28 (Table) | **CONCORDANT ([0.241, 0.410])** |
| **External V2 Cross F1: 0.2667** | `phase1_6_benchmark_v2.json` (line 496) | Table 5.1 (p. 24); Fig 5.2 (p. 25); Chap 5.4.1| Slide 26 (Fig 5.2), Slide 29 (Table) | **CONCORDANT (0.2667)** |
| **External V2 Struct Match: 0.1819**| `phase1_6_benchmark_v2.json` (line 498)| Table 5.1 (p. 24); Fig 5.2 (p. 25) | Slide 26 (Fig 5.2), Slide 30 (Table) | **CONCORDANT (0.1819)** |
| **External V2 Micro: 7 TP / 16 FP / 13 FN**| `phase1_6_benchmark_v2.json` (line 503)| Table 5.1 (p. 24) | Slide 28 (P=0.3043, R=0.3500) | **CONCORDANT (7/16/13)** |
| **Total Audited False Negatives (48)**| `error_inventory_v2.json`; Chap 5.5 | Abstract (p. 4); Chap 5.5 (p. 26); Fig 5.3 | Slide 28 (Fig 5.3), Slide 33 (Text) | **CONCORDANT (48 FNs)** |
| **Discourse-Level FNs: 28 (58.3%)**| `error_inventory_v2.json`; Fig 5.3 | Abstract (p. 4); Chap 5.5.1 (p. 26); Fig 5.3| Slide 28 (Fig 5.3), Slide 33 (Text) | **CONCORDANT (28 FNs)** |
| **Relation Triggering FNs: 20 (41.7%)**| `error_inventory_v2.json`; Fig 5.3 | Chap 5.5.1 (p. 26); Fig 5.3 | Slide 28 (Fig 5.3), Slide 33 (Text) | **CONCORDANT (20 FNs)** |
| **Pre-Intervention Baseline FPs (106)**| `POST_PHASE1_5_ERROR_INVENTORY.md` (l. 15)| Chap 5.5 (p. 26) | Slide 33 (Text) | **CONCORDANT (106 FPs)** |
| **Post-Intervention Verified FPs (104)**| `split_diagnostics.json`; Fig 5.3 | Chap 5.5.2 (p. 26); Fig 5.3 | Slide 28 (Fig 5.3), Slide 33 (Text) | **CONCORDANT (104 FPs)** |
| **PMC2816692 V1 Mismatch (43 FP, F1=0)**| `phase1_6_benchmark_v1.json` (l. 531) | Chap 5.4.1 (p. 25) | Slide 23 (Text) | **CONCORDANT (V1 Mismatch)** |
| **PMC2816692 V2 Recovery (F1=0.3636)**| `phase1_6_benchmark_v2.json` (l. 531) | Chap 5.4.1 (p. 25) | Slide 23 (Text) | **CONCORDANT (V2 Recovery)** |
| **Continual SCM Accuracy: 75.00%** | `run_continual_flux.py`; Fig 5.4 | Abstract (p. 4); Chap 5.6 (p. 27); Fig 5.4 | Excluded from Literature NLP; Slide 40 | **CONCORDANT (Scope Separated)**|
| **Continual Forgetting: 0.00% BWT**| `run_continual_flux.py`; Fig 5.4 | Abstract (p. 4); Chap 5.6 (p. 27); Fig 5.4 | Excluded from Literature NLP; Slide 40 | **CONCORDANT (Scope Separated)**|
| **Higher-Order HO-FLUX F1: 0.633** | `run_higher_order_benchmark.py`; Fig 5.4| Abstract (p. 4); Chap 5.6 (p. 27); Fig 5.4 | Excluded from Literature NLP | **CONCORDANT (Scope Separated)**|
| **Order-3 Recovery Rate: 85.0%** | `run_higher_order_benchmark.py`; Fig 5.4| Abstract (p. 4); Chap 5.6 (p. 27); Fig 5.4 | Excluded from Literature NLP | **CONCORDANT (Scope Separated)**|
| **Reliability Tests Passed (19/19)**| `tests/test_paper_reliability.py` | Chap 4.8 (p. 22); Chap 5.7 (p. 28) | Slide 37 (Reliability) | **CONCORDANT (19/19)** |
| **Unit Test Suite Passed (203+)** | Project pytest test suites | Chap 5.7 (p. 28); Table 5.2 | Slide 26 (Suite) | **CONCORDANT (203+)** |

---

## 2. Granular Section-by-Section Verification

### 2.1 Report Chapter 5 vs. Presentation Slides 26--30
1. **Table 5.1 vs. Slide 28 (Direct Extraction):**
   - Both report Table 5.1 and Presentation Slide 28 present identical Macro $F_1$ means: Train (0.3521), Dev (0.5076), Locked Test (0.3429), External V1 (0.2380), External V2 (0.3289).
   - Presentation Slide 28 displays micro precision and micro recall alongside Macro $F_1$, explicitly clarifying the aggregation type.
2. **Table 5.1 vs. Slide 29 (Cross-Page Extraction):**
   - Both report Table 5.1 and Presentation Slide 29 present identical Cross-Page $F_1$ means: Train (0.0833), Dev (0.3864), Locked Test (0.2002), External V1 (0.1667), External V2 (0.2667).
3. **Table 5.1 vs. Slide 30 (Structural Matching & Provenance):**
   - Exact Structural Match is identical across both documents: Train (0.1543), Dev (0.3162), Locked Test (0.1733), External V2 (0.1819).
   - Provenance Grounding Rate is 100.0% across all splits in both deliverables.
4. **Error Analysis (Report Chap 5.5 vs. Presentation Slide 33):**
   - Both deliverables report exactly 48 False Negatives: 28 Discourse-Level Claims (58.3%) and 20 Relation Triggering Gaps (41.7%).
   - Both deliverables explain that False Positives were reduced from 106 (pre-intervention baseline) to 104 (post-intervention release).

### 2.2 Scope Integrity Verification
- Synthetic SCM metrics (75.00% continual accuracy, 0.00% backward forgetting) and multivariate interaction metrics (0.633 F1, 85.0% order-3 recovery) are explicitly segregated under Section 5.6 of the report and are omitted from all literature extraction tables in both documents.
- In the presentation, Slide 40 references continual SCM adaptation strictly as a second-semester forward-looking research milestone.

---

## 3. Conclusion

Every material quantitative assertion in the EVRYN Phase 1 deliverables is fully reconciled, cross-referenced, and verified against reproducible machine artifacts. Zero contradictions exist between the research report and the presentation deck.
