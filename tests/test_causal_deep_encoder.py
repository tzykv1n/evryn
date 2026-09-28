# pytest tests/test_causal_deep_encoder.py
# python -m pytest tests/test_deep_encoder.py

"""Tests for DeepSets permutation-invariant neural encoder."""

import pytest
import numpy as np

from evryn.causal.features.deep_encoder import DeepSetDatasetEncoder


def test_deep_encoder_shapes():
    encoder = DeepSetDatasetEncoder(
        input_dim=2,
        hidden_dim=16,
        embedding_dim=8,
        pooling="mean",
        seed=42,
    )
    data = np.random.randn(100, 2)
    rep = encoder.encode(data)

    assert rep.shape == (8,)
    assert np.all(np.isfinite(rep))

    r, probs = encoder.forward(data)
    assert r.shape == (8,)
    assert probs.shape == (2,)
    assert np.isclose(np.sum(probs), 1.0)


def test_deep_encoder_permutation_invariance():
    """Verify that permuting dataset row ordering does NOT change the learned representation."""
    encoder = DeepSetDatasetEncoder(
        input_dim=2,
        hidden_dim=16,
        embedding_dim=8,
        pooling="mean",
        seed=42,
    )
    rng = np.random.default_rng(42)
    data = rng.normal(0, 1, (150, 2))

    perm_idx = rng.permutation(len(data))
    data_perm = data[perm_idx]

    rep1 = encoder.encode(data)
    rep2 = encoder.encode(data_perm)

    assert np.allclose(rep1, rep2, atol=1e-5)


def test_deep_encoder_train_step():
    encoder = DeepSetDatasetEncoder(hidden_dim=16, embedding_dim=8, seed=42)
    rng = np.random.default_rng(42)
    datasets = [rng.normal(0, 1, (50, 2)) for _ in range(4)]
    labels = [0, 1, 0, 1]

    loss = encoder.train_step(datasets, labels, lr=0.01)
    assert loss > 0.0
    assert np.isfinite(loss)
