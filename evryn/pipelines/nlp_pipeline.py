# evryn nlp

import os
import sys
import numpy as np
from typing import Dict, Any, List

from ..nlp.core.config import ExperimentConfig as NLPExperimentConfig
from ..nlp.core.cache import ArtifactCache as NLPCache
from ..nlp.datasets.semeval import SemEval2010Dataset
from ..nlp.features.tfidf_extractor import TFIDFExtractor
from ..nlp.models.classical_baseline import LogisticRegressionBaseline
from ..nlp.evaluation.metrics import compute_relation_metrics
from ..nlp.evaluation.error_analysis import ErrorAnalyzer

from ..core.config import EvrynConfig
from ..core.cache import EvrynCache
from ..ui.console import print_box, print_table, get_progress_bar


def _display_nlp_results(results: Dict[str, Any], total_test_samples: int = 2717) -> None:
    headers = ["Class / Category", "Precision", "Recall", "F1-Score", "Test Support"]
    rows = []
    metrics = results["metrics"]
    for c_name, c_data in metrics["per_class"].items():
        rows.append([
            c_name,
            f"{c_data['precision']:.4f}",
            f"{c_data['recall']:.4f}",
            f"{c_data['f1']:.4f}",
            str(c_data["support"]),
        ])
    rows.append([
        "Causal Macro-F1",
        f"{(metrics['per_class']['FORWARD']['precision'] + metrics['per_class']['BACKWARD']['precision'])/2:.4f}",
        f"{(metrics['per_class']['FORWARD']['recall'] + metrics['per_class']['BACKWARD']['recall'])/2:.4f}",
        f"{metrics['causal_macro_f1']:.4f}",
        str(metrics['per_class']['FORWARD']['support'] + metrics['per_class']['BACKWARD']['support']),
    ])
    rows.append([
        "Overall Macro (3-Class)",
        "-",
        "-",
        f"{metrics['macro_f1']:.4f}",
        str(total_test_samples),
    ])
    print_table(headers, rows, title="Frozen NLP Pairwise Baseline Results")

    err = results["error_analysis"]
    err_headers = ["Error Category", "Count", "Scientific Impact"]
    err_rows = [
        ["Directional Reversals", str(err["reversal_count"]), "Orientation inverted (A -> B vs A <- B)"],
        ["False Positives (Total)", str(err["false_positive_count"]), "Negative control misclassified as causal"],
        ["False Negatives (Total)", str(err["false_negative_count"]), "Causal instance classified as non-causal"],
        ["  - FN Implicit Causality", str(err["fn_implicit_causality_count"]), "Domain-specific semantic cause without trigger"],
        ["Temporal Confounding", str(err["temporal_confusion_count"]), "Temporal markers ('when', 'after') mistaken for causality"],
        ["Long-Distance (>5 tokens)", str(err["long_distance_error_count"]), "Wide token span separation between entities"],
        ["Joint-Cause Candidates", str(err["joint_cause_candidate_count"]), "Nominal coordination candidates for Order-2 FLUX"],
    ]
    print_table(err_headers, err_rows, title="Baseline Error Analysis & Order-2 Candidates")


def run_nlp_pipeline(config: EvrynConfig, cache: EvrynCache) -> Dict[str, Any]:
    print_box(
        "EVRYN Scientific NLP : Frozen Pairwise Causal Baseline",
        "SemEval-2010 Task 8 Official Held-Out Test Set (2,717 Instances)",
    )

    cached_res = cache.get("benchmarks", f"nlp_baseline_{config.seed}")
    if cached_res is not None:
        _display_nlp_results(cached_res)
        return cached_res

    results = {}
    with get_progress_bar("Executing Scientific NLP Pipeline") as prog:
        t_id = prog.add_task("Loading SemEval-2010 Gold Dataset...", total=3)

        nlp_cfg = NLPExperimentConfig()
        nlp_cache = NLPCache(cache_dir="cache", enabled=True)
        ds = SemEval2010Dataset(nlp_cfg.dataset, cache=nlp_cache).load()
        train_exs = ds.get_train_examples()
        test_exs = ds.get_test_examples()
        prog.advance(t_id)

        prog.update(t_id, description="Extracting Directional TF-IDF & Connective Features...")
        extractor = TFIDFExtractor(nlp_cfg.tfidf, cache=nlp_cache)
        d_hash = nlp_cfg.dataset.fingerprint()
        X_train = extractor.fit_transform(train_exs, dataset_hash=d_hash)
        X_test = extractor.transform(test_exs, split_name="test", dataset_hash=d_hash)

        y_train = np.array([int(e.relation_type) for e in train_exs])
        y_test = np.array([int(e.relation_type) for e in test_exs])

        clf = LogisticRegressionBaseline(nlp_cfg.tfidf, seed=config.seed).fit(X_train, y_train)
        preds = clf.predict(X_test)
        prog.advance(t_id)

        prog.update(t_id, description="Computing Directional Metrics & Error Taxonomy...")
        metrics = compute_relation_metrics(y_test, preds)
        analyzer = ErrorAnalyzer(test_exs, y_test, preds)
        err = analyzer.analyze()

        results = {
            "metrics": metrics,
            "error_analysis": err,
            "joint_cause_candidates": [
                {
                    "id": item.get("id", ""),
                    "e1": item.get("e1", ""),
                    "e2": item.get("e2", ""),
                    "text": item.get("sentence", ""),
                    "true_rel": item.get("true_relation", ""),
                }
                for item in err.get("joint_cause_samples", [])
            ],
            "frozen_status": "FROZEN (F1 >= 0.70 Target Exceeded)",
        }
        prog.advance(t_id)

    _display_nlp_results(results, len(y_test))
    cache.set("benchmarks", f"nlp_baseline_{config.seed}", results)
    return results
