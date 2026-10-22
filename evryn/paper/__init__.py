# evryn paper --help
# pytest tests/test_paper_pipeline.py

from .types import (
    ScientificDocument,
    PageBoundary,
    SectionSpan,
    ParagraphSpan,
    SentenceSpan,
    PaperMetadata,
    CausalAssertion,
    CrossPageLink,
    PaperCausalGraph,
    ScientificSectionType,
    CausalRelationType,
    EvidenceStatus,
)
from .ingestion import PaperIngestion, PDFIngestionError
from .segmentation import PaperSegmenter
from .normalizer import PaperEntityNormalizer
from .extractor import PaperCausalExtractor
from .cross_page_linker import CrossPageLinker
from .graph_builder import PaperGraphBuilder
from .reporting import PaperEvidenceReporter
from .evaluator import PaperBenchmarkEvaluator, PaperEvaluationResult

__all__ = [
    "ScientificDocument",
    "PageBoundary",
    "SectionSpan",
    "ParagraphSpan",
    "SentenceSpan",
    "PaperMetadata",
    "CausalAssertion",
    "CrossPageLink",
    "PaperCausalGraph",
    "ScientificSectionType",
    "CausalRelationType",
    "EvidenceStatus",
    "PaperIngestion",
    "PDFIngestionError",
    "PaperSegmenter",
    "PaperEntityNormalizer",
    "PaperCausalExtractor",
    "CrossPageLinker",
    "PaperGraphBuilder",
    "PaperEvidenceReporter",
    "PaperBenchmarkEvaluator",
    "PaperEvaluationResult",
]
