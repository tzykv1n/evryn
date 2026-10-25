#!/usr/bin/env python3
"""
Generate publication-quality, printer-friendly, monochrome-first figures
for the EVRYN Research Report and Presentation.

Mandatory rules enforced:
- Strictly square corners (no rounded corners anywhere)
- Large, readable typography (titles 13-14pt, labels 11-12pt, annotations 9.5-10.5pt)
- Generous canvas dimensions and uncrowded spacing
- High-contrast hatches and line styles
- Export both vector PDF and high-res 300 DPI PNG
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUTPUT_DIRS = [
    "/home/tk/projects/phase1_report/figures",
    "/home/tk/projects/phase1_presentation/figures",
    "/home/tk/projects/evryn/docs/phase1/figures",
]

for d in OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 11,
    "figure.titlesize": 14,
    "axes.linewidth": 1.0,
    "grid.linewidth": 0.6,
    "lines.linewidth": 1.2,
    "patch.linewidth": 1.0,
})


def save_fig(fig, base_name):
    for d in OUTPUT_DIRS:
        pdf_path = os.path.join(d, f"{base_name}.pdf")
        png_path = os.path.join(d, f"{base_name}.png")
        fig.savefig(pdf_path, bbox_inches="tight", dpi=300)
        fig.savefig(png_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved {base_name}.pdf and {base_name}.png to output directories.")


def generate_fig1_system_architecture():
    """Figure 1: End-to-End System Architecture (Expanded, large-type academic layout)."""
    fig, ax = plt.subplots(figsize=(13.2, 5.8), dpi=300)
    ax.set_xlim(0, 132)
    ax.set_ylim(0, 58)
    ax.axis("off")

    def draw_box(x, y, w, h, title, subtitle="", fill="#F8FAFC", edge="black", lw=1.2, ls="-"):
        rect = patches.Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge, linewidth=lw, linestyle=ls, zorder=2)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w / 2, y + h * 0.65, title, ha="center", va="center", fontsize=11, fontweight="bold", color="black", zorder=3)
            ax.text(x + w / 2, y + h * 0.30, subtitle, ha="center", va="center", fontsize=9.2, color="#1e293b", zorder=3)
        else:
            ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=11, fontweight="bold", color="black", zorder=3)
        return rect

    def draw_arrow(x1, y1, x2, y2, label="", ls="-"):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.4, linestyle=ls),
            zorder=4
        )
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.8, label, ha="center", va="bottom", fontsize=9.2, fontweight="bold", color="black", zorder=5)

    # Stages 1 to 5
    draw_box(2, 33, 22, 19, "Stage 1: Ingestion", "PMC-OA JATS XML / PDF\nLayout Geometry Offset")
    draw_arrow(24, 42.5, 27, 42.5)

    draw_box(27, 33, 22, 19, "Stage 2: Parsing", "Discourse Segmenter\nSection Roles & Bounds")
    draw_arrow(49, 42.5, 52, 42.5)

    draw_box(52, 33, 22, 19, "Stage 3: Normalizer", "Controlled Vocabs\nAcronyms & Synonyms")
    draw_arrow(74, 42.5, 77, 42.5)

    draw_box(77, 33, 22, 19, "Stage 4: Extraction", "Syntactic Causal Engine\nNegation & Polarity")
    draw_arrow(99, 42.5, 102, 42.5)

    draw_box(102, 33, 28, 19, "Stage 5: Verification", "Bounded Path Traversal\nConfidence Calibration")

    # Output box
    draw_box(102, 4, 28, 20, "Causal Graph Output", "Traceable Mechanism SCM\n100% Span Provenance", fill="#F1F5F9", edge="black", lw=1.4)
    draw_arrow(116, 33, 116, 24, "Resolved Claims")

    # Evidence Grounding Subsystem (Wide Lower Box)
    draw_box(2, 4, 94, 20, "Evidence Grounding Subsystem & Provenance Audit Contract",
             "Exact Character Index Spans [c_start, c_end] | Physical Page Numbers | Verbatim Quotes\nTerminal Phenotype Direction Invariant | Environmental Parameter Invariant | Homology Non-Causal Gating",
             fill="#FFFFFF", edge="black", lw=1.3, ls="--")

    # Connectors between stages and grounding subsystem
    draw_arrow(13, 33, 13, 24)
    draw_arrow(38, 33, 38, 24)
    draw_arrow(63, 33, 63, 24)
    draw_arrow(88, 33, 88, 24)
    draw_arrow(94, 14, 102, 14)
    ax.text(98, 16.2, "Verified", ha="center", va="bottom", fontsize=8.8, fontweight="bold", color="black", zorder=6)

    ax.set_title("EVRYN System Architecture: Modular End-to-End Multi-Page Causal Pipeline",
                 fontsize=13.5, fontweight="bold", pad=12)
    save_fig(fig, "fig1_system_architecture")


def generate_fig2_extraction_workflow():
    """Figure 2: Relation Extraction Workflow (High-legibility processing flow)."""
    fig, ax = plt.subplots(figsize=(13.2, 6.2), dpi=300)
    ax.set_xlim(0, 132)
    ax.set_ylim(0, 62)
    ax.axis("off")

    def draw_box(x, y, w, h, title, subtitle="", fill="#FFFFFF", edge="black", lw=1.2, ls="-", title_frac=0.68, sub_frac=0.32, sub_size=9.0):
        rect = patches.Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge, linewidth=lw, linestyle=ls, zorder=2)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w / 2, y + h * title_frac, title, ha="center", va="center", fontsize=11, fontweight="bold", color="black", zorder=3)
            ax.text(x + w / 2, y + h * sub_frac, subtitle, ha="center", va="center", fontsize=sub_size, color="#1e293b", zorder=3)
        else:
            ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=11, fontweight="bold", color="black", zorder=3)

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.4),
            zorder=4
        )
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, label, ha="center", va="center",
                    fontsize=8.8, fontweight="bold", color="black", zorder=5,
                    bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))

    # Left to right processing flow (upper row: y=36, h=18)
    draw_box(2, 36, 29, 18, "1. Candidate Generation", "Sentence-Level Entities\nLocal Syntactic Pairs")
    draw_arrow(31, 45, 35, 45)

    draw_box(35, 36, 29, 18, "2. Syntactic Validation", "Active/Passive Verbs\nAgent Nominal Patterns\nNegation Classification")
    draw_arrow(64, 45, 68, 45)

    draw_box(68, 36, 29, 18, "3. Context Resolution", "Demonstrative Anaphora\nAbbreviation Stitching\nDiscourse Connectives")
    draw_arrow(97, 45, 101, 45)

    draw_box(101, 36, 29, 18, "4. Multi-Page Linking", "2-Hop Transitive Search\nSemantic Gating\nCycle & Decay Pruning")

    # Lower Filter and Grounding Layer (lower row: y=4, h=23)
    draw_box(2, 4, 62, 23, "Strict False-Positive Controls",
             "Terminal Phenotype Invariant (Virulence cannot cause upstream genes)\nEnvironmental Parameter Invariant (Temperature/pH cannot be regulated)\nHomology & Cloning Non-Causal Gating (Cloning verbs & analogies filtered)",
             fill="#F8FAFC", edge="black", lw=1.2, ls="-", title_frac=0.76, sub_frac=0.36, sub_size=8.5)

    draw_box(68, 4, 62, 23, "5. Provenance & Calibration",
             "Dual-Sentence Evidence Tracking [S_causal, S_entity]\nCalibrated Confidence Score k in [0, 1]\nExact Character Spans & Verbatim Quotes",
             fill="#F1F5F9", edge="black", lw=1.3, title_frac=0.76, sub_frac=0.36, sub_size=8.5)

    draw_arrow(33, 36, 33, 27, "Direction Check")
    draw_arrow(82, 36, 82, 27, "Dual Spans")
    draw_arrow(115, 36, 115, 27, "Path Traversal")

    ax.set_title("EVRYN Relation Extraction Workflow: Candidate Generation to Grounded Attribution",
                 fontsize=13.5, fontweight="bold", pad=12)
    save_fig(fig, "fig2_extraction_workflow")


def generate_fig3_evidence_direction():
    """Figure 3: Evidence Grounding and Direction Diagram."""
    fig, ax = plt.subplots(figsize=(12.8, 5.5), dpi=300)
    ax.set_xlim(0, 128)
    ax.set_ylim(0, 55)
    ax.axis("off")

    def draw_box(x, y, w, h, title, subtitle="", fill="#FFFFFF", edge="black", lw=1.2, ls="-"):
        rect = patches.Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge, linewidth=lw, linestyle=ls, zorder=2)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=11, fontweight="bold", color="black", zorder=3)
            ax.text(x + w / 2, y + h * 0.30, subtitle, ha="center", va="center", fontsize=9.5, color="#1e293b", zorder=3)
        else:
            ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=11, fontweight="bold", color="black", zorder=3)

    # Top: Cause and Effect with explicit directed relation
    draw_box(6, 34, 30, 16, "Cause Entity (C)", "Canonical: PmrB\nMention: PmrB sensor kinase\nPhysical Page: Page 2", fill="#F8FAFC", edge="black", lw=1.3)
    draw_box(92, 34, 30, 16, "Effect Entity (E)", "Canonical: PmrA\nMention: response regulator\nPhysical Page: Page 3", fill="#F8FAFC", edge="black", lw=1.3)

    # Directed Causal Edge
    ax.annotate(
        "", xy=(92, 42), xytext=(36, 42),
        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.8),
        zorder=4
    )
    ax.text(64, 43.8, "RELATION: DIRECT_CAUSE (+)\nDirection: FORWARD | Confidence: 0.95",
            ha="center", va="bottom", fontsize=10.5, fontweight="bold", color="black", zorder=5)

    # Middle: Verbatim Evidence Quote
    quote_text = "\"Acid pH activates the PmrA/PmrB system by promoting PmrB-mediated phosphorylation of PmrA.\""
    draw_box(6, 17, 116, 13, "Primary Evidence Sentence (S_causal)",
             f"{quote_text}\nLocation: Section: RESULTS | Paragraph: 14 | Sentence ID: PMC1804205_s42 | Char Spans: [1420--1512]",
             fill="#FFFFFF", edge="black", lw=1.2)

    # Bottom: Contrast between Direct vs Context-Resolved vs Transitive
    draw_box(6, 2, 36, 11, "Direct Assertion", "C and E co-occur in S_causal\nSyntactic trigger: 'activation of'\nConfidence: 0.90--0.98", fill="#F8FAFC", edge="black")
    draw_box(46, 2, 36, 11, "Context-Resolved Candidate", "Span across S_k -> S_k+1\nDemonstrative pronoun bridge\nDual Provenance: [S_c, S_e]", fill="#FFFFFF", edge="black")
    draw_box(86, 2, 36, 11, "Multi-Page Transitive Link", "Path: A -> B (p.2) -> C (p.5)\nPhysical separation >= 1 page\nConfidence decay applied", fill="#F8FAFC", edge="black")

    ax.set_title("EVRYN Evidence Provenance Contract: Dual-Span Grounding and Direction Fidelity",
                 fontsize=13.5, fontweight="bold", pad=12)
    save_fig(fig, "fig3_evidence_direction")


def generate_fig4_evaluation_workflow():
    """Figure 4: Evaluation Workflow & Strict Split Isolation Boundary."""
    fig, ax = plt.subplots(figsize=(12.8, 5.8), dpi=300)
    ax.set_xlim(0, 128)
    ax.set_ylim(0, 58)
    ax.axis("off")

    def draw_box(x, y, w, h, title, subtitle="", fill="#FFFFFF", edge="black", lw=1.2, ls="-"):
        rect = patches.Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge, linewidth=lw, linestyle=ls, zorder=2)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=11, fontweight="bold", color="black", zorder=3)
            ax.text(x + w / 2, y + h * 0.30, subtitle, ha="center", va="center", fontsize=9.5, color="#1e293b", zorder=3)
        else:
            ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=11, fontweight="bold", color="black", zorder=3)

    # Development & Tuning Split (Left Box)
    rect_dev = patches.Rectangle((2, 22), 54, 32, facecolor="#F8FAFC", edgecolor="black", linewidth=1.2)
    ax.add_patch(rect_dev)
    ax.text(29, 50.5, "DEVELOPMENT & TUNING ZONE (Permitted Tuning)", ha="center", va="center", fontsize=11.5, fontweight="bold")

    draw_box(5, 25, 23, 22, "Train Split (4 Papers)", "PMC2651894--PMC2774163\nGrammar Discovery\nZero Test Access", fill="white")
    draw_box(31, 25, 23, 22, "Dev Split (8 Papers)", "PMC1804205--PMC2430206\nError Diagnosis & Census\nHyperparameter Tuning", fill="white")

    # Double-line strict split isolation boundary
    ax.plot([60.5, 60.5], [2, 56], color="black", linewidth=1.8, linestyle="--", zorder=5)
    ax.plot([63.5, 63.5], [2, 56], color="black", linewidth=1.8, linestyle="--", zorder=5)
    ax.text(62, 29, "STRICT ZERO-LEAKAGE RELEASE GATE\n(Code & Hyperparameters Frozen Prior to Confirmatory Evaluation)",
            ha="center", va="center", rotation=90, fontsize=10, fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.0), zorder=6)

    # Confirmatory & Generalization Zone (Right Box)
    rect_test = patches.Rectangle((67, 22), 59, 32, facecolor="#F1F5F9", edgecolor="black", linewidth=1.4)
    ax.add_patch(rect_test)
    ax.text(96.5, 50.5, "CONFIRMATORY EVALUATION ZONE (Strictly Blind)", ha="center", va="center", fontsize=11.5, fontweight="bold")

    draw_box(70, 25, 26, 22, "Locked Test (4 Papers)", "PMC2565068--PMC2639726\nConfirmatory Check\nFrozen Baseline Checkpoint", fill="white")
    draw_box(98, 25, 26, 22, "External Gen (4 Papers)", "PMC2816692--PMC2885601\nGenuinely Unseen Biology\nZero Prior Exposure", fill="white")

    # Lower benchmark audit box
    draw_box(2, 3, 124, 15, "Benchmark Integrity & Annotation Audit Gate",
             "Benchmark V1 (Raw / Unaligned BioCause; includes documented PMC2816692 Anthrax LF vs Salmonella SrcA mismatch)\n"
             "Benchmark V2 (Authenticated Domain-Aligned Ground Truth; 100% Provenance Coverage Verified Across All 20 Papers)",
             fill="#FFFFFF", edge="black", lw=1.2)

    ax.set_title("EVRYN 20-Paper Benchmark Partition and Strict Zero-Leakage Evaluation Protocol",
                 fontsize=13.5, fontweight="bold", pad=12)
    save_fig(fig, "fig4_evaluation_workflow")


def generate_fig5_error_analysis():
    """Figure 5: Error Analysis Taxonomy & False Negative / False Positive Breakdown."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.8, 5.5), dpi=300)

    # Left: False Negatives Taxonomy across 20-Paper Benchmark (32 Total FNs in Phase 1.12)
    categories = [
        "Discourse Claims\n(Multi-Sentence)",
        "Lexical Variant\n(Unseen Synonym)",
        "Syntactic Coordination\n(Complex Lists)",
    ]
    counts_fn = [18, 9, 5]
    pcts_fn = [c / sum(counts_fn) * 100 for c in counts_fn]

    bars1 = ax1.bar(categories, counts_fn, color=["#1e293b", "#334155", "#64748b"], edgecolor="black", width=0.50, linewidth=1.0)
    ax1.set_ylabel("False Negative Count", fontweight="bold", fontsize=11.5)
    ax1.set_title("False Negative Census (32 FNs in Phase 1.12)", fontweight="bold", fontsize=12.5, pad=12)
    ax1.set_ylim(0, 24)
    ax1.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")

    for bar, count, pct in zip(bars1, counts_fn, pcts_fn):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.6,
                 f"{count} ({pct:.1f}%)", ha="center", va="bottom", fontsize=10.5, fontweight="bold")

    # Sub-breakdown annotation
    ax1.text(0.95, 0.95, "FN Failure Census:\n• Multi-Sentence Claims: 56.2%\n• Unseen Chemical Synonyms: 28.1%\n• Non-standard Coordination: 15.6%",
             transform=ax1.transAxes, ha="right", va="top", fontsize=9.5, color="white",
             bbox=dict(boxstyle="square,pad=0.4", fc="#0f172a", ec="black", lw=1.0))

    # Right: False Positives Breakdown (76 Total FPs in V2 in Phase 1.12)
    fp_cats = [
        "Neighboring\nSpurious Pairs",
        "Passive Genetic\nComplementation",
        "Terminal Phenotype\nReversals",
        "Spurious Hub\nTransitive Leaps",
    ]
    counts_fp = [42, 14, 11, 9]
    bars2 = ax2.bar(fp_cats, counts_fp, color=["#334155", "#475569", "#64748b", "#94a3b8"], edgecolor="black", width=0.55, linewidth=1.0)
    ax2.set_ylabel("False Positive Count", fontweight="bold", fontsize=11.5)
    ax2.set_title("False Positive Taxonomy (76 FPs in V2)", fontweight="bold", fontsize=12.5, pad=12)
    ax2.set_ylim(0, 52)
    ax2.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")

    for bar, count in zip(bars2, counts_fp):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                 f"{count}", ha="center", va="bottom", fontsize=10.5, fontweight="bold")

    fig.suptitle("EVRYN Error Analysis: Systematic Census of Remaining Extraction Failures",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    save_fig(fig, "fig5_error_analysis")


def generate_fig6_results_progression():
    """Figure 6: Verified Results & Progression Across Evaluation Splits (Phase 1.12 Verified)."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(14.2, 5.2), dpi=300)

    splits = ["Train\n(4 papers)", "Dev\n(8 papers)", "Locked\n(4 papers)", "Ext V1\n(4 papers)", "Ext V2\n(4 papers)"]

    # Phase 1.12 Verified Metrics
    direct_f1 = [0.4750, 0.6551, 0.5654, 0.3269, 0.4808]
    direct_err_low = [0.4750 - 0.3667, 0.6551 - 0.5521, 0.5654 - 0.3750, 0.3269 - 0.1000, 0.4808 - 0.3538]
    direct_err_high = [0.6000 - 0.4750, 0.7523 - 0.6551, 0.7279 - 0.5654, 0.5269 - 0.3269, 0.6077 - 0.4808]

    cross_f1 = [0.2120, 0.4589, 0.2637, 0.2548, 0.3262]
    cross_err_low = [0.2120 - 0.0000, 0.4589 - 0.2585, 0.2637 - 0.0769, 0.2548 - 0.0833, 0.3262 - 0.2857]
    cross_err_high = [0.4239 - 0.2120, 0.6519 - 0.4589, 0.4176 - 0.2637, 0.3714 - 0.2548, 0.3714 - 0.3262]

    match_ratio = [0.2408, 0.4430, 0.3019, 0.1863, 0.2696]

    x = np.arange(len(splits))
    colors = ["#475569", "#0f172a", "#1e293b", "#64748b", "#334155"]

    # Panel 1: Direct F1
    bars1 = ax1.bar(x, direct_f1, yerr=[direct_err_low, direct_err_high], capsize=5,
                    color=colors, edgecolor="black", width=0.55, linewidth=1.0, error_kw=dict(lw=1.1, capthick=1.1))
    ax1.set_ylabel("Direct Causal F1", fontweight="bold", fontsize=11.5)
    ax1.set_title("Direct Relation F1 (95% CI)", fontweight="bold", fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(splits, fontsize=10)
    ax1.set_ylim(0, 0.98)
    ax1.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")
    for bar, val, eh in zip(bars1, direct_f1, direct_err_high):
        ci_top = val + eh
        ax1.text(bar.get_x() + bar.get_width() / 2, ci_top + 0.025, f"{val:.4f}",
                 ha="center", va="bottom", fontsize=9.2, fontweight="bold")

    # Panel 2: Cross-Page F1
    bars2 = ax2.bar(x, cross_f1, yerr=[cross_err_low, cross_err_high], capsize=5,
                    color=colors, edgecolor="black", width=0.55, linewidth=1.0, error_kw=dict(lw=1.1, capthick=1.1))
    ax2.set_ylabel("Cross-Page Causal F1", fontweight="bold", fontsize=11.5)
    ax2.set_title("Cross-Page Relation F1 (95% CI)", fontweight="bold", fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(splits, fontsize=10)
    ax2.set_ylim(0, 0.92)
    ax2.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")
    for bar, val, eh in zip(bars2, cross_f1, cross_err_high):
        ci_top = val + eh
        ax2.text(bar.get_x() + bar.get_width() / 2, ci_top + 0.025, f"{val:.4f}",
                 ha="center", va="bottom", fontsize=9.2, fontweight="bold")

    # Panel 3: Exact Structural Match
    bars3 = ax3.bar(x, match_ratio, color=colors, edgecolor="black", width=0.55, linewidth=1.0)
    ax3.set_ylabel("Exact Structural Match Ratio", fontweight="bold", fontsize=11.5)
    ax3.set_title("Exact Structural Match Ratio", fontweight="bold", fontsize=12)
    ax3.set_xticks(x)
    ax3.set_xticklabels(splits, fontsize=10)
    ax3.set_ylim(0, 0.60)
    ax3.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")
    for bar, val in zip(bars3, match_ratio):
        ax3.text(bar.get_x() + bar.get_width() / 2, val + 0.020, f"{val:.4f}",
                 ha="center", va="bottom", fontsize=9.2, fontweight="bold")

    fig.suptitle("EVRYN Phase 1.12 Verified Benchmark Metrics Across Isolated Splits",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    save_fig(fig, "fig6_results_progression")


def main():
    print("Generating 6 redesigned, large-format publication-quality academic figures...")
    generate_fig1_system_architecture()
    generate_fig2_extraction_workflow()
    generate_fig3_evidence_direction()
    generate_fig4_evaluation_workflow()
    generate_fig5_error_analysis()
    generate_fig6_results_progression()
    print("All 6 figures successfully regenerated in PDF and PNG vector/raster formats!")


if __name__ == "__main__":
    main()
