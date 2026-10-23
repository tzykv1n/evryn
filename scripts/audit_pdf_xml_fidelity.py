"""
Fidelity Audit Script for EVRYN Benchmark: Source XML vs Rendered-PDF.
Quantifies text extraction fidelity, character/word ratios, vocabulary overlap,
and entity recall across all 20 benchmark papers.
"""

import os
import re
import json
from typing import Dict, List, Any, Set

from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.paper.ingestion import PaperIngestion
from evryn.paper.real_benchmark import CURATED_REAL_PAPERS


def tokenize_words(text: str) -> List[str]:
    return re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())


def compute_jaccard(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a and not set_b:
        return 1.0
    union = set_a.union(set_b)
    if not union:
        return 1.0
    return len(set_a.intersection(set_b)) / len(union)


def run_fidelity_audit(repo_root: str = ".") -> Dict[str, Any]:
    manifest_path = os.path.join(repo_root, "data", "real_papers", "split_manifest.json")
    xml_dir = os.path.join(repo_root, "data", "real_papers", "xml")
    pdf_dir = os.path.join(repo_root, "data", "real_papers", "pdf")
    output_path = os.path.join(repo_root, "results", "phase2_1", "pdf_xml_fidelity_report.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    curated_map = {p["pmcid"]: p for p in CURATED_REAL_PAPERS}
    xml_ingester = PMCOAIngester(cache_dir=xml_dir)
    pdf_ingester = PaperIngestion(remove_hyphenation=True, clean_headers_footers=True)

    paper_reports: List[Dict[str, Any]] = []

    for item in manifest["papers"]:
        pmcid = item["pmcid"]
        split = item["split"]
        pdf_file = os.path.join(pdf_dir, f"{pmcid}.pdf")

        # Ingest XML
        pmc_doc = xml_ingester.ingest_pmcid(pmcid)
        xml_text = pmc_doc.full_text

        # Ingest PDF
        pdf_doc = pdf_ingester.ingest_pdf(pdf_file)
        pdf_text = pdf_doc.full_text

        xml_words = tokenize_words(xml_text)
        pdf_words = tokenize_words(pdf_text)

        xml_word_set = set(xml_words)
        pdf_word_set = set(pdf_words)

        jaccard_vocab = compute_jaccard(xml_word_set, pdf_word_set)

        # Entity recall check
        curated_info = curated_map.get(pmcid, {})
        canonical_entities = curated_info.get("canonical_entities", [])
        
        entities_in_xml = [e for e in canonical_entities if e.lower() in xml_text.lower()]
        entities_in_pdf = [e for e in canonical_entities if e.lower() in pdf_text.lower()]

        entity_recall_xml = len(entities_in_xml) / len(canonical_entities) if canonical_entities else 1.0
        entity_recall_pdf = len(entities_in_pdf) / len(canonical_entities) if canonical_entities else 1.0

        missing_in_pdf = [e for e in canonical_entities if e.lower() not in pdf_text.lower()]

        # Common extraction anomalies
        hyphen_artifacts = len(re.findall(r"\w+-\s+\w+", pdf_text))
        ligature_artifacts = len(re.findall(r"[\ufb00-\ufb06]", pdf_text))

        paper_report = {
            "pmcid": pmcid,
            "title": item["title"],
            "split": split,
            "page_count": pdf_doc.metadata.page_count,
            "xml_char_count": len(xml_text),
            "pdf_char_count": len(pdf_text),
            "char_ratio_pdf_to_xml": round(len(pdf_text) / max(1, len(xml_text)), 4),
            "xml_word_count": len(xml_words),
            "pdf_word_count": len(pdf_words),
            "word_ratio_pdf_to_xml": round(len(pdf_words) / max(1, len(xml_words)), 4),
            "vocab_jaccard_similarity": round(jaccard_vocab, 4),
            "canonical_entities_count": len(canonical_entities),
            "entities_found_in_xml": len(entities_in_xml),
            "entities_found_in_pdf": len(entities_in_pdf),
            "entity_retention_rate_pdf": round(entity_recall_pdf, 4),
            "missing_entities_in_pdf": missing_in_pdf,
            "hyphenation_artifacts": hyphen_artifacts,
            "ligature_artifacts": ligature_artifacts,
        }
        paper_reports.append(paper_report)

    # Compute aggregate metrics
    avg_char_ratio = sum(r["char_ratio_pdf_to_xml"] for r in paper_reports) / len(paper_reports)
    avg_vocab_jaccard = sum(r["vocab_jaccard_similarity"] for r in paper_reports) / len(paper_reports)
    avg_entity_retention = sum(r["entity_retention_rate_pdf"] for r in paper_reports) / len(paper_reports)

    # By split
    by_split: Dict[str, Dict[str, float]] = {}
    for sp in ["train", "dev", "locked_test", "external"]:
        sub = [r for r in paper_reports if r["split"] == sp]
        if sub:
            by_split[sp] = {
                "count": len(sub),
                "avg_char_ratio": round(sum(r["char_ratio_pdf_to_xml"] for r in sub) / len(sub), 4),
                "avg_vocab_jaccard": round(sum(r["vocab_jaccard_similarity"] for r in sub) / len(sub), 4),
                "avg_entity_retention": round(sum(r["entity_retention_rate_pdf"] for r in sub) / len(sub), 4),
            }

    summary = {
        "audit_version": "2.1.0",
        "total_papers_audited": len(paper_reports),
        "overall_averages": {
            "avg_char_ratio_pdf_to_xml": round(avg_char_ratio, 4),
            "avg_vocab_jaccard_similarity": round(avg_vocab_jaccard, 4),
            "avg_entity_retention_pdf": round(avg_entity_retention, 4),
        },
        "by_split": by_split,
        "papers": paper_reports,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Audit completed: {len(paper_reports)} papers audited.")
    print(f"Average PDF/XML char ratio: {avg_char_ratio:.4f}")
    print(f"Average vocab Jaccard similarity: {avg_vocab_jaccard:.4f}")
    print(f"Average canonical entity retention in PDF: {avg_entity_retention:.4f}")
    print(f"Report saved to {output_path}")

    return summary


if __name__ == "__main__":
    run_fidelity_audit()
