# pytest tests/test_causal_meta_features.py
# python -m pytest tests/test_meta_features.py

"""Tests for meta-feature extraction (Table 1 of the paper)."""

import pytest
import numpy as np

from evryn.causal.features.meta_features import MetaFeatureExtractor


def test_meta_features_shape_and_names():
    extractor = MetaFeatureExtractor(include_expanded=False)
    assert len(extractor.feature_names) == 6

    rng = np.random.default_rng(42)
    data = rng.normal(0, 1, size=(500, 2))
    feats = extractor.extract(data)

    assert isinstance(feats, np.ndarray)
    assert feats.shape == (6,)
    assert np.all(np.isfinite(feats))


def test_meta_features_statistical_validity():
    extractor = MetaFeatureExtractor(include_expanded=False)
    rng = np.random.default_rng(42)

    x = rng.normal(0, 1, 500)
    y = 2.0 * x + rng.normal(0, 0.2, 500)
    data = np.column_stack([x, y])

    feats = extractor.extract(data)
    corr_idx = extractor.feature_names.index("correlation")
    assert feats[corr_idx] > 0.85

    mi_idx = extractor.feature_names.index("mutual_information")
    assert feats[mi_idx] > 0.5


def test_meta_features_batch():
    extractor = MetaFeatureExtractor()
    rng = np.random.default_rng(42)
    datasets = [rng.normal(0, 1, size=(100, 2)) for _ in range(5)]
    batch_matrix = extractor.extract_batch(datasets)

    assert batch_matrix.shape == (5, 6)
