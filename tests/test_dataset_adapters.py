# pytest tests/test_dataset_adapters.py
# evryn datasets

import os
import pytest
from evryn.datasets.biocause import BioCauseDataset, load_biocause
from evryn.datasets.scierc import SciERCDataset, load_scierc
from evryn.datasets.pmc_oa import PMCOAIngester


def test_biocause_loading_and_standoff_parsing():
    ds = BioCauseDataset()
    assert os.path.exists(ds.zip_path)
    ds.load()
    assert len(ds.documents) > 100
    stats = ds.summary_statistics()
    assert stats["total_documents"] >= 190
    assert stats["unique_pmc_articles"] >= 15
    assert stats["causality_relations"] > 0
    assert stats["license"] == "CC BY-NC-SA 3.0"

    splits = ds.get_splits(train_ratio=0.70, dev_ratio=0.15)
    assert len(splits["train"]) > 0
    assert len(splits["dev"]) > 0
    assert len(splits["test"]) > 0

    train_pmcs = {d.pmcid for d in splits["train"]}
    dev_pmcs = {d.pmcid for d in splits["dev"]}
    test_pmcs = {d.pmcid for d in splits["test"]}
    assert len(train_pmcs.intersection(dev_pmcs)) == 0
    assert len(train_pmcs.intersection(test_pmcs)) == 0
    assert len(dev_pmcs.intersection(test_pmcs)) == 0


def test_scierc_schema_preservation():
    ds = SciERCDataset()
    assert os.path.exists(ds.tar_path)
    ds.load()
    assert len(ds.documents) >= 500
    stats = ds.summary_statistics()
    assert stats["total_entities"] > 5000
    assert stats["total_relations"] > 4000
    assert "USED-FOR" in stats["relation_type_counts"]
    assert "Causality" not in stats["relation_type_counts"]

    splits = ds.get_splits()
    assert len(splits["train"]) > len(splits["test"])
    for rel_type in stats["relation_type_counts"].keys():
        assert rel_type in ds.VALID_RELATION_TYPES or rel_type == "COREF"


def test_semeval2010_adapter():
    from evryn.datasets.semeval2010 import SemEval2010Dataset
    ds = SemEval2010Dataset()
    assert len(ds.train_samples) == 8000
    assert len(ds.test_samples) == 2717
    causal_test = ds.get_causal_test_samples()
    assert len(causal_test) == 328

    # Test evaluation method with a mock prediction
    sample = causal_test[0]
    preds = {sample.sample_id: (sample.cause_entity, sample.effect_entity)}
    metrics = ds.evaluate_causal_predictions(preds)
    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 0
    assert metrics["precision"] == 1.0


def test_pmc_oa_xml_ingestion_and_offsets():
    ingester = PMCOAIngester()
    xml_path = os.path.join(ingester.cache_dir, "PMC1804205.xml")
    assert os.path.exists(xml_path)
    with open(xml_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    doc = ingester.parse_xml(xml_content, pmcid_override="PMC1804205")
    assert doc.pmcid == "PMC1804205"
    assert doc.pmid == "17229213"
    assert doc.doi == "10.1111/j.1365-2958.2006.05512.x"
    assert "CC BY" in doc.license_type
    assert len(doc.sections) > 5
    assert len(doc.full_text) > 5000

    has_abstract = any(s.section_type == "ABSTRACT" for s in doc.sections)
    assert has_abstract

    total_sents = sum(len(s.sentences) for s in doc.sections)
    assert total_sents > 50
    first_sent = doc.sections[0].sentences[0]
    assert first_sent.end_char > first_sent.start_char
