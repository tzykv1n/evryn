"""
Factory for instantiating and selecting the extraction backend:
  - System A: nlp_baseline (Current repaired NLP rules pipeline)
  - System B: llm_only (Direct LLM extraction without strict validation)
  - System C: hybrid (Hybrid LLM proposition + deterministic validation)
"""

from typing import Optional, Any
from evryn.paper.extractor import PaperCausalExtractor
from evryn.nlp.llm.extractor import LLMCausalExtractor
from evryn.nlp.llm.hybrid import HybridCausalExtractor
from evryn.nlp.llm.providers import create_llm_provider, BaseLLMProvider
from evryn.paper.normalizer import PaperEntityNormalizer


def get_extraction_backend(
    system_mode: str = "nlp_baseline",
    provider: Optional[BaseLLMProvider] = None,
    model_name: Optional[str] = None,
    normalizer: Optional[PaperEntityNormalizer] = None,
    **kwargs: Any,
) -> Any:
    """
    Returns an extraction backend providing the common `extract_assertions(doc, known_entities)` interface.
    """
    norm = normalizer or PaperEntityNormalizer()
    mode = system_mode.lower().replace("-", "_")

    if mode in ("system_a", "nlp", "nlp_baseline", "baseline"):
        return PaperCausalExtractor(normalizer=norm, **kwargs)

    prov = provider or create_llm_provider(model_name=model_name)

    if mode in ("system_b", "llm", "llm_only"):
        return LLMCausalExtractor(provider=prov, **kwargs)

    elif mode in ("system_c", "hybrid", "hybrid_llm", "hybrid_validated"):
        llm_ext = LLMCausalExtractor(provider=prov, **kwargs)
        return HybridCausalExtractor(llm_extractor=llm_ext, normalizer=norm)

    else:
        raise ValueError(
            f"Unknown extraction system mode '{system_mode}'. "
            "Supported modes: 'nlp_baseline' (System A), 'llm_only' (System B), 'hybrid' (System C)."
        )
