# EVRYN Phase 1.6: Intervention Hypothesis

**Date:** 2026-10-24  
**Author:** EVRYN Lead Research & Engineering Team  
**Focus:** Biological Causality Direction Asymmetry & Microbiological Morphological Normalization.

---

## 1. Observed Failure Mechanisms

Following the post-Phase-1.5 error inventory across all 20 benchmark papers (48 false negatives and 106 false positives), two dominant, actionable failure mechanisms were identified:

1. **Direction Reversal in Genetic Complementation Experiments**:
   - In microbiological literature, authors demonstrate causality through genetic rescue:  
     $$\text{"[Phenotypic Defect] was restored in/by/upon [complementation with Gene]"}$$
   - Examples:
     - `PMC2714965` (Train): *"virulence was restored in the complemented cheB2 mutant"*
     - `PMC2358977` (Dev): *"The reduction in virulence was mostly restored in a complemented strain upon reintroduction of functional copies of salK and salR"*
     - `PMC2885601` (External): *"virulence was restored upon complementation with Mac"*
   - EVRYN's extractor currently treats `restored` solely as an active `ACTIVATION_PATTERN` in the forward direction. Consequently, it parses the phenotypic defect (e.g., `Virulence`) as the Cause and the restoring gene (e.g., `cheB2`, `SalR`, `Mac`) as the Effect, producing spurious inverted relations:
     $$\text{Virulence} \to \text{cheB2} \quad (\text{False Positive})$$
     $$\text{Virulence} \to \text{SalR} \quad (\text{False Positive})$$
     while dropping the genuine biological causal relation:
     $$\text{cheB2} \to \text{Virulence} \quad (\text{False Negative})$$
     $$\text{SalR} \to \text{Virulence} \quad (\text{False Negative})$$

2. **Violation of Terminal Phenotypic Direction Invariant**:
   - In pathogen biology, terminal host/disease outcomes (`Virulence`, `Pathogenicity`, `Host Survival`, `Protective Immunity`, `Mortality`, `Lethality`, `Host Colonization`) are strictly **terminal physiological endpoints**. A disease phenotype never acts as an upstream biochemical cause or transcriptional activator of a bacterial gene ($TerminalPhenotype \to MolecularGene$ is physically impossible).
   - Inverted predictions like `Virulence -> cheB2`, `Virulence -> SalK`, `Virulence -> SalR`, `Virulence -> Mac`, `Virulence -> SPI-2` persist because no terminal outcome constraint was enforced.

3. **Microbiological Morphological Gaps**:
   - Greek Delta (`Δ`) mutant prefixes (e.g., `ΔvicK`, `ΔrpoE`) denote gene deletion mutants. Because `Δ` is a non-ASCII symbol without word boundaries, it caused entity detection and canonicalization failures.
   - Greek Sigma (`σ`) in alternative sigma factors (e.g., `σE`, `σ(E)`) was not normalized to `sigmaE`.
   - Contextual equivalence between `Biofilm` and `Biofilm Formation` caused canonical entity mismatch against `known_entities`.

---

## 2. Why the Current Implementation Fails

1. **SVO Directionality Bias:** In `evryn/paper/extractor.py`, `r"\b(?:restores?|restored|restoring)\b"` was placed in `ACTIVATION_PATTERNS`, but never in `PASSIVE_INDICATORS`. In passive sentences with prepositional phrases (`was restored by/upon/in`), argument assignment was never inverted.
2. **Missing Terminal Constraint:** While Phase 1.4 enforced an input invariant for `ENV_PARAMS` ($Protein \to Environment$ is forbidden), no symmetric terminal invariant was enforced for disease phenotypes ($Phenotype \to Protein$ was permitted).
3. **Regex Word Boundary Limitation:** Standard `\b` fails between Greek characters (`\p{Lu}`) and ASCII letters, preventing `Δgene` from matching `gene`.

---

## 3. Proposed Intervention

We implement a targeted three-part intervention in `evryn/paper/extractor.py` and `evryn/paper/normalizer.py`:

1. **Passive Restorative Triggers:**
   Add `r"\b(?:is|was|are|were|has\s+been|have\s+been)?\s*(?:partially\s+|mostly\s+|fully\s+)?(?:restored|rescued)\s+(?:in|by|upon|with)\b"` to `PASSIVE_INDICATORS`, inverting argument directionality so that restoring genes are correctly assigned as Causes and the restored phenotypes as Effects.
2. **Terminal Phenotype Direction Invariant:**
   Reject any assertion where the Cause is a terminal phenotypic disease endpoint (`Virulence`, `Pathogenicity`, `Host Survival`, `Protective Immunity`, `Mortality`, `Lethality`, `Host Colonization`) and the Effect is a molecular entity, gene, or operon.
3. **Microbiological Morphological Canonicalization:**
   - Strip Greek `Δ` / `delta-` prefixes in `canonicalize`.
   - Normalize Greek `σ` / `σ(X)` to `sigmaX` in `canonicalize`.
   - Resolve bidirectional equivalence between `Biofilm` and `Biofilm Formation` against `known_entities`.

---

## 4. Expected Effect on Precision and Recall

- **Train Split:** Direct F1 expected to increase from `0.3306` to $\ge 0.3500$, with True Positives increasing from 7 to 8 and False Positives decreasing from 18 to 16.
- **Dev Split:** Direct F1 expected to increase from `0.5007` to $\ge 0.5070$, with False Positives decreasing from 35 to 34 and zero drop in True Positives.
- **Precision:** Noticeable reduction in spurious inverted false positives across all splits.

---

## 5. False-Positive Modes to Watch For

1. **Over-filtering valid phenotypic interactions:** Ensure that relations between two phenotypic endpoints (e.g., `Bacterial Survival -> Virulence` or `Adherence -> Host Colonization`) are **not** filtered out.
2. **Spurious passive matches:** Ensure that active statements (e.g., *"protein X restores growth"*) continue to be extracted in the forward direction.

---

## 6. Predefined Success Criteria

1. Measurable improvement in Train Direct Macro-F1 ($\ge 0.3500$, baseline $0.3306$) and Dev Direct Macro-F1 ($\ge 0.5070$, baseline $0.5007$).
2. Zero regression in Dev True Positives ($\ge 23$).
3. All 231 existing unit/integration tests continue to pass.
4. Clean confirmatory evaluation on Locked Test and External Generalization splits without tuning.
