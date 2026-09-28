# pytest tests/test_causal_causal_discovery.py
# python -m pytest tests/test_causal_discovery.py

"""Tests for causal discovery methods (ANM, LiNGAM)."""

import pytest
import numpy as np

from evryn.causal.discovery.anm import AdditiveNoiseModel, compute_distance_correlation
from evryn.causal.discovery.lingam import LiNGAM


def test_distance_correlation():
    rng = np.random.default_rng(42)
    x = rng.normal(0, 1, 300)
    y = rng.normal(0, 1, 300)
    dcor_ind = compute_distance_correlation(x, y)
    assert dcor_ind < 0.2

    y_dep = x ** 2
    dcor_dep = compute_distance_correlation(x, y_dep)
    assert dcor_dep > 0.4


def test_anm_bivariate_prediction():
    rng = np.random.default_rng(42)
    x0 = rng.uniform(-2, 2, 400)
    x1 = np.sin(x0) + rng.normal(0, 0.2, 400)
    data = np.column_stack([x0, x1])

    anm = AdditiveNoiseModel(random_state=42)
    pred_dir, conf = anm.predict_direction(data)

    assert pred_dir == 0
    assert conf >= 0.5


def test_lingam_bivariate_prediction():
    rng = np.random.default_rng(42)
    x0 = rng.laplace(0, 1, 500)
    x1 = 1.5 * x0 + rng.laplace(0, 0.5, 500)
    data = np.column_stack([x0, x1])

    lingam = LiNGAM(random_state=42)
    pred_dir, conf = lingam.predict_direction(data)

    assert pred_dir == 0
    assert conf >= 0.5
