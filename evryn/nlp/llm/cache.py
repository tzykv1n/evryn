"""
Content-hashed persistent disk cache for LLM extraction queries.
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional


class LLMCache:
    def __init__(self, cache_dir: str = "cache/llm"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _compute_key(
        self,
        model_name: str,
        prompt_version: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> str:
        payload = {
            "model_name": model_name,
            "prompt_version": prompt_version,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "temperature": temperature,
            "kwargs": {k: str(v) for k, v in sorted(kwargs.items())},
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def get(
        self,
        model_name: str,
        prompt_version: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        key = self._compute_key(model_name, prompt_version, system_prompt, user_prompt, temperature, **kwargs)
        path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def set(
        self,
        model_name: str,
        prompt_version: str,
        system_prompt: str,
        user_prompt: str,
        response_data: Dict[str, Any],
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> None:
        key = self._compute_key(model_name, prompt_version, system_prompt, user_prompt, temperature, **kwargs)
        path = os.path.join(self.cache_dir, f"{key}.json")
        record = {
            "key": key,
            "model_name": model_name,
            "prompt_version": prompt_version,
            "temperature": temperature,
            "response": response_data,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)
        except Exception:
            pass
