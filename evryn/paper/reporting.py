# evryn paper report <pdf_path>
# pytest tests/test_paper_pipeline.py

import os
import json
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import networkx as nx

from .types import (
    ScientificDocument,
    CausalAssertion,
    CrossPageLink,
    PaperCausalGraph,
    EvidenceStatus,
)


class PaperEvidenceReporter:

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(
        self,
        doc: ScientificDocument,
        assertions: List[CausalAssertion],
        cross_page_links: List[CrossPageLink],
        graph: PaperCausalGraph,
        prefix: str = "paper_causal",
    ) -> Dict[str, str]:
        md_path = os.path.join(self.output_dir, f"{prefix}_{doc.doc_id}_report.md")
        json_path = os.path.join(self.output_dir, f"{prefix}_{doc.doc_id}_evidence.json")
        fig_path = os.path.join(self.output_dir, f"{prefix}_{doc.doc_id}_graph.png")

        measured_facts = [a for a in assertions if a.evidence_status == EvidenceStatus.MEASURED_FACT and not a.is_negated]
        hypotheses = [a for a in assertions if a.evidence_status == EvidenceStatus.HYPOTHESIS_CLAIM and not a.is_negated]
        negations = [a for a in assertions if a.is_negated]

        md_content = self._build_markdown(
            doc, assertions, cross_page_links, graph, measured_facts, hypotheses, negations
        )
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        payload = {
            "document": doc.to_dict(),
            "assertions": [a.to_dict() for a in assertions],
            "cross_page_links": [l.to_dict() for l in cross_page_links],
            "graph": graph.to_dict(),
            "summary": {
                "total_pages": doc.metadata.page_count,
                "total_sections": len(doc.sections),
                "total_sentences": len(doc.sentences),
                "total_assertions": len(assertions),
                "measured_facts_count": len(measured_facts),
                "hypotheses_count": len(hypotheses),
                "negated_count": len(negations),
                "cross_page_links_count": len(cross_page_links),
                "graph_nodes_count": len(graph.nodes),
                "graph_edges_count": len(graph.edges),
            },
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        self._render_graph_figure(graph, fig_path)

        return {
            "markdown_report": md_path,
            "json_evidence": json_path,
            "graph_figure": fig_path,
        }

    def _build_markdown(
        self,
        doc: ScientificDocument,
        assertions: List[CausalAssertion],
        cross_page_links: List[CrossPageLink],
        graph: PaperCausalGraph,
        measured_facts: List[CausalAssertion],
        hypotheses: List[CausalAssertion],
        negations: List[CausalAssertion],
    ) -> str:
        lines: List[str] = []
        lines.append(f"# EVRYN Multi-Page Causal Evidence Report: {doc.metadata.title}\n")
        lines.append("## 1. Document Provenance & Metadata\n")
        lines.append(f"- **Document ID**: `{doc.doc_id}`")
        lines.append(f"- **File Path**: `{doc.file_path}`")
        lines.append(f"- **Title**: {doc.metadata.title}")
        if doc.metadata.authors:
            lines.append(f"- **Authors**: {', '.join(doc.metadata.authors)}")
        if doc.metadata.doi:
            lines.append(f"- **DOI**: `{doc.metadata.doi}`")
        if doc.metadata.pmcid:
            lines.append(f"- **PMCID**: `{doc.metadata.pmcid}`")
        if doc.metadata.pmid:
            lines.append(f"- **PMID**: `{doc.metadata.pmid}`")
        lines.append(f"- **Page Count**: {doc.metadata.page_count} pages")
        lines.append(f"- **Parsed Sections**: {len(doc.sections)}")
        lines.append(f"- **Segmented Sentences**: {len(doc.sentences)}\n")

        lines.append("## 2. Executive Causal Summary\n")
        lines.append("| Metric | Count | Description |")
        lines.append("| :--- | :--- | :--- |")
        lines.append(f"| Extracted Causal Assertions | {len(assertions)} | Sentence-level causal assertions identified |")
        lines.append(f"| Measured Experimental Facts | {len(measured_facts)} | Verified direct empirical observations |")
        lines.append(f"| Speculative Hypotheses / Claims | {len(hypotheses)} | Hedged claims in Discussion / Abstract |")
        lines.append(f"| Disproven / Negated Relations | {len(negations)} | Explicitly refuted or non-significant links |")
        lines.append(f"| Cross-Page Evidence Links | {len(cross_page_links)} | Transitive mechanisms spanning across page boundaries |")
        lines.append(f"| Graph Network Entities | {len(graph.nodes)} | Canonical entity nodes in reconstructed causal network |")
        lines.append(f"| Graph Network Edges | {len(graph.edges)} | Direct and synthesized causal transitions |\n")

        lines.append("## 3. Measured Experimental Facts (Empirical Grounding)\n")
        if measured_facts:
            lines.append("| Cause Entity | Effect Entity | Relation Type | Page | Section | Verbatim Evidence Quote |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for a in measured_facts[:15]:
                quote = a.evidence_quote.replace("\n", " ").strip()
                if len(quote) > 100:
                    quote = quote[:97] + "..."
                lines.append(f"| **{a.cause_canonical}** | **{a.effect_canonical}** | `{a.relation_type.value}` | Page {a.page_number} | {a.section_title} | \"{quote}\" |")
            lines.append("")
        else:
            lines.append("_No direct experimental facts detected._\n")

        lines.append("## 4. Cross-Page Synthesized Inferences (Multi-Page Evidence Flow)\n")
        if cross_page_links:
            lines.append("| Source Entity | Intermediate Mediators | Target Entity | Mechanism | Page Span | Confidence |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for link in cross_page_links[:15]:
                inter = link.intermediate_entity if link.intermediate_entity else "-"
                pages_str = f"Page {link.cause_page} → Page {link.effect_page} (Δ={link.distance_pages}p)"
                lines.append(f"| **{link.source_entity}** | {inter} | **{link.target_entity}** | `{link.linking_mechanism}` | {pages_str} | {link.confidence:.3f} |")
            lines.append("")
        else:
            lines.append("_No cross-page transitive links discovered._\n")

        lines.append("## 5. Hypotheses, Speculative Claims & Negations\n")
        if hypotheses or negations:
            lines.append("| Status | Cause | Effect | Page | Section | Evidence Quote |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for a in hypotheses[:10]:
                quote = a.evidence_quote.replace("\n", " ").strip()
                if len(quote) > 90:
                    quote = quote[:87] + "..."
                lines.append(f"| `HYPOTHESIS` | {a.cause_canonical} | {a.effect_canonical} | Page {a.page_number} | {a.section_title} | \"{quote}\" |")
            for a in negations[:10]:
                quote = a.evidence_quote.replace("\n", " ").strip()
                if len(quote) > 90:
                    quote = quote[:87] + "..."
                lines.append(f"| `REFUTED` | {a.cause_canonical} | {a.effect_canonical} | Page {a.page_number} | {a.section_title} | \"{quote}\" |")
            lines.append("")
        else:
            lines.append("_No speculative hypotheses or negations detected._\n")

        lines.append("## 6. Edge Provenance Map\n")
        lines.append("| Edge | Direct / Inferred | Provenance Assertions | Pages |\n| :--- | :--- | :--- | :--- |")
        for e in graph.edges:
            dir_str = "Direct (Sentence)" if e["is_direct"] else "Inferred (Cross-Page)"
            asrt_str = ", ".join(e["assertion_ids"]) if e["assertion_ids"] else "N/A"
            pages_str = ", ".join(f"p.{p}" for p in e["pages"])
            lines.append(f"| **{e['source']}** → **{e['target']}** | {dir_str} | `{asrt_str}` | {pages_str} |")
        lines.append("\n---\n*Report generated deterministically by EVRYN Multi-Page Causal Discovery Engine.*")

        return "\n".join(lines)

    def _render_graph_figure(self, graph: PaperCausalGraph, output_png: str):
        g = nx.DiGraph()
        for node in graph.nodes:
            g.add_node(node["id"], pages=node.get("pages", []))
        for edge in graph.edges:
            g.add_edge(
                edge["source"],
                edge["target"],
                is_direct=edge.get("is_direct", True),
                confidence=edge.get("confidence", 0.5),
                status=edge.get("evidence_status", "MEASURED_FACT"),
            )

        if len(g.nodes) == 0:
            return

        fig, ax = plt.subplots(figsize=(10, 7), dpi=300, layout="constrained")
        pos = nx.spring_layout(g, seed=42, k=1.8 / max(1, len(g.nodes) ** 0.5))

        node_colors = []
        for n in g.nodes():
            pages = g.nodes[n].get("pages", [])
            node_colors.append("#38bdf8" if len(pages) > 1 else "#e2e8f0")

        nx.draw_networkx_nodes(
            g,
            pos,
            ax=ax,
            node_color=node_colors,
            node_size=2400,
            edgecolors="#0f172a",
            linewidths=1.5,
        )

        direct_edges = [(u, v) for u, v, d in g.edges(data=True) if d.get("is_direct", True)]
        inferred_edges = [(u, v) for u, v, d in g.edges(data=True) if not d.get("is_direct", True)]

        if direct_edges:
            nx.draw_networkx_edges(
                g,
                pos,
                edgelist=direct_edges,
                ax=ax,
                edge_color="#059669",
                width=2.5,
                arrowsize=18,
                arrowstyle="-|>",
                connectionstyle="arc3,rad=0.08",
            )
        if inferred_edges:
            nx.draw_networkx_edges(
                g,
                pos,
                edgelist=inferred_edges,
                ax=ax,
                edge_color="#8b5cf6",
                width=2.0,
                style="dashed",
                arrowsize=18,
                arrowstyle="-|>",
                connectionstyle="arc3,rad=0.15",
            )

        nx.draw_networkx_labels(
            g,
            pos,
            ax=ax,
            font_size=9,
            font_family="sans-serif",
            font_weight="bold",
            font_color="#0f172a",
        )

        ax.set_title(
            f"EVRYN Multi-Page Causal Graph: {graph.title[:50]}",
            fontsize=13,
            fontweight="bold",
            pad=15,
            color="#0f172a",
        )

        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color="#059669", lw=2.5, label="Direct Sentence Evidence"),
            Line2D([0], [0], color="#8b5cf6", lw=2.0, ls="--", label="Cross-Page Inferred Chain"),
            Line2D([0], [0], marker="o", color="w", markerfacecolor="#38bdf8", markeredgecolor="#0f172a", markersize=10, label="Multi-Page Entity"),
            Line2D([0], [0], marker="o", color="w", markerfacecolor="#e2e8f0", markeredgecolor="#0f172a", markersize=10, label="Single-Page Entity"),
        ]
        ax.legend(handles=legend_elements, loc="upper right", frameon=True, fontsize=8)
        ax.axis("off")

        plt.savefig(output_png, dpi=300)
        plt.close(fig)
