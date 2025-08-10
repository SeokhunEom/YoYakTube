from __future__ import annotations

from typing import List, Optional

import requests
import streamlit as st

from .config import get_available_providers
from .i18n import TEXT
from . import state
from . import utils
from .llm import ChatMessage, get_or_create_llm, supports_temperature
from .utils import format_hms


@st.cache_data(ttl=60)
def get_ollama_models_cached(host: str) -> List[str]:
    try:
        resp = requests.get(f"{host.rstrip('/')}/api/tags", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        return [m.get("name") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


def explain_llm_error(e: Exception) -> None:
    from requests import ConnectionError, HTTPError, Timeout

    msg = TEXT["errors"]["llm_generic"]
    hint: Optional[str] = None
    try:
        if isinstance(e, Timeout):
            hint = TEXT["errors"]["llm_timeout"]
        elif isinstance(e, ConnectionError):
            hint = TEXT["errors"]["llm_connection"]
        elif isinstance(e, HTTPError):
            code = e.response.status_code if getattr(e, "response", None) else None
            if code == 401:
                hint = TEXT["errors"]["llm_auth"]
            elif code == 429:
                hint = TEXT["errors"]["llm_rate"]
            elif code in (500, 502, 503, 504):
                hint = TEXT["errors"]["llm_unavailable"]
        else:
            s = str(e).lower()
            if "rate limit" in s or "429" in s:
                hint = TEXT["errors"]["llm_rate"]
            elif "timeout" in s:
                hint = TEXT["errors"]["llm_timeout"]
            elif "unauthorized" in s or "invalid api key" in s or "api key" in s:
                hint = TEXT["errors"]["llm_auth"]
            elif "unavailable" in s or "overloaded" in s:
                hint = TEXT["errors"]["llm_unavailable"]
    except Exception:  # noqa: BLE001
        pass
    show_error(msg, hint)


def show_error(title: str, hint: Optional[str] = None) -> None:
    if hint:
        st.error(f"{title}\n\n💡 {hint}")
    else:
        st.error(title)


def render_provider_sidebar() -> tuple[str, str, str, str, str, str]:
    st.sidebar.header(TEXT["sidebar"]["header"])
    provider_list = get_available_providers()
    provider = st.sidebar.selectbox(TEXT["sidebar"]["provider"], provider_list, index=0)

    if "model_openai" not in st.session_state:
        st.session_state.model_openai = "gpt-5-mini"
    if "model_gemini" not in st.session_state:
        st.session_state.model_gemini = "gemini-2.5-flash"
    if "model_ollama" not in st.session_state:
        st.session_state.model_ollama = ""

    openai_key = ""
    gemini_key = ""
    ollama_host = ""

    if provider == "openai":
        model = st.sidebar.selectbox(
            TEXT["sidebar"]["openai_model"],
            options=["gpt-5-mini", "gpt-5", "gpt-5-nano"],
            index=["gpt-5-mini", "gpt-5", "gpt-5-nano"].index(
                st.session_state.get("model_openai", "gpt-5-mini")
            ),
            key="model_openai",
        )
        openai_key = st.sidebar.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.get("openai_key", "") or "",
            key="openai_key",
        )
    elif provider == "gemini":
        options = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
        model = st.sidebar.selectbox(
            TEXT["sidebar"]["gemini_model"],
            options=options,
            index=options.index(
                st.session_state.get("model_gemini", "gemini-2.5-flash")
            ),
            key="model_gemini",
        )
        gemini_key = st.sidebar.text_input(
            "Gemini API Key",
            type="password",
            value=st.session_state.get("gemini_key", "") or "",
            key="gemini_key",
        )
    elif provider == "ollama":
        ollama_host = st.sidebar.text_input(
            TEXT["sidebar"]["ollama_host"],
            value=st.session_state.get("ollama_host", "") or "http://localhost:11434",
            key="ollama_host",
        )
        col_host, col_refresh = st.sidebar.columns([4, 1])
        with col_host:
            st.write("")
        if col_refresh.button("↻", help=TEXT["sidebar"]["refresh"]):
            get_ollama_models_cached.clear()  # type: ignore[attr-defined]
        ollama_models = get_ollama_models_cached(ollama_host) or [""]
        current_model = st.session_state.get("model_ollama", ollama_models[0])
        if current_model not in ollama_models:
            current_model = ollama_models[0]
        model = st.sidebar.selectbox(
            "Ollama Model",
            options=ollama_models,
            index=ollama_models.index(current_model),
            key="model_ollama",
        )
    else:
        model = ""

    if provider == "openai" and (not model or not openai_key):
        st.sidebar.warning(TEXT["sidebar"]["warn_openai"])
    elif provider == "gemini" and (not model or not gemini_key):
        st.sidebar.warning(TEXT["sidebar"]["warn_gemini"])
    elif provider == "ollama" and (not model or not ollama_host):
        st.sidebar.warning(TEXT["sidebar"]["warn_ollama"])

    langs = st.sidebar.text_input(TEXT["sidebar"]["langs"], value="ko,en,ja")
    return provider, model, openai_key, gemini_key, ollama_host, langs


def render_transcript_toggle_once() -> None:
    transcript = state.get_transcript()
    if not transcript:
        return
    job = state.get_job()
    stage = job.get("stage") if job else None
    if stage not in (None, "done") and not state.get_summary():
        return
    show_transcript = st.session_state.get("show_transcript", False)
    if not show_transcript:
        return

    st.caption(TEXT["labels"].get("transcript_label", "자막 (읽기 전용)"))
    st.text_area(label="", value=transcript, height=320, disabled=True)
    # 닫기는 툴바의 토글 버튼으로 처리


def render_result_toolbar(
    vid: Optional[str],
    provider: str,
    model: str,
    openai_key: str,
    gemini_key: str,
    ollama_host: str,
) -> bool:
    # Row 1: 요약하기 | 자막보기
    col1, col2 = st.columns([1, 1])

    has_summary = bool(state.get_summary())
    has_transcript = bool(state.get_transcript())
    job = state.get_job()
    busy = bool(job and job.get("stage") in ("fetching", "summarizing"))

    summarize_clicked = col1.button(
        TEXT["buttons"]["summarize"],
        use_container_width=True,
        disabled=busy
        or not utils.provider_ready(
            provider, model, openai_key, gemini_key, ollama_host
        ),
        key="btn_summarize",
    )

    current_show = st.session_state.get("show_transcript", False)
    toggle_label = (
        TEXT["labels"].get("transcript_close", "자막 닫기")
        if current_show
        else TEXT["labels"].get("transcript_open", "자막 보기")
    )
    if col2.button(
        toggle_label,
        use_container_width=True,
        disabled=busy or (not has_transcript),
        key="btn_toolbar_toggle_transcript",
    ):
        st.session_state["show_transcript"] = not current_show
        st.rerun()

    # Row 2: 저장 버튼 3개
    d1, d2, d3 = st.columns([1, 1, 1])
    summary_value = state.get_summary() or ""
    summary_md = utils.make_summary_md(summary_value, vid)
    transcript_txt = utils.make_transcript_txt(state.get_transcript() or "")
    combined_md = utils.make_combined_md(
        state.get_summary() if has_summary else "",
        state.get_transcript() if has_transcript else "",
        vid,
    )

    d1.download_button(
        label=TEXT["buttons"]["dl_summary"],
        data=summary_md if has_summary else "",
        file_name=f"summary_{vid or 'video'}.md",
        mime="text/markdown",
        use_container_width=True,
        disabled=busy or (not has_summary),
        key="download_summary_btn",
    )
    d2.download_button(
        label=TEXT["buttons"]["dl_transcript"],
        data=transcript_txt if has_transcript else "",
        file_name=f"transcript_{vid or 'video'}.txt",
        mime="text/plain",
        use_container_width=True,
        disabled=busy or (not has_transcript),
        key="download_transcript_btn_menu",
    )
    d3.download_button(
        label=TEXT["buttons"]["dl_both"],
        data=combined_md if (has_summary or has_transcript) else "",
        file_name=f"summary_transcript_{vid or 'video'}.md",
        mime="text/markdown",
        use_container_width=True,
        disabled=busy or (not (has_summary or has_transcript)),
        key="download_both_btn",
    )

    return summarize_clicked


def render_chat_section(
    provider: str, model: str, openai_key: str, gemini_key: str, ollama_host: str
) -> None:
    st.subheader(TEXT["labels"]["chat_header"])

    for msg in state.get_chat():
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

    user_question = st.chat_input(TEXT["labels"]["chat_input"])
    if user_question:
        state.append_chat("user", user_question)
        with st.chat_message("user"):
            st.markdown(user_question)
        context = utils.build_qa_context(
            state.get_summary() or "", state.get_transcript()
        )
        llm = get_or_create_llm(provider, model, openai_key, gemini_key, ollama_host)
        msgs: List[ChatMessage] = [
            ChatMessage(
                role="system",
                content="You are a helpful assistant that writes concise Korean summaries for YouTube transcripts.",
            )
        ]
        if context:
            msgs.append(ChatMessage(role="user", content=f"[CONTEXT]\n{context}"))
        for h in state.get_chat()[:-1]:
            msgs.append(ChatMessage(role=h["role"], content=h["content"]))
        msgs.append(ChatMessage(role="user", content=user_question))
        temp = 0.2 if supports_temperature(provider, model) else 1
        with st.chat_message("assistant"):
            with st.spinner(TEXT["spinners"]["answering"]):
                try:
                    resp = llm.chat(msgs, temperature=temp)
                    answer = resp.content
                    st.markdown(answer)
                    state.append_chat("assistant", answer)
                except Exception as e:  # noqa: BLE001
                    explain_llm_error(e)


def render_video_metadata(meta: Optional[dict]) -> None:
    if not meta:
        return
    title = meta.get("title")
    channel = meta.get("channel")
    duration = meta.get("duration")
    upload_date = meta.get("upload_date")
    parts: list[str] = []
    if title:
        parts.append(f"🧾 {title}")
    if channel:
        parts.append(f"📺 {channel}")
    if duration is not None:
        parts.append(f"⏱️ {format_hms(float(duration))}")
    if upload_date:
        parts.append(f"🗓️ {upload_date}")
    if parts:
        st.caption(" | ".join(parts))
