#!/usr/bin/env python3
"""
Generate publication-quality, printer-friendly, light-academic figures
for the EVRYN Research Monograph and Presentation.

Mandatory rules enforced:
- Light, restrained academic color palette:
  - Muted blue (#2563EB, #3B82F6) for primary structures and headings
  - Soft teal (#0D9488, #14B8A6) for supporting elements and delivered components
  - Light blue-grey backgrounds (#F8FAFC, #F1F5F9) for grouped content
  - Muted amber (#D97706) for in-progress elements, distinctions, and cautions
  - Dark charcoal (#0F172A, #1E293B) for high-contrast legible text
  - White (#FFFFFF) canvas and card faces
- No solid dark bar fills, heavy black grids, or inverted black boxes
- Strictly square corners (no rounded corners anywhere)
- Large, readable typography (titles 13-14pt bold, labels 10.5-12pt, data 9.5-11pt)
- Generous canvas dimensions and zero overlapping text or connectors
- Export both vector PDF and high-res 300 DPI PNG
"""

import os
import textwrap
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
    "axes.labelsize": 11.5,
    "axes.titlesize": 13,
    "xtick.labelsize": 10.5,
    "ytick.labelsize": 10.5,
    "legend.fontsize": 10.5,
    "figure.titlesize": 14,
    "axes.linewidth": 1.0,
    "grid.linewidth": 0.6,
    "lines.linewidth": 1.3,
    "patch.linewidth": 1.0,
})


def save_fig(fig, base_name):
    for d in OUTPUT_DIRS:
        pdf_path = os.path.join(d, f"{base_name}.pdf")
        png_path = os.path.join(d, f"{base_name}.png")
        fig.savefig(pdf_path, bbox_inches="tight", dpi=300)
        fig.savefig(png_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved {base_name}.pdf and {base_name}.png to all output directories.")


# ==============================================================================
# Figure 1.1: Three-Phase Research Scope & Demarcation
# ==============================================================================
def generate_fig0_research_scope():
    """Figure 1.1: Three-Phase Overarching Research Scope."""
    fig, ax = plt.subplots(figsize=(15.6, 8.2), dpi=300)
    ax.set_xlim(0, 156)
    ax.set_ylim(0, 82)
    ax.axis("off")

    def draw_phase_column(x, y, w, h, phase_num, title, badge, bullets, border_col, badge_col, bg_col="#FFFFFF"):
        # Outer container
        rect = patches.Rectangle((x, y), w, h, facecolor=bg_col, edgecolor=border_col, linewidth=1.4, zorder=2)
        ax.add_patch(rect)

        # Header bar
        hbar = patches.Rectangle((x, y + h - 8.5), w, 8.5, facecolor="#F1F5F9", edgecolor=border_col, linewidth=1.4, zorder=3)
        ax.add_patch(hbar)

        # Header text
        ax.text(x + 2.5, y + h - 2.8, f"PHASE {phase_num}", ha="left", va="center",
                fontsize=11.5, fontweight="bold", color=border_col, zorder=4)
        ax.text(x + 2.5, y + h - 6.0, title, ha="left", va="center",
                fontsize=9.2, fontweight="bold", color="#0F172A", zorder=4)

        # Badge
        ax.text(x + w - 2.5, y + h - 4.4, badge, ha="right", va="center",
                fontsize=8.0, fontweight="bold", color=badge_col, zorder=4,
                bbox=dict(boxstyle="square,pad=0.28", fc="white", ec=badge_col, lw=0.9))

        # Bullets
        ty = y + h - 12.0
        for b in bullets:
            wrapped = textwrap.wrap(b, width=40)
            ax.text(x + 3.0, ty, f"• {wrapped[0]}", ha="left", va="top",
                    fontsize=8.6, color="#0F172A", fontweight="normal", zorder=4)
            if len(wrapped) > 1:
                ax.text(x + 5.5, ty - 2.9, f"{wrapped[1]}", ha="left", va="top",
                        fontsize=8.4, color="#334155", zorder=4)
            ty -= 6.8

    # Three columns (x positions: 5, 55, 105; widths: 46 each)
    p1_bullets = [
        "Full-text PMC-OA JATS XML & PDF parsing with geometry",
        "Section discourse tagging & coordinate tracking",
        "Syntactic & agent-nominal causal trigger parsing",
        "Dual-sentence context resolution [Sc, Se]",
        "Bounded transitive multi-hop reasoning (<= 2 hops)",
        "Calibrated confidence verification & Platt scaling",
        "100% Provenance contract (Doc, page, offsets, quotes)",
        "20-Paper authentic PMC benchmark validation"
    ]
    draw_phase_column(5, 4, 46, 70, "1", "Multi-Page Causal Extraction",
                      "DELIVERED (Phase 1.14)", p1_bullets,
                      border_col="#0D9488", badge_col="#0D9488", bg_col="#F8FAFC")

    p2_bullets = [
        "Multi-document graph fusion across literature",
        "Cross-paper entity normalization & alias resolution",
        "25-Year longitudinal corpus trajectory tracking",
        "Causal mechanism drift & belief revision detection",
        "Continual SCM adaptation with zero forgetting",
        "Conformal semantic gating via PubMedBERT",
        "Empirical evaluation on temporal SCM streams",
        "Cross-study consensus & refutation modeling"
    ]
    draw_phase_column(55, 4, 46, 70, "2", "Corpus Transfer & Adaptation",
                      "IN PROGRESS", p2_bullets,
                      border_col="#2563EB", badge_col="#2563EB", bg_col="#FFFFFF")

    p3_bullets = [
        "Dynamic causal graph manifold representation",
        "Prospective emergent link forecasting",
        "Pre-publication hypothesis generation & ranking",
        "Multi-hop cross-domain mechanism completion",
        "Prospective validation on post-cutoff publications",
        "Biomedical discovery prioritization pipeline",
        "Comprehensive M.Tech defense monograph",
        "Reproducible open-source software release"
    ]
    draw_phase_column(105, 4, 46, 70, "3", "Prospective Discovery Prediction",
                      "PLANNED", p3_bullets,
                      border_col="#64748B", badge_col="#64748B", bg_col="#FFFFFF")

    # Connectors between phases
    def draw_phase_arrow(x1, x2, y, label):
        ax.annotate(
            "", xy=(x2, y), xytext=(x1, y),
            arrowprops=dict(arrowstyle="-|>", color="#0F172A", lw=1.6),
            zorder=5
        )
        ax.text((x1 + x2) / 2, y + 1.8, label, ha="center", va="bottom",
                fontsize=8.0, fontweight="bold", color="#0F172A", zorder=6,
                bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="#CBD5E1", lw=0.8))

    draw_phase_arrow(51, 55, 38, "Grounded\nGraphs")
    draw_phase_arrow(101, 105, 38, "Longitudinal\nCorpus")

    ax.set_title("EVRYN Overarching Three-Phase Research Scope & Monograph Demarcation",
                 fontsize=13.5, fontweight="bold", pad=12)
    save_fig(fig, "research_scope")
    save_fig(fig, "fig1_research_scope")


# ==============================================================================
# Figure 4.1: End-to-End System Architecture
# ==============================================================================
def generate_fig1_system_architecture():
    """Figure 4.1: End-to-End System Architecture (Light academic layout)."""
    fig, ax = plt.subplots(figsize=(13.6, 6.0), dpi=300)
    ax.set_xlim(0, 136)
    ax.set_ylim(0, 60)
    ax.axis("off")

    def draw_box(x, y, w, h, title, subtitle="", fill="#FFFFFF", edge="#0F172A", lw=1.2, ls="-"):
        rect = patches.Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge, linewidth=lw, linestyle=ls, zorder=2)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w / 2, y + h * 0.65, title, ha="center", va="center", fontsize=10.5, fontweight="bold", color="#0F172A", zorder=3)
            ax.text(x + w / 2, y + h * 0.30, subtitle, ha="center", va="center", fontsize=9.0, color="#334155", zorder=3)
        else:
            ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=10.5, fontweight="bold", color="#0F172A", zorder=3)
        return rect

    def draw_arrow(x1, y1, x2, y2, label="", ls="-", col="#0F172A"):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color=col, lw=1.4, linestyle=ls),
            zorder=4
        )
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, label, ha="center", va="center",
                    fontsize=8.5, fontweight="bold", color="#0F172A", zorder=5,
                    bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="#CBD5E1", lw=0.8))

    # Upper Stages 1 to 5
    draw_box(3, 34, 23, 19, "Stage 1: Ingestion", "PMC-OA JATS XML / PDF\nLayout Geometry Offset", fill="#F8FAFC", edge="#0D9488")
    draw_arrow(26, 43.5, 29, 43.5)

    draw_box(29, 34, 23, 19, "Stage 2: Parsing", "Discourse Segmenter\nSection Roles & Bounds", fill="#F8FAFC", edge="#0D9488")
    draw_arrow(52, 43.5, 55, 43.5)

    draw_box(55, 34, 23, 19, "Stage 3: Normalizer", "Controlled Vocabularies\nAcronyms & Synonyms", fill="#F8FAFC", edge="#0D9488")
    draw_arrow(78, 43.5, 81, 43.5)

    draw_box(81, 34, 23, 19, "Stage 4: Extraction", "Syntactic Causal Engine\nAgent-Nominals & Polarity", fill="#F8FAFC", edge="#2563EB")
    draw_arrow(104, 43.5, 107, 43.5)

    draw_box(107, 34, 26, 19, "Stage 5: Verification", "Bounded Path Traversal\nConfidence Calibration", fill="#F8FAFC", edge="#2563EB")

    # Lower Deck: Grounding Subsystem & Final Graph
    draw_box(3, 5, 98, 21, "Evidence Grounding Subsystem & Provenance Audit Contract",
             "Exact Character Index Spans [c_start, c_end] | Physical Page Numbers | Verbatim Source Quotes\n"
             "Terminal Phenotype Direction Invariant | Environmental Parameter Invariant\n"
             "Homology Non-Causal Method Gating | Relative Clause Barrier",
             fill="#FFFFFF", edge="#0D9488", lw=1.3, ls="--")

    draw_box(107, 5, 26, 21, "Causal Graph Output", "Traceable Mechanism SCM\n100% Span Provenance", fill="#F1F5F9", edge="#2563EB", lw=1.4)

    # Vertical connectors
    draw_arrow(14.5, 34, 14.5, 26)
    draw_arrow(40.5, 34, 40.5, 26)
    draw_arrow(66.5, 34, 66.5, 26)
    draw_arrow(92.5, 34, 92.5, 26)
    draw_arrow(101, 15.5, 107, 15.5, "Verified")
    draw_arrow(120, 34, 120, 26, "Resolved Claims")

    ax.set_title("EVRYN System Architecture: Modular End-to-End Multi-Page Causal Discovery Pipeline",
                 fontsize=13.5, fontweight="bold", pad=12)
    save_fig(fig, "fig1_system_architecture")


# ==============================================================================
# Figure 4.2: Relation Extraction Workflow & Progress Architecture
# ==============================================================================
def generate_fig2_extraction_workflow():
    """Figure 4.2: Multi-Stage Causal Extraction Workflow (Clean light academic layout)."""
    fig, ax = plt.subplots(figsize=(15.6, 11.2), dpi=300)
    ax.set_xlim(0, 156)
    ax.set_ylim(0, 112)
    ax.axis("off")

    def draw_stage_box(x, y, w, h, stage_num, title, badge, bullets, border_col="#0D9488", badge_col="#0D9488"):
        rect = patches.Rectangle((x, y), w, h, facecolor="#FFFFFF", edgecolor=border_col, linewidth=1.3, zorder=2)
        ax.add_patch(rect)
        hbar = patches.Rectangle((x, y + h - 9.0), w, 9.0, facecolor="#F1F5F9", edgecolor=border_col, linewidth=1.1, zorder=3)
        ax.add_patch(hbar)

        # Top line of header
        ax.text(x + 2.5, y + h - 3.2, f"STAGE {stage_num}", ha="left", va="center",
                fontsize=10.2, fontweight="bold", color=border_col, zorder=4)
        ax.text(x + w - 2.5, y + h - 3.2, badge, ha="right", va="center",
                fontsize=7.8, fontweight="bold", color=badge_col, zorder=4,
                bbox=dict(boxstyle="square,pad=0.2", fc="white", ec=badge_col, lw=0.8))

        # Second line of header: Title
        ax.text(x + 2.5, y + h - 6.8, title, ha="left", va="center",
                fontsize=9.0, fontweight="bold", color="#0F172A", zorder=4)

        text_y = y + h - 13.0
        for b in bullets:
            ax.text(x + 2.5, text_y, f"• {b}", ha="left", va="top", fontsize=8.4, color="#1E293B", zorder=4)
            text_y -= 5.5

    def draw_arrow(x1, y1, x2, y2, label="", col="#0F172A"):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color=col, lw=1.4),
            zorder=5
        )
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, label, ha="center", va="center",
                    fontsize=8.0, fontweight="bold", color="#0F172A", zorder=6,
                    bbox=dict(boxstyle="square,pad=0.22", fc="white", ec="#CBD5E1", lw=0.8))

    # Upper Stages (y=66, h=38, w=34.5)
    draw_stage_box(4, 66, 34.5, 38, "1", "Candidate Generation", "DELIVERED",
                   ["Bio-Entity Span Detection", "Intra-Sentence Entity Pairs", "Paragraph & Section Bounds", "Pre-flight Quality Gating"],
                   border_col="#0D9488", badge_col="#0D9488")

    draw_stage_box(42.5, 66, 34.5, 38, "2", "Syntactic Validation", "DELIVERED",
                   ["Forward Causal Triggers", "Passive Inversion Rules", "Agent-Nominal Patterns", "Strict Negation Quarantining"],
                   border_col="#0D9488", badge_col="#0D9488")

    draw_stage_box(81, 66, 34.5, 38, "3", "Context Resolution", "DELIVERED",
                   ["Demonstrative Anaphora", "Abbreviation Normalization", "Discourse Connectives", "Dual-Sentence Alignment"],
                   border_col="#0D9488", badge_col="#0D9488")

    draw_stage_box(119.5, 66, 34.5, 38, "4", "Multi-Page Linking", "0.5350 F1",
                   ["Bounded Multi-Hop (<= 2 hops)", "Domain-Invariant Pruning", "Reverse Regulator Gating", "Confidence Compounding"],
                   border_col="#2563EB", badge_col="#2563EB")

    # Connectors between upper stages
    draw_arrow(38.5, 85, 42.5, 85)
    draw_arrow(77.0, 85, 81.0, 85)
    draw_arrow(115.5, 85, 119.5, 85)

    # Lower Deck: Panel 1 (Invariants)
    rect1 = patches.Rectangle((4, 4), 72, 52, facecolor="#F8FAFC", edgecolor="#2563EB", linewidth=1.3, zorder=2)
    ax.add_patch(rect1)
    hbar1 = patches.Rectangle((4, 48), 72, 8.0, facecolor="#F1F5F9", edgecolor="#2563EB", linewidth=1.1, zorder=3)
    ax.add_patch(hbar1)
    ax.text(6.5, 52.0, "Strict False-Positive Controls & Domain Invariants", ha="left", va="center",
            fontsize=10.0, fontweight="bold", color="#0F172A", zorder=4)
    ax.text(73.5, 52.0, "ACTIVE INVARIANTS", ha="right", va="center",
            fontsize=7.8, fontweight="bold", color="#2563EB", zorder=4,
            bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="#2563EB", lw=0.8))

    bullets_inv = [
        "Terminal Phenotype Invariant: Virulence and survival cannot cause upstream regulatory genes",
        "Environmental Invariant: Extracellular conditions (pH, temp) cannot be transcriptionally activated",
        "Homology & Method Gate: Non-causal cloning, homologue analogies, and methods suppressed",
        "Relative Clause Barrier: Suppresses spurious cross-clause entity-trigger associations",
        "Master Regulator Directionality: Restricts reverse feedback loops (InvF -> HilA, EspA -> PhoP)"
    ]
    ty = 44.5
    for b in bullets_inv:
        wrapped = textwrap.wrap(b, width=54)
        ax.text(6.5, ty, f"• {wrapped[0]}", ha="left", va="top", fontsize=8.3, color="#0F172A", zorder=4)
        if len(wrapped) > 1:
            ax.text(9.0, ty - 3.2, f"{wrapped[1]}", ha="left", va="top", fontsize=8.1, color="#475569", zorder=4)
        ty -= 8.0

    # Lower Deck: Panel 2 (Verification)
    rect2 = patches.Rectangle((80, 4), 72, 52, facecolor="#F8FAFC", edgecolor="#0D9488", linewidth=1.3, zorder=2)
    ax.add_patch(rect2)
    hbar2 = patches.Rectangle((80, 48), 72, 8.0, facecolor="#F1F5F9", edgecolor="#0D9488", linewidth=1.1, zorder=3)
    ax.add_patch(hbar2)
    ax.text(82.5, 52.0, "5. Provenance Grounding & Verification Engine", ha="left", va="center",
            fontsize=10.0, fontweight="bold", color="#0F172A", zorder=4)
    ax.text(149.5, 52.0, "VERIFIED (100%)", ha="right", va="center",
            fontsize=7.8, fontweight="bold", color="#0D9488", zorder=4,
            bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="#0D9488", lw=0.8))

    bullets_ver = [
        "Dual-Sentence Evidence Tracking: Verbatim [S_causal, S_entity] bindings with zero hallucination",
        "Calibrated Confidence Metric: Empirical Platt-scaled posterior precision score in [0.0, 1.0]",
        "Full Text Auditability: Exact character indices [c_start, c_end] and physical page numbers",
        "Selective Prediction Abstention: Rejection threshold tau = 0.45 for uncertain assertions",
        "Cryptographic Integrity: Frozen SHA-256 ground-truth ledger across all 20 benchmark papers"
    ]
    ty = 44.5
    for b in bullets_ver:
        wrapped = textwrap.wrap(b, width=54)
        ax.text(82.5, ty, f"• {wrapped[0]}", ha="left", va="top", fontsize=8.3, color="#0F172A", zorder=4)
        if len(wrapped) > 1:
            ax.text(85.0, ty - 3.2, f"{wrapped[1]}", ha="left", va="top", fontsize=8.1, color="#475569", zorder=4)
        ty -= 8.0

    # Vertical connectors between rows
    draw_arrow(59.75, 66, 59.75, 56, "Direction Check")
    draw_arrow(98.25, 66, 98.25, 56, "Dual Spans [Sc, Se]")
    draw_arrow(136.75, 66, 136.75, 56, "Transitive Paths")

    # Horizontal connector between invariants and verification
    draw_arrow(76, 28, 80, 28, "Gated")

    ax.set_title("EVRYN Multi-Stage Causal Extraction Workflow & Modular Verification Architecture",
                 fontsize=13.5, fontweight="bold", pad=12)
    save_fig(fig, "fig2_extraction_workflow")


# ==============================================================================
# Figure 3.1: Evidence Grounding and Causal Directionality
# ==============================================================================
def generate_fig3_evidence_direction():
    """Figure 3.1: Evidence Grounding and Direction Diagram (Clean layout and high readability)."""
    fig, ax = plt.subplots(figsize=(15.6, 9.6), dpi=300)
    ax.set_xlim(0, 156)
    ax.set_ylim(0, 96)
    ax.axis("off")

    def draw_entity_card(x, y, w, h, title, subtitle_lines, border_col="#0D9488"):
        rect = patches.Rectangle((x, y), w, h, facecolor="#F8FAFC", edgecolor=border_col, linewidth=1.4, zorder=2)
        ax.add_patch(rect)
        hbar = patches.Rectangle((x, y + h - 4.5), w, 4.5, facecolor=border_col, edgecolor=border_col, linewidth=1.0, zorder=3)
        ax.add_patch(hbar)
        ax.text(x + w / 2, y + h - 2.25, title, ha="center", va="center", fontsize=10.2, fontweight="bold", color="white", zorder=4)

        ty = y + h - 7.5
        for line in subtitle_lines:
            ax.text(x + 2.5, ty, line, ha="left", va="top", fontsize=8.6, color="#1E293B", zorder=4)
            ty -= 4.2

    # Top Cause & Effect
    draw_entity_card(5, 66, 38, 24, "Cause Entity (C)", [
        "Canonical: PmrB",
        "Mention: \"PmrB sensor kinase\"",
        "Entity Type: Sensor Kinase / Protein",
        "Section: Results | Page: 2"
    ], border_col="#0D9488")

    draw_entity_card(113, 66, 38, 24, "Effect Entity (E)", [
        "Canonical: PmrA",
        "Mention: \"response regulator PmrA\"",
        "Entity Type: Response Regulator / Protein",
        "Section: Results | Page: 3"
    ], border_col="#0D9488")

    # Directed Causal Arrow
    ax.annotate(
        "", xy=(113, 78), xytext=(43, 78),
        arrowprops=dict(arrowstyle="-|>", color="#0F172A", lw=2.2),
        zorder=4
    )
    ax.text(78, 83.5, "RELATION: DIRECT_CAUSE (+)", ha="center", va="center",
            fontsize=11.0, fontweight="bold", color="#0D9488", zorder=5,
            bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="#0D9488", lw=1.0))
    ax.text(78, 72.0, "Direction: FORWARD   |   Confidence: 0.95   |   Polarity: POSITIVE", ha="center", va="center",
            fontsize=8.8, fontweight="bold", color="#334155", zorder=5,
            bbox=dict(boxstyle="square,pad=0.25", fc="white", ec="#CBD5E1", lw=0.8))

    # Middle: Evidence Box
    rect_mid = patches.Rectangle((5, 37), 146, 23, facecolor="#FFFFFF", edgecolor="#2563EB", linewidth=1.4, zorder=2)
    ax.add_patch(rect_mid)
    hbar_mid = patches.Rectangle((5, 55.5), 146, 4.5, facecolor="#2563EB", edgecolor="#2563EB", linewidth=1.0, zorder=3)
    ax.add_patch(hbar_mid)
    ax.text(8.0, 57.75, "Primary Evidence Sentence & Verbatim Provenance Coordinates (S_causal)",
            ha="left", va="center", fontsize=10.0, fontweight="bold", color="white", zorder=4)
    ax.text(148.0, 57.75, "100% PROVENANCE VERIFIED",
            ha="right", va="center", fontsize=8.0, fontweight="bold", color="white", zorder=4)

    # Quote Callout
    rect_q = patches.Rectangle((8, 44), 140, 9.5, facecolor="#F1F5F9", edgecolor="#94A3B8", linewidth=0.9, zorder=3)
    ax.add_patch(rect_q)
    ax.text(78, 48.75, "\"Acid pH activates the PmrA/PmrB system by promoting PmrB-mediated phosphorylation of PmrA.\"",
            ha="center", va="center", fontsize=9.2, fontstyle="italic", color="#0F172A", zorder=4)

    # Metadata bar
    ax.text(78, 40.5, "Doc ID: PMC1804205  |  Section: RESULTS  |  Paragraph: 14  |  Sentence ID: s42  |  Offsets: [1420--1512]  |  Page: 2",
            ha="center", va="center", fontsize=8.5, fontweight="bold", color="#475569", zorder=4)

    # Downward Connectors
    for cx, lbl in [(28, "Intra-Sentence Context"), (78, "Anaphoric Context Resolution"), (128, "Transitive Multi-Hop Linking")]:
        ax.annotate(
            "", xy=(cx, 26), xytext=(cx, 37),
            arrowprops=dict(arrowstyle="-|>", color="#64748B", lw=1.3, linestyle="--"),
            zorder=3
        )
        ax.text(cx, 31.5, lbl, ha="center", va="center", fontsize=7.8, fontweight="bold", color="#1E293B", zorder=5,
                bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="#CBD5E1", lw=0.7))

    # Bottom Cards
    def draw_typology_card(x, y, w, h, title, subtitle, bullets, border_col):
        rect = patches.Rectangle((x, y), w, h, facecolor="#FFFFFF", edgecolor=border_col, linewidth=1.3, zorder=2)
        ax.add_patch(rect)
        hbar = patches.Rectangle((x, y + h - 5.5), w, 5.5, facecolor="#F8FAFC", edgecolor=border_col, linewidth=1.1, zorder=3)
        ax.add_patch(hbar)
        ax.text(x + 2.5, y + h - 2.8, title, ha="left", va="center", fontsize=9.2, fontweight="bold", color=border_col, zorder=4)
        ax.text(x + w - 2.5, y + h - 2.8, subtitle, ha="right", va="center", fontsize=7.6, color="#64748B", zorder=4)

        ty = y + h - 8.5
        for b in bullets:
            ax.text(x + 2.5, ty, f"• {b}", ha="left", va="top", fontsize=8.2, color="#1E293B", zorder=4)
            ty -= 3.8

    draw_typology_card(5, 4, 46, 22, "1. Direct Intra-Sentence Assertion", "Single Sentence", [
        "Both C & E co-occur in S_causal boundary",
        "Syntactic trigger: \"activation of\", \"induces\"",
        "Complete coordinates: <p.2, Results, [1420-1512]>",
        "High empirical precision (0.90--0.98 on gold)"
    ], border_col="#0D9488")

    draw_typology_card(55, 4, 46, 22, "2. Context-Resolved Candidate", "Cross-Sentence", [
        "Inter-sentence alignment across [S_k, S_{k+1}]",
        "Demonstrative pronoun & anaphora resolution",
        "Dual Provenance Binding: [S_cause, S_effect]",
        "Abbreviation expansion via domain normalizer"
    ], border_col="#2563EB")

    draw_typology_card(105, 4, 46, 22, "3. Multi-Page Transitive Link", "Multi-Page Graph", [
        "Path traversal: A -> B (p.2) -> C (p.8)",
        "Inter-page distance: Delta_p >= 1, hops <= 2",
        "Pruned by domain invariants (TCSTS_REVERSE_PAIRS)",
        "Distance decay: conf = prod(c_i) * lambda^d"
    ], border_col="#D97706")

    ax.set_title("EVRYN Evidence Grounding Contract: Dual-Span Provenance & Causal Directionality",
                 fontsize=13.5, fontweight="bold", pad=12)
    save_fig(fig, "fig3_evidence_direction")


# ==============================================================================
# Figure 5.1: Benchmark Split Architecture & Zero-Leakage Isolation
# ==============================================================================
def generate_fig4_evaluation_workflow():
    """Figure 5.1: Benchmark Partition and Zero-Leakage Evaluation Protocol."""
    fig, ax = plt.subplots(figsize=(15.6, 10.2), dpi=300)
    ax.set_xlim(0, 156)
    ax.set_ylim(0, 102)
    ax.axis("off")

    def draw_split_card(x, y, w, h, title, subtitle, papers, bullets, border_col):
        rect = patches.Rectangle((x, y), w, h, facecolor="#FFFFFF", edgecolor=border_col, linewidth=1.3, zorder=2)
        ax.add_patch(rect)
        hbar = patches.Rectangle((x, y + h - 5.5), w, 5.5, facecolor=border_col, edgecolor=border_col, linewidth=1.0, zorder=3)
        ax.add_patch(hbar)
        ax.text(x + w / 2, y + h - 2.8, title, ha="center", va="center", fontsize=9.2, fontweight="bold", color="white", zorder=4)

        # Subtitle
        ax.text(x + w / 2, y + h - 8.2, subtitle, ha="center", va="center", fontsize=7.8, fontweight="bold", color="#475569", zorder=4)

        # Papers box
        p_box = patches.Rectangle((x + 1.5, y + h - 24.5), w - 3.0, 14.5, facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=0.8, zorder=3)
        ax.add_patch(p_box)
        ax.text(x + 2.5, y + h - 11.5, "Papers / Identifiers:", ha="left", va="top", fontsize=7.4, fontweight="bold", color="#334155", zorder=4)
        py = y + h - 14.2
        for p in papers:
            ax.text(x + 2.5, py, p, ha="left", va="top", fontsize=7.1, color="#0F172A", zorder=4)
            py -= 2.6

        # Bullets
        by = y + h - 27.5
        for b in bullets:
            ax.text(x + 2.5, by, f"• {b}", ha="left", va="top", fontsize=7.7, color="#1E293B", zorder=4)
            by -= 4.2

    # Development & Tuning Zone
    rect_dev = patches.Rectangle((4, 25), 66, 71, facecolor="#F8FAFC", edgecolor="#0D9488", linewidth=1.4, zorder=1)
    ax.add_patch(rect_dev)
    ax.text(37, 92.5, "DEVELOPMENT & TUNING ZONE (Permitted Model Calibration)",
            ha="center", va="center", fontsize=10.2, fontweight="bold", color="#0D9488", zorder=2)

    draw_split_card(6.5, 28, 29, 61, "Train Split (4 Papers)", "35 Gold Relations (19 Dir, 16 Cross)", [
        "PMC2651894 (p. 5)  |  PMC2682197 (p. 12)",
        "PMC2714965 (p. 12) |  PMC2774163 (p. 13)"
    ], [
        "Grammar & trigger discovery",
        "Syntactic pattern mining",
        "Rule & invariant calibration",
        "Strictly isolated from test"
    ], border_col="#0D9488")

    draw_split_card(38.5, 28, 29, 61, "Dev Split (8 Papers)", "71 Gold Relations (36 Dir, 35 Cross)", [
        "PMC1804205 (p. 7)  |  PMC1874608 (p. 12)",
        "PMC1913099 (p. 16) |  PMC1974823 (p. 7)",
        "PMC2242835 (p. 10) |  PMC2266911 (p. 12)",
        "PMC2358977 (p. 12) |  PMC2430206 (p. 10)"
    ], [
        "Error census & FP diagnosis",
        "Threshold tuning (tau = 0.60)",
        "Criterion 5 verified (0.5350 F1)",
        "TCSTS reverse-edge gating"
    ], border_col="#0D9488")

    # Strict Zero-Leakage Gate
    rect_gate = patches.Rectangle((72, 25), 12, 71, facecolor="#F1F5F9", edgecolor="#475569", linewidth=1.5, hatch="//", zorder=2)
    ax.add_patch(rect_gate)
    ax.text(78, 92.5, "[GATE]", ha="center", va="center", fontsize=8.0, fontweight="bold", color="#0F172A", zorder=4,
            bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="#475569", lw=0.8))

    gate_lines = [
        "ZERO", "LEAKAGE", "RELEASE", "GATE",
        "──────",
        "Code & Rules", "Frozen Prior", "to Confirmatory", "Evaluation",
        "──────",
        "Zero Feedback", "Zero Leakage"
    ]
    gy = 86.0
    for gl in gate_lines:
        fw = "bold" if gl not in ["──────", "Frozen Prior", "to Confirmatory", "Evaluation"] else "normal"
        col = "#0F172A" if fw == "bold" else "#475569"
        ax.text(78, gy, gl, ha="center", va="center", fontsize=7.4, fontweight=fw, color=col, zorder=4)
        gy -= 4.8

    # Confirmatory Evaluation Zone
    rect_test = patches.Rectangle((86, 25), 66, 71, facecolor="#F1F5F9", edgecolor="#2563EB", linewidth=1.4, zorder=1)
    ax.add_patch(rect_test)
    ax.text(119, 92.5, "CONFIRMATORY EVALUATION ZONE (Strictly Held-Out & Blind)",
            ha="center", va="center", fontsize=10.2, fontweight="bold", color="#2563EB", zorder=2)

    draw_split_card(88.5, 28, 29, 61, "Locked Test (4 Papers)", "41 Gold Relations (21 Dir, 20 Cross)", [
        "PMC2565068 (p. 9)  |  PMC2581603 (p. 10)",
        "PMC2593050 (p. 5)  |  PMC2639726 (p. 14)"
    ], [
        "Single post-hoc evaluation",
        "Confirmatory generalization",
        "Frozen model parameters",
        "Zero hyperparameter tuning"
    ], border_col="#2563EB")

    draw_split_card(120.5, 28, 29, 61, "External Unseen (4 Papers)", "36 Gold Relations (20 Dir, 16 Cross)", [
        "PMC2816692 (p. 10) |  PMC2829055 (p. 9)",
        "PMC2858072 (p. 8)  |  PMC2885601 (p. 6)"
    ], [
        "Unseen pathogen genetics",
        "Authenticated V2 ground truth",
        "Out-of-domain evaluation",
        "Zero tuning feedback"
    ], border_col="#4F46E5")

    # Bottom: Benchmark Ground-Truth Ledger
    rect_bot = patches.Rectangle((4, 4), 148, 18, facecolor="#FFFFFF", edgecolor="#94A3B8", linewidth=1.3, zorder=2)
    ax.add_patch(rect_bot)
    hbar_bot = patches.Rectangle((4, 17.5), 148, 4.5, facecolor="#F8FAFC", edgecolor="#94A3B8", linewidth=1.0, zorder=3)
    ax.add_patch(hbar_bot)
    ax.text(78, 19.75, "Benchmark Ground-Truth Ledger & Annotation Audit Protocol (20 Papers, 183 Gold Causal Relations)",
            ha="center", va="center", fontsize=9.2, fontweight="bold", color="#0F172A", zorder=4)

    # Left Sub-panel: V1
    rect_v1 = patches.Rectangle((6, 6), 69, 10, facecolor="#FEF2F2", edgecolor="#EF4444", linewidth=0.9, zorder=3)
    ax.add_patch(rect_v1)
    ax.text(7.5, 13.8, "Legacy Benchmark V1 (Unaligned Metadata):", ha="left", va="center", fontsize=7.6, fontweight="bold", color="#B91C1C", zorder=4)
    ax.text(7.5, 10.8, "• PMC2816692: Title registered as Anthrax LF while XML described Salmonella SrcA", ha="left", va="center", fontsize=7.2, color="#7F1D1D", zorder=4)
    ax.text(7.5, 8.0, "• Resulted in 54 False Positives on External split; Direct F1 = 0.3269, Cross F1 = 0.2548", ha="left", va="center", fontsize=7.2, color="#7F1D1D", zorder=4)

    # Right Sub-panel: V2
    rect_v2 = patches.Rectangle((79, 6), 71, 10, facecolor="#F0FDF4", edgecolor="#16A34A", linewidth=0.9, zorder=3)
    ax.add_patch(rect_v2)
    ax.text(80.5, 13.8, "Authenticated Benchmark V2 (Audited Ground Truth):", ha="left", va="center", fontsize=7.6, fontweight="bold", color="#15803D", zorder=4)
    ax.text(80.5, 10.8, "• PMC2816692: Aligned to authentic SrcA/PipB2/SseL mechanisms (15 False Positives)", ha="left", va="center", fontsize=7.2, color="#14532D", zorder=4)
    ax.text(80.5, 8.0, "• 183 Gold Relations (96 Direct, 87 Cross); Ext Direct F1 = 0.4808, Cross F1 = 0.3262", ha="left", va="center", fontsize=7.2, color="#14532D", zorder=4)

    ax.set_title("EVRYN 20-Paper Benchmark Partition and Strict Zero-Leakage Evaluation Protocol",
                 fontsize=13.5, fontweight="bold", pad=12)
    save_fig(fig, "fig4_evaluation_workflow")


# ==============================================================================
# Figure 5.2: Verified Results & Progression Across Evaluation Splits
# ==============================================================================
def generate_fig6_results_progression():
    """Figure 5.2: Verified Results Across Evaluation Splits (Light academic palette)."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15.0, 5.6), dpi=300)

    splits = ["Train\n(4 papers)", "Dev\n(8 papers)", "Locked\n(4 papers)", "Ext V1\n(4 papers)", "Ext V2\n(4 papers)"]

    # Phase 1.14 Verified Metrics
    direct_f1 = [0.4958, 0.6820, 0.5584, 0.3269, 0.4808]
    direct_err_low = [0.4958 - 0.3667, 0.6820 - 0.5805, 0.5584 - 0.3542, 0.3269 - 0.1000, 0.4808 - 0.3538]
    direct_err_high = [0.6625 - 0.4958, 0.7757 - 0.6820, 0.7279 - 0.5584, 0.5269 - 0.3269, 0.6077 - 0.4808]

    cross_f1 = [0.2000, 0.5350, 0.2625, 0.2548, 0.3262]
    cross_err_low = [0.2000 - 0.0000, 0.5350 - 0.3037, 0.2625 - 0.1000, 0.2548 - 0.0833, 0.3262 - 0.2857]
    cross_err_high = [0.4000 - 0.2000, 0.7640 - 0.5350, 0.4000 - 0.2625, 0.3714 - 0.2548, 0.3714 - 0.3262]

    match_ratio = [0.2510, 0.4979, 0.2978, 0.1863, 0.2696]

    x = np.arange(len(splits))
    # Light restrained academic palette
    colors = ["#94A3B8", "#0D9488", "#2563EB", "#CBD5E1", "#4F46E5"]

    # Panel 1: Direct F1
    bars1 = ax1.bar(x, direct_f1, yerr=[direct_err_low, direct_err_high], capsize=5,
                    color=colors, edgecolor="#0F172A", width=0.55, linewidth=1.1, error_kw=dict(lw=1.2, capthick=1.2))
    ax1.set_ylabel("Direct Causal F1", fontweight="bold", fontsize=11.5, color="#0F172A")
    ax1.set_title("Direct Relation F1 (95% CI)", fontweight="bold", fontsize=12.5, pad=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(splits, fontsize=10)
    ax1.set_ylim(0, 0.98)
    ax1.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")
    for bar, val, eh in zip(bars1, direct_f1, direct_err_high):
        ci_top = val + eh
        ax1.text(bar.get_x() + bar.get_width() / 2, ci_top + 0.025, f"{val:.4f}",
                 ha="center", va="bottom", fontsize=9.2, fontweight="bold", color="#0F172A")

    # Panel 2: Cross-Page F1
    bars2 = ax2.bar(x, cross_f1, yerr=[cross_err_low, cross_err_high], capsize=5,
                    color=colors, edgecolor="#0F172A", width=0.55, linewidth=1.1, error_kw=dict(lw=1.2, capthick=1.2))
    ax2.set_ylabel("Cross-Page Causal F1", fontweight="bold", fontsize=11.5, color="#0F172A")
    ax2.set_title("Cross-Page Relation F1 (95% CI)", fontweight="bold", fontsize=12.5, pad=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(splits, fontsize=10)
    ax2.set_ylim(0, 0.92)
    ax2.axhline(0.50, color="#D97706", linestyle="--", linewidth=1.3, label="Phase 1 Threshold (0.50)")
    ax2.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=8.8)
    ax2.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")
    for bar, val, eh in zip(bars2, cross_f1, cross_err_high):
        ci_top = val + eh
        ax2.text(bar.get_x() + bar.get_width() / 2, ci_top + 0.025, f"{val:.4f}",
                 ha="center", va="bottom", fontsize=9.2, fontweight="bold", color="#0F172A")

    # Panel 3: Exact Structural Match
    bars3 = ax3.bar(x, match_ratio, color=colors, edgecolor="#0F172A", width=0.55, linewidth=1.1)
    ax3.set_ylabel("Exact Structural Match Ratio", fontweight="bold", fontsize=11.5, color="#0F172A")
    ax3.set_title("Exact Structural Match Ratio", fontweight="bold", fontsize=12.5, pad=10)
    ax3.set_xticks(x)
    ax3.set_xticklabels(splits, fontsize=10)
    ax3.set_ylim(0, 0.60)
    ax3.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")
    for bar, val in zip(bars3, match_ratio):
        ax3.text(bar.get_x() + bar.get_width() / 2, val + 0.020, f"{val:.4f}",
                 ha="center", va="bottom", fontsize=9.2, fontweight="bold", color="#0F172A")

    fig.suptitle("EVRYN Phase 1.13 Verified Benchmark Metrics Across Isolated Splits",
                 fontsize=14.0, fontweight="bold", y=1.02)
    plt.tight_layout()
    save_fig(fig, "fig6_results_progression")


# ==============================================================================
# Figure 5.3: Error Analysis Taxonomy (Audited 29 FN, 76 FP)
# ==============================================================================
def generate_fig5_error_analysis():
    """Figure 5.3: Error Analysis Taxonomy (Audited 29 FN, 76 FP in Benchmark V2) with Light Palette."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.2, 5.8), dpi=300)

    # Left: False Negatives Taxonomy (29 Cases)
    categories_fn = [
        "Multi-Complex\nAssembly",
        "Implicit\nPromoters",
        "Multi-Hop\nHypoxia",
        "Negative\nFeedback"
    ]
    counts_fn = [10, 9, 6, 4]
    pcts_fn = [c / sum(counts_fn) * 100 for c in counts_fn]
    colors_fn = ["#0D9488", "#14B8A6", "#2DD4BF", "#99F6E4"]

    bars1 = ax1.bar(categories_fn, counts_fn, color=colors_fn, edgecolor="#0F172A", width=0.52, linewidth=1.1)
    ax1.set_ylabel("False Negative Count", fontweight="bold", fontsize=11.5, color="#0F172A")
    ax1.set_title("False Negative Census (29 FNs in Benchmark V2)", fontweight="bold", fontsize=12.5, pad=12)
    ax1.set_ylim(0, 14)
    ax1.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")

    for bar, count, pct in zip(bars1, counts_fn, pcts_fn):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.35,
                 f"{count} ({pct:.1f}%)", ha="center", va="bottom", fontsize=9.8, fontweight="bold", color="#0F172A")

    # Light callout card for FN breakdown
    ax1.text(0.95, 0.95, "FN Census Summary (29 Cases):\n• Multi-Complex Assembly: 34.5%\n• Implicit Promoters: 31.0%\n• Multi-Hop Hypoxia: 20.7%\n• Negative Feedback: 13.8%",
             transform=ax1.transAxes, ha="right", va="top", fontsize=9.0, color="#0F172A",
             bbox=dict(boxstyle="square,pad=0.4", fc="#F8FAFC", ec="#0D9488", lw=1.1))

    # Right: False Positives Breakdown (76 Cases Post-Intervention)
    categories_fp = [
        "Experimental\nControls",
        "Co-occurring\nRegulators",
        "Assay\nReagents",
        "Broad\nPhenotypes"
    ]
    counts_fp = [28, 24, 14, 10]
    pcts_fp = [c / sum(counts_fp) * 100 for c in counts_fp]
    colors_fp = ["#2563EB", "#3B82F6", "#60A5FA", "#93C5FD"]

    bars2 = ax2.bar(categories_fp, counts_fp, color=colors_fp, edgecolor="#0F172A", width=0.52, linewidth=1.1)
    ax2.set_ylabel("False Positive Count", fontweight="bold", fontsize=11.5, color="#0F172A")
    ax2.set_title("False Positive Taxonomy (76 FPs in Benchmark V2)", fontweight="bold", fontsize=12.5, pad=12)
    ax2.set_ylim(0, 36)
    ax2.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")

    for bar, count, pct in zip(bars2, counts_fp, pcts_fp):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                 f"{count} ({pct:.1f}%)", ha="center", va="bottom", fontsize=9.8, fontweight="bold", color="#0F172A")

    # Light callout card for FP breakdown
    ax2.text(0.95, 0.95, "FP Taxonomy Summary (76 Cases):\n• Experimental Controls: 36.8%\n• Co-occurring Regulators: 31.6%\n• Assay Reagents: 18.4%\n• Broad Phenotypes: 13.2%",
             transform=ax2.transAxes, ha="right", va="top", fontsize=9.0, color="#0F172A",
             bbox=dict(boxstyle="square,pad=0.4", fc="#F8FAFC", ec="#2563EB", lw=1.1))

    fig.suptitle("EVRYN Error Analysis: Systematic Census of Remaining Extraction Failures",
                 fontsize=13.8, fontweight="bold", y=1.01)
    plt.tight_layout()
    save_fig(fig, "fig5_error_analysis")


# ==============================================================================
# Figure 5.4: Continual SCM Adaptation and Higher-Order Recovery
# ==============================================================================
def generate_fig7_continual_and_higher_order():
    """Figure 5.4: Continual Adaptation & Higher-Order Discovery (Expanded, large-type publication layout)."""
    fig = plt.figure(figsize=(15.2, 5.8), dpi=300)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1.0, 1.0], wspace=0.30)

    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax3 = fig.add_subplot(gs[2])

    # -------------------------------------------------------------
    # Panel 1: Continual Learning Trajectory (8 sequential tasks)
    # -------------------------------------------------------------
    tasks_x = np.arange(1, 9)
    # Authentic empirical trajectory from run_continual_flux
    em_acc = np.array([1.0, 1.0, 0.67, 0.75, 0.80, 0.83, 0.71, 0.75])
    scratch_acc = np.array([1.0, 0.50, 0.67, 0.50, 0.60, 0.67, 0.57, 0.625])

    ax1.plot(tasks_x, em_acc, "o-", color="#0D9488", linewidth=2.4, markersize=7,
             label=f"FLUX Evidence Matching (75.0%)", zorder=4)
    ax1.plot(tasks_x, scratch_acc, "s--", color="#DC2626", linewidth=1.8, markersize=6,
             label=f"Scratch Baseline (62.5%)", zorder=3)
    ax1.axhline(0.50, color="#64748B", linestyle=":", linewidth=1.2, label="Random Guess (50.0%)", zorder=2)

    ax1.set_title("Continual SCM Adaptation", fontweight="bold", fontsize=12.5, pad=10)
    ax1.set_xlabel("Sequential SCM Tasks", fontweight="bold", fontsize=11, color="#0F172A")
    ax1.set_ylabel("Cumulative Accuracy", fontweight="bold", fontsize=11, color="#0F172A")
    ax1.set_ylim(0.40, 1.05)
    ax1.set_xticks(tasks_x)
    ax1.grid(True, linestyle="--", alpha=0.5, color="#CBD5E1")
    ax1.legend(loc="lower left", frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=8.8)

    # Backward Transfer callout
    ax1.text(0.95, 0.95, "Backward Transfer: 0.00%\n(Zero Catastrophic Forgetting)",
             transform=ax1.transAxes, ha="right", va="top", fontsize=8.5, fontweight="bold", color="#0D9488",
             bbox=dict(boxstyle="square,pad=0.3", fc="#F8FAFC", ec="#0D9488", lw=0.9))

    # -------------------------------------------------------------
    # Panel 2: Higher-Order Recovery F1 vs Baselines
    # -------------------------------------------------------------
    methods = ["Pairwise\nFLUX", "HCAM\nBase", "HO-FLUX\n(Base)", "HO-FLUX\n(+ΔR²+HSIC)", "Order-3\n(Triplets)"]
    ho_scores = [0.333, 0.540, 0.583, 0.633, 0.850]
    ho_colors = ["#94A3B8", "#64748B", "#3B82F6", "#2563EB", "#0D9488"]

    bars2 = ax2.bar(methods, ho_scores, color=ho_colors, edgecolor="#0F172A", width=0.55, linewidth=1.1, zorder=3)
    ax2.set_ylabel("Recovery F1 Score", fontweight="bold", fontsize=11, color="#0F172A")
    ax2.set_title("Higher-Order Recovery vs Baselines", fontweight="bold", fontsize=12.5, pad=10)
    ax2.set_ylim(0, 1.05)
    ax2.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")

    for bar, val in zip(bars2, ho_scores):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.02, f"{val:.3f}",
                 ha="center", va="bottom", fontsize=9.0, fontweight="bold", color="#0F172A")

    # -------------------------------------------------------------
    # Panel 3: Mechanism-Specific Recovery
    # -------------------------------------------------------------
    mechs = ["Mixed", "Multiplic.", "Three-Way", "GP Non-P.", "Nonlinear", "Confound."]
    mech_vals = [1.000, 0.950, 0.950, 0.450, 0.350, 0.283]
    mech_colors = ["#0D9488", "#14B8A6", "#2563EB", "#F59E0B", "#F97316", "#DC2626"]

    bars3 = ax3.bar(mechs, mech_vals, color=mech_colors, edgecolor="#0F172A", width=0.55, linewidth=1.1, zorder=3)
    ax3.set_ylabel("Specific Recovery Rate", fontweight="bold", fontsize=11, color="#0F172A")
    ax3.set_title("Mechanism-Specific Generalization", fontweight="bold", fontsize=12.5, pad=10)
    ax3.set_ylim(0, 1.15)
    ax3.set_xticks(range(len(mechs)))
    ax3.set_xticklabels(mechs, rotation=25, ha="right", fontsize=9.2)
    ax3.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")

    for bar, val in zip(bars3, mech_vals):
        ax3.text(bar.get_x() + bar.get_width() / 2, val + 0.02, f"{val:.2f}",
                 ha="center", va="bottom", fontsize=8.8, fontweight="bold", color="#0F172A")

    fig.suptitle("EVRYN Continual SCM Adaptation and Multivariate Higher-Order Interaction Recovery",
                 fontsize=13.8, fontweight="bold", y=1.02)
    save_fig(fig, "fig7_continual_and_higher_order")

    # Also save separate large subfigures for backwards compatibility with existing \includegraphics
    # 1. continual_flux_results
    fig_c, ax_c = plt.subplots(figsize=(10.5, 5.0), dpi=300)
    ax_c.plot(tasks_x, em_acc, "o-", color="#0D9488", linewidth=2.4, markersize=8,
              label=f"FLUX Evidence Matching (Final: 75.0%)", zorder=4)
    ax_c.plot(tasks_x, scratch_acc, "s--", color="#DC2626", linewidth=2.0, markersize=7,
              label=f"Scratch Baseline (Final: 62.5%)", zorder=3)
    ax_c.axhline(0.50, color="#64748B", linestyle=":", linewidth=1.4, label="Random Guess (50.0%)", zorder=2)
    ax_c.set_title("Continual Causal Discovery under Causality in Flux (8 Tasks)", fontsize=13, fontweight="bold", pad=12)
    ax_c.set_xlabel("Sequential Tasks Encountered", fontsize=11.5, fontweight="bold")
    ax_c.set_ylabel("Cumulative Causal Accuracy", fontsize=11.5, fontweight="bold")
    ax_c.set_ylim(0.40, 1.05)
    ax_c.set_xticks(tasks_x)
    ax_c.grid(True, linestyle="--", alpha=0.5, color="#CBD5E1")
    ax_c.legend(loc="lower left", frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=10)
    ax_c.text(0.95, 0.95, "Backward Transfer: 0.00%\n(Zero Catastrophic Forgetting)",
              transform=ax_c.transAxes, ha="right", va="top", fontsize=9.5, fontweight="bold", color="#0D9488",
              bbox=dict(boxstyle="square,pad=0.4", fc="#F8FAFC", ec="#0D9488", lw=1.0))
    save_fig(fig_c, "continual_flux_results")

    # 2. higher_order_mechanisms
    fig_h, (ax_h1, ax_h2) = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=300)
    bars_h1 = ax_h1.bar(methods, ho_scores, color=ho_colors, edgecolor="#0F172A", width=0.55, linewidth=1.1, zorder=3)
    ax_h1.set_ylabel("Recovery F1 Score", fontweight="bold", fontsize=11.5, color="#0F172A")
    ax_h1.set_title("Higher-Order Causal Recovery vs Baselines", fontweight="bold", fontsize=12.5, pad=12)
    ax_h1.set_ylim(0, 1.05)
    ax_h1.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")
    for bar, val in zip(bars_h1, ho_scores):
        ax_h1.text(bar.get_x() + bar.get_width() / 2, val + 0.02, f"{val:.3f}",
                   ha="center", va="bottom", fontsize=9.2, fontweight="bold", color="#0F172A")

    bars_h2 = ax_h2.bar(mechs, mech_vals, color=mech_colors, edgecolor="#0F172A", width=0.55, linewidth=1.1, zorder=3)
    ax_h2.set_ylabel("Recovery F1 Score", fontweight="bold", fontsize=11.5, color="#0F172A")
    ax_h2.set_title("Mechanism-Specific Generalization", fontweight="bold", fontsize=12.5, pad=12)
    ax_h2.set_ylim(0, 1.15)
    ax_h2.set_xticks(range(len(mechs)))
    ax_h2.set_xticklabels(mechs, rotation=25, ha="right", fontsize=9.5)
    ax_h2.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")
    for bar, val in zip(bars_h2, mech_vals):
        ax_h2.text(bar.get_x() + bar.get_width() / 2, val + 0.02, f"{val:.2f}",
                   ha="center", va="bottom", fontsize=9.0, fontweight="bold", color="#0F172A")
    fig_h.suptitle("Multivariate Higher-Order Mechanism Recovery", fontsize=13.5, fontweight="bold", y=1.02)
    save_fig(fig_h, "higher_order_mechanisms")


def main():
    print("Generating complete suite of publication-quality, light academic figures...")
    generate_fig0_research_scope()
    generate_fig1_system_architecture()
    generate_fig2_extraction_workflow()
    generate_fig3_evidence_direction()
    generate_fig4_evaluation_workflow()
    generate_fig5_error_analysis()
    generate_fig6_results_progression()
    generate_fig7_continual_and_higher_order()
    print("All publication figures successfully regenerated in PDF and PNG formats across all directories!")


if __name__ == "__main__":
    main()
