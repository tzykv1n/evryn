# pytest tests/test_nlp_cache.py

import os
import shutil
from evryn.nlp.core.cache import ArtifactCache


def test_cache_roundtrip(tmp_path):
    cache = ArtifactCache(cache_dir=str(tmp_path / "cache"), enabled=True)
    stage = "test_stage"
    key = "sample_key_123"
    data = {"matrix": [1, 2, 3], "name": "sample"}

    assert not cache.has(stage, key)
    assert cache.get(stage, key) is None

    cache.set(stage, key, data, {"sample_count": 3})
    assert cache.has(stage, key)

    loaded = cache.get(stage, key)
    assert loaded == data

    entries = cache.list_entries()
    assert len(entries) == 1
    assert entries[0]["key_hash"] == key

    cache.invalidate(stage=stage)
    assert not cache.has(stage, key)
