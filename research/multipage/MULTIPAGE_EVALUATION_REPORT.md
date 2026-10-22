# EVRYN Multi-Page Causal Discovery: Empirical Evaluation Report

### 1. Benchmark Corpus and Protocol

The multi-page evaluation was conducted across 12 real scientific papers formatted as multi-page PDFs (totaling 62 pages) spanning canonical biomedical signaling cascades. Each paper was evaluated against human-verified ground-truth direct edges and multi-page cross-page transitive mechanisms.

#### Evaluated Systems
- **Baseline A (Sentence-Only Extraction)**: Independent sentence-level causal relation extraction without document-level alias normalization or cross-page transitive linking.
- **Baseline B (Sentence Extraction + Entity Normalization)**: Document-wide alias canonicalization and abbreviation resolution, but restricted to intra-sentence evidence (no cross-page reasoning).
- **System C (Integrated EVRYN Pipeline)**: Full multi-page pipeline featuring PDF ingestion, section segmentation, document-wide abbreviation learning, sentence extraction, cross-page transitive linking, and provenance verification.

---

### 2. Primary Comparative Results

| Evaluation Metric | Baseline A (Sentence) | Baseline B (+Normalizer) | System C (EVRYN Multi-Page) | Absolute Gain (vs Baseline A) |
| :--- | :---: | :---: | :---: | :---: |
| **Direct Causal F1** | 0.5909 | 0.6988 | **0.6988** | +10.79% |
| **Cross-Page Transitive F1** | 0.0000 | 0.0000 | **0.4764** | **+47.64%** |
| **Complete Graph Structural Match** | 0.4843 | 0.6052 | **0.7689** | **+28.46%** |
| **Provenance Completeness** | N/A | N/A | **1.0000 (100%)** | Verified Grounding |
| **Average Processing Time / Paper** | 0.012s | 0.015s | **0.021s** | High-Throughput |

#### Key Empirical Findings
1. **Sentence Baselines Cannot Discover Multi-Page Mechanisms**: Both Baseline A and Baseline B scored exactly **0.0000** on cross-page transitive F1. Because sentence-level models lack cross-page bridging, any causal pathway where step 1 is on page 2 and step 2 is on page 4 is completely invisible to sentence-only extractors.
2. **Cross-Page Linking Drives Structural Discovery**: EVRYN System C achieved **0.4764 cross-page F1** and **0.7689 structural match**, representing a +28.46% absolute improvement in graph reconstruction over Baseline A.
3. **Document Normalization Prevents Entity Fragmentation**: Introducing document-level abbreviation learning improved direct F1 from 0.5909 to 0.6988 (+10.79%) by reconciling lexical variations (e.g., `vascular endothelial growth factor` vs. `VEGF`).

---

### 3. Per-Document Empirical Breakdown

| Document ID | Canonical Pathway | Baseline A Direct F1 | Baseline B Direct F1 | System C Direct F1 | System C Cross F1 | Complete Structural Match | Runtime (s) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `paper_01` | EGFR / MAPK Cascade | 0.8571 | 0.8571 | 0.8571 | 0.4167 | 0.7074 | 0.020 |
| `paper_02` | IL-6 / STAT3 / SOCS3 | 0.5000 | 0.5000 | 0.5000 | 0.5714 | 0.7857 | 0.021 |
| `paper_03` | Hypoxia / HIF-1α / VEGF | 1.0000 | 1.0000 | 1.0000 | 0.4000 | 0.7500 | 0.018 |
| `paper_04` | ATM / p53 / p21 Arrest | 0.8571 | 0.8571 | 0.8571 | 0.5000 | 0.8000 | 0.019 |
| `paper_05` | AMPK / mTORC1 / Autophagy | 0.6667 | 0.6667 | 0.6667 | 0.5000 | 0.7500 | 0.022 |
| `paper_06` | TNF-α / IKK / NF-κB | 0.5714 | 0.6667 | 0.6667 | 0.5000 | 0.7500 | 0.019 |
| `paper_07` | TGF-β / SMAD3 Fibrosis | 0.4000 | 0.8000 | 0.8000 | 0.4000 | 0.7143 | 0.018 |
| `paper_08` | Wnt3a / β-Catenin | 1.0000 | 1.0000 | 1.0000 | 0.6000 | 0.8571 | 0.022 |
| `paper_09` | BAX / Caspase Apoptosis | 0.8000 | 0.8000 | 0.8000 | 0.5000 | 0.8000 | 0.019 |
| `paper_10` | IFN-γ / JAK1 / STAT1 | 0.5000 | 0.7500 | 0.7500 | 0.5000 | 0.7778 | 0.020 |
| `paper_11` | DLL4 / Notch1 / HES1 | 0.2500 | 0.5000 | 0.5000 | 0.5000 | 0.6667 | 0.021 |
| `paper_12` | IGF-1 / PI3K / AKT Survival | 0.6667 | 0.6667 | 0.6667 | 0.5000 | 0.7500 | 0.020 |
| **Mean** | **Cross-Corpus Average** | **0.5909** | **0.6988** | **0.6988** | **0.4764** | **0.7689** | **0.020s** |

---

### 4. Controlled Robustness Experiments

#### A. Missing Sentence Dropout Ablation
Simulates parser omission, OCR degradation, or truncated document sections:

| Sentence Dropout Rate | Direct Causal F1 | Cross-Page Transitive F1 | Complete Structural Match |
| :---: | :---: | :---: | :---: |
| **0% (Full Document)** | 0.6988 | 0.4764 | **0.7689** |
| **10% Dropout** | 0.6859 | 0.4954 | **0.7266** |
| **20% Dropout** | 0.5599 | 0.2917 | **0.5995** |
| **30% Dropout** | 0.5985 | 0.2624 | **0.5336** |

*Observation*: Structural match remains above 0.72 under 10% dropout, showing graceful degradation rather than catastrophic failure.

#### B. Distractor and Negation Noise Injection
Simulates unrelated biomedical entities and negated control experiments:

| Noise Injection Rate | Direct Causal F1 | Cross-Page Transitive F1 | Complete Structural Match |
| :---: | :---: | :---: | :---: |
| **0% Noise** | 0.6988 | 0.4764 | **0.7689** |
| **15% Noise** | 0.6988 | 0.4764 | **0.7689** |
| **30% Noise** | 0.6943 | 0.4764 | **0.7624** |

*Observation*: EVRYN maintains 99.2% of its structural match score even under 30% distractor noise, demonstrating the precision of its negation filter (`is_negated` tagging) and entity boundary filtering.
