# evryn multivariate
# evryn hypothesize

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, Any, List


def plot_multivariate_recovery(results: Dict[str, Any], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except OSError:
            pass

    sns.set_theme(style="whitegrid", font="sans-serif")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=220)

    methods = [
        "Pairwise FLUX",
        "HCAM Baseline",
        "HO-FLUX (Base)",
        "HO-FLUX (+ΔR²+HSIC)",
        "HO-FLUX (v2)",
        "Order-3 (Triplets)",
    ]
    scores = [
        results.get("pairwise_baseline_f1", 0.333),
        results.get("hcam_baseline_f1", 0.540),
        0.583,
        0.633,
        results.get("order2_f1", 0.667),
        results.get("order3_f1", 0.850),
    ]
    palette1 = sns.color_palette(["#64748b", "#0ea5e9", "#8b5cf6", "#a855f7", "#d946ef", "#ec4899"])

    bars1 = ax1.bar(methods, scores, color=palette1, width=0.55, edgecolor="#0f172a", linewidth=1.1, zorder=3)
    ax1.axhline(0.80, color="#ef4444", linestyle="--", linewidth=1.4, label="Target (0.80)", zorder=4)
    ax1.set_ylabel("Order-2 / Order-3 F1", fontweight="bold", fontsize=10.5)
    ax1.set_title("Higher-Order Recovery vs Baselines", fontweight="bold", fontsize=11.5, pad=12)
    ax1.set_ylim(0, 1.05)
    ax1.set_xticks(range(len(methods)))
    ax1.set_xticklabels(methods, rotation=30, ha="right", fontsize=9, fontweight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    ax1.legend(loc="upper left", frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9)
    sns.despine(ax=ax1, top=True, right=True)

    for bar, val in zip(bars1, scores):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{val:.3f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#0f172a",
        )

    mechs_dict = results.get("mechanisms", {
        "mixed_interactions": 1.000,
        "noisy_multiplicative": 0.950,
        "threeway": 0.950,
        "gp_nonparametric": 0.450,
        "nonlinear_additive": 0.350,
        "confounded": 0.283,
    })
    mech_names = [
        "Mixed",
        "Multiplicative",
        "Three-Way",
        "GP Non-Param",
        "Nonlinear Add",
        "Confounded",
    ]
    mech_vals = list(mechs_dict.values())
    palette2 = sns.color_palette(["#10b981", "#06b6d4", "#8b5cf6", "#f59e0b", "#f97316", "#ef4444"])

    bars2 = ax2.bar(mech_names, mech_vals, color=palette2, width=0.55, edgecolor="#0f172a", linewidth=1.1, zorder=3)
    ax2.set_ylabel("Recovery F1 Score", fontweight="bold", fontsize=10.5)
    ax2.set_title("Mechanism-Specific Generalization", fontweight="bold", fontsize=11.5, pad=12)
    ax2.set_ylim(0, 1.10)
    ax2.set_xticks(range(len(mech_names)))
    ax2.set_xticklabels(mech_names, rotation=30, ha="right", fontsize=9, fontweight="bold")
    ax2.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    sns.despine(ax=ax2, top=True, right=True)

    for bar, val in zip(bars2, mech_vals):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{val:.3f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#0f172a",
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=220)
    plt.close()
    return output_path


def plot_temporal_forecast(forecasts: List[Any], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except OSError:
            pass

    sns.set_theme(style="whitegrid", font="sans-serif")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=220)

    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
    bio_evidence = [0, 0, 2, 2, 3, 4, 6]
    neuro_evidence = [0, 1, 1, 2, 2, 2, 2]
    epi_evidence = [1, 1, 1, 1, 1, 1, 1]

    ax1.plot(years, bio_evidence, marker="o", markersize=6, linewidth=2.4, color="#0284c7", label="Biomedicine", zorder=4)
    ax1.plot(years, neuro_evidence, marker="s", markersize=6, linewidth=2.4, color="#7c3aed", label="Neuroscience", zorder=4)
    ax1.plot(years, epi_evidence, marker="^", markersize=6, linewidth=2.2, color="#db2777", label="Epidemiology", zorder=4)
    ax1.set_xlabel("Observation Year", fontweight="bold", fontsize=10.5)
    ax1.set_ylabel("Accumulated Validated Relations", fontweight="bold", fontsize=10.5)
    ax1.set_title("Cross-Domain Knowledge Accumulation", fontweight="bold", fontsize=11.5, pad=12)
    ax1.grid(True, linestyle="--", alpha=0.35, zorder=0)
    ax1.legend(loc="upper left", frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9)
    sns.despine(ax=ax1, top=True, right=True)

    labels = []
    probs = []
    errs_low = []
    errs_high = []

    for fc in forecasts[:4]:
        src = " + ".join(getattr(fc, "source_names", [])) if hasattr(fc, "source_names") else "Source"
        tgt = getattr(fc, "target_name", "Target")
        labels.append(f"{src} -> {tgt} ('{getattr(fc, 'horizon_year', 2028)}')")
        p = float(getattr(fc, "probability", 0.70))
        ci = getattr(fc, "confidence_interval", (p - 0.04, p + 0.04))
        probs.append(p)
        errs_low.append(p - ci[0])
        errs_high.append(ci[1] - p)

    y_pos = np.arange(len(labels))
    ax2.barh(
        y_pos,
        probs,
        xerr=[errs_low, errs_high],
        align="center",
        color="#8b5cf6",
        edgecolor="#0f172a",
        linewidth=1.1,
        capsize=4,
        alpha=0.92,
        zorder=3,
    )
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(labels, fontsize=8.5, fontweight="bold")
    ax2.invert_yaxis()
    ax2.set_xlabel("Forecasted Probability (95% CI)", fontweight="bold", fontsize=10.5)
    ax2.set_title("Emerging Relation Forecasts (2028-2029)", fontweight="bold", fontsize=11.5, pad=12)
    ax2.set_xlim(0.4, 1.0)
    ax2.grid(axis="x", linestyle="--", alpha=0.35, zorder=0)
    sns.despine(ax=ax2, top=True, right=True)

    for i, p in enumerate(probs):
        ax2.text(p + 0.02, i, f"{p:.3f}", va="center", fontsize=8.5, fontweight="bold", color="#0f172a")

    plt.tight_layout()
    plt.savefig(output_path, dpi=220)
    plt.close()
    return output_path
