# EVRYN Phase 1.12 — Automated Validation & Integrity Report

**Repository:** `https://github.com/tzykv1n/evryn`  
**Execution Timestamp:** 2026-10-25  
**Python Runtime:** `/home/tk/projects/flux-nlp/.venv/bin/python` (Python 3.12)  
**Tectonic Compiler:** `/home/tk/.local/bin/tectonic`  

---

## 1. Test Suite Results

The comprehensive test suite was executed across all unit, extraction, evaluation, and regression test modules:

```bash
pytest tests/ -v
```

### Result Summary
- **Total Tests Collected:** 274
- **Passed:** **274**
- **Failed:** **0**
- **Skipped / XFailed:** **0**
- **Pass Rate:** **100.0%**
- **Execution Wall Clock Time:** ~2.1 seconds

### New Phase 1.12 Test Coverage (`tests/test_phase1_12_extraction.py`)
- `test_agent_nominal_activation_extraction`: Validates direct edge extraction from `"SlyA activation of ssrB promoter"`.
- `test_agent_nominal_inhibition_extraction`: Validates direct edge extraction from `"Fur repression of entC transcription"`.
- `test_homology_filter_suppresses_cloning_cooccurrence`: Validates that cloning statements (`"The gene was cloned and amplified..."`) do not yield spurious causal edges.
- `test_homology_filter_suppresses_sequence_homology`: Validates that statements comparing homologues (`"SeMac is a functional homologue of Mac-1..."`) do not produce false causal edges.
- `test_ablation_toggle_disables_nominal_activation`: Validates that setting `enable_agent_nominal_activation=False` restores baseline behavior.
- `test_ablation_toggle_disables_homology_filter`: Validates that setting `enable_homology_filter=False` permits permissive extraction.

---

## 2. Zero-Leakage & Data Hygiene Audit

- **Held-Out Integrity:** Under no circumstances were training rules tuned on the locked test papers (`PMC2593050`, `PMC2639726`, `PMC2651894`, `PMC2682197`) or external generalization papers (`PMC2816692`, `PMC2858072`, `PMC2885601`, `PMC2908250`).
- **Feature Generalization:** Patterns implemented (`PAT_AGENT_NOMINAL_ACT`, `METHOD_HOMOLOGY_RE`) were formulated based on standard biomedical linguistic grammar, not paper-specific identifiers or ad-hoc overrides.
- **Phase Boundary Integrity:** Strict Phase 1 boundaries were preserved. No Phase 2 work or components were triggered or altered.

---

## 3. PDF Compilation Verification

Both primary research deliverables were compiled cleanly from source:

1. **LaTeX Research Monograph (`main.pdf`):**
   - Source: `/home/tk/projects/phase1_report/main.tex`
   - Compiler: `tectonic`
   - Page Count: 34 pages
   - Build Status: Clean build, 0 fatal errors, 0 undefined references, all figures scaled to full textwidth.
   - Mirrored Location: `/home/tk/projects/evryn/docs/phase1/main.pdf`

2. **Beamer Presentation (`Temporal_Causal_Knowledge_Phase1_Presentation.pdf`):**
   - Source: `/home/tk/projects/phase1_presentation/Temporal_Causal_Knowledge_Phase1_Presentation.tex`
   - Compiler: `tectonic`
   - Slide Count: 40 slides
   - Build Status: Clean build, 0 fatal errors, 0 overfull boxes.
   - Mirrored Locations:
     - `/home/tk/projects/evryn/docs/phase1/Temporal_Causal_Knowledge_Phase1_Presentation.pdf`
     - `/home/tk/projects/evryn/Temporal_Causal_Knowledge_Phase1_Presentation.pdf`
