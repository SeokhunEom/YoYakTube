from __future__ import annotations

from typing import List, Optional, Tuple, Dict, Any

import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)


@retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
def fetch_transcript_text(video_id: str, langs: List[str]) -> Optional[Tuple[str, str]]:
    preferred = langs or ["en"]

    try:
        if hasattr(YouTubeTranscriptApi, "fetch") and callable(
            getattr(YouTubeTranscriptApi, "fetch", None)
        ):
            api = YouTubeTranscriptApi()
            fetched = api.fetch(video_id, languages=preferred)
            if hasattr(fetched, "to_raw_data"):
                data = fetched.to_raw_data()
                text = " ".join(
                    d.get("text", "") for d in data if d.get("text", "").strip()
                )
            else:
                text = " ".join(
                    getattr(sn, "text", "")
                    for sn in fetched
                    if getattr(sn, "text", "").strip()
                )
            lang_code = (
                getattr(fetched, "language_code", None)
                or getattr(fetched, "language", None)
                or "unknown"
            )
            return (text, lang_code) if text.strip() else None
    except NoTranscriptFound:
        try:
            api = YouTubeTranscriptApi()
            tr_list = api.list(video_id)
            try:
                tr = tr_list.find_transcript(preferred)
            except NoTranscriptFound:
                tr = None
            if tr is None:
                try:
                    tr = tr_list.find_generated_transcript(preferred)
                except Exception:
                    tr = None
            if tr is not None:
                fetched = tr.fetch()
                if hasattr(fetched, "to_raw_data"):
                    data = fetched.to_raw_data()
                    text = " ".join(
                        d.get("text", "") for d in data if d.get("text", "").strip()
                    )
                else:
                    text = " ".join(
                        getattr(sn, "text", "")
                        for sn in fetched
                        if getattr(sn, "text", "").strip()
                    )
                lang_code = (
                    getattr(fetched, "language_code", None)
                    or getattr(fetched, "language", None)
                    or getattr(tr, "language_code", None)
                    or "unknown"
                )
                return (text, lang_code) if text.strip() else None
        except (NoTranscriptFound, Exception):
            pass
    except (TranscriptsDisabled, VideoUnavailable):
        return None
    except Exception:
        pass

    try:
        if hasattr(YouTubeTranscriptApi, "get_transcript"):
            lines = YouTubeTranscriptApi.get_transcript(video_id, languages=preferred)
            text = " ".join(
                s.get("text", "") for s in lines if s.get("text", "").strip()
            )
            return (text, "auto") if text.strip() else None
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable):
        return None
    except Exception:
        return None

    return None


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


def fetch_transcript_entries(
    video_id: str, langs: List[str]
) -> Optional[Tuple[List[dict], str]]:
    preferred = langs or ["en"]
    try:
        lines = YouTubeTranscriptApi.get_transcript(video_id, languages=preferred)
        return (lines, "auto") if lines else None
    except Exception:
        return None
