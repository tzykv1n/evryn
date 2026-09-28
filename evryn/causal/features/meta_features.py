# meflux feature_ablation
# python -m causality_in_flux.experiments.feature_ablation_nested

r"""Meta-Features Extraction for Causal Datasets.

Implements the exact meta-features from Table 1 of the paper:
"Causality in Flux: Continual Adaptation of Causal Knowledge via Evidence Matching"
1. Skewness: E[(X - \mu_X)^3] / \sigma_X^3 (measures normality / asymmetry)
2. Kurtosis: E[(X - \mu_X)^4] / \sigma_X^4 (measures tail heaviness / outlier propensity)
3. Mutual Information: MI(X1, X2) (measures non-linear dependency / entropy)
4. Correlation: \rho_{X1, X2} (measures linear dependency)

Also supports expanded statistical meta-features capturing joint and marginal
distributional properties.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from scipy import stats
from sklearn.feature_selection import mutual_info_regression


class MetaFeatureExtractor:
    """Extracts meta-features from a dataset of observations X in R^{n x d}."""

    def __init__(
        self,
        include_expanded: bool = False,
        random_state: int = 42,
    ):
        self.include_expanded = include_expanded
        self.random_state = random_state

    @property
    def feature_names(self) -> List[str]:
        core = [
            "skewness_x1",
            "skewness_x2",
            "kurtosis_x1",
            "kurtosis_x2",
            "mutual_information",
            "correlation",
        ]
        if self.include_expanded:
            core.extend([
                "spearman_correlation",
                "variance_ratio_log",
                "quantile_spread_x1",
                "quantile_spread_x2",
                "mean_diff_normalized",
            ])
        return core

    def extract(self, data: np.ndarray) -> np.ndarray:
        """Extract meta-features from data array of shape (N, 2).

        Returns:
            np.ndarray of shape (num_features,)
        """
        if data.ndim != 2 or data.shape[1] < 2:
            raise ValueError(f"Expected 2D array with at least 2 columns, got shape {data.shape}")

        x1 = data[:, 0].astype(np.float64)
        x2 = data[:, 1].astype(np.float64)

        valid_mask = np.isfinite(x1) & np.isfinite(x2)
        if not np.all(valid_mask):
            x1 = x1[valid_mask]
            x2 = x2[valid_mask]

        if len(x1) < 4:
            raise ValueError("Too few samples to calculate meta-features.")

        skew_x1 = float(stats.skew(x1, bias=False))
        skew_x2 = float(stats.skew(x2, bias=False))

        kurt_x1 = float(stats.kurtosis(x1, fisher=False, bias=False))
        kurt_x2 = float(stats.kurtosis(x2, fisher=False, bias=False))

        std_x1 = np.std(x1, ddof=1)
        std_x2 = np.std(x2, ddof=1)
        if std_x1 < 1e-12 or std_x2 < 1e-12:
            corr = 0.0
        else:
            r, _ = stats.pearsonr(x1, x2)
            corr = float(r) if np.isfinite(r) else 0.0

        try:
            if len(x1) > 2000:
                rng = np.random.default_rng(self.random_state)
                idx = rng.choice(len(x1), size=2000, replace=False)
                sub_x1, sub_x2 = x1[idx], x2[idx]
            else:
                sub_x1, sub_x2 = x1, x2

            mi_val = mutual_info_regression(
                sub_x1.reshape(-1, 1),
                sub_x2,
                n_neighbors=3,
                random_state=self.random_state,
            )[0]
            mi = float(max(0.0, mi_val))
        except Exception:
            mi = 0.0

        features = [
            skew_x1,
            skew_x2,
            kurt_x1,
            kurt_x2,
            mi,
            corr,
        ]

        if self.include_expanded:
            sr, _ = stats.spearmanr(x1, x2)
            spearman_corr = float(sr) if np.isfinite(sr) else 0.0

            v1 = np.var(x1, ddof=1) + 1e-9
            v2 = np.var(x2, ddof=1) + 1e-9
            var_ratio = float(np.log(v1 / v2))

            iqr1 = stats.iqr(x1) / (std_x1 + 1e-9)
            iqr2 = stats.iqr(x2) / (std_x2 + 1e-9)

            mean_diff = float((np.mean(x1) - np.mean(x2)) / (std_x1 + std_x2 + 1e-9))

            features.extend([
                spearman_corr,
                var_ratio,
                float(iqr1),
                float(iqr2),
                mean_diff,
            ])

        return np.array(features, dtype=np.float32)

    def extract_batch(self, datasets: List[np.ndarray]) -> np.ndarray:
        """Extract meta-features for multiple datasets.

        Returns:
            np.ndarray of shape (len(datasets), num_features)
        """
        matrix = [self.extract(d) for d in datasets]
        return np.vstack(matrix)
