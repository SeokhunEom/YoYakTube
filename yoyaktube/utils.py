from __future__ import annotations

import re
import logging
from typing import Optional

import streamlit as st

from .state import get_summary_meta
from datetime import timedelta


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
    from urllib.parse import parse_qs, urlparse

    q = parse_qs(urlparse(url).query).get("v")
    if q and len(q[0]) >= 10:
        return q[0]
    m = re.search(r"youtu\.be/([A-Za-z0-9_\-]{6,})", url)
    if m:
        return m.group(1)
    m = re.search(r"/shorts/([A-Za-z0-9_\-]{6,})", url)
    if m:
        return m.group(1)
    return None


def make_summary_md(summary: str, vid: Optional[str]) -> str:
    if not summary:
        return ""
    link = f"https://www.youtube.com/watch?v={vid}" if vid else ""
    meta = get_summary_meta()
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
    meta = get_summary_meta()
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
    if not seconds and seconds != 0:
        return ""
    try:
        td = timedelta(seconds=int(seconds))
        total_seconds = int(td.total_seconds())
        hrs = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    except Exception:
        return ""


def build_llm_summary_context(
    *,
    source_url: str | None,
    duration_sec: float | int | None,
    upload_date: str | None,
    transcript_entries: Optional[list],
    plain_transcript: Optional[str],
) -> str:
    parts: list[str] = []
    # Metadata header
    if source_url:
        parts.append(f"[SOURCE]\n{source_url}")
    if duration_sec is not None:
        parts.append(f"[DURATION]\n{format_hms(float(duration_sec))}")
    if upload_date:
        # Accept YYYYMMDD or other; pass through
        parts.append(f"[UPLOAD_DATE]\n{upload_date}")
    # Transcript body
    if transcript_entries:
        lines: list[str] = []
        for e in transcript_entries:
            t = e.get("text", "").strip()
            if not t:
                continue
            ts = format_hms(float(e.get("start", 0.0)))
            lines.append(f"[{ts}] {t}")
        if lines:
            parts.append("[TRANSCRIPT]\n" + "\n".join(lines))
    elif plain_transcript:
        parts.append("[TRANSCRIPT]\n" + plain_transcript)
    return "\n\n".join(parts)


def show_error(title: str, hint: Optional[str] = None):
    if hint:
        st.error(f"{title}\n\n💡 {hint}")
    else:
        st.error(title)


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
