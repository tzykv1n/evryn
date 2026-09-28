# evryn cache --status

import os
import json
import pickle
import time
import hashlib
from typing import Any, Optional, Dict, List


class EvrynCache:

    def __init__(
        self,
        cache_dir: str = "cache",
        enabled: bool = True,
        force_rebuild: bool = False,
    ):
        self.cache_dir = cache_dir
        self.enabled = enabled
        self.force_rebuild = force_rebuild
        self.hits = 0
        self.misses = 0
        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)

    def _get_paths(self, stage: str, key: str) -> tuple[str, str]:
        stage_dir = os.path.join(self.cache_dir, stage)
        os.makedirs(stage_dir, exist_ok=True)
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()
        data_path = os.path.join(stage_dir, f"{h}.pkl")
        meta_path = os.path.join(stage_dir, f"{h}.meta.json")
        return data_path, meta_path

    def get(self, stage: str, key: str) -> Optional[Any]:
        if not self.enabled or self.force_rebuild:
            self.misses += 1
            return None

        data_path, meta_path = self._get_paths(stage, key)
        if not (os.path.exists(data_path) and os.path.exists(meta_path)):
            self.misses += 1
            return None

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if meta.get("key") != key:
                self.misses += 1
                return None

            with open(data_path, "rb") as f:
                obj = pickle.load(f)
            self.hits += 1
            return obj
        except Exception:
            self.misses += 1
            return None

    def set(self, stage: str, key: str, obj: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not self.enabled:
            return

        data_path, meta_path = self._get_paths(stage, key)
        tmp_data = f"{data_path}.tmp"
        tmp_meta = f"{meta_path}.tmp"

        try:
            with open(tmp_data, "wb") as f:
                pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)

            meta = {
                "key": key,
                "key_hash": hashlib.sha256(key.encode("utf-8")).hexdigest(),
                "stage": stage,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": time.time(),
                "size_bytes": os.path.getsize(tmp_data),
                "custom_metadata": metadata or {},
            }
            with open(tmp_meta, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            os.replace(tmp_data, data_path)
            os.replace(tmp_meta, meta_path)
        except Exception:
            if os.path.exists(tmp_data):
                try:
                    os.remove(tmp_data)
                except OSError:
                    pass
            if os.path.exists(tmp_meta):
                try:
                    os.remove(tmp_meta)
                except OSError:
                    pass

    def invalidate(self, stage: Optional[str] = None) -> int:
        if not os.path.exists(self.cache_dir):
            return 0

        count = 0
        stages = [stage] if stage else os.listdir(self.cache_dir)
        for s in stages:
            s_path = os.path.join(self.cache_dir, s)
            if os.path.isdir(s_path):
                for fname in os.listdir(s_path):
                    f_path = os.path.join(s_path, fname)
                    try:
                        if os.path.isfile(f_path):
                            os.remove(f_path)
                            count += 1
                    except OSError:
                        pass
        return count

    def list_entries(self) -> List[Dict[str, Any]]:
        entries = []
        if not os.path.exists(self.cache_dir):
            return entries

        for stage in sorted(os.listdir(self.cache_dir)):
            s_path = os.path.join(self.cache_dir, stage)
            if not os.path.isdir(s_path):
                continue
            for fname in sorted(os.listdir(s_path)):
                if fname.endswith(".meta.json"):
                    try:
                        with open(os.path.join(s_path, fname), "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            entries.append(meta)
                    except Exception:
                        continue
        return entries
