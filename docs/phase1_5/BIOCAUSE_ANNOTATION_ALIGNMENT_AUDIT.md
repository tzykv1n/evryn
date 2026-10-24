# EVRYN Phase 1.5: BioCause Annotation Alignment & Standoff Parsing Audit

**Date:** 2026-10-24  
**Author:** EVRYN Lead Research & Engineering Team  
**Focus:** Standoff event dereferencing, Theme vs Effect mapping, and self-referential edge elimination in BioCause.

---

## 1. Executive Summary

During Phase 1.5 diagnostic inspection of the BioCause-derived papers—specifically `PMC1804205` (*Salmonella enterica* PmrA/PmrB two-component system) and `PMC1874608` (*Salmonella enterica* Mlc/HilD/HilA/SPI1 regulatory circuit)—an anomalous pattern was identified in the gold annotations: numerous relations possessed identical causes and effects, such as `PhoQ -> PhoQ` and `Mlc -> Mlc`.

A systematic audit revealed that this was **not** an authentic biological annotation authored by domain experts, but rather a **critical standoff parsing defect** in `evryn/datasets/biocause.py`. The parser queried `args.get("Effect")`, which does not exist in the BioNLP Shared Task format; upon evaluating `None`, it fell back to `args.get("Cause")`, generating self-referential loops across **87.8%** of the BioCause relations.

We implemented recursive standoff event dereferencing to extract the true `Theme` target (dereferencing through nested `Gene_expression` and `Regulation` event structures). This eliminated the artificial self-loops, restored genuine biological regulatory relations (`PhoQ -> PmrA`, `Mlc -> hilE`, `Mlc -> hilD`), and aligned EVRYN's evaluation with the authentic ground truth.

---

## 2. Anomaly Discovery & Symptom Distribution

In the Phase 1.4 benchmark and Examples tab inspection, gold relation comparisons for `PMC1804205` and `PMC1874608` showed:

| Paper | Sample "Gold" Relation | Actual Biology | Model Extraction | Status Before Audit |
|---|---|---|---|---|
| `PMC1804205` | `PhoQ -> PhoQ` | PhoQ sensor activates PmrA via PmrD | `PhoQ -> PmrA` | False Negative + False Positive Penalty |
| `PMC1804205` | `PhoP -> PhoP` | PhoP regulates PmrD transcription | `PhoP -> PmrD` | False Negative + False Positive Penalty |
| `PMC1874608` | `Mlc -> Mlc` | Mlc represses `hilE` transcription | `Mlc -> hilE` | False Negative + False Positive Penalty |
| `PMC1874608` | `HilD -> HilD` | HilD activates `hilA` expression | `HilD -> hilA` | False Negative + False Positive Penalty |

Because an extraction model adhering to directed causal semantics will never predict that a protein causes itself ($A \to A$), the model was systematically penalized twice for every correct extraction:
1. **False Negative:** It failed to extract the spurious self-loop `A -> A`.
2. **False Positive:** Its correct biological extraction `A -> B` was marked spurious because `B` was missing from the corrupted gold set.

---

## 3. Root Cause Analysis in `evryn/datasets/biocause.py`

### 3.1 The Defect in `_load_standoff`

The legacy parser in `evryn/datasets/biocause.py` processed event lines (`E1 Positive_regulation:T5 Theme:E2 Cause:T1`) with the following logic:

```python
# Legacy defective implementation in biocause.py:
cause_id = args.get("Cause")
effect_id = args.get("Effect") or args.get("Cause")
```

### 3.2 BioNLP Shared Task Standoff Schema

In the standard BioNLP Shared Task standoff annotation schema (and BioCause corpus):
- **Event Type:** `Positive_regulation`, `Negative_regulation`, `Regulation`.
- **Regulator:** Always keyed as `Cause` (e.g., `Cause:T1`).
- **Regulated Target:** Always keyed as `Theme` (e.g., `Theme:T2` or `Theme:E2`), **never** `Effect`.

When `args.get("Effect")` was evaluated, it consistently returned `None`. The fallback expression `or args.get("Cause")` was immediately triggered, setting:
$$\text{effect\_id} = \text{cause\_id}$$
Consequently, `cause` and `effect` pointed to the exact same standoff entity token:
$$\text{cause} = \text{standoff}[\text{cause\_id}].\text{text}, \quad \text{effect} = \text{standoff}[\text{cause\_id}].\text{text}$$

### 3.3 Corpus Impact Breakdown

Across all BioCause standoff annotations in the repository:
- **Total Relations Parsed:** 417
- **Corrupted Identical Pairs ($A \to A$):** 366 (87.77%)
- **True Distinct Pairs ($A \to B$):** 51 (12.23%)

---

## 4. Engineering Fix: Recursive Standoff Dereferencing

### 4.1 Recursive Dereferencer Implementation

In `evryn/datasets/biocause.py`, we implemented `_resolve_target` to recursively trace `Theme` arguments through nested events:

```python
# Resolved implementation:
effect_id = args.get("Theme") or args.get("Effect")

def _resolve_target(t_id: str, depth: int = 0) -> str:
    if depth > 5 or not t_id:
        return ""
    if t_id in entities:
        return entities[t_id]
    if t_id in events:
        sub_ev_args = events[t_id].get("args", {})
        sub_theme = sub_ev_args.get("Theme")
        if sub_theme:
            return _resolve_target(sub_theme, depth + 1)
        sub_cause = sub_ev_args.get("Cause")
        if sub_cause:
            return _resolve_target(sub_cause, depth + 1)
    return ""

cause = entities.get(cause_id, "")
effect = _resolve_target(effect_id) if effect_id else ""
```

### 4.2 Post-Fix Corpus Statistics

- **Total Relations Processed:** 391
- **Distinct Non-Self Relations ($A \to B$):** 379 (96.93%)
- **Residual Self-Loops:** 12 (3.07%, cases where biological feedback or autophosphorylation was explicitly annotated in the source text).

Sample authentic recovered relations:
- `PMC1804205`: `PhoQ -> PmrA`, `PhoP -> PmrD`, `PmrA -> pbgP`, `PmrB -> PmrA`
- `PMC1874608`: `Mlc -> hilE`, `Mlc -> hilD`, `HilD -> hilA`, `HilA -> SPI1`

---

## 5. Examples Cache Rebuilding & UI Verification

1. **Cache Regeneration:** Executed `RealExamplesService.prebuild_catalog()` and updated `data/real_papers/examples_cache.json`.
2. **Server Reload:** Restarted the EVRYN application daemon (`http://127.0.0.1:8000`).
3. **API & Browser Verification:**
   - Queried `/api/examples/paper/PMC1804205` and `/api/examples/paper/PMC1874608`: confirmed 0 artificial `A -> A` loops in gold relations.
   - Ran `node scripts/verify_browser_ui.js`: 0 console errors, modal causal comparison rendered clean authentic pairs.

---

## 6. Scientific Integrity & Benchmark Versioning Guarantee

- **Benchmark V1 Preserved:** As required by the zero-leakage protocol, `CURATED_REAL_PAPERS_V1` and `split_manifest.json` remain untouched and reproducible.
- **Reporting Transparency:** The benchmark evaluator reports both V1 and V2, ensuring that all historical progress is fully auditable and reproducible without revisionism.
