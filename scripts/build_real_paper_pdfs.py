#!/usr/bin/env python3
"""
Generate publication-quality multi-page PDFs from authentic PubMed Central JATS XMLs
for all 20 real papers in the EVRYN corpus, and generate split_manifest.json with hashes.
"""

import os
import sys
import json
import hashlib
from typing import Dict, List, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether
from reportlab.pdfgen import canvas

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from evryn.datasets.pmc_oa import PMCOAIngester
from evryn.datasets.biocause import BioCauseDataset

SPLIT_ASSIGNMENTS = {
    # 4 Training papers
    "PMC2651894": "train",
    "PMC2682197": "train",
    "PMC2714965": "train",
    "PMC2774163": "train",
    # 8 Development papers
    "PMC1804205": "dev",
    "PMC1874608": "dev",
    "PMC1913099": "dev",
    "PMC1974823": "dev",
    "PMC2242835": "dev",
    "PMC2266911": "dev",
    "PMC2358977": "dev",
    "PMC2430206": "dev",
    # 4 Locked Test papers
    "PMC2565068": "locked_test",
    "PMC2581603": "locked_test",
    "PMC2593050": "locked_test",
    "PMC2639726": "locked_test",
    # 4 External Generalization papers
    "PMC2816692": "external",
    "PMC2829055": "external",
    "PMC2858072": "external",
    "PMC2885601": "external",
}


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header (pages > 1)
        if self._pageNumber > 1:
            header_text = getattr(self, "paper_header", "EVRYN Scientific Causal Discovery")
            self.drawString(54, 750, header_text)
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Running footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, footer_text)
        doi_text = getattr(self, "paper_doi_footer", "Open Access Scientific Literature")
        self.drawString(54, 36, doi_text)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)

        self.restoreState()


def render_pdf_for_paper(doc, output_pdf_path: str):
    doc_template = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PaperTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
    )

    journal_style = ParagraphStyle(
        "JournalHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2563eb"),
        textTransform="uppercase",
        spaceAfter=4,
    )

    author_style = ParagraphStyle(
        "Authors",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    meta_banner_style = ParagraphStyle(
        "MetaBanner",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=14,
    )

    sec_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyText",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        alignment=4,  # Justified
        spaceAfter=8,
    )

    story = []

    # Journal / Source Header
    journal_label = f"{doc.journal.upper()} &bull; OPEN ACCESS &bull; {doc.license_type}"
    story.append(Paragraph(journal_label, journal_style))
    story.append(Spacer(1, 4))

    # Title
    story.append(Paragraph(doc.title, title_style))
    story.append(Spacer(1, 4))

    # Authors
    authors_str = ", ".join(doc.authors) if doc.authors else "Scientific Research Team"
    story.append(Paragraph(f"<b>Authors:</b> {authors_str}", author_style))

    # Metadata Banner
    doi_part = f"DOI: {doc.doi}" if doc.doi else ""
    pmid_part = f"PMID: {doc.pmid}" if doc.pmid else ""
    pmcid_part = f"PMCID: {doc.pmcid}"
    meta_line = " &nbsp;|&nbsp; ".join(p for p in [pmcid_part, pmid_part, doi_part, doc.license_type] if p)
    story.append(Paragraph(meta_line, meta_banner_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

    # Sections & Paragraphs
    for sec in doc.sections:
        story.append(Paragraph(sec.title, sec_heading_style))
        for p in sec.paragraphs:
            safe_text = p.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe_text, body_style))
        story.append(Spacer(1, 6))

    def canvas_maker(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.paper_header = f"{doc.pmcid} &bull; {doc.journal}"
        c.paper_doi_footer = f"PMC: {doc.pmcid} | DOI: {doc.doi or 'N/A'}"
        return c

    doc_template.build(story, canvasmaker=canvas_maker)


def sha256_of_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    xml_dir = os.path.join(REPO_ROOT, "data", "real_papers", "xml")
    pdf_dir = os.path.join(REPO_ROOT, "data", "real_papers", "pdf")
    os.makedirs(pdf_dir, exist_ok=True)

    ingester = PMCOAIngester(cache_dir=xml_dir)
    biocause = BioCauseDataset().load()

    manifest = {
        "version": "2.0.0",
        "description": "EVRYN Real-Paper Causal Benchmark Split Manifest",
        "total_papers": len(SPLIT_ASSIGNMENTS),
        "split_counts": {"train": 0, "dev": 0, "locked_test": 0, "external": 0},
        "papers": [],
    }

    for pmcid, split in sorted(SPLIT_ASSIGNMENTS.items()):
        manifest["split_counts"][split] += 1
        xml_path = os.path.join(xml_dir, f"{pmcid}.xml")
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"Missing XML for {pmcid} at {xml_path}")

        with open(xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        doc = ingester.parse_xml(xml_content, pmcid_override=pmcid)

        # Build PDF
        pdf_path = os.path.join(pdf_dir, f"{pmcid}.pdf")
        render_pdf_for_paper(doc, pdf_path)

        xml_hash = sha256_of_file(xml_path)
        pdf_hash = sha256_of_file(pdf_path)

        # Get BioCause relations
        bioc_docs = [d for k, d in biocause.documents.items() if d.pmcid == pmcid]
        gold_relations = sum(len(d.relations) for d in bioc_docs)
        cross_sentence_gold = sum(sum(1 for r in d.relations if r.is_cross_sentence) for d in bioc_docs)

        # Page count check via pypdf
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        page_count = len(reader.pages)

        paper_entry = {
            "pmcid": pmcid,
            "split": split,
            "title": doc.title,
            "journal": doc.journal,
            "authors": doc.authors,
            "doi": doc.doi,
            "pmid": doc.pmid,
            "license": doc.license_type,
            "xml_path": os.path.relpath(xml_path, REPO_ROOT),
            "xml_sha256": xml_hash,
            "pdf_path": os.path.relpath(pdf_path, REPO_ROOT),
            "pdf_sha256": pdf_hash,
            "page_count": page_count,
            "section_count": len(doc.sections),
            "paragraph_count": sum(len(s.paragraphs) for s in doc.sections),
            "gold_relations_count": gold_relations,
            "cross_sentence_gold_count": cross_sentence_gold,
        }
        manifest["papers"].append(paper_entry)
        print(f"[{split.upper():11}] {pmcid}: {page_count} pages, {gold_relations} gold relations, PDF generated.")

    manifest_path = os.path.join(REPO_ROOT, "data", "real_papers", "split_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest successfully written to {manifest_path}")
    print(f"Summary: {manifest['split_counts']}")


if __name__ == "__main__":
    main()
