# meflux table2
# python -m causality_in_flux.experiments.reproduce_table2

"""Reproduction of Table 2 from Seng, Busch & Kersting (2024/2025).

Table 2: Evidence Matching using Random Forests.
Trains a Random Forest classifier 5 times on different 70% train / 30% test splits
using the meta-features derived from the Tübingen Cause-Effect Pairs dataset.
Compares against the 0.50 random baseline.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from ..datasets.tuebingen_loader import TuebingenPairLoader
from ..features.meta_features import MetaFeatureExtractor


def run_table2_experiment(
    data_dir: Optional[str] = None,
    num_splits: int = 5,
    train_size: float = 0.70,
    random_seeds: Optional[List[int]] = None,
    include_expanded: bool = True,
    n_estimators: int = 100,
) -> Dict[str, Any]:
    """Run the 5-fold Random Forest classification experiment.

    Returns:
        dict containing split accuracies, mean, std, and dataframe.
    """
    seeds = random_seeds or [78, 36, 47, 56, 10]

    loader = TuebingenPairLoader(data_dir=data_dir)
    tasks = loader.load_clean_pairs(augment_swapped=True)

    print(f"Loaded {len(tasks)} augmented Tübingen datasets.")

    extractor = MetaFeatureExtractor(include_expanded=include_expanded)
    feature_matrix = []
    labels = []
    task_ids = []

    print("Extracting meta-features (Skewness, Kurtosis, Mutual Information, Correlation)...")
    for task in tasks:
        feats = extractor.extract(task.observations)
        feature_matrix.append(feats)
        labels.append(task.label)
        task_ids.append(task.task_id)

    X = np.vstack(feature_matrix)
    y = np.array(labels, dtype=int)

    split_accuracies = []

    for i in range(num_splits):
        seed = seeds[i % len(seeds)]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            train_size=train_size,
            random_state=seed,
            stratify=y,
        )

        clf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=6,
            random_state=seed,
        )
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        acc = float(accuracy_score(y_test, y_pred))
        split_accuracies.append(acc)

    mean_acc = float(np.mean(split_accuracies))
    std_acc = float(np.std(split_accuracies))

    results = {
        "num_datasets": len(tasks),
        "split_accuracies": split_accuracies,
        "average_accuracy": mean_acc,
        "std_accuracy": std_acc,
        "feature_names": extractor.feature_names,
    }

    return results


def print_table2_results(results: Dict[str, Any]) -> None:
    """Print results formatted as Table 2 from the paper."""
    accs = results["split_accuracies"]
    mean_val = results["average_accuracy"]
    std_val = results["std_accuracy"]

    print("\n" + "=" * 65)
    print("Table 2: Evidence Matching using Random Forests (Tübingen Benchmark)")
    print("=" * 65)
    header = " | ".join([f"Split {i+1}" for i in range(len(accs))]) + " | Average"
    print(header)
    print("-" * len(header))
    vals = " | ".join([f"{a:0.2f}   " for a in accs]) + f" | {mean_val:0.2f} ± {std_val:0.2f}"
    print(vals)
    print("=" * 65)
    print("Paper Reported Average: 0.79 ± 0.07  (Baseline: 0.50 Random Chance)")
    print(f"Reproduced Average:     {mean_val:0.2f} ± {std_val:0.2f}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    res = run_table2_experiment()
    print_table2_results(res)
