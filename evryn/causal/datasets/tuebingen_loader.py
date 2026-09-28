# meflux --help

"""Tübingen Cause-Effect Pairs Dataset Loader.

Loads, validates, and augments the Tübingen cause-effect pairs benchmark
as described in Section 5.1 of Seng, Busch & Kersting (2024/2025):
- 108 total pairs in the repository.
- Excludes multi-dimensional, corrupted, or sub-109 sample pairs, leaving exactly 85 clean bivariate pairs.
- Data augmentation: for each pair D = {(x_i, y_i)} with class 0 (X -> Y),
  adds D' = {(y_i, x_i)} with class 1 (Y -> X), doubling the total datasets to exactly 170.
"""

import os
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import networkx as nx
from ..scm.generator import CausalTask


class TuebingenPairLoader:
    """Loads and preprocesses the Tübingen Cause-Effect Pairs benchmark."""

    EXCLUDED_PAIRS = {
        "0052", "0053", "0054", "0055", "0071", "0105",
        "0081", "0082", "0083",
        "0098",
        "0047", "0070", "0107",
        "0093",
    }

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            cands = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "tuebingen"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "tuebingen"),
                "data/tuebingen",
            ]
            for c in cands:
                if os.path.exists(os.path.join(c, "pairmeta.txt")):
                    data_dir = c
                    break
            if data_dir is None:
                data_dir = cands[0]
        self.data_dir = os.path.abspath(data_dir)
        self.meta_file = os.path.join(self.data_dir, "pairmeta.txt")

    def load_clean_pairs(
        self,
        target_pairs: Optional[int] = 85,
        augment_swapped: bool = True,
        min_samples: int = 109,
        max_samples: Optional[int] = 16500,
    ) -> List[CausalTask]:
        """Load the cleaned Tübingen cause-effect pairs.

        Args:
            target_pairs: Number of clean bivariate pairs to load (default: 85, per paper).
                          Pass None to load all valid pairs.
            augment_swapped: Whether to add column-swapped versions to double size (85 -> 170).
            min_samples: Minimum number of samples (default: 109, per paper).
            max_samples: Maximum number of samples (default: 16500, per paper).

        Returns:
            List of CausalTask objects (exactly 85 base pairs, or 170 with swapped augmentation).
        """
        if not os.path.exists(self.meta_file):
            raise FileNotFoundError(
                f"pairmeta.txt not found at {self.meta_file}. Please download the dataset first."
            )

        with open(self.meta_file, "r") as f:
            lines = f.readlines()

        clean_tasks: List[CausalTask] = []

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 6:
                continue

            pair_id_str = parts[0]
            if pair_id_str in self.EXCLUDED_PAIRS:
                continue

            c_start, c_end = int(parts[1]), int(parts[2])
            e_start, e_end = int(parts[3]), int(parts[4])
            weight = float(parts[5])

            if not (c_start == c_end and e_start == e_end):
                continue

            txt_file = os.path.join(self.data_dir, f"pair{pair_id_str}.txt")
            if not os.path.exists(txt_file):
                continue

            try:
                data = np.loadtxt(txt_file)
                if data.ndim != 2 or data.shape[1] < 2:
                    continue

                if not np.all(np.isfinite(data)):
                    continue

                if len(data) < min_samples:
                    continue

                if max_samples is not None and len(data) > max_samples:
                    data = data[:max_samples]

                col_x = data[:, 0]
                col_y = data[:, 1]
                pair_matrix = np.column_stack([col_x, col_y])

                if c_start == 1 and e_start == 2:
                    direction = 0
                    g = nx.DiGraph()
                    g.add_nodes_from(["X0", "X1"])
                    g.add_edge("X0", "X1")
                elif c_start == 2 and e_start == 1:
                    direction = 1
                    g = nx.DiGraph()
                    g.add_nodes_from(["X0", "X1"])
                    g.add_edge("X1", "X0")
                else:
                    continue

                task = CausalTask(
                    task_id=f"pair{pair_id_str}",
                    observations=pair_matrix,
                    graph=g,
                    variable_names=["X0", "X1"],
                    domain="tuebingen",
                    meta_info={
                        "pair_id": pair_id_str,
                        "weight": weight,
                        "direction": direction,
                        "swapped": False,
                    },
                )
                clean_tasks.append(task)

            except Exception:
                continue

        if target_pairs is not None:
            clean_tasks = clean_tasks[:target_pairs]

        if not augment_swapped:
            return clean_tasks

        augmented_tasks: List[CausalTask] = []
        for task in clean_tasks:
            augmented_tasks.append(task)

            swapped_data = np.column_stack([task.observations[:, 1], task.observations[:, 0]])
            original_dir = task.meta_info["direction"]
            new_dir = 1 - original_dir

            swapped_g = nx.DiGraph()
            swapped_g.add_nodes_from(["X0", "X1"])
            if new_dir == 0:
                swapped_g.add_edge("X0", "X1")
            else:
                swapped_g.add_edge("X1", "X0")

            swapped_task = CausalTask(
                task_id=f"{task.task_id}_swapped",
                observations=swapped_data,
                graph=swapped_g,
                variable_names=["X0", "X1"],
                domain="tuebingen",
                meta_info={
                    "pair_id": f"{task.task_id}_swapped",
                    "weight": task.meta_info["weight"],
                    "direction": new_dir,
                    "swapped": True,
                },
            )
            augmented_tasks.append(swapped_task)

        return augmented_tasks
