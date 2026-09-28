# meflux --help

"""Semi-Markovian Structural Causal Model Generator with Explicit 4-Class Ground Truth.

Generates multivariate causal models with:
1. Directed cause-effect relations (Xi -> Xj and Xi <- Xj)
2. Bidirected confounded relations (Xi <-> Xj) via unobserved latent common causes
3. Explicit negative examples:
   - True independence (Xi _|_ Xj)
   - Non-causal association via observed common causes (Z -> Xi and Z -> Xj without direct edge)
   - Colliders (Xi -> Z <- Xj without direct edge)
4. Domain shifts for lifelong continual learning (Causality in Flux)
5. Controlled class-balanced benchmark variants to decouple class imbalance from continual-learning effects.
"""

from typing import List, Tuple, Dict, Optional, Any, Set
import numpy as np
import networkx as nx
from .mixed_graph import MixedCausalGraph, RelationType, HyperCausalRelation
from .mechanisms import (
    gaussian_noise,
    laplace_noise,
    uniform_noise,
    linear_mechanism,
    polynomial_mechanism,
    sigmoid_mechanism,
    tanh_mechanism,
)


class MultivariateCausalTask:
    """A multivariate causal task containing observations matrix X and mixed graph G."""

    def __init__(
        self,
        task_id: str,
        observations: np.ndarray,
        graph: MixedCausalGraph,
        variable_names: List[str],
        domain: str = "multivariate",
        meta_info: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.observations = observations
        self.graph = graph
        self.variable_names = list(variable_names)
        self.domain = domain
        self.meta_info = meta_info or {}

    @property
    def num_samples(self) -> int:
        return self.observations.shape[0]

    @property
    def num_variables(self) -> int:
        return self.observations.shape[1]


class SemiMarkovianTaskGenerator:
    """Generates synthetic multivariate tasks with directed, bidirected, and empty edges."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate_task(
        self,
        task_id: str,
        num_variables: int = 5,
        num_samples: int = 1000,
        directed_prob: float = 0.35,
        confounded_prob: float = 0.25,
        mechanism_type: str = "linear",
        noise_type: str = "laplace",
        domain: str = "synthetic",
        template_graph: Optional[MixedCausalGraph] = None,
        ensure_all_classes: bool = True,
    ) -> MultivariateCausalTask:
        """Generate a multivariate semi-Markovian task supporting all four relation classes."""
        var_names = [f"X{i}" for i in range(num_variables)] if template_graph is None else list(template_graph.nodes)
        d = len(var_names)
        node_map = {n: i for i, n in enumerate(var_names)}

        if template_graph is not None:
            graph = template_graph
            directed_adj = np.zeros((d, d), dtype=int)
            for u, v in graph.directed_edges:
                directed_adj[node_map[u], node_map[v]] = 1

            latent_pairs: List[Tuple[int, int]] = []
            for pair in graph.bidirected_edges:
                u, v = list(pair)
                latent_pairs.append((node_map[u], node_map[v]))

            dg = nx.DiGraph()
            dg.add_nodes_from(range(d))
            for i in range(d):
                for j in range(d):
                    if directed_adj[i, j] == 1:
                        dg.add_edge(i, j)
            try:
                perm = list(nx.topological_sort(dg))
            except Exception:
                perm = list(range(d))

        else:
            graph = MixedCausalGraph(var_names)

            perm = self.rng.permutation(d)
            inv_perm = np.zeros(d, dtype=int)
            for rank, node_idx in enumerate(perm):
                inv_perm[node_idx] = rank

            directed_adj = np.zeros((d, d), dtype=int)

            for i in range(d):
                for j in range(i + 1, d):
                    if self.rng.random() < directed_prob:
                        if inv_perm[i] < inv_perm[j]:
                            directed_adj[i, j] = 1
                            graph.add_directed_edge(var_names[i], var_names[j])
                        else:
                            directed_adj[j, i] = 1
                            graph.add_directed_edge(var_names[j], var_names[i])

            latent_pairs = []
            for i in range(d):
                for j in range(i + 1, d):
                    if directed_adj[i, j] == 0 and directed_adj[j, i] == 0:
                        if self.rng.random() < confounded_prob:
                            latent_pairs.append((i, j))
                            graph.add_bidirected_edge(var_names[i], var_names[j])

            if ensure_all_classes and d >= 4:
                pairs_by_rel: Dict[int, List[Tuple[int, int]]] = {0: [], 1: [], 2: [], 3: []}
                for i in range(d):
                    for j in range(i + 1, d):
                        rel = graph.get_relation(var_names[i], var_names[j])
                        pairs_by_rel[rel].append((i, j))

                if len(pairs_by_rel[3]) == 0 and len(pairs_by_rel[0]) > 1:
                    i, j = pairs_by_rel[0].pop()
                    latent_pairs.append((i, j))
                    graph.add_bidirected_edge(var_names[i], var_names[j])
                    pairs_by_rel[3].append((i, j))

                if len(pairs_by_rel[1]) == 0 and len(pairs_by_rel[0]) > 1:
                    i, j = pairs_by_rel[0].pop()
                    if inv_perm[i] < inv_perm[j]:
                        directed_adj[i, j] = 1
                        graph.add_directed_edge(var_names[i], var_names[j])
                    else:
                        inv_perm[i], inv_perm[j] = min(inv_perm[i], inv_perm[j]), max(inv_perm[i], inv_perm[j])
                        directed_adj[i, j] = 1
                        graph.add_directed_edge(var_names[i], var_names[j])
                    pairs_by_rel[1].append((i, j))

                if len(pairs_by_rel[2]) == 0 and len(pairs_by_rel[0]) > 1:
                    i, j = pairs_by_rel[0].pop()
                    if inv_perm[j] < inv_perm[i]:
                        directed_adj[j, i] = 1
                        graph.add_directed_edge(var_names[j], var_names[i])
                    else:
                        inv_perm[j], inv_perm[i] = min(inv_perm[i], inv_perm[j]), max(inv_perm[i], inv_perm[j])
                        directed_adj[j, i] = 1
                        graph.add_directed_edge(var_names[j], var_names[i])
                    pairs_by_rel[2].append((i, j))

                dg = nx.DiGraph()
                dg.add_nodes_from(range(d))
                for i in range(d):
                    for j in range(d):
                        if directed_adj[i, j] == 1:
                            dg.add_edge(i, j)
                try:
                    perm = list(nx.topological_sort(dg))
                except Exception:
                    perm = list(range(d))

        num_latents = len(latent_pairs)
        if num_latents > 0:
            if noise_type == "laplace":
                L = self.rng.laplace(0, 1.2, size=(num_samples, num_latents))
            elif noise_type == "uniform":
                L = self.rng.uniform(-2.0, 2.0, size=(num_samples, num_latents))
            else:
                L = self.rng.normal(0, 1.0, size=(num_samples, num_latents))
        else:
            L = np.zeros((num_samples, 0))

        if noise_type == "laplace":
            E = self.rng.laplace(0, 0.8, size=(num_samples, d))
        elif noise_type == "uniform":
            E = self.rng.uniform(-1.5, 1.5, size=(num_samples, d))
        else:
            E = self.rng.normal(0, 0.8, size=(num_samples, d))

        X = np.zeros((num_samples, d))

        for var_idx in perm:
            val = E[:, var_idx].copy()

            for p in range(d):
                if directed_adj[p, var_idx] == 1:
                    weight = float(self.rng.uniform(0.7, 1.3) * self.rng.choice([-1, 1]))
                    parent_vals = X[:, p]

                    if mechanism_type == "polynomial":
                        val += weight * 0.35 * (parent_vals ** 2) + 0.5 * parent_vals
                    elif mechanism_type == "tanh":
                        val += weight * 1.6 * np.tanh(parent_vals)
                    elif mechanism_type == "mixed":
                        if p % 2 == 0:
                            val += weight * 1.3 * np.tanh(parent_vals)
                        else:
                            val += weight * parent_vals
                    else:
                        val += weight * parent_vals

            for k, (u_idx, v_idx) in enumerate(latent_pairs):
                if var_idx in (u_idx, v_idx):
                    w_latent = float(self.rng.uniform(0.75, 1.25))
                    val += w_latent * L[:, k]

            X[:, var_idx] = val

        return MultivariateCausalTask(
            task_id=task_id,
            observations=X,
            graph=graph,
            variable_names=var_names,
            domain=domain,
            meta_info={
                "num_directed": len(graph.directed_edges),
                "num_bidirected": len(graph.bidirected_edges),
                "mechanism": mechanism_type,
                "noise": noise_type,
            },
        )

    def generate_multivariate_flux_stream(
        self,
        num_tasks: int = 16,
        num_variables: int = 5,
        samples_per_task: int = 600,
        regimes: Optional[List[str]] = None,
    ) -> List[MultivariateCausalTask]:
        """Generate a lifelong sequence of multivariate tasks with domain flux across 4 regimes."""
        regimes = regimes or ["linear_sparse", "nonlinear_confounded", "dense_mixed", "heavy_tail_flux"]
        tasks: List[MultivariateCausalTask] = []

        configs = {
            "linear_sparse": {"dir_p": 0.25, "conf_p": 0.20, "mech": "linear", "noise": "gaussian"},
            "nonlinear_confounded": {"dir_p": 0.35, "conf_p": 0.35, "mech": "tanh", "noise": "laplace"},
            "dense_mixed": {"dir_p": 0.40, "conf_p": 0.25, "mech": "mixed", "noise": "laplace"},
            "heavy_tail_flux": {"dir_p": 0.30, "conf_p": 0.30, "mech": "polynomial", "noise": "uniform"},
        }

        domain_templates: Dict[str, MixedCausalGraph] = {}
        for r_name in regimes:
            cfg = configs[r_name]
            base_t = self.generate_task(
                task_id=f"template_{r_name}",
                num_variables=num_variables,
                num_samples=100,
                directed_prob=cfg["dir_p"],
                confounded_prob=cfg["conf_p"],
                mechanism_type=cfg["mech"],
                noise_type=cfg["noise"],
                domain=r_name,
                ensure_all_classes=True,
            )
            domain_templates[r_name] = base_t.graph

        for idx in range(num_tasks):
            regime = regimes[idx % len(regimes)]
            cfg = configs[regime]
            task_id = f"mflux_{idx+1:02d}_{regime}"

            task = self.generate_task(
                task_id=task_id,
                num_variables=num_variables,
                num_samples=samples_per_task,
                mechanism_type=cfg["mech"],
                noise_type=cfg["noise"],
                domain=regime,
                template_graph=domain_templates[regime],
            )
            tasks.append(task)

        return tasks

    def generate_class_balanced_stream(
        self,
        num_tasks: int = 16,
        num_variables: int = 6,
        samples_per_task: int = 600,
    ) -> List[MultivariateCausalTask]:
        """Generate a controlled class-balanced benchmark variant to decouple class imbalance from continual learning."""
        regimes = ["linear_sparse", "nonlinear_confounded", "dense_mixed", "heavy_tail_flux"]
        tasks: List[MultivariateCausalTask] = []

        configs = {
            "linear_sparse": {"mech": "linear", "noise": "gaussian"},
            "nonlinear_confounded": {"mech": "tanh", "noise": "laplace"},
            "dense_mixed": {"mech": "mixed", "noise": "laplace"},
            "heavy_tail_flux": {"mech": "polynomial", "noise": "uniform"},
        }

        for idx in range(num_tasks):
            regime = regimes[idx % len(regimes)]
            cfg = configs[regime]
            task_id = f"bal_flux_{idx+1:02d}_{regime}"

            var_names = [f"X{i}" for i in range(num_variables)]
            graph = MixedCausalGraph(var_names)

            graph.add_directed_edge(var_names[0], var_names[1])
            graph.add_directed_edge(var_names[1], var_names[2])
            graph.add_directed_edge(var_names[3], var_names[0])
            graph.add_directed_edge(var_names[4], var_names[2])
            graph.add_bidirected_edge(var_names[0], var_names[4])
            graph.add_bidirected_edge(var_names[1], var_names[5])

            task = self.generate_task(
                task_id=task_id,
                num_variables=num_variables,
                num_samples=samples_per_task,
                mechanism_type=cfg["mech"],
                noise_type=cfg["noise"],
                domain=regime,
                template_graph=graph,
            )
            tasks.append(task)

        return tasks
