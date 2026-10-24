# evryn paper --help
# pytest tests/test_paper_pipeline.py

import os
import json
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

from evryn.paper import (
    ScientificDocument,
    PageBoundary,
    SectionSpan,
    ScientificSectionType,
    CausalRelationType,
    EvidenceStatus,
    PaperIngestion,
    PaperSegmenter,
    PaperEntityNormalizer,
    PaperCausalExtractor,
    CrossPageLinker,
    PaperGraphBuilder,
    PaperEvidenceReporter,
    PaperBenchmarkEvaluator,
)
from evryn.paper.robustness import PaperRobustnessExperiments


@pytest.fixture
def sample_pdf(tmp_path):
    pdf_path = str(tmp_path / "test_signaling_paper.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Interleukin-6 Signaling in Macrophages", styles["Heading1"]),
        Paragraph("Authors: Jane Doe, MD<br/>DOI: 10.1038/s41586-024-00101-x | PMID: 38291001 | PMCID: PMC10821001", styles["Normal"]),
        Paragraph("Page 1 — Abstract & Introduction", styles["Heading2"]),
        Paragraph("Interleukin-6 (IL-6) stimulates JAK2 kinase activation at the plasma membrane.", styles["Normal"]),
        PageBreak(),
        Paragraph("Page 2 — Results", styles["Heading2"]),
        Paragraph("Active JAK2 directly phosphorylates STAT3 to drive transcription.", styles["Normal"]),
        Paragraph("In contrast, vehicle did not stimulate STAT3 phosphorylation.", styles["Normal"]),
        PageBreak(),
        Paragraph("Page 3 — Discussion & Conclusions", styles["Heading2"]),
        Paragraph("We hypothesize that IL-6 may potentially induce STAT3 signaling in inflammation.", styles["Normal"]),
    ]
    doc.build(story)
    return pdf_path


def test_pdf_ingestion_and_metadata(sample_pdf):
    ingest = PaperIngestion()
    doc = ingest.ingest_pdf(sample_pdf)
    assert doc.metadata.page_count == 3
    assert doc.metadata.doi == "10.1038/s41586-024-00101-x"
    assert doc.metadata.pmid == "38291001"
    assert doc.metadata.pmcid == "PMC10821001"
    assert len(doc.pages) == 3
    assert doc.pages[0].page_number == 1
    assert doc.pages[1].page_number == 2
    assert doc.pages[2].page_number == 3


def test_paper_segmentation(sample_pdf):
    ingest = PaperIngestion()
    doc = ingest.ingest_pdf(sample_pdf)
    segmenter = PaperSegmenter()
    doc = segmenter.segment_document(doc)
    assert len(doc.sections) >= 3
    assert len(doc.sentences) >= 4
    pages_observed = {s.page_number for s in doc.sentences}
    assert 1 in pages_observed
    assert 2 in pages_observed


def test_entity_normalization():
    norm = PaperEntityNormalizer()
    text = "Binding of interleukin-6 (IL-6) activates signal transducer and activator of transcription 3 (STAT3)."
    abbr = norm.extract_document_abbreviations(text)
    assert "il-6" in abbr or "stat3" in abbr
    canon_il6 = norm.canonicalize("interleukin-6", abbr)
    assert canon_il6 == "IL-6"
    canon_stat3 = norm.canonicalize("signal transducer and activator of transcription 3", abbr)
    assert canon_stat3 == "STAT3"


def test_causal_extraction_and_negation(sample_pdf):
    ingest = PaperIngestion()
    segmenter = PaperSegmenter()
    doc = segmenter.segment_document(ingest.ingest_pdf(sample_pdf))
    extractor = PaperCausalExtractor()
    assertions = extractor.extract_assertions(doc)
    assert len(assertions) >= 2

    direct_asrt = [a for a in assertions if a.cause_canonical == "IL-6" and a.effect_canonical == "JAK2"]
    assert len(direct_asrt) >= 1
    assert direct_asrt[0].page_number == 1
    assert not direct_asrt[0].is_negated
    assert direct_asrt[0].evidence_status == EvidenceStatus.MEASURED_FACT

    jak_stat = [a for a in assertions if a.cause_canonical == "JAK2" and a.effect_canonical == "STAT3"]
    assert len(jak_stat) >= 1
    assert jak_stat[0].page_number == 2


def test_cross_page_linking(sample_pdf):
    ingest = PaperIngestion()
    segmenter = PaperSegmenter()
    doc = segmenter.segment_document(ingest.ingest_pdf(sample_pdf))
    extractor = PaperCausalExtractor()
    assertions = extractor.extract_assertions(doc)
    linker = CrossPageLinker(min_page_distance=0)
    links = linker.find_cross_page_links(assertions)
    transitive = [l for l in links if l.source_entity == "IL-6" and l.target_entity == "STAT3"]
    assert len(transitive) >= 1
    assert transitive[0].cause_page == 1
    assert transitive[0].effect_page == 2
    assert transitive[0].distance_pages >= 1


def test_graph_builder_and_reporting(sample_pdf, tmp_path):
    out_dir = str(tmp_path / "reports")
    ingest = PaperIngestion()
    segmenter = PaperSegmenter()
    doc = segmenter.segment_document(ingest.ingest_pdf(sample_pdf))
    extractor = PaperCausalExtractor()
    assertions = extractor.extract_assertions(doc)
    linker = CrossPageLinker(min_page_distance=0)
    links = linker.find_cross_page_links(assertions)
    builder = PaperGraphBuilder()
    graph = builder.build_graph(doc.doc_id, doc.metadata.title, assertions, links)

    assert len(graph.nodes) >= 3
    assert len(graph.edges) >= 3

    reporter = PaperEvidenceReporter(out_dir)
    res = reporter.generate_report(doc, assertions, links, graph)
    assert os.path.isfile(res["markdown_report"])
    assert os.path.isfile(res["json_evidence"])
    assert os.path.isfile(res["graph_figure"])


def test_benchmark_evaluator_and_robustness(sample_pdf, tmp_path):
    out_dir = str(tmp_path / "bench")
    ingest = PaperIngestion()
    segmenter = PaperSegmenter()
    doc = segmenter.segment_document(ingest.ingest_pdf(sample_pdf))

    gt = {
        "canonical_entities": ["IL-6", "JAK2", "STAT3"],
        "direct_edges": [["IL-6", "JAK2"], ["JAK2", "STAT3"]],
        "cross_page_edges": [["IL-6", "STAT3"]],
    }

    evaluator = PaperBenchmarkEvaluator(out_dir)
    paper_res = evaluator.evaluate_paper(doc, gt)
    assert paper_res.baseline_a_cross_f1 == 0.0
    assert paper_res.baseline_b_cross_f1 == 0.0
    assert paper_res.system_c_cross_f1 > 0.0
    assert paper_res.provenance_completeness == 1.0

    rob = PaperRobustnessExperiments(evaluator, out_dir)
    dropout_res = rob.run_dropout_ablation([doc], [gt], dropout_rates=[0.0, 0.2])
    assert "0%" in dropout_res
    assert "20%" in dropout_res


def test_open_domain_cyclic_canonicalization():
    norm = PaperEntityNormalizer()
    known = ["di-GMP", "Biofilm", "Virulence"]
    assert norm.canonicalize("c-di-GMP", known_entities=known) == "di-GMP"
    assert norm.canonicalize("cyclic-di-GMP", known_entities=known) == "di-GMP"
    assert norm.canonicalize("cyclic di-gmp", known_entities=known) == "di-GMP"

    known_c = ["cyclic-di-GMP", "Biofilm", "Virulence"]
    assert norm.canonicalize("di-GMP", known_entities=known_c) == "cyclic-di-GMP"
    assert norm.canonicalize("c-di-GMP", known_entities=known_c) == "cyclic-di-GMP"


def test_open_domain_omp_lps_normalization():
    norm = PaperEntityNormalizer()
    known = ["BvrR", "BvrS", "Outer Membrane Proteins", "Lipopolysaccharide"]
    assert norm.canonicalize("Omp3b", known_entities=known) == "Outer Membrane Proteins"
    assert norm.canonicalize("Omp25", known_entities=known) == "Outer Membrane Proteins"
    assert norm.canonicalize("ompa", known_entities=known) == "Outer Membrane Proteins"
    assert norm.canonicalize("LPS", known_entities=known) == "Lipopolysaccharide"
    assert norm.canonicalize("lps", known_entities=known) == "Lipopolysaccharide"


def test_open_domain_abbreviation_recheck_canonicalization():
    norm = PaperEntityNormalizer()
    local_abbr = {"omps": "outer membrane proteins"}
    known = ["Outer Membrane Proteins", "Virulence"]
    assert norm.canonicalize("OMPs", local_abbr_map=local_abbr, known_entities=known) == "Outer Membrane Proteins"


def test_benchmark_v1_and_v2_specifications():
    from evryn.paper.real_benchmark import get_curated_papers, CURATED_REAL_PAPERS_V1, CURATED_REAL_PAPERS_V2
    v1 = get_curated_papers("v1")
    v2 = get_curated_papers("v2")
    assert len(v1) == 20
    assert len(v2) == 20

    v1_map = {p["pmcid"]: p for p in v1}
    v2_map = {p["pmcid"]: p for p in v2}

    assert v1_map["PMC2816692"]["canonical_entities"] == ["Protective Antigen", "Lethal Factor", "MEK1/2", "MAPK Signaling", "Cytotoxicity", "Virulence"]
    assert v2_map["PMC2816692"]["canonical_entities"] == ["SrcA", "SsaN", "PipB2", "SseL", "Effector Translocation", "Virulence"]
    assert "SrcA" in [e[0] for e in v2_map["PMC2816692"]["direct_edges"]]
    assert v2_map["PMC2774163"]["title"] == "A Novel Signaling Network Essential for Regulating Pseudomonas aeruginosa Biofilm Development"

