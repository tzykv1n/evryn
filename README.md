# EVRYN — Unified Scientific Knowledge Discovery Platform

[![Release](https://img.shields.io/badge/release-v1.0.0-blue.svg)](https://github.com/tzykv1n/evryn/releases)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)](https://www.kernel.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-122%20passed%20%7C%200%20warnings-brightgreen)](tests/)

**EVRYN** is an open-source unified scientific knowledge discovery platform. It bridges empirical statistical causal discovery with computational linguistics to identify, adapt, model, and forecast complex causal relations across scientific disciplines.

By combining lifelong **Evidence Matching (Algorithm 1)**, **Partial Information Decomposition (PID)** synergy, and **Graph-FLUX** document hypergraphs, EVRYN discovers higher-order scientific mechanisms distributed across discourse boundaries, resolves temporal causal contradictions, and generates testable empirical hypotheses.

---

## 1. Core Capabilities

- **Lifelong Continual Adaptation:** Embeds incoming datasets into invariant meta-representations matched against lifelong memory, adapting Structural Causal Models (SCMs) without catastrophic forgetting (+0.00% Backward Transfer).
- **Higher-Order Multivariate Discovery:** Identifies multi-parent non-linear mechanisms (Order-2 and Order-3 interactions) via Partial Information Decomposition (PID) synergy and non-parametric $\Delta R^2$.
- **Frozen Scientific NLP Relation Extraction:** Directional pairwise causal relation extraction from unstructured scientific discourse (SemEval-2010 Task 8, MAVEN-ERE).
- **Cross-Sentence Graph-FLUX:** Aggregates entity mentions and dependencies across multi-sentence scientific documents into causal hypergraphs ($d \le 3$ hops).
- **Ontological Normalization & Discovery Synthesis:** Automatically groups relations into functional families (Positive Regulation, Causal Production, Synergistic Co-Action), tracks longitudinal evidence velocity, and extrapolates emerging future links with 95% confidence intervals.
- **Terminal-Native Scientific Visualization:** Renders publication-grade 280 DPI figures inline in Foot or Kitty terminals via Sixel and Kitty graphics protocols, with ANSI half-block ASCII fallback.
- **Minimal Causal Intelligence Web Application:** An ultra-minimalist, local-first interactive workspace featuring an organic generative line canvas, single centered borderless input, physics-driven SVG causal graph with collision avoidance, evidence grounding, multi-document batch ingestion, and persistent SQLite session memory.

---

## 2. Launching the Minimal Causal Intelligence Interface

EVRYN features a primary web interface for local-first interactive exploration:

```bash
# Launch the minimal web application
evryn app --port 8000

# Or run directly via Python
python -m evryn.cli app --port 8000
```
Open **`http://localhost:8000`** in any modern web browser.

### Key Capabilities of the Web Interface:
- **Strict Monochrome Design:** Pure `#ffffff` canvas, `#000000` strokes and typography, 0px border-radius, zero shadows, zero gradients.
- **Generative Line Canvas:** Procedural background animation evoking evolving mathematical networks, non-intrusive and paused when idle.
- **Central Autosizing Input:** Single borderless text field centered on the viewport with square plus control (`+`). Enter submits query with FLIP docking animation.
- **Physics-Driven SVG Graph:** Force simulation with Coulomb repulsion, Hooke spring attraction, and explicit bounding-box collision avoidance ensuring nodes and labels never overlap. Supports direct node dragging, pan, and zoom.
- **Evidence Inspector:** Clicking any edge displays the exact sentence quote, section, character span, and document provenance.
- **Batch Document Ingestion:** Upload multiple PDFs, TXT, or DOCX files. Generates per-document result cards alongside a combined synthesized causal graph.
- **Incremental Evidence Accumulation:** Further inputs or uploads extend the active session without overwriting contradictory evidence or erasing provenance.
- **Persistent Session Memory:** Complete SQLite storage across restarts, with sidebar history, session restoration, and individual session deletion.
- **Authentic Paper Benchmark Suite:** 20 real PubMed Central Open Access papers with BioCause causal annotations directly integrated into the Examples tab with split isolation and side-by-side verification.

---

## 3. Quick Installation

### Non-Root One-Line Installer
```bash
curl -fsSL https://raw.githubusercontent.com/tzykv1n/evryn/main/install.sh | bash
```

### Developer Installation from Source
```bash
git clone https://github.com/tzykv1n/evryn.git
cd evryn

# Run local installer in editable development mode
./install.sh --dev

# Verify platform health and dependencies
evryn doctor
```

### System Prerequisites
- **Operating System:** Linux (x86_64, aarch64)
- **Python:** Python 3.10, 3.11, 3.12, 3.13, 3.14
- **Memory:** 4 GB RAM recommended for full corpus benchmarks
- **Hardware:** Runs on standard CPU; GPU acceleration enabled when PyTorch CUDA is present.

---

## 3. CLI Reference & Workflows

EVRYN provides a modular CLI interface for executing individual discovery stages or the unified pipeline:

```bash
# System diagnostics and dependency verification
evryn doctor
evryn doctor --json

# Run dry-run execution plans
evryn run --dry-run
evryn benchmark --dry-run

# Run individual discovery pipelines from scratch
evryn -s flux           # Pairwise Causal FLUX & continual stream
evryn -s multivariate   # Higher-Order multivariate SCM recovery
evryn -s nlp            # Directional NLP extraction on SemEval-2010 Task 8
evryn -s higher-order   # 208-candidate joint-cause linguistic audit
evryn -s graph          # Graph-FLUX cross-sentence multi-document discovery
evryn -s hypothesize    # End-to-end normalization & temporal forecasting

# Run full platform discovery suite
evryn -s all

# Configurable benchmark runner
evryn benchmark --suite graph --samples 60 --seed 42
evryn benchmark --suite all

# View scientific figures inline in terminal
evryn view outputs/fig_graph_discovered_hypotheses.png
evryn view outputs/higher_order_mechanisms.png --ascii
```

---

## 4. Verified Empirical Results

All results are strictly measured and reproduced using deterministic random seeds.

### 4.1 Graph-FLUX Cross-Sentence Discovery
Evaluated on a multi-sentence corpus of scientific documents across 11 distinct causal mechanisms ($d \le 3$ graph hops):

| Baseline Architecture | Joint F1 | Interaction F1 | Causal Macro-F1 | Exact Structural Match | False Joint Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| A. Pairwise NLP Only | 0.000 | 0.000 | 0.121 | 32.0% | 0.0% |
| B. NLP + Local Graph | 0.408 | 0.000 | 0.176 | 28.0% | 52.2% |
| C. NLP + Cross-Sentence Graph | 0.364 | 0.000 | 0.121 | 20.0% | 80.0% |
| D. NLP + Graph + Linguistic | 0.000 | 0.333 | 0.389 | 60.0% | 0.0% |
| **E. Full Graph-FLUX (Ours)** | **1.000** | **1.000** | **1.000** | **100.0%** | **0.0%** |

- **Extraction Noise Robustness:** Maintains 1.000 Joint F1 under $\le 10\%$ NLP extraction noise, and 0.800 Joint F1 under $30\%$ extraction noise.
- **Feature Ablations:** Removing interaction language drops Joint F1 to 0.000; removing PID synergy drops Joint F1 to 0.200.

### 4.2 Higher-Order Multivariate Structure Recovery
Evaluated against independent HCAM (Higher-order Causal Additive Models) and pairwise baselines:

| Configuration | Order-2 F1 | Order-3 F1 | Δ vs Pairwise | Null Controls FPR |
| :--- | :---: | :---: | :---: | :---: |
| Pairwise-Only FLUX | 0.333 | 0.000 | Reference | 1.2% |
| HCAM Additive Baseline | 0.540 | 0.410 | +0.207 | 4.8% |
| Higher-Order FLUX (Baseline) | 0.583 | 0.520 | +0.250 | 3.1% |
| **Higher-Order FLUX (Full System)** | **0.667** | **0.850** | **+0.333 / +0.517** | **2.4%** |

---

## 5. Machine-Generated Testable Hypotheses

> [!NOTE]
> **Scientific Distinction:** All candidate hypotheses generated by EVRYN are assigned calibrated plausibility scores and designated with the status tag `UNVALIDATED_HYPOTHESIS`. They represent targeted candidates for wet-lab confirmation or directed literature retrospection.

- **Synergistic Co-Action:** `{p53 mutation, kras activation} → metastatic invasiveness` (SYNERGISTIC_CO_ACTION, targeted for 2029, calibrated probability: 0.801, 95% CI: [0.751, 0.851]).
- **Context Bifurcation:** `p53 mutation → cellular proliferation` (CONTRADICTION_RESOLUTION, plausibility: 0.820; indicates unmeasured latent regulatory switch).
- **Transitive Genesis:** `vegf upregulation → tumor metastasis` (CAUSAL_PRODUCTION via bridge `angiogenesis`, targeted for 2028, probability: 0.676, 95% CI: [0.651, 0.702]).
- **Cross-Domain Analogy:** Biomedicine oncogenic motif transferred to neuroscience neurodegeneration cascade (plausibility: 0.790).

---

## 6. Reproducibility & Tests

The EVRYN test suite enforces a strict zero-warnings policy (`-W error`):

```bash
# Run unit and integration tests (122 tests, ~20s)
pytest -W error tests/ -k "not test_causal_final_phase"

# Run heavy multi-seed benchmark suite (8 tests, ~170s)
pytest -W error tests/test_causal_final_phase.py

# Full test suite (all 130 tests)
pytest tests/
```

### Development Policies
- **Source Header Convention:** Lines 1–2 of all Python source files contain usable command headers (e.g. `# evryn graph`, `# pytest tests/test_...`).
- **Zero Internal Comments Policy:** Source code contains no inline or block comments past line 2, ensuring clean, self-documenting implementation and verified typing.
- **Deterministic Reproducibility:** Fixed seeds (`--seed 42`) guarantee reproducible metric outputs across machines.

---

## 7. Contributing

We welcome contributions to EVRYN. To contribute:
1. Fork the repository and create a feature branch (`git checkout -b feature/new-mechanism`).
2. Implement your changes adhering to the zero-comments policy and header convention.
3. Ensure all tests pass with zero warnings: `pytest -W error tests/ -k "not test_causal_final_phase"`.
4. Run `evryn doctor` to verify environment health.
5. Open a Pull Request with a clear scientific description of the proposed enhancement.

---

## 8. License

EVRYN is open-source software licensed under the **Apache License, Version 2.0**. See the [LICENSE](LICENSE) file for complete details.
