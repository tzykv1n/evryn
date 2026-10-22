# EVRYN: Evidence-Traceable Multi-Page Causal Discovery in Scientific Literature
## Research Plan and Milestone Objectives

### 1. Executive Summary

Existing scientific NLP extraction pipelines predominantly operate on isolated sentences or localized paragraphs, failing to synthesize mechanistic causal pathways that span across multiple pages of full-text scientific papers. In real scientific literature, hypotheses are framed in the introduction, experimental mechanisms are observed in distinct result sections across different pages, and high-level syntheses are discussed in concluding sections.

This milestone advances EVRYN from sentence-level and synthetic graph discovery toward **evidence-traceable causal discovery across multiple pages of scientific papers (PDFs)**.

### 2. Hypotheses & Research Objectives

1. **Hypothesis 1 (Cross-Page Mechanistic Bridging)**: Integrating multi-page text segmentation with document-wide entity normalization and transitive causal chaining significantly outperforms independent sentence-level extraction in discovering end-to-end signaling cascades.
2. **Hypothesis 2 (Provenance Grounding)**: Grounding reconstructed causal graphs directly in physical page numbers, section types, and verbatim quotes eliminates ungrounded inferences without sacrificing extraction recall.
3. **Hypothesis 3 (Distractor & Negation Resilience)**: Rule-gated causal pattern matching coupled with explicit negation tracking provides high resilience against irrelevant distractor mentions and non-significant experimental findings.

### 3. Pipeline Stages & Architectural Scope

- **Stage A (PDF Ingestion & Provenance)**: Parse real scientific PDFs preserving physical page boundaries, extracting metadata (DOI, PMID, PMCID), cleaning headers/footers, and repairing word hyphenation.
- **Stage B (Document Segmentation)**: Segment full text into sections (Abstract, Introduction, Methods, Results, Discussion, Conclusion), paragraphs, and sentences with stable character offsets.
- **Stage C (Sentence Causal Extraction)**: Detect causal interactions, directionality, negation status (`REFUTED_NEGATION`), and uncertainty scoring (`MEASURED_FACT` vs. `HYPOTHESIS_CLAIM`).
- **Stage D (Document-Wide Entity Normalization)**: Discover local abbreviation definitions (e.g., `vascular endothelial growth factor (VEGF)`) and canonicalize entities across pages.
- **Stage E (Cross-Page Evidence Linking)**: Discover multi-page transitive mechanisms ($A \to B$ on page $p_1$, $B \to C$ on page $p_2 \implies A \to B \to C$) and ground high-level claims in empirical results.
- **Stage F (Directed Causal Graph Reconstruction)**: Synthesize NetworkX directed causal graphs with direct and inferred edges, accompanied by complete provenance maps.
- **Stage G (Traceable Reporting & Visualization)**: Generate Markdown evidence reports, JSON structured registries, and publication-grade graph visualizations at 300 DPI.

### 4. Experimental Milestones & Deliverables

1. **Benchmark Corpus**: 12 multi-page scientific papers formatted as real PDFs with ground-truth causal graphs and cross-page chains across canonical biomedical pathways (EGFR/MAPK, IL-6/STAT3, HIF-1alpha/VEGF, p53/ATM, AMPK/mTOR, NF-kB, TGF-beta/SMAD, Wnt/beta-catenin, Caspase/Apoptosis, IFN-gamma/JAK/STAT, Notch signaling, IGF-1/PI3K/AKT).
2. **Evaluation Protocol**: Comparative benchmarking of:
   - **Baseline A**: Sentence-only extraction without document-wide normalization or cross-page linking.
   - **Baseline B**: Sentence-level extraction with document-wide normalization, without cross-page linking.
   - **System C**: Full EVRYN integrated multi-page pipeline.
3. **Robustness Suites**: Sentence dropout sweeps (0%, 10%, 20%, 30%) and distractor/negation noise injection (0%, 15%, 30%).
4. **CLI Subsystems**: First-class CLI support via `evryn paper inspect|extract|graph|report|evaluate` and `evryn benchmark --suite multi-page`.
5. **Reproducibility & Verification**: Full test suite verification under strict `-W error` mode.
