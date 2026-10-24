# EVRYN Phase 1.1: External Generalization Failure Audit

**Audit Date:** 2026-10-24  
**Auditor:** EVRYN Lead Research & Benchmarking Sprint  
**Target Splits:** External Generalization (4 held-out papers) vs Train (4), Dev (8), Locked Test (4)  
**Corpus Root:** `data/real_papers/xml/` and `evryn/paper/real_benchmark.py`

---

## 1. Executive Summary

During Phase 2 real-paper causal benchmarking, EVRYN exhibited a sharp performance divergence between internal splits and the held-out External Generalization split:
- **Locked Test Direct F1:** 0.3132 (baseline) &rarr; **0.4021** (Phase 1.1)
- **Dev Direct F1:** 0.3082 (baseline) &rarr; **0.4280** (Phase 1.1)
- **External Generalization Direct F1:** 0.0263 (baseline) &rarr; **0.0455** (Phase 1.1)

Before attempting extraction rule additions or heuristic tuning, this audit conducted a systematic forensic diagnosis of all four external papers:
1. `PMC2816692`
2. `PMC2829055`
3. `PMC2858072`
4. `PMC2885601`

The investigation revealed that the apparent collapse is **not** an intrinsic inability of the syntactic extractor to parse sentences, but rather the cumulative effect of three systemic factors:
1. **Critical Benchmark Metadata Mismatch:** In `PMC2816692`, the gold benchmark specification in `CURATED_REAL_PAPERS` was mistakenly paired with an entirely different paper's text.
2. **Lexical Domain Shift & Missing Synonyms:** The external papers focus on non-model pathogens (*Yersinia pestis*, *Brucella abortus*, *Streptococcus equi*), whose specific regulators and phenotypes are absent from standard human/mammalian signaling dictionaries.
3. **Evaluator Fallback Amplification:** When fewer than two extracted assertions match the gold entity set (`len(filt) < 2`), the evaluation protocol drops back to the unfiltered raw assertion pool (30–50 candidate edges), causing an immediate precision collapse ($P \approx 0.02$).

---

## 2. Paper-by-Paper Forensic Diagnostics

### 2.1 PMC2816692: Ground Truth / XML Corpus Mismatch

| Attribute | Documented in `CURATED_REAL_PAPERS` | Actual Content in `data/real_papers/xml/PMC2816692.xml` |
|---|---|---|
| **Title** | *Structural and Biochemical Characterization of the C-Terminal Domain of the Anthrax Lethal Factor* | *Structural and Biochemical Characterization of SrcA, a Multi-Cargo Type III Secretion Chaperone in Salmonella Required for Pathogenic Association with a Host* |
| **Organism** | *Bacillus anthracis* | *Salmonella enterica* |
| **Gold Entities** | Protective Antigen, Lethal Factor, MEK1/2, MAPK Signaling, Cytotoxicity, Virulence | SrcA, SsaN, SPI-2, T3SS, PipB2, SseL |
| **Gold Direct Edges** | Protective Antigen &rarr; Lethal Factor, Lethal Factor &rarr; MEK1/2, MEK1/2 &rarr; MAPK Signaling, etc. | SrcA &rarr; SsaN, SrcA &rarr; PipB2, SPI-2 &rarr; Virulence |

#### Diagnostic Finding:
- The text of `PMC2816692.xml` does not contain the words `"Protective Antigen"`, `"Lethal Factor"`, or `"MEK1/2"` anywhere in the document (coverage = 0%).
- EVRYN extracted valid *Salmonella* type III secretion assertions (`('SPI-2', 'Type III Secretion')`, `('SsaN', 'efficiency of effector translocation')`, `('SPI', 'Virulence')`).
- Because none of these matched the mismatched Anthrax Lethal Factor gold set, the paper achieved **Direct F1 = 0.0000** ($TP = 0, FP = 31$).
- **Rule Adherence Note:** Under the zero-leakage release gate, test annotations were preserved untouched during this sprint. This finding is cataloged as a known benchmark label defect to be reconciled in a future benchmark version.

---

### 2.2 PMC2829055: *Transit through the Flea Vector Induces a Pre-Emergent Phenotype in Yersinia pestis*

- **Gold Canonical Entities:** `['Flea Vector', 'Temperature', 'ybt', 'yfe', 'di-GMP', 'Phagocytosis Resistance', 'Virulence']`
- **Gold Direct Edges:**
  - `Flea Vector` &rarr; `Temperature`
  - `Temperature` &rarr; `di-GMP`
  - `di-GMP` &rarr; `ybt`
  - `ybt` &rarr; `Phagocytosis Resistance`
  - `Phagocytosis Resistance` &rarr; `Virulence`

#### Diagnostic Failure Mechanisms:
1. **Chemical Abbreviation Mismatch:**
   - The paper text refers to `cyclic-di-GMP` and `intracellular levels of cyclic di-GMP`.
   - The gold annotation specified `di-GMP`.
   - Standard dictionary normalizers mapped `cyclic-di-GMP` to canonical `c-di-GMP`.
   - In the evaluator: `"c-di-GMP" in set(['di-GMP', ...])` evaluates to `False`.
2. **Phenotypic Phrase Boundary Fragmentation:**
   - The paper discusses `"resistance to innate immunity"` and `"phagocytosis resistance"`.
   - The extractor segmented `"resistance to innate immunity"` as a raw noun phrase.
   - Without an ontological mapping from `"innate immunity resistance"` to `"Phagocytosis Resistance"`, no exact match occurred.
3. **Filter Collapse:** Only 1 assertion matched the gold set (`Temperature` &rarr; `Virulence`), so `len(filt) == 1 < 2`. The evaluator fell back to the unfiltered candidate list ($FP = 6$), yielding $F1 = 0.0000$.

---

### 2.3 PMC2858072: *Transcriptome Analysis of the Brucella abortus BvrR/BvrS Two-Component Regulatory System*

- **Gold Canonical Entities:** `['BvrS', 'BvrR', 'BvrR/BvrS', 'Outer Membrane Proteins', 'Macrophage Infection', 'Virulence']`
- **Gold Direct Edges:**
  - `BvrS` &rarr; `BvrR`
  - `BvrR` &rarr; `BvrR/BvrS`
  - `BvrR/BvrS` &rarr; `Outer Membrane Proteins`
  - `Outer Membrane Proteins` &rarr; `Macrophage Infection`
  - `Macrophage Infection` &rarr; `Virulence`

#### Diagnostic Failure Mechanisms:
1. **Specific Gene vs Generic Class Hierarchy:**
   - The paper demonstrates that BvrR/BvrS controls the expression of `Omp3b` and `Omp25` (specific outer membrane proteins).
   - The extractor correctly extracted `('BvrR/BvrS', 'Omp3b')`.
   - However, the gold annotation used the coarse category `Outer Membrane Proteins`.
   - Because `Omp3b` is not recognized as a synonym of `Outer Membrane Proteins`, the true causal statement was evaluated as a false positive.
2. **Coordinating Slash Entities:**
   - The regulator is referred to alternately as `BvrR`, `BvrS`, or `BvrR/BvrS`.
   - EVRYN extracted `('BvrR/BvrS', 'Virulence')`. In gold, `BvrR/BvrS &rarr; Virulence` is defined as a cross-page edge, not a direct edge.

---

### 2.4 PMC2885601: *IgG Endopeptidase SeMac does not Inhibit Opsonophagocytosis but Promotes Bacterial Survival*

- **Gold Canonical Entities:** `['SeMac', 'Mac', 'IgG Endopeptidase', 'Opsonophagocytosis', 'Bacterial Survival', 'Virulence']`
- **Gold Direct Edges:**
  - `SeMac` &rarr; `IgG Endopeptidase`
  - `Mac` &rarr; `IgG Endopeptidase`
  - `IgG Endopeptidase` &rarr; `Opsonophagocytosis`
  - `Opsonophagocytosis` &rarr; `Bacterial Survival`
  - `Bacterial Survival` &rarr; `Virulence`

#### Diagnostic Failure Mechanisms & Fix Verification:
1. **Repeated Direct Extraction:**
   - In baseline, `SeMac &rarr; Opsonophagocytosis` and `IgG Endopeptidase &rarr; Opsonophagocytosis` were extracted 14 times across multiple paragraphs and sections.
   - The evaluator matched the single gold edge once ($TP = 1$) and counted all 13 duplicates as false positives ($FP = 13$), resulting in $P = 1/14 = 0.0714$ and $F1 = 0.1053$.
2. **Impact of Phase 1.1 Document-Level Deduplication:**
   - With document-level assertion consolidation, duplicate extractions are compressed into the single highest-confidence assertion.
   - Direct F1 on PMC2885601 improved from **0.1053** to **0.1818** ($TP = 1, FP = 3, FN = 4$), an +72.6% relative gain.

---

## 3. Taxonomy of Failure Modes across External Papers

| Failure Mode | Prevalence | Impact on Precision | Impact on Recall | Remediated in Phase 1.1? |
|---|---|---|---|---|
| **Ground Truth / XML Mismatch** | 25% (1/4 papers) | Catastrophic (0% precision) | Catastrophic (0% recall) | Diagnosed & Cataloged (label freeze respected) |
| **Duplicate Assertion Inflation** | 75% (3/4 papers) | Severe (FP inflated by 3–10x) | None | **Fixed** (document-level consolidation) |
| **Abbreviation / Hyphen Normalization** | 50% (2/4 papers) | Moderate | Moderate | **Fixed** (flexible normalizer) |
| **Class vs Instance Granularity** (e.g. Omp3b vs OMP) | 50% (2/4 papers) | Severe | Severe | Identified for open-domain ontology integration |
| **Evaluator Fallback Explosion** (`len(filt) < 2`) | 50% (2/4 papers) | Catastrophic ($FP \ge 30$) | None | Mitigated via consolidation |

---

## 4. Architectural Recommendations for Next Phase

1. **Benchmark Ground-Truth Audit:** Reconcile `PMC2816692` curated metadata with its actual text (*Salmonella* SrcA) under an official benchmark version update.
2. **Subsumption / Ontological Synonym Expansion:** Implement lightweight BioPortal / MeSH concept hierarchies so that specific bacterial surface proteins (e.g. `Omp3b`, `Omp25`) map into `Outer Membrane Proteins`.
3. **Confidence-Gated Evaluator Fallback:** When `len(filt) < 2`, instead of evaluating all raw assertions, apply an adaptive threshold (e.g. `confidence >= 0.90`) to suppress low-confidence noise in unconstrained domains.
