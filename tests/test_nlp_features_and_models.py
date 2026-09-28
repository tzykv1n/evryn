# pytest tests/test_nlp_features_and_models.py

import numpy as np
from evryn.nlp.core.types import RelationExample, CausalRelationType
from evryn.nlp.features.tfidf_extractor import TFIDFExtractor
from evryn.nlp.models.classical_baseline import LogisticRegressionBaseline
from evryn.nlp.evaluation.metrics import compute_relation_metrics
from evryn.nlp.evaluation.error_analysis import ErrorAnalyzer


def test_tfidf_and_model_pipeline():
    exs = [
        RelationExample("1", "Smoking causes cancer.", "Smoking", "cancer", (0, 7), (15, 21), CausalRelationType.FORWARD, "Cause-Effect(e1,e2)"),
        RelationExample("2", "Cancer caused by smoking.", "Cancer", "smoking", (0, 6), (17, 24), CausalRelationType.BACKWARD, "Cause-Effect(e2,e1)"),
        RelationExample("3", "The bird sat on the branch.", "bird", "branch", (4, 8), (20, 26), CausalRelationType.NO_RELATION, "Other"),
        RelationExample("4", "Viruses induce illness.", "Viruses", "illness", (0, 7), (15, 22), CausalRelationType.FORWARD, "Cause-Effect(e1,e2)"),
    ]

    ext = TFIDFExtractor()
    X = ext.fit_transform(exs, dataset_hash="test")
    assert X.shape[0] == 4

    y = np.array([int(e.relation_type) for e in exs])
    clf = LogisticRegressionBaseline().fit(X, y)
    preds = clf.predict(X)
    assert len(preds) == 4

    metrics = compute_relation_metrics(y, preds)
    assert "causal_macro_f1" in metrics
    assert "accuracy" in metrics

    analyzer = ErrorAnalyzer(exs, y, preds)
    err = analyzer.analyze()
    assert "reversal_count" in err
    assert "false_positive_count" in err
