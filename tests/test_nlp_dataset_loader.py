# pytest tests/test_nlp_dataset_loader.py

from evryn.nlp.datasets.semeval import SemEval2010Dataset
from evryn.nlp.core.config import DatasetConfig


def test_semeval_dataset_split():
    cfg = DatasetConfig(val_ratio=0.15, seed=42)
    ds = SemEval2010Dataset(config=cfg).load()

    train_exs = ds.get_train_examples()
    val_exs = ds.get_val_examples()
    test_exs = ds.get_test_examples()

    assert len(train_exs) == 6800
    assert len(val_exs) == 1200
    assert len(test_exs) == 2717

    train_ids = {e.example_id for e in train_exs}
    val_ids = {e.example_id for e in val_exs}
    test_ids = {e.example_id for e in test_exs}

    assert len(train_ids.intersection(val_ids)) == 0
    assert len(train_ids.intersection(test_ids)) == 0
    assert len(val_ids.intersection(test_ids)) == 0
