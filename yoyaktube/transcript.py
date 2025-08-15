from __future__ import annotations

from typing import List, Optional, Tuple, Dict, Any
import sys
from pathlib import Path

# Conditionally import streamlit
try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False

# CLI core 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from cli.core import collect_transcript, collect_transcript_entries


def fetch_transcript_text(video_id: str, langs: List[str]) -> Optional[Tuple[str, str]]:
    """CLI core 모듈의 collect_transcript를 래핑"""
    return collect_transcript(video_id, langs)


if _HAS_STREAMLIT:
    @st.cache_data(ttl=3600, show_spinner=False)
    def cached_fetch_transcript(video_id: str, langs_key: str) -> Optional[Tuple[str, str]]:
        langs_list = [s.strip() for s in langs_key.split(",") if s.strip()]
        return fetch_transcript_text(video_id, langs_list)

    @st.cache_data(ttl=3600, show_spinner=False)
    def cached_fetch_transcript_entries(
        video_id: str, langs_key: str
    ) -> Optional[Tuple[List[Dict[str, Any]], str]]:
        langs_list = [s.strip() for s in langs_key.split(",") if s.strip()]
        return fetch_transcript_entries(video_id, langs_list)
else:
    # Fallback implementations without caching for CLI usage
    def cached_fetch_transcript(video_id: str, langs_key: str) -> Optional[Tuple[str, str]]:
        langs_list = [s.strip() for s in langs_key.split(",") if s.strip()]
        return fetch_transcript_text(video_id, langs_list)

    def cached_fetch_transcript_entries(
        video_id: str, langs_key: str
    ) -> Optional[Tuple[List[Dict[str, Any]], str]]:
        langs_list = [s.strip() for s in langs_key.split(",") if s.strip()]
        return fetch_transcript_entries(video_id, langs_list)


def fetch_transcript_entries(
    video_id: str, langs: List[str]
) -> Optional[Tuple[List[dict], str]]:
    """CLI core 모듈의 collect_transcript_entries를 래핑"""
    return collect_transcript_entries(video_id, langs)
