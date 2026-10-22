# EVRYN Multi-Page Causal Discovery: Reproducibility Protocol

### 1. Environment & Prerequisite Verification

All benchmarks and experiments in EVRYN are designed to run deterministically on ordinary Linux hardware without requiring GPU resources or proprietary API keys.

#### Environment Verification
Run the EVRYN diagnostic doctor to verify all runtime dependencies, storage permissions, and Git health:
```bash
evryn doctor
# Alternatively via virtual environment:
/home/tk/projects/flux-nlp/.venv/bin/python -m evryn.cli doctor
```

Verified environment baseline:
- **Operating System**: Linux 7.2.7-arch1-1 (x86_64)
- **Python**: 3.14.7
- **Key Dependencies**: `numpy 2.5.3`, `scipy 1.18.1`, `pandas 3.0.6`, `scikit-learn 1.9.1`, `matplotlib 3.11.2`, `seaborn 0.13.2`, `networkx 3.6.1`, `pypdf 6.21.2`, `reportlab 5.1.0`, `rich`
- **CPU & Memory**: Verified on 7.0 GB RAM Linux host.

---

### 2. Multi-Page Paper Pipeline Commands

#### A. Document Inspection
Inspect PDF metadata, extracted identifiers (DOI, PMID, PMCID), page boundaries, and section segmentation:
```bash
evryn paper inspect data/multipage_papers/paper_01_egfr_mapk.pdf
```

#### B. Sentence-Level Causal Extraction
Extract sentence assertions with page numbers, confidence, relation subtype, and negation/uncertainty status:
```bash
evryn paper extract data/multipage_papers/paper_01_egfr_mapk.pdf
```

#### C. Causal Graph Reconstruction
Reconstruct the directed causal network combining direct sentence evidence and cross-page transitive links:
```bash
evryn paper graph data/multipage_papers/paper_01_egfr_mapk.pdf
```

#### D. Full Evidence Report & Visualization
Generate complete Markdown report, JSON evidence registry, and 300-DPI publication graph visualization:
```bash
evryn paper report data/multipage_papers/paper_01_egfr_mapk.pdf --output-dir outputs
```

---

### 3. Comprehensive Benchmark & Robustness Suites

#### A. Automated Benchmark Execution
Execute the automated multi-page evaluation across all 12 reference scientific papers:
```bash
evryn benchmark --suite multi-page --seed 42 --output-dir outputs
```

#### B. Dry-Run Plan Inspection
Inspect the scheduled benchmark plan without modifying files or executing computations:
```bash
evryn benchmark --suite multi-page --dry-run
```

#### C. Standalone Python Evaluator
Run the evaluation suite programmatically:
```python
import glob, json
from evryn.paper import PaperIngestion, PaperSegmenter, PaperBenchmarkEvaluator
from evryn.paper.robustness import PaperRobustnessExperiments

ingest = PaperIngestion()
segmenter = PaperSegmenter()
evaluator = PaperBenchmarkEvaluator("outputs")

docs, gts = [], []
for pdf in sorted(glob.glob("data/multipage_papers/*.pdf")):
    with open(pdf.replace(".pdf", "_ground_truth.json")) as f:
        gts.append(json.load(f))
    docs.append(segmenter.segment_document(ingest.ingest_pdf(pdf)))

summary = evaluator.run_suite(docs, gts)
rob = PaperRobustnessExperiments(evaluator, "outputs", seed=42)
rob.run_all_robustness(docs, gts)
```

---

### 4. Verification Suites & Strict Zero-Warnings Policy

Run test suites under strict `-W error` mode:

1. **Paper Pipeline Unit & Integration Suite**:
   ```bash
   /home/tk/projects/flux-nlp/.venv/bin/pytest -W error tests/test_paper_pipeline.py
   ```
2. **Platform CLI Test Suite**:
   ```bash
   /home/tk/projects/flux-nlp/.venv/bin/pytest -W error tests/test_cli_commands.py
   ```
3. **Complete Standard Platform Suite**:
   ```bash
   /home/tk/projects/flux-nlp/.venv/bin/pytest -W error tests/ -k "not test_causal_final_phase"
   ```
4. **Heavy Causal Final Phase Suite**:
   ```bash
   /home/tk/projects/flux-nlp/.venv/bin/pytest -W error tests/test_causal_final_phase.py
   ```
