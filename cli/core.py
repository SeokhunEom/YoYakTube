#!/usr/bin/env python3
"""
YoYakTube CLI 공통 기능 모듈
Streamlit 의존성 없이 동작하는 핵심 기능들
"""

import re
import os
import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse
from datetime import timedelta


# ============================================================================
# 비디오 ID 추출
# ============================================================================

def extract_video_id(url: str) -> Optional[str]:
    """YouTube URL에서 비디오 ID 추출"""
    if not url:
        return None
    
    # 이미 비디오 ID인 경우 (11자리 영숫자)
    if len(url) == 11 and re.match(r'^[A-Za-z0-9_\-]{11}$', url):
        return url
    
    # watch?v= 형태
    q = parse_qs(urlparse(url).query).get("v")
    if q and len(q[0]) >= 10:
        return q[0]
    
    # youtu.be/ 형태
    m = re.search(r"youtu\.be/([A-Za-z0-9_\-]{6,})", url)
    if m:
        return m.group(1)
    
    # shorts 형태
    m = re.search(r"/shorts/([A-Za-z0-9_\-]{6,})", url)
    if m:
        return m.group(1)
    
    return None


# ============================================================================
# 메타데이터 추출
# ============================================================================

def fetch_video_metadata(video_id: str) -> Optional[Dict[str, Any]]:
    """yt-dlp를 사용하여 비디오 메타데이터 추출"""
    try:
        from yt_dlp import YoutubeDL
    except ImportError:
        logging.error("yt-dlp가 설치되지 않았습니다: pip install yt-dlp")
        return None

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "nocheckcertificate": True,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        return {
            "id": video_id,
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "uploader_id": info.get("uploader_id"),
            "uploader_url": info.get("uploader_url"),
            "duration": info.get("duration"),  # seconds
            "upload_date": info.get("upload_date"),  # YYYYMMDD
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "description": info.get("description"),
            "tags": info.get("tags", []),
            "category": info.get("category"),
            "webpage_url": info.get("webpage_url") or url,
        }
    except Exception as e:
        logging.error(f"메타데이터 추출 실패: {e}")
        return None


# ============================================================================
# 자막 추출
# ============================================================================

def collect_transcript(video_id: str, languages: List[str] = None) -> Optional[Tuple[str, str]]:
    """비디오에서 자막 텍스트 추출"""
    try:
        from youtube_transcript_api import (
            NoTranscriptFound, TranscriptsDisabled, 
            VideoUnavailable, YouTubeTranscriptApi
        )
    except ImportError:
        logging.error("youtube-transcript-api가 설치되지 않았습니다")
        return None
    
    if not languages:
        languages = ["ko", "en", "ja"]
    
    try:
        # 기본 자막 시도
        lines = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        text = " ".join(s.get("text", "") for s in lines if s.get("text", "").strip())
        return (text, "auto") if text.strip() else None
        
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable):
        try:
            # 생성된 자막 시도
            api = YouTubeTranscriptApi()
            tr_list = api.list(video_id)
            
            # 선호 언어 순서대로 시도
            for lang in languages:
                try:
                    tr = tr_list.find_generated_transcript([lang])
                    fetched = tr.fetch()
                    text = " ".join(
                        getattr(entry, "text", "")
                        for entry in fetched
                        if getattr(entry, "text", "").strip()
                    )
                    return (text, lang) if text.strip() else None
                except:
                    continue
            
            return None
        except Exception:
            return None
    except Exception:
        return None


def collect_transcript_entries(video_id: str, languages: List[str] = None) -> Optional[Tuple[List[Dict], str]]:
    """비디오에서 타임스탬프가 포함된 자막 엔트리 추출"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        logging.error("youtube-transcript-api가 설치되지 않았습니다")
        return None
    
    if not languages:
        languages = ["ko", "en", "ja"]
    
    try:
        lines = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        return (lines, "auto") if lines else None
    except Exception:
        return None


# ============================================================================
# LLM 클라이언트 (Streamlit 의존성 제거)
# ============================================================================

@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatResponse:
    content: str
    usage: Dict[str, int]
    model: str


class LLMClient:
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model

    def chat(self, messages: List[ChatMessage], temperature: float = 0.2) -> ChatResponse:
        raise NotImplementedError


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        super().__init__("openai", model)
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai 패키지가 설치되지 않았습니다")
        
        self._client = OpenAI(api_key=api_key)

    def chat(self, messages: List[ChatMessage], temperature: float = 0.2) -> ChatResponse:
        payload = [{"role": m.role, "content": m.content} for m in messages]
        kwargs = {"model": self.model, "messages": payload}
        
        if not str(self.model).startswith("gpt-5"):
            kwargs["temperature"] = temperature

        try:
            r = self._client.chat.completions.create(**kwargs)
        except Exception as e:
            if "temperature" in str(e).lower():
                kwargs.pop("temperature", None)
                r = self._client.chat.completions.create(**kwargs)
            else:
                raise

        msg = r.choices[0].message.content or ""
        usage = getattr(r, "usage", None)
        usage_dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        if usage:
            try:
                usage_dict = {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                }
            except Exception:
                pass
        
        return ChatResponse(content=msg.strip(), usage=usage_dict, model=self.model)


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        super().__init__("gemini", model)
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai 패키지가 필요합니다")
        
        self._genai = genai
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    def chat(self, messages: List[ChatMessage], temperature: float = 0.2) -> ChatResponse:
        sys = "\n".join(m.content for m in messages if m.role == "system")
        convo = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in messages if m.role != "system"
        )
        prompt = (sys + "\n\n" + convo).strip()
        
        try:
            r = self._model.generate_content(
                prompt, generation_config={"temperature": temperature}
            )
        except Exception as e:
            if "temperature" in str(e).lower():
                r = self._model.generate_content(prompt)
            else:
                raise
        
        text = getattr(r, "text", "") or ""
        return ChatResponse(
            content=text.strip(),
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            model=self.model,
        )


class OllamaClient(LLMClient):
    def __init__(self, host: str, model: str):
        super().__init__("ollama", model)
        self.host = host.rstrip("/")

    def chat(self, messages: List[ChatMessage], temperature: float = 0.2) -> ChatResponse:
        import requests
        
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature}
        }
        
        try:
            r = requests.post(f"{self.host}/api/chat", json=payload, timeout=60)
            r.raise_for_status()
        except Exception:
            # temperature 제거하고 재시도
            payload.pop("options", None)
            r = requests.post(f"{self.host}/api/chat", json=payload, timeout=60)
            r.raise_for_status()
        
        data = r.json()
        content = (data.get("message", {}) or {}).get("content", "") or ""
        return ChatResponse(
            content=content.strip(),
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            model=self.model,
        )


def get_or_create_llm(provider: str, model: str, openai_key: str, gemini_key: str, ollama_host: str) -> LLMClient:
    """LLM 클라이언트 생성 (Streamlit 세션 상태 없이)"""
    if provider == "openai":
        if not openai_key:
            raise ValueError("OpenAI API Key가 필요합니다")
        return OpenAIClient(api_key=openai_key, model=model)
    elif provider == "gemini":
        if not gemini_key:
            raise ValueError("Gemini API Key가 필요합니다")
        return GeminiClient(api_key=gemini_key, model=model)
    elif provider == "ollama":
        return OllamaClient(host=ollama_host, model=model)
    else:
        raise ValueError(f"지원하지 않는 제공자: {provider}")


# ============================================================================
# 설정 관리
# ============================================================================

def get_config() -> Dict[str, Any]:
    """설정 로드 (Streamlit 없이)"""
    # 환경 변수에서 설정 파일 경로 확인
    config_path = os.getenv("YYT_CONFIG")
    if not config_path:
        config_path = os.path.join(os.getcwd(), "yoyaktube.config.json")
    
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass
    
    # 기본값 설정
    if "providers" not in config:
        env_providers = os.getenv("YYT_PROVIDERS")
        if env_providers:
            config["providers"] = [p.strip() for p in env_providers.split(",")]
        else:
            config["providers"] = ["openai", "gemini", "ollama"]
    
    return config


# ============================================================================
# 유틸리티 함수들
# ============================================================================

def format_hms(seconds: Optional[float]) -> str:
    """초를 H:MM:SS 형식으로 변환"""
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
    source_url: str = None,
    duration_sec: float = None,
    upload_date: str = None,
    transcript_entries: List[Dict] = None,
    plain_transcript: str = None,
) -> str:
    """LLM 요약을 위한 컨텍스트 구성"""
    parts = []
    
    # 메타데이터 헤더
    if source_url:
        parts.append(f"[SOURCE]\n{source_url}")
    if duration_sec is not None:
        parts.append(f"[DURATION]\n{format_hms(float(duration_sec))}")
    if upload_date:
        parts.append(f"[UPLOAD_DATE]\n{upload_date}")
    
    # 자막 본문
    if transcript_entries:
        lines = []
        for e in transcript_entries:
            text = e.get("text", "").strip()
            if not text:
                continue
            ts = format_hms(float(e.get("start", 0.0)))
            lines.append(f"[{ts}] {text}")
        if lines:
            parts.append("[TRANSCRIPT]\n" + "\n".join(lines))
    elif plain_transcript:
        parts.append("[TRANSCRIPT]\n" + plain_transcript)
    
    return "\n\n".join(parts)


def create_qa_context(transcript: str, chat_history: List[Dict] = None) -> str:
    """Q&A를 위한 컨텍스트 구성"""
    parts = []
    
    if transcript:
        parts.append(f"[자막 내용]\n{transcript}")
    
    if chat_history:
        parts.append("[이전 대화]")
        for item in chat_history[-3:]:  # 최근 3개만
            parts.append(f"Q: {item.get('question', '')}")
            parts.append(f"A: {item.get('answer', '')}")
    
    return "\n\n".join(parts)


# ============================================================================
# 상수들
# ============================================================================

ALLOWED_PROVIDERS = ["openai", "gemini", "ollama"]

SYS_KO = """당신은 한국어 유튜브 영상 자막을 분석하고 요약하는 전문가입니다."""

FULL_SUMMARY_PROMPT = """다음 YouTube 영상의 자막을 분석하여 한국어로 구조화된 요약을 제공해주세요.

요약 형식:
## 📝 주요 내용
- 핵심 포인트들을 3-5개 불릿으로 정리

## ⏰ 주요 타임스탬프
- [시간] 중요한 내용 (자막에 타임스탬프가 있는 경우)

## 💡 핵심 메시지
- 영상의 핵심 메시지나 결론

## 🎯 대상 독자
- 이 영상이 도움이 될 사람들

가독성이 좋도록 마크다운 형식으로 작성해주세요."""

QA_SYSTEM_PROMPT = """당신은 YouTube 영상 자막을 기반으로 질문에 답변하는 AI 어시스턴트입니다.

주어진 자막 내용을 참고하여 정확하고 도움이 되는 답변을 한국어로 제공해주세요.
자막에 없는 내용에 대해서는 "자막에서 해당 내용을 찾을 수 없습니다"라고 말해주세요."""