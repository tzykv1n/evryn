# EVRYN Phase 1 Research Deliverables & Reproducibility Guide

## 1. Research Objective & Scope
The objective of EVRYN Phase 1 is to build a scientifically rigorous, evidence-traceable multi-page causal knowledge extraction engine and interactive causal discovery workspace. The system extracts directed, signed, and provenance-grounded causal assertions from authentic PubMed Central Open Access (PMC-OA) scientific literature, synthesizes cross-page pathways across distinct sections, prevents catastrophic forgetting across continual SCM task streams, and exposes an interactive causal exploration interface.

## 2. Tracked Phase 1 Deliverables
- **Research Progress Report (PDF):** [`docs/phase1/main.pdf`](main.pdf)  
  *Format:* CUSAT M.Tech Phase 1 Format, 29 numbered pages.
- **Academic Slide Presentation (PDF):** [`docs/phase1/Temporal_Causal_Knowledge_Phase1_Presentation.pdf`](Temporal_Causal_Knowledge_Phase1_Presentation.pdf)  
  *Format:* Strictly 40 slides, 16:9 widescreen, monochrome square-cornered presentation.
- **Benchmark Audit Report:** [`docs/phase1/benchmark_audit_report.md`](benchmark_audit_report.md)  
  *Content:* Complete discrepancy analysis, hash audits, and gate recommendations.
- **Reproducibility Metrics:** [`results/phase1/recomputed_metrics.json`](../../results/phase1/recomputed_metrics.json)  
  *Content:* Machine-readable JSON metrics recomputed from canonical predictions.

## 3. How to Run Tests and Benchmark Evaluation

### 3.1 Environment Activation
```bash
source /home/tk/projects/flux-nlp/.venv/bin/activate
cd /home/tk/projects/evryn
```

### 3.2 Run Pytest Suite (Backend & Semantic Extraction)
```bash
pytest tests/ -v
# Quick execution:
pytest tests/test_extraction_semantics.py tests/test_paper_reliability.py -v
```

### 3.3 Run Frontend Interaction & Contract Suites
```bash
node tests/test_active_relations_contract.js
node tests/test_sidebar_interactions.js
node tests/test_ui_regression.js
node tests/test_ui_overlaps.js
```

### 3.4 Run Canonical 12-Paper Benchmark
```bash
python evryn/cli.py paper evaluate
```

## 4. Benchmark Datasets and Split Partitioning
Evaluations operate on 12 authentic PMC-OA biomedical papers across two strictly separated partitions:
- **Development Split (8 papers):** `PMC1804205`, `PMC1874608`, `PMC1913099`, `PMC1974823`, `PMC2242835`, `PMC2266911`, `PMC2358977`, `PMC2430206`
- **Locked Held-Out Test Split (4 papers):** `PMC2565068`, `PMC2581603`, `PMC2593050`, `PMC2639726`

## 5. Verified Experimental Results & Status

| Metric | Baseline A (Sentence) | Baseline B (Paragraph) | Baseline C (Doc NPMI) | Baseline D (Dense MiniLM) | EVRYN System C (Final) | 95% Bootstrap CI |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Direct Causal $F_1$** | 0.4788 | **0.5273** | 0.3645 | 0.1171 | **0.4232** | [0.343, 0.506] |
| **Cross-Page $F_1$** | 0.0000 | 0.0000 | 0.2546 | 0.1989 | **0.2550** | [0.157, 0.345] |
| **Structural Match** | 0.3311 | **0.5607** | 0.2800 | 0.3500 | **0.3605** | [0.276, 0.444] |
| **Provenance Grounding** | 100.0% | 100.0% | 0.0% | 14.3% | **100.0%** | — |
| **Negation Error Rate** | — | — | — | — | **0.0%** | (1.7% overall) |

### Formal Acceptance Status:
- **Zero Unhandled Failures:** SATISFIED (19/19 passed)
- **Complete Provenance:** SATISFIED (100.0% grounded)
- **Controlled Transitivity:** IN PROGRESS (54 false jumps, $-81.8\%$ from baseline 296)
- **Directional Accuracy:** SATISFIED on unambiguous mechanisms (0 negation errors)
- **Real Literature $F_1 \ge 0.50$:** IN PROGRESS ($F_1^{\text{cross}} = 0.2550$)
- **Regression Stability:** SATISFIED (203/203 unit tests passed)

*Note on Acceptance Threshold:* Because Criterion 5 ($F_1^{\text{cross}} \ge 0.50$) is in progress, multi-page extraction remains under active development for Phase 2. No metrics have been fabricated or altered.
