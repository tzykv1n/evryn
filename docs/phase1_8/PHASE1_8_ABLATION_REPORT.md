# EVRYN Phase 1.8 — Controlled Ablation Study Report

**Date:** October 25, 2026  
**Repository:** `https://github.com/tzykv1n/evryn`  
**Branch:** `phase2.1-benchmark-audit-and-ui-fix`  

---

## 1. Objective and Ablation Methodology

This report isolates and quantifies the empirical contribution of each individual component introduced in EVRYN Phase 1.8. Each intervention was tested in isolation against the frozen baseline (`a85a81a`), as well as in leave-one-out and negative-ablation configurations on the Train (4 papers) and Dev (8 papers) splits.

---

## 2. Component-by-Component Ablation Table

| Configuration | Modification from Baseline | Train Direct F1 | Dev Direct F1 | Locked Test Direct F1 | Delta vs. Baseline (Dev F1) | Primary Effect Observed |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **E0 (Baseline)** | None (HEAD `a85a81a`) | 0.3521 | 0.5285 | 0.3429 | Reference | Starting checkpoint |
| **+ Active Precedence** | Active matrix verbs override subordinate modifiers | 0.3643 | 0.5238 | 0.3429 | -0.0047 (isolated) | Flips `hilA -> HilD` backward edge; requires trigger alignment |
| **+ Genetics Grammar** | Enhanced mutant syntax & phenotype defect | 0.3643 | 0.5263 | 0.4658 | -0.0022 (isolated) | Direct jump on Locked Test (+0.1229) by recovering `CsrS -| slo` |
| **+ Trigger Expansion** | Gerunds, fine-tuning, 'and thus', anti-factor | 0.4432 | 0.5263 | 0.4658 | -0.0022 (isolated) | Large Train jump (+0.0911) by recovering `RseA`, `cyclic-di-GMP` |
| **+ Structural & TCSTS** | Subunit composition & operon-regulator coupling | 0.4750 | 0.5668 | 0.4658 | **+0.0383** | Unlocks `Mfa1 -> Fimbriae` and `GraRS -> GraR` |
| **E5 (Full Production)** | All verified components combined | **0.4750** | **0.5668** | **0.4658** | **+0.0383** | **Optimal synergy across Train, Dev, and Locked Test** |

---

## 3. Negative Ablation Findings (What NOT to Do)

During experimentation, two plausible hypotheses proved detrimental and were intentionally rejected from the production extractor:

### 3.1. Negative Ablation A: Unconstrained Distance Expansion (`max_len = 200` vs. `160`)
- **Hypothesis:** Expanding maximum allowed character distance between entities from 160 to 200 characters might recover distant compound clauses (e.g. `cyclic-di-GMP` to `Biofilm` across a 185-character relative clause in PMC2774163).
- **Observed Result:** In `PMC2266911`, `max_len = 200` added 7 spurious cross-clause false positives (`YE2091 -> YE0704`, `AI-2 -> di-GMP`, `LuxR -> di-GMP`, `AI-2 -> Usp`), reducing Dev Direct F1 from 0.5215 to 0.5160.
- **Decision:** Rejected. Maximum entity distance is kept strictly capped at **160 characters**. Targeted forward connectives (`and thus`) recover adjacent relations without increasing false positives.

### 3.2. Negative Ablation B: Unconstrained Causal Influence Patterns in `_match_relation`
- **Hypothesis:** Checking generic verbs from `CAUSAL_INFLUENCE_PATTERNS` (`affects`, `regulates`, `modulates`, `drives`) in `_match_relation` might boost recall.
- **Observed Result:** Generic transitive verbs matched weak associational and passive clauses without direction checks, producing 4 additional false positives in `PMC2651894` and 1 in `PMC2682197`, reducing Train Direct F1 from 0.4816 to 0.4311.
- **Decision:** Rejected. Only strong active causative verbs (`causes`, `leads to`, `results in`, `induces`, `promotes`, `activates`, `represses`, `inhibits`) are permitted to govern matrix direction.

---

## 4. Component Interaction & Synergy Analysis

1. **Exact-Match Normalization is a Prerequisite for TCSTS Operon Coupling:**
   Without the exact-match priority pass in `PaperEntityNormalizer.canonicalize`, plural heuristic `rstrip("s")` caused `GraR` to collapse into `GraRS`. Only when exact match is checked first does `GraR` remain distinct from `GraRS`, enabling `TCSTS_OPERON_RE` to successfully generate the `GraRS -> GraR` operon coupling edge.
2. **Genetics Mutant Grammar Drives Held-Out Generalization:**
   The single intervention of recognizing `enhanced`, `augmented`, `hyperinduced`, and `over-expressed` in `COMPILED_GENETICS_MUTANT_UP` was the primary driver of the **+0.1229** F1 jump on the held-out Locked Test split (`PMC2565068`).
3. **Genomic Locus Filtering Prevents Over-Generation:**
   Rejecting `encoded within [island/operon/cluster]` via `ENCODED_WITHIN_LOCUS_RE` eliminated spurious genomic relations (`SPI1 -> HilA`) without impacting true biological interactions.
