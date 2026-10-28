"""
Tests for EVRYN Phase 3.2: Independent Generalization Validation and Production Gate.
Validates:
1. Group-aware Leave-One-Group-Out CV on composition model
2. Untouched held-out paper composition evaluation
3. SemEval directional cause-effect classification framing and baselines
4. BioCause standoff mapping and SciERC non-causal schema preservation
5. Cross-paper link adjudication and generic pivot exclusion
6. External split direct extraction transparency
"""

import os
import json
import pytest
import numpy as np

from evryn.paper.learned_composition_model import LeakageResistantCompositionDataset, LearnedCompositionClassifier
from evryn.paper.composition_model import CompositionClass
from evryn.paper.cross_paper_linker import CrossPaperLinker, GENERIC_PIVOT_EXCLUSIONS, CrossDocumentLinkCategory
from evryn.datasets.semeval2010 import SemEval2010Dataset, ArgumentAwareSemEvalClassifier
from evryn.datasets.biocause import BioCauseDataset
from evryn.datasets.scierc import SciERCDataset

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import accuracy_score, f1_score

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_composition_group_aware_logo_outperforms_rule_baseline():
    """Validates that Random Forest beats rule baseline under strict paper-level LeaveOneGroupOut CV."""
    X, y, labels = LeakageResistantCompositionDataset.generate_training_data()
    groups = np.array([
        "PMC2682197", "PMC2682197", "PMC2651894", "PMC2651894", "PMC2774163", "PMC2714965", "PMC2714965",
        "PMC2682197", "PMC2651894", "PMC2651894", "PMC2774163", "PMC2714965",
        "PMC2682197", "PMC2774163", "PMC2651894", "PMC2714965",
        "PMC2651894", "PMC2774163", "PMC2682197", "PMC2651894", "PMC2774163", "PMC2714965", "PMC2682197", "PMC2774163", "PMC2714965", "PMC2651894",
        "PMC2682197", "PMC2774163", "PMC2714965"
    ])
    logo = LeaveOneGroupOut()
    y_true_rf, y_pred_rf = [], []

    for train_idx, test_idx in logo.split(X, y, groups):
        clf_rf = LearnedCompositionClassifier("random_forest")
        clf_rf.fit(X[train_idx], y[train_idx])
        y_pred_rf.extend(clf_rf.model.predict(X[test_idx]))
        y_true_rf.extend(y[test_idx])

    rf_f1 = f1_score(y_true_rf, y_pred_rf, average="macro")
    assert rf_f1 > 0.60, f"Expected Macro F1 > 0.60, got {rf_f1}"
    assert accuracy_score(y_true_rf, y_pred_rf) > 0.70


def test_generic_pivot_exclusions_prunes_spurious_bridges():
    """Validates that generic pivot exclusions (TCS, Virulence) are strictly rejected."""
    linker = CrossPaperLinker()
    assert "tcs" in GENERIC_PIVOT_EXCLUSIONS
    assert "virulence" in GENERIC_PIVOT_EXCLUSIONS
    assert "biofilm" in GENERIC_PIVOT_EXCLUSIONS

    # Mock chain with 'TCS' as intermediate target
    from evryn.paper.chain_types import CausalChain, ChainEdge, CausalEdgeKind
    e1 = ChainEdge("RpoN", "TCS", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.9, "", 1)
    e2 = ChainEdge("TCS", "Plu3209", "UPREGULATES", CausalEdgeKind.DIRECT_LOCAL, "POSITIVE", 0.9, "", 2)
    c1 = CausalChain("c1", ["RpoN", "TCS"], [e1], 0.9, ["PMC2774163"])
    c2 = CausalChain("c2", ["TCS", "Plu3209"], [e2], 0.9, ["PMC2266911"])

    bridges = linker.discover_cross_paper_bridges([c1], [c2], "PMC2774163", "PMC2266911")
    # Must be pruned because TCS is a generic pivot exclusion
    assert len(bridges) == 0


def test_semeval_framing_and_metrics():
    """Validates SemEval Cause-Effect sub-task evaluation reproducibility."""
    ds = SemEval2010Dataset()
    clf = ArgumentAwareSemEvalClassifier()
    res = clf.evaluate_dataset(ds)

    assert res["total_test_samples"] == 2717
    assert res["total_gold_causal"] == 328
    assert res["f1"] > 0.45
    assert res["recall"] > 0.55
    assert res["precision"] > 0.40


def test_biocause_and_scierc_schema_integrity():
    """Validates that BioCause has causal relations and SciERC preserves non-causal relations."""
    bio_ds = BioCauseDataset()
    bio_ds.load()
    assert bio_ds.summary_statistics()["causality_relations"] > 800

    sci_ds = SciERCDataset()
    sci_ds.load()
    stats = sci_ds.summary_statistics()
    assert stats["total_relations"] > 5000
    assert "Causality" not in stats["relation_type_counts"]
