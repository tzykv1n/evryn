# EVRYN Phase 1 Visual Revision & Phase 1.7 Advancement Changelog

**Release Date:** October 24, 2026  
**Branch:** `phase2.1-benchmark-audit-and-ui-fix`  

---

## 1. Visual Revision Summary

### Workstream A: Presentation Redesign (`Temporal_Causal_Knowledge_Phase1_Presentation.pdf`)
1. **Academic Color Palette Enforced**:
   - Deep Navy (`#0F172A`): Structural framing, header bands, main cards, primary identity.
   - Teal (`#0D9488`): EVRYN components, causal edges, provenance grounding, SCM interventions.
   - Blue (`#2563EB`): Data pipelines, intermediate representations, parser stages.
   - Amber (`#D97706`): Caution blocks, limitations, associational correlations, threats to validity.
   - Green (`#16A34A`): Verified hits, accepted hypotheses, true positives, checkmarks.
   - Red (`#DC2626`): Errors, baseline failures, isolation walls, false negatives.
   - Slate Background (`#F8FAFC`): Crisp, glare-free card backgrounds.
2. **Strict Sharp $90^\circ$ Corners**:
   - All TikZ nodes, cards, blocks, and frames set to `sharp corners`, `rounded=false`. Zero rounded corners.
3. **Visual-First Layouts**:
   - Replaced bullet-point text walls with structured diagrams, comparative matrices, and pipeline flowcharts across all 40 slides.
   - Slide 5: 4-quadrant comparative matrix (Sentence NLP, Co-occurrence, LLMs, EVRYN).
   - Slide 7: Structured research question mapping grid.
   - Slide 9: Directed Acyclic Graph with Pearl's $do$-calculus intervention node.
   - Slide 22: Visual 20-paper partition diagram with a solid red "LOCKED ISOLATION GATE".
   - Slide 33: Two-panel visual error taxonomy breakdown.
   - Slide 40: 5-phase visual research roadmap.
4. **Compilation & Overflow Elimination**:
   - Compiled with `tectonic`: Exactly 40 slides, 0 compilation errors, 0 overfull vboxes, 0 overfull hboxes.

### Research Report Verification (`main.pdf`)
1. **Monochrome Policy Enforcement**:
   - Strictly 100\% black-and-white / grayscale throughout all 33 pages ($R=G=B$).
   - Sole authorized color exception: Official CUSAT logo on the title page.
   - All 6 vector and PNG figures converted to pure grayscale.
   - `hypersetup` configured with `hidelinks=true, colorlinks=false`.

---

## 2. Phase 1.7 Model Advancement Summary

### Workstream B: Document-Context Relation Resolution
1. **Targeting Discourse False Negatives**:
   - Addressed the 28 discourse-level false negatives (58.3\% of total FNs) whose entities span sentence boundaries.
   - Implemented `DocumentContextResolver` in `evryn/paper/document_context.py`.
2. **Experimental Matrix (E0--E5)**:
   - Evaluated 6 configurations across Train (4), Dev (8), Locked Test (4), External V1 (4), and External V2 (4).
   - **Configuration E3 (Demonstrative Causal Anaphora)** emerged as the optimal calibrated model:
     - **Dev Direct F1 increased to 0.5285** (95\% CI: `[0.4722, 0.5875]`), up from 0.5076/0.5133.
     - **Dev Recall increased from 63.89\% to 66.67\%** (recovering gold discourse claims).
     - **Locked Test Direct F1 preserved at 0.3429** (95\% CI: `[0.1537, 0.5625]`).
     - **External V2 Direct F1 preserved at 0.3289** (95\% CI: `[0.2409, 0.4103]`).
     - Zero regressions on any held-out split.
3. **Biological Invariant Filtering**:
   - Enforced 3 hard constraints: Terminal Phenotype Invariant, Environmental Input Invariant, and Genetic Complementation Filter.
4. **Automated Test Suite**:
   - Created `tests/test_document_context.py` with 100\% test coverage.
   - All 248 tests across the repository pass without error.

---

## 3. Phase 1.8 Comprehensive Extraction Advancement Summary

### Key Innovations & Interventions
1. **Active Matrix Causative Precedence**:
   - Resolved passive override bug: active matrix verbs (`caused`, `induces`, `promotes`, `activates`, `leads to`) govern direction when subordinate construct modifiers (`under the control of`, `in response to`) are present.
2. **Expanded Genetics Mutant Phenotype Grammar**:
   - Recognized direction-inverted regulation prose (`enhanced`, `hyperinduced`, `over-expressed` in mutants) and phenotype defect syntax (`mutant defect in chemotaxis`), mapping `CsrS -| slo` and `cheB1 -> Chemotaxis`.
3. **Syntactic Triggers & Forward Connectives**:
   - Added gerund regulatory triggers (`plays an important role in regulating`), fine-tuning (`involved in fine-tuning`), forward connectives (`and thus`), and anti-factor release (`from anti-sigma factor RseA`).
4. **Structural Composition & TCSTS Operon Resolution**:
   - Added subunit composition (`made up of Mfa1`), TCSTS operon-regulator coupling (`GraRS regulatory genes -> GraR`), and exact-match canonicalization priority preventing TCSTS collisions.
5. **Genomic Locus False Positive Pruning**:
   - Replaced spurious locus encoding edges (`SPI1 -> HilA`) via `ENCODED_WITHIN_LOCUS_RE`.

### Metric Milestone Progression
- **Locked Test Direct F1**: **0.4658** (up from 0.3429 baseline, **+35.8% relative gain** on frozen held-out literature).
- **Dev Direct F1**: **0.5668** (up from 0.5285 baseline).
- **Train Direct F1**: **0.4750** (up from 0.3521 baseline, Cross-Page F1 up to **0.2083**).
- **Total Errors Reduced**: FNs reduced by **-15.2%** (46 to 39); FPs reduced by **-18.3%** (104 to 85).
- **Test Suite**: **252 / 252 tests passing (100%)** with `tests/test_phase1_8_extraction.py`.
- **Throughput**: **586.2 ms/paper** (15.87 pages/sec).
