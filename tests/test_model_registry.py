# pytest tests/test_model_registry.py
# evryn models

import numpy as np
import pytest
from evryn.models.registry import (
    ModelRegistry,
    DenseEmbeddingModel,
    LexicalEmbeddingModel,
    CalibratedVerifier,
    get_model_registry,
)


def test_model_registry_lifecycle():
    reg = get_model_registry()
    models = reg.list_models()
    names = {m["name"] for m in models}
    assert "dense-minilm" in names
    assert "calibrated-verifier" in names
    assert "lexical-tfidf" in names

    verifier = reg.get("calibrated-verifier")
    assert isinstance(verifier, CalibratedVerifier)


def test_dense_and_lexical_models():
    reg = get_model_registry()
    dense = reg.get("dense-minilm")
    assert dense.is_available

    embs = dense.encode(["EGFR activates MAPK pathway", "Cellular senescence and aging"])
    assert embs.shape == (2, 384)
    sim = dense.similarity("EGFR activates MAPK", "EGFR stimulates MAPK")
    assert 0.0 <= sim <= 1.0

    lex = LexicalEmbeddingModel()
    corpus = [
        "interleukin-6 induces signal transducer activation",
        "hypoxia triggers hif-1alpha stabilization",
    ]
    lex.fit(corpus)
    sim_lex = lex.similarity("interleukin-6 induces activation", "interleukin-6 induces signal")
    assert sim_lex > 0.0


def test_calibrated_verifier_diagnostics():
    verifier = CalibratedVerifier(abstention_threshold=0.40)
    rng = np.random.RandomState(42)
    X = rng.randn(50, 4)
    y = (X[:, 0] > 0).astype(int)

    verifier.fit_calibration(X, y)
    cand = verifier.verify_candidate(np.array([1.5, 0.5, 0.0, 0.0]))
    assert "calibrated_probability" in cand
    assert "decision" in cand
    assert "confidence" in cand

    metrics = verifier.evaluate_calibration(X, y, n_bins=5)
    assert 0.0 <= metrics.brier_score <= 1.0
    assert 0.0 <= metrics.expected_calibration_error <= 1.0
    assert 0.0 <= metrics.abstention_rate <= 1.0
    assert len(metrics.reliability_bins) > 0
