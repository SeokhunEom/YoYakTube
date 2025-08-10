from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Iterable

import requests
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential

from .constants import LLM_CAPS, SS_LLM, SS_LLM_CFG, logger


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

    def chat(
        self, messages: Iterable[ChatMessage], temperature: float = 0.2
    ) -> ChatResponse:
        raise NotImplementedError

    def stream_chat(self, messages: Iterable[ChatMessage], temperature: float = 0.2):
        resp = self.chat(messages, temperature=temperature)
        yield resp.content


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        super().__init__("openai", model)
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:  # noqa: F841
            raise ImportError(
                "openai 패키지가 설치되어 있지 않습니다. requirements.txt를 확인하세요."
            )
        self._OpenAI = OpenAI
        self._client = OpenAI(api_key=api_key)

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3)
    )
    def chat(
        self, messages: Iterable[ChatMessage], temperature: float = 0.2
    ) -> ChatResponse:
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

    def stream_chat(self, messages: Iterable[ChatMessage], temperature: float = 0.2):
        payload = [{"role": m.role, "content": m.content} for m in messages]
        kwargs = {"model": self.model, "messages": payload, "stream": True}
        if not str(self.model).startswith("gpt-5"):
            kwargs["temperature"] = temperature
        try:
            stream = self._client.chat.completions.create(**kwargs)
        except Exception as e:
            if "temperature" in str(e).lower():
                kwargs.pop("temperature", None)
                stream = self._client.chat.completions.create(**kwargs)
            else:
                raise
        for chunk in stream:
            try:
                delta = chunk.choices[0].delta.content or ""
            except Exception:
                delta = ""
            if delta:
                yield delta


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        super().__init__("gemini", model)
        try:
            import google.generativeai as genai  # type: ignore
        except Exception:
            raise ImportError("google-generativeai 패키지가 필요합니다.")
        self._genai = genai
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3)
    )
    def chat(
        self, messages: Iterable[ChatMessage], temperature: float = 0.2
    ) -> ChatResponse:
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

    def stream_chat(self, messages: Iterable[ChatMessage], temperature: float = 0.2):
        sys = "\n".join(m.content for m in messages if m.role == "system")
        convo = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in messages if m.role != "system"
        )
        prompt = (sys + "\n\n" + convo).strip()
        try:
            stream = self._model.generate_content(
                prompt, generation_config={"temperature": temperature}, stream=True
            )
        except Exception as e:
            if "temperature" in str(e).lower():
                stream = self._model.generate_content(prompt, stream=True)
            else:
                raise
        for chunk in stream:
            delta = getattr(chunk, "text", "") or ""
            if delta:
                yield delta


class OllamaClient(LLMClient):
    def __init__(self, host: str, model: str):
        super().__init__("ollama", model)
        self.host = host.rstrip("/")

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3)
    )
    def chat(
        self, messages: Iterable[ChatMessage], temperature: float = 0.2
    ) -> ChatResponse:
        base_payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        payload = dict(base_payload)
        payload["options"] = {"temperature": temperature}
        try:
            r = requests.post(f"{self.host}/api/chat", json=payload, timeout=60)
            r.raise_for_status()
        except Exception as e:
            if hasattr(e, "response") or "temperature" in str(e).lower():
                r = requests.post(
                    f"{self.host}/api/chat", json=base_payload, timeout=60
                )
                r.raise_for_status()
            else:
                raise
        data = r.json()
        content = (data.get("message", {}) or {}).get("content", "") or ""
        return ChatResponse(
            content=content.strip(),
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            model=self.model,
        )

    def stream_chat(self, messages: Iterable[ChatMessage], temperature: float = 0.2):
        base_payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        payload = dict(base_payload)
        payload["options"] = {"temperature": temperature}
        try:
            with requests.post(
                f"{self.host}/api/chat", json=payload, stream=True, timeout=60
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode("utf-8"))
                        delta = (data.get("message") or {}).get("content") or ""
                        if delta:
                            yield delta
                        if data.get("done"):
                            break
                    except Exception:
                        continue
        except Exception:
            for once in [self.chat(messages, temperature=temperature).content]:
                yield once


class MockClient(LLMClient):
    def __init__(self):
        super().__init__("mock", "mock")

    def chat(
        self, messages: Iterable[ChatMessage], temperature: float = 0.0
    ) -> ChatResponse:  # noqa: ARG002
        last_user = next(
            (m.content for m in reversed(list(messages)) if m.role == "user"), ""
        )
        return ChatResponse(
            content=f"[MOCK]\n{last_user[:800]}",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            model=self.model,
        )


def build_llm(
    provider: str, model: str, openai_key: str, gemini_key: str, ollama_host: str
) -> LLMClient:
    if provider == "openai":
        if not openai_key:
            st.warning("OpenAI Key가 필요합니다.")
        return OpenAIClient(api_key=openai_key, model=model)
    if provider == "gemini":
        if not gemini_key:
            st.warning("Gemini Key가 필요합니다.")
        return GeminiClient(api_key=gemini_key, model=model)
    if provider == "ollama":
        return OllamaClient(host=ollama_host, model=model)
    return MockClient()


def _current_llm_config(
    provider: str, model: str, openai_key: str, gemini_key: str, ollama_host: str
) -> dict:
    return {
        "provider": provider,
        "model": model or "",
        "openai_key": (openai_key or "***"),
        "gemini_key": (gemini_key or "***"),
        "ollama_host": (ollama_host or ""),
    }


def get_or_create_llm(
    provider: str, model: str, openai_key: str, gemini_key: str, ollama_host: str
) -> LLMClient:
    cfg = _current_llm_config(provider, model, openai_key, gemini_key, ollama_host)
    if SS_LLM not in st.session_state or st.session_state.get(SS_LLM_CFG) != cfg:
        st.session_state[SS_LLM] = build_llm(
            provider, model, openai_key, gemini_key, ollama_host
        )
        st.session_state[SS_LLM_CFG] = cfg
        logger.info("LLM instance (re)created: %s", cfg)
    return st.session_state[SS_LLM]


def supports_temperature(provider: str, model: str) -> bool:
    return LLM_CAPS.get(provider, {}).get("supports_temperature", lambda _m: True)(
        model
    )
