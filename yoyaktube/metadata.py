from __future__ import annotations

from typing import Optional, Dict, Any

import streamlit as st


def _extract_with_yt_dlp(video_id: str) -> Optional[Dict[str, Any]]:
    try:
        from yt_dlp import YoutubeDL  # type: ignore
    except Exception:
        return None

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "nocheckcertificate": True,
        "extract_flat": True,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return {
            "source_url": info.get("webpage_url") or url,
            "duration": info.get("duration"),  # seconds
            "upload_date": info.get("upload_date"),  # YYYYMMDD
            "title": info.get("title"),
            "channel": info.get("uploader"),
        }
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_video_metadata(video_id: str) -> Optional[Dict[str, Any]]:
    return _extract_with_yt_dlp(video_id)
