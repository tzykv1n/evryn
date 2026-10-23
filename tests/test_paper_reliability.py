# pytest tests/test_paper_reliability.py

import os
import time
import json
import tempfile
import pytest
import pypdf
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

from evryn.paper.types import (
    ScientificDocument,
    PageBoundary,
    PaperMetadata,
    CausalAssertion,
    CausalRelationType,
    EvidenceStatus,
)
from evryn.paper.reliability import (
    ReliabilityConfig,
    DocumentValidator,
    CheckpointManager,
    StructuredExecutionLogger,
    PDFValidationStatus,
    PDFValidationError,
    EmptyPDFError,
    CorruptPDFError,
    EncryptedPDFError,
    ImageOnlyPDFError,
    PageLimitExceededError,
    FileSizeLimitExceededError,
    PaperReliabilityError,
    PipelineFailureCategory,
    atomic_write_json,
    execute_with_retry,
)
from evryn.paper.ingestion import PaperIngestion
from evryn.paper.segmentation import PaperSegmenter
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.cross_page_linker import CrossPageLinker
from evryn.paper.graph_builder import PaperGraphBuilder


@pytest.fixture
def sample_valid_pdf(tmp_path):
    pdf_path = str(tmp_path / "valid_multipage.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Hypoxia and VEGF Signaling in Glioblastoma", styles["Heading1"]),
        Paragraph("Abstract: Hypoxia induces HIF-1alpha stabilization.", styles["Normal"]),
        PageBreak(),
        Paragraph("Results: Stabilized HIF-1alpha directly activates VEGF transcription.", styles["Normal"]),
        Paragraph("In contrast, normoxia did not induce VEGF expression.", styles["Normal"]),
        PageBreak(),
        Paragraph("Discussion: Thus, hypoxia stimulates VEGF to promote angiogenesis across tissues.", styles["Normal"]),
    ]
    doc.build(story)
    return pdf_path


def test_normal_multipage_pdf_ingestion(sample_valid_pdf):
    config = ReliabilityConfig(max_pages=50, max_file_size_mb=10.0)
    ingest = PaperIngestion(config=config)
    doc = ingest.ingest_pdf(sample_valid_pdf)
    assert doc.metadata.page_count == 3
    assert len(doc.pages) == 3
    assert "Hypoxia" in doc.full_text


def test_empty_pdf_error(tmp_path):
    empty_path = str(tmp_path / "empty_file.pdf")
    with open(empty_path, "wb") as f:
        pass
    validator = DocumentValidator()
    with pytest.raises(EmptyPDFError) as exc_info:
        validator.validate_pdf(empty_path)
    assert exc_info.value.status == PDFValidationStatus.EMPTY_FILE


def test_corrupt_pdf_error(tmp_path):
    corrupt_path = str(tmp_path / "corrupt_data.pdf")
    with open(corrupt_path, "wb") as f:
        f.write(b"NOT_A_REAL_PDF_DATA_STREAM_HEADER")
    validator = DocumentValidator()
    with pytest.raises(CorruptPDFError) as exc_info:
        validator.validate_pdf(corrupt_path)
    assert exc_info.value.status == PDFValidationStatus.CORRUPT


def test_encrypted_pdf_handling(tmp_path):
    src_pdf = str(tmp_path / "source.pdf")
    enc_pdf = str(tmp_path / "encrypted.pdf")
    doc = SimpleDocTemplate(src_pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    doc.build([Paragraph("Confidential Clinical Results", styles["Normal"])])

    reader = pypdf.PdfReader(src_pdf)
    writer = pypdf.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("secret_pass")
    with open(enc_pdf, "wb") as f:
        writer.write(f)

    validator = DocumentValidator()
    with pytest.raises(EncryptedPDFError) as exc_info:
        validator.validate_pdf(enc_pdf)
    assert exc_info.value.status == PDFValidationStatus.ENCRYPTED


def test_image_only_pdf_detection(tmp_path):
    image_pdf = str(tmp_path / "scanned_image_only.pdf")
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with open(image_pdf, "wb") as f:
        writer.write(f)

    validator = DocumentValidator()
    with pytest.raises(ImageOnlyPDFError) as exc_info:
        validator.validate_pdf(image_pdf)
    assert exc_info.value.status == PDFValidationStatus.IMAGE_ONLY


def test_page_limit_violation(sample_valid_pdf):
    config = ReliabilityConfig(max_pages=2)
    validator = DocumentValidator(config)
    with pytest.raises(PageLimitExceededError) as exc_info:
        validator.validate_pdf(sample_valid_pdf)
    assert exc_info.value.status == PDFValidationStatus.PAGE_LIMIT_EXCEEDED


def test_file_size_limit_violation(sample_valid_pdf):
    config = ReliabilityConfig(max_file_size_mb=0.0001)
    validator = DocumentValidator(config)
    with pytest.raises(FileSizeLimitExceededError) as exc_info:
        validator.validate_pdf(sample_valid_pdf)
    assert exc_info.value.status == PDFValidationStatus.SIZE_LIMIT_EXCEEDED


def test_page_failing_while_others_succeed(sample_valid_pdf):
    ingest = PaperIngestion()
    doc = ingest.ingest_pdf(sample_valid_pdf)
    assert len(doc.pages) == 3
    segmenter = PaperSegmenter()
    doc = segmenter.segment_document(doc)
    assert len(doc.sentences) > 0


def test_transient_failure_bounded_retry():
    calls = []

    def flaky_service():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("Temporary network reset")
        return {"status": "ok", "result": 42}

    logger = StructuredExecutionLogger()
    res = execute_with_retry(
        flaky_service,
        max_retries=3,
        backoff_factor=1.1,
        transient_exceptions=(ConnectionError,),
        logger=logger,
        doc_id="doc_retry_test",
        stage="api_extraction",
    )
    assert res["status"] == "ok"
    assert len(calls) == 3
    assert any(r.status == "RETRYING" for r in logger.records)
    assert any(r.status == "SUCCESS" for r in logger.records)


def test_permanent_failure_no_infinite_retry():
    calls = []

    def permanent_fail():
        calls.append(1)
        raise ValueError("Invalid configuration syntax")

    logger = StructuredExecutionLogger()
    with pytest.raises(ValueError):
        execute_with_retry(
            permanent_fail,
            max_retries=3,
            logger=logger,
            doc_id="doc_perm_fail",
        )
    assert len(calls) == 1
    assert logger.records[-1].status == "FAILED"


def test_checkpoint_save_and_resume(tmp_path):
    ckpt_dir = str(tmp_path / "ckpts")
    mgr = CheckpointManager(checkpoint_dir=ckpt_dir)
    doc_id = "doc_test_checkpoint_123"

    assert mgr.load_checkpoint(doc_id, "stage1") is None

    mgr.save_checkpoint(doc_id, "stage1", {"completed_pages": [1, 2], "partial_graph": {"nodes": 5}})
    loaded = mgr.load_checkpoint(doc_id, "stage1")
    assert loaded is not None
    assert loaded["completed_pages"] == [1, 2]
    assert loaded["partial_graph"]["nodes"] == 5

    mgr.clear_checkpoint(doc_id, "stage1")
    assert mgr.load_checkpoint(doc_id, "stage1") is None


def test_atomic_write_preserves_valid_output_on_crash(tmp_path):
    target_file = str(tmp_path / "valid_results.json")
    atomic_write_json(target_file, {"status": "valid", "score": 0.95})

    assert os.path.isfile(target_file)
    with open(target_file) as f:
        data = json.load(f)
    assert data["score"] == 0.95

    try:
        tmp_crash = target_file + ".tmp_failing"
        with open(tmp_crash, "w") as f:
            f.write("PARTIAL_CORRUPT_JSON_DATA")
        raise RuntimeError("Simulated crash mid-pipeline")
    except RuntimeError:
        pass

    with open(target_file) as f:
        data_after = json.load(f)
    assert data_after["score"] == 0.95
    assert data_after["status"] == "valid"


def test_idempotent_repeated_execution(sample_valid_pdf):
    ingest = PaperIngestion()
    segmenter = PaperSegmenter()
    extractor = PaperCausalExtractor()
    linker = CrossPageLinker()
    builder = PaperGraphBuilder()

    doc1 = segmenter.segment_document(ingest.ingest_pdf(sample_valid_pdf))
    asrt1 = extractor.extract_assertions(doc1)
    links1 = linker.find_cross_page_links(asrt1)
    g1 = builder.build_graph(doc1.doc_id, doc1.metadata.title, asrt1, links1)

    doc2 = segmenter.segment_document(ingest.ingest_pdf(sample_valid_pdf))
    asrt2 = extractor.extract_assertions(doc2)
    links2 = linker.find_cross_page_links(asrt2)
    g2 = builder.build_graph(doc2.doc_id, doc2.metadata.title, asrt2, links2)

    assert len(asrt1) == len(asrt2)
    assert len(links1) == len(links2)
    assert len(g1.edges) == len(g2.edges)


def test_duplicate_prevention_during_reassembly(sample_valid_pdf):
    ingest = PaperIngestion()
    segmenter = PaperSegmenter()
    extractor = PaperCausalExtractor()
    doc = segmenter.segment_document(ingest.ingest_pdf(sample_valid_pdf))
    assertions = extractor.extract_assertions(doc)

    keys = [(a.cause_canonical, a.effect_canonical, a.sentence_id) for a in assertions]
    assert len(keys) == len(set(keys))


def test_structured_logger_never_logs_secrets():
    logger = StructuredExecutionLogger()
    logger.log_event(
        doc_id="doc_secret_test",
        stage="model_call",
        status="FAILED",
        message="Failed authentication using sk-ant-api03-secretkey123 and Bearer ghp_token456",
    )
    rec = logger.records[0]
    assert "sk-ant" not in rec.message
    assert "ghp_" not in rec.message
    assert "[REDACTED]" in rec.message


def test_citation_numbers_and_verbs_not_aliases():
    from evryn.paper.normalizer import PaperEntityNormalizer
    normalizer = PaperEntityNormalizer()
    text = (
        "Previous findings (10) reported that interleukin-6 activates STAT3. "
        "Furthermore, subsequent trials (14, 15) evaluated tumor progression. "
        "In the absence of negative regulators (HilD), activation was observed."
    )
    abbrs = normalizer.extract_document_abbreviations(text)
    assert "10" not in abbrs
    assert "14" not in abbrs
    assert "15" not in abbrs
    assert "14, 15" not in abbrs
    assert not any(k.isdigit() for k in abbrs.keys())
    assert not any("in the absence" in k for k in abbrs.keys())


def test_cross_page_transitive_link_hop_and_distance_bounds():
    linker = CrossPageLinker(min_page_distance=1, max_transitive_hops=2, min_confidence=0.60)
    
    # Same page assertions should NOT produce cross-page links
    a1 = CausalAssertion(
        assertion_id="a1",
        cause="Hypoxia",
        cause_canonical="Hypoxia",
        effect="HIF-1alpha",
        effect_canonical="HIF-1alpha",
        direction="forward",
        relation_type=CausalRelationType.DIRECT_CAUSE,
        is_negated=False,
        uncertainty_score=0.1,
        sentence_id="s1",
        page_number=2,
        section_title="Results",
        confidence=0.90,
        evidence_quote="Hypoxia induces HIF-1alpha.",
        char_span=(0, 20),
        evidence_status=EvidenceStatus.MEASURED_FACT,
    )
    a2 = CausalAssertion(
        assertion_id="a2",
        cause="HIF-1alpha",
        cause_canonical="HIF-1alpha",
        effect="VEGF",
        effect_canonical="VEGF",
        direction="forward",
        relation_type=CausalRelationType.DIRECT_CAUSE,
        is_negated=False,
        uncertainty_score=0.1,
        sentence_id="s2",
        page_number=2,
        section_title="Results",
        confidence=0.90,
        evidence_quote="HIF-1alpha activates VEGF.",
        char_span=(25, 45),
        evidence_status=EvidenceStatus.MEASURED_FACT,
    )
    links_same_page = linker.find_cross_page_links([a1, a2])
    assert len(links_same_page) == 0

    # Cross-page assertions should produce a transitive link
    a2_cross = CausalAssertion(
        assertion_id="a2_cross",
        cause="HIF-1alpha",
        cause_canonical="HIF-1alpha",
        effect="VEGF",
        effect_canonical="VEGF",
        direction="forward",
        relation_type=CausalRelationType.DIRECT_CAUSE,
        is_negated=False,
        uncertainty_score=0.1,
        sentence_id="s3",
        page_number=5,
        section_title="Discussion",
        confidence=0.90,
        evidence_quote="HIF-1alpha activates VEGF on page 5.",
        char_span=(0, 20),
        evidence_status=EvidenceStatus.MEASURED_FACT,
    )
    links_cross = linker.find_cross_page_links([a1, a2_cross])
    assert len(links_cross) == 1
    assert links_cross[0].source_entity == "Hypoxia"
    assert links_cross[0].target_entity == "VEGF"
    assert links_cross[0].distance_pages == 3


def test_negation_detection_and_positive_exclusion(sample_valid_pdf):
    ingest = PaperIngestion()
    segmenter = PaperSegmenter()
    extractor = PaperCausalExtractor()
    linker = CrossPageLinker()

    doc = segmenter.segment_document(ingest.ingest_pdf(sample_valid_pdf))
    assertions = extractor.extract_assertions(doc)
    
    negated = [a for a in assertions if a.is_negated]
    assert len(negated) >= 1
    assert any("normoxia" in a.cause.lower() or "not induce" in a.evidence_quote.lower() for a in negated)

    # Negated assertions must NOT form positive edges in linker
    links = linker.find_cross_page_links(assertions)
    for link in links:
        assert "normoxia" not in link.source_entity.lower()


def test_provenance_validity_guarantees(sample_valid_pdf):
    ingest = PaperIngestion()
    segmenter = PaperSegmenter()
    extractor = PaperCausalExtractor()

    doc = segmenter.segment_document(ingest.ingest_pdf(sample_valid_pdf))
    assertions = extractor.extract_assertions(doc)
    
    assert len(assertions) > 0
    for a in assertions:
        assert a.page_number >= 1
        assert len(a.section_title.strip()) > 0
        assert a.char_span[0] >= 0
        assert a.char_span[1] > a.char_span[0]
        assert len(a.evidence_quote.strip()) > 0
        assert len(a.cause_canonical.strip()) > 0
        assert len(a.effect_canonical.strip()) > 0
