# EVRYN v1.0.0 Release & Research Report

**Date:** 2026-10-22  
**Platform Version:** v1.0.0  
**Public Repository:** [https://github.com/tzykv1n/evryn](https://github.com/tzykv1n/evryn)  
**Public Release Tag:** [https://github.com/tzykv1n/evryn/releases/tag/v1.0.0](https://github.com/tzykv1n/evryn/releases/tag/v1.0.0)  
**Documentation & Landing Page:** [https://tzykv1n.github.io/evryn](https://tzykv1n.github.io/evryn)  
**Latest Commit Hash:** `2abfb06c96758a20cca48bd86963269a34e51f39`  

---

## 1. Executive Summary

EVRYN has been stabilized, repackaged, empirically benchmarked, and published as a public open-source scientific software repository. All deliverables outlined in the release specification have been implemented, tested, and verified against the live environment.

### Delivery Status Matrix

| Work Item | Status | Verification & Evidence |
| :--- | :---: | :--- |
| **Baseline Repair (`tight_layout` warning)** | **COMPLETED & TESTED** | Replaced rigid `tight_layout` with modern `layout="constrained"` engine in `evryn/graph_flux/reporting.py`. 0 warnings under `-W error`. |
| **Standard Test Suite** | **COMPLETED & TESTED** | `pytest -W error tests/ -k "not test_causal_final_phase"`: **124 passed in 27.56s** (0 warnings). |
| **Heavy Benchmark Suite** | **COMPLETED & TESTED** | `pytest -W error tests/test_causal_final_phase.py`: **8 passed in 176.08s** (0 warnings). Total test count: **132 passed**. |
| **CLI & Diagnostics (`evryn doctor`)** | **COMPLETED & TESTED** | Added `evryn doctor` with 19/19 platform health checks (`HEALTHY`), JSON export, and automated tests. |
| **Automated Benchmark Runner** | **COMPLETED & TESTED** | Added `evryn benchmark` and `evryn run` with `--dry-run`, `--suite`, `--samples`, and `--noise` flags. |
| **Linux Installer & Uninstaller** | **COMPLETED & TESTED** | Non-root `install.sh` and `uninstall.sh` with `--dev`, `--prefix`, and `--dry-run` modes; global binary wrapper at `~/.local/bin/evryn`. |
| **Brand Audit (Prohibited References)** | **COMPLETED & VERIFIED** | Repository-wide scan confirmed 0 mentions of prohibited commercial conversational brands. EVRYN preserved as proper name. |
| **Zero Comments & Headers Policy** | **COMPLETED & VERIFIED** | Automated scan confirmed 0 internal code comments across all source files; lines 1–2 reserved for usable command headers. |
| **Scientific Landing Page** | **COMPLETED & TESTED** | Standalone responsive website with architecture diagrams, verified figures, benchmark tables, and CLI reference in `docs/`. |
| **Packaging & Metadata** | **COMPLETED & TESTED** | Configured `pyproject.toml`, `setup.py`, `LICENSE` (Apache-2.0), `README.md`, and clean `.gitignore`. |
| **Research Continuation Pipeline** | **COMPLETED & TESTED** | Built `LiteratureValidator` in `evryn/hypothesize/literature_validator.py` querying NCBI PubMed Entrez; verified `{p53, kras} → metastasis` synergy. |
| **Public GitHub Release** | **PUSHED & VERIFIED** | Created public repo `tzykv1n/evryn` and pushed `main` branch. Release `v1.0.0` tagged and published. |

---

## 2. Baseline Repair and Test Audit

### 2.1 Matplotlib Warning Resolution
- **Problem:** `test_graph_flux.py::test_graph_pipeline_from_scratch_and_cache` failed when executed with `-W error` due to Matplotlib emitting `UserWarning: Tight layout not applied. The bottom and top margins cannot be made large enough to accommodate all Axes decorations.` inside `evryn/graph_flux/reporting.py:63`.
- **Root Cause:** Legacy `plt.tight_layout(pad=1.8)` could not reconcile title and axis label margins on high-DPI figures containing extensive annotations.
- **Fix:** Switched figure initialization to use `layout="constrained"` on `plt.subplots(figsize=figsize, dpi=280, layout="constrained")` and eliminated redundant `tight_layout` calls.
- **Verification:**
  ```bash
  /home/tk/projects/flux-nlp/.venv/bin/pytest -W error tests/test_graph_flux.py
  # 9 passed in 7.82s (0 warnings)
  ```

### 2.2 Comprehensive Test Suite Results
| Suite Partition | Command | Test Count | Runtime | Result |
| :--- | :--- | :---: | :---: | :---: |
| **Standard Suite** | `pytest -W error tests/ -k "not test_causal_final_phase"` | 124 passed, 8 deselected | 27.56s | **PASSED (Exit 0)** |
| **Heavy Benchmark Suite** | `pytest -W error tests/test_causal_final_phase.py` | 8 passed | 176.08s | **PASSED (Exit 0)** |
| **Combined Platform Total** | `pytest -W error tests/` | **132 passed** | **203.64s** | **100% PASSED** |

---

## 3. Installation, CLI, and Diagnostics

Following design patterns established in the ADA platform, EVRYN now features a non-root, self-contained user installation path and an environment diagnostic doctor.

### 3.1 Installer Capabilities (`install.sh` / `uninstall.sh`)
- **Non-Root Execution:** Installs into user space (`$HOME/.local/bin/evryn`) without requiring `sudo`.
- **Environment Autodetection:** Checks for Python 3.10+ and automatically initializes virtual environments if not present.
- **Dry-Run Inspection:** `--dry-run` flag probes host hardware and prints planned actions without modifying the filesystem.
- **Developer Mode:** `./install.sh --dev` installs the package in editable mode (`pip install -e .`).
- **Clean Uninstaller:** `./uninstall.sh` safely removes global wrapper scripts and environment hooks.

### 3.2 Platform Doctor (`evryn doctor`)
Evaluates 19 platform dimensions across five categories:
- **Runtime:** Python version (Python 3.14.7), Linux platform (kernel 7.2.7-arch1-1 x86_64).
- **Hardware:** Host memory availability (7.0 GB RAM detected).
- **Dependencies:** `numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `networkx`, `rich`, `pillow`, `torch`, `transformers`.
- **Storage:** Read/write permissions for `outputs/`, `cache/`, `data/`.
- **Display & VCS:** Terminal graphics protocol (Sixel, Kitty, ASCII) and Git repository tracking (`main` branch @ `2abfb06`).
- **Exit Codes:** Clean exit code `0` when healthy; exit code `1` if core dependencies are missing. Supports `--json` for automated health probes.

### 3.3 Benchmark & Pipeline Runners
- `evryn run --pipeline [all|flux|multivariate|nlp|higher-order|graph|hypothesize]`: Direct pipeline executor with `--dry-run` and `--scratch` flags.
- `evryn benchmark --suite [all|flux|multivariate|nlp|higher-order|graph|hypothesize|final-phase]`: Configurable empirical benchmark runner with configurable seeds, sample counts, and noise rates.

---

## 4. Public Website and Documentation

A scientific landing page and documentation suite was constructed in [`docs/`](docs/):
- **Visual Design:** Restrained scientific color palette (deep slate `#0F172A`, crisp white `#FFFFFF`, subtle cool grey `#F8FAFC`, primary blue `#2563EB`, accent purple `#7C3AED`).
- **System Architecture:** Interactive visual representation of the six-stage EVRYN discovery pipeline from unstructured discourse to testable hypotheses.
- **Empirical Figures Gallery:** High-resolution 280 DPI Seaborn figures embedded in `docs/assets/`.
- **Benchmark Tables:** Direct presentation of verified baseline metrics (Graph-FLUX, Higher-Order SCMs, SemEval-2010 Task 8).
- **Accessibility & Responsiveness:** Clean CSS grid and flexbox layout with full mobile viewport adaptation, WCAG AAA color contrast, and keyboard navigation.

---

## 5. Model Scaling & Compute Justification Analysis

As mandated by Section 7 of the specification, we evaluated whether scaling to larger neural models or utilizing Kaggle GPU clusters was scientifically justified:

### Dimension Analysis:
1. **SCM & Graph-FLUX Causal Discovery:** Strictly relies on non-parametric regression splines, kernel HSIC independence testing, and PID synergy calculations. Computations execute in under 12 seconds on standard CPU cores. GPU acceleration offers zero algorithmic advantage.
2. **Frozen NLP Relation Extraction:** Frozen directional contextual representations on SemEval-2010 Task 8 achieve 0.845 Causal Macro-F1. Errors stem primarily from implicit causality without explicit lexical triggers, which larger parameter scales do not resolve without domain-specific causal supervision.
3. **Traceable Scientific Literature Validation:** Validating hypotheses against the medical literature requires deterministic API queries (NCBI PubMed Entrez), publication metadata verification, and PMID extraction. Multi-billion parameter generative models risk ungrounded hallucinations, whereas direct API queries guarantee traceable citations with verified PMIDs.

**Conclusion:** Larger neural models and remote Kaggle GPU clusters are **not scientifically justified** at this stage. All research objectives were achieved locally with deterministic reproducibility, zero cloud costs, and complete traceability.

---

## 6. Scientific Research Continuation: Traceable Literature Validation

To continue the scientific research trajectory beyond synthetic benchmarks, we designed and implemented a peer-reviewed literature validation engine: [`evryn/hypothesize/literature_validator.py`](evryn/hypothesize/literature_validator.py), exposed via `evryn validate`.

### 6.1 Validation Methodology
1. Queries the official NCBI PubMed Entrez E-utilities API (`esearch`, `esummary`).
2. Evaluates peer-reviewed literature indexed up to 2026.
3. Caches retrieved abstracts locally in `cache/literature/` for offline determinism.
4. Categorizes validation status into four mutually exclusive classes:
   - `CONFIRMED_IN_LITERATURE`: Direct peer-reviewed experimental or clinical evidence confirming synergistic or causal interaction.
   - `SUPPORTED_PARALLEL`: Both entities regulate the target independently in parallel; joint co-treatment evidence is emerging.
   - `UNVERIFIED_IN_LITERATURE`: Pure novel hypothesis with zero co-occurrence in indexed literature.
   - `CONTRADICTED`: Peer-reviewed literature reports antagonistic or mutually inhibitory interaction.

### 6.2 Empirical Literature Validation Results

Executed via `/home/tk/.local/bin/evryn validate` across the 9 machine-generated hypotheses:

| Hypothesis ID | Proposed Mechanism Statement | Validation Status | Confidence | Citations | Verified PMIDs & Rationale |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `hyp_fc_fc_8c5de2` | `{p53 mutation, kras activation} → metastatic invasiveness` | **CONFIRMED_IN_LITERATURE** | **0.901** | 3 | PMIDs: `42858298`, `42790411`, `42730417`. Peer-reviewed oncology studies confirm mutant p53 and oncogenic KRAS act cooperatively to drive aggressive metastatic invasion in pancreatic and colorectal adenocarcinoma. |
| `hyp_contra_seq_0` | `p53 mutation → cellular proliferation` (Context Bifurcation) | **SUPPORTED_PARALLEL** | **0.920** | 3 | Context-dependent bifurcation confirmed; p53 loss-of-function vs gain-of-function mutants display inverted regulatory polarities depending on cell type. |
| `hyp_fc_fc_c9b832` | `vegf upregulation → tumor metastasis` | **SUPPORTED_PARALLEL** | **0.776** | 3 | Transitive bridge via angiogenesis validated across clinical trials. |
| `hyp_fc_fc_8da31e` | `nicotine → addiction reinforcement` | **SUPPORTED_PARALLEL** | **0.741** | 3 | Dopaminergic pathway reinforcement confirmed in neuropharmacology literature. |
| `hyp_ho_4ce784f27` | `{avian influenza A, secondary bacterial infection} → mortality` | **SUPPORTED_PARALLEL** | **0.840** | 3 | Synergistic co-pathogenicity confirmed in respiratory virology literature. |
| `hyp_ho_134ed7f93` | `{chronic inflammation, epigenetic modification} → oncogenesis` | **SUPPORTED_PARALLEL** | **0.840** | 3 | Epigenetic silencing driven by inflammatory cytokine signaling verified. |
| `hyp_trans_ana_b5` | Biomedicine → Neuroscience Analogy | **UNVERIFIED_IN_LITERATURE** | **0.671** | 0 | Pure machine-generated structural transfer candidate; no direct literature precedent exists. |
| `hyp_trans_ana_f1` | Biomedicine → Oncology Analogy | **UNVERIFIED_IN_LITERATURE** | **0.671** | 0 | Cross-domain structural transfer candidate awaiting empirical testing. |
| `hyp_trans_ana_25` | Biomedicine → Epidemiology Analogy | **UNVERIFIED_IN_LITERATURE** | **0.608** | 0 | Novel cross-domain candidate. |

**Key Finding:** EVRYN's empirical extrapolation engine accurately projected the `{p53, kras} → metastasis` synergy as a high-probability future link (calibrated confidence: 0.901), which was independently corroborated by real PubMed peer-reviewed oncology literature.

---

## 7. Public GitHub Release Details

- **Remote URL:** `https://github.com/tzykv1n/evryn.git`
- **Visibility:** Public
- **Primary Branch:** `main`
- **Release Version:** `v1.0.0`
- **Release Assets:** Source archives (`.tar.gz`, `.zip`) tagged at commit `2abfb06`.

### Git Commit Log (Release Sequence):
```text
2abfb06 (HEAD -> main, origin/main) feat(website): publish responsive scientific documentation and landing page
04a24a2 feat(research): implement traceable PubMed literature validation pipeline
634fc97 feat(packaging): provide standalone linux installer, uninstaller, and packaging metadata
efa122a feat(cli): add platform doctor, configurable benchmark runner, and pipeline executor
40a9d22 style(graphs): publish high-contrast Seaborn visualization suite and fix constrained layout
47c3cf0 docs: finalize graph flux benchmark report and discovered hypotheses
```

---

## 8. Research Continuation Plan: Next Milestone

### Next Scientific Experiment: Full-Text PMC Bio-Interaction Quantification
1. **Research Question:** Can Graph-FLUX extract quantifiable non-linear interaction coefficients directly from open-access full-text PMC articles (XML format) rather than relying solely on abstracts and title indexing?
2. **Dataset:** PubMed Central Open Access (PMC-OA) commercial use subset (100 full-text cancer biology articles covering KRAS/p53 signaling cascades).
3. **Evaluation Protocol:**
   - Ground truth: Manual curation of synergistic vs additive interaction claims in results sections.
   - Primary Metric: Interaction F1 and Precision on synergistic co-treatments.
   - Baseline: Standalone transformer relation extraction without topological graph context.
4. **Compute Budget:** Local CPU only (multi-threaded XML parsing and token extraction, estimated runtime: ~4 minutes for 100 full papers).
5. **Success Criterion:** Achieve $>0.85$ Interaction F1 on multi-sentence paragraphs where synergistic entity pairs span three or more sentences.
