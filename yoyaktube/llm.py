from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Iterable
import sys
from pathlib import Path

import requests
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential

from .constants import LLM_CAPS, SS_LLM, SS_LLM_CFG, logger

# CLI core 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from cli.core import (
    ChatMessage as CoreChatMessage, 
    ChatResponse as CoreChatResponse,
    LLMClient as CoreLLMClient,
    get_or_create_llm as _get_or_create_llm
)


# 기존 클래스들은 CLI core에서 import한 것으로 대체
ChatMessage = CoreChatMessage
ChatResponse = CoreChatResponse
LLMClient = CoreLLMClient


# 기존 클라이언트들은 CLI core에서 import (더 이상 필요 없음)


def build_llm(
    provider: str, model: str, openai_key: str, gemini_key: str, ollama_host: str
) -> LLMClient:
    """CLI core의 get_or_create_llm을 래핑하여 Streamlit 경고 추가"""
    try:
        return _get_or_create_llm(provider, model, openai_key, gemini_key, ollama_host)
    except ValueError as e:
        if "OpenAI API Key" in str(e):
            st.warning("OpenAI Key가 필요합니다.")
        elif "Gemini API Key" in str(e):
            st.warning("Gemini Key가 필요합니다.")
        # MockClient 대신 에러 재발생
        raise


def _current_llm_config(
    provider: str, model: str, openai_key: str, gemini_key: str, ollama_host: str
) -> dict:
    return {
        "provider": provider,
        "model": model or "",
        "openai_key": (openai_key or "***"),
        "gemini_key": (gemini_key or "***"),
        "ollama_host": (ollama_host or ""),
    }


def get_or_create_llm(
    provider: str, model: str, openai_key: str, gemini_key: str, ollama_host: str
) -> LLMClient:
    cfg = _current_llm_config(provider, model, openai_key, gemini_key, ollama_host)
    if SS_LLM not in st.session_state or st.session_state.get(SS_LLM_CFG) != cfg:
        st.session_state[SS_LLM] = build_llm(
            provider, model, openai_key, gemini_key, ollama_host
        )
        st.session_state[SS_LLM_CFG] = cfg
        logger.info("LLM instance (re)created: %s", cfg)
    return st.session_state[SS_LLM]


def supports_temperature(provider: str, model: str) -> bool:
    return LLM_CAPS.get(provider, {}).get("supports_temperature", lambda _m: True)(
        model
    )
