from __future__ import annotations

from typing import Dict, List, Optional

import streamlit as st

from .constants import (
    SS_TRANSCRIPT,
    SS_TRANSCRIPT_ENTRIES,
    SS_VIDEO_META,
    SS_SUMMARY,
    SS_CHAT,
    SS_ACTIVE_VID,
    SS_JOB,
    SS_META,
)


def get_transcript() -> Optional[str]:
    return st.session_state.get(SS_TRANSCRIPT)


def set_transcript(text: Optional[str]) -> None:
    st.session_state[SS_TRANSCRIPT] = text


def get_summary() -> Optional[str]:
    return st.session_state.get(SS_SUMMARY)


def set_summary(text: Optional[str]) -> None:
    st.session_state[SS_SUMMARY] = text


def get_chat() -> List[Dict[str, str]]:
    if SS_CHAT not in st.session_state:
        st.session_state[SS_CHAT] = []
    return st.session_state[SS_CHAT]


def append_chat(role: str, content: str) -> None:
    get_chat().append({"role": role, "content": content})


def reset_state_for_new_video(new_vid: str) -> None:
    st.session_state[SS_ACTIVE_VID] = new_vid
    st.session_state[SS_CHAT] = []
    st.session_state[SS_TRANSCRIPT] = None
    if SS_TRANSCRIPT_ENTRIES in st.session_state:
        del st.session_state[SS_TRANSCRIPT_ENTRIES]
    if SS_VIDEO_META in st.session_state:
        del st.session_state[SS_VIDEO_META]
    st.session_state[SS_SUMMARY] = None
    if SS_META in st.session_state:
        del st.session_state[SS_META]
    if "show_transcript" in st.session_state:
        del st.session_state["show_transcript"]
    if SS_JOB in st.session_state:
        del st.session_state[SS_JOB]


def get_job() -> Optional[dict]:
    return st.session_state.get(SS_JOB)


def start_job(vid: str) -> None:
    st.session_state[SS_JOB] = {"vid": vid, "stage": "fetching", "error": None}


def set_job_stage(stage: str, error: Optional[str] = None) -> None:
    job = st.session_state.get(SS_JOB) or {}
    job["stage"] = stage
    job["error"] = error
    st.session_state[SS_JOB] = job


def clear_job() -> None:
    if SS_JOB in st.session_state:
        del st.session_state[SS_JOB]


def set_transcript_entries(entries: Optional[list]) -> None:
    st.session_state[SS_TRANSCRIPT_ENTRIES] = entries


def get_transcript_entries() -> Optional[list]:
    return st.session_state.get(SS_TRANSCRIPT_ENTRIES)


def set_video_meta(meta: Optional[dict]) -> None:
    st.session_state[SS_VIDEO_META] = meta


def get_video_meta() -> Optional[dict]:
    return st.session_state.get(SS_VIDEO_META)


def set_summary_meta(provider: str, model: str, prompt_version: str) -> None:
    st.session_state[SS_META] = {
        "provider": provider,
        "model": model,
        "prompt_version": prompt_version,
    }


def get_summary_meta() -> dict:
    return st.session_state.get(SS_META, {})
