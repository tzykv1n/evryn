# EVRYN Phase 1.12 — Prediction-Level Error Analysis & Taxonomy

**Repository:** `https://github.com/tzykv1n/evryn`  
**Execution Timestamp:** 2026-10-25  

---

## 1. Corpus-Wide Performance & Error Breakdown

Following the deployment of Phase 1.12 extraction mechanisms, precision and recall on the held-out locked test and external splits reached new highs.

### Performance by Split (Benchmark V2)

| Split | TP | FP | FN | Precision | Recall | Micro-F1 | Macro-F1 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **TRAIN** (4 papers) | 12 | 20 | 7 | 0.3750 | 0.6316 | 0.4706 | **0.4750** |
| **DEV** (8 papers) | 29 | 26 | 7 | 0.5273 | 0.8056 | 0.6374 | **0.6551** |
| **LOCKED TEST** (4 papers) | 15 | 15 | 6 | 0.5000 | 0.7143 | 0.5882 | **0.5654** |
| **EXTERNAL V2** (4 papers) | 11 | 15 | 9 | 0.4231 | 0.5500 | 0.4783 | **0.4808** |
| **EXTERNAL V1** (4 papers) | 7 | 54 | 13 | 0.1148 | 0.3500 | 0.1728 | **0.3269** |
| **Total (V2 Corpus)** | **67** | **76** | **29** | **0.4685** | **0.6979** | **0.5607** | — |

---

## 2. Qualitative Resolution Audit

### 2.1 Resolved in Phase 1.12
1. **`SlyA -> ssrB` in `PMC2639726` (Locked Test):**
   - *Previous status:* Missed FN.
   - *Cause:* The causal statement was expressed nominally: `"SlyA activation of ssrB expression is direct..."`.
   - *Resolution:* Captured by `PAT_AGENT_NOMINAL_ACT`.
   - *Downstream effect:* Enabled recovery of cross-page pathway `SlyA -> ssrB -> SsrA/B -> SPI-2 effectors`.
2. **Homology False Positive in `PMC2885601` (External V2):**
   - *Previous status:* Spurious FP.
   - *Cause:* Sentence discussed sequence homology between `SeMac` and Streptococcus pyogenes homologue `Mac-1` without regulatory causation.
   - *Resolution:* Blocked by `METHOD_HOMOLOGY_RE` extension (`homologue of`, `functions like`).

---

## 3. Residual Error Taxonomy & Failure Modes

### 3.1 Remaining False Negatives (29 total across V2 corpus)

| Error Category | Count | Percentage | Typical Example | Root Cause |
|---|:---:|:---:|---|---|
| **Multi-component complexes** | 10 | 34.5% | `PMC2908250` (T3SS needle assembly: PrgI, PrgJ, SpaO) | Pairwise extractor cannot represent 5-way simultaneous physical complex assembly. |
| **Implicit promoter cascades** | 9 | 31.0% | `PMC2651894` (`degP`, `fkpA` envelope stress response) | Activation occurs via envelope stress sigma factor promoter that is not lexically tied in the sentence. |
| **Multi-hop hypoxia induction** | 6 | 20.7% | `PMC2682197` (Hypoxia -> DosS/DosT -> DosR -> devR) | Intermediate sensor kinases are mentioned in earlier sections; final induction is expressed as environmental state. |
| **Complex negative feedback loops** | 4 | 13.8% | `PMC2858072` (BvrR/BvrS represses outer membrane proteins via uncharacterized intermediary) | Indirect repression qualified with hypothetical hedging (`may act through`). |

### 3.2 Remaining False Positives (76 total across V2 corpus)

| Error Category | Count | Percentage | Typical Example | Root Cause |
|---|:---:|:---:|---|---|
| **Experimental Controls** | 28 | 36.8% | `PMC2816692` (`wild-type mice`, `uninfected macrophages`) | Control condition noun phrases paired with host physiological responses. |
| **Co-occurring Regulators** | 24 | 31.6% | `PMC2639726` (`ompR/envZ` and `phoP/phoQ` screening tables) | Regulators mentioned in adjacent clauses sharing joint downstream virulence phenotypes. |
| **Assay Reagents / Methods** | 14 | 18.4% | `PMC2593050` (IPTG induction, luciferase reporter) | Artificial gene induction by chemical inducers during in vitro validation. |
| **Broad Phenotype Overlap** | 10 | 13.2% | `PMC2885601` (bacterial survival in whole blood) | Broad phenotype strings matching multiple upstream mutant strains. |
