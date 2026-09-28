# meflux feature_ablation
# python -m causality_in_flux.experiments.feature_ablation_nested

from typing import Dict, List, Tuple, Optional, Any, Union
import warnings
import numpy as np
from scipy import stats
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from scipy.special import digamma
from sklearn.linear_model import LinearRegression, Ridge

from .multivariate_features import MultivariateMetaFeatureExtractor
from ..discovery.anm import compute_distance_correlation


def ksg_mutual_information(X: np.ndarray, Y: np.ndarray, k: int = 3, max_samples: int = 350) -> float:
    X_arr = np.atleast_2d(X)
    if X_arr.shape[0] < X_arr.shape[1] and X_arr.shape[0] <= 4:
        X_arr = X_arr.T
    Y_arr = np.atleast_2d(Y)
    if Y_arr.shape[0] < Y_arr.shape[1] and Y_arr.shape[0] <= 4:
        Y_arr = Y_arr.T

    n = X_arr.shape[0]
    if n > max_samples:
        idx = np.linspace(0, n - 1, max_samples, dtype=int)
        X_arr = X_arr[idx]
        Y_arr = Y_arr[idx]
        n = max_samples

    std_x = np.std(X_arr, axis=0) + 1e-9
    std_y = np.std(Y_arr, axis=0) + 1e-9
    X_norm = (X_arr - np.mean(X_arr, axis=0)) / std_x
    Y_norm = (Y_arr - np.mean(Y_arr, axis=0)) / std_y

    Z = np.hstack([X_norm, Y_norm])
    tree_z = cKDTree(Z)
    tree_x = cKDTree(X_norm)
    tree_y = cKDTree(Y_norm)

    k_eff = min(k, n - 2)
    if k_eff < 1:
        return 0.0

    dists, _ = tree_z.query(Z, k=k_eff + 1, p=np.inf)
    eps = dists[:, -1] - 1e-15

    nx = np.array([len(tree_x.query_ball_point(pt, eps[i], p=np.inf)) - 1 for i, pt in enumerate(X_norm)])
    ny = np.array([len(tree_y.query_ball_point(pt, eps[i], p=np.inf)) - 1 for i, pt in enumerate(Y_norm)])

    mi = digamma(k_eff) - np.mean(digamma(nx + 1) + digamma(ny + 1)) + digamma(n)
    return max(0.0, float(mi))


def compute_gaussian_entropy(X: np.ndarray) -> float:
    cov = np.cov(X, rowvar=False)
    cov = np.atleast_2d(cov)
    d = cov.shape[0]
    _, logdet = np.linalg.slogdet(cov + 1e-6 * np.eye(d))
    return float(0.5 * d * (1.0 + np.log(2.0 * np.pi)) + 0.5 * logdet)


def compute_hsic_metric(X: np.ndarray, Y: np.ndarray, max_samples: int = 300) -> float:
    X_arr = np.atleast_2d(X)
    if X_arr.shape[0] < X_arr.shape[1] and X_arr.shape[0] <= 4:
        X_arr = X_arr.T
    Y_arr = np.atleast_2d(Y)
    if Y_arr.shape[0] < Y_arr.shape[1] and Y_arr.shape[0] <= 4:
        Y_arr = Y_arr.T

    n = min(X_arr.shape[0], max_samples)
    if n < 4:
        return 0.0

    X_sub = X_arr[:n]
    Y_sub = Y_arr[:n]

    d_x = cdist(X_sub, X_sub, "sqeuclidean")
    d_y = cdist(Y_sub, Y_sub, "sqeuclidean")
    med_x = float(np.median(d_x))
    med_y = float(np.median(d_y))
    gamma_x = 1.0 / (med_x + 1e-6)
    gamma_y = 1.0 / (med_y + 1e-6)

    K = np.exp(-gamma_x * d_x)
    L = np.exp(-gamma_y * d_y)

    H = np.eye(n) - np.ones((n, n)) / n
    Kc = H @ K @ H
    Lc = H @ L @ H

    hsic_xy = np.trace(Kc @ Lc) / ((n - 1) ** 2)
    hsic_xx = np.trace(Kc @ Kc) / ((n - 1) ** 2)
    hsic_yy = np.trace(Lc @ Lc) / ((n - 1) ** 2)

    denom = np.sqrt(max(1e-12, hsic_xx * hsic_yy))
    return float(np.clip(hsic_xy / denom, 0.0, 1.0))


class FastRFFTransformer:

    def __init__(self, n_components: int = 36, gamma: float = 0.5, seed: int = 42):
        self.n_components = n_components
        self.gamma = gamma
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.W = None
        self.b = None

    def transform(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.atleast_2d(X)
        d = X_arr.shape[1]
        if self.W is None or self.W.shape[0] != d:
            self.W = self.rng.normal(0, np.sqrt(2 * self.gamma), size=(d, self.n_components))
            self.b = self.rng.uniform(0, 2 * np.pi, size=self.n_components)
        proj = np.dot(X_arr, self.W) + self.b
        return np.sqrt(2.0 / self.n_components) * np.cos(proj)


class HigherOrderFeatureExtractor:

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.pairwise_extractor = MultivariateMetaFeatureExtractor(random_state=random_state)
        self.rff_a = FastRFFTransformer(n_components=28, gamma=0.5, seed=42)
        self.rff_b = FastRFFTransformer(n_components=28, gamma=0.5, seed=43)
        self.rff_j = FastRFFTransformer(n_components=56, gamma=0.5, seed=44)
        self._cache: Dict[Tuple[int, int, int, int, bool], Dict[str, float]] = {}

    def extract_triple_features(
        self,
        data: np.ndarray,
        src_a: int,
        src_b: int,
        target_c: int,
        environments_data: Optional[List[np.ndarray]] = None,
        interventions_data: Optional[Dict[str, np.ndarray]] = None,
    ) -> Dict[str, float]:
        n_samples = data.shape[0]
        sub_n = min(350, n_samples)

        cache_key = (
            id(data),
            min(src_a, src_b),
            max(src_a, src_b),
            target_c,
            environments_data is not None,
        )
        if cache_key in self._cache:
            return self._cache[cache_key]

        A = data[:sub_n, src_a].astype(np.float64)
        B = data[:sub_n, src_b].astype(np.float64)
        C = data[:sub_n, target_c].astype(np.float64)

        std_a = np.std(A) + 1e-9
        std_b = np.std(B) + 1e-9
        std_c = np.std(C) + 1e-9
        a = (A - np.mean(A)) / std_a
        b = (B - np.mean(B)) / std_b
        c = (C - np.mean(C)) / std_c

        mi_ac = ksg_mutual_information(a, c, max_samples=sub_n)
        mi_bc = ksg_mutual_information(b, c, max_samples=sub_n)
        mi_ab = ksg_mutual_information(a, b, max_samples=sub_n)

        ab_joint = np.column_stack([a, b])
        mi_joint = ksg_mutual_information(ab_joint, c, max_samples=sub_n)

        cmi_a_given_b = max(0.0, mi_joint - mi_bc)
        cmi_b_given_a = max(0.0, mi_joint - mi_ac)

        interaction_info = float(mi_joint - mi_ac - mi_bc)

        redundancy = min(mi_ac, mi_bc)
        unique_a = max(0.0, mi_ac - redundancy)
        unique_b = max(0.0, mi_bc - redundancy)
        synergy = max(0.0, interaction_info + redundancy)
        synergy_ratio = float(synergy / (mi_joint + 1e-6))
        redundancy_ratio = float(redundancy / (mi_joint + 1e-6))

        X_add = np.column_stack([a, b, a**2, b**2, np.tanh(a), np.tanh(b)])
        X_joint = np.column_stack([X_add, a * b, np.tanh(a * b)])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                reg_add = LinearRegression().fit(X_add, c)
                r2_add = float(np.clip(reg_add.score(X_add, c), 0.0, 1.0))
            except Exception:
                r2_add = 0.0

            try:
                reg_joint = LinearRegression().fit(X_joint, c)
                r2_joint = float(np.clip(reg_joint.score(X_joint, c), 0.0, 1.0))
            except Exception:
                r2_joint = 0.0

        r2_interaction_gain = max(0.0, float(r2_joint - r2_add))
        interaction_ratio = float(r2_interaction_gain / (1.0 - r2_add + 1e-6))

        phi_a = self.rff_a.transform(a.reshape(-1, 1))
        phi_b = self.rff_b.transform(b.reshape(-1, 1))
        phi_add = np.hstack([phi_a, phi_b])
        phi_joint = self.rff_j.transform(ab_joint)

        try:
            r_add_np = Ridge(alpha=1.0).fit(phi_add, c)
            r_joint_np = Ridge(alpha=1.0).fit(phi_joint, c)
            r2_add_np = float(np.clip(r_add_np.score(phi_add, c), 0.0, 1.0))
            r2_joint_np = float(np.clip(r_joint_np.score(phi_joint, c), 0.0, 1.0))
            delta_r2_nonparam = max(0.0, float(r2_joint_np - r2_add_np))
        except Exception:
            r2_add_np, r2_joint_np, delta_r2_nonparam = 0.0, 0.0, 0.0

        X_poly_add = np.column_stack([A, B, A**2, B**2, np.tanh(A), np.tanh(B)])
        X_poly_joint = np.column_stack([X_poly_add, A * B])
        try:
            r_p_add = Ridge(alpha=1e-3).fit(X_poly_add, C)
            r_p_joint = Ridge(alpha=1e-3).fit(X_poly_joint, C)
            rss_add = float(np.sum((C - r_p_add.predict(X_poly_add))**2))
            rss_joint = float(np.sum((C - r_p_joint.predict(X_poly_joint))**2))
            bic_gain = float(-0.5 * sub_n * np.log(max(1e-9, rss_joint / max(1e-9, rss_add))) - 0.5 * np.log(sub_n))
        except Exception:
            bic_gain = 0.0

        hsic_joint = compute_hsic_metric(ab_joint, c)
        hsic_interaction = compute_hsic_metric((a * b).reshape(-1, 1), c)

        dcor_joint = float(compute_distance_correlation(ab_joint[:200], c[:200]))
        dcor_interaction = float(compute_distance_correlation((a * b)[:200].reshape(-1, 1), c[:200]))

        abc_mat = np.column_stack([a, b, c])
        h_abc = compute_gaussian_entropy(abc_mat)
        h_a = compute_gaussian_entropy(a.reshape(-1, 1))
        h_b = compute_gaussian_entropy(b.reshape(-1, 1))
        h_c = compute_gaussian_entropy(c.reshape(-1, 1))
        total_correlation = max(0.0, float(h_a + h_b + h_c - h_abc))

        res_joint = c - reg_joint.predict(X_joint) if 'reg_joint' in locals() else c
        res_dep = float(compute_distance_correlation(ab_joint[:200], res_joint[:200]))

        if environments_data is not None and len(environments_data) > 1:
            env_slopes = []
            env_res_vars = []
            for e_data in environments_data:
                e_sub = min(200, len(e_data))
                e_a = (e_data[:e_sub, src_a] - np.mean(e_data[:e_sub, src_a])) / (np.std(e_data[:e_sub, src_a]) + 1e-9)
                e_b = (e_data[:e_sub, src_b] - np.mean(e_data[:e_sub, src_b])) / (np.std(e_data[:e_sub, src_b]) + 1e-9)
                e_c = (e_data[:e_sub, target_c] - np.mean(e_data[:e_sub, target_c])) / (np.std(e_data[:e_sub, target_c]) + 1e-9)
                e_feat = np.column_stack([e_a, e_b, e_a * e_b])
                try:
                    e_reg = Ridge(alpha=1e-2).fit(e_feat, e_c)
                    env_slopes.append(e_reg.coef_)
                    res = e_c - e_reg.predict(e_feat)
                    env_res_vars.append(float(np.var(res)))
                except Exception:
                    pass
            if len(env_slopes) > 1:
                coef_variance = float(np.mean(np.var(env_slopes, axis=0)))
                residual_variance_var = float(np.var(env_res_vars))
                cmi_stability = float(1.0 / (1.0 + coef_variance + residual_variance_var))
            else:
                coef_variance, residual_variance_var, cmi_stability = 0.0, 0.0, 1.0
        else:
            comp = a + b
            q1, q2 = np.percentile(comp, [33.3, 66.7])
            env_slopes, env_res_vars = [], []
            for mask in [comp <= q1, (comp > q1) & (comp <= q2), comp > q2]:
                if np.sum(mask) >= 12:
                    try:
                        e_feat = np.column_stack([a[mask], b[mask], a[mask] * b[mask]])
                        e_reg = Ridge(alpha=1e-2).fit(e_feat, c[mask])
                        env_slopes.append(e_reg.coef_)
                        res = c[mask] - e_reg.predict(e_feat)
                        env_res_vars.append(float(np.var(res)))
                    except Exception:
                        pass
            if len(env_slopes) > 1:
                coef_variance = float(np.mean(np.var(env_slopes, axis=0)))
                residual_variance_var = float(np.var(env_res_vars))
                cmi_stability = float(1.0 / (1.0 + coef_variance + residual_variance_var))
            else:
                coef_variance, residual_variance_var, cmi_stability = 0.0, 0.0, 1.0

        confounding_score = float(np.clip(coef_variance + residual_variance_var, 0.0, 50.0))

        intervention_shift = 0.0
        if interventions_data is not None and len(interventions_data) > 0:
            shifts = []
            obs_mean_c = float(np.mean(c))
            for int_name, int_data in interventions_data.items():
                if int_data.shape[0] > 10:
                    int_c = (int_data[:, target_c] - np.mean(C)) / std_c
                    shifts.append(abs(float(np.mean(int_c)) - obs_mean_c))
            if shifts:
                intervention_shift = float(np.mean(shifts))

        pf_ac = self.pairwise_extractor.extract_pair_features(data, src_a, target_c)
        pf_bc = self.pairwise_extractor.extract_pair_features(data, src_b, target_c)
        pf_ab = self.pairwise_extractor.extract_pair_features(data, src_a, src_b)

        res_dict = {
            "mi_ac": mi_ac,
            "mi_bc": mi_bc,
            "mi_ab": mi_ab,
            "mi_joint": mi_joint,
            "cmi_a_given_b": cmi_a_given_b,
            "cmi_b_given_a": cmi_b_given_a,
            "interaction_info": interaction_info,
            "redundancy": redundancy,
            "unique_a": unique_a,
            "unique_b": unique_b,
            "synergy": synergy,
            "synergy_ratio": synergy_ratio,
            "redundancy_ratio": redundancy_ratio,
            "r2_add": r2_add,
            "r2_joint": r2_joint,
            "r2_interaction_gain": r2_interaction_gain,
            "interaction_ratio": interaction_ratio,
            "r2_add_np": r2_add_np,
            "r2_joint_np": r2_joint_np,
            "delta_r2_nonparam": delta_r2_nonparam,
            "bic_gain": bic_gain,
            "hsic_joint": hsic_joint,
            "hsic_interaction": hsic_interaction,
            "dcor_joint": dcor_joint,
            "dcor_interaction": dcor_interaction,
            "total_correlation": total_correlation,
            "joint_entropy": h_abc,
            "res_joint_dep": res_dep,
            "coef_variance": coef_variance,
            "residual_variance_var": residual_variance_var,
            "cmi_stability": cmi_stability,
            "confounding_score": confounding_score,
            "intervention_shift": intervention_shift,
            "pf_ac_corr": float(pf_ac[0]),
            "pf_bc_corr": float(pf_bc[0]),
            "pf_ab_corr": float(pf_ab[0]),
            "pf_ac_part": float(pf_ac[2]),
            "pf_bc_part": float(pf_bc[2]),
            "pf_ac_asym": float(pf_ac[9]),
            "pf_bc_asym": float(pf_bc[9]),
        }

        self._cache[cache_key] = res_dict
        return res_dict

    def extract_order3_features(
        self,
        data: np.ndarray,
        src_a: int,
        src_b: int,
        src_c: int,
        target_d: int,
    ) -> Dict[str, float]:
        n_samples = data.shape[0]
        sub_n = min(350, n_samples)
        A = data[:sub_n, src_a].astype(np.float64)
        B = data[:sub_n, src_b].astype(np.float64)
        C = data[:sub_n, src_c].astype(np.float64)
        D = data[:sub_n, target_d].astype(np.float64)

        a = (A - np.mean(A)) / (np.std(A) + 1e-9)
        b = (B - np.mean(B)) / (np.std(B) + 1e-9)
        c = (C - np.mean(C)) / (np.std(C) + 1e-9)
        d = (D - np.mean(D)) / (np.std(D) + 1e-9)

        mi_ad = ksg_mutual_information(a, d, max_samples=sub_n)
        mi_bd = ksg_mutual_information(b, d, max_samples=sub_n)
        mi_cd = ksg_mutual_information(c, d, max_samples=sub_n)

        abc_joint = np.column_stack([a, b, c])
        mi_joint_3way = ksg_mutual_information(abc_joint, d, max_samples=sub_n)

        ii_3way = float(mi_joint_3way - (mi_ad + mi_bd + mi_cd))

        X_add = np.column_stack([a, b, c, a**2, b**2, c**2])
        X_joint = np.column_stack([X_add, a * b, a * c, b * c, a * b * c])

        try:
            r2_add = float(np.clip(LinearRegression().fit(X_add, d).score(X_add, d), 0.0, 1.0))
            r2_joint = float(np.clip(LinearRegression().fit(X_joint, d).score(X_joint, d), 0.0, 1.0))
        except Exception:
            r2_add, r2_joint = 0.0, 0.0

        r2_gain = max(0.0, r2_joint - r2_add)

        cols_add = [A, B, C, A**2, B**2, C**2, np.tanh(A), np.tanh(B), np.tanh(C), A * B, A * C, B * C]
        X_poly_add = np.column_stack(cols_add)
        X_poly_joint = np.column_stack([X_poly_add, A * B * C])
        try:
            r_3_add = Ridge(alpha=1e-3).fit(X_poly_add, D)
            r_3_joint = Ridge(alpha=1e-3).fit(X_poly_joint, D)
            rss_add = float(np.sum((D - r_3_add.predict(X_poly_add))**2))
            rss_joint = float(np.sum((D - r_3_joint.predict(X_poly_joint))**2))
            bic_gain_3way = float(-0.5 * sub_n * np.log(max(1e-9, rss_joint / max(1e-9, rss_add))) - 0.5 * np.log(sub_n))
        except Exception:
            bic_gain_3way = 0.0

        hsic_3way = compute_hsic_metric(abc_joint, d)

        abcd_mat = np.column_stack([a, b, c, d])
        tc_4 = max(0.0, float(compute_gaussian_entropy(a.reshape(-1, 1)) +
                              compute_gaussian_entropy(b.reshape(-1, 1)) +
                              compute_gaussian_entropy(c.reshape(-1, 1)) +
                              compute_gaussian_entropy(d.reshape(-1, 1)) -
                              compute_gaussian_entropy(abcd_mat)))

        return {
            "mi_ad": mi_ad,
            "mi_bd": mi_bd,
            "mi_cd": mi_cd,
            "mi_joint_3way": mi_joint_3way,
            "ii_3way": ii_3way,
            "r2_add": r2_add,
            "r2_joint": r2_joint,
            "r2_gain_3way": r2_gain,
            "bic_gain_3way": bic_gain_3way,
            "hsic_3way": hsic_3way,
            "tc_4way": tc_4,
        }

    def vector_from_dict(
        self,
        feat_dict: Dict[str, float],
        ablation_group: str = "all_features",
    ) -> np.ndarray:
        pairwise_keys = ["pf_ac_corr", "pf_bc_corr", "pf_ab_corr", "pf_ac_part", "pf_bc_part", "pf_ac_asym", "pf_bc_asym", "mi_ac", "mi_bc", "mi_ab"]
        higher_order_keys = ["mi_joint", "total_correlation", "joint_entropy", "res_joint_dep"]
        synergy_keys = ["interaction_info", "synergy", "synergy_ratio", "r2_interaction_gain", "interaction_ratio", "redundancy", "redundancy_ratio"]
        cond_dep_keys = ["cmi_a_given_b", "cmi_b_given_a", "unique_a", "unique_b"]
        invariance_keys = ["coef_variance", "residual_variance_var", "cmi_stability", "intervention_shift"]

        mechanism_aware_keys = [
            "delta_r2_nonparam",
            "bic_gain",
            "hsic_joint",
            "hsic_interaction",
            "dcor_joint",
            "dcor_interaction",
            "confounding_score",
        ]

        if ablation_group in ("cond_A", "pairwise_only", "pairwise"):
            selected = pairwise_keys
        elif ablation_group in ("cond_B", "plus_joint_mi"):
            selected = pairwise_keys + ["mi_joint", "total_correlation"]
        elif ablation_group in ("cond_C", "plus_conditional_mi"):
            selected = pairwise_keys + ["mi_joint", "total_correlation"] + ["cmi_a_given_b", "cmi_b_given_a"]
        elif ablation_group in ("cond_D", "plus_pid_synergy"):
            selected = pairwise_keys + ["mi_joint", "total_correlation"] + ["cmi_a_given_b", "cmi_b_given_a"] + [
                "interaction_info", "synergy", "synergy_ratio", "redundancy", "redundancy_ratio"
            ]
        elif ablation_group in ("cond_E", "plus_interaction_gain"):
            selected = pairwise_keys + ["mi_joint", "total_correlation"] + ["cmi_a_given_b", "cmi_b_given_a"] + [
                "interaction_info", "synergy", "synergy_ratio", "redundancy", "redundancy_ratio",
                "r2_interaction_gain", "interaction_ratio"
            ]
        elif ablation_group in ("cond_F", "plus_invariance"):
            selected = pairwise_keys + higher_order_keys + cond_dep_keys + synergy_keys + invariance_keys
        elif ablation_group == "pairwise_plus_higher_order":
            selected = pairwise_keys + higher_order_keys
        elif ablation_group == "pairwise_plus_synergy":
            selected = pairwise_keys + higher_order_keys + ["interaction_info", "synergy", "synergy_ratio"]
        elif ablation_group == "all_features":
            selected = pairwise_keys + higher_order_keys + synergy_keys + cond_dep_keys + invariance_keys
        elif ablation_group == "plus_nonparam_r2":
            selected = pairwise_keys + higher_order_keys + cond_dep_keys + synergy_keys + invariance_keys + ["delta_r2_nonparam", "r2_add_np", "r2_joint_np"]
        elif ablation_group == "plus_hsic":
            selected = pairwise_keys + higher_order_keys + cond_dep_keys + synergy_keys + invariance_keys + ["delta_r2_nonparam", "hsic_joint", "hsic_interaction"]
        elif ablation_group == "plus_dcor":
            selected = pairwise_keys + higher_order_keys + cond_dep_keys + synergy_keys + invariance_keys + ["delta_r2_nonparam", "hsic_joint", "hsic_interaction", "dcor_joint", "dcor_interaction"]
        elif ablation_group == "plus_confounding":
            selected = pairwise_keys + higher_order_keys + cond_dep_keys + synergy_keys + invariance_keys + ["delta_r2_nonparam", "bic_gain", "confounding_score"]
        elif ablation_group in ("mechanism_aware", "cond_G"):
            selected = pairwise_keys + higher_order_keys + synergy_keys + cond_dep_keys + invariance_keys + mechanism_aware_keys
        else:
            selected = pairwise_keys + higher_order_keys + synergy_keys + cond_dep_keys + invariance_keys + mechanism_aware_keys

        vals = [feat_dict.get(k, 0.0) for k in selected]
        vec = np.nan_to_num(np.array(vals, dtype=np.float32), nan=0.0, posinf=10.0, neginf=-10.0)
        return np.clip(vec, -20.0, 20.0)
