# EVRYN Phase 1.10 — Error Taxonomy and Remaining Failure Modes

**Repository:** `https://github.com/tzykv1n/evryn`  
**Branch:** `phase2.1-benchmark-audit-and-ui-fix`  
**Execution Timestamp:** 2026-10-25  

---

## 1. Residual Error Census (Development Split)

Following Phase 1.10 interventions, the Development split (8 papers) contains:
- **True Positives:** 29 (up from 27 in Phase 1.9, 23 in Phase 1.6)
- **False Positives:** 26 (down from 29 in Phase 1.9, 34 in Phase 1.6)
- **False Negatives:** 7 (down from 9 in Phase 1.9, 13 in Phase 1.6)

---

## 2. Taxonomy of Residual False Negatives (7 Cases)

1. **Multi-Section Discourse Claims (4 cases):**
   - Claims where experimental perturbation is stated in *Results* (e.g. deletion of a gene) and the phenotypic outcome is only discussed in the *Discussion* or *Abstract*, without sentence-level bridging.
2. **Nominalized Multi-Step Cascades (2 cases):**
   - Complex nominal expressions (e.g. `"phosphorylation-dependent multimerization resulting in target promoter clearance"`) where the verbal trigger is embedded inside a compound nominal head.
3. **Implicit Biochemical Activity (1 case):**
   - Relations where causality is implied through enzymatic designation (e.g. `"protease SpeB cleavage"`) without explicit assertion of up/downregulation.

---

## 3. Taxonomy of Residual False Positives (26 Cases)

1. **Neighboring Narrative Associations (14 cases):**
   - Co-occurrence of two genuine entities in adjacent descriptive narrative clauses where correlation or co-expression is described rather than a direct causative mechanism.
2. **Negative Experimental Controls (6 cases):**
   - Situations where a control mutation is tested against an invariant parameter (e.g. `"wild-type levels were maintained"`).
3. **Hub Pathway Generalizations (4 cases):**
   - Broad phenotypic associations where an entity is linked to general host virulence without direct mechanistic intermediary.
4. **Boundary Parenthetical Entities (2 cases):**
   - Entities cited parenthetically as historical references within findings statements.

---

## 4. Recommendations for Subsequent Development (Phase 2)

- Extend section-level discourse synthesis to bridge *Results* and *Discussion* sections.
- Incorporate dependency parse sub-tree nominalization unrolling for complex biochemical cascade verbs.
- Maintain strict zero-regression gating on the frozen Locked Held-Out Test split.
