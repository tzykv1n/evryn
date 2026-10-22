# pytest tests/test_literature_validator.py
# python -m pytest tests/test_literature_validator.py

import os
import json
from evryn.core.types import NormalizedEntity, Provenance, ScientificDomain
from evryn.hypothesize.generator import ScientificHypothesis
from evryn.hypothesize.literature_validator import LiteratureValidator


def test_literature_validator_mock(tmp_path):
    out_dir = str(tmp_path / "outputs")
    cache_dir = str(tmp_path / "cache")

    validator = LiteratureValidator(cache_dir=cache_dir, output_dir=out_dir)

    e1 = NormalizedEntity(entity_id="e1", canonical_name="p53 mutation", domain=ScientificDomain.BIOMEDICINE)
    e2 = NormalizedEntity(entity_id="e2", canonical_name="kras activation", domain=ScientificDomain.BIOMEDICINE)
    e3 = NormalizedEntity(entity_id="e3", canonical_name="metastatic invasiveness", domain=ScientificDomain.BIOMEDICINE)

    hyp = ScientificHypothesis(
        hypothesis_id="hyp_test_001",
        title="Test Synergy",
        statement="{p53 mutation, kras activation} -> metastatic invasiveness",
        hypothesis_type="HIGHER_ORDER_SYNERGY",
        involved_entities=[e1, e2, e3],
        plausibility_score=0.82,
        reasoning_chain=["Step 1", "Step 2"],
        supporting_relation_ids=["rel1", "rel2"],
        provenance=Provenance(source_id="test"),
    )

    res = validator.validate_hypothesis(hyp)
    assert res["hypothesis_id"] == "hyp_test_001"
    assert "validation_status" in res
    assert res["validation_status"] in ("CONFIRMED_IN_LITERATURE", "SUPPORTED_PARALLEL", "UNVERIFIED_IN_LITERATURE", "CONTRADICTED")
    assert "calibrated_confidence" in res
    assert isinstance(res["traceable_citations"], list)


def test_literature_validation_all(tmp_path):
    out_dir = str(tmp_path / "outputs")
    cache_dir = str(tmp_path / "cache")

    validator = LiteratureValidator(cache_dir=cache_dir, output_dir=out_dir)

    e1 = NormalizedEntity(entity_id="e1", canonical_name="vegf upregulation", domain=ScientificDomain.BIOMEDICINE)
    e2 = NormalizedEntity(entity_id="e2", canonical_name="tumor metastasis", domain=ScientificDomain.BIOMEDICINE)

    hyp = ScientificHypothesis(
        hypothesis_id="hyp_test_002",
        title="Test Transitive",
        statement="vegf upregulation -> tumor metastasis",
        hypothesis_type="TEMPORAL_EXTRAPOLATION",
        involved_entities=[e1, e2],
        plausibility_score=0.75,
        reasoning_chain=["Step 1"],
        supporting_relation_ids=["rel3"],
        provenance=Provenance(source_id="test"),
    )

    results = validator.validate_all([hyp])
    assert len(results) == 1
    assert os.path.exists(os.path.join(out_dir, "hypothesis_literature_validation.json"))
    assert os.path.exists(os.path.join(out_dir, "fig_literature_validation.png"))
