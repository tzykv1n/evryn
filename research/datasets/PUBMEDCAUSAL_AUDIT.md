# PubMedCausal Dataset Audit and Investigation Report

**Document Version:** 1.0.0  
**Date:** October 2026  
**Auditor:** EVRYN Core NLP & Causal Systems Group  
**Status:** Audit Complete — Integration Deferred Pending Public Release  

---

## 1. Executive Summary

This report evaluates the candidate dataset **PubMedCausal** for potential integration into EVRYN's causal discovery and evaluation benchmark suite. Following rigorous verification against official preprint records, public model hubs, and scientific code repositories, we determine that while the underlying annotation schema is scientifically valuable, **the dataset release artifacts and annotated corpus are currently not publicly accessible**.

In accordance with EVRYN's non-negotiable data provenance and reproducibility policies, we do not fabricate, synthesize, or substitute placeholder annotations for unreleased corpora. Integration of PubMedCausal is formally cataloged and will proceed immediately upon its verified public data release.

---

## 2. Bibliographic Identification & Scope

- **Title:** *PubMedCausal: A Span-Level Annotated Corpus for Causal Relation Extraction in Biomedical Text*
- **Authors:** Kunle-John, A., et al.
- **Preprint Identifier:** arXiv:2605.28363 [cs.CL]
- **Target Domain:** Full-text biomedical scientific literature indexed in PubMed Central (PMC).
- **Primary Task:** Span-level causal relation extraction with trigger identification, cause argument detection, and effect argument detection.

---

## 3. Schema and Annotation Structure Analysis

Based on the published technical specification in arXiv:2605.28363, PubMedCausal defines a three-tier annotation schema:

1. **Causal Trigger Spans:** Explicit lexical operators indicating causal directionality (e.g., *"leads to"*, *"triggers"*, *"attenuates"*, *"is mediated by"*).
2. **Cause Argument Spans:** Upstream biomolecular entities, treatments, mutations, or pathological conditions.
3. **Effect Argument Spans:** Downstream phenotypic responses, gene expression shifts, cellular responses, or clinical outcomes.
4. **Scope Boundaries:** Sentence-bounded relations alongside multi-clause compound assertions.

### Schema Comparison with Existing EVRYN Benchmarks

| Feature | BioCause (NaCTeM) | SciERC (UW/AI2) | PubMedCausal (Planned) | EVRYN Multi-Page Benchmark |
| :--- | :--- | :--- | :--- | :--- |
| **Causal Argument Spans** | Standoff `Cause` / `Effect` | N/A (Relational) | Span `Cause` / `Effect` | Span + Normalized Canonical Entity |
| **Trigger Spans** | Standoff `Causality` trigger | N/A | Explicit Trigger Span | Lexical Anchor + Syntactic Head |
| **Cross-Sentence Scope** | Present (~22% of relations) | Discourse coref | Limited (~8% multi-clause) | Cross-section & Cross-page |
| **Transitive Path Labels** | Not explicit | Not explicit | Not annotated | Explicitly labeled as Inferred |
| **License Type** | CC BY-NC-SA 3.0 | CC BY-NC 4.0 | Planned Open Research | CC BY 4.0 Open Benchmark |

---

## 4. Accessibility and Availability Audit

Our automated retrieval and repository audit checked the following distribution points:

1. **Zenodo Research Archives:** Searched DOI index and `PubMedCausal` keyword query. (Result: 0 records found).
2. **HuggingFace Hub (`datasets/`):** Queried Hugging Face dataset registry for `pubmedcausal`, `pubmed-causal`. (Result: No public repository).
3. **GitHub / Git Code Repositories:** Searched public repositories for `PubMedCausal`. The arXiv paper explicitly notes in Section 7 (Data Availability):
   > *"The annotated PubMedCausal corpus, extraction scripts, and baseline checkpoints will be made publicly available at [repository link to be added upon peer-reviewed acceptance]."*
4. **Direct Authors / Institutional Pages:** Confirmed no pre-release tarball or FTP dump is presently hosted.

---

## 5. Decision and Integration Roadmap

- **Audit Outcome:** DEFERRED.
- **Reason:** Upstream artifacts are not yet released to the public domain. Fabricating annotations or using unverified third-party scrapes would violate EVRYN's strict non-fabrication directive.
- **Adapter Readiness:** The EVRYN dataset ingestion framework (`evryn.datasets.biocause` and `evryn.datasets.pmc_oa`) provides the exact structural interface (`cause_span`, `effect_span`, `trigger_span`, `offsets`) required by PubMedCausal. As soon as the authors release the dataset upon peer review acceptance, an adapter (`evryn.datasets.pubmedcausal.PubMedCausalDataset`) will be activated with zero disruption to the existing pipeline.
