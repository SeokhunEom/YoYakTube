from __future__ import annotations

import os
from typing import List, Optional
import sys
from pathlib import Path

from .constants import ALLOWED_PROVIDERS

# CLI core 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from cli.core import get_config as _get_config, ALLOWED_PROVIDERS as _ALLOWED_PROVIDERS


def _load_config_file() -> Optional[dict]:
    """CLI core의 get_config를 래핑"""
    return _get_config()


def get_available_providers() -> List[str]:
    """CLI core의 get_config를 사용하여 제공자 목록 반환"""
    cfg = _get_config()
    providers = cfg.get("providers", ["openai", "gemini", "ollama"])
    providers = [p for p in providers if p in _ALLOWED_PROVIDERS]
    if not providers:
        providers = ["openai"]
    return providers
