"""
YoYakTube - YouTube Video Summarization and Q&A Chatbot

A tool for extracting transcripts from YouTube videos and generating 
structured Korean summaries using various LLM providers.
"""

__version__ = "0.1.0"
__author__ = "YoYakTube Team"

from .utils import extract_video_id, format_hms, build_llm_summary_context
from .transcript import collect_transcript, collect_transcript_entries
from .metadata import fetch_video_metadata
from .llm import OpenAIClient, get_or_create_llm

__all__ = [
    "extract_video_id",
    "format_hms", 
    "build_llm_summary_context",
    "collect_transcript",
    "collect_transcript_entries",
    "fetch_video_metadata",
    "OpenAIClient",
    "get_or_create_llm"
]