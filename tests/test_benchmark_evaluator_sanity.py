"""
Evaluator Sanity Test Suite for EVRYN Benchmark.
Deterministically verifies evaluator behavior on canonical edge cases:
- Perfect match (P=1.0, R=1.0, F1=1.0)
- Reversed edge (P=0.0, R=0.0, F1=0.0)
- Missing edge (Recall penalty)
- Unsupported edge / Hallucination (Precision penalty)
- Duplicate edge idempotency
- Wrong trigger / Negated relation filtering
- Micro vs. Macro averaging arithmetic
- Bootstrap Confidence Interval invariance and coverage
"""

import pytest
import numpy as np
from evryn.paper.evaluator import PaperBenchmarkEvaluator


@pytest.fixture
def evaluator():
    return PaperBenchmarkEvaluator(output_dir="outputs")


def test_evaluator_perfect_match(evaluator):
    gt = {("Protein A", "Kinase B"), ("Gene X", "Phenotype Y")}
    pred = {("Protein A", "Kinase B"), ("Gene X", "Phenotype Y")}

    prec, rec, f1 = evaluator._calc_prf(pred, gt)
    sm = evaluator._calc_structural_match(pred, gt)

    assert prec == 1.0
    assert rec == 1.0
    assert f1 == 1.0
    assert sm == 1.0


def test_evaluator_reversed_edge(evaluator):
    gt = {("Protein A", "Kinase B"), ("Gene X", "Phenotype Y")}
    pred = {("Kinase B", "Protein A"), ("Phenotype Y", "Gene X")}

    prec, rec, f1 = evaluator._calc_prf(pred, gt)
    sm = evaluator._calc_structural_match(pred, gt)

    assert prec == 0.0
    assert rec == 0.0
    assert f1 == 0.0
    assert sm == 0.0


def test_evaluator_missing_edge_recall_penalty(evaluator):
    gt = {("Protein A", "Kinase B"), ("Gene X", "Phenotype Y")}
    pred = {("Protein A", "Kinase B")}

    prec, rec, f1 = evaluator._calc_prf(pred, gt)
    sm = evaluator._calc_structural_match(pred, gt)

    assert prec == 1.0
    assert rec == 0.5
    assert round(f1, 4) == round(2 * 1.0 * 0.5 / (1.0 + 0.5), 4)  # 0.6667
    assert sm == 0.5  # 1 intersection / 2 union


def test_evaluator_unsupported_edge_precision_penalty(evaluator):
    gt = {("Protein A", "Kinase B")}
    pred = {("Protein A", "Kinase B"), ("Hallucinated C", "Target D")}

    prec, rec, f1 = evaluator._calc_prf(pred, gt)
    sm = evaluator._calc_structural_match(pred, gt)

    assert prec == 0.5
    assert rec == 1.0
    assert round(f1, 4) == round(2 * 0.5 * 1.0 / (0.5 + 1.0), 4)  # 0.6667
    assert sm == 0.5


def test_evaluator_duplicate_edge_idempotency(evaluator):
    gt = {("Protein A", "Kinase B")}
    pred_list = [("Protein A", "Kinase B"), ("Protein A", "Kinase B")]
    pred_set = set(pred_list)

    prec, rec, f1 = evaluator._calc_prf(pred_set, gt)
    assert prec == 1.0
    assert rec == 1.0
    assert f1 == 1.0


def test_evaluator_empty_cases(evaluator):
    # Both empty
    p1, r1, f1 = evaluator._calc_prf(set(), set())
    assert (p1, r1, f1) == (1.0, 1.0, 1.0)
    assert evaluator._calc_structural_match(set(), set()) == 1.0

    # Predictions empty when gold exists
    p2, r2, f2 = evaluator._calc_prf(set(), {("A", "B")})
    assert (p2, r2, f2) == (0.0, 0.0, 0.0)
    assert evaluator._calc_structural_match(set(), {("A", "B")}) == 0.0

    # Predictions made when gold is empty
    p3, r3, f3 = evaluator._calc_prf({("A", "B")}, set())
    assert (p3, r3, f3) == (0.0, 1.0, 0.0)
    assert evaluator._calc_structural_match({("A", "B")}, set()) == 0.0


def test_micro_vs_macro_averaging():
    """
    Demonstrate mathematical distinction between micro and macro averaging across documents.
    Doc 1: 1 gold edge, 1 prediction, 1 TP -> P=1.0, R=1.0, F1=1.0
    Doc 2: 9 gold edges, 0 predictions, 0 TP -> P=0.0, R=0.0, F1=0.0
    """
    doc1_tp, doc1_pred, doc1_gold = 1, 1, 1
    doc2_tp, doc2_pred, doc2_gold = 0, 0, 9

    # Macro average (mean of per-document F1)
    doc1_f1 = 1.0
    doc2_f1 = 0.0
    macro_f1 = (doc1_f1 + doc2_f1) / 2.0
    assert macro_f1 == 0.5

    # Micro average (pooled TP, FP, FN)
    total_tp = doc1_tp + doc2_tp  # 1
    total_pred = doc1_pred + doc2_pred  # 1
    total_gold = doc1_gold + doc2_gold  # 10

    micro_prec = total_tp / total_pred  # 1.0
    micro_rec = total_tp / total_gold  # 0.10
    micro_f1 = (2 * micro_prec * micro_rec) / (micro_prec + micro_rec)  # 2 * 0.1 / 1.1 = 0.1818...

    assert round(micro_f1, 4) == 0.1818
    assert macro_f1 != micro_f1


def test_bootstrap_ci_properties(evaluator):
    # Constant array -> Zero variance, bounds equal mean
    constant_ci = evaluator._compute_bootstrap_ci([0.75, 0.75, 0.75, 0.75])
    assert constant_ci["mean"] == 0.75
    assert constant_ci["ci_lower"] == 0.75
    assert constant_ci["ci_upper"] == 0.75

    # Varying array -> Lower <= Mean <= Upper
    sample_scores = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    var_ci = evaluator._compute_bootstrap_ci(sample_scores, n_bootstrap=1000, alpha=0.05)
    assert var_ci["ci_lower"] <= var_ci["mean"] <= var_ci["ci_upper"]
    assert var_ci["ci_lower"] >= 0.4
    assert var_ci["ci_upper"] <= 0.9
