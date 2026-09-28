# python cli.py external_benchmark --seeds 20 --samples 1000 --noise 0.25 --max-order 3
# meflux external_benchmark --seeds 20 --samples 1000 --noise 0.25 --max-order 3

from typing import List, Tuple, Dict, Optional, Any
import numpy as np
from .mixed_graph import MixedCausalGraph, RelationType
from .semi_markovian_generator import MultivariateCausalTask


class IndependentHCAMGenerator:

    TRAIN_MECHANISMS = ["linear", "polynomial", "multiplicative"]
    TEST_MECHANISMS = ["nonlinear", "mixed", "gp_nonparametric", "noisy_multiplicative", "threeway", "confounded"]

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def _get_rng(self, seed: Optional[int] = None) -> np.random.Generator:
        if seed is None:
            return self.rng
        return np.random.default_rng(seed)

    def generate_linear_additive(self, num_samples: int = 1000, noise: float = 0.25, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_directed_edge("A", "C")
        graph.add_directed_edge("B", "C")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        eps = rng.normal(0, noise, size=num_samples)
        c = 1.1 * a + 1.2 * b + eps

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="hcam_linear_additive",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "linear", "is_joint": False, "split": "train"},
        )

    def generate_polynomial(self, num_samples: int = 1000, alpha: float = 1.0, noise: float = 0.25, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="polynomial")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        eps = rng.normal(0, noise, size=num_samples)
        c = alpha * (a * b) + 0.3 * (a ** 2) - 0.3 * (b ** 2) + eps

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="hcam_polynomial",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "polynomial", "is_joint": True, "split": "train"},
        )

    def generate_multiplicative(self, num_samples: int = 1000, alpha: float = 1.5, noise: float = 0.25, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="multiplicative")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        eps = rng.normal(0, noise, size=num_samples)
        c = alpha * (a * b) + eps

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="hcam_multiplicative",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "multiplicative", "is_joint": True, "split": "train"},
        )

    def generate_nonlinear_additive(self, num_samples: int = 1000, noise: float = 0.25, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_directed_edge("A", "C")
        graph.add_directed_edge("B", "C")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        eps = rng.normal(0, noise, size=num_samples)
        c = 1.3 * np.sin(a) + 1.2 * np.tanh(b) + eps

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="hcam_nonlinear_additive",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "nonlinear", "is_joint": False, "split": "test"},
        )

    def generate_mixed_interaction(self, num_samples: int = 1000, alpha: float = 1.2, noise: float = 0.25, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="mixed")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        eps = rng.normal(0, noise, size=num_samples)
        c = 0.8 * np.sin(a) + 0.8 * np.tanh(b) + alpha * (a * b) + eps

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="hcam_mixed",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "mixed", "is_joint": True, "split": "test"},
        )

    def generate_gp_nonparametric(self, num_samples: int = 1000, num_features: int = 20, noise: float = 0.25, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="gp_nonparametric")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        inp = np.column_stack([a, b])

        w_freq = rng.normal(0, 1.0, size=(2, num_features))
        b_phase = rng.uniform(0, 2 * np.pi, size=num_features)
        weights = rng.normal(0, 1.0, size=num_features)

        proj = np.dot(inp, w_freq) + b_phase
        phi = np.sqrt(2.0 / num_features) * np.cos(proj)
        f_val = 2.0 * np.dot(phi, weights)

        eps = rng.normal(0, noise, size=num_samples)
        c = f_val + eps

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="hcam_gp_nonparametric",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "gp_nonparametric", "is_joint": True, "split": "test"},
        )

    def generate_noisy_multiplicative(self, num_samples: int = 1000, alpha: float = 1.0, noise: float = 0.5, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="noisy_multiplicative")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        eps = rng.laplace(0, noise, size=num_samples)
        c = alpha * (a * b) + eps

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="hcam_noisy_multiplicative",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "noisy_multiplicative", "is_joint": True, "split": "test"},
        )

    def generate_threeway_hcam(self, num_samples: int = 1000, alpha: float = 1.5, noise: float = 0.25, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C", "D"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B", "C"], "D", relation_type=RelationType.JOINT_CAUSAL, mechanism="3way_hcam")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        c = rng.normal(0, 1.0, size=num_samples)
        eps = rng.normal(0, noise, size=num_samples)
        d = alpha * (a * b * c) + 0.3 * np.tanh(a * b) + eps

        X = np.column_stack([a, b, c, d])
        return MultivariateCausalTask(
            task_id="hcam_threeway",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "threeway", "is_joint": True, "split": "test"},
        )

    def generate_confounded_mechanism(self, num_samples: int = 1000, noise: float = 0.25, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="confounded_joint")
        graph.add_bidirected_edge("A", "B")

        u = rng.laplace(0, 1.0, size=num_samples)
        eps_a = rng.normal(0, 0.4, size=num_samples)
        eps_b = rng.normal(0, 0.4, size=num_samples)
        eps_c = rng.normal(0, noise, size=num_samples)

        a = 0.9 * u + eps_a
        b = 0.9 * u + eps_b
        c = 1.5 * (a * b) + 0.6 * u + eps_c

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="hcam_confounded",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "confounded", "is_joint": True, "split": "test"},
        )

    def generate_v_structure(self, num_samples: int = 1000, noise: float = 0.25, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_directed_edge("A", "C")
        graph.add_directed_edge("B", "C")

        a = rng.normal(0, 1.0, size=num_samples)
        b = rng.normal(0, 1.0, size=num_samples)
        eps = rng.normal(0, noise, size=num_samples)
        c = 1.2 * a + 1.2 * b + eps

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="hcam_v_structure",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "v_structure", "is_joint": False, "split": "confounder_bench"},
        )

    def generate_confounded_parents(self, num_samples: int = 1000, noise: float = 0.25, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_bidirected_edge("A", "C")
        graph.add_bidirected_edge("B", "C")

        u = rng.normal(0, 1.0, size=num_samples)
        a = 0.8 * u + rng.normal(0, 0.5, size=num_samples)
        b = 0.8 * u + rng.normal(0, 0.5, size=num_samples)
        c = 1.0 * u + rng.normal(0, noise, size=num_samples)

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="hcam_confounded_parents",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "confounded_parents", "is_joint": False, "split": "confounder_bench"},
        )

    def generate_chain(self, num_samples: int = 1000, noise: float = 0.25, seed: Optional[int] = None) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_directed_edge("A", "B")
        graph.add_directed_edge("B", "C")

        a = rng.normal(0, 1.0, size=num_samples)
        b = 1.2 * a + rng.normal(0, noise, size=num_samples)
        c = 1.1 * b + rng.normal(0, noise, size=num_samples)

        X = np.column_stack([a, b, c])
        return MultivariateCausalTask(
            task_id="hcam_chain",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info={"mechanism": "chain", "is_joint": False, "split": "confounder_bench"},
        )

    def generate_multi_environment_joint(
        self,
        num_samples: int = 1000,
        num_envs: int = 3,
        noise: float = 0.25,
        seed: Optional[int] = None,
    ) -> MultivariateCausalTask:
        rng = self._get_rng(seed)
        nodes = ["A", "B", "C"]
        graph = MixedCausalGraph(nodes)
        graph.add_hyperedge(["A", "B"], "C", relation_type=RelationType.JOINT_CAUSAL, mechanism="multi_env_joint")

        samples_per_env = num_samples // num_envs
        all_X = []
        env_datasets = []

        for e in range(num_envs):
            var_a = 0.5 + 0.5 * e
            var_b = 1.0 + 0.3 * e
            a_e = rng.normal(0, var_a, size=samples_per_env)
            b_e = rng.normal(0, var_b, size=samples_per_env)
            eps_e = rng.normal(0, noise, size=samples_per_env)
            c_e = 1.2 * (a_e * b_e) + 0.4 * (a_e ** 2) + eps_e
            X_e = np.column_stack([a_e, b_e, c_e])
            all_X.append(X_e)
            env_datasets.append(X_e)

        X = np.vstack(all_X)
        meta = {"mechanism": "multi_env_joint", "is_joint": True, "split": "confounder_bench", "num_envs": num_envs, "environments_data": env_datasets}
        return MultivariateCausalTask(
            task_id="hcam_multi_env_joint",
            observations=X,
            graph=graph,
            variable_names=nodes,
            domain="independent_hcam",
            meta_info=meta,
        )

    def generate_confounder_benchmark_suite(
        self,
        num_samples: int = 1000,
        noise: float = 0.25,
        seed: Optional[int] = None,
    ) -> List[MultivariateCausalTask]:
        s = seed if seed is not None else self.seed
        tasks = [
            self.generate_v_structure(num_samples=num_samples, noise=noise, seed=s + 101),
            self.generate_confounded_parents(num_samples=num_samples, noise=noise, seed=s + 102),
            self.generate_chain(num_samples=num_samples, noise=noise, seed=s + 103),
            self.generate_linear_additive(num_samples=num_samples, noise=noise, seed=s + 104),
            self.generate_multiplicative(num_samples=num_samples, noise=noise, seed=s + 105),
            self.generate_confounded_mechanism(num_samples=num_samples, noise=noise, seed=s + 106),
            self.generate_multi_environment_joint(num_samples=num_samples, noise=noise, seed=s + 107),
        ]
        return tasks

    def generate_training_set(self, num_samples: int = 600, seed: Optional[int] = None) -> List[MultivariateCausalTask]:
        s = seed if seed is not None else self.seed
        tasks = [
            self.generate_linear_additive(num_samples=num_samples, seed=s + 1),
            self.generate_polynomial(num_samples=num_samples, seed=s + 2),
            self.generate_multiplicative(num_samples=num_samples, seed=s + 3),
            self.generate_linear_additive(num_samples=num_samples, seed=s + 4),
            self.generate_polynomial(num_samples=num_samples, seed=s + 5),
            self.generate_multiplicative(num_samples=num_samples, seed=s + 6),
        ]
        return tasks

    def generate_test_set(
        self,
        num_samples: int = 1000,
        noise: float = 0.25,
        alpha: float = 1.0,
        seed: Optional[int] = None,
    ) -> List[MultivariateCausalTask]:
        s = seed if seed is not None else self.seed
        tasks = [
            self.generate_nonlinear_additive(num_samples=num_samples, noise=noise, seed=s + 10),
            self.generate_mixed_interaction(num_samples=num_samples, alpha=alpha, noise=noise, seed=s + 20),
            self.generate_gp_nonparametric(num_samples=num_samples, noise=noise, seed=s + 30),
            self.generate_noisy_multiplicative(num_samples=num_samples, alpha=alpha, noise=noise, seed=s + 40),
            self.generate_threeway_hcam(num_samples=num_samples, alpha=alpha, noise=noise, seed=s + 50),
            self.generate_confounded_mechanism(num_samples=num_samples, noise=noise, seed=s + 60),
        ]
        return tasks
