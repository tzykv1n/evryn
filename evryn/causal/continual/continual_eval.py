# meflux continual_ablation
# python -m causality_in_flux.experiments.continual_ablation

r"""Continual Learning Evaluation Metrics for Causality in Flux.

Computes:
1. Average Accuracy across tasks: (1/T) \sum_{t=1}^T R_{T, t}
2. Backward Transfer (BWT) / Catastrophic Forgetting:
   BWT = (1 / (T - 1)) \sum_{i=1}^{T-1} (R_{T, i} - R_{i, i})
   where R_{i, j} is performance on task j after training on task i.
   Negative BWT indicates catastrophic forgetting.
3. Forward Transfer (FWT):
   Exploiting prior knowledge to solve new tasks before explicit training.
"""

from typing import List, Dict, Any, Optional
import numpy as np


class ContinualCausalEvaluator:
    """Tracks and evaluates continual causal learning performance over a sequence of tasks."""

    def __init__(self, num_tasks: int):
        self.num_tasks = num_tasks
        self.accuracy_matrix = np.full((num_tasks, num_tasks), np.nan)
        self.task_predictions: List[Dict[str, Any]] = []

    def record_eval(self, trained_up_to_task: int, evaluated_task: int, accuracy: float) -> None:
        """Record accuracy on evaluated_task after learning up to trained_up_to_task (0-indexed)."""
        self.accuracy_matrix[trained_up_to_task, evaluated_task] = accuracy

    def compute_metrics(self) -> Dict[str, float]:
        """Compute standard continual learning metrics."""
        T = self.num_tasks
        final_row = self.accuracy_matrix[T - 1, :]
        valid_final = final_row[~np.isnan(final_row)]
        avg_acc = float(np.mean(valid_final)) if len(valid_final) > 0 else 0.0

        bwt_vals = []
        for i in range(T - 1):
            r_final = self.accuracy_matrix[T - 1, i]
            r_diag = self.accuracy_matrix[i, i]
            if not np.isnan(r_final) and not np.isnan(r_diag):
                bwt_vals.append(r_final - r_diag)

        bwt = float(np.mean(bwt_vals)) if len(bwt_vals) > 0 else 0.0

        forgetting = float(max(0.0, -bwt))

        return {
            "average_accuracy": avg_acc,
            "backward_transfer": bwt,
            "catastrophic_forgetting": forgetting,
        }
