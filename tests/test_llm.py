import pytest
from unittest.mock import patch, Mock, MagicMock
import openai
from typing import List, Dict, Any


class TestOpenAIClient:
    """Tests for OpenAIClient class"""

    @patch("yoyaktube.llm.openai.OpenAI")
    def test_openai_client_initialization(self, mock_openai, api_keys):
        """Test OpenAI client initialization"""
        from Core.llm import OpenAIClient

        client = OpenAIClient(api_keys["openai"], "gpt-4")

        assert client.api_key == api_keys["openai"]
        assert client.model == "gpt-4"
        mock_openai.assert_called_once_with(api_key=api_keys["openai"])

    @patch("yoyaktube.llm.openai.OpenAI")
    def test_openai_client_chat_success(
        self, mock_openai, api_keys, sample_chat_messages
    ):
        """Test successful OpenAI chat completion"""
        from Core.llm import OpenAIClient

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = (
            "이 영상은 테스트에 대한 설명을 제공합니다."
        )
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 25
        mock_response.usage.total_tokens = 125

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        client = OpenAIClient(api_keys["openai"], "gpt-4")
        result = client.chat(sample_chat_messages)

        assert result is not None
        assert result["content"] == "이 영상은 테스트에 대한 설명을 제공합니다."
        assert result["usage"]["prompt_tokens"] == 100
        assert result["usage"]["completion_tokens"] == 25
        assert result["usage"]["total_tokens"] == 125

        # Verify API call parameters
        mock_client_instance.chat.completions.create.assert_called_once()
        call_args = mock_client_instance.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-4"
        assert call_args[1]["messages"] == sample_chat_messages
        assert call_args[1]["temperature"] == 0.2  # Default temperature

    @patch("yoyaktube.llm.openai.OpenAI")
    def test_openai_client_chat_with_custom_temperature(
        self, mock_openai, api_keys, sample_chat_messages
    ):
        """Test OpenAI chat with custom temperature"""
        from Core.llm import OpenAIClient

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 60

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        client = OpenAIClient(api_keys["openai"], "gpt-4")
        result = client.chat(sample_chat_messages, temperature=0.7)

        # Verify custom temperature is used
        call_args = mock_client_instance.chat.completions.create.call_args
        assert call_args[1]["temperature"] == 0.7

    @patch("yoyaktube.llm.openai.OpenAI")
    def test_openai_client_api_error(self, mock_openai, api_keys, sample_chat_messages):
        """Test handling OpenAI API errors"""
        from Core.llm import OpenAIClient

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.side_effect = openai.OpenAIError(
            "API Error"
        )
        mock_openai.return_value = mock_client_instance

        client = OpenAIClient(api_keys["openai"], "gpt-4")

        with pytest.raises(openai.OpenAIError):
            client.chat(sample_chat_messages)

    @patch("yoyaktube.llm.openai.OpenAI")
    def test_openai_client_authentication_error(
        self, mock_openai, sample_chat_messages
    ):
        """Test handling authentication error"""
        from Core.llm import OpenAIClient

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.side_effect = (
            openai.AuthenticationError("Invalid API key")
        )
        mock_openai.return_value = mock_client_instance

        client = OpenAIClient("invalid-key", "gpt-4")

        with pytest.raises(openai.AuthenticationError):
            client.chat(sample_chat_messages)

    @patch("yoyaktube.llm.openai.OpenAI")
    def test_openai_client_rate_limit_error(
        self, mock_openai, api_keys, sample_chat_messages
    ):
        """Test handling rate limit error"""
        from Core.llm import OpenAIClient

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.side_effect = (
            openai.RateLimitError("Rate limit exceeded")
        )
        mock_openai.return_value = mock_client_instance

        client = OpenAIClient(api_keys["openai"], "gpt-4")

        with pytest.raises(openai.RateLimitError):
            client.chat(sample_chat_messages)

    @patch("yoyaktube.llm.openai.OpenAI")
    def test_openai_client_empty_messages(self, mock_openai, api_keys):
        """Test handling empty messages list"""
        from Core.llm import OpenAIClient

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Empty response"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        client = OpenAIClient(api_keys["openai"], "gpt-4")
        result = client.chat([])

        assert result is not None
        assert result["content"] == "Empty response"


class TestGetOrCreateLlm:
    """Tests for get_or_create_llm factory function"""

    @patch("yoyaktube.llm.OpenAIClient")
    def test_create_openai_client(self, mock_openai_client, api_keys):
        """Test creating OpenAI client"""
        from Core.llm import get_or_create_llm

        mock_client_instance = Mock()
        mock_openai_client.return_value = mock_client_instance

        result = get_or_create_llm(
            provider="openai",
            model="gpt-4",
            openai_key=api_keys["openai"],
            gemini_key="",
            ollama_host="",
        )

        assert result == mock_client_instance
        mock_openai_client.assert_called_once_with(api_keys["openai"], "gpt-4")

    def test_create_openai_client_missing_key(self):
        """Test creating OpenAI client with missing API key"""
        from Core.llm import get_or_create_llm

        with pytest.raises(ValueError, match="OpenAI API key is required"):
            get_or_create_llm(
                provider="openai",
                model="gpt-4",
                openai_key="",
                gemini_key="",
                ollama_host="",
            )

    def test_create_openai_client_none_key(self):
        """Test creating OpenAI client with None API key"""
        from Core.llm import get_or_create_llm

        with pytest.raises(ValueError, match="OpenAI API key is required"):
            get_or_create_llm(
                provider="openai",
                model="gpt-4",
                openai_key=None,
                gemini_key="",
                ollama_host="",
            )

    def test_unsupported_provider(self, api_keys):
        """Test error for unsupported provider"""
        from Core.llm import get_or_create_llm

        with pytest.raises(ValueError, match="Unsupported provider"):
            get_or_create_llm(
                provider="unsupported",
                model="test-model",
                openai_key=api_keys["openai"],
                gemini_key="",
                ollama_host="",
            )

    def test_empty_provider(self, api_keys):
        """Test error for empty provider"""
        from Core.llm import get_or_create_llm

        with pytest.raises(ValueError, match="Provider is required"):
            get_or_create_llm(
                provider="",
                model="gpt-4",
                openai_key=api_keys["openai"],
                gemini_key="",
                ollama_host="",
            )

    def test_none_provider(self, api_keys):
        """Test error for None provider"""
        from Core.llm import get_or_create_llm

        with pytest.raises(ValueError, match="Provider is required"):
            get_or_create_llm(
                provider=None,
                model="gpt-4",
                openai_key=api_keys["openai"],
                gemini_key="",
                ollama_host="",
            )

    @patch("yoyaktube.llm.OpenAIClient")
    def test_empty_model_name(self, mock_openai_client, api_keys):
        """Test creating client with empty model name"""
        from Core.llm import get_or_create_llm

        with pytest.raises(ValueError, match="Model name is required"):
            get_or_create_llm(
                provider="openai",
                model="",
                openai_key=api_keys["openai"],
                gemini_key="",
                ollama_host="",
            )

    @patch("yoyaktube.llm.OpenAIClient")
    def test_none_model_name(self, mock_openai_client, api_keys):
        """Test creating client with None model name"""
        from Core.llm import get_or_create_llm

        with pytest.raises(ValueError, match="Model name is required"):
            get_or_create_llm(
                provider="openai",
                model=None,
                openai_key=api_keys["openai"],
                gemini_key="",
                ollama_host="",
            )


class TestLlmIntegration:
    """Integration tests for LLM functionality"""

    @patch("yoyaktube.llm.openai.OpenAI")
    def test_end_to_end_summarization_flow(
        self, mock_openai, api_keys, sample_transcript_text
    ):
        """Test complete flow from transcript to summary"""
        from Core.llm import get_or_create_llm

        # Mock OpenAI response for summarization
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[
            0
        ].message.content = """# 영상 요약

이 영상은 소프트웨어 테스팅의 중요성에 대해 설명합니다.

## 주요 내용
- 단위 테스트의 필요성
- 통합 테스트의 중요성
- 엔드투엔드 테스트 방법론

## 핵심 포인트
- 테스트는 소프트웨어 품질 보장의 핵심
- 다양한 테스트 유형을 조합하여 사용
- 지속적인 테스트 자동화가 중요"""

        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 300

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        # Create LLM client
        llm = get_or_create_llm(
            provider="openai",
            model="gpt-4",
            openai_key=api_keys["openai"],
            gemini_key="",
            ollama_host="",
        )

        # Prepare summarization messages
        messages = [
            {
                "role": "system",
                "content": "당신은 YouTube 영상 자막을 한국어로 요약하는 전문가입니다.",
            },
            {
                "role": "user",
                "content": f"다음 자막을 요약해주세요:\n\n{sample_transcript_text}",
            },
        ]

        result = llm.chat(messages)

        assert result is not None
        assert "영상 요약" in result["content"]
        assert "주요 내용" in result["content"]
        assert "핵심 포인트" in result["content"]
        assert result["usage"]["total_tokens"] == 300

    @patch("yoyaktube.llm.openai.OpenAI")
    def test_qa_chat_flow(self, mock_openai, api_keys, sample_transcript_text):
        """Test Q&A chat flow with transcript context"""
        from Core.llm import get_or_create_llm

        # Mock OpenAI response for Q&A
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = (
            "이 영상에서는 단위 테스트, 통합 테스트, 엔드투엔드 테스트 총 3가지 유형의 테스트를 다룹니다."
        )

        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 30
        mock_response.usage.total_tokens = 180

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        llm = get_or_create_llm(
            provider="openai",
            model="gpt-4",
            openai_key=api_keys["openai"],
            gemini_key="",
            ollama_host="",
        )

        # Q&A messages with context
        messages = [
            {
                "role": "system",
                "content": f"다음은 YouTube 영상의 자막입니다:\n\n{sample_transcript_text}\n\n이 자막을 바탕으로 질문에 답변해주세요.",
            },
            {
                "role": "user",
                "content": "이 영상에서 다루는 테스트 유형은 몇 가지인가요?",
            },
        ]

        result = llm.chat(messages)

        assert result is not None
        assert "3가지" in result["content"] or "세 가지" in result["content"]
        assert "단위 테스트" in result["content"]
        assert "통합 테스트" in result["content"]
        assert "엔드투엔드 테스트" in result["content"]
