#!/usr/bin/env python3
"""
Generate publication-quality, printer-friendly, monochrome-first figures
for the EVRYN Research Report and Presentation.

Mandatory rules enforced:
- Strictly square corners (no rounded corners anywhere)
- Black text, thin black rules (0.6-1.2pt), neutral grayscale fills
- Color used strictly as meaningful accent, 100% readable in grayscale
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
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 12,
    "axes.linewidth": 0.8,
    "grid.linewidth": 0.5,
    "lines.linewidth": 1.0,
    "patch.linewidth": 0.8,
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
    """Figure 1: End-to-End System Architecture (Square-cornered academic layout)."""
    fig, ax = plt.subplots(figsize=(10.5, 4.6), dpi=300)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 46)
    ax.axis("off")

    # Helper for square box
    def draw_box(x, y, w, h, title, subtitle="", fill="#F8FAFC", edge="black", lw=1.0, ls="-"):
        rect = patches.Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge, linewidth=lw, linestyle=ls, zorder=2)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w / 2, y + h * 0.65, title, ha="center", va="center", fontsize=9.5, fontweight="bold", color="black", zorder=3)
            ax.text(x + w / 2, y + h * 0.32, subtitle, ha="center", va="center", fontsize=7.5, color="#222222", zorder=3)
        else:
            ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=9.5, fontweight="bold", color="black", zorder=3)
        return rect

    def draw_arrow(x1, y1, x2, y2, label="", ls="-"):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.0, linestyle=ls),
            zorder=4
        )
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.2, label, ha="center", va="bottom", fontsize=7.5, color="black", zorder=5)

    # Stages 1 to 5
    draw_box(2, 26, 17, 14, "Stage 1: Ingestion", "JATS XML & PDF\nLayout Geometry Offset")
    draw_arrow(19, 33, 22, 33)

    draw_box(22, 26, 17, 14, "Stage 2: Parsing", "Discourse Segmenter\nSection Roles & Bounds")
    draw_arrow(39, 33, 42, 33)

    draw_box(42, 26, 17, 14, "Stage 3: Normalizer", "Controlled Vocabularies\nAcronyms & Synonyms")
    draw_arrow(59, 33, 62, 33)

    draw_box(62, 26, 17, 14, "Stage 4: Extraction", "Syntactic Causal Engine\nNegation & Polarity")
    draw_arrow(79, 33, 82, 33)

    draw_box(82, 26, 21, 14, "Stage 5: Verification", "Bounded Path Traversal\nConfidence Calibration")

    # Output box
    draw_box(82, 4, 21, 14, "Causal Graph Output", "Traceable Mechanism SCM\n100% Span Provenance", fill="#F1F5F9", edge="black", lw=1.2)
    draw_arrow(92.5, 26, 92.5, 18, "Resolved Claims")

    # Evidence Grounding Subsystem (Wide Lower Box)
    draw_box(2, 4, 77, 14, "Evidence Grounding Subsystem & Provenance Audit Contract",
             "Exact Character Index Spans [c_start, c_end] | Physical Page Numbers | Verbatim Quotes\nTerminal Phenotype Direction Invariant | Environmental Parameter Invariant",
             fill="#FFFFFF", edge="black", lw=1.1, ls="--")

    # Connectors between stages and grounding subsystem
    draw_arrow(10.5, 26, 10.5, 18)
    draw_arrow(30.5, 26, 30.5, 18)
    draw_arrow(50.5, 26, 50.5, 18)
    draw_arrow(70.5, 26, 70.5, 18)
    draw_arrow(79, 11, 82, 11, "Verified")

    ax.set_title("EVRYN System Architecture: Modular End-to-End Multi-Page Causal Pipeline",
                 fontsize=11, fontweight="bold", pad=8)
    save_fig(fig, "fig1_system_architecture")


def generate_fig2_extraction_workflow():
    """Figure 2: Relation Extraction Workflow (Clear processing flow)."""
    fig, ax = plt.subplots(figsize=(10.5, 4.4), dpi=300)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 44)
    ax.axis("off")

    def draw_box(x, y, w, h, title, subtitle="", fill="#FFFFFF", edge="black", lw=1.0, ls="-"):
        rect = patches.Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge, linewidth=lw, linestyle=ls, zorder=2)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w / 2, y + h * 0.65, title, ha="center", va="center", fontsize=9, fontweight="bold", color="black", zorder=3)
            ax.text(x + w / 2, y + h * 0.32, subtitle, ha="center", va="center", fontsize=7.5, color="#222222", zorder=3)
        else:
            ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=9, fontweight="bold", color="black", zorder=3)

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.0),
            zorder=4
        )
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.2, label, ha="center", va="bottom", fontsize=7.5, color="black", zorder=5)

    # Left to right processing flow
    draw_box(2, 24, 21, 15, "1. Candidate Generation", "Sentence-Level Entities\nLocal Syntactic Pairs")
    draw_arrow(23, 31.5, 27, 31.5)

    draw_box(27, 24, 23, 15, "2. Syntactic Validation", "Active/Passive Verbs\nNegation Classification\nUncertainty Scoring")
    draw_arrow(50, 31.5, 54, 31.5)

    draw_box(54, 24, 23, 15, "3. Context Resolution", "Demonstrative Anaphora\nAbbreviation Stitching\nDiscourse Connectives")
    draw_arrow(77, 31.5, 81, 31.5)

    draw_box(81, 24, 22, 15, "4. Multi-Page Linking", "2-Hop Transitive Search\nSemantic Gating\nCycle & Decay Pruning")

    # Lower Filter and Grounding Layer
    draw_box(2, 5, 48, 13, "Strict False-Positive Controls",
             "Terminal Phenotype Invariant (Virulence cannot cause upstream genes)\nEnvironmental Parameter Invariant (Temperature/pH cannot be regulated)\nPassive Genetic Complementation Invariant",
             fill="#F8FAFC", edge="black", lw=1.0, ls="-")

    draw_box(54, 5, 49, 13, "5. Provenance & Calibration",
             "Dual-Sentence Evidence Tracking [S_causal, S_entity]\nCalibrated Confidence Score k in [0, 1]\nExact Char Spans & Verbatim Quotes",
             fill="#F1F5F9", edge="black", lw=1.1)

    draw_arrow(26, 24, 26, 18, "Direction Check")
    draw_arrow(65.5, 24, 65.5, 18, "Dual Spans")
    draw_arrow(92, 24, 92, 18, "Path Traversal")

    ax.set_title("EVRYN Relation Extraction Workflow: Candidate Generation to Grounded Attribution",
                 fontsize=11, fontweight="bold", pad=8)
    save_fig(fig, "fig2_extraction_workflow")


def generate_fig3_evidence_direction():
    """Figure 3: Evidence Grounding and Direction Diagram."""
    fig, ax = plt.subplots(figsize=(10.5, 4.4), dpi=300)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 44)
    ax.axis("off")

    def draw_box(x, y, w, h, title, subtitle="", fill="#FFFFFF", edge="black", lw=1.0, ls="-"):
        rect = patches.Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge, linewidth=lw, linestyle=ls, zorder=2)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w / 2, y + h * 0.65, title, ha="center", va="center", fontsize=9, fontweight="bold", color="black", zorder=3)
            ax.text(x + w / 2, y + h * 0.32, subtitle, ha="center", va="center", fontsize=7.5, color="#222222", zorder=3)
        else:
            ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=9, fontweight="bold", color="black", zorder=3)

    # Top: Cause and Effect with explicit directed relation
    draw_box(6, 27, 24, 12, "Cause Entity (C)", "Canonical: PmrB\nMention: PmrB sensor kinase\nPhysical Page: Page 2", fill="#F8FAFC", edge="black", lw=1.2)
    draw_box(74, 27, 25, 12, "Effect Entity (E)", "Canonical: PmrA\nMention: response regulator\nPhysical Page: Page 3", fill="#F8FAFC", edge="black", lw=1.2)

    # Directed Causal Edge
    ax.annotate(
        "", xy=(74, 33), xytext=(30, 33),
        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5),
        zorder=4
    )
    ax.text(52, 34.5, "RELATION: DIRECT_CAUSE (+)\nDirection: FORWARD | Confidence: 0.95",
            ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="black", zorder=5)

    # Middle: Verbatim Evidence Quote
    quote_text = "\"Acid pH activates the PmrA/PmrB system by promoting PmrB-mediated phosphorylation of PmrA.\""
    draw_box(6, 12, 93, 11, "Primary Evidence Sentence (S_causal)",
             f"{quote_text}\nLocation: Section: RESULTS | Paragraph: 14 | Sentence ID: PMC1804205_s42 | Char Spans: [1420--1512]",
             fill="#FFFFFF", edge="black", lw=1.0)

    # Bottom: Contrast between Direct vs Context-Resolved vs Transitive
    draw_box(6, 1, 29, 9, "Direct Assertion", "C and E co-occur in S_causal\nSyntactic dependency trigger\nConfidence: 0.90--0.98", fill="#F8FAFC", edge="black")
    draw_box(38, 1, 29, 9, "Context-Resolved Candidate", "Span across S_k -> S_k+1\nDemonstrative pronoun bridge\nDual Provenance: [S_c, S_e]", fill="#FFFFFF", edge="black")
    draw_box(70, 1, 29, 9, "Multi-Page Transitive Link", "Path: A -> B (p.2) -> C (p.5)\nPhysical separation >= 1 page\nConfidence decay applied", fill="#F8FAFC", edge="black")

    ax.set_title("EVRYN Evidence Provenance Contract: Dual-Span Grounding and Direction Fidelity",
                 fontsize=11, fontweight="bold", pad=8)
    save_fig(fig, "fig3_evidence_direction")


def generate_fig4_evaluation_workflow():
    """Figure 4: Evaluation Workflow & Strict Split Isolation Boundary."""
    fig, ax = plt.subplots(figsize=(10.5, 4.6), dpi=300)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 46)
    ax.axis("off")

    def draw_box(x, y, w, h, title, subtitle="", fill="#FFFFFF", edge="black", lw=1.0, ls="-"):
        rect = patches.Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge, linewidth=lw, linestyle=ls, zorder=2)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w / 2, y + h * 0.65, title, ha="center", va="center", fontsize=9, fontweight="bold", color="black", zorder=3)
            ax.text(x + w / 2, y + h * 0.32, subtitle, ha="center", va="center", fontsize=7.5, color="#222222", zorder=3)
        else:
            ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=9, fontweight="bold", color="black", zorder=3)

    # Development & Tuning Split (Unshaded Left Box)
    rect_dev = patches.Rectangle((2, 18), 44, 25, facecolor="#F8FAFC", edgecolor="black", linewidth=1.0)
    ax.add_patch(rect_dev)
    ax.text(24, 40.5, "DEVELOPMENT & TUNING ZONE (Permitted Tuning)", ha="center", va="center", fontsize=9, fontweight="bold")

    draw_box(4, 20, 19, 17, "Train Split (4 Papers)", "PMC2651894--PMC2774163\nGrammar Discovery\nZero Test Access", fill="white")
    draw_box(25, 20, 19, 17, "Dev Split (8 Papers)", "PMC1804205--PMC2430206\nError Diagnosis & Census\nHyperparameter Tuning", fill="white")

    # Double-line strict split isolation boundary
    ax.plot([49.5, 49.5], [2, 44], color="black", linewidth=1.5, linestyle="--", zorder=5)
    ax.plot([51.5, 51.5], [2, 44], color="black", linewidth=1.5, linestyle="--", zorder=5)
    ax.text(50.5, 23, "STRICT ZERO-LEAKAGE RELEASE GATE\n(Code & Hyperparameters Frozen Prior to Evaluation)",
            ha="center", va="center", rotation=90, fontsize=8, fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.4", fc="white", ec="black", lw=0.8), zorder=6)

    # Confirmatory & Generalization Zone (Right Box)
    rect_test = patches.Rectangle((55, 18), 48, 25, facecolor="#F1F5F9", edgecolor="black", linewidth=1.2)
    ax.add_patch(rect_test)
    ax.text(79, 40.5, "CONFIRMATORY EVALUATION ZONE (Strictly Blind)", ha="center", va="center", fontsize=9, fontweight="bold")

    draw_box(57, 20, 21, 17, "Locked Test (4 Papers)", "PMC2565068--PMC2639726\nConfirmatory Check\nFrozen Baseline Checkpoint", fill="white")
    draw_box(80, 20, 21, 17, "External Gen (4 Papers)", "PMC2816692--PMC2885601\nGenuinely Unseen Biology\nZero Prior Exposure", fill="white")

    # Lower benchmark audit box
    draw_box(2, 3, 101, 12, "Benchmark Integrity & Annotation Audit Gate",
             "Benchmark V1 (Raw / Unaligned BioCause; includes documented PMC2816692 Anthrax LF vs Salmonella SrcA mismatch)\n"
             "Benchmark V2 (Authenticated Domain-Aligned Ground Truth; 100% Provenance Coverage Verified Across All 20 Papers)",
             fill="#FFFFFF", edge="black", lw=1.1)

    ax.set_title("EVRYN 20-Paper Benchmark Partition and Strict Zero-Leakage Evaluation Protocol",
                 fontsize=11, fontweight="bold", pad=8)
    save_fig(fig, "fig4_evaluation_workflow")


def generate_fig5_error_analysis():
    """Figure 5: Error Analysis Taxonomy & False Negative / False Positive Breakdown."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.4), dpi=300)

    # Left: False Negatives Taxonomy (48 Total)
    categories = [
        "Discourse Claims\n(Cross-Sentence)",
        "Relation Trigger\n(Lexical/Syntactic)",
    ]
    counts_fn = [28, 20]
    pcts_fn = [28 / 48 * 100, 20 / 48 * 100]

    bars1 = ax1.bar(categories, counts_fn, color=["#334155", "#64748B"], edgecolor="black", width=0.45, linewidth=0.9)
    ax1.set_ylabel("False Negative Count (out of 48)", fontweight="bold", fontsize=9.5)
    ax1.set_title("False Negative Census (48 FNs)", fontweight="bold", fontsize=10.5, pad=10)
    ax1.set_ylim(0, 35)
    ax1.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")

    for bar, count, pct in zip(bars1, counts_fn, pcts_fn):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                 f"{count} ({pct:.1f}%)", ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Sub-breakdown annotation for discourse claims
    ax1.text(0, 14, "Sub-breakdown of 28 Discourse FNs:\n• Lexical/Synonym Gap: 13 (46.4%)\n• Multi-Section Synthesis: 8 (28.6%)\n• Demonstrative Anaphora: 5 (17.9%)\n• Sentence Boundary Split: 2 (7.1%)",
             ha="center", va="center", fontsize=7.5, color="white",
             bbox=dict(boxstyle="square,pad=0.3", fc="#1E293B", ec="black", lw=0.8))

    # Right: False Positives Breakdown (104 Total)
    fp_cats = [
        "Neighboring\nSpurious Pairs",
        "Passive Genetic\nComplementation",
        "Terminal Phenotype\nReversals",
        "Spurious Hub\nTransitive Leaps",
    ]
    counts_fp = [62, 18, 14, 10]
    bars2 = ax2.bar(fp_cats, counts_fp, color=["#475569", "#64748B", "#94A3B8", "#CBD5E1"], edgecolor="black", width=0.55, linewidth=0.9)
    ax2.set_ylabel("False Positive Count (out of 104)", fontweight="bold", fontsize=9.5)
    ax2.set_title("False Positive Taxonomy (104 FPs in V2)", fontweight="bold", fontsize=10.5, pad=10)
    ax2.set_ylim(0, 75)
    ax2.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")

    for bar, count in zip(bars2, counts_fp):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                 f"{count}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    fig.suptitle("EVRYN Error Analysis: Systematic Census of Remaining Extraction Failures",
                 fontsize=11.5, fontweight="bold", y=1.02)
    plt.tight_layout()
    save_fig(fig, "fig5_error_analysis")


def generate_fig6_results_progression():
    """Figure 6: Verified Results & Progression Across Evaluation Splits (V1 vs V2)."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(11.5, 4.2), dpi=300)

    splits = ["Train\n(4 papers)", "Dev\n(8 papers)", "Locked\n(4 papers)", "External V1\n(4 papers)", "External V2\n(4 papers)"]

    # Direct F1
    direct_f1 = [0.3521, 0.5076, 0.3429, 0.2380, 0.3289]
    direct_err_low = [0.3521 - 0.2549, 0.5076 - 0.4625, 0.3429 - 0.1537, 0.2380 - 0.0769, 0.3289 - 0.2409]
    direct_err_high = [0.4583 - 0.3521, 0.5584 - 0.5076, 0.5625 - 0.3429, 0.3833 - 0.2380, 0.4103 - 0.3289]

    # Cross-Page F1
    cross_f1 = [0.0833, 0.3864, 0.2002, 0.1667, 0.2667]
    cross_err_low = [0.0833 - 0.0, 0.3864 - 0.2233, 0.2002 - 0.0714, 0.1667 - 0.0, 0.2667 - 0.0833]
    cross_err_high = [0.25 - 0.0833, 0.5392 - 0.3864, 0.3095 - 0.2002, 0.3333 - 0.1667, 0.3833 - 0.2667]

    # Structural Match
    match_ratio = [0.1543, 0.3162, 0.1733, 0.1243, 0.1819]

    x = np.arange(len(splits))
    colors = ["#475569", "#1E293B", "#334155", "#94A3B8", "#0F172A"]

    # Panel 1: Direct F1
    bars1 = ax1.bar(x, direct_f1, yerr=[direct_err_low, direct_err_high], capsize=4,
                    color=colors, edgecolor="black", width=0.55, linewidth=0.9, error_kw=dict(lw=0.9, capthick=0.9))
    ax1.set_ylabel("Direct Causal F1", fontweight="bold", fontsize=9.5)
    ax1.set_title("Direct Relation F1 (95% CI)", fontweight="bold", fontsize=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(splits, fontsize=8)
    ax1.set_ylim(0, 0.70)
    ax1.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")
    for bar, val in zip(bars1, direct_f1):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.04, f"{val:.4f}",
                 ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    # Panel 2: Cross-Page F1
    bars2 = ax2.bar(x, cross_f1, yerr=[cross_err_low, cross_err_high], capsize=4,
                    color=colors, edgecolor="black", width=0.55, linewidth=0.9, error_kw=dict(lw=0.9, capthick=0.9))
    ax2.set_ylabel("Cross-Page Causal F1", fontweight="bold", fontsize=9.5)
    ax2.set_title("Cross-Page Relation F1 (95% CI)", fontweight="bold", fontsize=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(splits, fontsize=8)
    ax2.set_ylim(0, 0.65)
    ax2.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")
    for bar, val in zip(bars2, cross_f1):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.04, f"{val:.4f}",
                 ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    # Panel 3: Exact Structural Match
    bars3 = ax3.bar(x, match_ratio, color=colors, edgecolor="black", width=0.55, linewidth=0.9)
    ax3.set_ylabel("Exact Structural Match Ratio", fontweight="bold", fontsize=9.5)
    ax3.set_title("Exact Structural Match Ratio", fontweight="bold", fontsize=10)
    ax3.set_xticks(x)
    ax3.set_xticklabels(splits, fontsize=8)
    ax3.set_ylim(0, 0.45)
    ax3.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")
    for bar, val in zip(bars3, match_ratio):
        ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.015, f"{val:.4f}",
                 ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    fig.suptitle("EVRYN Phase 1 Verified Benchmark Metrics Across Isolated Splits",
                 fontsize=11.5, fontweight="bold", y=1.02)
    plt.tight_layout()
    save_fig(fig, "fig6_results_progression")


def main():
    print("Generating 6 core publication-quality academic figures...")
    generate_fig1_system_architecture()
    generate_fig2_extraction_workflow()
    generate_fig3_evidence_direction()
    generate_fig4_evaluation_workflow()
    generate_fig5_error_analysis()
    generate_fig6_results_progression()
    print("All 6 figures successfully generated in PDF and PNG vector/raster formats!")

if __name__ == "__main__":
    main()
