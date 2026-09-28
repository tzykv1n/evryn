# python cli.py evaluate

import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    confusion_matrix,
    accuracy_score,
)
from ..core.types import CausalRelationType


def compute_relation_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    labels = [0, 1, 2]
    target_names = ["NO_RELATION", "FORWARD", "BACKWARD"]

    p_per_class = precision_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    r_per_class = recall_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    f1_per_class = f1_score(y_true, y_pred, labels=labels, average=None, zero_division=0)

    fwd_f1 = float(f1_per_class[1])
    bwd_f1 = float(f1_per_class[2])
    causal_macro_f1 = float((fwd_f1 + bwd_f1) / 2.0)

    macro_f1 = float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0))
    micro_f1 = float(f1_score(y_true, y_pred, labels=labels, average="micro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    acc = float(accuracy_score(y_true, y_pred))

    y_true_binary = (y_true > 0).astype(int)
    y_pred_binary = (y_pred > 0).astype(int)
    binary_prec = float(precision_score(y_true_binary, y_pred_binary, zero_division=0))
    binary_rec = float(recall_score(y_true_binary, y_pred_binary, zero_division=0))
    binary_f1 = float(f1_score(y_true_binary, y_pred_binary, zero_division=0))

    cm = confusion_matrix(y_true, y_pred, labels=labels)

    class_metrics = {}
    for idx, name in enumerate(target_names):
        class_metrics[name] = {
            "precision": float(p_per_class[idx]),
            "recall": float(r_per_class[idx]),
            "f1": float(f1_per_class[idx]),
            "support": int(np.sum(y_true == idx)),
        }

    return {
        "accuracy": acc,
        "balanced_accuracy": bal_acc,
        "macro_f1": macro_f1,
        "micro_f1": micro_f1,
        "weighted_f1": weighted_f1,
        "causal_macro_f1": causal_macro_f1,
        "forward_f1": fwd_f1,
        "backward_f1": bwd_f1,
        "binary_causal": {
            "precision": binary_prec,
            "recall": binary_rec,
            "f1": binary_f1,
        },
        "per_class": class_metrics,
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_labels": target_names,
    }
