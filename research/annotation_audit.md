# EVRYN: Benchmark Annotation & Curation Audit
## PMC-OA Real Scientific Paper Causal Discovery Benchmark

This document establishes the verified, text-grounded benchmark annotations for the 12 open-access PubMed Central full-text articles ingested in EVRYN (`data/real_papers/xml/`).

### Evaluation Protocol & Data Partitioning
To guarantee zero benchmark contamination and rigorous scientific defensibility:
- **Development Split (Dev, 8 Papers):** Used for vocabulary alignment, entity alias calibration, and ablation studies.
  - `PMC1804205`: *Salmonella enterica* PmrA/PmrB acid pH activation.
  - `PMC1874608`: *Salmonella enterica* Mlc regulation of SPI-1 via hilE.
  - `PMC1913099`: *Streptococcus pyogenes* adherence transcriptome and virulence factor regulation.
  - `PMC1974823`: *Porphyromonas gingivalis* short fimbriae regulation via FimS/FimR.
  - `PMC2242835`: *Mycobacterium tuberculosis* PhoP control of ESAT-6 secretion and T-cell recognition.
  - `PMC2266911`: *Photorhabdus luminescens* and *Yersinia enterocolitica* signaling, c-di-GMP, and pathogenicity.
  - `PMC2358977`: *Streptococcus suis* 89K pathogenicity island SalK/SalR regulation and PMN resistance.
  - `PMC2430206`: *Staphylococcus aureus* GraRS regulation of teichoic acid alanylation and CAMP susceptibility.
- **Held-Out Test Split (Test, 4 Papers):** Locked evaluation set. Never used for rule tuning or parameter fitting.
  - `PMC2565068`: *Streptococcus pyogenes* CsrS regulatory mutation, SLO, ScpC, and neutrophil incompetence.
  - `PMC2581603`: *Pseudomonas aeruginosa* extracellular DNA cation chelation and PhoPQ/PmrAB antimicrobial resistance.
  - `PMC2593050`: *Streptococcus equi* VicRK regulation of growth, attenuation, and protective immunity.
  - `PMC2639726`: *Salmonella enterica* PhoPQ, SlyA, and SsrB coordinated regulation of SPI-2 systemic virulence.

---

### Audited Paper Catalog & Ground Truth

#### 1. PMC1804205 (Dev Split)
- **Title:** *Acid pH activation of the PmrA/PmrB two-component regulatory system of Salmonella enterica*
- **Journal:** *Molecular Microbiology* (2007) | **PMID:** 17229213 | **DOI:** 10.1111/j.1365-2958.2006.05512.x | **License:** CC BY
- **Canonical Entities:** `["Acid pH", "PmrB", "PmrA", "PmrD", "Fe3+", "Lipopolysaccharide", "Polymyxin B"]`
- **Textual Evidence:**
  - *Acid pH -> PmrB:* "Mild acid (pH 5.8) promotes transcription of genes activated by the response regulator PmrA... via the PmrB sensor."
  - *PmrB -> PmrA:* "The PmrB sensor kinase activates the PmrA response regulator."
  - *PmrA -> PmrD:* "PmrA promotes expression of the connector protein PmrD."
  - *PmrA -> Lipopolysaccharide:* "PmrA-activated genes modify the lipopolysaccharide core."
  - *Lipopolysaccharide -> Polymyxin B:* "Modifications of lipopolysaccharide confer resistance to the antibiotic polymyxin B."
- **Direct Edges:** `[["Acid pH", "PmrB"], ["PmrB", "PmrA"], ["PmrA", "PmrD"], ["PmrA", "Lipopolysaccharide"], ["Lipopolysaccharide", "Polymyxin B"]]`
- **Cross-Page Edges:** `[["Acid pH", "PmrA"], ["Acid pH", "PmrD"], ["PmrB", "Lipopolysaccharide"], ["PmrB", "Polymyxin B"], ["Acid pH", "Polymyxin B"]]`

#### 2. PMC1874608 (Dev Split)
- **Title:** *Mlc regulation of Salmonella pathogenicity island I gene expression via hilE repression*
- **Journal:** *Nucleic Acids Research* (2007) | **PMID:** 17344322 | **DOI:** 10.1093/nar/gkm060 | **License:** CC BY
- **Canonical Entities:** `["Mlc", "HilD", "HilA", "SPI1", "InvF", "Type III Secretion"]`
- **Textual Evidence:**
  - *Mlc -> HilD:* "Mlc regulates expression of HilD by repressing the negative regulator hilE."
  - *HilD -> HilA:* "HilD activates hilA transcription by derepressing H-NS-mediated transcriptional silencing."
  - *HilA -> InvF:* "HilA directly activates transcription of invF."
  - *HilA -> SPI1:* "HilA is the master transcriptional activator of Salmonella pathogenicity island 1 (SPI1)."
  - *InvF -> Type III Secretion:* "InvF activates genes encoding the Type III Secretion apparatus and effector proteins."
- **Direct Edges:** `[["Mlc", "HilD"], ["HilD", "HilA"], ["HilA", "InvF"], ["HilA", "SPI1"], ["InvF", "Type III Secretion"]]`
- **Cross-Page Edges:** `[["Mlc", "HilA"], ["Mlc", "SPI1"], ["HilD", "SPI1"], ["Mlc", "Type III Secretion"], ["HilD", "Type III Secretion"]]`

#### 3. PMC1913099 (Dev Split)
- **Title:** *Novel Algorithms Reveal Streptococcal Transcriptomes and Clues about Undefined Genes*
- **Journal:** *PLoS Computational Biology* (2007) | **PMID:** 17616984 | **DOI:** 10.1371/journal.pcbi.0030132 | **License:** CC BY 4.0
- **Canonical Entities:** `["Adherence", "Streptolysin O", "SpeB", "Host Cell Cytotoxicity", "Host Colonization"]`
- **Textual Evidence:**
  - *Adherence -> Streptolysin O:* "Streptolysin O (slo or spy0167) was downregulated during pharyngeal cell adherence."
  - *Streptolysin O -> Host Cell Cytotoxicity:* "Streptolysin O is a cytotoxin that damages human tissue and increases host cell cytotoxicity."
  - *Adherence -> SpeB:* "SpeB production decreases during streptococcal adherence to human pharyngeal cells."
  - *SpeB -> Host Colonization:* "SpeB protease degrades host barrier proteins to facilitate invasive streptococcal host colonization."
- **Direct Edges:** `[["Adherence", "Streptolysin O"], ["Streptolysin O", "Host Cell Cytotoxicity"], ["Adherence", "SpeB"], ["SpeB", "Host Colonization"]]`
- **Cross-Page Edges:** `[["Adherence", "Host Cell Cytotoxicity"], ["Streptolysin O", "Host Colonization"], ["Adherence", "Host Colonization"]]`

#### 4. PMC1974823 (Dev Split)
- **Title:** *Porphyromonas gingivalis short fimbriae are regulated by a FimS/FimR two-component system*
- **Journal:** *FEMS Microbiology Letters* (2007) | **PMID:** 17517036 | **DOI:** 10.1111/j.1574-6968.2007.00722.x | **License:** CC BY
- **Canonical Entities:** `["FimS", "FimR", "Mfa1", "Short Fimbriae", "Biofilm"]`
- **Textual Evidence:**
  - *FimS -> FimR:* "FimS sensor kinase phosphorylates the cognate response regulator FimR."
  - *FimR -> Mfa1:* "Expression of mfa1 is positively controlled by the FimR regulator."
  - *Mfa1 -> Short Fimbriae:* "Mfa1 is the primary structural subunit encoding short fimbriae."
  - *Short Fimbriae -> Biofilm:* "Short fimbriae are required for the development and maturation of Porphyromonas biofilms."
- **Direct Edges:** `[["FimS", "FimR"], ["FimR", "Mfa1"], ["Mfa1", "Short Fimbriae"], ["Short Fimbriae", "Biofilm"]]`
- **Cross-Page Edges:** `[["FimS", "Mfa1"], ["FimS", "Short Fimbriae"], ["FimR", "Biofilm"], ["FimS", "Biofilm"]]`

#### 5. PMC2242835 (Dev Split)
- **Title:** *Control of M. tuberculosis ESAT-6 Secretion and Specific T Cell Recognition by PhoP*
- **Journal:** *PLoS Pathogens* (2008) | **PMID:** 18282096 | **DOI:** 10.1371/journal.ppat.0040033 | **License:** CC BY 4.0
- **Canonical Entities:** `["PhoP", "EspA", "ESX-1", "ESAT-6", "T Cell Recognition"]`
- **Textual Evidence:**
  - *PhoP -> EspA:* "PhoP regulates transcription of the rv3614c-rv3616c (espA) gene cluster."
  - *EspA -> ESX-1:* "EspA is an essential component required for functional ESX-1 secretion system assembly."
  - *ESX-1 -> ESAT-6:* "ESX-1 mediates the transport and secretion of ESAT-6 into the host environment."
  - *ESAT-6 -> T Cell Recognition:* "Secreted ESAT-6 stimulates interferon-gamma release and specific T cell recognition."
- **Direct Edges:** `[["PhoP", "EspA"], ["EspA", "ESX-1"], ["ESX-1", "ESAT-6"], ["ESAT-6", "T Cell Recognition"]]`
- **Cross-Page Edges:** `[["PhoP", "ESX-1"], ["PhoP", "ESAT-6"], ["PhoP", "T Cell Recognition"], ["EspA", "T Cell Recognition"], ["ESX-1", "T Cell Recognition"]]`

#### 6. PMC2266911 (Dev Split)
- **Title:** *Comparative analysis of the Photorhabdus luminescens and the Yersinia enterocolitica genomes: uncovering candidate genes involved in insect pathogenicity*
- **Journal:** *BMC Genomics* (2008) | **PMID:** 18218141 | **DOI:** 10.1186/1471-2164-9-40 | **License:** CC BY 2.0
- **Canonical Entities:** `["AHL", "LuxR", "c-di-GMP", "Biofilm Formation", "Virulence"]`
- **Textual Evidence:**
  - *AHL -> LuxR:* "Diffusible acyl homoserine lactones (AHLs) bind and activate LuxR-like receptors."
  - *LuxR -> Virulence:* "LuxR-mediated quorum sensing controls the coordinated expression of virulence factors."
  - *c-di-GMP -> Biofilm Formation:* "The second messenger c-di-GMP activates bacterial biofilm formation."
  - *Biofilm Formation -> Virulence:* "Biofilm formation regulates the phenotypic transition between colonizing and virulent states."
- **Direct Edges:** `[["AHL", "LuxR"], ["LuxR", "Virulence"], ["c-di-GMP", "Biofilm Formation"], ["Biofilm Formation", "Virulence"]]`
- **Cross-Page Edges:** `[["AHL", "Biofilm Formation"], ["AHL", "Virulence"], ["c-di-GMP", "Virulence"]]`

#### 7. PMC2358977 (Dev Split)
- **Title:** *SalK/SalR, a Two-Component Signal Transduction System, Is Essential for Full Virulence of Highly Invasive Streptococcus suis Serotype 2*
- **Journal:** *PLoS ONE* (2008) | **PMID:** 18461142 | **DOI:** 10.1371/journal.pone.0002080 | **License:** CC BY 4.0
- **Canonical Entities:** `["89K", "SalK", "SalR", "PMN Resistance", "Virulence"]`
- **Textual Evidence:**
  - *89K -> SalK:* "The specific 89K pathogenicity island encodes the SalK/SalR two-component system."
  - *SalK -> SalR:* "SalK histidine kinase transfers phosphate to its cognate regulator SalR."
  - *SalR -> PMN Resistance:* "Deletion of salKR leads to decreased resistance to PMN-mediated killing."
  - *PMN Resistance -> Virulence:* "Resistance to polymorphonuclear neutrophil killing is essential for systemic virulence and bacteremia."
  - *SalR -> Virulence:* "SalK/SalR is requisite for the full virulence and lethality of Chinese epidemic SS2."
- **Direct Edges:** `[["89K", "SalK"], ["SalK", "SalR"], ["SalR", "PMN Resistance"], ["PMN Resistance", "Virulence"], ["SalR", "Virulence"]]`
- **Cross-Page Edges:** `[["89K", "SalR"], ["89K", "PMN Resistance"], ["89K", "Virulence"], ["SalK", "PMN Resistance"], ["SalK", "Virulence"]]`

#### 8. PMC2430206 (Dev Split)
- **Title:** *The GraRS regulatory system controls Staphylococcus aureus susceptibility to antimicrobial host defenses*
- **Journal:** *BMC Microbiology* (2008) | **PMID:** 18533037 | **DOI:** 10.1186/1471-2180-8-85 | **License:** CC BY 2.0
- **Canonical Entities:** `["GraRS", "GraR", "dltA", "LL-37", "Virulence"]`
- **Textual Evidence:**
  - *GraRS -> GraR:* "GraRS operates as a two-component sensor-regulator complex with response regulator GraR."
  - *GraRS -> dltA:* "The GraRS regulatory genes control expression of the dltA teichoic acid alanylation operon."
  - *dltA -> LL-37:* "D-alanylation by dltA reduces surface negativity and prevents killing by cationic peptide LL-37."
  - *GraRS -> LL-37:* "The graRS mutant is significantly more susceptible to inactivation by the human cathelicidin LL-37."
  - *LL-37 -> Virulence:* "Susceptibility to LL-37 clearance attenuates bacterial survival and kidney burden in mouse models."
- **Direct Edges:** `[["GraRS", "GraR"], ["GraRS", "dltA"], ["dltA", "LL-37"], ["GraRS", "LL-37"], ["LL-37", "Virulence"]]`
- **Cross-Page Edges:** `[["GraRS", "Virulence"], ["GraR", "LL-37"], ["GraR", "Virulence"], ["dltA", "Virulence"]]`

#### 9. PMC2565068 (Locked Test Split)
- **Title:** *Incompetence of Neutrophils to Invasive Group A streptococcus Is Attributed to Induction of Plural Virulence Factors by Dysfunction of a Regulator*
- **Journal:** *PLoS ONE* (2008) | **PMID:** 18846227 | **DOI:** 10.1371/journal.pone.0003455 | **License:** CC BY 4.0
- **Canonical Entities:** `["CsrS", "Streptolysin O", "ScpC", "IL-8", "PMN Death", "Virulence"]`
- **Textual Evidence:**
  - *CsrS -> Streptolysin O:* "Enhanced expression of the slo gene in severe invasive GAS is attributed to mutation of CsrS."
  - *CsrS -> ScpC:* "Dysfunction of CsrS relieves repression of the serine proteinase scpC."
  - *Streptolysin O -> PMN Death:* "PMN were rapidly killed by streptolysin O (SLO) from severe invasive streptococci."
  - *ScpC -> IL-8:* "Enhanced production of serine proteinase ScpC degrades the chemokine IL-8."
  - *CsrS -> Virulence:* "CsrS mutation is essential for systemic bacteremia and lethal virulence in mouse models."
  - *Streptolysin O -> Virulence:* "Streptolysin O cytolytic activity promotes systemic tissue destruction and invasive virulence."
- **Direct Edges:** `[["CsrS", "Streptolysin O"], ["CsrS", "ScpC"], ["Streptolysin O", "PMN Death"], ["ScpC", "IL-8"], ["CsrS", "Virulence"], ["Streptolysin O", "Virulence"]]`
- **Cross-Page Edges:** `[["CsrS", "PMN Death"], ["CsrS", "IL-8"], ["ScpC", "Virulence"], ["PMN Death", "Virulence"]]`

#### 10. PMC2581603 (Locked Test Split)
- **Title:** *Extracellular DNA Chelates Cations and Induces Antibiotic Resistance in Pseudomonas aeruginosa Biofilms*
- **Journal:** *PLoS Pathogens* (2008) | **PMID:** 19023416 | **DOI:** 10.1371/journal.ppat.1000213 | **License:** CC BY 4.0
- **Canonical Entities:** `["Extracellular DNA", "Cation Chelation", "PhoPQ", "PmrAB", "arn Operon", "Antibiotic Resistance"]`
- **Textual Evidence:**
  - *Extracellular DNA -> Cation Chelation:* "Extracellular DNA exhibits strong cation chelating activity that binds divalent metal ions."
  - *Cation Chelation -> PhoPQ:* "Cation chelation creates localized Mg2+ limitation that directly activates the PhoPQ system."
  - *PhoPQ -> PmrAB:* "PhoPQ and PmrAB two-component systems are coordinately activated in response to cation depletion."
  - *PmrAB -> arn Operon:* "Activated PmrAB binds the promoter and induces expression of the arnBCADTEF (arn) operon."
  - *arn Operon -> Antibiotic Resistance:* "The arn operon adds aminoarabinose to lipid A, conferring high-level antibiotic resistance to polymyxins."
- **Direct Edges:** `[["Extracellular DNA", "Cation Chelation"], ["Cation Chelation", "PhoPQ"], ["PhoPQ", "PmrAB"], ["PmrAB", "arn Operon"], ["arn Operon", "Antibiotic Resistance"]]`
- **Cross-Page Edges:** `[["Extracellular DNA", "PhoPQ"], ["Extracellular DNA", "PmrAB"], ["Cation Chelation", "arn Operon"], ["Extracellular DNA", "Antibiotic Resistance"], ["Cation Chelation", "Antibiotic Resistance"], ["PhoPQ", "Antibiotic Resistance"]]`

#### 11. PMC2593050 (Locked Test Split)
- **Title:** *The Two-Component Regulatory System VicRK is Important to Virulence of Streptococcus equi Subspecies equi*
- **Journal:** *The Open Microbiology Journal* (2008) | **PMID:** 19088898 | **DOI:** 10.2174/1874285800802010089 | **License:** CC BY 2.0
- **Canonical Entities:** `["VicK", "VicR", "Bacterial Growth", "Virulence", "Protective Immunity"]`
- **Textual Evidence:**
  - *VicK -> VicR:* "VicK membrane sensor phosphorylates the cognate response regulator VicR."
  - *VicK -> Bacterial Growth:* "The vicK deletion causes a severe defect in bacterial growth in blood and THY medium."
  - *Bacterial Growth -> Virulence:* "The growth defect of the mutant contributes to the profound attenuation of virulence in infection models."
  - *VicK -> Virulence:* "VicK is important to virulence of Streptococcus equi in subcutaneous and intranasal models."
  - *Virulence -> Protective Immunity:* "Infection with the attenuated strain confers robust protective immunity against lethal reinfection."
- **Direct Edges:** `[["VicK", "VicR"], ["VicK", "Bacterial Growth"], ["Bacterial Growth", "Virulence"], ["VicK", "Virulence"], ["Virulence", "Protective Immunity"]]`
- **Cross-Page Edges:** `[["VicK", "Protective Immunity"], ["VicR", "Virulence"], ["VicR", "Bacterial Growth"], ["Bacterial Growth", "Protective Immunity"]]`

#### 12. PMC2639726 (Locked Test Split)
- **Title:** *Coordinated Regulation of Virulence during Systemic Infection of Salmonella enterica Serovar Typhimurium*
- **Journal:** *PLoS Pathogens* (2009) | **PMID:** 19214216 | **DOI:** 10.1371/journal.ppat.1000306 | **License:** CC BY 4.0
- **Canonical Entities:** `["PhoQ", "PhoP", "SlyA", "SsrB", "SPI-2", "Virulence"]`
- **Textual Evidence:**
  - *PhoQ -> PhoP:* "Environmental cues activate the sensor PhoQ, leading to phosphorylation of the regulator PhoP."
  - *PhoP -> SlyA:* "PhoP promotes the expression and activation of the transcriptional regulator SlyA."
  - *SlyA -> SsrB:* "SlyA binds the promoter region and activates transcription of the SsrA/SsrB regulatory system."
  - *SsrB -> SPI-2:* "SsrB activates transcription of the type III secretion system encoded within pathogenicity island 2 (SPI-2)."
  - *SPI-2 -> Virulence:* "SPI-2 encodes effectors required for intramacrophage replication and systemic virulence in mice."
- **Direct Edges:** `[["PhoQ", "PhoP"], ["PhoP", "SlyA"], ["SlyA", "SsrB"], ["SsrB", "SPI-2"], ["SPI-2", "Virulence"]]`
- **Cross-Page Edges:** `[["PhoQ", "SlyA"], ["PhoP", "SsrB"], ["PhoP", "SPI-2"], ["PhoP", "Virulence"], ["PhoQ", "Virulence"], ["SlyA", "Virulence"]]`
