# meflux --help

"""Additive Noise Model (ANM) Causal Discovery.

Implements ANM (Hoyer et al., 2009; Mooij et al., 2016):
Given two variables X and Y:
1. Fit non-linear regression Y = f(X) + U_Y, test independence of U_Y and X.
2. Fit non-linear regression X = g(Y) + U_X, test independence of U_X and Y.
3. Compare dependence score (HSIC / Distance Correlation) to infer causal direction.
"""

from typing import Tuple, List, Optional
import numpy as np
import networkx as nx
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.kernel_ridge import KernelRidge
from .base import BaseCausalDiscovery


def compute_distance_covariance(x: np.ndarray, y: np.ndarray) -> float:
    """Compute distance covariance between arrays x and y (Székely et al., 2007)."""
    n = len(x)
    if n <= 1:
        return 0.0

    if x.ndim == 1:
        a = np.abs(x[:, None] - x[None, :])
    else:
        a = np.linalg.norm(x[:, None, :] - x[None, :, :], axis=-1)

    if y.ndim == 1:
        b = np.abs(y[:, None] - y[None, :])
    else:
        b = np.linalg.norm(y[:, None, :] - y[None, :, :], axis=-1)

    a_mean_row = np.mean(a, axis=1, keepdims=True)
    a_mean_col = np.mean(a, axis=0, keepdims=True)
    a_mean = np.mean(a)
    A = a - a_mean_row - a_mean_col + a_mean

    b_mean_row = np.mean(b, axis=1, keepdims=True)
    b_mean_col = np.mean(b, axis=0, keepdims=True)
    b_mean = np.mean(b)
    B = b - b_mean_row - b_mean_col + b_mean

    dcov2 = np.sum(A * B) / (n * n)
    return float(np.sqrt(max(0.0, dcov2)))


def compute_distance_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Compute distance correlation in [0, 1].

    dCor(X, Y) = 0 if and only if X and Y are independent.
    """
    dcov_xy = compute_distance_covariance(x, y)
    dcov_xx = compute_distance_covariance(x, x)
    dcov_yy = compute_distance_covariance(y, y)

    denom = np.sqrt(dcov_xx * dcov_yy)
    if denom < 1e-12:
        return 0.0
    return float(np.clip(dcov_xy / denom, 0.0, 1.0))


class AdditiveNoiseModel(BaseCausalDiscovery):
    """Additive Noise Model (ANM) for bivariate causal discovery."""

    def __init__(
        self,
        regressor: str = "ridge",
        subsample: int = 500,
        random_state: int = 42,
    ):
        self.regressor = regressor
        self.subsample = subsample
        self.random_state = random_state

    def _fit_residual(self, cause: np.ndarray, effect: np.ndarray) -> Tuple[np.ndarray, float]:
        """Fit effect = f(cause) + residual and measure dependence(residual, cause)."""
        n = len(cause)
        if n > self.subsample:
            rng = np.random.default_rng(self.random_state)
            idx = rng.choice(n, size=self.subsample, replace=False)
            x_sub = cause[idx]
            y_sub = effect[idx]
        else:
            x_sub = cause
            y_sub = effect

        X = x_sub.reshape(-1, 1)
        Y = y_sub

        if self.regressor == "rf":
            model = RandomForestRegressor(
                n_estimators=30, max_depth=5, random_state=self.random_state
            )
        else:
            model = KernelRidge(kernel="rbf", alpha=0.1, gamma=0.5)

        try:
            model.fit(X, Y)
            y_pred = model.predict(X)
            residual = Y - y_pred
        except Exception:
            slope, intercept, _, _, _ = stats.linregress(x_sub, y_sub)
            residual = y_sub - (slope * x_sub + intercept)

        dep = compute_distance_correlation(x_sub, residual)
        return residual, dep

    def predict_direction(self, data: np.ndarray) -> Tuple[int, float]:
        """Infer causal direction between data[:, 0] and data[:, 1].

        Returns:
            (direction, confidence)
            direction: 0 if X0 -> X1, 1 if X1 -> X0
        """
        x0 = data[:, 0]
        x1 = data[:, 1]

        _, dep_forward = self._fit_residual(x0, x1)

        _, dep_backward = self._fit_residual(x1, x0)

        if dep_forward < dep_backward:
            direction = 0
            diff = dep_backward - dep_forward
        else:
            direction = 1
            diff = dep_forward - dep_backward

        confidence = float(np.clip(0.5 + diff, 0.5, 1.0))
        return direction, confidence

    def fit(self, data: np.ndarray, variable_names: Optional[List[str]] = None) -> nx.DiGraph:
        var_names = variable_names or [f"X{i}" for i in range(data.shape[1])]
        g = nx.DiGraph()
        g.add_nodes_from(var_names)

        if len(var_names) == 2:
            direction, _ = self.predict_direction(data)
            if direction == 0:
                g.add_edge(var_names[0], var_names[1])
            else:
                g.add_edge(var_names[1], var_names[0])

        return g
