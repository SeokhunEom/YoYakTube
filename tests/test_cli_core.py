#!/usr/bin/env python3
"""Tests for cli/core.py module"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from pathlib import Path
import json

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.core import (
    extract_video_id,
    fetch_video_metadata,
    collect_transcript,
    collect_transcript_entries,
    ChatMessage,
    ChatResponse,
    OpenAIClient,
    GeminiClient,
    OllamaClient,
    get_or_create_llm,
    get_config,
    format_hms,
    build_llm_summary_context,
    create_qa_context
)


class TestVideoIdExtraction(unittest.TestCase):
    
    def test_extract_video_id_youtube_watch(self):
        """Test video ID extraction from youtube.com/watch URLs"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = extract_video_id(url)
        self.assertEqual(result, "dQw4w9WgXcQ")
    
    def test_extract_video_id_youtube_watch_with_params(self):
        """Test video ID extraction with additional parameters"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s&list=PLxx"
        result = extract_video_id(url)
        self.assertEqual(result, "dQw4w9WgXcQ")
    
    def test_extract_video_id_youtu_be(self):
        """Test video ID extraction from youtu.be URLs"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        result = extract_video_id(url)
        self.assertEqual(result, "dQw4w9WgXcQ")
    
    def test_extract_video_id_shorts(self):
        """Test video ID extraction from shorts URLs"""
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        result = extract_video_id(url)
        self.assertEqual(result, "dQw4w9WgXcQ")
    
    def test_extract_video_id_direct_id(self):
        """Test video ID when input is already a video ID"""
        video_id = "dQw4w9WgXcQ"
        result = extract_video_id(video_id)
        self.assertEqual(result, "dQw4w9WgXcQ")
    
    def test_extract_video_id_invalid_url(self):
        """Test video ID extraction from invalid URLs"""
        invalid_urls = [
            "https://example.com",
            "not_a_url",
            "",
            "https://youtube.com",
            "short_id"
        ]
        for url in invalid_urls:
            result = extract_video_id(url)
            self.assertIsNone(result)


class TestMetadataExtraction(unittest.TestCase):
    
    def test_fetch_video_metadata_no_yt_dlp(self):
        """Test metadata extraction when yt-dlp is not available"""
        # 실제 yt-dlp가 없는 경우 None을 반환하는지 테스트
        # 실제 패키지가 없으면 ImportError가 발생해야 함
        try:
            from yt_dlp import YoutubeDL
            # yt-dlp가 있으면 이 테스트는 스킵
            self.skipTest("yt-dlp is available")
        except ImportError:
            # yt-dlp가 없으면 fetch_video_metadata가 None을 반환해야 함
            result = fetch_video_metadata("dQw4w9WgXcQ")
            self.assertIsNone(result)


class TestTranscriptExtraction(unittest.TestCase):
    
    def test_collect_transcript_no_api(self):
        """Test transcript collection when API is not available"""
        # 실제 youtube_transcript_api가 없는 경우 None을 반환하는지 테스트
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            # API가 있으면 이 테스트는 스킵
            self.skipTest("youtube-transcript-api is available")
        except ImportError:
            # API가 없으면 collect_transcript가 None을 반환해야 함
            result = collect_transcript("dQw4w9WgXcQ", ["en"])
            self.assertIsNone(result)
    
    def test_collect_transcript_entries_no_api(self):
        """Test transcript entries collection when API is not available"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            self.skipTest("youtube-transcript-api is available")
        except ImportError:
            result = collect_transcript_entries("dQw4w9WgXcQ", ["en"])
            self.assertIsNone(result)


class TestLLMClients(unittest.TestCase):
    
    def test_chat_message_creation(self):
        """Test ChatMessage creation"""
        message = ChatMessage(role="user", content="Hello")
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello")
    
    def test_chat_response_creation(self):
        """Test ChatResponse creation"""
        response = ChatResponse(
            content="Hi there!",
            usage={"total_tokens": 10},
            model="gpt-4"
        )
        self.assertEqual(response.content, "Hi there!")
        self.assertEqual(response.usage["total_tokens"], 10)
        self.assertEqual(response.model, "gpt-4")
    
    def test_openai_client_creation(self):
        """Test OpenAI client creation without actual API call"""
        try:
            client = OpenAIClient("test_key", "gpt-4")
            self.assertEqual(client.name, "openai")
            self.assertEqual(client.model, "gpt-4")
        except ImportError:
            self.skipTest("openai package not available")
    
    def test_gemini_client_creation(self):
        """Test Gemini client creation without actual API call"""
        try:
            client = GeminiClient("test_key", "gemini-pro")
            self.assertEqual(client.name, "gemini")
            self.assertEqual(client.model, "gemini-pro")
        except ImportError:
            self.skipTest("google-generativeai package not available")
    
    def test_ollama_client_creation(self):
        """Test Ollama client creation"""
        client = OllamaClient("http://localhost:11434", "llama2")
        self.assertEqual(client.name, "ollama")
        self.assertEqual(client.model, "llama2")
        self.assertEqual(client.host, "http://localhost:11434")
    
    def test_get_or_create_llm_missing_key(self):
        """Test LLM client creation with missing API key"""
        with self.assertRaises(ValueError):
            get_or_create_llm("openai", "gpt-4", "", "", "")
    
    def test_get_or_create_llm_invalid_provider(self):
        """Test LLM client creation with invalid provider"""
        with self.assertRaises(ValueError):
            get_or_create_llm("invalid", "model", "key", "", "")
    
    def test_get_or_create_llm_ollama(self):
        """Test LLM client creation for Ollama"""
        client = get_or_create_llm("ollama", "llama2", "", "", "http://localhost:11434")
        self.assertIsInstance(client, OllamaClient)
        self.assertEqual(client.name, "ollama")
        self.assertEqual(client.model, "llama2")


class TestUtilityFunctions(unittest.TestCase):
    
    def test_format_hms_normal(self):
        """Test HMS formatting with normal values"""
        self.assertEqual(format_hms(65), "00:01:05")
        self.assertEqual(format_hms(3661), "01:01:01")
        self.assertEqual(format_hms(0), "00:00:00")
    
    def test_format_hms_edge_cases(self):
        """Test HMS formatting with edge cases"""
        self.assertEqual(format_hms(None), "")
        self.assertEqual(format_hms("invalid"), "")
    
    def test_build_llm_summary_context(self):
        """Test LLM summary context building"""
        transcript_entries = [
            {"start": 0, "text": "Hello world"},
            {"start": 5, "text": "This is a test"}
        ]
        
        context = build_llm_summary_context(
            source_url="https://youtube.com/watch?v=test",
            duration_sec=300,
            upload_date="20240815",
            transcript_entries=transcript_entries
        )
        
        self.assertIn("[SOURCE]", context)
        self.assertIn("https://youtube.com/watch?v=test", context)
        self.assertIn("[DURATION]", context)
        self.assertIn("00:05:00", context)
        self.assertIn("[UPLOAD_DATE]", context)
        self.assertIn("20240815", context)
        self.assertIn("[TRANSCRIPT]", context)
        self.assertIn("[00:00:00] Hello world", context)
        self.assertIn("[00:00:05] This is a test", context)
    
    def test_build_llm_summary_context_plain_transcript(self):
        """Test LLM summary context with plain transcript"""
        context = build_llm_summary_context(
            plain_transcript="This is a plain transcript text"
        )
        
        self.assertIn("[TRANSCRIPT]", context)
        self.assertIn("This is a plain transcript text", context)
    
    def test_create_qa_context(self):
        """Test Q&A context creation"""
        transcript = "This is the video transcript"
        chat_history = [
            {"question": "Previous question", "answer": "Previous answer"}
        ]
        
        context = create_qa_context(transcript, chat_history)
        
        self.assertIn("[자막 내용]", context)
        self.assertIn("This is the video transcript", context)
        self.assertIn("[이전 대화]", context)
        self.assertIn("Q: Previous question", context)
        self.assertIn("A: Previous answer", context)
    
    def test_create_qa_context_no_history(self):
        """Test Q&A context creation without history"""
        transcript = "This is the video transcript"
        
        context = create_qa_context(transcript)
        
        self.assertIn("[자막 내용]", context)
        self.assertIn("This is the video transcript", context)
        self.assertNotIn("[이전 대화]", context)


class TestConfigManagement(unittest.TestCase):
    
    @patch('cli.core.os.path.exists')
    @patch('cli.core.open', new_callable=mock_open)
    def test_get_config_with_file(self, mock_file, mock_exists):
        """Test config loading from file"""
        mock_exists.return_value = True
        mock_config = {"providers": ["openai", "gemini"]}
        mock_file.return_value.read.return_value = json.dumps(mock_config)
        
        with patch('cli.core.json.load', return_value=mock_config):
            config = get_config()
            self.assertEqual(config["providers"], ["openai", "gemini"])
    
    @patch.dict('cli.core.os.environ', {'YYT_PROVIDERS': 'openai,gemini'})
    @patch('cli.core.os.path.exists')
    def test_get_config_from_env(self, mock_exists):
        """Test config loading from environment variables"""
        mock_exists.return_value = False
        
        config = get_config()
        
        self.assertEqual(config["providers"], ["openai", "gemini"])
    
    @patch('cli.core.os.path.exists')
    def test_get_config_defaults(self, mock_exists):
        """Test config loading with defaults"""
        mock_exists.return_value = False
        
        with patch.dict('cli.core.os.environ', {}, clear=True):
            config = get_config()
            self.assertEqual(config["providers"], ["openai", "gemini", "ollama"])


if __name__ == '__main__':
    unittest.main()