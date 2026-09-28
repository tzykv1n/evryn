# meflux --help

"""Synthetic Causal Task Generator.

Generates:
1. Cause-Effect pairs with various mechanisms and noise distributions.
2. Non-stationary task streams with domain shifts (flux over time).
3. Multi-variable DAG benchmark tasks.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import networkx as nx
from .structural_causal_model import StructuralCausalModel
from .mechanisms import (
    gaussian_noise,
    laplace_noise,
    uniform_noise,
    gumbel_noise,
    linear_mechanism,
    polynomial_mechanism,
    sigmoid_mechanism,
    tanh_mechanism,
    sinusoidal_mechanism,
    simulate_lotka_volterra,
    simulate_financial_market_cycle,
)


class CausalTask:
    """A causal task (X, G) where X is observation matrix and G is the ground truth graph."""

    def __init__(
        self,
        task_id: str,
        observations: np.ndarray,
        graph: nx.DiGraph,
        variable_names: List[str],
        domain: str = "synthetic",
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

    @property
    def label(self) -> int:
        """For bivariate cause-effect pairs: 0 if X0 -> X1, 1 if X1 -> X0."""
        if len(self.variable_names) == 2:
            v0, v1 = self.variable_names[0], self.variable_names[1]
            if self.graph.has_edge(v0, v1):
                return 0
            elif self.graph.has_edge(v1, v0):
                return 1
        return -1


class CausalTaskGenerator:
    """Generates synthetic tasks under stationary and non-stationary (flux) conditions."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate_bivariate_pair(
        self,
        task_id: str,
        direction: int = 0,
        mechanism_type: str = "linear",
        noise_type: str = "gaussian",
        num_samples: int = 1000,
        domain: str = "general",
    ) -> CausalTask:
        """Generate a bivariate cause-effect pair."""
        scm = StructuralCausalModel(name=task_id)

        noise_factories = {
            "gaussian": gaussian_noise(1.0),
            "laplace": laplace_noise(1.0),
            "uniform": uniform_noise(-1.5, 1.5),
            "gumbel": gumbel_noise(0.0, 1.0),
        }
        cause_noise = noise_factories.get(noise_type, gaussian_noise(1.0))
        effect_noise = noise_factories.get(noise_type, gaussian_noise(0.8))

        mechanism_factories = {
            "linear": linear_mechanism(weight=1.2),
            "polynomial": polynomial_mechanism(deg=2, scale=0.4),
            "sigmoid": sigmoid_mechanism(steepness=2.5, scale=2.0),
            "tanh": tanh_mechanism(scale=1.8),
            "sine": sinusoidal_mechanism(freq=1.5, amp=1.5),
        }
        mech = mechanism_factories.get(mechanism_type, linear_mechanism(1.0))

        if direction == 0:
            cause_var, effect_var = "X0", "X1"
        else:
            cause_var, effect_var = "X1", "X0"

        scm.add_variable(cause_var, parent_vars=[], noise_dist=cause_noise)
        scm.add_variable(effect_var, parent_vars=[cause_var], func=mech, noise_dist=effect_noise)

        data_matrix, var_names = scm.sample_matrix(
            num_samples=num_samples,
            var_order=["X0", "X1"],
            seed=int(self.rng.integers(0, 100000)),
        )

        return CausalTask(
            task_id=task_id,
            observations=data_matrix,
            graph=scm.graph,
            variable_names=["X0", "X1"],
            domain=domain,
            meta_info={
                "direction": direction,
                "mechanism": mechanism_type,
                "noise": noise_type,
            },
        )

    def generate_coupled_cycle_task(
        self,
        task_id: str,
        system_type: str = "lotka_volterra",
        num_samples: int = 1000,
    ) -> CausalTask:
        """Generate tasks from coupled dynamical systems (Lotka-Volterra or Financial)."""
        seed = int(self.rng.integers(0, 100000))
        if system_type == "lotka_volterra":
            x, y = simulate_lotka_volterra(num_samples=num_samples, seed=seed)
            domain = "ecology"
        else:
            x, y = simulate_financial_market_cycle(num_samples=num_samples, seed=seed)
            domain = "finance"

        graph = nx.DiGraph()
        graph.add_edge("X0", "X1")
        data_matrix = np.column_stack([x, y])

        return CausalTask(
            task_id=task_id,
            observations=data_matrix,
            graph=graph,
            variable_names=["X0", "X1"],
            domain=domain,
            meta_info={"system": system_type},
        )

    def generate_flux_stream(
        self,
        num_tasks: int = 20,
        samples_per_task: int = 500,
        regimes: Optional[List[str]] = None,
    ) -> List[CausalTask]:
        """Generate a sequential stream of causal tasks with domain shifts ("Causality in Flux").

        Demonstrates:
        1. Ecology regime (Lotka-Volterra prey-predator)
        2. Financial regime (stock price-volume dynamics)
        3. Physical regime (polynomial/tanh mechanisms)
        4. Economy regime (linear/sigmoid mechanisms)
        """
        regimes = regimes or ["ecology", "finance", "physics", "economy"]
        tasks: List[CausalTask] = []

        mechanisms_map = {
            "physics": ["polynomial", "tanh"],
            "economy": ["linear", "sigmoid"],
        }
        noises = ["gaussian", "laplace", "uniform", "gumbel"]

        for i in range(num_tasks):
            regime = regimes[i % len(regimes)]
            task_id = f"task_{i+1:03d}_{regime}"
            direction = int(self.rng.choice([0, 1]))

            if regime == "ecology":
                task = self.generate_coupled_cycle_task(task_id, "lotka_volterra", samples_per_task)
            elif regime == "finance":
                task = self.generate_coupled_cycle_task(task_id, "financial_cycle", samples_per_task)
            else:
                mech = str(self.rng.choice(mechanisms_map[regime]))
                noise = str(self.rng.choice(noises))
                task = self.generate_bivariate_pair(
                    task_id=task_id,
                    direction=direction,
                    mechanism_type=mech,
                    noise_type=noise,
                    num_samples=samples_per_task,
                    domain=regime,
                )

            tasks.append(task)

        return tasks
