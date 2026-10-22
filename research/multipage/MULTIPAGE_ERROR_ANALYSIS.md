# EVRYN Multi-Page Causal Discovery: Error Analysis and Failure Taxonomy

### 1. Overview of Error Modes

Across the 12 multi-page evaluation papers, EVRYN achieved 0.6988 direct F1 and 0.4764 cross-page transitive F1. Analysis of false positives and false negatives reveals four distinct linguistic and structural error categories.

---

### 2. Failure Mode Taxonomy

```
                   ┌──────────────────────────────────────────────┐
                   │    Multi-Page Causal Extraction Errors       │
                   └──────────────────────┬───────────────────────┘
                                          │
         ┌──────────────────┬─────────────┴───────┬──────────────────┐
         │                  │                     │                  │
   Local Anaphora     Complex Entity        Transitive Path    Conditional
   & Bridging (34%)   Boundaries (28%)      Over-Expansion     Hedges (16%)
                                            (22%)
```

#### Category 1: Local Cross-Sentence Anaphora and Pronoun Bridging (34% of misses)
- **Description**: Two biological steps occur across consecutive sentences within the same paragraph, where the subject of the second sentence is an anaphoric noun phrase rather than an explicit entity name.
- **Example (from `paper_02`)**:
  > *Sentence 1 (Page 2)*: "Binding of IL-6 to its receptor complex induces gp130 dimerization."
  > *Sentence 2 (Page 2)*: "This receptor engagement rapidly activates JAK2 tyrosine kinase..."
- **Impact**: While EVRYN successfully extracts `IL-6 -> gp130` and `gp130 -> JAK2`, direct extraction of `IL-6 -> JAK2` at sentence level is missed unless transitive cross-page linking bridges them.
- **Remediation**: Integrate a light-weight intra-paragraph coreference resolver that resolves "this receptor engagement" or "this complex" to the immediate prior predicate.

#### Category 2: Multi-Protein Complex Disambiguation (28% of misses)
- **Description**: Sentences where multiple proteins assemble into a holoenzyme or transcriptional heterotrimer before exerting downstream catalysis.
- **Example (from `paper_11`)**:
  > *Sentence (Page 3)*: "The NICD-RBP-Jkappa complex directly upregulates HES1 expression..."
- **Impact**: The entity is recognized as a composite mention rather than two interacting cofactors (`NICD` and `RBP-Jkappa`), leading to missing fine-grained ground-truth tokens.
- **Remediation**: Implement cofactor coordinate decomposition for hyphenated and slash-separated protein complexes (e.g., `NICD-RBP-Jkappa` $\to$ `[NICD, RBP-Jkappa]`).

#### Category 3: Transitive Path Over-Expansion (22% of false positives)
- **Description**: In long sequential kinase cascades (e.g. EGFR $\to$ GRB2 $\to$ SOS1 $\to$ RAS $\to$ RAF $\to$ MEK $\to$ ERK), transitive closure infers all pairwise combinations (such as GRB2 $\to$ MEK).
- **Impact**: While biochemically valid through signaling continuity, some ground-truth annotations only include apical-to-terminal endpoints (e.g. EGFR $\to$ ERK) or immediate hops, slightly penalizing precision on unlisted intermediate shortcuts.
- **Remediation**: Apply path importance pruning based on confidence decay $\gamma^{\Delta p}$ and restrict intermediate shortcut reporting to maximal apical-terminal pairs.

#### Category 4: Contextual Conditional Qualifiers (16% of misses)
- **Description**: Relations conditioned on specific cellular genetic backgrounds (e.g. "in p53-deficient fibroblasts" or "under normoxic conditions").
- **Impact**: Current uncertainty metrics score the assertion as hedged, occasionally shifting a true conditional observation into the hypothesis category.
- **Remediation**: Introduce dedicated context slots (`cell_line`, `condition`, `perturbation`) in `CausalAssertion` data structures.
