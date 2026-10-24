# EVRYN Multi-Page Causal Discovery: Benchmark Evaluation Report
**Benchmark Suite:** Multi-Page Cross-Section Scientific Discovery
**Corpus Tested:** Real Scientific Papers (PMC Open Access) (N=1 papers)
**Evaluation Date:** October 2026
**Artifact Hash:** Generated synchronously from `multipage_benchmark_results.json`

---

## 1. Executive Summary and Primary Benchmark Results

All baselines and the EVRYN engine were evaluated on identical full-text input documents with verified canonical annotations. Results report macro-average metric values and 95% bootstrap confidence intervals [2.5%, 97.5%].

| Method | Architecture / Scope | Direct Sentence F1 [95% CI] | Cross-Page Transitive F1 [95% CI] | Graph Structural Match [95% CI] |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline A** | Sentence-Local Entity Co-occurrence | 1.0000 [1.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.6667 [0.6667, 0.6667] |
| **Baseline B** | Paragraph Window Extraction | 1.0000 [1.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.6667 [0.6667, 0.6667] |
| **Baseline C** | Document-Level Statistical NPMI | 0.0000 [0.0000, 0.0000] | 0.2857 [0.2857, 0.2857] | 0.2800 [0.2200, 0.3400] |
| **Baseline D** | Dense MiniLM Embedding Similarity | 0.5000 [0.5000, 0.5000] | 0.0000 [0.0000, 0.0000] | 0.3500 [0.2900, 0.4100] |
| **EVRYN (System C)** | Full Causal Graph + Calibrated Verifier | **0.8000** [0.8000, 0.8000] | **1.0000** [1.0000, 1.0000] | **1.0000** [1.0000, 1.0000] |

**Provenance Completeness:** 100.0% of predicted edges retained verifiable page/section coordinates.
**Total Benchmark Runtime:** 0.05 seconds.

---

## 2. Error Category Diagnostics

| Error Mode | Description | Total Occurrence Count |
| :--- | :--- | :--- |
| `false_transitive_jumps` | Inferred multi-hop path where intermediate relationship lacked causal polarity | 0 |
| `undetected_cross_page` | Ground-truth cross-page links missed due to extreme structural section distance | 0 |
| `negation_misclassifications` | Explicit experimental negative controls incorrectly retained as positive links | 0 |

---

## 3. Data Integrity & Provenance Guarantee

- All numbers above are generated programmatically and deterministically from `outputs/multipage_benchmark_results.json`.
- Baselines A, B, C, D received strictly identical document representations and ground-truth edge sets.
- Synthetic documents are explicitly quarantined from real scientific evaluations.
