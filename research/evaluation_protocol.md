# EVRYN Evaluation Protocol: Multi-Page Causal Knowledge Extraction

## 1. Paper Partitioning & Integrity Rules
To guarantee zero data contamination and scientific defensibility:
- **Development Partition (8 papers):** Used for developing extraction rules, tuning distance and confidence thresholds, and ablation studies.
  - `PMC1804205`, `PMC1874608`, `PMC1913099`, `PMC1974823`, `PMC2242835`, `PMC2266911`, `PMC2358977`, `PMC2430206`
- **Locked Held-Out Test Partition (4 papers):** Strictly frozen evaluation split.
  - `PMC2565068`, `PMC2581603`, `PMC2593050`, `PMC2639726`
- **Contamination Prevention:**
  - No entity synonyms, patterns, or thresholds are adjusted based on the locked test papers.
  - Extraction runs fully autonomously without gold entity labels injected into test documents.

## 2. Evaluation Metrics Definitions
For each paper and across suites:
- **Direct Causal Extraction:**
  - Evaluated on within-page and adjacent-context causal assertions.
  - Strict exact tuple match: `(pred_cause, pred_effect) == (gold_cause, gold_effect)`.
  - Precision ($P_{dir}$), Recall ($R_{dir}$), F1 ($F_{1, dir}$).
- **Cross-Page Causal Synthesis:**
  - Evaluated on multi-hop transitive paths where evidence spans $\ge 1$ page boundaries.
  - Precision ($P_{cross}$), Recall ($R_{cross}$), F1 ($F_{1, cross}$).
- **Overall Joint Extraction:**
  - Direct union Cross-page graph edges evaluated against the union of direct and cross-page gold edges.
  - Joint Precision ($P_{joint}$), Joint Recall ($R_{joint}$), Joint F1 ($F_{1, joint}$).
- **Structural Match (Graph Jaccard):**
  - $\text{Jaccard}(E_{pred}, E_{gold}) = \frac{|E_{pred} \cap E_{gold}|}{|E_{pred} \cup E_{gold}|}$.
- **Provenance Completeness:**
  - Fraction of extracted graph edges anchored to verified source sentence IDs and page numbers ($Prov \ge 0.95$).

## 3. Statistical Significance & Resampling Protocol
- Non-parametric bootstrap resampling ($B = 1000$ iterations) resampled by paper to compute 95% Confidence Intervals:
  - $\text{CI}_{95\%} = [\text{Quantile}_{0.025}, \text{Quantile}_{0.975}]$.
