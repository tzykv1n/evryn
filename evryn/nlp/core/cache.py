# python cli.py cache --status

import os
import shutil
import pickle
import json
import time
import hashlib
from typing import Any, Optional, Dict, List


class ArtifactCache:
    VERSION = "1.0.0"

    def __init__(self, cache_dir: str = "cache", enabled: bool = True, force_rebuild: bool = False):
        self.cache_dir = cache_dir
        self.enabled = enabled
        self.force_rebuild = force_rebuild
        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)

    def _get_paths(self, stage: str, key_hash: str):
        stage_dir = os.path.join(self.cache_dir, stage)
        os.makedirs(stage_dir, exist_ok=True)
        data_path = os.path.join(stage_dir, f"{key_hash}.pkl")
        meta_path = os.path.join(stage_dir, f"{key_hash}.meta.json")
        return data_path, meta_path

    def has(self, stage: str, key_hash: str) -> bool:
        if not self.enabled or self.force_rebuild:
            return False
        data_path, meta_path = self._get_paths(stage, key_hash)
        if not (os.path.exists(data_path) and os.path.exists(meta_path)):
            return False
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if meta.get("version") != self.VERSION:
                return False
            expected_size = meta.get("size_bytes")
            actual_size = os.path.getsize(data_path)
            return expected_size == actual_size
        except Exception:
            return False

    def get(self, stage: str, key_hash: str) -> Optional[Any]:
        if not self.has(stage, key_hash):
            return None
        data_path, _ = self._get_paths(stage, key_hash)
        try:
            with open(data_path, "rb") as f:
                data = pickle.load(f)
            return data
        except Exception:
            self.remove(stage, key_hash)
            return None

    def set(self, stage: str, key_hash: str, artifact: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        if not self.enabled:
            return ""
        data_path, meta_path = self._get_paths(stage, key_hash)
        temp_data = f"{data_path}.tmp"
        with open(temp_data, "wb") as f:
            pickle.dump(artifact, f, protocol=pickle.HIGHEST_PROTOCOL)

        size_bytes = os.path.getsize(temp_data)
        os.replace(temp_data, data_path)

        meta: Dict[str, Any] = {
            "version": self.VERSION,
            "stage": stage,
            "key_hash": key_hash,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "size_bytes": size_bytes,
        }
        if metadata:
            meta.update(metadata)

        temp_meta = f"{meta_path}.tmp"
        with open(temp_meta, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        os.replace(temp_meta, meta_path)
        return data_path

    def remove(self, stage: str, key_hash: str) -> None:
        data_path, meta_path = self._get_paths(stage, key_hash)
        if os.path.exists(data_path):
            os.remove(data_path)
        if os.path.exists(meta_path):
            os.remove(meta_path)

    def invalidate(self, stage: Optional[str] = None) -> int:
        count = 0
        if stage:
            stage_dir = os.path.join(self.cache_dir, stage)
            if os.path.exists(stage_dir):
                count = len(os.listdir(stage_dir)) // 2
                shutil.rmtree(stage_dir)
        else:
            if os.path.exists(self.cache_dir):
                for root, dirs, files in os.walk(self.cache_dir):
                    count += len([f for f in files if f.endswith(".pkl")])
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
        return count

    def list_entries(self) -> List[Dict[str, Any]]:
        entries = []
        if not os.path.exists(self.cache_dir):
            return entries
        for root, dirs, files in os.walk(self.cache_dir):
            for f in files:
                if f.endswith(".meta.json"):
                    meta_path = os.path.join(root, f)
                    try:
                        with open(meta_path, "r", encoding="utf-8") as fp:
                            entries.append(json.load(fp))
                    except Exception:
                        pass
        return entries
