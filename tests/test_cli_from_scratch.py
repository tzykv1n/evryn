# pytest tests/test_cli_from_scratch.py

import os
import shutil
import pytest

from evryn.cli import build_parser, _is_scratch_mode
from evryn.core.cache import EvrynCache
from evryn.core.config import EvrynConfig
from evryn.pipelines.evryn_pipeline import run_evryn_pipeline


def test_cli_scratch_flag_parsing():
    parser = build_parser()

    cases = [
        (["-s", "all"], True, "all"),
        (["all", "-s"], True, "all"),
        (["--from-scratch", "flux"], True, "flux"),
        (["flux", "--from-scratch"], True, "flux"),
        (["flux", "-s"], True, "flux"),
        (["multivariate", "--force"], True, "multivariate"),
        (["-s", "nlp"], True, "nlp"),
        (["hypothesize", "-s"], True, "hypothesize"),
        (["all"], False, "all"),
        (["flux"], False, "flux"),
        (["multivariate"], False, "multivariate"),
        (["nlp"], False, "nlp"),
        (["hypothesize"], False, "hypothesize"),
    ]

    for argv, expected_scratch, expected_cmd in cases:
        args = parser.parse_args(argv)
        assert _is_scratch_mode(args) == expected_scratch
        assert args.command == expected_cmd


def test_cache_force_rebuild_bypasses_derived_artifacts(tmp_path):
    c_dir = str(tmp_path / "cache")
    cache_normal = EvrynCache(cache_dir=c_dir, enabled=True, force_rebuild=False)
    cache_scratch = EvrynCache(cache_dir=c_dir, enabled=True, force_rebuild=True)

    cache_normal.set("benchmarks", "flux_key_42", {"accuracy": 0.75, "f1": 0.585})

    hit_res = cache_normal.get("benchmarks", "flux_key_42")
    assert hit_res is not None
    assert hit_res["accuracy"] == 0.75
    assert cache_normal.hits == 1

    bypass_res = cache_scratch.get("benchmarks", "flux_key_42")
    assert bypass_res is None
    assert cache_scratch.misses == 1


def test_regenerated_artifacts_become_valid_cache_entries(tmp_path):
    c_dir = str(tmp_path / "cache")
    cache_scratch = EvrynCache(cache_dir=c_dir, enabled=True, force_rebuild=True)
    cache_scratch.set("benchmarks", "nlp_key_42", {"causal_macro_f1": 0.8455})

    cache_next = EvrynCache(cache_dir=c_dir, enabled=True, force_rebuild=False)
    res = cache_next.get("benchmarks", "nlp_key_42")
    assert res is not None
    assert res["causal_macro_f1"] == 0.8455
    assert cache_next.hits == 1


def test_raw_datasets_remain_available():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sachs_raw = os.path.join(root, "data", "sachs", "sachs_observational.tsv")
    semeval_train = os.path.join(root, "data", "semeval2010", "TRAIN_FILE.TXT")
    semeval_test = os.path.join(root, "data", "semeval2010", "TEST_FILE_FULL.TXT")

    assert os.path.exists(sachs_raw), f"Missing raw source dataset: {sachs_raw}"
    assert os.path.exists(semeval_train), f"Missing raw source dataset: {semeval_train}"
    assert os.path.exists(semeval_test), f"Missing raw source dataset: {semeval_test}"


def test_deterministic_from_scratch_regeneration(tmp_path):
    c_dir = str(tmp_path / "cache")
    out_dir = str(tmp_path / "out")
    cfg = EvrynConfig(seed=42, output_dir=out_dir)

    cache1 = EvrynCache(cache_dir=c_dir, enabled=True, force_rebuild=True)
    res1 = run_evryn_pipeline(cfg, cache1)

    cache2 = EvrynCache(cache_dir=c_dir, enabled=True, force_rebuild=True)
    res2 = run_evryn_pipeline(cfg, cache2)

    assert res1["num_relations"] == res2["num_relations"]
    assert res1["num_families"] == res2["num_families"]
    assert res1["num_forecasts"] == res2["num_forecasts"]
    assert res1["num_hypotheses"] == res2["num_hypotheses"]

    h_ids1 = [h["hypothesis_id"] if isinstance(h, dict) else h.hypothesis_id for h in res1["hypotheses"]]
    h_ids2 = [h["hypothesis_id"] if isinstance(h, dict) else h.hypothesis_id for h in res2["hypotheses"]]
    assert h_ids1 == h_ids2
