#!/usr/bin/env python3
"""Tests for yyt_summarize.py with mocked LLM calls"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.yyt_summarize import (
    get_transcript_from_video,
    read_transcript_from_file,
    read_transcript_from_stdin,
    create_llm_client,
    summarize_transcript
)


class TestYytSummarize(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_metadata = {
            "id": "dQw4w9WgXcQ",
            "title": "테스트 영상",
            "uploader": "테스트 채널",
            "duration": 212,
            "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "upload_date": "20240815"
        }
        
        self.sample_entries = [
            {"start": 0, "text": "안녕하세요, 테스트입니다."},
            {"start": 5, "text": "이것은 샘플 자막입니다."},
            {"start": 10, "text": "요약 테스트를 위한 내용입니다."}
        ]
        
        self.sample_transcript = "안녕하세요, 테스트입니다. 이것은 샘플 자막입니다. 요약 테스트를 위한 내용입니다."
    
    @patch('cli.yyt_summarize.fetch_video_metadata')
    @patch('cli.yyt_summarize.collect_transcript_entries')
    @patch('cli.yyt_summarize.collect_transcript')
    @patch('cli.yyt_summarize.extract_video_id')
    def test_get_transcript_from_video_success(self, mock_extract_id, mock_collect, mock_collect_entries, mock_fetch):
        """Test successful transcript extraction from video"""
        mock_extract_id.return_value = "dQw4w9WgXcQ"
        mock_collect.return_value = (self.sample_transcript, "ko")
        mock_collect_entries.return_value = (self.sample_entries, "ko")
        mock_fetch.return_value = self.sample_metadata
        
        transcript, metadata, entries = get_transcript_from_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        self.assertEqual(transcript, self.sample_transcript)
        self.assertEqual(metadata, self.sample_metadata)
        self.assertEqual(entries, self.sample_entries)
    
    @patch('cli.yyt_summarize.collect_transcript')
    @patch('cli.yyt_summarize.extract_video_id')
    def test_get_transcript_from_video_no_transcript(self, mock_extract_id, mock_collect):
        """Test transcript extraction when no transcript found"""
        mock_extract_id.return_value = "dQw4w9WgXcQ"
        mock_collect.return_value = None
        
        with self.assertRaises(ValueError) as context:
            get_transcript_from_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        self.assertIn("자막을 찾을 수 없습니다", str(context.exception))
    
    @patch('cli.yyt_summarize.extract_video_id')
    def test_get_transcript_from_video_invalid_id(self, mock_extract_id):
        """Test transcript extraction with invalid video ID"""
        mock_extract_id.return_value = None
        
        with self.assertRaises(ValueError) as context:
            get_transcript_from_video("invalid_url")
        
        self.assertIn("올바른 YouTube URL", str(context.exception))
    
    def test_get_transcript_from_video_direct_id(self):
        """Test transcript extraction with direct video ID"""
        with patch('cli.yyt_summarize.collect_transcript') as mock_collect, \
             patch('cli.yyt_summarize.collect_transcript_entries') as mock_collect_entries, \
             patch('cli.yyt_summarize.fetch_video_metadata') as mock_fetch:
            
            mock_collect.return_value = (self.sample_transcript, "ko")
            mock_collect_entries.return_value = (self.sample_entries, "ko")
            mock_fetch.return_value = self.sample_metadata
            
            transcript, metadata, entries = get_transcript_from_video("dQw4w9WgXcQ")
            
            self.assertEqual(transcript, self.sample_transcript)
    
    @patch('builtins.open', new_callable=mock_open, read_data="파일에서 읽은 자막 내용")
    def test_read_transcript_from_file_success(self, mock_file):
        """Test successful transcript reading from file"""
        result = read_transcript_from_file("test.txt")
        
        self.assertEqual(result, "파일에서 읽은 자막 내용")
        mock_file.assert_called_once_with("test.txt", 'r', encoding='utf-8')
    
    @patch('builtins.open', side_effect=FileNotFoundError("파일이 없습니다"))
    def test_read_transcript_from_file_error(self, mock_file):
        """Test transcript reading from file with error"""
        with self.assertRaises(ValueError) as context:
            read_transcript_from_file("nonexistent.txt")
        
        self.assertIn("파일을 읽을 수 없습니다", str(context.exception))
    
    @patch('sys.stdin')
    def test_read_transcript_from_stdin_success(self, mock_stdin):
        """Test successful transcript reading from stdin"""
        mock_stdin.read.return_value = "표준 입력에서 읽은 내용\n"
        
        result = read_transcript_from_stdin()
        
        self.assertEqual(result, "표준 입력에서 읽은 내용")
    
    @patch('sys.stdin')
    def test_read_transcript_from_stdin_error(self, mock_stdin):
        """Test transcript reading from stdin with error"""
        mock_stdin.read.side_effect = Exception("입력 오류")
        
        with self.assertRaises(ValueError) as context:
            read_transcript_from_stdin()
        
        self.assertIn("표준 입력을 읽을 수 없습니다", str(context.exception))
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_openai_key',
        'GEMINI_API_KEY': 'test_gemini_key',
        'OLLAMA_HOST': 'http://localhost:11434'
    })
    @patch('cli.yyt_summarize.get_or_create_llm')
    @patch('cli.yyt_summarize.get_config')
    def test_create_llm_client_default_provider(self, mock_get_config, mock_get_llm):
        """Test LLM client creation with default provider"""
        mock_get_config.return_value = {
            'providers': ['openai', 'gemini', 'ollama']
        }
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        
        client = create_llm_client()
        
        mock_get_llm.assert_called_once_with(
            'openai', 'gpt-5-mini',
            'test_openai_key', 'test_gemini_key', 'http://localhost:11434'
        )
        self.assertEqual(client, mock_llm)
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_openai_key',
        'GEMINI_API_KEY': 'test_gemini_key'
    })
    @patch('cli.yyt_summarize.get_or_create_llm')
    @patch('cli.yyt_summarize.get_config')
    def test_create_llm_client_specific_provider(self, mock_get_config, mock_get_llm):
        """Test LLM client creation with specific provider"""
        mock_get_config.return_value = {}
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        
        client = create_llm_client(provider='gemini', model='gemini-2.5-pro')
        
        mock_get_llm.assert_called_once_with(
            'gemini', 'gemini-2.5-pro',
            'test_openai_key', 'test_gemini_key', 'http://localhost:11434'
        )
    
    @patch('cli.yyt_summarize.create_llm_client')
    @patch('cli.yyt_summarize.build_llm_summary_context')
    def test_summarize_transcript_with_metadata(self, mock_build_context, mock_create_client):
        """Test transcript summarization with metadata"""
        # Mock LLM client
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "이것은 AI가 생성한 요약입니다."
        mock_llm.chat.return_value = mock_response
        mock_create_client.return_value = mock_llm
        
        # Mock context building
        mock_build_context.return_value = "enriched context"
        
        result = summarize_transcript(
            self.sample_transcript,
            self.sample_metadata,
            self.sample_entries,
            provider='openai',
            model='gpt-5-mini'
        )
        
        self.assertEqual(result, "이것은 AI가 생성한 요약입니다.")
        mock_build_context.assert_called_once()
        mock_llm.chat.assert_called_once()
    
    @patch('cli.yyt_summarize.create_llm_client')
    def test_summarize_transcript_without_metadata(self, mock_create_client):
        """Test transcript summarization without metadata"""
        # Mock LLM client
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "메타데이터 없이 생성한 요약입니다."
        mock_llm.chat.return_value = mock_response
        mock_create_client.return_value = mock_llm
        
        result = summarize_transcript(self.sample_transcript)
        
        self.assertEqual(result, "메타데이터 없이 생성한 요약입니다.")
        mock_llm.chat.assert_called_once()
        
        # Check that the transcript was used directly (not enriched)
        call_args = mock_llm.chat.call_args[0][0]  # First positional argument (messages)
        user_message = call_args[1].content  # Second message should be user message
        self.assertIn(self.sample_transcript, user_message)
    
    @patch('cli.yyt_summarize.create_llm_client')
    def test_summarize_transcript_with_temperature(self, mock_create_client):
        """Test transcript summarization with custom temperature"""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "커스텀 온도로 생성한 요약입니다."
        mock_llm.chat.return_value = mock_response
        mock_create_client.return_value = mock_llm
        
        result = summarize_transcript(
            self.sample_transcript,
            temperature=0.7
        )
        
        self.assertEqual(result, "커스텀 온도로 생성한 요약입니다.")
        
        # Check that temperature was passed correctly
        call_args = mock_llm.chat.call_args
        self.assertEqual(call_args[1]['temperature'], 0.7)


if __name__ == '__main__':
    unittest.main()