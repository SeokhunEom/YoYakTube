from __future__ import annotations

from typing import Optional, Dict, Any
import sys
from pathlib import Path

import streamlit as st

# CLI core 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from cli.core import fetch_video_metadata


def _extract_with_yt_dlp(video_id: str) -> Optional[Dict[str, Any]]:
    """CLI core 모듈의 fetch_video_metadata를 래핑"""
    metadata = fetch_video_metadata(video_id)
    if not metadata:
        return None
    
    # 기존 형식에 맞게 변환
    return {
        "source_url": metadata.get("webpage_url"),
        "duration": metadata.get("duration"),
        "upload_date": metadata.get("upload_date"),
        "title": metadata.get("title"),
        "channel": metadata.get("uploader"),
    }


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_video_metadata(video_id: str) -> Optional[Dict[str, Any]]:
    return _extract_with_yt_dlp(video_id)
