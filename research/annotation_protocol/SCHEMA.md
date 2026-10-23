# EVRYN Causal Annotation Schema Specification

**Schema Standard:** `evryn-causal-v2.json`  
**License:** CC BY 4.0  

---

## 1. JSON Schema Definition

Every annotated scientific document in the EVRYN benchmark follows this formal structure:

```json
{
  "$schema": "https://evryn.org/schemas/causal-annotation-v2.json",
  "document_id": "PMC1804205",
  "identifiers": {
    "pmcid": "PMC1804205",
    "pmid": "17329402",
    "doi": "10.1371/journal.ppat.0030019"
  },
  "metadata": {
    "title": "Salmonella enterica serovar Typhimurium virulence gene regulation",
    "journal": "PLoS Pathogens",
    "license": "CC BY 2.5",
    "is_synthetic": false,
    "provenance": "PubMed Central Open Access"
  },
  "canonical_entities": [
    {
      "id": "E1",
      "canonical_name": "PmrA",
      "concept_type": "PROTEIN",
      "mentions": [
        {"section_id": "sec_1", "start": 26, "end": 30, "text": "PmrA"}
      ]
    }
  ],
  "causal_relations": [
    {
      "id": "R1",
      "cause_entity_id": "E1",
      "cause_text": "mild acid (pH 5.8)",
      "cause_span": [405, 423],
      "effect_entity_id": "E2",
      "effect_text": "transcription of PmrA-activated genes",
      "effect_span": [433, 470],
      "relation_type": "UPREGULATES",
      "trigger_text": "promotes",
      "trigger_span": [424, 432],
      "scope": "LOCAL",
      "is_direct": true,
      "is_inferred": false,
      "evidence_section": "Introduction",
      "evidence_sentence": "Growth in mild acid (pH 5.8) promotes transcription of genes activated by the response regulator PmrA.",
      "evidence_offsets": [405, 508],
      "adjudication_status": "CONSENSUS"
    }
  ]
}
```

---

## 2. Field Specifications

- `is_synthetic` (*boolean*): Must be `false` for all real full-text scientific papers; `true` only for procedural sanity fixtures.
- `scope` (*enum*): `LOCAL` (same sentence), `PARA` (same paragraph), `CROSS_PAGE` (distinct sections/pages), `TRANSITIVE` (graph deduction).
- `is_direct` (*boolean*): Explicit causal assertion stated by authors.
- `is_inferred` (*boolean*): Synthesized transitive path ($A \to C$) not explicitly asserted in a single statement.
- `adjudication_status` (*enum*): `CONSENSUS`, `RESOLVED`, `GOLD_CURATOR`.
