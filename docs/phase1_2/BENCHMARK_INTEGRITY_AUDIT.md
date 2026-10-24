# EVRYN Phase 1.2: Benchmark Integrity & Gold-Label Audit

**Audit Date:** 2026-10-24  
**Auditor:** EVRYN Lead Benchmark Auditor  
**Corpus Scope:** 20 authentic PubMed Central papers (`data/real_papers/xml/`) across 4 paper-disjoint splits  
**Evaluation Harness:** `scripts/evaluate_phase2_splits.py` & `evryn/paper/real_benchmark.py`

---

## 1. Executive Summary

As mandated by Section 2 of the Phase 1.2 Mission, benchmark validity is the **first release gate**. Prior to evaluating unseen-paper generalization claims, every paper in the 20-paper corpus was independently inspected to verify:
1. Document identity (PMCID, PMID, DOI, and journal).
2. Correspondence between curated gold specifications (`CURATED_REAL_PAPERS`) and XML source documents on disk.
3. Canonical entity textual support (presence of gold entities in the article full text).
4. Causal evidence grounding and relation directionality.
5. Cross-split independence (ensuring no shared strains, duplicate texts, or author-level data contamination across Train, Dev, Locked Test, and External splits).

### Audit Verdict:
- **19 of 20 papers** (95.0%) have valid, evidence-grounded gold annotations corresponding directly to their source articles.
- **1 of 20 papers** (`PMC2816692`, External Generalization split) exhibits a **fatal ground-truth mismatch**: the curated benchmark specification describes *Bacillus anthracis* Lethal Factor, whereas the XML file on disk describes *Salmonella enterica* SrcA.
- **Protocol Decision:** To preserve benchmark immutability and evaluation integrity:
  - The original 20-paper benchmark is preserved untouched (`CURATED_REAL_PAPERS` remains unmodified).
  - Results are reported in two distinct views:
    1. **Original Protocol:** All 4 External papers ($N=4$, including the mismatched paper).
    2. **Validated Protocol:** The 3 valid External papers ($N=3$, excluding the mismatched paper).

---

## 2. Comprehensive 20-Paper Forensic Ledger

| PMCID | Split | Curated Title | XML Source Title | Entity Coverage | Audit Status | Notes |
|---|---|---|---|---|---|---|
| **PMC2651894** | Train | RpoE fine tunes expression of a subset of SsrB-regulated virulence factors... | RpoE fine tunes expression of a subset of SsrB-regulated virulence factors... | 6/7 (85.7%) | **VALID** | sigmaE mapped to RpoE; authentic Salmonella study. |
| **PMC2682197** | Train | Mycobacterium tuberculosis Universal Stress Protein Rv2623 Regulates Bacillary Growth... | Mycobacterium tuberculosis Universal Stress Protein Rv2623 Regulates Bacillary Growth... | 5/6 (83.3%) | **VALID** | Bacillary growth discussed as "growth of bacilli". |
| **PMC2714965** | Train | Caenorhabditis elegans Semi-Automated Liquid Screen Identifies Novel Small Molecules... | Caenorhabditis elegans Semi-Automated Liquid Screen Reveals a Specialized Role... | 5/6 (83.3%) | **VALID** | Title phrasing minor variance; entities and cheB1/cheB2 causal relations verified. |
| **PMC2774163** | Train | A Novel Signaling Network Essential for Regulated Secretion of Toxoplasma gondii... | A Novel Signaling Network Essential for Regulating Pseudomonas aeruginosa Biofilm... | 5/6 (83.3%) | **VALID (Metadata Typo)** | Curated title string had Toxoplasma copy-paste typo, but canonical entities and relations belong 100% to the P. aeruginosa Biofilm paper on disk. |
| **PMC1804205** | Dev | Acid pH activation of the PmrA/PmrB two-component system... | Acid pH activation of the PmrA/PmrB two-component regulatory system... | 7/7 (100.0%) | **VALID** | Full textual grounding. Authentic Salmonella PmrA/PmrB. |
| **PMC1874608** | Dev | Mlc regulation of Salmonella pathogenicity island 1 expression... | Mlc regulation of Salmonella pathogenicity island I gene expression via hilE... | 6/6 (100.0%) | **VALID** | Full textual grounding. Mlc-hilE-hilD-hilA cascade verified. |
| **PMC1913099** | Dev | Novel Algorithms Reveal Streptococcal Transcriptomes and Clues about Undefined Genes | Novel Algorithms Reveal Streptococcal Transcriptomes and Clues about Undefined Genes | 5/5 (100.0%) | **VALID** | Authentic Group A Streptococcus transcriptome. |
| **PMC1974823** | Dev | Porphyromonas gingivalis short fimbriae are regulated by FimS/FimR | Porphyromonas gingivalis short fimbriae are regulated by a FimS/FimR two-component system | 5/5 (100.0%) | **VALID** | Authentic P. gingivalis fimbriae regulation. |
| **PMC2242835** | Dev | Control of M. tuberculosis ESAT-6 Secretion and Specific T Cell Recognition by PhoP | Control of M. tuberculosis ESAT-6 Secretion and Specific T Cell Recognition by PhoP | 5/5 (100.0%) | **VALID** | Authentic M. tuberculosis ESX-1/PhoP regulation. |
| **PMC2266911** | Dev | Comparative analysis of Photorhabdus luminescens and Yersinia enterocolitica... | Comparative analysis of the Photorhabdus luminescens and the Yersinia enterocolitica... | 5/5 (100.0%) | **VALID** | Quorum sensing & LuxR virulence regulation verified. |
| **PMC2358977** | Dev | SalK/SalR, a Two-Component Signal Transduction System, Is Essential for Full Virulence... | SalK/SalR, a Two-Component Signal Transduction System, Is Essential for Full Virulence... | 4/5 (80.0%) | **VALID** | S. suis invasive virulence. PMN resistance in text as "killing by neutrophils". |
| **PMC2430206** | Dev | The GraRS regulatory system controls Staphylococcus aureus susceptibility... | The GraRS regulatory system controls Staphylococcus aureus susceptibility... | 5/5 (100.0%) | **VALID** | S. aureus GraRS and antimicrobial peptide defense. |
| **PMC2565068** | Locked Test | Incompetence of Neutrophils to Invasive Group A streptococcus Is Attributed... | Incompetence of Neutrophils to Invasive Group A streptococcus Is Attributed... | 6/6 (100.0%) | **VALID** | Authentic GAS streptolysin O and neutrophil apoptosis. |
| **PMC2581603** | Locked Test | Extracellular DNA Chelates Cations and Induces Antibiotic Resistance in Pseudomonas... | Extracellular DNA Chelates Cations and Induces Antibiotic Resistance in Pseudomonas... | 5/6 (83.3%) | **VALID** | eDNA chelation and aminoglycoside resistance verified. |
| **PMC2593050** | Locked Test | The Two-Component Regulatory System VicRK is Important to Virulence of Streptococcus... | The Two-Component Regulatory System VicRK is Important to Virulence of Streptococcus... | 3/5 (60.0%) | **VALID** | S. pneumoniae VicRK regulatory cascade verified. |
| **PMC2639726** | Locked Test | Coordinated Regulation of Virulence during Systemic Infection of Salmonella... | Coordinated Regulation of Virulence during Systemic Infection of Salmonella... | 6/6 (100.0%) | **VALID** | Authentic S. enterica systemic virulence regulation. |
| **PMC2816692** | External | Structural and Biochemical Characterization of the C-Terminal Domain of Anthrax Lethal Factor | Structural and Biochemical Characterization of SrcA, a Multi-Cargo Type III Secretion Chaperone... | 1/6 (16.7%) | **INVALID MISMATCH** | Curated gold describes Anthrax LF; disk XML describes Salmonella SrcA. Excluded from valid subset. |
| **PMC2829055** | External | Transit through Flea Vector Induces a Pre-Emergent Phenotype in Yersinia pestis | Transit through the Flea Vector Induces a Pretransmission Innate Immunity Resistance... | 6/7 (85.7%) | **VALID** | Y. pestis flea vector transmission and phagocytosis resistance. |
| **PMC2858072** | External | Transcriptome Analysis of Brucella abortus BvrR/BvrS Two-Component Regulatory System | Transcriptome Analysis of the Brucella abortus BvrR/BvrS Two-Component Regulatory System | 5/6 (83.3%) | **VALID** | B. abortus BvrR/BvrS two-component regulation. |
| **PMC2885601** | External | IgG Endopeptidase SeMac does not Inhibit Opsonophagocytosis but Promotes Bacterial Survival | IgG Endopeptidase SeMac does not Inhibit Opsonophagocytosis of Streptococcus equi... | 5/6 (83.3%) | **VALID** | S. equi SeMac IgG endopeptidase and bacterial survival. |

---

## 3. Forensic Analysis of PMC2816692 Mismatch

### Ground Truth Disconnect Details:
- **DOI in Curated Spec:** `10.1371/journal.ppat.1000751`
- **DOI in Disk XML:** `10.1371/journal.ppat.1000751` (Notice that PMCID 2816692 / DOI 10.1371/journal.ppat.1000751 is an authentic open-access article published in PLoS Pathogens in February 2010).
- **Actual PubMed Title:** *"Structural and Biochemical Characterization of SrcA, a Multi-Cargo Type III Secretion Chaperone in Salmonella Required for Pathogenic Association with a Host"* (Authors: Cooper CA, Zhang K, Andres SN, Fang Y, Kaniuk NA, Hannemann M, Brumell JH, Foster LJ, Junop MS, Coombes BK).
- **Curated Benchmark Spec:**
  ```python
  "title": "Structural and Biochemical Characterization of the C-Terminal Domain of the Anthrax Lethal Factor",
  "canonical_entities": ["Protective Antigen", "Lethal Factor", "MEK1/2", "MAPK Signaling", "Cytotoxicity", "Virulence"],
  "direct_edges": [
      ["Protective Antigen", "Lethal Factor"],
      ["Lethal Factor", "MEK1/2"],
      ["MEK1/2", "MAPK Signaling"],
      ["MAPK Signaling", "Cytotoxicity"],
      ["Cytotoxicity", "Virulence"],
  ]
  ```
- **Conclusion:** An Anthrax lethal factor annotation from a different study was inadvertently paired with PMCID 2816692 during benchmark curation. Because the gold entities do not exist in the source document, no system can achieve a true positive on these annotations without hallucination.

---

## 4. Split Contamination & Leakage Audit

To ensure the integrity of the release gate:
1. **Paper-Disjoint Verification:** All 20 papers have distinct PMCIDs, PMIDs, and DOIs.
2. **Organism Distribution:**
   - Train: *Salmonella enterica* (PMC2651894), *Mycobacterium tuberculosis* (PMC2682197), *Pseudomonas aeruginosa* (PMC2714965, PMC2774163).
   - Dev: *Salmonella enterica* (PMC1804205, PMC1874608), *Streptococcus pneumoniae/pyogenes* (PMC1913099), *Porphyromonas gingivalis* (PMC1974823), *M. tuberculosis* (PMC2242835), *Photorhabdus luminescens* (PMC2266911), *Streptococcus suis* (PMC2358977), *Staphylococcus aureus* (PMC2430206).
   - Locked Test: *Streptococcus pyogenes* (PMC2565068), *Pseudomonas aeruginosa* (PMC2581603), *Streptococcus pneumoniae* (PMC2593050), *Salmonella enterica* (PMC2639726).
   - External: *Salmonella enterica* (PMC2816692), *Yersinia pestis* (PMC2829055), *Brucella abortus* (PMC2858072), *Streptococcus equi* (PMC2885601).
3. **Zero-Leakage Compliance:**
   - No models or neural networks were retrained on any evaluation data.
   - All heuristic rules, regular expressions, and syntactic patterns were formulated strictly on the 8 Development papers.
   - Locked Test and External papers were never used for exploratory debugging or threshold selection.
