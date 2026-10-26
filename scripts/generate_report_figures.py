#!/usr/bin/env python3
"""Report figures drawn at FINAL PRINT SIZE (text width 6.3 in, subfigures 3.05 in)
so fonts are never shrunk by LaTeX. Include with width=\\textwidth (or 0.48\\textwidth
for the two Fig 5.3 panels). Few words, large type."""
import os
import shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as P
import numpy as np

DEFAULT_DIRS = [
    "/home/tk/projects/phase1_report/figures",
    "/home/tk/projects/phase1_presentation/figures",
    "/home/tk/projects/evryn/docs/phase1/figures",
]
OUTPUT_DIRS = [d for d in os.environ.get("EVRYN_FIG_DIRS", os.pathsep.join(DEFAULT_DIRS)).split(os.pathsep) if d]
for d in OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

INK, MUTE, SLATE, RULE = "#0F172A", "#475569", "#64748B", "#CBD5E1"
PANEL, BAND, TEAL, BLUE, AMBER, GREY = "#F8FAFC", "#F1F5F9", "#0D9488", "#2563EB", "#D97706", "#94A3B8"

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 10.5,
    "axes.linewidth": 0.8, "pdf.fonttype": 42,
})
W = 6.3  # text width in inches


def save(fig, name):
    first = OUTPUT_DIRS[0]
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(first, f"{name}.{ext}"), dpi=300)  # no bbox=tight: keep exact size
        for d in OUTPUT_DIRS[1:]:
            shutil.copyfile(os.path.join(first, f"{name}.{ext}"), os.path.join(d, f"{name}.{ext}"))
    plt.close(fig)
    print("saved", name)


def sheet(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ---- Fig 1.1 ----------------------------------------------------------------
def scope():
    fig, ax = sheet(W, 2.3)
    w, gap, x0 = 1.82, 0.36, 0.04
    cols = [
        ("PHASE 1", "CURRENT", "Causal Extraction", ["Multi-page parsing", "Causal extraction", "100% provenance"], TEAL, PANEL),
        ("PHASE 2", "NEXT", "Corpus Transfer", ["25-year corpus", "Mechanism drift", "Continual adaptation"], BLUE, "white"),
        ("PHASE 3", "FUTURE", "Discovery Prediction", ["Link forecasting", "Hypothesis ranking", "Prospective tests"], SLATE, "white"),
    ]
    y, h = 0.1, 2.1
    for i, (ph, st, ttl, items, col, bg) in enumerate(cols):
        x = x0 + i * (w + gap)
        ax.add_patch(P.Rectangle((x, y), w, h, fc=bg, ec=col, lw=1.4))
        ax.add_patch(P.Rectangle((x, y + h - 0.78), w, 0.78, fc=BAND, ec=col, lw=1.1))
        ax.text(x + 0.12, y + h - 0.22, ph, fontsize=10.5, fontweight="bold", color=col, va="center")
        ax.text(x + w - 0.1, y + h - 0.22, st, fontsize=8.5, fontweight="bold", color=col, ha="right", va="center",
                bbox=dict(boxstyle="square,pad=0.22", fc="white", ec=col, lw=0.8))
        ax.text(x + 0.12, y + h - 0.57, ttl, fontsize=11, fontweight="bold", color=INK, va="center")
        for j, t in enumerate(items):
            ax.text(x + 0.12, y + h - 1.1 - j * 0.34, "\u2022 " + t, fontsize=10.5, color=INK, va="center")
        if i < 2:
            ax.annotate("", xy=(x + w + gap - 0.05, y + h / 2), xytext=(x + w + 0.05, y + h / 2),
                        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5))
    save(fig, "research_scope")


# ---- Fig 4.1 ----------------------------------------------------------------
def architecture():
    fig, ax = sheet(W, 2.0)
    names = ["Ingestion", "Segmentation", "Normalization", "Extraction", "Linking &\nVerification"]
    cols = [TEAL, TEAL, TEAL, BLUE, BLUE]
    w, gap, x0, y, h = 1.08, 0.2, 0.05, 0.95, 0.98
    for i, (n, c) in enumerate(zip(names, cols)):
        x = x0 + i * (w + gap)
        ax.add_patch(P.Rectangle((x, y), w, h, fc=PANEL, ec=c, lw=1.4))
        ax.text(x + w / 2, y + h - 0.2, str(i + 1), fontsize=10, fontweight="bold", color=c, ha="center", va="center")
        ax.text(x + w / 2, y + 0.36, n, fontsize=10, fontweight="bold", color=INK, ha="center", va="center", linespacing=1.15)
        if i < 4:
            ax.annotate("", xy=(x + w + gap - 0.01, y + h / 2), xytext=(x + w + 0.01, y + h / 2),
                        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.4, shrinkA=0, shrinkB=0))
    ax.add_patch(P.Rectangle((x0, 0.1), 5 * w + 4 * gap, 0.58, fc="white", ec=TEAL, lw=1.3, ls="--"))
    ax.text(x0 + (5 * w + 4 * gap) / 2, 0.39, "100% provenance grounding", fontsize=11, fontweight="bold",
            color=INK, ha="center", va="center")
    save(fig, "fig1_system_architecture")


# ---- Fig 3.1 ----------------------------------------------------------------
def evidence_direction():
    fig, ax = sheet(W, 3.4)

    # 1. Top row: Cause Entity -> Effect Entity
    ax.add_patch(P.Rectangle((0.05, 2.45), 1.85, 0.90, fc=PANEL, ec=TEAL, lw=1.3))
    ax.text(0.14, 3.18, "Cause Entity (C)", fontsize=10.5, fontweight="bold", color=TEAL, va="center")
    ax.text(0.14, 2.92, "Canonical: PmrB", fontsize=10, fontweight="bold", color=INK, va="center")
    ax.text(0.14, 2.68, "Sensor kinase  •  p. 2", fontsize=9.2, color=MUTE, va="center")

    ax.add_patch(P.Rectangle((4.40, 2.45), 1.85, 0.90, fc=PANEL, ec=TEAL, lw=1.3))
    ax.text(4.49, 3.18, "Effect Entity (E)", fontsize=10.5, fontweight="bold", color=TEAL, va="center")
    ax.text(4.49, 2.92, "Canonical: PmrA", fontsize=10, fontweight="bold", color=INK, va="center")
    ax.text(4.49, 2.68, "Response reg.  •  p. 3", fontsize=9.2, color=MUTE, va="center")

    ax.annotate("", xy=(4.32, 2.90), xytext=(1.98, 2.90),
                arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1.8, shrinkA=0, shrinkB=0))
    ax.text(3.15, 3.14, "DIRECT_CAUSE (+)", fontsize=10, fontweight="bold", color=TEAL, ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.22", fc="white", ec=TEAL, lw=0.9))
    ax.text(3.15, 2.68, "conf = 0.95  •  Forward  •  Results", fontsize=9.2, fontweight="bold", color=SLATE, ha="center", va="center")

    # 2. Middle row: Evidence Sentence & Provenance
    ax.add_patch(P.Rectangle((0.05, 1.48), 6.20, 0.85, fc="white", ec=BLUE, lw=1.3))
    ax.add_patch(P.Rectangle((0.05, 2.05), 6.20, 0.28, fc=BAND, ec="none"))
    ax.text(0.18, 2.19, "Evidence Sentence (S_causal)", fontsize=10, fontweight="bold", color=BLUE, va="center")
    ax.text(6.12, 2.19, "100% PROVENANCE GROUNDED", fontsize=8.8, fontweight="bold", color=TEAL, ha="right", va="center")
    ax.text(3.15, 1.88, "\"Acid pH activates PmrA/PmrB by promoting PmrB-mediated phosphorylation of PmrA.\"",
            fontsize=9.8, fontstyle="italic", color=INK, ha="center", va="center")
    ax.text(3.15, 1.63, "Doc: PMC1804205   •   Section: Results   •   Page: 2   •   Offsets: [1420–1512]",
            fontsize=9.2, fontweight="bold", color=SLATE, ha="center", va="center")

    for cx in (1.02, 3.15, 5.28):
        ax.annotate("", xy=(cx, 1.30), xytext=(cx, 1.48),
                    arrowprops=dict(arrowstyle="-|>", color=SLATE, lw=1.2, ls="--"))

    # 3. Bottom row: Typology cards (3 cards)
    cards = [
        ("1. Direct Assertion", "Single sentence boundary", TEAL, [
            "Co-occurs in single sentence",
            "Trigger: activates, induces",
            "Exact offsets [1420–1512], p. 2",
            "Precision 0.90–0.98 on gold",
        ]),
        ("2. Context-Resolved", "Cross-sentence bridge", BLUE, [
            "Aligned across [S_k, S_k+1] spans",
            "Demonstrative anaphora resolution",
            "Dual-sentence provenance binding",
            "Acronym & synonym mapping",
        ]),
        ("3. Transitive Link", "Multi-page graph traversal", AMBER, [
            "Path: A (p.2) \u2192 B \u2192 C (p.8)",
            "Page \u0394p \u2265 1, hops \u2264 2",
            "Pruned by domain invariants",
            "Calibrated score compounding",
        ]),
    ]

    cw = 1.96
    gaps = [0.05, 2.17, 4.29]
    for (ttl, sub, col, items), x in zip(cards, gaps):
        ax.add_patch(P.Rectangle((x, 0.05), cw, 1.22, fc=PANEL, ec=col, lw=1.2))
        ax.text(x + 0.10, 1.12, ttl, fontsize=9.8, fontweight="bold", color=col, va="center")
        ax.text(x + 0.10, 0.94, sub, fontsize=8.4, color=SLATE, va="center")
        for j, it in enumerate(items):
            ax.text(x + 0.10, 0.73 - j * 0.20, f"\u2022 {it}", fontsize=8.8, color=INK, va="center")

    save(fig, "fig3_evidence_direction")


# ---- Fig 4.2 ----------------------------------------------------------------
def extraction_workflow():
    fig, ax = sheet(W, 3.4)

    stages = [
        ("STAGE 1", "Candidate Gen.", "Delivered", TEAL, [
            "Bio-entity detection",
            "Sentence bounds",
            "Quality filtering",
        ]),
        ("STAGE 2", "Syntactic Parse", "Delivered", TEAL, [
            "Dependency parsing",
            "Causal verb cues",
            "Negation quarantine",
        ]),
        ("STAGE 3", "Context Resolve", "Delivered", TEAL, [
            "Anaphora resolution",
            "Acronym expansion",
            "Cross-sentence bridge",
        ]),
        ("STAGE 4", "Multi-Page Link", "0.5350 F1", BLUE, [
            "Bounded \u2264 2 hops",
            "Inter-page (\u0394p \u2265 1)",
            "Distance decay",
        ]),
    ]

    sw = 1.42
    sgap = 0.18
    sx0 = 0.05
    sy = 1.70
    sh = 1.62

    for i, (stg, ttl, badge, col, items) in enumerate(stages):
        x = sx0 + i * (sw + sgap)
        ax.add_patch(P.Rectangle((x, sy), sw, sh, fc=PANEL, ec=col, lw=1.3))
        ax.add_patch(P.Rectangle((x, sy + sh - 0.52), sw, 0.52, fc=BAND, ec="none"))
        ax.text(x + sw / 2, sy + sh - 0.16, stg, fontsize=9.5, fontweight="bold", color=col, ha="center", va="center")
        ax.text(x + sw / 2, sy + sh - 0.38, ttl, fontsize=10, fontweight="bold", color=INK, ha="center", va="center")

        ax.text(x + sw / 2, sy + sh - 0.68, badge, fontsize=8.2, fontweight="bold", color=col, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.18", fc="white", ec=col, lw=0.7))

        for j, it in enumerate(items):
            ax.text(x + 0.10, sy + sh - 0.96 - j * 0.24, f"\u2022 {it}", fontsize=9.2, color=INK, va="center")

        if i < 3:
            ax.annotate("", xy=(x + sw + sgap - 0.01, sy + sh / 2), xytext=(x + sw + 0.01, sy + sh / 2),
                        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.3, shrinkA=0, shrinkB=0))

    # Connectors to bottom row
    ax.annotate("", xy=(1.55, 1.44), xytext=(1.55, 1.70),
                arrowprops=dict(arrowstyle="-|>", color=SLATE, lw=1.2, ls="--"))
    ax.text(1.63, 1.57, "Syntax & Entities", fontsize=8.5, color=SLATE, va="center")

    ax.annotate("", xy=(4.75, 1.44), xytext=(4.75, 1.70),
                arrowprops=dict(arrowstyle="-|>", color=SLATE, lw=1.2, ls="--"))
    ax.text(4.83, 1.57, "Transitive Paths", fontsize=8.5, color=SLATE, va="center")

    # Bottom Row: 2 Verifier Panels
    panels = [
        ("Domain Invariants", "ACTIVE INVARIANTS", BLUE, 0.05, 3.00, [
            "Terminal phenotypes cannot cause upstream genes",
            "Extracellular pH / temp cannot be activated",
            "Master regulator reverse feedback loops pruned",
            "Homology and cloning mentions suppressed",
        ]),
        ("Calibrated Verification", "100% PROVENANCE", TEAL, 3.25, 3.00, [
            "100% provenance: PMCID, page, offsets, quote",
            "Platt posterior confidence calibration in [0, 1]",
            "Calibrated selective prediction threshold (\u03c4 = 0.60)",
            "Frozen SHA-256 ground-truth benchmark audit",
        ]),
    ]

    py = 0.05
    ph = 1.38
    for pttl, pbadge, pcol, px, pw, pitems in panels:
        ax.add_patch(P.Rectangle((px, py), pw, ph, fc="white", ec=pcol, lw=1.3))
        ax.add_patch(P.Rectangle((px, py + ph - 0.30), pw, 0.30, fc=BAND, ec="none"))
        ax.text(px + 0.12, py + ph - 0.15, pttl, fontsize=10, fontweight="bold", color=pcol, va="center")
        ax.text(px + pw - 0.12, py + ph - 0.15, pbadge, fontsize=8.2, fontweight="bold", color=pcol, ha="right", va="center")
        for j, it in enumerate(pitems):
            ax.text(px + 0.12, py + ph - 0.48 - j * 0.24, f"\u2022 {it}", fontsize=8.9, color=INK, va="center")

    # Connector between Invariants and Provenance
    ax.annotate("", xy=(3.24, py + ph - 0.15), xytext=(3.06, py + ph - 0.15),
                arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1.3, shrinkA=0, shrinkB=0))
    ax.text(3.15, py + ph + 0.08, "Gated", fontsize=8.2, fontweight="bold", color=TEAL, ha="center")

    save(fig, "fig2_extraction_workflow")


# ---- Fig 5.1 ----------------------------------------------------------------
def baselines():
    labels = ["A  Sentence", "B  Paragraph", "C  NPMI", "D  Dense", "EVRYN"]
    direct = [0.4788, 0.5273, 0.3645, 0.1171, 0.4449]
    cross = [0.0000, 0.0000, 0.2546, 0.1989, 0.2657]
    struct = [0.3311, 0.5607, 0.2800, 0.3500, 0.3880]
    fig, axes = plt.subplots(1, 3, figsize=(W, 2.5), sharey=True)
    fig.subplots_adjust(left=0.165, right=0.99, bottom=0.04, top=0.84, wspace=0.08)
    y = np.arange(5)
    cols = [GREY] * 4 + [TEAL]
    for ax, vals, ttl in zip(axes, [direct, cross, struct], ["Direct F$_1$", "Cross-Page F$_1$", "Structural Match"]):
        ax.barh(y, vals, color=cols, edgecolor=INK, linewidth=0.8, height=0.62)
        for yi, v in zip(y, vals):
            ax.text(v + 0.02, yi, f"{v:.2f}", va="center", fontsize=10, fontweight="bold" if yi == 4 else "normal", color=INK)
        ax.set_xlim(0, 0.8)
        ax.set_xticks([])
        ax.set_title(ttl, fontsize=11, fontweight="bold", pad=6)
        clean(ax); ax.spines["bottom"].set_visible(False)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(labels, fontsize=10.5)
    axes[0].get_yticklabels()[4].set_fontweight("bold")
    axes[0].invert_yaxis()
    for ax in axes[1:]:
        ax.tick_params(left=False)
    save(fig, "baseline_comparison")


# ---- Fig 5.2 ----------------------------------------------------------------
def errors():
    fig, ax = plt.subplots(figsize=(W, 2.5))
    fig.subplots_adjust(left=0.04, right=0.99, bottom=0.2, top=0.97)
    before, after = [296, 57], [62, 34]
    x = np.arange(2); bw = 0.3
    b1 = ax.bar(x - bw / 2 - 0.01, before, bw, color=AMBER, edgecolor=INK, linewidth=0.8, label="Before gating")
    b2 = ax.bar(x + bw / 2 + 0.01, after, bw, color=TEAL, edgecolor=INK, linewidth=0.8, label="After gating")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 6, f"{int(b.get_height())}",
                    ha="center", va="bottom", fontsize=11, fontweight="bold", color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(["False transitive jumps\n\u221279.1%", "Missed cross-page links\n\u221240.4%"], fontsize=10.5)
    ax.set_ylim(0, 350); ax.set_xlim(-0.65, 1.65)
    ax.set_yticks([]); clean(ax); ax.spines["left"].set_visible(False)
    ax.tick_params(bottom=False)
    ax.legend(loc="upper right", frameon=False, fontsize=10.5)
    save(fig, "error_distribution")


# ---- Fig 5.3 (a)(b) ---------------------------------------------------------
def continual():
    t = np.arange(1, 9)
    em = [1.0, 1.0, 0.67, 0.75, 0.80, 0.83, 0.71, 0.75]
    sc = [1.0, 0.50, 0.67, 0.50, 0.60, 0.67, 0.57, 0.625]
    fig, ax = plt.subplots(figsize=(3.05, 2.6))
    fig.subplots_adjust(left=0.17, right=0.98, bottom=0.17, top=0.96)
    ax.plot(t, em, "o-", color=TEAL, lw=1.9, ms=4.5, zorder=4)
    ax.plot(t, sc, "s--", color=AMBER, lw=1.6, ms=4, zorder=3)
    ax.axhline(0.5, color=SLATE, ls=":", lw=1.1, zorder=1)
    ax.text(8.3, em[-1], "FLUX\n75%", color=TEAL, fontsize=9.5, fontweight="bold", va="center", linespacing=1.1)
    ax.text(8.3, sc[-1] - 0.01, "Scratch\n62.5%", color=AMBER, fontsize=9.5, fontweight="bold", va="center", linespacing=1.1)
    ax.text(0.97, 0.97, "Backward transfer 0%", transform=ax.transAxes, ha="right", va="top",
            fontsize=9.5, fontweight="bold", color=TEAL)
    ax.set_xlim(0.7, 10.6); ax.set_ylim(0.4, 1.08)
    ax.set_xticks(t); ax.tick_params(labelsize=9.5)
    ax.set_xlabel("Task", fontsize=10.5); ax.set_ylabel("Accuracy", fontsize=10.5)
    clean(ax)
    save(fig, "continual_flux_results")


def higher_order():
    names = ["Pairwise", "HCAM", "HO-FLUX", "HO-FLUX\n+\u0394R$^2$/HSIC"]
    vals = [0.333, 0.540, 0.583, 0.633]
    cols = [GREY, GREY, "#3B82F6", TEAL]
    fig, ax = plt.subplots(figsize=(3.05, 2.6))
    fig.subplots_adjust(left=0.34, right=0.97, bottom=0.17, top=0.96)
    y = np.arange(4)
    ax.barh(y, vals, color=cols, edgecolor=INK, linewidth=0.8, height=0.62)
    for yi, v in zip(y, vals):
        ax.text(v + 0.02, yi, f"{v:.2f}", va="center", fontsize=10, fontweight="bold", color=INK)
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=10); ax.invert_yaxis()
    ax.set_xlim(0, 0.8); ax.set_xticks([0, 0.2, 0.4, 0.6]); ax.tick_params(axis="x", labelsize=9.5)
    ax.set_xlabel("Recovery F$_1$", fontsize=10.5)
    clean(ax)
    save(fig, "higher_order_mechanisms")


if __name__ == "__main__":
    scope()
    evidence_direction()
    architecture()
    extraction_workflow()
    baselines()
    errors()
    continual()
    higher_order()
