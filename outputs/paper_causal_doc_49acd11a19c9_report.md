# EVRYN Multi-Page Causal Evidence Report: (anonymous)

## 1. Document Provenance & Metadata

- **Document ID**: `doc_49acd11a19c9`
- **File Path**: `/home/tk/projects/evryn/data/multipage_papers/paper_01_egfr_mapk.pdf`
- **Title**: (anonymous)
- **Authors**: (anonymous)
- **DOI**: `10.1038/s41586-024-00101-x`
- **PMCID**: `PMC10821001`
- **PMID**: `38291001`
- **Page Count**: 5 pages
- **Parsed Sections**: 4
- **Segmented Sentences**: 13

## 2. Executive Causal Summary

| Metric | Count | Description |
| :--- | :--- | :--- |
| Extracted Causal Assertions | 8 | Sentence-level causal assertions identified |
| Measured Experimental Facts | 8 | Verified direct empirical observations |
| Speculative Hypotheses / Claims | 0 | Hedged claims in Discussion / Abstract |
| Disproven / Negated Relations | 0 | Explicitly refuted or non-significant links |
| Cross-Page Evidence Links | 18 | Transitive mechanisms spanning across page boundaries |
| Graph Network Entities | 8 | Canonical entity nodes in reconstructed causal network |
| Graph Network Edges | 26 | Direct and synthesized causal transitions |

## 3. Measured Experimental Facts (Empirical Grounding)

| Cause Entity | Effect Entity | Relation Type | Page | Section | Verbatim Evidence Quote |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EGFR** | **GRB2** | `UPREGULATES` | Page 2 | Page 2 — Methods & Early Signaling | "Phosphorylated EGFR recruits the adaptor protein GRB2 via its SH2 domain." |
| **GRB2** | **SOS1** | `UPREGULATES` | Page 2 | Page 2 — Methods & Early Signaling | "Subsequently, GRB2 binds the guanine nucleotide exchange factor SOS1 to form a stable binary sign..." |
| **SOS1** | **RAS** | `UPREGULATES` | Page 3 | Page 2 — Methods & Early Signaling | "Page 3 — Intermediate Cascade Membrane-anchored SOS1 stimulates RAS by catalyzing GDP-GTP exchange." |
| **RAS** | **RAF** | `UPREGULATES` | Page 3 | Page 2 — Methods & Early Signaling | "Active GTP-bound RAS directly binds and activates RAF serine/threonine kinase, initiating the cyt..." |
| **RAF** | **MEK** | `UPREGULATES` | Page 4 | Page 4 — Results & Kinase Phosphorylation | "In our experimental assays, active RAF phosphorylates MEK at dual serine residues Ser217 and Ser221." |
| **MEK** | **ERK** | `UPREGULATES` | Page 4 | Page 4 — Results & Kinase Phosphorylation | "Activated MEK directly phosphorylates ERK to elicit full enzymatic activation of MAPK." |
| **MEK** | **MAPK** | `UPREGULATES` | Page 4 | Page 4 — Results & Kinase Phosphorylation | "Activated MEK directly phosphorylates ERK to elicit full enzymatic activation of MAPK." |
| **EGFR** | **MAPK** | `UPREGULATES` | Page 5 | Page 5 — Discussion & Conclusions | "Consequently, EGFR signaling drives cellular proliferation through sequential MAPK activation." |

## 4. Cross-Page Synthesized Inferences (Multi-Page Evidence Flow)

| Source Entity | Intermediate Mediators | Target Entity | Mechanism | Page Span | Confidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EGFR** | GRB2 | **SOS1** | `transitive_chain` | Page 2 → Page 2 (Δ=0p) | 0.810 |
| **GRB2** | SOS1 | **RAS** | `transitive_chain` | Page 2 → Page 3 (Δ=1p) | 0.810 |
| **SOS1** | RAS | **RAF** | `transitive_chain` | Page 3 → Page 3 (Δ=0p) | 0.810 |
| **RAS** | RAF | **MEK** | `transitive_chain` | Page 3 → Page 4 (Δ=1p) | 0.810 |
| **RAF** | MEK | **ERK** | `transitive_chain` | Page 4 → Page 4 (Δ=0p) | 0.810 |
| **RAF** | MEK | **MAPK** | `transitive_chain` | Page 4 → Page 4 (Δ=0p) | 0.810 |
| **EGFR** | GRB2 -> SOS1 | **RAS** | `transitive_chain` | Page 2 → Page 3 (Δ=1p) | 0.729 |
| **GRB2** | SOS1 -> RAS | **RAF** | `transitive_chain` | Page 2 → Page 3 (Δ=1p) | 0.729 |
| **SOS1** | RAS -> RAF | **MEK** | `transitive_chain` | Page 3 → Page 4 (Δ=1p) | 0.729 |
| **RAS** | RAF -> MEK | **ERK** | `transitive_chain` | Page 3 → Page 4 (Δ=1p) | 0.729 |
| **RAS** | RAF -> MEK | **MAPK** | `transitive_chain` | Page 3 → Page 4 (Δ=1p) | 0.729 |
| **EGFR** | GRB2 -> SOS1 -> RAS | **RAF** | `transitive_chain` | Page 2 → Page 3 (Δ=1p) | 0.656 |
| **SOS1** | RAS -> RAF -> MEK | **ERK** | `transitive_chain` | Page 3 → Page 4 (Δ=1p) | 0.656 |
| **SOS1** | RAS -> RAF -> MEK | **MAPK** | `transitive_chain` | Page 3 → Page 4 (Δ=1p) | 0.656 |
| **GRB2** | SOS1 -> RAS -> RAF | **MEK** | `transitive_chain` | Page 2 → Page 4 (Δ=2p) | 0.630 |

## 5. Hypotheses, Speculative Claims & Negations

_No speculative hypotheses or negations detected._

## 6. Edge Provenance Map

| Edge | Direct / Inferred | Provenance Assertions | Pages |
| :--- | :--- | :--- | :--- |
| **EGFR** → **GRB2** | Direct (Sentence) | `asrt_doc_49_2_0001` | p.2 |
| **EGFR** → **MAPK** | Direct (Sentence) | `asrt_doc_49_5_0008` | p.5 |
| **EGFR** → **SOS1** | Inferred (Cross-Page) | `asrt_doc_49_2_0001, asrt_doc_49_2_0002` | p.2 |
| **EGFR** → **RAS** | Inferred (Cross-Page) | `asrt_doc_49_2_0001, asrt_doc_49_2_0002, asrt_doc_49_3_0003` | p.2, p.3 |
| **EGFR** → **RAF** | Inferred (Cross-Page) | `asrt_doc_49_2_0001, asrt_doc_49_2_0002, asrt_doc_49_3_0003, asrt_doc_49_3_0004` | p.2, p.3 |
| **EGFR** → **MEK** | Inferred (Cross-Page) | `asrt_doc_49_2_0001, asrt_doc_49_2_0002, asrt_doc_49_3_0003, asrt_doc_49_3_0004, asrt_doc_49_4_0005` | p.2, p.4 |
| **GRB2** → **SOS1** | Direct (Sentence) | `asrt_doc_49_2_0002` | p.2 |
| **GRB2** → **RAS** | Inferred (Cross-Page) | `asrt_doc_49_2_0002, asrt_doc_49_3_0003` | p.2, p.3 |
| **GRB2** → **RAF** | Inferred (Cross-Page) | `asrt_doc_49_2_0002, asrt_doc_49_3_0003, asrt_doc_49_3_0004` | p.2, p.3 |
| **GRB2** → **MEK** | Inferred (Cross-Page) | `asrt_doc_49_2_0002, asrt_doc_49_3_0003, asrt_doc_49_3_0004, asrt_doc_49_4_0005` | p.2, p.4 |
| **GRB2** → **ERK** | Inferred (Cross-Page) | `asrt_doc_49_2_0002, asrt_doc_49_3_0003, asrt_doc_49_3_0004, asrt_doc_49_4_0005, asrt_doc_49_4_0006` | p.2, p.4 |
| **GRB2** → **MAPK** | Inferred (Cross-Page) | `asrt_doc_49_2_0002, asrt_doc_49_3_0003, asrt_doc_49_3_0004, asrt_doc_49_4_0005, asrt_doc_49_4_0007` | p.2, p.4 |
| **SOS1** → **RAS** | Direct (Sentence) | `asrt_doc_49_3_0003` | p.3 |
| **SOS1** → **RAF** | Inferred (Cross-Page) | `asrt_doc_49_3_0003, asrt_doc_49_3_0004` | p.3 |
| **SOS1** → **MEK** | Inferred (Cross-Page) | `asrt_doc_49_3_0003, asrt_doc_49_3_0004, asrt_doc_49_4_0005` | p.3, p.4 |
| **SOS1** → **ERK** | Inferred (Cross-Page) | `asrt_doc_49_3_0003, asrt_doc_49_3_0004, asrt_doc_49_4_0005, asrt_doc_49_4_0006` | p.3, p.4 |
| **SOS1** → **MAPK** | Inferred (Cross-Page) | `asrt_doc_49_3_0003, asrt_doc_49_3_0004, asrt_doc_49_4_0005, asrt_doc_49_4_0007` | p.3, p.4 |
| **RAS** → **RAF** | Direct (Sentence) | `asrt_doc_49_3_0004` | p.3 |
| **RAS** → **MEK** | Inferred (Cross-Page) | `asrt_doc_49_3_0004, asrt_doc_49_4_0005` | p.3, p.4 |
| **RAS** → **ERK** | Inferred (Cross-Page) | `asrt_doc_49_3_0004, asrt_doc_49_4_0005, asrt_doc_49_4_0006` | p.3, p.4 |
| **RAS** → **MAPK** | Inferred (Cross-Page) | `asrt_doc_49_3_0004, asrt_doc_49_4_0005, asrt_doc_49_4_0007` | p.3, p.4 |
| **RAF** → **MEK** | Direct (Sentence) | `asrt_doc_49_4_0005` | p.4 |
| **RAF** → **ERK** | Inferred (Cross-Page) | `asrt_doc_49_4_0005, asrt_doc_49_4_0006` | p.4 |
| **RAF** → **MAPK** | Inferred (Cross-Page) | `asrt_doc_49_4_0005, asrt_doc_49_4_0007` | p.4 |
| **MEK** → **ERK** | Direct (Sentence) | `asrt_doc_49_4_0006` | p.4 |
| **MEK** → **MAPK** | Direct (Sentence) | `asrt_doc_49_4_0007` | p.4 |

---
*Report generated deterministically by EVRYN Multi-Page Causal Discovery Engine.*