from __future__ import annotations

import logging

import streamlit as st

from . import i18n, ui, utils, transcript, state, metadata
from .constants import PROMPT_VERSION, SYS_KO, FULL_SUMMARY_PROMPT
from .state import get_transcript_entries, get_video_meta
from .llm import ChatMessage, get_or_create_llm, supports_temperature


def run() -> None:
    logging.basicConfig(level=logging.INFO)

    st.set_page_config(page_title="YoYakTube", page_icon="🤖", layout="wide")
    st.title("YoYakTube - YouTube 영상 요약 & 질문 챗봇")
    # Ensure minimal required session keys are initialized
    if "_job_state" not in st.session_state:
        st.session_state["_job_state"] = None

    st.markdown(
        """
        <style>
        div.stButton > button,
        div.stDownloadButton > button,
        div.stDownloadButton > a {
            height: 56px; min-height: 56px; line-height: 56px; padding: 0 16px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 16px;
            display: inline-flex; align-items: center; justify-content: center;
        }
        /* Remove default horizontal rules spacing look by hiding the rule used previously */
        hr { display: none; }

        /* Responsive: stack columns on small screens */
        @media (max-width: 768px) {
            [data-testid="stHorizontalBlock"] { flex-direction: column !important; align-items: stretch !important; }
            [data-testid="column"] { width: 100% !important; flex: 0 0 100% !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    provider, model, openai_key, gemini_key, ollama_host, langs = (
        ui.render_provider_sidebar()
    )

    yt_url = st.text_input(i18n.TEXT["labels"]["enter_url"])

    if "transcript_text" not in st.session_state:
        st.session_state["transcript_text"] = None
    if "summary" not in st.session_state:
        st.session_state["summary"] = None

    if yt_url:
        vid = utils.extract_video_id(yt_url)

        # Ensure session keys
        if "_chat_messages" not in st.session_state:
            st.session_state["_chat_messages"] = []
        if "_active_video_id" not in st.session_state:
            st.session_state["_active_video_id"] = None

        if vid and st.session_state["_active_video_id"] != vid:
            state.reset_state_for_new_video(vid)

        # Layout: Left (video + summary), Right (chat)
        left_col, right_col = st.columns([3, 2])

        # Left: video and toolbar
        with left_col:
            if vid:
                st.video(f"https://www.youtube.com/watch?v={vid}")
                # Fetch and render video metadata once per video
                if not state.get_video_meta():
                    meta = metadata.cached_fetch_video_metadata(vid)
                    if meta:
                        state.set_video_meta(meta)
                ui.render_video_metadata(state.get_video_meta())
            else:
                st.warning(i18n.TEXT["labels"]["video_invalid"])

            summarize_clicked = ui.render_result_toolbar(
                vid=vid,
                provider=provider,
                model=model,
                openai_key=openai_key,
                gemini_key=gemini_key,
                ollama_host=ollama_host,
            )

        # Prepare left content containers later to control order

        # Start summarization job if requested
        if summarize_clicked and vid:
            state.start_job(vid)

        # Job processing with spinner inside the left column
        job = state.get_job()
        if (
            job
            and job.get("vid") == vid
            and job.get("stage") in ("fetching", "summarizing")
        ):
            with left_col:
                with st.spinner(
                    i18n.TEXT["spinners"]["fetching_transcript"]
                    if job.get("stage") == "fetching"
                    else i18n.TEXT["spinners"]["summarizing"]
                ):
                    if job.get("stage") == "fetching":
                        # Fetch plain transcript text and entries (timestamps)
                        fetched = transcript.cached_fetch_transcript(vid, langs)
                        fetched_entries = transcript.cached_fetch_transcript_entries(
                            vid, langs
                        )
                        if not fetched:
                            ui.show_error(
                                i18n.TEXT["errors"]["no_transcript"],
                                i18n.TEXT["errors"]["no_transcript_hint"],
                            )
                            state.set_job_stage("error", error="no_transcript")
                        else:
                            text, _lang_code = fetched
                            state.set_transcript(text)
                            # store timestamped entries if available
                            if fetched_entries:
                                entries, _lc = fetched_entries
                                state.set_transcript_entries(entries)
                            state.set_job_stage("summarizing")
                            st.rerun()

                    job = state.get_job()
                    if (
                        job
                        and job.get("stage") == "summarizing"
                        and state.get_transcript()
                    ):
                        llm = get_or_create_llm(
                            provider, model, openai_key, gemini_key, ollama_host
                        )
                        # Build enriched context: source URL, duration, upload date, timestamped transcript
                        entries = get_transcript_entries()
                        plain_text = state.get_transcript()
                        meta = get_video_meta() or {}
                        source_url = (
                            f"https://www.youtube.com/watch?v={vid}" if vid else None
                        )
                        duration_sec = (
                            meta.get("duration") if isinstance(meta, dict) else None
                        )
                        upload_date = (
                            meta.get("upload_date") if isinstance(meta, dict) else None
                        )
                        enriched_context = utils.build_llm_summary_context(
                            source_url=source_url,
                            duration_sec=duration_sec,
                            upload_date=upload_date,
                            transcript_entries=entries,
                            plain_transcript=plain_text,
                        )
                        msgs = [
                            ChatMessage(role="system", content=SYS_KO),
                            ChatMessage(
                                role="user",
                                content=FULL_SUMMARY_PROMPT.format(
                                    transcript=enriched_context
                                ),
                            ),
                        ]
                        temp = 0.2 if supports_temperature(provider, model) else 1
                        try:
                            resp = llm.chat(msgs, temperature=temp)
                            state.set_summary(resp.content)
                            state.set_summary_meta(provider, model, PROMPT_VERSION)
                            state.set_job_stage("done")
                            st.rerun()
                        except Exception as e:
                            ui.explain_llm_error(e)
                            state.set_job_stage("error", error=str(e))

        # After summary is ready, render transcript (top) + summary (below) on the left, chat on the right
        if state.get_summary():
            with left_col:
                ui.render_transcript_toggle_once()
                st.subheader(i18n.TEXT["labels"]["summary"])
                st.write(state.get_summary())
            with right_col:
                ui.render_chat_section(
                    provider, model, openai_key, gemini_key, ollama_host
                )
    else:
        st.info(i18n.TEXT["labels"]["need_url"])
