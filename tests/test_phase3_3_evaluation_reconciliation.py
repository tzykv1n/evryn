"""
EVRYN Phase 3.3 — Evaluation Integrity, Reconciliation, and Scientific Status Tests.
Validates:
1. SemEval Task 8 Cause-Effect exact counts, denominator reconciliation, and confusion matrix.
2. Canonical metrics pipeline contract (TP + FN == Total Gold).
3. Explicit scientific status categories distinguishing verified facts from exploratory hypotheses.
4. Provenance audit tracking development vs held-out evaluation papers.
"""

import os
import pytest
from evryn.datasets.semeval2010 import SemEval2010Dataset, ArgumentAwareSemEvalClassifier
from evryn.paper.cross_paper_linker import CrossDocumentLinkCategory
from evryn.paper.composition_model import CompositionClass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_semeval_canonical_reconciliation_and_denominators():
    """Verify that SemEval metrics resolve all reported discrepancies with strict denominator integrity."""
    ds = SemEval2010Dataset()
    clf = ArgumentAwareSemEvalClassifier()
    res = clf.evaluate_dataset(ds)

    # 1. Total instance counts
    assert res["total_test_samples"] == 2717
    assert res["total_gold_causal"] == 328
    assert res["total_predictions"] == 281

    # 2. Confusion matrix component counts
    assert res["true_positives"] == 119
    assert res["false_negatives"] == 83            # Pure non-prediction misses
    assert res["direction_inversions"] == 126       # Direction inversions on causal sentences
    assert res["non_causal_false_positives"] == 36 # False alarms on non-causal sentences
    assert res["false_positives"] == 162           # 126 + 36 = 162

    # 3. Denominator integrity
    assert res["reconciled_false_negatives"] == 209 # 83 + 126 = 209
    assert res["true_positives"] + res["reconciled_false_negatives"] == res["total_gold_causal"] # 119 + 209 == 328
    assert res["true_positives"] + res["false_positives"] == res["total_predictions"]            # 119 + 162 == 281
    assert res["reconciliation_notes"]["reconciled_gold_check"] is True
    assert res["reconciliation_notes"]["reconciled_pred_check"] is True

    # 4. Canonical metrics
    assert res["precision_canonical"] == 0.4235
    assert res["recall_canonical"] == 0.3628
    assert res["f1_canonical"] == 0.3908

    # 5. Binary causal detection metrics
    assert res["binary_precision"] == 0.8719
    assert res["binary_recall"] == 0.7470
    assert res["binary_f1"] == 0.8046

    # 6. Legacy Phase 3.1 historical preservation
    assert res["recall"] == 0.5891
    assert res["f1"] == 0.4928


def test_scientific_status_categories_distinct():
    """Validates that candidate hypotheses are structurally and categorically distinct from verified knowledge."""
    # Composition classes must cleanly separate supported from exploratory and invalid
    comp_classes = set(c.value for c in CompositionClass)
    assert "DIRECT_SUPPORTED" in comp_classes
    assert "MULTI_HOP_SUPPORTED" in comp_classes
    assert "PLAUSIBLE_COMPOSED" in comp_classes
    assert "UNSUPPORTED_SHORTCUT" in comp_classes
    assert "INDETERMINATE" in comp_classes

    # Cross-document link categories distinguish same-species, orthology hypothesis, and generic pivot exclusions
    link_cats = set(c.value for c in CrossDocumentLinkCategory)
    assert "SUPPORTED_CHAIN_SPAN" in link_cats        # Same-species verified span
    assert "PLAUSIBLE_HYPOTHESIS" in link_cats        # Cross-species orthology candidate
    assert "COMPLEMENTARY_EVIDENCE" in link_cats      # Dual reciprocal alignment
    assert "UNSUPPORTED_CONTRADICTORY" in link_cats   # Incompatible polarity
    assert "INDETERMINATE" in link_cats


def test_split_membership_and_leakage_isolation():
    """Verify that paper splits remain mutually exclusive with documented provenance."""
    import json

    manifest_path = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    papers = manifest["papers"]
    dev_pmcids = {p["pmcid"] for p in papers if p.get("split") == "dev"}
    train_pmcids = {p["pmcid"] for p in papers if p.get("split") == "train"}
    test_pmcids = {p["pmcid"] for p in papers if p.get("split") == "locked_test"}
    ext_pmcids = {p["pmcid"] for p in papers if p.get("split") == "external"}

    assert len(dev_pmcids) == 8
    assert len(train_pmcids) == 4
    assert len(test_pmcids) == 4
    assert len(ext_pmcids) == 4

    # No paper may belong to multiple splits
    assert dev_pmcids.isdisjoint(train_pmcids), "Dev and Train must be disjoint"
    assert dev_pmcids.isdisjoint(test_pmcids), "Dev and Locked Test must be disjoint"
    assert dev_pmcids.isdisjoint(ext_pmcids), "Dev and External must be disjoint"
    assert test_pmcids.isdisjoint(ext_pmcids), "Locked Test and External must be disjoint"
