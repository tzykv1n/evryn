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
            if x1 == x2:  # Vertical arrow
                ax.text(x1 + 1.4, (y1 + y2) / 2, label, ha="left", va="center",
                        fontsize=9.0, fontweight="bold", color="black", zorder=5,
                        bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
            elif y1 == y2:  # Horizontal arrow
                ax.text((x1 + x2) / 2, y1 + 1.8, label, ha="center", va="bottom",
                        fontsize=9.0, fontweight="bold", color="black", zorder=5,
                        bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
            else:
                ax.text((x1 + x2) / 2, (y1 + y2) / 2, label, ha="center", va="center",
                        fontsize=9.0, fontweight="bold", color="black", zorder=5,
                        bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))

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

    # Evidence Grounding Subsystem (Wide Lower Box: x=2, w=92 -> right edge x=94)
    draw_box(2, 4, 92, 20, "Evidence Grounding Subsystem & Provenance Audit Contract",
             "Exact Character Index Spans [c_start, c_end] | Physical Page Numbers | Verbatim Quotes\n"
             "Terminal Phenotype Direction Invariant | Environmental Parameter Invariant\n"
             "Homology Non-Causal Method Gating | Relative Clause Barrier",
             fill="#FFFFFF", edge="black", lw=1.3, ls="--")

    # Connectors between stages and grounding subsystem
    draw_arrow(13, 33, 13, 24)
    draw_arrow(38, 33, 38, 24)
    draw_arrow(63, 33, 63, 24)
    draw_arrow(88, 33, 88, 24)
    draw_arrow(94, 14, 102, 14)
    ax.text(98, 16.5, "Verified", ha="center", va="bottom", fontsize=8.6, fontweight="bold", color="black", zorder=6,
            bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))

    ax.set_title("EVRYN System Architecture: Modular End-to-End Multi-Page Causal Pipeline",
                 fontsize=13.5, fontweight="bold", pad=12)
    save_fig(fig, "fig1_system_architecture")


def generate_fig2_extraction_workflow():
    """Figure 2: Relation Extraction Workflow & Progress Architecture (Enlarged, high-legibility processing flow)."""
    import textwrap
    fig, ax = plt.subplots(figsize=(15.0, 9.0), dpi=300)
    ax.set_xlim(0, 150)
    ax.set_ylim(0, 90)
    ax.axis("off")

    def draw_stage_box(x, y, w, h, stage_num, title, badge, bullets, fill="#FFFFFF", edge="#0F172A", lw=1.3):
        # Main container
        rect = patches.Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge, linewidth=lw, zorder=2)
        ax.add_patch(rect)
        # Distinct header band
        hbar = patches.Rectangle((x, y + h - 6.5), w, 6.5, facecolor="#F1F5F9", edgecolor=edge, linewidth=lw, zorder=2)
        ax.add_patch(hbar)
        # Stage title (left-aligned)
        ax.text(x + 2.0, y + h - 3.25, f"{stage_num}. {title}", ha="left", va="center", fontsize=10.5, fontweight="bold", color="#0F172A", zorder=4)
        # Badge (right-aligned, no overlap)
        badge_col = "#16A34A" if "DELIVERED" in badge or "100%" in badge else ("#D97706" if "PROGRESS" in badge else "#2563EB")
        ax.text(x + w - 2.0, y + h - 3.25, badge, ha="right", va="center", fontsize=7.8, fontweight="bold", color=badge_col, zorder=4,
                bbox=dict(boxstyle="square,pad=0.2", fc="white", ec=badge_col, lw=0.8))
        # Bullet list inside
        text_y = y + h - 9.5
        for b in bullets:
            ax.text(x + 2.5, text_y, f"• {b}", ha="left", va="top", fontsize=8.6, color="#1E293B", zorder=4)
            text_y -= 4.6

    def draw_arrow(x1, y1, x2, y2, label="", col="#0F172A"):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color=col, lw=1.5),
            zorder=5
        )
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, label, ha="center", va="center",
                    fontsize=8.2, fontweight="bold", color="#0F172A", zorder=6,
                    bbox=dict(boxstyle="square,pad=0.25", fc="white", ec="#CBD5E1", lw=0.8))

    # Upper Stages (y=52, h=27)
    draw_stage_box(4, 52, 32, 27, "1", "Candidate Gen", "DELIVERED",
                   ["Bio-Entity Extraction", "Local Intra-Sentence Pairs", "Paragraph & Section Bounds", "Pre-flight Quality Gating"])

    draw_stage_box(40, 52, 32, 27, "2", "Syntactic Validation", "DELIVERED",
                   ["Forward Causal Triggers", "Passive Inversion Rules", "Agent-Nominal Patterns", "Strict Negation Parsing"])

    draw_stage_box(76, 52, 32, 27, "3", "Context Resolution", "DELIVERED",
                   ["Demonstrative Anaphora", "Acronym Normalization", "Discourse Connectives", "Dual-Sentence Alignment"])

    draw_stage_box(112, 52, 34, 27, "4", "Multi-Page Linking", "IN PROGRESS",
                   ["Bounded Multi-Hop (<=2)", "Semantic Gating Gate", "Cross-Page Graph Closure", "Distance Decay (d >= 1)"])

    # Flow arrows between upper stages
    draw_arrow(36, 65.5, 40, 65.5)
    draw_arrow(72, 65.5, 76, 65.5)
    draw_arrow(108, 65.5, 112, 65.5)

    # Lower Row Subsystems (y=6, h=33)
    # Subsystem 1: Invariants
    rect1 = patches.Rectangle((4, 6), 68, 33, facecolor="#F8FAFC", edgecolor="#0F172A", linewidth=1.3, zorder=2)
    ax.add_patch(rect1)
    hbar1 = patches.Rectangle((4, 32.5), 68, 6.5, facecolor="#F1F5F9", edgecolor="#0F172A", linewidth=1.3, zorder=2)
    ax.add_patch(hbar1)
    ax.text(6.0, 35.75, "Strict False-Positive Controls & Invariants", ha="left", va="center", fontsize=11, fontweight="bold", color="#0F172A", zorder=4)
    ax.text(70.0, 35.75, "ACTIVE INVARIANTS", ha="right", va="center", fontsize=8.0, fontweight="bold", color="#2563EB", zorder=4,
            bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="#2563EB", lw=0.8))

    bullets_inv = [
        "Terminal Phenotype Invariant: Virulence and survival cannot cause upstream regulatory genes",
        "Environmental Parameter Invariant: Temperature and pH cannot be transcriptionally modulated",
        "Homology & Cloning Gating: Non-causal method statements and homologue analogies suppressed",
        "Relative Clause Boundary Barrier: Suppresses spurious cross-clause entity-trigger associations"
    ]
    ty = 30.0
    for b in bullets_inv:
        wrapped = textwrap.wrap(b, width=54)
        ax.text(6.5, ty, f"• {wrapped[0]}", ha="left", va="top", fontsize=8.4, color="#1E293B", zorder=4)
        if len(wrapped) > 1:
            ax.text(8.8, ty - 3.4, f"{wrapped[1]}", ha="left", va="top", fontsize=8.4, color="#475569", zorder=4)
        ty -= 6.2

    # Subsystem 2: Provenance & Verification
    rect2 = patches.Rectangle((76, 6), 70, 33, facecolor="#F8FAFC", edgecolor="#0F172A", linewidth=1.3, zorder=2)
    ax.add_patch(rect2)
    hbar2 = patches.Rectangle((76, 32.5), 70, 6.5, facecolor="#F1F5F9", edgecolor="#0F172A", linewidth=1.3, zorder=2)
    ax.add_patch(hbar2)
    ax.text(78.0, 35.75, "5. Provenance Grounding & Verification Engine", ha="left", va="center", fontsize=11, fontweight="bold", color="#0F172A", zorder=4)
    ax.text(144.0, 35.75, "VERIFIED (100%)", ha="right", va="center", fontsize=8.0, fontweight="bold", color="#16A34A", zorder=4,
            bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="#16A34A", lw=0.8))

    bullets_ver = [
        "Dual-Sentence Evidence Tracking: Verbatim [S_causal, S_entity] bindings with zero hallucination",
        "Calibrated Confidence Metric: Empirical Platt-scaled posterior precision score in [0.0, 1.0]",
        "Full Text Auditability: Exact character indices [c_start, c_end] and physical page numbers",
        "Strict Zero-Leakage Protocol: Benchmark isolation verified across all 20 PMC-OA papers"
    ]
    ty = 30.0
    for b in bullets_ver:
        wrapped = textwrap.wrap(b, width=54)
        ax.text(78.5, ty, f"• {wrapped[0]}", ha="left", va="top", fontsize=8.4, color="#1E293B", zorder=4)
        if len(wrapped) > 1:
            ax.text(80.8, ty - 3.4, f"{wrapped[1]}", ha="left", va="top", fontsize=8.4, color="#475569", zorder=4)
        ty -= 6.2

    # Vertical connectors between rows (gap between y=39 and y=52 is 13 units!)
    draw_arrow(56, 52, 56, 39, "Direction Check")
    draw_arrow(92, 52, 92, 39, "Dual Spans [Sc, Se]")
    draw_arrow(128, 52, 128, 39, "Transitive Paths")

    # Horizontal connector between invariants and verification
    draw_arrow(72, 22.5, 76, 22.5, "Gated")

    ax.set_title("EVRYN Relation Extraction Workflow & Modular Progress Architecture",
                 fontsize=14.0, fontweight="bold", pad=12)
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
    """Figure 5: Error Analysis Taxonomy & False Negative / False Positive Breakdown (Audited 29 FN, 76 FP)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.6), dpi=300)

    # Left: False Negatives Taxonomy across 20-Paper Benchmark (29 Total FNs in Benchmark V2)
    categories_fn = [
        "Multi-Complex\nAssembly",
        "Implicit\nPromoters",
        "Multi-Hop\nHypoxia",
        "Negative\nFeedback"
    ]
    counts_fn = [10, 9, 6, 4]
    pcts_fn = [c / sum(counts_fn) * 100 for c in counts_fn]
    colors_fn = ["#0F172A", "#1E293B", "#334155", "#475569"]

    bars1 = ax1.bar(categories_fn, counts_fn, color=colors_fn, edgecolor="black", width=0.52, linewidth=1.1)
    ax1.set_ylabel("False Negative Count", fontweight="bold", fontsize=11.5)
    ax1.set_title("False Negative Census (29 FNs in Benchmark V2)", fontweight="bold", fontsize=12.5, pad=12)
    ax1.set_ylim(0, 14)
    ax1.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")

    for bar, count, pct in zip(bars1, counts_fn, pcts_fn):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.35,
                 f"{count} ({pct:.1f}%)", ha="center", va="bottom", fontsize=9.8, fontweight="bold")

    # Sub-breakdown annotation
    ax1.text(0.95, 0.95, "FN Failure Census (29 Cases):\n• Multi-Complex Assembly: 34.5%\n• Implicit Promoters: 31.0%\n• Multi-Hop Hypoxia: 20.7%\n• Negative Feedback: 13.8%",
             transform=ax1.transAxes, ha="right", va="top", fontsize=9.0, color="white",
             bbox=dict(boxstyle="square,pad=0.4", fc="#0F172A", ec="black", lw=1.0))

    # Right: False Positives Breakdown (76 Total FPs in Benchmark V2)
    categories_fp = [
        "Experimental\nControls",
        "Co-occurring\nRegulators",
        "Assay\nReagents",
        "Broad\nPhenotypes"
    ]
    counts_fp = [28, 24, 14, 10]
    pcts_fp = [c / sum(counts_fp) * 100 for c in counts_fp]
    colors_fp = ["#1E293B", "#334155", "#475569", "#64748B"]

    bars2 = ax2.bar(categories_fp, counts_fp, color=colors_fp, edgecolor="black", width=0.52, linewidth=1.1)
    ax2.set_ylabel("False Positive Count", fontweight="bold", fontsize=11.5)
    ax2.set_title("False Positive Taxonomy (76 FPs in Benchmark V2)", fontweight="bold", fontsize=12.5, pad=12)
    ax2.set_ylim(0, 36)
    ax2.grid(axis="y", linestyle="--", alpha=0.6, color="#CCCCCC")

    for bar, count, pct in zip(bars2, counts_fp, pcts_fp):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                 f"{count} ({pct:.1f}%)", ha="center", va="bottom", fontsize=9.8, fontweight="bold")

    fig.suptitle("EVRYN Error Analysis: Systematic Census of Remaining Extraction Failures",
                 fontsize=13.8, fontweight="bold", y=1.01)
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


def generate_gantt_schedule():
    """Gantt Milestone Schedule: Publication-quality implementation roadmap (Nov 2026 – Apr 2027)."""
    fig, ax = plt.subplots(figsize=(15.2, 8.0), dpi=300)

    # Set up grid
    month_names = ["Nov 2026", "Dec 2026", "Jan 2027", "Feb 2027", "Mar 2027", "Apr 2027"]
    for i in range(6):
        bg_color = "#FFFFFF" if i % 2 == 0 else "#F8FAFC"
        ax.axvspan(i, i + 1, facecolor=bg_color, alpha=1.0, zorder=0)
        ax.axvline(i, color="#CBD5E1", linewidth=1.0, linestyle="-", zorder=1)
    ax.axvline(6, color="#CBD5E1", linewidth=1.0, linestyle="-", zorder=1)

    tasks = [
        # (row, display_name, start, end, status, badge)
        (9, "1. JATS XML & PDF Ingestion Engine", 0.0, 0.75, "DELIVERED", "Delivered (100%)"),
        (8, "2. Syntactic Trigger & Polarity Engine", 0.0, 0.85, "DELIVERED", "Delivered (100%)"),
        (7, "3. 20-Paper Benchmark & Provenance Audit", 0.0, 0.95, "DELIVERED", "Delivered (100%)"),
        (6, "4. M.Tech Phase 1 Monograph & Presentation", 0.0, 1.0, "DELIVERED", "Delivered (100%)"),

        (4, "5. Conformal Semantic Gating (PubMedBERT)", 1.0, 2.0, "IN_PROGRESS", "In Progress (Active)"),
        (3, "6. 25-Yr Longitudinal PMC-OA Corpus Graph", 2.0, 3.0, "PLANNED", "Planned (Jan)"),
        (2, "7. Continual Mechanism Adaptation (FLUX)", 3.0, 4.0, "PLANNED", "Planned (Feb)"),

        (1, "8. SCM-Forecaster Discovery Link Prediction", 4.0, 5.0, "PLANNED", "Planned (Mar)"),
        (0, "9. Final M.Tech Thesis & Code Release", 5.0, 6.0, "PLANNED", "Planned (Apr)"),
    ]

    color_map = {
        "DELIVERED": ("#0F172A", "white"),    # Dark Navy
        "IN_PROGRESS": ("#0D9488", "white"),  # Teal
        "PLANNED": ("#475569", "white"),      # Slate
    }

    for row, name, start, end, status, badge in tasks:
        bar_fc, text_fc = color_map[status]
        bar = patches.Rectangle((start, row - 0.26), end - start, 0.52,
                                facecolor=bar_fc, edgecolor="black", linewidth=1.1, zorder=3)
        ax.add_patch(bar)
        bar_center_x = (start + end) / 2
        ax.text(bar_center_x, row, badge, ha="center", va="center",
                fontsize=9.0, fontweight="bold", color=text_fc, zorder=4)

    # Y-axis task labels
    ax.set_yticks([t[0] for t in tasks])
    ax.set_yticklabels([t[1] for t in tasks], fontsize=11.0, fontweight="bold", color="#0F172A")
    ax.tick_params(axis="y", which="both", length=0, pad=10)

    # Section category separator lines and labels
    ax.axhline(5.2, color="#0F172A", linewidth=1.1, linestyle="--", alpha=0.4, zorder=2)
    ax.axhline(1.5, color="#0D9488", linewidth=1.1, linestyle="--", alpha=0.4, zorder=2)

    # Pure data coordinates
    ax.text(0.05, 9.65, "PHASE 1: CONSOLIDATION & EVIDENCE GROUNDING",
            fontsize=9.8, fontweight="bold", color="#0F172A", zorder=5)
    ax.text(1.05, 4.65, "PHASE 2: LONGITUDINAL CORPUS TRANSFER & CONTINUAL ADAPTATION",
            fontsize=9.8, fontweight="bold", color="#0D9488", zorder=5)
    ax.text(4.05, 1.65, "PHASE 3: PROSPECTIVE DISCOVERY PREDICTION & FINAL THESIS DEFENSE",
            fontsize=9.8, fontweight="bold", color="#2563EB", zorder=5)

    # Milestones
    milestones = [
        (1.0, 6.0, "Milestone M1 (Nov 30)\nPhase 1 Defense & Benchmark Freeze", "#D97706"),
        (4.0, 2.0, "Milestone M2 (Feb 28)\nLongitudinal Transfer & Gating Audit", "#D97706"),
        (6.0, 0.0, "Milestone M3 (Apr 30)\nFinal M.Tech Thesis & Degree Defense", "#16A34A"),
    ]

    for mx, my, mtitle, mcolor in milestones:
        ax.plot(mx, my, marker="D", markersize=12, color=mcolor, markeredgecolor="black", markeredgewidth=1.2, zorder=5)
        ax.axvline(mx, color=mcolor, linewidth=1.3, linestyle=":", alpha=0.8, zorder=2)
        offset_x = -0.05 if mx >= 5.5 else 0.05
        ha = "right" if mx >= 5.5 else "left"
        ax.text(mx + offset_x, my + 0.45, mtitle, ha=ha, va="bottom", fontsize=9.0, fontweight="bold",
                color="#0F172A", zorder=6,
                bbox=dict(boxstyle="square,pad=0.25", fc="white", ec=mcolor, lw=1.0))

    # X-axis
    ax.set_xlim(0, 6.0)
    ax.set_ylim(-0.8, 10.2)
    ax.set_xticks([i + 0.5 for i in range(6)])
    ax.set_xticklabels(month_names, fontsize=12.0, fontweight="bold")
    ax.tick_params(axis="x", which="both", length=0, pad=10)

    ax.set_title("EVRYN Research Implementation Roadmap & Gantt Milestone Schedule (Nov 2026 – Apr 2027)",
                 fontsize=13.5, fontweight="bold", pad=16)

    # Legend
    leg_handles = [
        patches.Patch(facecolor="#0F172A", edgecolor="black", label="Completed Work (Phase 1 Delivered 100%)"),
        patches.Patch(facecolor="#0D9488", edgecolor="black", label="Work in Progress (Phase 2 Active Gating)"),
        patches.Patch(facecolor="#475569", edgecolor="black", label="Planned Work (Phase 2–3 Scaling & Discovery)"),
        matplotlib.lines.Line2D([0], [0], marker="D", color="w", markerfacecolor="#D97706", markeredgecolor="black", markersize=9, label="Phase Milestone (M1, M2, M3)"),
    ]
    ax.legend(handles=leg_handles, loc="upper right", bbox_to_anchor=(1.0, -0.08), ncol=4, frameon=True, fontsize=9.5)

    fig.subplots_adjust(left=0.30, right=0.96, top=0.92, bottom=0.12)
    save_fig(fig, "gantt_schedule")


def main():
    print("Generating redesigned, large-format publication-quality academic figures...")
    generate_fig1_system_architecture()
    generate_fig2_extraction_workflow()
    generate_fig3_evidence_direction()
    generate_fig4_evaluation_workflow()
    generate_fig5_error_analysis()
    generate_fig6_results_progression()
    print("All 6 publication figures successfully regenerated in PDF and PNG formats!")


if __name__ == "__main__":
    main()
