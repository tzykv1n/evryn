# pytest tests/test_families.py

import pytest
from evryn.core.types import NormalizedRelation, RelationType, EvidenceSpan
from evryn.normalization.normalizer import RelationNormalizer
from evryn.families.discovery import RelationFamilyRegistry, RelationFamilyDiscoverer


def test_standard_families():
    families = RelationFamilyRegistry.get_standard_families()
    assert "POSITIVE_REGULATION" in families
    assert "NEGATIVE_REGULATION" in families
    assert "CAUSAL_PRODUCTION" in families
    assert "PHYSICAL_INTERACTION" in families
    assert "SYNERGISTIC_CO_ACTION" in families
    assert "METABOLIC_CONVERSION" in families


def test_assign_family_keywords():
    norm = RelationNormalizer()
    discoverer = RelationFamilyDiscoverer()

    rel_pos = norm.normalize_pairwise(
        "IL-6", "STAT3", "FORWARD", 0.9,
        "IL-6 stimulates and enhances phosphorylation of STAT3.",
        (0, 4), (38, 43),
    )
    fam_pos = discoverer.assign_family(rel_pos)
    assert fam_pos == "POSITIVE_REGULATION"

    rel_neg = norm.normalize_pairwise(
        "Aspirin", "COX-2", "FORWARD", 0.95,
        "Aspirin inhibits and suppresses COX-2 synthesis.",
        (0, 7), (32, 37),
    )
    fam_neg = discoverer.assign_family(rel_neg)
    assert fam_neg == "NEGATIVE_REGULATION"

    rel_phys = norm.normalize_pairwise(
        "Protein A", "Protein B", "FORWARD", 0.85,
        "Protein A binds directly to Protein B.",
        (0, 9), (28, 37),
    )
    fam_phys = discoverer.assign_family(rel_phys)
    assert fam_phys == "PHYSICAL_INTERACTION"


def test_assign_family_higher_order():
    norm = RelationNormalizer()
    discoverer = RelationFamilyDiscoverer()

    norm_rel, _ = norm.normalize_higher_order(
        ["RAF", "MEK"], "ERK", "joint_activation", 0.8, 0.95,
        "RAF and MEK jointly activate ERK.",
    )
    fam = discoverer.assign_family(norm_rel)
    assert fam == "SYNERGISTIC_CO_ACTION"


def test_discover_families():
    norm = RelationNormalizer()
    discoverer = RelationFamilyDiscoverer()

    r1 = norm.normalize_pairwise("A", "B", "FORWARD", 0.9, "A promotes B", (0, 1), (11, 12))
    r2 = norm.normalize_pairwise("C", "D", "FORWARD", 0.9, "C blocks D", (0, 1), (9, 10))
    summary = discoverer.discover_families([r1, r2])

    assert summary["POSITIVE_REGULATION"]["count"] >= 1
    assert summary["NEGATIVE_REGULATION"]["count"] >= 1
