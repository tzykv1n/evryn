#!/usr/bin/env python3
"""
Generate publication-quality, printer-friendly, light-academic figures
for the EVRYN Research Monograph and Presentation.

Mandatory rules enforced:
- Light, restrained academic color palette (muted blue / soft teal / amber for
  caution; charcoal text; white canvas; light blue-grey grouping panels)
- No solid dark bar fills, heavy black grids, hatching, or inverted boxes
- Strictly square corners
- Readable typography; no overlapping text, connectors or labels
- Export both vector PDF and 300 DPI PNG

Set EVRYN_FIG_DIRS (os.pathsep-separated) to override the output directories.
"""

import os
import shutil
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

DEFAULT_DIRS = [
    "/home/tk/projects/phase1_report/figures",
    "/home/tk/projects/phase1_presentation/figures",
    "/home/tk/projects/evryn/docs/phase1/figures",
]
OUTPUT_DIRS = [d for d in os.environ.get("EVRYN_FIG_DIRS", os.pathsep.join(DEFAULT_DIRS)).split(os.pathsep) if d]
for d in OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

# ---- Palette ---------------------------------------------------------------
INK, INK2, MUTE, SLATE = "#0F172A", "#1E293B", "#475569", "#64748B"
RULE, PANEL, BAND, WHITE = "#CBD5E1", "#F8FAFC", "#F1F5F9", "#FFFFFF"
TEAL, BLUE, AMBER, INDIGO = "#0D9488", "#2563EB", "#D97706", "#4F46E5"

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
    "pdf.fonttype": 42,   # embed TrueType (editable / journal-safe)
    "ps.fonttype": 42,
})

U = 0.1  # inches per data unit on every "diagram" canvas


def save_fig(fig, *base_names):
    """Render once into the first directory, then copy to the rest."""
    first = OUTPUT_DIRS[0]
    for base in base_names:
        for ext in ("pdf", "png"):
            fig.savefig(os.path.join(first, f"{base}.{ext}"), bbox_inches="tight", pad_inches=0.15, dpi=300)
            for d in OUTPUT_DIRS[1:]:
                shutil.copyfile(os.path.join(first, f"{base}.{ext}"), os.path.join(d, f"{base}.{ext}"))
        print(f"Saved {base}.pdf / .png")
    plt.close(fig)


# ---- Diagram helpers ---------------------------------------------------------
def canvas(w_units, h_units):
    """Axes fill the whole figure, so 1 data unit == exactly U inches
    (plt.subplots() default margins silently shrank everything by ~22%)."""
    fig = plt.figure(figsize=(w_units * U, h_units * U), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w_units)
    ax.set_ylim(0, h_units)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, fc=WHITE, ec=INK, lw=1.3, ls="-", z=2):
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                                   linewidth=lw, linestyle=ls, zorder=z))


def band(ax, x, y_top, w, h, ec, lw=1.1):
    """Light header band (replaces the old solid dark bars)."""
    box(ax, x, y_top - h, w, h, BAND, ec, lw, z=3)


def tag(ax, x, y, s, col=INK, fs=9.0, ec=RULE, ha="center", va="center", z=7, lw=0.9):
    ax.text(x, y, s, ha=ha, va=va, fontsize=fs, fontweight="bold", color=col, zorder=z,
            bbox=dict(boxstyle="square,pad=0.25", fc="white", ec=ec, lw=lw))


def arrow(ax, x1, y1, x2, y2, col=INK, lw=1.5, ls="-", z=5):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, linestyle=ls,
                                shrinkA=0, shrinkB=0), zorder=z)


def bullets(ax, x, y_top, items, wrap, fs, gap, color=INK, z=4):
    """Wrapped bullet list with hanging indent. Returns the y below the last item."""
    lh = fs * 1.25 / 72 / U
    y = y_top
    for it in items:
        lines = textwrap.wrap(it, width=wrap, initial_indent="\u2022 ", subsequent_indent="   ")
        ax.text(x, y, "\n".join(lines), ha="left", va="top", fontsize=fs,
                color=color, linespacing=1.25, zorder=z)
        y -= len(lines) * lh + gap
    return y


def title(ax, s):
    ax.set_title(s, fontsize=13.5, fontweight="bold", pad=10, color=INK)


# ==============================================================================
# Figure 1.1: Three-Phase Research Scope
# ==============================================================================
def generate_fig0_research_scope():
    fig, ax = canvas(156, 66)

    def column(x, y, w, h, num, ttl, badge, items, col, bg):
        box(ax, x, y, w, h, bg, col, 1.5)
        band(ax, x, y + h, w, 10.5, col, 1.3)
        ax.text(x + 2.5, y + h - 3.2, f"PHASE {num}", ha="left", va="center",
                fontsize=12, fontweight="bold", color=col, zorder=4)
        ax.text(x + 2.5, y + h - 7.4, ttl, ha="left", va="center",
                fontsize=10, fontweight="bold", color=INK, zorder=4)
        tag(ax, x + w - 2.5, y + h - 3.4, badge, col, fs=8.6, ec=col, ha="right")
        bullets(ax, x + 3, y + h - 14, items, wrap=52, fs=9.6, gap=2.2)

    p1 = [
        "Full-text PMC-OA JATS XML & PDF parsing with geometry",
        "Section discourse tagging & coordinate tracking",
        "Syntactic & agent-nominal causal trigger parsing",
        "Dual-sentence context resolution [Sc, Se]",
        "Bounded transitive multi-hop reasoning (<= 2 hops)",
        "Calibrated confidence verification & Platt scaling",
        "100% provenance contract (doc, page, offsets, quotes)",
        "20-paper authentic PMC benchmark validation",
    ]
    p2 = [
        "Multi-document graph fusion across literature",
        "Cross-paper entity normalization & alias resolution",
        "25-year longitudinal corpus trajectory tracking",
        "Causal mechanism drift & belief revision detection",
        "Continual SCM adaptation with zero forgetting",
        "Conformal semantic gating via PubMedBERT",
        "Empirical evaluation on temporal SCM streams",
        "Cross-study consensus & refutation modeling",
    ]
    p3 = [
        "Dynamic causal graph manifold representation",
        "Prospective emergent link forecasting",
        "Pre-publication hypothesis generation & ranking",
        "Multi-hop cross-domain mechanism completion",
        "Prospective validation on post-cutoff publications",
        "Biomedical discovery prioritization pipeline",
        "Comprehensive M.Tech defense monograph",
        "Reproducible open-source software release",
    ]
    # 3 columns of width 42 with 12-unit gutters (room for connector labels)
    column(4, 3, 42, 58, "1", "Multi-Page Causal Extraction", "DELIVERED (Phase 1.14)", p1, TEAL, PANEL)
    column(58, 3, 42, 58, "2", "Corpus Transfer & Adaptation", "IN PROGRESS", p2, BLUE, WHITE)
    column(112, 3, 42, 58, "3", "Prospective Discovery Prediction", "PLANNED", p3, SLATE, WHITE)

    for x1, x2, lbl in [(46.8, 57.2, "Grounded\nGraphs"), (100.8, 111.2, "Longitudinal\nCorpus")]:
        arrow(ax, x1, 30, x2, 30, lw=1.7)
        tag(ax, (x1 + x2) / 2, 34.6, lbl, INK, fs=8.4)

    title(ax, "EVRYN Overarching Three-Phase Research Scope & Monograph Demarcation")
    save_fig(fig, "research_scope", "fig1_research_scope")


# ==============================================================================
# Figure 4.1: End-to-End System Architecture
# ==============================================================================
def generate_fig1_system_architecture():
    fig, ax = canvas(136, 56)

    def stage(x, y, w, h, ttl, sub, ec, fill=PANEL, lw=1.3, ls="-"):
        box(ax, x, y, w, h, fill, ec, lw, ls)
        ax.text(x + w / 2, y + h * 0.68, ttl, ha="center", va="center", fontsize=10.5,
                fontweight="bold", color=INK, zorder=3)
        ax.text(x + w / 2, y + h * 0.32, sub, ha="center", va="center", fontsize=9.2,
                color=INK2, zorder=3, linespacing=1.3)

    stage(3, 34, 22, 19, "Stage 1: Ingestion", "PMC-OA JATS XML / PDF\nLayout Geometry Offset", TEAL)
    arrow(ax, 25, 43.5, 29, 43.5)
    stage(29, 34, 22, 19, "Stage 2: Parsing", "Discourse Segmenter\nSection Roles & Bounds", TEAL)
    arrow(ax, 51, 43.5, 55, 43.5)
    stage(55, 34, 22, 19, "Stage 3: Normalizer", "Controlled Vocabularies\nAcronyms & Synonyms", TEAL)
    arrow(ax, 77, 43.5, 81, 43.5)
    stage(81, 34, 22, 19, "Stage 4: Extraction", "Syntactic Causal Engine\nAgent-Nominals & Polarity", BLUE)
    arrow(ax, 103, 43.5, 107, 43.5)
    stage(107, 34, 26, 19, "Stage 5: Verification", "Bounded Path Traversal\nConfidence Calibration", BLUE)

    # Grounding subsystem (narrowed so the "Verified" connector has room)
    box(ax, 3, 5, 94, 21, WHITE, TEAL, 1.3, "--")
    ax.text(50, 22, "Evidence Grounding Subsystem & Provenance Audit Contract", ha="center", va="center",
            fontsize=10.5, fontweight="bold", color=INK, zorder=3)
    ax.text(50, 13.2,
            "Exact Character Index Spans [c_start, c_end]  |  Physical Page Numbers  |  Verbatim Source Quotes\n"
            "Terminal Phenotype Direction Invariant  |  Environmental Parameter Invariant\n"
            "Homology Non-Causal Method Gating  |  Relative Clause Barrier",
            ha="center", va="center", fontsize=9.2, color=INK2, zorder=3, linespacing=1.55)

    box(ax, 107, 5, 26, 21, BAND, BLUE, 1.4)
    ax.text(120, 19, "Causal Graph Output", ha="center", va="center", fontsize=10.5, fontweight="bold", color=INK, zorder=3)
    ax.text(120, 11.5, "Traceable Mechanism SCM\n100% Span Provenance", ha="center", va="center",
            fontsize=9.2, color=INK2, zorder=3, linespacing=1.3)

    for cx in (14, 40, 66, 92):
        arrow(ax, cx, 34, cx, 26)
    arrow(ax, 97, 15.5, 107, 15.5)
    tag(ax, 102, 19.3, "Verified", INK, fs=8.8)
    arrow(ax, 120, 34, 120, 26)
    tag(ax, 121.4, 30, "Resolved Claims", INK, fs=8.8, ha="left")

    title(ax, "EVRYN System Architecture: Modular End-to-End Multi-Page Causal Discovery Pipeline")
    save_fig(fig, "fig1_system_architecture")


# ==============================================================================
# Figure 4.2: Multi-Stage Causal Extraction Workflow
# ==============================================================================
def generate_fig2_extraction_workflow():
    fig, ax = canvas(156, 98)

    def stage(x, y, w, h, num, ttl, badge, items, col):
        box(ax, x, y, w, h, WHITE, col, 1.3)
        band(ax, x, y + h, w, 10, col)
        ax.text(x + 2.5, y + h - 3.2, f"STAGE {num}", ha="left", va="center", fontsize=10.5,
                fontweight="bold", color=col, zorder=4)
        tag(ax, x + w - 2.5, y + h - 3.4, badge, col, fs=8.2, ec=col, ha="right")
        ax.text(x + 2.5, y + h - 7.4, ttl, ha="left", va="center", fontsize=9.6,
                fontweight="bold", color=INK, zorder=4)
        bullets(ax, x + 2.5, y + h - 13.5, items, wrap=34, fs=9.2, gap=1.8, color=INK2)

    stage(4, 60, 34.5, 36, "1", "Candidate Generation", "DELIVERED",
          ["Bio-Entity Span Detection", "Intra-Sentence Entity Pairs", "Paragraph & Section Bounds", "Pre-flight Quality Gating"], TEAL)
    stage(42.5, 60, 34.5, 36, "2", "Syntactic Validation", "DELIVERED",
          ["Forward Causal Triggers", "Passive Inversion Rules", "Agent-Nominal Patterns", "Strict Negation Quarantining"], TEAL)
    stage(81, 60, 34.5, 36, "3", "Context Resolution", "DELIVERED",
          ["Demonstrative Anaphora", "Abbreviation Normalization", "Discourse Connectives", "Dual-Sentence Alignment"], TEAL)
    stage(119.5, 60, 34.5, 36, "4", "Multi-Page Linking", "0.5350 F1",
          ["Bounded Multi-Hop (<= 2 hops)", "Domain-Invariant Pruning", "Reverse Regulator Gating", "Confidence Compounding"], BLUE)
    for x1, x2 in [(38.5, 42.5), (77, 81), (115.5, 119.5)]:
        arrow(ax, x1, 78, x2, 78)

    def panel(x, ttl, badge, items, col):
        box(ax, x, 4, 68, 46, PANEL, col, 1.3)
        band(ax, x, 50, 68, 8.5, col)
        ax.text(x + 2.5, 45.75, ttl, ha="left", va="center", fontsize=10, fontweight="bold", color=INK, zorder=4)
        tag(ax, x + 65.5, 45.75, badge, col, fs=8.2, ec=col, ha="right")
        bullets(ax, x + 2.5, 38, items, wrap=82, fs=9.4, gap=2.6)

    panel(4, "Strict False-Positive Controls & Domain Invariants", "ACTIVE INVARIANTS", [
        "Terminal Phenotype Invariant: Virulence and survival cannot cause upstream regulatory genes",
        "Environmental Invariant: Extracellular conditions (pH, temp) cannot be transcriptionally activated",
        "Homology & Method Gate: Non-causal cloning, homologue analogies, and methods suppressed",
        "Relative Clause Barrier: Suppresses spurious cross-clause entity-trigger associations",
        "Master Regulator Directionality: Restricts reverse feedback loops (InvF -> HilA, EspA -> PhoP)",
    ], BLUE)
    panel(84, "5. Provenance Grounding & Verification", "VERIFIED (100%)", [
        "Dual-Sentence Evidence Tracking: Verbatim [S_causal, S_entity] bindings with zero hallucination",
        "Calibrated Confidence Metric: Empirical Platt-scaled posterior precision score in [0.0, 1.0]",
        "Full Text Auditability: Exact character indices [c_start, c_end] and physical page numbers",
        "Selective Prediction Abstention: Rejection threshold tau = 0.45 for uncertain assertions",
        "Cryptographic Integrity: Frozen SHA-256 ground-truth ledger across all 20 benchmark papers",
    ], TEAL)

    # Vertical connectors (labels sit beside the line, never on top of it)
    for cx, lbl in [(59.75, "Direction Check"), (98.25, "Dual Spans [Sc, Se]"), (136.75, "Transitive Paths")]:
        arrow(ax, cx, 60, cx, 50)
        tag(ax, cx + 1.6, 55, lbl, INK, fs=8.4, ha="left")
    arrow(ax, 72, 25, 84, 25)
    tag(ax, 78, 28.4, "Gated", INK, fs=8.6)

    title(ax, "EVRYN Multi-Stage Causal Extraction Workflow & Modular Verification Architecture")
    save_fig(fig, "fig2_extraction_workflow")


# ==============================================================================
# Figure 3.1: Evidence Grounding and Causal Directionality
# ==============================================================================
def generate_fig3_evidence_direction():
    fig, ax = canvas(156, 98)

    def entity_card(x, y, w, h, ttl, lines, col):
        box(ax, x, y, w, h, PANEL, col, 1.4)
        band(ax, x, y + h, w, 5, col)
        ax.text(x + w / 2, y + h - 2.5, ttl, ha="center", va="center", fontsize=10.4,
                fontweight="bold", color=col, zorder=4)
        ty = y + h - 8.2
        for ln in lines:
            ax.text(x + 2.5, ty, ln, ha="left", va="top", fontsize=9.2, color=INK2, zorder=4)
            ty -= 4.3

    entity_card(5, 66, 38, 25, "Cause Entity (C)", [
        "Canonical: PmrB", "Mention: \"PmrB sensor kinase\"",
        "Entity Type: Sensor Kinase / Protein", "Section: Results | Page: 2"], TEAL)
    entity_card(113, 66, 38, 25, "Effect Entity (E)", [
        "Canonical: PmrA", "Mention: \"response regulator PmrA\"",
        "Entity Type: Response Regulator / Protein", "Section: Results | Page: 3"], TEAL)

    arrow(ax, 43, 78, 113, 78, lw=2.2)
    tag(ax, 78, 84.5, "RELATION: DIRECT_CAUSE (+)", TEAL, fs=11, ec=TEAL, lw=1.0)
    tag(ax, 78, 71.5, "Direction: FORWARD   |   Confidence: 0.95   |   Polarity: POSITIVE", MUTE, fs=9.2)

    # Evidence box
    box(ax, 5, 37, 146, 24, WHITE, BLUE, 1.4)
    band(ax, 5, 61, 146, 5, BLUE, 1.2)
    ax.text(8, 58.5, "Primary Evidence Sentence & Verbatim Provenance Coordinates (S_causal)",
            ha="left", va="center", fontsize=10.2, fontweight="bold", color=BLUE, zorder=4)
    ax.text(148, 58.5, "100% PROVENANCE VERIFIED", ha="right", va="center", fontsize=8.8,
            fontweight="bold", color=TEAL, zorder=4)
    box(ax, 8, 44.2, 140, 9.6, BAND, "#94A3B8", 0.9, z=3)
    ax.text(78, 49, "\"Acid pH activates the PmrA/PmrB system by promoting PmrB-mediated phosphorylation of PmrA.\"",
            ha="center", va="center", fontsize=9.8, fontstyle="italic", color=INK, zorder=4)
    ax.text(78, 40.6,
            "Doc ID: PMC1804205  |  Section: RESULTS  |  Paragraph: 14  |  Sentence ID: s42  |  Offsets: [1420\u20131512]  |  Page: 2",
            ha="center", va="center", fontsize=9.0, fontweight="bold", color=MUTE, zorder=4)

    # Downward connectors; labels beside the line
    for cx, lbl in [(28, "Intra-Sentence Context"), (78, "Anaphoric Context Resolution"), (128, "Transitive Multi-Hop Linking")]:
        arrow(ax, cx, 37, cx, 29, col=SLATE, lw=1.3, ls="--", z=3)
        tag(ax, cx + 1.6, 33, lbl, INK2, fs=8.6, ha="left", lw=0.7)

    def typology(x, ttl, sub, items, col):
        y, w, h = 3, 46, 26
        box(ax, x, y, w, h, WHITE, col, 1.3)
        band(ax, x, y + h, w, 6, col)
        ax.text(x + 2.5, y + h - 3, ttl, ha="left", va="center", fontsize=9.6, fontweight="bold", color=col, zorder=4)
        ax.text(x + w - 2.5, y + h - 3, sub, ha="right", va="center", fontsize=8.4, color=SLATE, zorder=4)
        ty = y + h - 9.4
        for it in items:
            ax.text(x + 2.5, ty, f"\u2022 {it}", ha="left", va="top", fontsize=9.0, color=INK2, zorder=4)
            ty -= 4.1

    typology(5, "1. Direct Intra-Sentence Assertion", "Single Sentence", [
        "Both C & E co-occur in S_causal boundary",
        "Syntactic trigger: \"activation of\", \"induces\"",
        "Coordinates: <p.2, Results, [1420\u20131512]>",
        "High empirical precision (0.90\u20130.98 on gold)"], TEAL)
    typology(55, "2. Context-Resolved Candidate", "Cross-Sentence", [
        "Inter-sentence alignment across [S_k, S_k+1]",
        "Demonstrative pronoun & anaphora resolution",
        "Dual provenance binding: [S_cause, S_effect]",
        "Abbreviation expansion via domain normalizer"], BLUE)
    typology(105, "3. Multi-Page Transitive Link", "Multi-Page Graph", [
        "Path traversal: A -> B (p.2) -> C (p.8)",
        "Inter-page distance: \u0394p >= 1, hops <= 2",
        "Pruned by domain invariants (TCSTS_REVERSE_PAIRS)",
        "Distance decay: conf = prod(c_i) * \u03bb^d"], AMBER)

    title(ax, "EVRYN Evidence Grounding Contract: Dual-Span Provenance & Causal Directionality")
    save_fig(fig, "fig3_evidence_direction")


# ==============================================================================
# Figure 5.1: Benchmark Split Architecture & Zero-Leakage Isolation
# ==============================================================================
def generate_fig4_evaluation_workflow():
    fig, ax = canvas(156, 102)

    def split_card(x, ttl, sub, papers, items, col):
        y, w, h = 28, 29, 56
        box(ax, x, y, w, h, WHITE, col, 1.4)
        band(ax, x, y + h, w, 6, col)
        ax.text(x + w / 2, y + h - 3, ttl, ha="center", va="center", fontsize=9.8, fontweight="bold", color=col, zorder=4)
        ty = y + h - 8.8
        for s in sub:
            ax.text(x + w / 2, ty, s, ha="center", va="center", fontsize=8.8, fontweight="bold", color=MUTE, zorder=4)
            ty -= 2.3
        pb_top, pb_h = y + h - 13.6, 18.6
        box(ax, x + 1.5, pb_top - pb_h, w - 3, pb_h, PANEL, RULE, 0.9, z=3)
        ax.text(x + 2.8, pb_top - 1.0, "Papers (pages):", ha="left", va="top", fontsize=8.6, fontweight="bold", color=MUTE, zorder=4)
        py = pb_top - 3.9
        for p in papers:
            ax.text(x + 2.8, py, p, ha="left", va="top", fontsize=8.8, color=INK, zorder=4)
            py -= 1.75
        by = pb_top - pb_h - 3.2
        for b in items:
            ax.text(x + 2.5, by, f"\u2022 {b}", ha="left", va="top", fontsize=9.0, color=INK2, zorder=4)
            by -= 4.4

    # Development zone
    box(ax, 4, 25, 66, 70, PANEL, TEAL, 1.4, z=1)
    ax.text(37, 91, "DEVELOPMENT & TUNING ZONE (Permitted Model Calibration)", ha="center", va="center",
            fontsize=9.8, fontweight="bold", color=TEAL, zorder=2)
    split_card(6.5, "Train Split (4 Papers)", ["35 Gold Relations", "(19 Direct, 16 Cross)"],
               ["PMC2651894 (p. 5)", "PMC2682197 (p. 12)", "PMC2714965 (p. 12)", "PMC2774163 (p. 13)"],
               ["Grammar & trigger discovery", "Syntactic pattern mining", "Rule & invariant calibration", "Strictly isolated from test"], TEAL)
    split_card(38.5, "Dev Split (8 Papers)", ["71 Gold Relations", "(36 Direct, 35 Cross)"],
               ["PMC1804205 (p. 7)", "PMC1874608 (p. 12)", "PMC1913099 (p. 16)", "PMC1974823 (p. 7)",
                "PMC2242835 (p. 10)", "PMC2266911 (p. 12)", "PMC2358977 (p. 12)", "PMC2430206 (p. 10)"],
               ["Error census & FP diagnosis", "Threshold tuning (tau = 0.60)", "Criterion 5 verified (0.5350 F1)", "TCSTS reverse-edge gating"], TEAL)

    # Zero-leakage gate (light fill, no hatching, no box-drawing glyphs)
    box(ax, 72, 25, 12, 70, BAND, MUTE, 1.5, z=2)
    gate = [("ZERO", 1), ("LEAKAGE", 1), ("RELEASE", 1), ("GATE", 1), None,
            ("Code & Rules", 1), ("Frozen Prior", 0), ("to Confirmatory", 0), ("Evaluation", 0), None,
            ("Zero Feedback", 1), ("Zero Leakage", 1)]
    gy = 89
    for g in gate:
        if g is None:
            ax.plot([74.2, 81.8], [gy + 0.2, gy + 0.2], color=SLATE, lw=0.9, zorder=4)
            gy -= 2.8
            continue
        ax.text(78, gy, g[0], ha="center", va="center", fontsize=8.4,
                fontweight="bold" if g[1] else "normal", color=INK if g[1] else MUTE, zorder=4)
        gy -= 4.4

    # Confirmatory zone
    box(ax, 86, 25, 66, 70, BAND, BLUE, 1.4, z=1)
    ax.text(119, 91, "CONFIRMATORY EVALUATION ZONE (Strictly Held-Out & Blind)", ha="center", va="center",
            fontsize=9.8, fontweight="bold", color=BLUE, zorder=2)
    split_card(88.5, "Locked Test (4 Papers)", ["41 Gold Relations", "(21 Direct, 20 Cross)"],
               ["PMC2565068 (p. 9)", "PMC2581603 (p. 10)", "PMC2593050 (p. 5)", "PMC2639726 (p. 14)"],
               ["Single post-hoc evaluation", "Confirmatory generalization", "Frozen model parameters", "Zero hyperparameter tuning"], BLUE)
    split_card(120.5, "External Unseen (4 Papers)", ["36 Gold Relations", "(20 Direct, 16 Cross)"],
               ["PMC2816692 (p. 10)", "PMC2829055 (p. 9)", "PMC2858072 (p. 8)", "PMC2885601 (p. 6)"],
               ["Unseen pathogen genetics", "Authenticated V2 ground truth", "Out-of-domain evaluation", "Zero tuning feedback"], INDIGO)

    # Ledger
    box(ax, 4, 3, 148, 19, WHITE, "#94A3B8", 1.3, z=2)
    band(ax, 4, 22, 148, 4.6, "#94A3B8", 1.0)
    ax.text(78, 19.7, "Benchmark Ground-Truth Ledger & Annotation Audit Protocol (20 Papers, 183 Gold Causal Relations)",
            ha="center", va="center", fontsize=9.8, fontweight="bold", color=INK, zorder=4)

    box(ax, 6, 4.8, 70, 11.4, "#FFFBEB", AMBER, 0.9, z=3)
    ax.text(7.5, 14.4, "Legacy Benchmark V1 (Unaligned Metadata):", ha="left", va="center", fontsize=8.8, fontweight="bold", color="#92400E", zorder=4)
    ax.text(7.5, 11.3, "\u2022 PMC2816692: title registered as Anthrax LF while XML described Salmonella SrcA", ha="left", va="center", fontsize=8.5, color="#78350F", zorder=4)
    ax.text(7.5, 8.2, "\u2022 54 false positives on External split; Direct F1 = 0.3269, Cross F1 = 0.2548", ha="left", va="center", fontsize=8.5, color="#78350F", zorder=4)

    box(ax, 80, 4.8, 70, 11.4, "#F0FDFA", TEAL, 0.9, z=3)
    ax.text(81.5, 14.4, "Authenticated Benchmark V2 (Audited Ground Truth):", ha="left", va="center", fontsize=8.8, fontweight="bold", color="#0F766E", zorder=4)
    ax.text(81.5, 11.3, "\u2022 PMC2816692: aligned to authentic SrcA/PipB2/SseL mechanisms (15 false positives)", ha="left", va="center", fontsize=8.5, color="#134E4A", zorder=4)
    ax.text(81.5, 8.2, "\u2022 183 gold relations (96 Direct, 87 Cross); Ext Direct F1 = 0.4808, Cross F1 = 0.3262", ha="left", va="center", fontsize=8.5, color="#134E4A", zorder=4)

    title(ax, "EVRYN 20-Paper Benchmark Partition and Strict Zero-Leakage Evaluation Protocol")
    save_fig(fig, "fig4_evaluation_workflow")


# ==============================================================================
# Figure 5.2: Verified Results Across Evaluation Splits
# ==============================================================================
def generate_fig6_results_progression():
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15.0, 5.6), dpi=300)
    splits = ["Train\n(4 papers)", "Dev\n(8 papers)", "Locked\n(4 papers)", "Ext V1\n(4 papers)", "Ext V2\n(4 papers)"]

    direct_f1 = [0.4958, 0.6820, 0.5584, 0.3269, 0.4808]
    d_lo = [0.4958 - 0.3667, 0.6820 - 0.5805, 0.5584 - 0.3542, 0.3269 - 0.1000, 0.4808 - 0.3538]
    d_hi = [0.6625 - 0.4958, 0.7757 - 0.6820, 0.7279 - 0.5584, 0.5269 - 0.3269, 0.6077 - 0.4808]
    cross_f1 = [0.2000, 0.5350, 0.2625, 0.2548, 0.3262]
    c_lo = [0.2000 - 0.0000, 0.5350 - 0.3037, 0.2625 - 0.1000, 0.2548 - 0.0833, 0.3262 - 0.2857]
    c_hi = [0.4000 - 0.2000, 0.7640 - 0.5350, 0.4000 - 0.2625, 0.3714 - 0.2548, 0.3714 - 0.3262]
    match_ratio = [0.2510, 0.4979, 0.2978, 0.1863, 0.2696]

    x = np.arange(len(splits))
    colors = ["#94A3B8", TEAL, BLUE, RULE, INDIGO]
    ekw = dict(lw=1.2, capthick=1.2, ecolor=INK)

    def annotate(ax, bars, vals, tops, off):
        for bar, v, t in zip(bars, vals, tops):
            ax.text(bar.get_x() + bar.get_width() / 2, t + off, f"{v:.4f}", ha="center", va="bottom",
                    fontsize=9.6, fontweight="bold", color=INK)

    b1 = ax1.bar(x, direct_f1, yerr=[d_lo, d_hi], capsize=5, color=colors, edgecolor=INK, width=0.55, linewidth=1.1, error_kw=ekw, zorder=3)
    ax1.set_ylabel("Direct Causal F1", fontweight="bold", fontsize=11.5, color=INK)
    ax1.set_title("Direct Relation F1 (95% CI)", fontweight="bold", fontsize=12.5, pad=10)
    ax1.set_ylim(0, 0.98)
    annotate(ax1, b1, direct_f1, [v + h for v, h in zip(direct_f1, d_hi)], 0.02)

    b2 = ax2.bar(x, cross_f1, yerr=[c_lo, c_hi], capsize=5, color=colors, edgecolor=INK, width=0.55, linewidth=1.1, error_kw=ekw, zorder=3)
    ax2.set_ylabel("Cross-Page Causal F1", fontweight="bold", fontsize=11.5, color=INK)
    ax2.set_title("Cross-Page Relation F1 (95% CI)", fontweight="bold", fontsize=12.5, pad=10)
    ax2.set_ylim(0, 0.98)
    ax2.axhline(0.50, color=AMBER, linestyle="--", linewidth=1.4, label="Phase 1 Threshold (0.50)", zorder=2)
    ax2.legend(loc="upper right", frameon=True, facecolor="white", edgecolor=RULE, fontsize=9.6)
    annotate(ax2, b2, cross_f1, [v + h for v, h in zip(cross_f1, c_hi)], 0.02)

    b3 = ax3.bar(x, match_ratio, color=colors, edgecolor=INK, width=0.55, linewidth=1.1, zorder=3)
    ax3.set_ylabel("Exact Structural Match Ratio", fontweight="bold", fontsize=11.5, color=INK)
    ax3.set_title("Exact Structural Match Ratio", fontweight="bold", fontsize=12.5, pad=10)
    ax3.set_ylim(0, 0.60)
    annotate(ax3, b3, match_ratio, match_ratio, 0.012)

    for ax in (ax1, ax2, ax3):
        ax.set_xticks(x)
        ax.set_xticklabels(splits, fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.5, color=RULE, zorder=0)
        ax.set_axisbelow(True)

    fig.suptitle("EVRYN Phase 1.13 Verified Benchmark Metrics Across Isolated Splits",
                 fontsize=14.0, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, "fig6_results_progression")


# ==============================================================================
# Figure 5.3: Error Analysis Taxonomy
# ==============================================================================
def generate_fig5_error_analysis():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.2, 5.8), dpi=300)

    def panel(ax, cats, counts, cols, ylab, ttl, ylim, off, edge, summary_title):
        total = sum(counts)
        pcts = [c / total * 100 for c in counts]
        bars = ax.bar(cats, counts, color=cols, edgecolor=INK, width=0.52, linewidth=1.1, zorder=3)
        ax.set_ylabel(ylab, fontweight="bold", fontsize=11.5, color=INK)
        ax.set_title(ttl, fontweight="bold", fontsize=12.5, pad=12)
        ax.set_ylim(0, ylim)
        ax.grid(axis="y", linestyle="--", alpha=0.5, color=RULE, zorder=0)
        ax.set_axisbelow(True)
        for bar, c, p in zip(bars, counts, pcts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + off, f"{c} ({p:.1f}%)",
                    ha="center", va="bottom", fontsize=10, fontweight="bold", color=INK)
        names = [t.replace("\n", " ") for t in cats]
        body = "\n".join(f"\u2022 {n}: {p:.1f}%" for n, p in zip(names, pcts))
        ax.text(0.97, 0.97, f"{summary_title} ({total} Cases):\n{body}", transform=ax.transAxes,
                ha="right", va="top", multialignment="left", fontsize=9.2, color=INK, zorder=5, linespacing=1.35,
                bbox=dict(boxstyle="square,pad=0.45", fc=PANEL, ec=edge, lw=1.1))

    panel(ax1, ["Multi-Complex\nAssembly", "Implicit\nPromoters", "Multi-Hop\nHypoxia", "Negative\nFeedback"],
          [10, 9, 6, 4], [TEAL, "#14B8A6", "#2DD4BF", "#99F6E4"], "False Negative Count",
          "False Negative Census (29 FNs in Benchmark V2)", 15.5, 0.35, TEAL, "FN Census Summary")
    panel(ax2, ["Experimental\nControls", "Co-occurring\nRegulators", "Assay\nReagents", "Broad\nPhenotypes"],
          [28, 24, 14, 10], [BLUE, "#3B82F6", "#60A5FA", "#93C5FD"], "False Positive Count",
          "False Positive Taxonomy (76 FPs in Benchmark V2)", 40, 0.8, BLUE, "FP Taxonomy Summary")

    fig.suptitle("EVRYN Error Analysis: Systematic Census of Remaining Extraction Failures",
                 fontsize=13.8, fontweight="bold", y=1.01)
    fig.tight_layout()
    save_fig(fig, "fig5_error_analysis")


# ==============================================================================
# Figure 5.4: Continual SCM Adaptation and Higher-Order Recovery
# ==============================================================================
def generate_fig7_continual_and_higher_order():
    tasks_x = np.arange(1, 9)
    em_acc = np.array([1.0, 1.0, 0.67, 0.75, 0.80, 0.83, 0.71, 0.75])
    scratch_acc = np.array([1.0, 0.50, 0.67, 0.50, 0.60, 0.67, 0.57, 0.625])
    methods = ["Pairwise\nFLUX", "HCAM\nBase", "HO-FLUX\n(Base)", "HO-FLUX\n(+\u0394R\u00b2+HSIC)", "Order-3\n(Triplets)"]
    ho_scores = [0.333, 0.540, 0.583, 0.633, 0.850]
    ho_colors = ["#94A3B8", SLATE, "#3B82F6", BLUE, TEAL]
    mechs = ["Mixed", "Multiplic.", "Three-Way", "GP Non-P.", "Nonlinear", "Confound."]
    mech_vals = [1.000, 0.950, 0.950, 0.450, 0.350, 0.283]
    mech_colors = [TEAL, "#14B8A6", BLUE, "#F59E0B", AMBER, "#B45309"]

    def draw_continual(ax, lw_em, ms_em, ms_sc, legend_fs, callout_fs, final_tag=""):
        ax.plot(tasks_x, em_acc, "o-", color=TEAL, linewidth=lw_em, markersize=ms_em,
                label=f"FLUX Evidence Matching ({final_tag}75.0%)", zorder=4)
        ax.plot(tasks_x, scratch_acc, "s--", color=AMBER, linewidth=lw_em - 0.5, markersize=ms_sc,
                label=f"Scratch Baseline ({final_tag}62.5%)", zorder=3)
        ax.axhline(0.50, color=SLATE, linestyle=":", linewidth=1.3, label="Random Guess (50.0%)", zorder=2)
        ax.set_ylim(0.40, 1.08)
        ax.set_xticks(tasks_x)
        ax.set_ylabel("Cumulative Accuracy", fontweight="bold", fontsize=11, color=INK)
        ax.set_xlabel("Sequential SCM Tasks", fontweight="bold", fontsize=11, color=INK)
        ax.grid(True, linestyle="--", alpha=0.5, color=RULE)
        # legend BELOW the axes so it never sits on top of the curves
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=1, frameon=True,
                  facecolor="white", edgecolor=RULE, fontsize=legend_fs)
        ax.text(0.97, 0.97, "Backward Transfer: 0.00%\n(Zero Catastrophic Forgetting)", transform=ax.transAxes,
                ha="right", va="top", multialignment="left", fontsize=callout_fs, fontweight="bold", color=TEAL,
                bbox=dict(boxstyle="square,pad=0.35", fc=PANEL, ec=TEAL, lw=0.9), zorder=6)

    def draw_ho(ax, fs_val):
        bars = ax.bar(range(len(methods)), ho_scores, color=ho_colors, edgecolor=INK, width=0.55, linewidth=1.1, zorder=3)
        ax.set_xticks(range(len(methods)))
        ax.set_xticklabels([m.replace("\n", " ") for m in methods], rotation=25, ha="right", fontsize=9.6)
        ax.set_ylabel("Recovery F1 Score", fontweight="bold", fontsize=11, color=INK)
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", linestyle="--", alpha=0.5, color=RULE, zorder=0)
        ax.set_axisbelow(True)
        for b, v in zip(bars, ho_scores):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}", ha="center", va="bottom",
                    fontsize=fs_val, fontweight="bold", color=INK)

    def draw_mech(ax, ylabel, fs_val):
        bars = ax.bar(mechs, mech_vals, color=mech_colors, edgecolor=INK, width=0.55, linewidth=1.1, zorder=3)
        ax.set_ylabel(ylabel, fontweight="bold", fontsize=11, color=INK)
        ax.set_ylim(0, 1.15)
        ax.set_xticks(range(len(mechs)))
        ax.set_xticklabels(mechs, rotation=25, ha="right", fontsize=9.6)
        ax.grid(axis="y", linestyle="--", alpha=0.5, color=RULE, zorder=0)
        ax.set_axisbelow(True)
        for b, v in zip(bars, mech_vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.2f}", ha="center", va="bottom",
                    fontsize=fs_val, fontweight="bold", color=INK)

    # Combined 3-panel figure
    fig = plt.figure(figsize=(15.2, 6.4), dpi=300)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1.0, 1.0], wspace=0.30)
    a1, a2, a3 = (fig.add_subplot(gs[i]) for i in range(3))
    draw_continual(a1, 2.4, 7, 6, 9.4, 8.8)
    a1.set_title("Continual SCM Adaptation", fontweight="bold", fontsize=12.5, pad=10)
    draw_ho(a2, 9.4)
    a2.set_title("Higher-Order Recovery vs Baselines", fontweight="bold", fontsize=12.5, pad=10)
    draw_mech(a3, "Specific Recovery Rate", 9.2)
    a3.set_title("Mechanism-Specific Generalization", fontweight="bold", fontsize=12.5, pad=10)
    fig.suptitle("EVRYN Continual SCM Adaptation and Multivariate Higher-Order Interaction Recovery",
                 fontsize=13.8, fontweight="bold", y=1.0)
    save_fig(fig, "fig7_continual_and_higher_order")

    # Standalone continual figure
    fig_c, ax_c = plt.subplots(figsize=(10.5, 5.8), dpi=300)
    draw_continual(ax_c, 2.4, 8, 7, 10, 9.5, final_tag="Final: ")
    ax_c.set_title("Continual Causal Discovery under Causality in Flux (8 Tasks)", fontsize=13, fontweight="bold", pad=12)
    save_fig(fig_c, "continual_flux_results")

    # Standalone higher-order figure
    fig_h, (h1, h2) = plt.subplots(1, 2, figsize=(13.5, 5.4), dpi=300)
    draw_ho(h1, 9.4)
    h1.set_title("Higher-Order Causal Recovery vs Baselines", fontweight="bold", fontsize=12.5, pad=12)
    draw_mech(h2, "Recovery F1 Score", 9.2)
    h2.set_title("Mechanism-Specific Generalization", fontweight="bold", fontsize=12.5, pad=12)
    fig_h.suptitle("Multivariate Higher-Order Mechanism Recovery", fontsize=13.5, fontweight="bold", y=1.02)
    fig_h.tight_layout()
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
    
    # Generate final-print-size figures (6.3 in / 3.05 in subfigures)
    import subprocess
    import sys
    rep_script = os.path.join(os.path.dirname(__file__), "generate_report_figures.py")
    if os.path.exists(rep_script):
        subprocess.run([sys.executable, rep_script], check=True)

    print("All publication and report figures successfully regenerated.")


if __name__ == "__main__":
    main()
