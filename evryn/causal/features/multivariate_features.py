# meflux feature_ablation
# python -m causality_in_flux.experiments.feature_ablation_nested

"""Multivariate Meta-Feature Extractor for Mixed Causal Graphs.

Extracts distributional, conditional independence, and asymmetry signatures to classify:
1. No relation (none / independent / conditionally independent)
2. Forward cause-effect (u -> v)
3. Backward cause-effect (u <- v)
4. Bidirected confounded relation (u <-> v, unobserved confounding)
"""

from typing import List, Tuple, Dict, Optional
import warnings
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import mutual_info_regression
from ..discovery.anm import compute_distance_correlation


class MultivariateMetaFeatureExtractor:
    """Extracts relational meta-features for pairs of variables in multivariate data."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state

    def compute_partial_correlation(self, data: np.ndarray, i: int, j: int) -> Tuple[float, float]:
        """Compute partial correlation between variable i and j given all other variables, and Fisher z-score."""
        n_samples, n_vars = data.shape
        if n_vars <= 2:
            r, _ = stats.pearsonr(data[:, i], data[:, j])
            pr = float(r) if np.isfinite(r) else 0.0
        else:
            other_idx = [k for k in range(n_vars) if k not in (i, j)]
            Z = data[:, other_idx]

            reg_i = np.linalg.lstsq(Z, data[:, i], rcond=None)[0]
            res_i = data[:, i] - Z @ reg_i

            reg_j = np.linalg.lstsq(Z, data[:, j], rcond=None)[0]
            res_j = data[:, j] - Z @ reg_j

            std_i = np.std(res_i)
            std_j = np.std(res_j)
            if std_i < 1e-9 or std_j < 1e-9:
                pr = 0.0
            else:
                pr_val = float(np.corrcoef(res_i, res_j)[0, 1])
                pr = pr_val if np.isfinite(pr_val) else 0.0

        clamped = np.clip(pr, -0.9999, 0.9999)
        dof = max(1, n_samples - n_vars - 3)
        z_score = float(0.5 * np.log((1 + clamped) / (1 - clamped)) * np.sqrt(dof))
        return pr, z_score

    def extract_pair_features(self, data: np.ndarray, i: int, j: int) -> np.ndarray:
        """Extract relational features for pair (i, j) in multivariate data matrix X."""
        xi = data[:, i].astype(np.float64)
        xj = data[:, j].astype(np.float64)
        n_samples, n_vars = data.shape

        std_i = float(np.std(xi))
        std_j = float(np.std(xj))
        if std_i < 1e-6 or std_j < 1e-6:
            return np.zeros(16, dtype=np.float32)

        z_i = (xi - np.mean(xi)) / std_i
        z_j = (xj - np.mean(xj)) / std_j

        try:
            s_i = float(stats.skew(xi))
            s_j = float(stats.skew(xj))
            k_i = float(stats.kurtosis(xi, fisher=False))
            k_j = float(stats.kurtosis(xj, fisher=False))
        except Exception:
            s_i, s_j, k_i, k_j = 0.0, 0.0, 3.0, 3.0

        try:
            r = float(np.corrcoef(xi, xj)[0, 1])
            pearson_r = r if np.isfinite(r) else 0.0
        except Exception:
            pearson_r = 0.0

        try:
            sr, _ = stats.spearmanr(xi, xj)
            spearman_r = float(sr) if np.isfinite(sr) else 0.0
        except Exception:
            spearman_r = 0.0

        part_r, z_part = self.compute_partial_correlation(data, i, j)

        try:
            slope_fwd, inter_fwd, _, _, _ = stats.linregress(xi, xj)
            if not np.isfinite(slope_fwd):
                slope_fwd, inter_fwd = 0.0, float(np.mean(xj))
            res_fwd = xj - (slope_fwd * xi + inter_fwd)
        except Exception:
            res_fwd = xj - float(np.mean(xj))

        sub_n = min(250, len(xi))
        sub_xi = xi[:sub_n]
        sub_res_fwd = res_fwd[:sub_n]
        dep_fwd = compute_distance_correlation(sub_xi, sub_res_fwd)

        try:
            slope_bwd, inter_bwd, _, _, _ = stats.linregress(xj, xi)
            if not np.isfinite(slope_bwd):
                slope_bwd, inter_bwd = 0.0, float(np.mean(xi))
            res_bwd = xi - (slope_bwd * xj + inter_bwd)
        except Exception:
            res_bwd = xi - float(np.mean(xi))

        sub_xj = xj[:sub_n]
        sub_res_bwd = res_bwd[:sub_n]
        dep_bwd = compute_distance_correlation(sub_xj, sub_res_bwd)
        asym_dep = float(dep_bwd - dep_fwd)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                poly_f = np.polyfit(xi, xj, 2)
                poly_b = np.polyfit(xj, xi, 2)
                res_poly_f = xj - np.polyval(poly_f, xi)
                res_poly_b = xi - np.polyval(poly_b, xj)
                r2_f = 1.0 - float(np.var(res_poly_f)) / (std_j ** 2 + 1e-9)
                r2_b = 1.0 - float(np.var(res_poly_b)) / (std_i ** 2 + 1e-9)
                r2_diff = float(r2_f - r2_b)
            except Exception:
                r2_f, r2_b, r2_diff = 0.0, 0.0, 0.0

            try:
                cor_res2_f = float(abs(stats.pearsonr(xi[:sub_n], res_fwd[:sub_n] ** 2)[0]))
                cor_res2_b = float(abs(stats.pearsonr(xj[:sub_n], res_bwd[:sub_n] ** 2)[0]))
                anm_asym2 = float(cor_res2_b - cor_res2_f)
            except Exception:
                anm_asym2 = 0.0

        cum_diff = float(np.mean(z_i * (z_j ** 3)) - np.mean((z_i ** 3) * z_j))

        try:
            res_corr = float(np.corrcoef(res_fwd, res_bwd)[0, 1])
            res_corr = res_corr if np.isfinite(res_corr) else 0.0
        except Exception:
            res_corr = 0.0

        cross_kurt = float(np.mean((z_i ** 2) * (z_j ** 2)))

        mi_n = min(300, len(xi))
        try:
            mi = float(mutual_info_regression(xi[:mi_n].reshape(-1, 1), xj[:mi_n], n_neighbors=3, random_state=self.random_state)[0])
        except Exception:
            mi = 0.0

        skew_denom = abs(s_i) + abs(s_j) + 1e-4
        kurt_denom = abs(k_i) + abs(k_j) + 1e-4
        var_ratio = float(np.log((std_i ** 2 + 1e-5) / (std_j ** 2 + 1e-5)))

        features = [
            abs(pearson_r),
            abs(spearman_r),
            abs(part_r),
            abs(z_part),
            mi,
            (s_i - s_j) / skew_denom,
            (k_i - k_j) / kurt_denom,
            cum_diff,
            r2_diff,
            asym_dep,
            anm_asym2,
            res_corr,
            cross_kurt,
            var_ratio,
            r2_f,
            r2_b,
        ]
        feat_arr = np.nan_to_num(np.array(features, dtype=np.float32), nan=0.0, posinf=10.0, neginf=-10.0)
        return np.clip(feat_arr, -20.0, 20.0)

    def extract_dataset_representation(self, data: np.ndarray) -> np.ndarray:
        """Extract a global dataset representation vector for evidence matching."""
        d = data.shape[1]
        pair_feats = []
        for i in range(d):
            for j in range(i + 1, d):
                pair_feats.append(self.extract_pair_features(data, i, j))

        pair_matrix = np.vstack(pair_feats)
        rep_mean = np.mean(pair_matrix, axis=0)
        rep_std = np.std(pair_matrix, axis=0)
        rep_max = np.max(pair_matrix, axis=0)
        rep = np.concatenate([rep_mean, rep_std, rep_max])
        rep = np.nan_to_num(rep, nan=0.0, posinf=5.0, neginf=-5.0)
        return np.clip(rep, -20.0, 20.0)
