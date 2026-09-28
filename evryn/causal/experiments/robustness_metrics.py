# meflux robustness
# python -m causality_in_flux.experiments.run_robustness_benchmark

"""Statistical Metrics, Paired Significance Tests, and Calibration for Higher-Order Robustness.

Provides rigorous evaluation tools:
1. Distribution statistics (mean, std, median, min, max, 95% confidence intervals via Student-t)
2. Paired statistical significance tests (paired t-test and Wilcoxon signed-rank test across matched seeds)
3. Realism regime decomposition: Pairwise failure -> Higher-Order recovery analysis
4. Calibration, Precision-Recall, ROC, Brier score, and Expected Calibration Error (ECE)

Follows Sections 3, 12, 14, and 15 of experimental requirements.
"""

from typing import Dict, List, Tuple, Optional, Any, Iterable
import numpy as np
from scipy import stats
from sklearn.metrics import (
    precision_recall_curve,
    average_precision_score,
    roc_curve,
    roc_auc_score,
    brier_score_loss,
)


def compute_distribution_statistics(values: Iterable[float]) -> Dict[str, float]:
    """Compute summary statistics and 95% confidence intervals for a sequence of values."""
    arr = np.array(list(values), dtype=np.float64)
    n = len(arr)
    if n == 0:
        return {
            "mean": 0.0,
            "std": 0.0,
            "median": 0.0,
            "min": 0.0,
            "max": 0.0,
            "ci_95_lower": 0.0,
            "ci_95_upper": 0.0,
            "count": 0,
        }

    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))
    std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0

    if n > 1 and std_val > 1e-9:
        t_crit = float(stats.t.ppf(0.975, df=n - 1))
        half_width = t_crit * (std_val / np.sqrt(n))
        ci_lower = float(mean_val - half_width)
        ci_upper = float(mean_val + half_width)
    else:
        ci_lower = mean_val
        ci_upper = mean_val

    return {
        "mean": mean_val,
        "std": std_val,
        "median": median_val,
        "min": min_val,
        "max": max_val,
        "ci_95_lower": ci_lower,
        "ci_95_upper": ci_upper,
        "count": int(n),
    }


def paired_significance_test(
    scores_ho: List[float],
    scores_pw: List[float],
) -> Dict[str, Any]:
    """Perform matched-seed paired significance testing between Higher-Order FLUX and Pairwise-Only baseline.
    
    Computes:
    - Paired differences d_i = ho_i - pw_i
    - Mean improvement, std, and 95% CI
    - Paired Student-t test (statistic, p-value)
    - Wilcoxon signed-rank test (statistic, p-value)
    - Statistical significance flag (p < 0.05)
    """
    arr_ho = np.array(scores_ho, dtype=np.float64)
    arr_pw = np.array(scores_pw, dtype=np.float64)
    if len(arr_ho) != len(arr_pw) or len(arr_ho) == 0:
        raise ValueError("scores_ho and scores_pw must have identical non-zero lengths.")

    diffs = arr_ho - arr_pw
    diff_stats = compute_distribution_statistics(diffs)

    n = len(diffs)
    if n > 1 and np.std(diffs) > 1e-9:
        t_stat, t_pval = stats.ttest_rel(arr_ho, arr_pw)
        t_stat = float(t_stat)
        t_pval = float(t_pval)
    else:
        t_stat = 0.0
        t_pval = 1.0

    non_zeros = diffs[diffs != 0]
    if len(non_zeros) >= 5:
        try:
            w_stat, w_pval = stats.wilcoxon(diffs, zero_method="wilcox")
            w_stat = float(w_stat)
            w_pval = float(w_pval)
        except Exception:
            w_stat = 0.0
            w_pval = 1.0
    else:
        w_stat = 0.0
        w_pval = 1.0

    is_sig = (t_pval < 0.05) or (w_pval < 0.05)

    return {
        "mean_difference": diff_stats["mean"],
        "std_difference": diff_stats["std"],
        "ci_95_lower": diff_stats["ci_95_lower"],
        "ci_95_upper": diff_stats["ci_95_upper"],
        "t_statistic": t_stat,
        "t_pvalue": t_pval,
        "wilcoxon_statistic": w_stat,
        "wilcoxon_pvalue": w_pval,
        "is_significant": bool(is_sig),
    }


def evaluate_failure_recovery(
    pw_correct: List[bool],
    ho_correct: List[bool],
) -> Dict[str, Any]:
    """Realism Test: Classify outcomes into 4 regimes:
    1. both_correct
    2. pw_fails_ho_recovers (Higher-Order Recovery Regime)
    3. both_fail
    4. ho_fails_pw_correct (Higher-Order Breakdown Regime)
    """
    if len(pw_correct) != len(ho_correct) or len(pw_correct) == 0:
        raise ValueError("Input lists must have identical non-zero lengths.")

    n = len(pw_correct)
    both_correct = 0
    pw_fails_ho_recovers = 0
    both_fail = 0
    ho_fails_pw_correct = 0

    for pw, ho in zip(pw_correct, ho_correct):
        if pw and ho:
            both_correct += 1
        elif not pw and ho:
            pw_fails_ho_recovers += 1
        elif not pw and not ho:
            both_fail += 1
        else:
            ho_fails_pw_correct += 1

    return {
        "total_cases": n,
        "both_correct_count": both_correct,
        "both_correct_rate": float(both_correct / n),
        "pw_fails_ho_recovers_count": pw_fails_ho_recovers,
        "pw_fails_ho_recovers_rate": float(pw_fails_ho_recovers / n),
        "both_fail_count": both_fail,
        "both_fail_rate": float(both_fail / n),
        "ho_fails_pw_correct_count": ho_fails_pw_correct,
        "ho_fails_pw_correct_rate": float(ho_fails_pw_correct / n),
    }


def compute_calibration_and_pr(
    y_true: List[int],
    y_prob: List[float],
    n_bins: int = 5,
) -> Dict[str, Any]:
    """Compute calibration curve, Brier score, Expected Calibration Error (ECE), and PR curve metrics."""
    y_t = np.array(y_true, dtype=int)
    y_p = np.array(y_prob, dtype=np.float64)

    if len(y_t) == 0:
        return {}

    brier = float(brier_score_loss(y_t, y_p))

    prec, rec, thresholds_pr = precision_recall_curve(y_t, y_p)
    avg_prec = float(average_precision_score(y_t, y_p)) if len(np.unique(y_t)) > 1 else 1.0

    fpr, tpr, thresholds_roc = roc_curve(y_t, y_p)
    auc_roc = float(roc_auc_score(y_t, y_p)) if len(np.unique(y_t)) > 1 else 1.0

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    bin_confidences = []
    bin_accuracies = []
    bin_counts = []
    ece = 0.0

    n_total = len(y_p)
    for b in range(n_bins):
        bin_lower = bin_boundaries[b]
        bin_upper = bin_boundaries[b + 1]
        in_bin = (y_p >= bin_lower) & (y_p <= bin_upper if b == n_bins - 1 else y_p < bin_upper)
        count_in_bin = int(np.sum(in_bin))
        bin_counts.append(count_in_bin)

        if count_in_bin > 0:
            avg_conf = float(np.mean(y_p[in_bin]))
            avg_acc = float(np.mean(y_t[in_bin]))
            bin_confidences.append(avg_conf)
            bin_accuracies.append(avg_acc)
            ece += (count_in_bin / n_total) * abs(avg_acc - avg_conf)
        else:
            bin_confidences.append((bin_lower + bin_upper) / 2.0)
            bin_accuracies.append(0.0)

    return {
        "brier_score": brier,
        "ece": float(ece),
        "average_precision": avg_prec,
        "roc_auc": auc_roc,
        "pr_precision": prec.tolist(),
        "pr_recall": rec.tolist(),
        "pr_thresholds": thresholds_pr.tolist(),
        "roc_fpr": fpr.tolist(),
        "roc_tpr": tpr.tolist(),
        "bin_confidences": bin_confidences,
        "bin_accuracies": bin_accuracies,
        "bin_counts": bin_counts,
    }
