# pytest tests/test_causal_dataset_loader.py
# python -m pytest tests/test_dataset_loader.py

"""Tests for Tübingen Cause-Effect dataset loader."""

import pytest
import numpy as np

from evryn.causal.datasets.tuebingen_loader import TuebingenPairLoader


def test_tuebingen_loader_clean():
    loader = TuebingenPairLoader()
    clean_tasks = loader.load_clean_pairs(augment_swapped=False)

    assert len(clean_tasks) == 85, f"Expected exactly 85 pairs as in the paper, got {len(clean_tasks)}"
    for task in clean_tasks:
        assert task.observations.ndim == 2
        assert task.observations.shape[1] == 2
        assert np.all(np.isfinite(task.observations))
        assert task.label in (0, 1)


def test_tuebingen_augmentation():
    """Verify that swapped augmentation doubles the 85 datasets to 170 and balances classes."""
    loader = TuebingenPairLoader()
    clean_tasks = loader.load_clean_pairs(augment_swapped=False)
    aug_tasks = loader.load_clean_pairs(augment_swapped=True)

    assert len(clean_tasks) == 85
    assert len(aug_tasks) == 170, f"Expected 170 augmented datasets (85 * 2), got {len(aug_tasks)}"

    labels = [t.label for t in aug_tasks]
    count_0 = labels.count(0)
    count_1 = labels.count(1)
    assert count_0 == count_1 == 85

