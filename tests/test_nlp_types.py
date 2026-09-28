# pytest tests/test_nlp_types.py

from evryn.nlp.core.types import CausalRelationType, RelationExample


def test_relation_types():
    assert CausalRelationType.from_str("Cause-Effect(e1,e2)") == CausalRelationType.FORWARD
    assert CausalRelationType.from_str("Cause-Effect(e2,e1)") == CausalRelationType.BACKWARD
    assert CausalRelationType.from_str("Component-Whole(e1,e2)") == CausalRelationType.NO_RELATION
    assert CausalRelationType.from_str("Other") == CausalRelationType.NO_RELATION


def test_relation_example_properties():
    ex = RelationExample(
        example_id="1",
        sentence="The burst was caused by water pressure.",
        entity1_text="burst",
        entity2_text="pressure",
        entity1_span=(4, 9),
        entity2_span=(30, 38),
        relation_type=CausalRelationType.BACKWARD,
        raw_label="Cause-Effect(e2,e1)",
    )
    assert ex.is_causal is True
    assert ex.middle_context == "was caused by water"
    marked = ex.marked_sentence
    assert "<e1>burst</e1>" in marked
    assert "<e2>pressure</e2>" in marked
