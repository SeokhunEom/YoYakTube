from __future__ import annotations

import re
import logging
from typing import Optional
import sys
from pathlib import Path

# Conditionally import streamlit-dependent modules
try:
    import streamlit as st
    from .state import get_summary_meta
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False
from datetime import timedelta

# CLI core 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from cli.core import extract_video_id as _extract_video_id, format_hms as _format_hms, build_llm_summary_context as _build_llm_summary_context


def provider_ready(
    provider: str, model: str, openai_key: str, gemini_key: str, ollama_host: str
) -> bool:
    if provider == "openai":
        return bool(model) and bool(openai_key)
    if provider == "gemini":
        return bool(model) and bool(gemini_key)
    if provider == "ollama":
        return bool(model) and bool(ollama_host)
    return False


def extract_video_id(url: str) -> Optional[str]:
    """CLI core 모듈의 extract_video_id를 래핑"""
    return _extract_video_id(url)


def make_summary_md(summary: str, vid: Optional[str]) -> str:
    if not summary:
        return ""
    link = f"https://www.youtube.com/watch?v={vid}" if vid else ""
    meta = get_summary_meta() if _HAS_STREAMLIT else {}
    footer = (
        f"\n\n---\n_meta_: provider={meta.get('provider','')}, "
        f"model={meta.get('model','')}, prompt={meta.get('prompt_version','')}\n"
    )
    return (
        f"# 요약\n\n{summary}\n\n" + (f"[영상 링크]({link})\n" if link else "") + footer
    )


def make_transcript_txt(transcript: str) -> str:
    return transcript or ""


def make_combined_md(
    summary: Optional[str], transcript: Optional[str], vid: Optional[str]
) -> str:
    if not (summary or transcript):
        return ""
    meta = get_summary_meta() if _HAS_STREAMLIT else {}
    parts = ["# 영상 요약 및 자막\n"]
    if vid:
        parts.append(f"- Video: https://www.youtube.com/watch?v={vid}\n")
    if summary:
        parts.append(f"\n## 요약\n\n{summary}\n")
    if transcript:
        parts.append(f"\n## 자막\n\n```\n{transcript}\n```\n")
    parts.append(
        f"\n---\n_meta_: provider={meta.get('provider','')}, "
        f"model={meta.get('model','')}, prompt={meta.get('prompt_version','')}\n"
    )
    return "".join(parts)


def build_qa_context(
    summary: str, transcript: Optional[str], extra_chars: int = 4000
) -> str:
    # Use full transcript when available per requirement
    if transcript:
        parts = []
        if summary:
            parts.append(summary)
        parts.append("[원문 전체]\n" + transcript)
        return "\n\n".join(parts)
    return summary or ""


def format_hms(seconds: Optional[float]) -> str:
    """CLI core 모듈의 format_hms를 래핑"""
    return _format_hms(seconds)


def build_llm_summary_context(
    *,
    source_url: str | None,
    duration_sec: float | int | None,
    upload_date: str | None,
    transcript_entries: Optional[list],
    plain_transcript: Optional[str],
) -> str:
    """CLI core 모듈의 build_llm_summary_context를 래핑"""
    return _build_llm_summary_context(
        source_url=source_url,
        duration_sec=duration_sec,
        upload_date=upload_date,
        transcript_entries=transcript_entries,
        plain_transcript=plain_transcript,
    )


def show_error(title: str, hint: Optional[str] = None):
    if _HAS_STREAMLIT:
        if hint:
            st.error(f"{title}\n\n💡 {hint}")
        else:
            st.error(title)
    else:
        # Fallback for CLI usage
        if hint:
            print(f"Error: {title}\n💡 {hint}")
        else:
            print(f"Error: {title}")


def explain_llm_error(e: Exception, *, text_errors: dict):
    from requests import HTTPError, Timeout, ConnectionError

    msg = text_errors.get("llm_generic", "오류가 발생했습니다.")
    hint = None
    try:
        if isinstance(e, Timeout):
            hint = text_errors.get("llm_timeout")
        elif isinstance(e, ConnectionError):
            hint = text_errors.get("llm_connection")
        elif isinstance(e, HTTPError):
            code = e.response.status_code if getattr(e, "response", None) else None
            if code == 401:
                hint = text_errors.get("llm_auth")
            elif code == 429:
                hint = text_errors.get("llm_rate")
            elif code in (500, 502, 503, 504):
                hint = text_errors.get("llm_unavailable")
        else:
            s = str(e).lower()
            if "rate limit" in s or "429" in s:
                hint = text_errors.get("llm_rate")
            elif "timeout" in s:
                hint = text_errors.get("llm_timeout")
            elif "unauthorized" in s or "invalid api key" in s or "api key" in s:
                hint = text_errors.get("llm_auth")
            elif "unavailable" in s or "overloaded" in s:
                hint = text_errors.get("llm_unavailable")
    except Exception:
        pass
    show_error(msg, hint)
