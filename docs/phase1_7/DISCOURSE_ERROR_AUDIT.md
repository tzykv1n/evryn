# EVRYN Phase 1.7 — Exhaustive Discourse Error Audit

## Executive Summary

During the Phase 1.6 error census, 28 false negatives out of 48 total false negatives (58.3%) were classified
as `cross_sentence_discourse` because their gold source and target entity strings did not co-occur verbatim
in any single sentence of `doc.sentences`. This exhaustive audit examines all 28 cases individually across
Train, Dev, Locked Test, and External splits to diagnose the exact computational and linguistic mechanisms
underlying the extraction failure.

### Key Audit Findings

Our deep audit reveals that the 28 'discourse' false negatives decompose into four distinct technical categories:

1. **Sentence Boundary Splitting Artifacts (Abbreviation Periods) (Cases 3, 7):**
   Sentences were prematurely truncated by regular expression sentence segmenters encountering taxonomic genus abbreviations
   (e.g. `P. gingivalis`, `S. aureus`, `E. coli`) or academic abbreviations (e.g. `et al. [15]`, `Fig. 3`). This severed valid single-sentence
   syntactic relations across artificial sentence boundaries.

2. **Demonstrative Anaphora & Cross-Sentence Connectives (Cases 5, 6, 19, 21, 24):**
   The causal claim is asserted across immediately adjacent sentences ($dist = 1$) via demonstrative pronouns
   (e.g., `'This result may account partially... for the virulence loss'`, `'These anti-phagocytic mechanisms are essential for...'`).
   Resolving the antecedent entity in sentence $S_k$ to the causal predicate in sentence $S_{k+1}$ directly recovers the gold relation.

3. **Lexical / Synonym / Nomenclature Gaps in Exact Substring Search (Cases 1, 8, 9, 10, 11, 12, 13, 14, 15, 16, 20, 25, 27):**
   Both entities were actually asserted within the *same* sentence or within 1 sentence, but exact string search missed them
   due to hyphenation variants (`ATP-Binding` vs `ATP binding`), Greek unicode characters (`σE` vs `sigmaE`), or recognized biological synonyms
   (`arnBCADTEF` for `arn Operon`, `T3SS` for `Type III Secretion`, `slo` for `Streptolysin O`).

4. **Multi-Paragraph / Multi-Section Experimental Synthesis (Cases 2, 4, 17, 18, 22, 23, 26, 28):**
   The relation represents a high-level scientific conclusion synthesized across multiple sections or distant experimental figures
   without a local syntactic connective.

---

## Census Breakdown by Taxonomic Class

| Category | Case Count | Case IDs | Primary Solution Mechanism |
| :--- | :---: | :--- | :--- |
| **Sentence Boundary Splitting** | 2 | 3, 7 | Abbreviation period stitching (`P.`, `S.`, `E.`) |
| **Demonstrative Anaphora & Connectives** | 5 | 5, 6, 19, 21, 24 | Demonstrative antecedent resolution + dual-sentence evidence tracking |
| **Synonym & Normalization Gaps** | 13 | 1, 8, 9, 10, 11, 12, 13, 14, 15, 16, 20, 25, 27 | Unicode Greek mapping, unhyphenated variant matching, operon normalization |
| **Multi-Paragraph Synthesis** | 8 | 2, 4, 17, 18, 22, 23, 26, 28 | Cross-page/cross-section multi-hop chain synthesis |
| **Total** | **28** | **All Cases 1–28** | Bounded Document-Context Resolver |

---

## Individual Case-by-Case Audit (All 28 Cases)

### Case 01: PMC1913099 (DEV) — `Adherence` $\to$ `Streptolysin O`

- **Gold Source Entity:** `Adherence`
- **Gold Target Entity:** `Streptolysin O`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 0-2 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 47
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 42
- **Discourse Relation / Connective:** Document-level abbreviation / coreference (slo = Streptolysin O)
- **Assertion Type:** Explicit assertion in sentence 47 using slo synonym
- **Extraction Requirement:** Resolve 'slo' to 'Streptolysin O' via local abbreviation table; detect 'downregulation during adherence' as Adherence -| Streptolysin O.

---

### Case 02: PMC1913099 (DEV) — `SpeB` $\to$ `Host Colonization`

- **Gold Source Entity:** `SpeB`
- **Gold Target Entity:** `Host Colonization`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 21 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 51
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 21
- **Discourse Relation / Connective:** Section-level discourse scope; nominal synonym ('pharyngeal cell attachment' = Host Colonization)
- **Assertion Type:** Inference across experimental discussion
- **Extraction Requirement:** Discourse bridging between pharyngeal colonization goal and SpeB proteolysis.

---

### Case 03: PMC1974823 (DEV) — `Short Fimbriae` $\to$ `Biofilm`

- **Gold Source Entity:** `Short Fimbriae`
- **Gold Target Entity:** `Biofilm`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 1 sentence boundary (severed at abbreviation period)
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 27
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 26
- **Discourse Relation / Connective:** Sentence splitting artifact ('between P.' / 'gingivalis and Streptococcus gordonii require the interaction of Mfa1...')
- **Assertion Type:** Explicit syntactic causal assertion fragmented by punctuation tokenizer
- **Extraction Requirement:** Sentence boundary stitch across genus abbreviation period ('P. gingivalis') reunites 'biofilm development' and 'require the interaction of Mfa1'.

---

### Case 04: PMC2242835 (DEV) — `EspA` $\to$ `ESX-1`

- **Gold Source Entity:** `EspA`
- **Gold Target Entity:** `ESX-1`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 2 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 102
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 100
- **Discourse Relation / Connective:** Discourse contrast across knock-in experiment ('outside RD1/ESX-1 region')
- **Assertion Type:** Experimental deduction
- **Extraction Requirement:** Link gene cluster rv3612c-rv3616c (espA) to ESX-1 secretion system functionality.

---

### Case 05: PMC2358977 (DEV) — `SalR` $\to$ `PMN Resistance`

- **Gold Source Entity:** `SalR`
- **Gold Target Entity:** `PMN Resistance`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 0-1 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 106
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 106
- **Discourse Relation / Connective:** Intra-sentence mutant phenotype + local noun phrase ('less able to resist killing by PMNs')
- **Assertion Type:** Explicit mutant phenotype assertion in Sentence 106
- **Extraction Requirement:** Recognize 'resist killing by PMNs' as 'PMN Resistance' phenotype; extract genetics mutant regulation.

---

### Case 06: PMC2358977 (DEV) — `PMN Resistance` $\to$ `Virulence`

- **Gold Source Entity:** `PMN Resistance`
- **Gold Target Entity:** `Virulence`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 1 sentence (adjacent sentences 106 -> 107)
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 107
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 106
- **Discourse Relation / Connective:** Demonstrative causal anaphora ('This result may account partially... for the virulence loss')
- **Assertion Type:** Explicit causal assertion linking sentence 106 outcome to sentence 107 claim
- **Extraction Requirement:** Resolve demonstrative pronoun 'This result' in sentence 107 to the killing resistance phenotype in sentence 106.

---

### Case 07: PMC2430206 (DEV) — `dltA` $\to$ `LL-37`

- **Gold Source Entity:** `dltA`
- **Gold Target Entity:** `LL-37`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 5 sentences (and sentence split across 'S. aureus')
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 31
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 39
- **Discourse Relation / Connective:** Mutant sensitivity paragraph scope ('dltA mutant' binding and susceptibility to CAMPs/LL-37)
- **Assertion Type:** Experimental sensitivity assay deduction
- **Extraction Requirement:** Resolve dltA mutant background susceptibility across paragraph results.

---

### Case 08: PMC2581603 (LOCKED_TEST) — `Cation Chelation` $\to$ `PhoPQ`

- **Gold Source Entity:** `Cation Chelation`
- **Gold Target Entity:** `PhoPQ`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 9 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 234
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 225
- **Discourse Relation / Connective:** Causal connective ('chelation of cations by extracellular DNA activates PhoPQ')
- **Assertion Type:** Explicit assertion with synonym variation ('chelation of divalent cations')
- **Extraction Requirement:** Map 'chelation of divalent cations' to canonical 'Cation Chelation'.

---

### Case 09: PMC2581603 (LOCKED_TEST) — `PmrAB` $\to$ `arn Operon`

- **Gold Source Entity:** `PmrAB`
- **Gold Target Entity:** `arn Operon`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 0-1 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 236
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 236
- **Discourse Relation / Connective:** Intra-sentence operon regulation ('PmrA-regulated arnBCADTEF operon')
- **Assertion Type:** Explicit syntactic modification
- **Extraction Requirement:** Map 'arnBCADTEF' / 'pmrHFIJKLM' to 'arn Operon'.

---

### Case 10: PMC2581603 (LOCKED_TEST) — `arn Operon` $\to$ `Antibiotic Resistance`

- **Gold Source Entity:** `arn Operon`
- **Gold Target Entity:** `Antibiotic Resistance`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 0-1 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 238
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 238
- **Discourse Relation / Connective:** Intra-sentence causal predicate ('arn operon mediates polymyxin resistance')
- **Assertion Type:** Explicit causal assertion
- **Extraction Requirement:** Map 'polymyxin resistance' to 'Antibiotic Resistance'.

---

### Case 11: PMC2593050 (LOCKED_TEST) — `VicK` $\to$ `Bacterial Growth`

- **Gold Source Entity:** `VicK`
- **Gold Target Entity:** `Bacterial Growth`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 0-1 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 112
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 112
- **Discourse Relation / Connective:** Mutant growth kinetics predicate ('ΔvicK showed impaired growth in culture')
- **Assertion Type:** Explicit mutant growth assertion
- **Extraction Requirement:** Detect 'impaired growth' as 'Bacterial Growth' phenotype.

---

### Case 12: PMC2593050 (LOCKED_TEST) — `Bacterial Growth` $\to$ `Virulence`

- **Gold Source Entity:** `Bacterial Growth`
- **Gold Target Entity:** `Virulence`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 1 sentence
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 114
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 113
- **Discourse Relation / Connective:** Demonstrative connective ('This growth defect accounts for attenuated virulence in mice')
- **Assertion Type:** Explicit causal assertion
- **Extraction Requirement:** Resolve 'This growth defect' to 'Bacterial Growth'.

---

### Case 13: PMC2593050 (LOCKED_TEST) — `Virulence` $\to$ `Protective Immunity`

- **Gold Source Entity:** `Virulence`
- **Gold Target Entity:** `Protective Immunity`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 2 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 118
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 116
- **Discourse Relation / Connective:** Vaccination trial discourse ('attenuated strain confers protective immunity upon challenge')
- **Assertion Type:** Vaccine challenge assertion
- **Extraction Requirement:** Resolve attenuated virulence link to immunity.

---

### Case 14: PMC2651894 (TRAIN) — `RseA` $\to$ `sigmaE`

- **Gold Source Entity:** `RseA`
- **Gold Target Entity:** `sigmaE`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 0-1 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 14
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 14
- **Discourse Relation / Connective:** Anti-sigma factor binding predicate ('Release of σE from its inner membrane anchored anti-sigma factor, RseA')
- **Assertion Type:** Explicit biochemical regulatory mechanism
- **Extraction Requirement:** Detect Greek unicode 'σE' as 'sigmaE' and extract anti-sigma regulation.

---

### Case 15: PMC2651894 (TRAIN) — `sigmaE` $\to$ `RpoE`

- **Gold Source Entity:** `sigmaE`
- **Gold Target Entity:** `RpoE`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 0 sentences (same sentence 13)
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 13
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 13
- **Discourse Relation / Connective:** Parenthetical equivalence ('alternative sigma factor, RpoE (σE)')
- **Assertion Type:** Explicit nomenclature definition
- **Extraction Requirement:** Detect 'σE' and extract parenthetical identity.

---

### Case 16: PMC2682197 (TRAIN) — `ATP-Binding` $\to$ `Bacillary Growth`

- **Gold Source Entity:** `ATP-Binding`
- **Gold Target Entity:** `Bacillary Growth`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 0 sentences (same sentence 142)
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 142
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 142
- **Discourse Relation / Connective:** Intra-sentence correlation predicate ('direct correlation between the ATP-binding activity ... and its ability to regulate bacillary growth')
- **Assertion Type:** Explicit causal correlation
- **Extraction Requirement:** Map unhyphenated 'ATP binding' to 'ATP-Binding' and 'bacillary growth' to 'Bacillary Growth'.

---

### Case 17: PMC2682197 (TRAIN) — `Bacillary Growth` $\to$ `Persistent Infection`

- **Gold Source Entity:** `Bacillary Growth`
- **Gold Target Entity:** `Persistent Infection`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 3 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 12
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 11
- **Discourse Relation / Connective:** Discourse thesis ('signaling intermediate in a pathway that promotes persistent infection')
- **Assertion Type:** Explicit hypothesis claim
- **Extraction Requirement:** Link growth regulation to persistence entry.

---

### Case 18: PMC2714965 (TRAIN) — `PMN Infiltration` $\to$ `Host Survival`

- **Gold Source Entity:** `PMN Infiltration`
- **Gold Target Entity:** `Host Survival`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 5 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 76
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 71
- **Discourse Relation / Connective:** Inflammatory pathology discourse ('decreased PMN recruitment prolonged survival')
- **Assertion Type:** Experimental survival curve inference
- **Extraction Requirement:** Link neutrophil influx attenuation to animal survival.

---

### Case 19: PMC2774163 (TRAIN) — `GacS` $\to$ `cyclic-di-GMP`

- **Gold Source Entity:** `GacS`
- **Gold Target Entity:** `cyclic-di-GMP`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 1-2 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 38
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 37
- **Discourse Relation / Connective:** Two-component kinase switch connective ('inactivation of LadS and GacS elevates c-di-GMP')
- **Assertion Type:** Explicit regulatory assertion
- **Extraction Requirement:** Resolve 'c-di-GMP' to 'cyclic-di-GMP' across adjacent sentences.

---

### Case 20: PMC2774163 (TRAIN) — `Type III Secretion` $\to$ `Virulence`

- **Gold Source Entity:** `Type III Secretion`
- **Gold Target Entity:** `Virulence`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 0-1 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 334
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 334
- **Discourse Relation / Connective:** T3SS abbreviation + virulence phenotype ('T3SS is required for cytotoxicity and virulence')
- **Assertion Type:** Explicit requirement assertion
- **Extraction Requirement:** Map 'T3SS' / 'type III secretion' to 'Type III Secretion'.

---

### Case 21: PMC2816692 (EXTERNAL) — `Effector Translocation` $\to$ `Virulence`

- **Gold Source Entity:** `Effector Translocation`
- **Gold Target Entity:** `Virulence`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 1 sentence
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 19
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 18
- **Discourse Relation / Connective:** Demonstrative discourse connective ('This failure of effector translocation prevents systemic virulence')
- **Assertion Type:** Explicit causal assertion
- **Extraction Requirement:** Resolve demonstrative 'This failure of effector translocation' to 'Effector Translocation'.

---

### Case 22: PMC2829055 (EXTERNAL) — `di-GMP` $\to$ `ybt`

- **Gold Source Entity:** `di-GMP`
- **Gold Target Entity:** `ybt`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** Multi-paragraph / section
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 152
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 34
- **Discourse Relation / Connective:** Section-level regulatory synthesis (HmsT/di-GMP activates iron-scavenging ybt cluster)
- **Assertion Type:** Deduction across microarrays and genetics
- **Extraction Requirement:** Cross-section synthesis of HmsT/di-GMP second messenger cascade.

---

### Case 23: PMC2829055 (EXTERNAL) — `ybt` $\to$ `Phagocytosis Resistance`

- **Gold Source Entity:** `ybt`
- **Gold Target Entity:** `Phagocytosis Resistance`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 2 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 156
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 154
- **Discourse Relation / Connective:** Causal consequence connective ('yersiniabactin synthesis prevents macrophage killing')
- **Assertion Type:** Explicit assay assertion
- **Extraction Requirement:** Resolve 'yersiniabactin' to 'ybt' and 'macrophage killing resistance' to 'Phagocytosis Resistance'.

---

### Case 24: PMC2829055 (EXTERNAL) — `Phagocytosis Resistance` $\to$ `Virulence`

- **Gold Source Entity:** `Phagocytosis Resistance`
- **Gold Target Entity:** `Virulence`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 1 sentence
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 160
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 159
- **Discourse Relation / Connective:** Demonstrative causal anaphora ('These anti-phagocytic mechanisms are essential for bubonic and pneumonic virulence')
- **Assertion Type:** Explicit causal assertion
- **Extraction Requirement:** Resolve demonstrative 'These anti-phagocytic mechanisms' to 'Phagocytosis Resistance'.

---

### Case 25: PMC2858072 (EXTERNAL) — `Outer Membrane Proteins` $\to$ `Macrophage Infection`

- **Gold Source Entity:** `Outer Membrane Proteins`
- **Gold Target Entity:** `Macrophage Infection`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 0-1 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 64
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 64
- **Discourse Relation / Connective:** OMP abbreviation ('altered outer membrane protein profile impairs macrophage penetration')
- **Assertion Type:** Explicit phenotype assertion
- **Extraction Requirement:** Map 'OMPs' / 'outer membrane proteins' to canonical entity.

---

### Case 26: PMC2858072 (EXTERNAL) — `Macrophage Infection` $\to$ `Virulence`

- **Gold Source Entity:** `Macrophage Infection`
- **Gold Target Entity:** `Virulence`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 2 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 68
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 66
- **Discourse Relation / Connective:** Intracellular niche discourse ('intracellular persistence in macrophages mediates chronic infection')
- **Assertion Type:** Pathogenesis mechanism claim
- **Extraction Requirement:** Map 'macrophage persistence' to 'Macrophage Infection' and link to virulence.

---

### Case 27: PMC2885601 (EXTERNAL) — `Opsonophagocytosis` $\to$ `Bacterial Survival`

- **Gold Source Entity:** `Opsonophagocytosis`
- **Gold Target Entity:** `Bacterial Survival`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 0-1 sentences
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 52
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 52
- **Discourse Relation / Connective:** Complement-mediated killing assay ('resistance to opsonophagocytic killing enables survival in whole blood')
- **Assertion Type:** Explicit biochemical mechanism assertion
- **Extraction Requirement:** Map 'survival in whole blood' to 'Bacterial Survival'.

---

### Case 28: PMC2885601 (EXTERNAL) — `Bacterial Survival` $\to$ `Virulence`

- **Gold Source Entity:** `Bacterial Survival`
- **Gold Target Entity:** `Virulence`
- **Entities Present in Paper:** Yes (both present)
- **Sentence Distance:** 1 sentence
- **Causal Assertion Sentence ($S_{causal}$):** Sentence 55
- **Entity Introducing Sentence ($S_{entity}$):** Sentence 54
- **Discourse Relation / Connective:** Discourse consequence ('bacterial survival during bacteremia promotes systemic disease and mortality')
- **Assertion Type:** Explicit causal assertion
- **Extraction Requirement:** Resolve bacteremic survival link to mortality/virulence.

---
