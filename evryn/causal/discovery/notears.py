# python cli.py external_benchmark --seeds 20
# meflux external_benchmark

from typing import List, Optional
import numpy as np
from scipy import linalg
from scipy.optimize import minimize
from ..scm.mixed_graph import MixedCausalGraph


class NOTEARSBaseline:

    def __init__(self, lambda1: float = 0.1, loss_type: str = "l2", max_iter: int = 100, h_tol: float = 1e-8, rho_max: float = 1e+16, w_threshold: float = 0.3):
        self.lambda1 = lambda1
        self.loss_type = loss_type
        self.max_iter = max_iter
        self.h_tol = h_tol
        self.rho_max = rho_max
        self.w_threshold = w_threshold

    def _h(self, W: np.ndarray) -> float:
        d = W.shape[0]
        M = np.eye(d) + W * W / d
        E = np.linalg.matrix_power(M, d - 1)
        h = np.trace(E @ M) - d
        return float(h)

    def fit_dag(self, X: np.ndarray, variable_names: List[str]) -> MixedCausalGraph:
        n, d = X.shape
        w_est = np.zeros((d, d))
        rho, alpha, h = 1.0, 0.0, np.inf
        bnds = [(0, 0) if i == j else (None, None) for i in range(d) for j in range(d)]

        for _ in range(self.max_iter):
            w_new, h_new = None, None
            while rho < self.rho_max:
                def _func(w_vec):
                    W = w_vec.reshape((d, d))
                    diff = X - X @ W
                    loss = 0.5 / n * np.sum(diff ** 2)
                    M = np.eye(d) + W * W / d
                    E = np.linalg.matrix_power(M, d - 1)
                    h_val = float(np.trace(E @ M) - d)
                    obj = loss + 0.5 * rho * h_val * h_val + alpha * h_val + self.lambda1 * np.sum(np.abs(W))
                    return obj

                res = minimize(_func, w_est.flatten(), method="L-BFGS-B", bounds=bnds, options={"maxiter": 150})
                w_new = res.x.reshape((d, d))
                h_new = self._h(w_new)
                if h_new <= 0.25 * h:
                    break
                rho *= 10.0

            w_est, h = w_new, h_new
            alpha += rho * h
            if h <= self.h_tol or rho >= self.rho_max:
                break

        w_est[np.abs(w_est) < self.w_threshold] = 0.0
        graph = MixedCausalGraph(variable_names)
        for i in range(d):
            for j in range(d):
                if i != j and abs(w_est[i, j]) > 0.0:
                    graph.add_directed_edge(variable_names[i], variable_names[j])

        return graph
