from __future__ import annotations

import os
from typing import List, Optional

from .constants import ALLOWED_PROVIDERS


def _load_config_file() -> Optional[dict]:
    import json as _json

    path = os.getenv("YYT_CONFIG")
    if not path:
        default_path = os.path.join(os.getcwd(), "yoyaktube.config.json")
        if os.path.exists(default_path):
            path = default_path
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return None


def get_available_providers() -> List[str]:
    cfg = _load_config_file() or {}
    providers = cfg.get("providers")
    if not providers:
        env_val = os.getenv("YYT_PROVIDERS")
        if env_val:
            providers = [p.strip() for p in env_val.split(",") if p.strip()]
    if not providers:
        providers = ["openai", "gemini", "ollama"]
    providers = [p for p in providers if p in ALLOWED_PROVIDERS]
    if not providers:
        providers = ["openai"]
    return providers
