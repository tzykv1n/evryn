# EVRYN Phase 1 Visual Revision Change Log

This document records the visual, structural, and numerical revisions executed across the EVRYN Phase 1 deliverables (Research Report and 40-Slide Presentation).

---

## 1. Executive Summary of Changes

The research report and 40-slide presentation were revised to implement an authoritative, publication-grade visual system with minimal text clutter, square orthogonal geometry, and verified benchmark metrics.

| Deliverable | Previous State | Revised State | Key Improvements |
| :--- | :--- | :--- | :--- |
| **Presentation** (`Temporal_Causal_Knowledge_Phase1_Presentation.pdf`) | 40 slides, dense paragraphs, mixed styles | 40 slides, visual-first, strictly $\le 3$ bullets per slide, square TikZ diagrams | Direct visual storytelling, 0 clipped boxes, no rounded corners |
| **Research Report** (`main.pdf`) | 33 pages, legacy raster diagrams, outdated 12-paper setup | 33 pages, 6 vector/300 DPI publication figures, authentic 20-paper multi-split setup | Crisp monochrome-legible vector graphics, updated error census & multi-split tables |
| **Core Publication Figures** | Mixed styles, missing workflow & split diagrams | 6 unified publication figures (PDF & 300 DPI PNG) | Standardized typography, square borders, zero color dependency |

---

## 2. Visual System Specifications

Across all diagrams, presentation slides, and report figures, the following constraints were strictly enforced:
- **Zero Rounded Corners**: All node boxes, frames, and callouts use sharp $90^\circ$ orthogonal corners (`rectangle`, `sharp corners`).
- **Monochrome & Grayscale Legibility**: Designed in black, white, and neutral grays (`gray!5`, `gray!10`, `gray!15`, `#1E293B`, `#475569`, `#94A3B8`, `#F8FAFC`). Legible with high contrast on standard 1-bit or grayscale printouts.
- **Rule Weight Calibration**: Clean hairline to medium rules (0.6\,pt to 1.2\,pt), matching academic IEEE/ACM publishing standards.
- **Typography**: Clean sans-serif and TeX Computer Modern / Latin Modern fonts, scaled proportionally to prevent any text clipping or overflow.

---

## 3. Publication Figures Created and Integrated

Six core publication figures were generated via `scripts/generate_publication_figures.py` and saved in both editable vector PDF and 300 DPI PNG formats in `figures/`:

1. `fig1_system_architecture` (PDF / PNG):
   - **Report**: Figure 4.1 (`chapter4_architecture.tex`)
   - **Presentation**: Slide 14
   - **Content**: 6-stage end-to-end pipeline: PDF/Document Ingestion $\to$ Text & Structure Segmentation $\to$ Entity & Relation Candidate Extraction $\to$ Normalization & Directional Resolution $\to$ Evidence-Grounded Assertion Output $\to$ Graph Visualization & Verification.
2. `fig2_extraction_workflow` (PDF / PNG):
   - **Report**: Figure 4.2 (`chapter4_architecture.tex`)
   - **Presentation**: Slide 17
   - **Content**: 5-step detailed workflow: Candidate Generation $\to$ Relation Validation $\to$ Context Resolution $\to$ Multi-Page Linking $\to$ Provenance & Calibration.
3. `fig3_evidence_direction` (PDF / PNG):
   - **Report**: Figure 3.1 (`chapter3_methodology.tex`)
   - **Presentation**: Slide 9
   - **Content**: Contrast between Direct Localized assertion, Transitive Multi-Page chain, and Observational/Negated claims with full provenance metadata ($[c_{\text{start}}, c_{\text{end}}]$, PMCID, section, verbatim quote).
4. `fig4_evaluation_workflow` (PDF / PNG):
   - **Report**: Figure 5.1 (`chapter5_results.tex`)
   - **Presentation**: Slide 24
   - **Content**: Complete 20-paper partition showing 4 Train, 8 Dev, double-line zero-leakage gate, 4 Locked Held-Out Test, and 4 External Unseen articles with V1 vs V2 audit protocol.
5. `fig5_error_analysis` (PDF / PNG):
   - **Report**: Figure 5.3 (`chapter5_results.tex`)
   - **Presentation**: Slide 28
   - **Content**: Audited error census displaying 48 False Negatives (28 discourse-level cross-sentence claims, 20 relation triggering gaps) and 104 False Positives (neighboring co-occurrences, complementation controls, terminal phenotypes).
6. `fig6_results_progression` (PDF / PNG):
   - **Report**: Figure 5.2 (`chapter5_results.tex`)
   - **Presentation**: Slide 26
   - **Content**: Comparative performance progression showing Direct Causal $F_1$, Cross-Page $F_1$, and Exact Structural Match with 95% bootstrap confidence intervals across Train, Dev, Locked Test, External V1, and External V2.

---

## 4. Report Content Updates

- **Abstract (`main.tex`)**: Updated from legacy 12-paper text to the verified 20-paper benchmark partition (4 Train, 8 Dev, 4 Locked Test, 4 External Unseen), citing authentic Dev Direct $F_1 = 0.5076$, External V2 Direct $F_1 = 0.3289$, and the 48 FN / 104 FP error census.
- **Chapter 3 (`chapter3_methodology.tex`)**: Added Figure 3.1 illustrating evidence grounding, causal directionality, and relational typology.
- **Chapter 4 (`chapter4_architecture.tex`)**: Replaced Figure 4.1 with `fig1_system_architecture.pdf` and added Figure 4.2 (`fig2_extraction_workflow.pdf`).
- **Chapter 5 (`chapter5_results.tex`)**:
  - Formalized the 20-paper benchmark partition and zero-leakage isolation gate with Figure 5.1 (`fig4_evaluation_workflow.pdf`).
  - Updated Table 5.1 with verified empirical metrics across all 5 split configurations (Train, Dev, Locked Test, External V1, External V2) including 95% bootstrap confidence intervals and exact micro counts (External V1 micro: 5 TP / 55 FP / 15 FN).
  - Added Figure 5.2 (`fig6_results_progression.pdf`).
  - Documented the PMC2816692 *Salmonella* SrcA vs. legacy Anthrax LF metadata mismatch audit and recovery in External V2.
  - Reconciled the 106 baseline FPs vs. 104 post-intervention FPs census in Section 5.5 and Figure 5.3 (`fig5_error_analysis.pdf`).
  - Explicitly segregated Track 1 (Natural Language Literature Extraction on PMC-OA) from Track 2 (Continual SCM task streams) and Track 3 (Higher-Order interaction modeling).
- **Chapter 6 (`chapter6_conclusion.tex`)**: Updated deliverable summary to reflect the 20-paper benchmark.

---

## 5. Numerical Provenance Audit & Machine-Readable Deliverables
- Generated `FINAL_BENCHMARK_COMPARISON.csv` containing machine-readable metrics for all benchmark splits across V1 and V2.
- Produced `FINAL_METRIC_PROVENANCE_AUDIT.md` providing line-by-line artifact evidence for the 106 vs 104 FP resolution and external score evolution (`0.1566` $\to$ `0.2335` $\to$ `0.2380` $\to$ `0.3289`).
- Produced `FINAL_REPORT_PRESENTATION_CONSISTENCY.md` cross-referencing all 38 numerical claims across deliverables.

---

## 6. Presentation Content & Structural Revisions

- Completely rebuilt using `scripts/build_revised_presentation.py` to produce `Temporal_Causal_Knowledge_Phase1_Presentation.tex`.
- Guaranteed exact 40-slide count matching the target presentation sequence.
- Strict visual-first constraints:
  - Every slide contains a bold takeaway header.
  - Slide bodies prioritize structured TikZ flowcharts, comparative tables, and metrics cards over paragraphs.
  - Bulleted lists are restricted to $\le 3$ concise points per slide.
  - Zero rounded corners anywhere; all boxes have square $90^\circ$ corners.
  - Monochrome legibility verified across all 40 slides.
