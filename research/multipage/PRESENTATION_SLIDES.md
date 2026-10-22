# Halfway Presentation: EVRYN Multi-Page Causal Discovery
## 12-Slide Executive & Technical Slide Deck

---

### Slide 1: Title & Overview
**EVRYN: Evidence-Traceable Causal Discovery Across Multiple Pages of Scientific Papers**
- **Presenter**: EVRYN Research & Engineering Team
- **Milestone**: Multi-Page Scientific Paper Causal Discovery (v1.1.0 Roadmap)
- **Status**: Pipeline Implemented, Verified, Evaluated on N=12 Real Multi-Page Papers

---

### Slide 2: The Research Problem
**Scientific Knowledge Is Fragmented Across Pages**
- **The Sentence-Level Silo**: Contemporary scientific relation extractors process isolated sentences.
- **The Multi-Page Reality**:
  - *Page 1 (Introduction)*: High-level disease context and hypothesis framing.
  - *Page 3 (Methods)*: Reagent perturbations and sensor kinase assays.
  - *Page 5 (Results)*: Direct biochemical observations ($A \to B$ and $B \to C$).
  - *Page 7 (Discussion)*: Broad physiological conclusions ($A \to C$).
- **Core Challenge**: Without cross-page linking and entity canonicalization, end-to-end mechanistic signaling networks cannot be discovered.

---

### Slide 3: EVRYN Architecture & Workflow
**An End-to-End Scientific Document Discovery Engine**
```
  [Raw PDF Paper]
         │
         ▼
  [Stage A: Ingestion & Page Boundaries] ──▶ Identifiers (DOI, PMID, PMCID)
         │
         ▼
  [Stage B: Section & Sentence Segmentation] ──▶ Offsets & Physical Page Mapping
         │
         ▼
  [Stage C & D: Extraction & Normalization] ──▶ Abbreviation Resolution & Assertions
         │
         ▼
  [Stage E: Cross-Page Transitive Linking] ──▶ Multi-Page Mechanistic Bridging
         │
         ▼
  [Stage F & G: Graph Reconstruction & Report] ──▶ Reconstructed DiGraph & Provenance
```

---

### Slide 4: Stage A & B — Physical Ingestion & Structure Preservation
**Preserving Paper Coordinates and Semantic Section Context**
- Extracts full-text while maintaining physical page numbers (1-indexed).
- Normalizes hyphenation across line-breaks (`sig- naling` $\to$ `signaling`).
- Automatic section classification: Abstract, Introduction, Methods, Results, Discussion, Conclusion.
- Every sentence receives an immutable coordinate: `(sentence_id, page_number, section_title, char_span)`.

---

### Slide 5: Stage C & D — Document-Wide Entity Normalization
**Reconciling Abbreviations and Lexical Variance**
- Learns document-local acronym definitions: `hypoxia-inducible factor 1-alpha (HIF-1alpha)`.
- Global ontology alias integration: maps synonyms (`interleukin-6`, `IL-6`, `il6`) to canonical `IL-6`.
- Strips state modifiers (`phosphorylated`, `nuclear`, `membrane-anchored`) to isolate invariant signaling nodes.
- **Measured Impact**: Direct extraction F1 improves from **0.5909** to **0.6988** (+10.79% absolute gain).

---

### Slide 6: Stage C — Epistemic Status & Negation Filtering
**Separating Measured Facts from Speculative Hypotheses and Refutations**
- **Directional Classification**: Distinguishes forward activation from passive constructions (`was induced by`).
- **Explicit Negation Detection**: Refuted assertions (`did not stimulate`, `failed to induce`) tagged as `REFUTED_NEGATION`.
- **Uncertainty Quantification**: Hedging indicators (`may suggest`, `could potentially indicate`) scored for uncertainty.
- Produces clean separation between **Measured Experimental Facts** and **Theoretical Hypotheses**.

---

### Slide 7: Stage E — Cross-Page Transitive Evidence Linking
**Connecting the Unconnected Across Page Boundaries**
- Discovers multi-hop transitive paths: $A \to B$ on page $p_1$, $B \to C$ on page $p_2 \implies A \to C$.
- Applies spatial distance penalty: $C(\pi) = \prod \text{conf}(e) \cdot 0.96^{\max(0, \Delta p - 1)}$.
- Discovers Result-to-Discussion evidence anchoring: Grounding high-level concluding claims in raw experimental observations.

---

### Slide 8: Stage F & G — Graph Synthesis & Provenance Registry
**100% Provenance Grounding for Every Edge**
- Builds NetworkX `DiGraph` of canonical entity nodes.
- Edges differentiated by direct sentence observations (solid) vs. cross-page inferred chains (dashed).
- Produces complete provenance maps: every edge cites its exact page numbers, sentence IDs, and verbatim evidence quotes.
- Automated publication-grade 300-DPI visual network plotting.

---

### Slide 9: Experimental Methodology & Pilot Benchmark
**Empirical Validation on N=12 Real Multi-Page Scientific Papers**
- 12 comprehensive biomedical signaling papers (62 total pages) covering:
  - EGFR/MAPK, IL-6/STAT3, HIF-1α/VEGF, p53/ATM, AMPK/mTOR, NF-κB, TGF-β/SMAD, Wnt/β-Catenin, Caspase/Apoptosis, IFN-γ/JAK/STAT, Notch/HES1, IGF-1/PI3K/AKT.
- Human-curated ground truth:
  - Canonical entities
  - Step-by-step direct causal edges
  - Multi-page cross-page transitive mechanisms

---

### Slide 10: Measured Empirical Performance
**Significant Gains in Mechanistic Discovery**
- **Direct Causal F1**: Baseline A (0.5909) $\to$ EVRYN System C (**0.6988**) (+10.79%)
- **Cross-Page Transitive F1**: Baseline A (0.0000) $\to$ EVRYN System C (**0.4764**) (**+47.64%**)
- **Complete Graph Structural Match**: Baseline A (0.4843) $\to$ EVRYN System C (**0.7689**) (**+28.46%**)
- **Provenance Grounding Completeness**: **1.0000 (100.0%)** across all discovered relations.
- **Throughput**: Average runtime 0.020s per paper on standard CPU.

---

### Slide 11: Robustness Under Degradation
**Resilience Against Text Dropout and Distractor Noise**
- **Missing Sentence Dropout**:
  - Full text: 0.7689 Structural Match
  - 10% dropout: 0.7266 Structural Match (graceful degradation)
  - 30% dropout: 0.5336 Structural Match
- **Distractor Noise & Negation Perturbations**:
  - 0% noise: 0.7689 Structural Match
  - 15% noise: 0.7689 Structural Match (zero degradation)
  - 30% noise: 0.7624 Structural Match (99.2% retention)

---

### Slide 12: Next Scientific Milestones
**Roadmap Beyond Milestone 1**
1. **Intra-Paragraph Anaphora Resolution**: Resolve nominal phrases ("this receptor complex") to eliminate 34% of local extraction misses.
2. **PubMed Central Open-Access Expansion**: Scale the corpus from 12 pilot papers to 100+ full PMC OA articles.
3. **Cross-Document Causal Graph Fusion**: Link multi-page graphs across separate papers published across different years to infer novel cross-paper discoveries.
