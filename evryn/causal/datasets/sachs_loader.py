# meflux sachs_improved
# python -m causality_in_flux.experiments.sachs_improved

"""Sachs (2005) Protein Signaling Multivariate Causal Benchmark Loader.

Loads the flow cytometry single-cell signaling dataset (Sachs et al., Science 2005):
- 11 phosphoproteins / phospholipids
- Observational dataset (855 cells)
- Interventional dataset (5400 cells under specific kinase perturbations)
- Ground-truth consensus network with:
  1. Direct cause-effect edges (->)
  2. Bidirected confounded / feedback edges (<->)
  3. No relation pairs (none)
"""

import os
from typing import List, Dict, Tuple, Optional
import numpy as np
import pandas as pd
from ..scm.mixed_graph import MixedCausalGraph, RelationType
from ..scm.semi_markovian_generator import MultivariateCausalTask


class SachsBenchmarkLoader:
    """Loads Sachs (2005) multivariate causal benchmark."""

    PROTEINS = [
        "Raf", "Mek", "Plcg", "PIP2", "PIP3",
        "Erk", "Akt", "PKA", "PKC", "P38", "Jnk"
    ]

    DIRECTED_EDGES = [
        ("Raf", "Mek"),
        ("Mek", "Erk"),
        ("Plcg", "PIP2"),
        ("Plcg", "PKC"),
        ("Erk", "Akt"),
        ("PKA", "Raf"),
        ("PKA", "Mek"),
        ("PKA", "Erk"),
        ("PKA", "Akt"),
        ("PKA", "P38"),
        ("PKA", "Jnk"),
        ("PKC", "Raf"),
        ("PKC", "Mek"),
        ("PKC", "P38"),
    ]

    BIDIRECTED_EDGES = [
        ("P38", "Jnk"),
        ("PIP2", "PIP3"),
        ("PKC", "Jnk"),
        ("Plcg", "PIP3"),
    ]

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            cands = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "sachs"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "sachs"),
                "data/sachs",
            ]
            for c in cands:
                if os.path.exists(os.path.join(c, "sachs_observational.tsv")):
                    data_dir = c
                    break
            if data_dir is None:
                data_dir = cands[0]
        self.data_dir = os.path.abspath(data_dir)
        self.obs_file = os.path.join(self.data_dir, "sachs_observational.tsv")
        self.int_file = os.path.join(self.data_dir, "sachs_interventional.tsv")

    def get_ground_truth_graph(self) -> MixedCausalGraph:
        """Construct the consensus ground truth MixedCausalGraph for Sachs network."""
        graph = MixedCausalGraph(self.PROTEINS)
        for u, v in self.DIRECTED_EDGES:
            graph.add_directed_edge(u, v)
        for u, v in self.BIDIRECTED_EDGES:
            graph.add_bidirected_edge(u, v)
        return graph

    def load_observational_task(self) -> MultivariateCausalTask:
        """Load observational single-cell protein expression task."""
        if not os.path.exists(self.obs_file):
            raise FileNotFoundError(f"Sachs observational file not found at {self.obs_file}")

        df = pd.read_csv(self.obs_file, sep="\t")
        cols = [c for c in self.PROTEINS if c in df.columns]
        data = df[cols].values.astype(np.float64)

        data_log = np.log(data + 1.0)

        graph = self.get_ground_truth_graph()
        return MultivariateCausalTask(
            task_id="sachs_observational",
            observations=data_log,
            graph=graph,
            variable_names=cols,
            domain="biology_cell_signaling",
            meta_info={"samples": len(data_log), "regime": "observational"},
        )

    def load_interventional_task(self) -> MultivariateCausalTask:
        """Load interventional single-cell protein expression task."""
        if not os.path.exists(self.int_file):
            raise FileNotFoundError(f"Sachs interventional file not found at {self.int_file}")

        df = pd.read_csv(self.int_file, sep=r"\s+", quotechar='"')
        cols = [c for c in self.PROTEINS if c in df.columns]
        data = df[cols].values.astype(np.float64)
        data_log = np.log(data + 1.0)

        graph = self.get_ground_truth_graph()
        return MultivariateCausalTask(
            task_id="sachs_interventional",
            observations=data_log,
            graph=graph,
            variable_names=cols,
            domain="biology_cell_signaling",
            meta_info={"samples": len(data_log), "regime": "interventional"},
        )

    def load_all_condition_tasks(self) -> List[MultivariateCausalTask]:
        """Load individual experimental condition tasks from Sachs dataset."""
        tasks = [self.load_observational_task()]

        if not os.path.exists(self.int_file):
            return tasks

        df = pd.read_csv(self.int_file, sep=r"\s+", quotechar='"')
        cols = [c for c in self.PROTEINS if c in df.columns]
        graph = self.get_ground_truth_graph()

        condition_names = {
            0: "Control",
            9: "Anti-CD3+CD28",
            8: "ICAM-2",
            7: "Akt-Inhibitor",
            4: "G0076 (PKC-Inhibitor)",
            2: "Pspect (P38/Jnk)",
        }

        for int_val, group in df.groupby("INT"):
            name = condition_names.get(int(int_val), f"Intervention_{int_val}")
            data = group[cols].values.astype(np.float64)
            data_log = np.log(data + 1.0)
            tasks.append(
                MultivariateCausalTask(
                    task_id=f"sachs_int_{int_val}_{name}",
                    observations=data_log,
                    graph=graph,
                    variable_names=cols,
                    domain=f"perturbation_{name}",
                    meta_info={"int_code": int_val, "condition": name, "num_cells": len(data_log)},
                )
            )
        return tasks
