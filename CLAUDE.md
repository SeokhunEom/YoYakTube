# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YoYakTube is a Streamlit-based YouTube video summarization and Q&A chatbot that extracts transcripts from YouTube videos and generates structured Korean summaries using various LLM providers (OpenAI, Google Gemini, Ollama).

## Development Commands

### Running the Application
```bash
streamlit run app.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Virtual Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Architecture

### Entry Point
- `app.py`: Simple entry point that imports and runs the main app
- `yoyaktube/app_main.py`: Core application orchestration with Streamlit UI setup

### Core Modules
- `yoyaktube/ui.py`: Sidebar, toolbar, chat interface, and metadata display components
- `yoyaktube/state.py`: Streamlit session state management wrapper
- `yoyaktube/transcript.py`: YouTube transcript collection with caching (`st.cache_data`)
- `yoyaktube/metadata.py`: Video metadata extraction using yt-dlp with caching
- `yoyaktube/llm.py`: Multi-provider LLM client abstraction (OpenAI/Gemini/Ollama)
- `yoyaktube/config.py`: Provider configuration loading from files/environment variables
- `yoyaktube/constants.py`: Application constants, prompts, and session keys
- `yoyaktube/i18n.py`: Korean UI text localization
- `yoyaktube/utils.py`: Utilities for video ID extraction, formatting, and markdown generation

### LLM Provider Configuration
The app supports multiple LLM providers with the following priority:
1. JSON config file specified by `YYT_CONFIG` environment variable
2. `yoyaktube.config.json` in current working directory
3. `YYT_PROVIDERS` environment variable (comma-separated: `openai,gemini,ollama`)
4. Default: `["openai", "gemini", "ollama"]`

### Session State Management
Session keys are defined in `constants.py` and accessed through `state.py` wrapper functions:
- `SS_TRANSCRIPT`: Raw transcript text
- `SS_TRANSCRIPT_ENTRIES`: Timestamped transcript entries
- `SS_VIDEO_META`: Video metadata (title, channel, duration, etc.)
- `SS_SUMMARY`: Generated summary
- `SS_LLM`: Cached LLM client instance
- `SS_CHAT`: Chat message history

### Caching Strategy
- Transcript and metadata use `st.cache_data` with 1-hour TTL (3600 seconds)
- LLM client instances are cached in session state to avoid recreation
- Video processing results are cached by video ID

### Key Features
- Multi-language subtitle support with priority ordering (e.g., "ko,en,ja")
- Structured Korean summaries with timestamp highlighting
- Q&A chat using summary/transcript as context
- Export functionality for summaries (.md) and transcripts (.txt)
- Responsive UI with mobile support

## Important Implementation Details

### Video ID Extraction
- Supports both `youtube.com/watch?v=` and `youtu.be/` URL formats
- Video ID validation and extraction handled in `utils.py`

### Error Handling
- Robust error handling for API calls with retry logic (tenacity)
- Provider-specific error messages for authentication and rate limiting
- Graceful fallbacks when transcripts are unavailable

### UI Layout
- Wide layout with responsive column stacking on mobile
- Custom CSS for consistent button sizing and spacing
- Sidebar configuration with real-time model list refresh for Ollama

### Prompts and Context
- Main summarization prompt in `constants.py` as `FULL_SUMMARY_PROMPT`
- Chat context construction utilities in `utils.py`
- Version tracking for prompts via `PROMPT_VERSION` constant