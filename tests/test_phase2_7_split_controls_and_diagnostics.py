"""
Phase 2.7 Verification Suite:
1. Frozen Phase 1 artifacts preservation (bit-for-bit SHA-256 invariance).
2. Core Extractor & Normalizer enhancements (synonym resolution, prefix stripping, noise removal).
3. Controlled ablation toggles in extractor and cross-page linker.
4. PipelineDiagnosticsService: Stage 1-8 analysis & 8 canonical error classes.
5. Live web API diagnostics & ablations endpoints.
"""

import os
import hashlib
import pytest
from fastapi.testclient import TestClient

from evryn.paper.normalizer import PaperEntityNormalizer
from evryn.paper.extractor import PaperCausalExtractor
from evryn.paper.cross_page_linker import CrossPageLinker
from evryn.paper.ingestion import PaperIngestion
from evryn.paper.segmentation import PaperSegmenter
from evryn.paper.evaluator import PaperBenchmarkEvaluator
from evryn.paper.real_benchmark import CURATED_REAL_PAPERS
from evryn.web.pipeline_diagnostics_service import PipelineDiagnosticsService, ERROR_CLASSES_SPEC
from evryn.web.server import app


PHASE1_MAIN_HASH = "4e7eb0ffb6390260b4d0e8bea70abc420237d7a952ebd7fa977ad2db8b8fce5d"
PHASE1_PRES_HASH = "dfeafd264a583442d9cf8a647db5f0465d5cbeaf3f488135eb10138ebefc822b"


def test_phase1_hash_invariance():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_pdf = os.path.join(repo_root, "docs", "phase1", "main.pdf")
    pres_pdf = os.path.join(repo_root, "docs", "phase1", "Temporal_Causal_Knowledge_Phase1_Presentation.pdf")

    assert os.path.exists(main_pdf), "Phase 1 main.pdf missing"
    assert os.path.exists(pres_pdf), "Phase 1 presentation PDF missing"

    with open(main_pdf, "rb") as f:
        main_h = hashlib.sha256(f.read()).hexdigest()
    with open(pres_pdf, "rb") as f:
        pres_h = hashlib.sha256(f.read()).hexdigest()

    assert main_h == PHASE1_MAIN_HASH, f"Phase 1 main.pdf hash changed: {main_h}"
    assert pres_h == PHASE1_PRES_HASH, f"Phase 1 presentation PDF hash changed: {pres_h}"


def test_normalizer_lps_and_prefix_stripping():
    normalizer = PaperEntityNormalizer()

    # 1. LPS synonym mapping
    assert normalizer.canonicalize("lipopolysaccharide") == "Lipopolysaccharide"
    assert normalizer.canonicalize("lipopolysacharide") == "Lipopolysaccharide"

    # 2. Structural component prefix stripping
    assert normalizer.canonicalize("various components of the lipopolysaccharide") == "Lipopolysaccharide"
    assert normalizer.canonicalize("components of LPS") == "Lipopolysaccharide"
    assert normalizer.canonicalize("major modifications to the lipopolysacharide") == "Lipopolysaccharide"


def test_extractor_discourse_noise_stripping():
    normalizer = PaperEntityNormalizer()
    extractor = PaperCausalExtractor(normalizer)

    # 1. Discourse noise leading cleanup
    assert extractor._clean_phrase("Likewise, the human receptor OGR1") == "human receptor OGR1"
    assert extractor._clean_phrase("Similarly, the sensor PhoQ") == "sensor PhoQ"
    assert extractor._clean_phrase("In contrast, the kinase PmrB") == "kinase PmrB"

    # 2. Preamble filter toggle
    assert extractor.enable_cited_preamble_filter is True
    extractor.enable_cited_preamble_filter = False
    assert extractor.enable_cited_preamble_filter is False
    extractor.enable_cited_preamble_filter = True


def test_linker_adapter_invariants_toggle():
    linker = CrossPageLinker()
    assert linker.enable_adapter_invariants is True
    assert linker.enable_transitive_invariants is True

    linker.enable_adapter_invariants = False
    assert linker.enable_adapter_invariants is False
    linker.enable_adapter_invariants = True


def test_diagnostics_service_8_error_classes():
    svc = PipelineDiagnosticsService.get_instance()
    assert len(ERROR_CLASSES_SPEC) == 8

    # Test Class 1: direction inversion
    cls_id, _ = svc.classify_error({
        "cause_name": "PmrB",
        "effect_name": "low pH",
        "evidence_quote": "PmrB sensing to low pH triggers response.",
    })
    assert cls_id == "direction_inversion"

    # Test Class 2: negation & polarity
    cls_id, _ = svc.classify_error({
        "cause_name": "PmrA",
        "effect_name": "expression",
        "is_negated": True,
        "evidence_quote": "PmrA failed to activate transcription.",
    })
    assert cls_id == "negation_polarity"

    # Test Class 3: speculative hypothesis
    cls_id, _ = svc.classify_error({
        "cause_name": "PhoP",
        "effect_name": "PmrD",
        "evidence_quote": "We hypothesized that PhoP mediates this resistance.",
    })
    assert cls_id == "speculative_hypothesis"

    # Test Class 6: missing direct
    cls_id, _ = svc.classify_error({}, is_missed=True)
    assert cls_id == "missing_direct"

    # Test Class 7: unsupported transitive
    cls_id, _ = svc.classify_error({
        "cause_name": "PmrD",
        "effect_name": "polymyxin resistance",
        "is_transitive": True,
        "evidence_quote": "Inferred path across pages.",
    }, is_cross=True)
    assert cls_id == "unsupported_transitive"

    # Test Class 8: citation preamble
    cls_id, _ = svc.classify_error({
        "cause_name": "Iron",
        "effect_name": "PmrA",
        "evidence_quote": "Because iron activates PmrA (Wosten et al., 2000), we tested growth.",
    })
    assert cls_id == "citation_preamble"


def test_pipeline_diagnostics_analysis():
    svc = PipelineDiagnosticsService.get_instance()
    res = svc.analyze_pipeline_run("PMC1804205")

    assert res["status"] == "success"
    assert res["pmcid"] == "PMC1804205"
    assert len(res["stage_breakdown"]) == 8
    assert "error_counts" in res
    assert "diagnostic_relations" in res
    assert res["total_diagnosed_relations"] > 0


def test_controlled_ablations_runner():
    svc = PipelineDiagnosticsService.get_instance()
    res = svc.run_controlled_ablations("PMC1804205")

    assert res["status"] == "success"
    assert len(res["ablations"]) == 4

    # Baseline should match official scores
    baseline = next(a for a in res["ablations"] if a["variant"] == "baseline")
    assert baseline["direct_f1"] == 0.7143
    assert baseline["cross_f1"] == 0.5455
    assert baseline["false_transitive_jumps"] == 3


def test_diagnostics_api_endpoints():
    client = TestClient(app)

    # 1. Pipeline diagnostics endpoint
    res = client.get("/api/diagnostics/pipeline/PMC1804205")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["stage_breakdown"]) == 8

    # 2. Controlled ablations endpoint
    res = client.get("/api/diagnostics/ablations")
    assert res.status_code == 200
    abl_data = res.json()
    assert abl_data["status"] == "success"
    assert len(abl_data["ablations"]) == 4
