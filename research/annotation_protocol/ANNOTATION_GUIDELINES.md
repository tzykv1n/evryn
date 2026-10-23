# EVRYN Multi-Page Causal Discovery: Human Annotation Protocol & Guidelines

**Standard Operating Procedure:** SOP-EVR-NLP-004  
**Version:** 2.1.0  
**Domain:** Cross-Section and Multi-Page Scientific Causal Relation Extraction  
**Compliance:** CC BY 4.0 Open Annotation Standard  

---

## 1. Overview and Scientific Motivation

Single-sentence relation extraction datasets (e.g., SemEval-2010 Task 8, BioNLP shared tasks) restrict relations to entities occurring within the exact same sentence. However, in scientific discovery and biomedical full-text publications:
1. **Cross-Section Arguments:** An upstream causal intervention or stimulus is frequently established in the *Abstract* or *Introduction*, while intermediate kinase cascades are characterized in *Methods*, and ultimate phenotypic endpoints appear across multiple figures in *Results* and *Discussion*.
2. **Mechanistic Transitivity:** Chains of causal regulation ($A \to B \to C \to D$) are distributed across distinct paragraphs or pages. Distinguishing direct evidence ($A \to B$) from transitive deductions ($A \to D$) is essential to avoid hallucinated direct interactions.
3. **Correlation vs. Causation & Confounding:** Observational correlations (*"X was observed alongside Y"*) must never be annotated as causal assertions without mechanistic manipulation, knockouts, or statistical identification.

This document defines the rigorous protocol for annotating and adjudicating multi-page scientific causal relations.

---

## 2. Relation Typology and Taxonomy

Annotators must classify each candidate relationship into one of the following canonical types:

| Relation Type | Code | Operational Definition | Positive Lexical Triggers |
| :--- | :--- | :--- | :--- |
| **Direct Up-Regulation** | `UPREGULATES` | Entity A directly increases the level, activity, expression, or phosphorylation of Entity B without intermediate named agents in that claim. | *activates, stimulates, phosphorylates, induces, triggers, promotes, upregulates* |
| **Direct Down-Regulation** | `DOWNREGULATES` | Entity A directly suppresses, represses, inhibits, degrades, or dephosphorylates Entity B. | *inhibits, represses, blocks, attenuates, degrades, knocks down, downregulates* |
| **General Causality** | `DIRECT_CAUSE` | Explicit mechanistic causation where directional polarity is non-binary or bidirectional. | *causes, leads to, drives, results in, is responsible for* |
| **Mediated Causality** | `MEDIATES` | Entity B acts as the necessary intermediate conduit transmitting causal force from Entity A to Entity C. | *mediates, acts through, requires intermediate activation of* |
| **Associative / Non-Causal** | `ASSOCIATED` | Statistical co-occurrence or correlational observation without demonstrated causal mechanism. | *correlates with, is associated with, parallels, coincides with* |
| **Confounded / Spurious** | `CONFOUNDED` | Entity A and B co-vary solely due to mutual regulation by unobserved or upstream factor Z. | *spurious correlation, co-regulated downstream of* |

---

## 3. Span Annotation Rules

### 3.1 Entity Spans (Cause and Effect)
- **Maximal Specificity:** Annotate the exact nominal entity span. If a specific mutant or state is tested (e.g., *phospho-EGFR (Tyr1068)*), annotate the qualified entity span rather than just the generic gene family.
- **No Span Overflow:** Do not include leading determiners (*the*, *a*) or trailing punctuation in the entity span unless it is an intrinsic part of the biochemical nomenclature.

### 3.2 Trigger and Evidence Spans
- **Explicit Trigger:** Every direct causal claim must identify the trigger token(s) (e.g., *"phosphorylates"*, *"induced"*).
- **Exact Sentence Offset:** Every claim must reference the exact 0-indexed character offsets (`[start, end]`) and page/section number where the evidence appears.

---

## 4. Scope Classification: Direct vs. Cross-Page vs. Inferred

Each annotation must record its topological scope:

1. **Sentence-Local (`LOCAL`):** Cause entity, effect entity, and trigger all reside within a single sentence boundary.
2. **Cross-Sentence Paragraph-Local (`PARA`):** Arguments reside in different sentences within the same paragraph/section block.
3. **Cross-Section / Cross-Page (`CROSS_PAGE`):** Cause and effect are stated across distinct structural sections (e.g., Introduction vs. Discussion).
4. **Inferred Transitive Path (`TRANSITIVE`):** A multi-hop deduction ($A \to C$) derived from intermediate direct assertions ($A \to B$ on Page 1, $B \to C$ on Page 4). Transitive paths are **never** scored as ground-truth direct edges unless an explicit concluding sentence in the text synthesizes the end-to-end claim.

---

## 5. Negative and Non-Causal Boundary Examples

To prevent annotator drift, annotators must apply negative filters:

- **Negative Correlation:**  
  *Text:* "High levels of Protein X were observed in patients exhibiting Symptom Y."  
  *Decision:* Label as `ASSOCIATED`, **NOT** `DIRECT_CAUSE`.
- **Negated Causality:**  
  *Text:* "Inhibition of MEK failed to alter EGFR phosphorylation."  
  *Decision:* Do not annotate as an activating or inhibitory causal edge. Annotate as explicit negative control / absence of regulation.
- **Hypothetical / Future Work:**  
  *Text:* "We hypothesize that Factor A may potentially modulate Factor B in other tissue types."  
  *Decision:* Exclude from verified causal assertions; label as hypothesis only.

---

## 6. Annotator Agreement and Multi-Pass Adjudication

1. **Independent Dual Annotation:** Two independent annotators (Annotator A and Annotator B) review each paper without seeing each other's spans or relation assignments.
2. **Inter-Annotator Agreement (IAA):** Compute Cohen's Kappa ($\kappa$) on relation categories and strict span-overlap F1.
3. **Adjudication Phase:** Discrepant relation labels or boundary differences greater than 3 tokens are escalated to a senior biomedical curator. Consensus or strict tie-breaker rules decide the canonical gold standard.
