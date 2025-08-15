#!/usr/bin/env python3
"""Tests for yyt_chat.py with mocked LLM calls"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from pathlib import Path
import json

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.yyt_chat import (
    get_transcript_from_video,
    read_transcript_from_file,
    create_llm_client,
    answer_question,
    interactive_chat
)


class TestYytChat(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_metadata = {
            "title": "테스트 영상",
            "uploader": "테스트 채널",
            "duration": 212
        }
        
        self.sample_transcript = "안녕하세요, 테스트입니다. 이것은 샘플 자막입니다. Q&A 테스트를 위한 내용입니다."
        
        self.sample_question = "이 영상의 주요 내용은 무엇인가요?"
        self.sample_answer = "이 영상은 테스트를 위한 샘플 콘텐츠입니다."
    
    @patch('cli.yyt_chat.fetch_video_metadata')
    @patch('cli.yyt_chat.collect_transcript')
    @patch('cli.yyt_chat.extract_video_id')
    def test_get_transcript_from_video_success(self, mock_extract_id, mock_collect, mock_fetch):
        """Test successful transcript extraction from video"""
        mock_extract_id.return_value = "dQw4w9WgXcQ"
        mock_collect.return_value = (self.sample_transcript, "ko")
        mock_fetch.return_value = self.sample_metadata
        
        transcript, metadata = get_transcript_from_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        self.assertEqual(transcript, self.sample_transcript)
        self.assertEqual(metadata, self.sample_metadata)
    
    @patch('cli.yyt_chat.collect_transcript')
    @patch('cli.yyt_chat.extract_video_id')
    def test_get_transcript_from_video_no_transcript(self, mock_extract_id, mock_collect):
        """Test transcript extraction when no transcript found"""
        mock_extract_id.return_value = "dQw4w9WgXcQ"
        mock_collect.return_value = None
        
        with self.assertRaises(ValueError) as context:
            get_transcript_from_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        self.assertIn("자막을 찾을 수 없습니다", str(context.exception))
    
    @patch('builtins.open', new_callable=mock_open, read_data="파일에서 읽은 자막 내용")
    def test_read_transcript_from_file_success(self, mock_file):
        """Test successful transcript reading from file"""
        result = read_transcript_from_file("test.txt")
        
        self.assertEqual(result, "파일에서 읽은 자막 내용")
        mock_file.assert_called_once_with("test.txt", 'r', encoding='utf-8')
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_openai_key',
        'GEMINI_API_KEY': 'test_gemini_key',
        'OLLAMA_HOST': 'http://localhost:11434'
    })
    @patch('cli.yyt_chat.get_or_create_llm')
    @patch('cli.yyt_chat.get_config')
    def test_create_llm_client_success(self, mock_get_config, mock_get_llm):
        """Test LLM client creation"""
        mock_get_config.return_value = {
            'providers': ['openai', 'gemini', 'ollama']
        }
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        
        client = create_llm_client(provider='openai', model='gpt-5-mini')
        
        mock_get_llm.assert_called_once_with(
            'openai', 'gpt-5-mini',
            'test_openai_key', 'test_gemini_key', 'http://localhost:11434'
        )
        self.assertEqual(client, mock_llm)
    
    @patch('cli.yyt_chat.create_llm_client')
    @patch('cli.yyt_chat.create_qa_context')
    def test_answer_question_success(self, mock_create_context, mock_create_client):
        """Test successful question answering"""
        # Mock LLM client
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = self.sample_answer
        mock_llm.chat.return_value = mock_response
        mock_create_client.return_value = mock_llm
        
        # Mock context creation
        mock_create_context.return_value = "context for Q&A"
        
        result = answer_question(
            self.sample_transcript,
            self.sample_question,
            provider='openai',
            model='gpt-5-mini'
        )
        
        self.assertEqual(result, self.sample_answer)
        mock_create_context.assert_called_once_with(self.sample_transcript, None)
        mock_llm.chat.assert_called_once()
    
    @patch('cli.yyt_chat.create_llm_client')
    @patch('cli.yyt_chat.create_qa_context')
    def test_answer_question_with_history(self, mock_create_context, mock_create_client):
        """Test question answering with chat history"""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "히스토리를 고려한 답변"
        mock_llm.chat.return_value = mock_response
        mock_create_client.return_value = mock_llm
        
        mock_create_context.return_value = "context with history"
        
        chat_history = [
            {"question": "이전 질문", "answer": "이전 답변"}
        ]
        
        result = answer_question(
            self.sample_transcript,
            "후속 질문",
            context_history=chat_history
        )
        
        self.assertEqual(result, "히스토리를 고려한 답변")
        mock_create_context.assert_called_once_with(self.sample_transcript, chat_history)
    
    @patch('builtins.input')
    @patch('builtins.print')
    @patch('cli.yyt_chat.answer_question')
    def test_interactive_chat_single_question(self, mock_answer, mock_print, mock_input):
        """Test interactive chat with single question"""
        # Mock user input sequence: question -> quit
        mock_input.side_effect = ["테스트 질문입니다", "quit"]
        mock_answer.return_value = "테스트 답변입니다"
        
        interactive_chat(
            self.sample_transcript,
            self.sample_metadata,
            provider='openai',
            model='gpt-5-mini'
        )
        
        # Check that answer_question was called
        mock_answer.assert_called_once_with(
            self.sample_transcript,
            "테스트 질문입니다",
            'openai',
            'gpt-5-mini',
            []
        )
        
        # Check that answer was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("테스트 답변입니다" in call for call in print_calls))
    
    @patch('builtins.input')
    @patch('builtins.print')
    @patch('builtins.open', new_callable=mock_open)
    def test_interactive_chat_save_history(self, mock_file, mock_print, mock_input):
        """Test interactive chat with save functionality"""
        # Mock user input: save command -> quit
        mock_input.side_effect = ["save chat_history.json", "quit"]
        
        interactive_chat(
            self.sample_transcript,
            self.sample_metadata
        )
        
        # Check that file was opened for writing
        mock_file.assert_called_with("chat_history.json", 'w', encoding='utf-8')
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_chat_empty_input(self, mock_print, mock_input):
        """Test interactive chat with empty input"""
        # Mock user input: empty string -> quit
        mock_input.side_effect = ["", "quit"]
        
        interactive_chat(self.sample_transcript)
        
        # Should handle empty input gracefully and continue
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("채팅을 종료합니다" in call for call in print_calls))
    
    @patch('builtins.input')
    @patch('builtins.print')
    @patch('cli.yyt_chat.answer_question')
    def test_interactive_chat_answer_error(self, mock_answer, mock_print, mock_input):
        """Test interactive chat when answer generation fails"""
        mock_input.side_effect = ["테스트 질문", "quit"]
        mock_answer.side_effect = Exception("API 오류")
        
        interactive_chat(self.sample_transcript)
        
        # Should handle error gracefully
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("답변 생성 실패" in call for call in print_calls))
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_chat_keyboard_interrupt(self, mock_print, mock_input):
        """Test interactive chat with keyboard interrupt"""
        mock_input.side_effect = KeyboardInterrupt()
        
        interactive_chat(self.sample_transcript)
        
        # Should handle KeyboardInterrupt gracefully
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("채팅을 종료합니다" in call for call in print_calls))
    
    @patch('builtins.input')
    @patch('builtins.print')
    @patch('cli.yyt_chat.answer_question')
    def test_interactive_chat_multiple_questions(self, mock_answer, mock_print, mock_input):
        """Test interactive chat with multiple questions"""
        mock_input.side_effect = [
            "첫 번째 질문",
            "두 번째 질문", 
            "exit"
        ]
        mock_answer.side_effect = [
            "첫 번째 답변",
            "두 번째 답변"
        ]
        
        interactive_chat(self.sample_transcript)
        
        # Check that both questions were answered
        self.assertEqual(mock_answer.call_count, 2)
        
        # Check that chat history was passed to second question
        second_call = mock_answer.call_args_list[1]
        chat_history = second_call[1]['context_history']  # keyword argument
        self.assertEqual(len(chat_history), 1)
        self.assertEqual(chat_history[0]['question'], "첫 번째 질문")
        self.assertEqual(chat_history[0]['answer'], "첫 번째 답변")


if __name__ == '__main__':
    unittest.main()