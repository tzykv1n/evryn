"""
System B: LLM-Only Causal Extraction Backend for EVRYN.
Extracts candidate causal assertions using an LLM provider with structured JSON outputs.
"""

import time
import json
from typing import List, Dict, Any, Optional, Set, Tuple

from evryn.paper.types import (
    ScientificDocument,
    CausalAssertion,
    SentenceSpan,
)
from evryn.nlp.llm.schema import CausalRelationRecord, ValidationStatus
from evryn.nlp.llm.providers import BaseLLMProvider, LLMGenerationResult, create_llm_provider
from evryn.nlp.llm.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, PROMPT_VERSION
from evryn.nlp.llm.cache import LLMCache


class LLMCausalExtractor:
    """
    Candidate relation extractor using an LLM provider (System B).
    """
    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        cache: Optional[LLMCache] = None,
        enable_cache: bool = True,
        max_sentences_per_batch: int = 5,
        temperature: float = 0.0,
    ):
        self.provider = provider or create_llm_provider()
        self.cache = cache or LLMCache()
        self.enable_cache = enable_cache
        self.max_sentences_per_batch = max_sentences_per_batch
        self.temperature = temperature

        # Metrics recording
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_latency_seconds = 0.0
        self.total_cost_usd = 0.0
        self.total_calls = 0
        self.cache_hits = 0
        self.errors: List[str] = []

    def reset_metrics(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_latency_seconds = 0.0
        self.total_cost_usd = 0.0
        self.total_calls = 0
        self.cache_hits = 0
        self.errors.clear()

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "cache_hits": self.cache_hits,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_latency_seconds": round(self.total_latency_seconds, 4),
            "estimated_cost_usd": round(self.total_cost_usd, 6),
            "model_name": self.provider.model_name,
            "error_count": len(self.errors),
        }

    def extract_candidates_from_text(
        self,
        text: str,
        doc_id: str = "doc_001",
        page_number: int = 1,
        section_title: str = "Results",
        canonical_entities: Optional[List[str]] = None,
    ) -> List[CausalRelationRecord]:
        """Extract candidate relations from a passage of text."""
        ent_str = "\n".join([f"- {e}" for e in (canonical_entities or [])]) or "None specified."
        user_prompt = USER_PROMPT_TEMPLATE.format(
            doc_id=doc_id,
            page_number=page_number,
            section_title=section_title,
            canonical_entities=ent_str,
            text=text,
        )

        gen_res = None
        if self.enable_cache:
            cached = self.cache.get(
                model_name=self.provider.model_name,
                prompt_version=PROMPT_VERSION,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=self.temperature,
            )
            if cached and "response" in cached:
                self.cache_hits += 1
                r = cached["response"]
                gen_res = LLMGenerationResult(
                    text=r.get("text", ""),
                    parsed_json=r.get("parsed_json"),
                    prompt_tokens=r.get("prompt_tokens", 0),
                    completion_tokens=r.get("completion_tokens", 0),
                    total_tokens=r.get("total_tokens", 0),
                    latency_seconds=0.0,
                    model_name=self.provider.model_name,
                    provider_name="cached",
                    estimated_cost_usd=0.0,
                    is_cached=True,
                )

        if gen_res is None:
            self.total_calls += 1
            gen_res = self.provider.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=self.temperature,
            )
            if gen_res.error:
                self.errors.append(gen_res.error)

            if self.enable_cache and not gen_res.error:
                self.cache.set(
                    model_name=self.provider.model_name,
                    prompt_version=PROMPT_VERSION,
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    response_data={
                        "text": gen_res.text,
                        "parsed_json": gen_res.parsed_json,
                        "prompt_tokens": gen_res.prompt_tokens,
                        "completion_tokens": gen_res.completion_tokens,
                        "total_tokens": gen_res.total_tokens,
                    },
                    temperature=self.temperature,
                )

        # Track usage
        self.total_prompt_tokens += gen_res.prompt_tokens
        self.total_completion_tokens += gen_res.completion_tokens
        self.total_latency_seconds += gen_res.latency_seconds
        self.total_cost_usd += gen_res.estimated_cost_usd

        # Parse JSON into records
        records: List[CausalRelationRecord] = []
        raw_items = gen_res.parsed_json
        if raw_items is None and gen_res.text:
            try:
                raw_items = json.loads(gen_res.text)
                if isinstance(raw_items, dict) and "relations" in raw_items:
                    raw_items = raw_items["relations"]
            except Exception as e:
                self.errors.append(f"JSON decode failure: {e}")

        if isinstance(raw_items, list):
            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                c_ent = item.get("cause_entity", "").strip()
                e_ent = item.get("effect_entity", "").strip()
                if not c_ent or not e_ent:
                    continue
                rec = CausalRelationRecord(
                    cause_entity=c_ent,
                    effect_entity=e_ent,
                    relation_type=item.get("relation_type", "DIRECT_CAUSE"),
                    polarity=item.get("polarity", "POSITIVE"),
                    modality=item.get("modality", "FACTUAL"),
                    evidence_text=item.get("evidence_text", text[:200]),
                    document_id=doc_id,
                    page_number=page_number,
                    extraction_method="llm_candidate",
                    direct_or_inferred="direct",
                    validation_status=ValidationStatus.PENDING.value,
                    confidence=float(item.get("confidence", 0.80)),
                    model_name=self.provider.model_name,
                    prompt_version=PROMPT_VERSION,
                )
                records.append(rec)

        return records

    def extract_document_records(
        self,
        doc: ScientificDocument,
        known_entities: Optional[List[str]] = None,
    ) -> List[CausalRelationRecord]:
        """Extract candidate relations across all paragraphs of a document."""
        all_records: List[CausalRelationRecord] = []

        # If document has paragraphs, iterate over paragraphs
        passages = []
        if doc.paragraphs:
            for p in doc.paragraphs:
                if len(p.text.strip()) > 30:
                    passages.append((p.text, p.page_number, p.section_title))
        elif doc.sentences:
            # Batch sentences
            batch_text = []
            curr_page = 1
            curr_sec = "Main"
            for s in doc.sentences:
                curr_page = s.page_number
                curr_sec = s.section_title
                batch_text.append(s.text)
                if len(batch_text) >= self.max_sentences_per_batch:
                    passages.append((" ".join(batch_text), curr_page, curr_sec))
                    batch_text = []
            if batch_text:
                passages.append((" ".join(batch_text), curr_page, curr_sec))
        else:
            passages.append((doc.full_text[:3000], 1, "Full Document"))

        for text, page_num, sec_title in passages:
            recs = self.extract_candidates_from_text(
                text=text,
                doc_id=doc.doc_id,
                page_number=page_num,
                section_title=sec_title,
                canonical_entities=known_entities,
            )
            all_records.extend(recs)

        return all_records

    def extract_assertions(
        self,
        doc: ScientificDocument,
        known_entities: Optional[List[str]] = None,
    ) -> List[CausalAssertion]:
        """
        Public extraction entrypoint conforming to PaperCausalExtractor interface.
        Returns EVRYN CausalAssertion objects directly from LLM output.
        """
        records = self.extract_document_records(doc, known_entities=known_entities)
        return [rec.to_causal_assertion() for rec in records]
