# python cli.py external_benchmark --seeds 20
# meflux external_benchmark

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from ..scm.mixed_graph import MixedCausalGraph, RelationType


class HCAMBaseline:

    def __init__(self, max_order: int = 2, preselect_k: int = 5, bic_penalty: float = 1.0, random_state: int = 42):
        self.max_order = max_order
        self.preselect_k = preselect_k
        self.bic_penalty = bic_penalty
        self.random_state = random_state

    def _basis_features(self, X_subset: np.ndarray) -> np.ndarray:
        n, p = X_subset.shape
        cols = [X_subset]
        for i in range(p):
            cols.append(X_subset[:, i:i+1] ** 2)
            cols.append(np.sin(X_subset[:, i:i+1]))
            cols.append(np.tanh(X_subset[:, i:i+1]))
        if p >= 2:
            for i in range(p):
                for j in range(i + 1, p):
                    cols.append((X_subset[:, i:i+1] * X_subset[:, j:j+1]))
        if p >= 3:
            cols.append((X_subset[:, 0:1] * X_subset[:, 1:2] * X_subset[:, 2:3]))
        return np.hstack(cols)

    def _bic_score(self, y: np.ndarray, y_pred: np.ndarray, num_params: int) -> float:
        n = len(y)
        rss = float(np.sum((y - y_pred) ** 2))
        sigma2 = max(1e-9, rss / n)
        log_lik = -0.5 * n * np.log(2.0 * np.pi * sigma2) - 0.5 * n
        bic = log_lik - 0.5 * self.bic_penalty * num_params * np.log(n)
        return bic

    def fit_hypergraph(self, data: np.ndarray, variable_names: List[str]) -> MixedCausalGraph:
        n, d = data.shape
        graph = MixedCausalGraph(variable_names)

        corrs = np.zeros((d, d))
        for i in range(d):
            for j in range(d):
                if i != j:
                    si = np.std(data[:, i])
                    sj = np.std(data[:, j])
                    if si > 1e-9 and sj > 1e-9:
                        r = float(np.corrcoef(data[:, i], data[:, j])[0, 1])
                        corrs[i, j] = abs(r) if np.isfinite(r) else 0.0

        for tgt in range(d):
            y = data[:, tgt]
            empty_bic = self._bic_score(y, np.mean(y) * np.ones(n), num_params=1)

            ranked_parents = np.argsort(corrs[:, tgt])[::-1]
            top_parents = [p for p in ranked_parents if p != tgt][:self.preselect_k]

            best_pw = []
            for p in top_parents:
                X_p = self._basis_features(data[:, p:p+1])
                reg = Ridge(alpha=1e-3).fit(X_p, y)
                pred = reg.predict(X_p)
                bic = self._bic_score(y, pred, num_params=X_p.shape[1])
                if bic > empty_bic:
                    best_pw.append((p, bic))

            best_pw.sort(key=lambda x: x[1], reverse=True)
            chosen_single = [p for p, _ in best_pw[:2]]

            for p in chosen_single:
                graph.add_directed_edge(variable_names[p], variable_names[tgt])

            if self.max_order >= 2 and len(top_parents) >= 2:
                for idx1 in range(len(top_parents)):
                    for idx2 in range(idx1 + 1, len(top_parents)):
                        p1, p2 = top_parents[idx1], top_parents[idx2]
                        X_pair = data[:, [p1, p2]]
                        X_add = np.column_stack([
                            data[:, p1], data[:, p2],
                            data[:, p1]**2, data[:, p2]**2,
                            np.tanh(data[:, p1]), np.tanh(data[:, p2])
                        ])
                        X_joint = np.column_stack([X_add, data[:, p1] * data[:, p2]])

                        reg_add = Ridge(alpha=1e-3).fit(X_add, y)
                        pred_add = reg_add.predict(X_add)
                        bic_add = self._bic_score(y, pred_add, num_params=X_add.shape[1])

                        reg_joint = Ridge(alpha=1e-3).fit(X_joint, y)
                        pred_joint = reg_joint.predict(X_joint)
                        bic_joint = self._bic_score(y, pred_joint, num_params=X_joint.shape[1])

                        gain = bic_joint - bic_add
                        if gain > 5.0:
                            graph.add_hyperedge(
                                sources=[variable_names[p1], variable_names[p2]],
                                target=variable_names[tgt],
                                relation_type=RelationType.JOINT_CAUSAL,
                                mechanism="hcam_greedy_additive",
                            )

            if self.max_order >= 3 and len(top_parents) >= 3:
                for idx1 in range(min(3, len(top_parents))):
                    for idx2 in range(idx1 + 1, min(4, len(top_parents))):
                        for idx3 in range(idx2 + 1, min(5, len(top_parents))):
                            p1, p2, p3 = top_parents[idx1], top_parents[idx2], top_parents[idx3]
                            X_3add = np.column_stack([
                                data[:, p1], data[:, p2], data[:, p3],
                                data[:, p1]*data[:, p2], data[:, p1]*data[:, p3], data[:, p2]*data[:, p3]
                            ])
                            X_3joint = np.column_stack([X_3add, data[:, p1] * data[:, p2] * data[:, p3]])

                            r_add = Ridge(alpha=1e-3).fit(X_3add, y)
                            b_add = self._bic_score(y, r_add.predict(X_3add), num_params=X_3add.shape[1])

                            r_joint = Ridge(alpha=1e-3).fit(X_3joint, y)
                            b_joint = self._bic_score(y, r_joint.predict(X_3joint), num_params=X_3joint.shape[1])

                            if (b_joint - b_add) > 8.0:
                                graph.add_hyperedge(
                                    sources=[variable_names[p1], variable_names[p2], variable_names[p3]],
                                    target=variable_names[tgt],
                                    relation_type=RelationType.JOINT_CAUSAL,
                                    mechanism="hcam_3way",
                                )

        return graph
