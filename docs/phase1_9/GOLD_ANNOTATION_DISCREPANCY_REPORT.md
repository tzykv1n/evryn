# EVRYN Phase 1.9 — Gold Annotation Discrepancy Report

**Date:** 2026-10-25  
**Investigator:** Antigravity (Advanced Agentic Pair Programmer)  
**Target Paper:** PMC1804205 (*Acid pH activation of the PmrA/PmrB two-component regulatory system of Salmonella enterica*)  
**Status:** Documented with full textual evidence; evaluated under both unadjusted and adjusted gold standards.

---

## 1. Executive Summary

During the systematic prediction-level error census of EVRYN Phase 1.9, an edge directionality discrepancy was identified in the curated ground truth annotation for **PMC1804205**.

- **Curated Ground Truth Direct Edge:** `("PmrA", "PmrD")` (interpreting PmrA as the upstream cause of PmrD).
- **Textual Evidence and Biological Ground Truth:** The paper repeatedly and unequivocally establishes that **PmrD is an upstream activator of PmrA** ($PmrD \to PmrA$), protecting phosphorylated PmrA from dephosphorylation. PmrA does not regulate or activate PmrD in this study.
- **Evaluation Penalty:** EVRYN correctly extracts `PmrD -> PmrA` directly from the paper's findings. However, against the unadjusted reference annotation, EVRYN is penalized twice:
  1. Once as a **False Negative** (`PmrA -> PmrD` marked undetected).
  2. Once as a **False Positive** (`PmrD -> PmrA` marked spurious).

In accordance with strict benchmark isolation and annotation integrity policies, **the ground truth JSON file has not been modified**. Instead, this report documents the exhaustive textual provenance, provides an adjusted metric comparison, and preserves both scores for complete scientific transparency.

---

## 2. Textual Evidence from PMC1804205

Every mention of the interaction between PmrA and PmrD in PMC1804205 demonstrates that PmrD activates PmrA:

### Citation 1 — Abstract / Summary (`sec_1_s5`)
> *"Here we report that this activation requires both PmrA's cognate sensor kinase PmrB, which had been previously shown to respond to Fe3+ and Al3+, and **PmrA's post-translational activator PmrD**."*
- **Role:** Explicitly designates PmrD as the "activator" of the "PmrA protein".

### Citation 2 — Introduction (`sec_2_s18`)
> *"**PmrD binds to the phosphorylated form of PmrA protecting it from dephosphorylation by PmrB** (Kato and Groisman, 2004)."*
- **Role:** Direct biochemical mechanism: PmrD binds to phosphorylated PmrA and stabilizes its active state.

### Citation 3 — Results Section (`sec_5_s1`)
> *"The **PhoP-activated PmrD protein favours the phosphorylated state of the PmrA protein** (Fig. 1)."*
- **Role:** Upstream transcriptional regulator PhoP induces PmrD, which then maintains PmrA in its activated state ($PhoP \to PmrD \to PmrA$).

### Citation 4 — Discussion (`sec_8_s29`)
> *"The PmrB protein plays the primary role in the pH-dependent activation of PmrA, but **full activation also requires PmrD, the post-translational activator of the PmrA protein** (Fig. 1)."*
- **Role:** Re-affirms that PmrD is required for the full activation of PmrA.

### Citation 5 — Discussion (`sec_8_s32`)
> *"Thus, **PmrD may be necessary to ensure that the amount of phosphorylated PmrA is such to promote transcription of its regulated genes**."*
- **Role:** Demonstrates PmrD's upstream regulatory control over PmrA's transcriptional output.

There is zero textual evidence in PMC1804205 suggesting that PmrA regulates, activates, or transcribes PmrD.

---

## 3. Quantitative Impact on Development Metrics

When evaluated on the 8 Development papers:

| Metric | Unadjusted Gold Standard | Adjusted Gold Standard (`PmrD -> PmrA`) | Difference |
|---|---|---|---|
| **PMC1804205 Direct TP** | 4 / 5 | **5 / 5 (100.0% Recall)** | +1 TP |
| **PMC1804205 Direct FP** | 5 | **4** | -1 FP |
| **PMC1804205 Direct Precision** | 0.4444 | **0.5556** | +0.1112 |
| **PMC1804205 Direct Recall** | 0.8000 | **1.0000** | +0.2000 |
| **PMC1804205 Direct F1** | 0.5714 | **0.7143** | **+0.1429** |
| **Dev Split Direct Macro-F1** | 0.6137 | **0.6316** | **+0.0179 (+1.79 points)** |
| **Dev Total Direct TPs** | 27 | **28** | +1 TP |
| **Dev Total Direct FPs** | 29 | **28** | -1 FP |

---

## 4. Policy and Recommendation

1. **Official Score Reporting:** EVRYN continues to report the conservative **0.6137** Dev Macro-F1 against the unadjusted benchmark to maintain exact comparability with historical runs.
2. **Provenance Documentation:** All evaluation tables cite this report to clarify that EVRYN's extracted edge `PmrD -> PmrA` is fully supported by the paper's primary evidence.
3. **Future Benchmark Versions:** Any future revision of the curated benchmark ground truth (e.g., Version 3) should adopt `["PmrD", "PmrA"]` to reflect primary biological ground truth.
