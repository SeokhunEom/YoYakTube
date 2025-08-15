#!/usr/bin/env python3
"""Tests for yyt_ai.py with mocked API calls"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import json

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.yyt_ai import (
    get_available_models,
    list_models,
    test_model,
    interactive_chat,
    benchmark_models
)


class TestYytAI(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_ollama_response = {
            "models": [
                {"name": "llama2:latest"},
                {"name": "codellama:7b"},
                {"name": "mistral:latest"}
            ]
        }
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_openai_key',
        'GEMINI_API_KEY': 'test_gemini_key',
        'OLLAMA_HOST': 'http://localhost:11434'
    })
    @patch('requests.get')
    def test_get_available_models_all_providers(self, mock_requests):
        """Test getting available models from all providers"""
        # Mock Ollama API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.mock_ollama_response
        mock_requests.return_value = mock_response
        
        models = get_available_models()
        
        # Check OpenAI models
        self.assertIn('gpt-5-mini', models['openai'])
        self.assertIn('gpt-5', models['openai'])
        
        # Check Gemini models
        self.assertIn('gemini-2.5-pro', models['gemini'])
        self.assertIn('gemini-2.5-flash', models['gemini'])
        
        # Check Ollama models
        self.assertIn('llama2:latest', models['ollama'])
        self.assertIn('codellama:7b', models['ollama'])
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('requests.get')
    def test_get_available_models_no_api_keys(self, mock_requests):
        """Test getting available models without API keys"""
        mock_requests.side_effect = Exception("Connection error")
        
        models = get_available_models()
        
        # Should return empty lists when no API keys
        self.assertEqual(models['openai'], [])
        self.assertEqual(models['gemini'], [])
        self.assertEqual(models['ollama'], [])
    
    @patch('requests.get')
    def test_get_available_models_ollama_error(self, mock_requests):
        """Test getting available models when Ollama is unavailable"""
        mock_requests.side_effect = Exception("Connection refused")
        
        models = get_available_models()
        
        # Should handle Ollama error gracefully
        self.assertEqual(models['ollama'], [])
    
    @patch('builtins.print')
    @patch('cli.yyt_ai.get_available_models')
    def test_list_models_all_providers(self, mock_get_models, mock_print):
        """Test listing models from all providers"""
        mock_get_models.return_value = {
            'openai': ['gpt-5-mini', 'gpt-5'],
            'gemini': ['gemini-2.5-flash'],
            'ollama': ['llama2:latest']
        }
        
        list_models()
        
        # Check that all providers were printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        
        self.assertIn("OPENAI", output)
        self.assertIn("GEMINI", output)
        self.assertIn("OLLAMA", output)
        self.assertIn("gpt-5-mini", output)
        self.assertIn("gemini-2.5-flash", output)
        self.assertIn("llama2:latest", output)
    
    @patch('builtins.print')
    @patch('cli.yyt_ai.get_available_models')
    def test_list_models_specific_provider(self, mock_get_models, mock_print):
        """Test listing models from specific provider"""
        mock_get_models.return_value = {
            'openai': ['gpt-5-mini', 'gpt-5'],
            'gemini': ['gemini-2.5-flash'],
            'ollama': []
        }
        
        list_models(provider='openai')
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        
        self.assertIn("OPENAI", output)
        self.assertIn("gpt-5-mini", output)
        self.assertNotIn("GEMINI", output)
    
    @patch('builtins.print')
    @patch('cli.yyt_ai.get_available_models')
    def test_list_models_invalid_provider(self, mock_get_models, mock_print):
        """Test listing models with invalid provider"""
        mock_get_models.return_value = {
            'openai': ['gpt-5-mini'],
            'gemini': ['gemini-2.5-flash'],
            'ollama': []
        }
        
        list_models(provider='invalid')
        
        mock_print.assert_called_with("오류: 알 수 없는 제공자 'invalid'", file=sys.stderr)
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('cli.yyt_ai.get_or_create_llm')
    @patch('builtins.print')
    def test_test_model_success(self, mock_print, mock_get_llm):
        """Test successful model testing"""
        # Mock LLM client
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test successful"
        mock_response.usage = {"total_tokens": 25}
        mock_llm.chat.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        with patch('time.time', side_effect=[0, 1.5]):  # Mock response time
            result = test_model('openai', 'gpt-5-mini')
        
        self.assertTrue(result)
        
        # Check that success message was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("테스트 성공", output)
        self.assertIn("1.50초", output)
        self.assertIn("토큰 사용량: 25", output)
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('builtins.print')
    def test_test_model_no_api_key(self, mock_print):
        """Test model testing without API key"""
        result = test_model('openai', 'gpt-5-mini')
        
        self.assertFalse(result)
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("OPENAI_API_KEY 환경변수가 설정되지 않았습니다", output)
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('cli.yyt_ai.get_or_create_llm')
    @patch('builtins.print')
    def test_test_model_api_error(self, mock_print, mock_get_llm):
        """Test model testing with API error"""
        mock_get_llm.side_effect = Exception("API 오류")
        
        result = test_model('openai', 'gpt-5-mini')
        
        self.assertFalse(result)
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("테스트 실패", output)
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('cli.yyt_ai.get_or_create_llm')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_chat_single_exchange(self, mock_print, mock_input, mock_get_llm):
        """Test interactive chat with single message exchange"""
        # Mock user input
        mock_input.side_effect = ["안녕하세요", "quit"]
        
        # Mock LLM response
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "안녕하세요! 무엇을 도와드릴까요?"
        mock_llm.chat.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        interactive_chat('openai', 'gpt-5-mini')
        
        # Check that LLM was called
        mock_llm.chat.assert_called_once()
        
        # Check that response was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("안녕하세요! 무엇을 도와드릴까요?", output)
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('cli.yyt_ai.get_or_create_llm')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_chat_error_handling(self, mock_print, mock_input, mock_get_llm):
        """Test interactive chat error handling"""
        mock_input.side_effect = ["테스트 메시지", "exit"]
        
        # Mock LLM error
        mock_llm = MagicMock()
        mock_llm.chat.side_effect = Exception("API 한도 초과")
        mock_get_llm.return_value = mock_llm
        
        interactive_chat('openai', 'gpt-5-mini')
        
        # Check that error was handled
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("오류 발생", output)
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_openai_key',
        'GEMINI_API_KEY': 'test_gemini_key'
    })
    @patch('cli.yyt_ai.get_or_create_llm')
    @patch('builtins.print')
    def test_benchmark_models_success(self, mock_print, mock_get_llm):
        """Test successful model benchmarking"""
        # Mock LLM responses
        def mock_llm_factory(provider, model, *args):
            mock_llm = MagicMock()
            mock_response = MagicMock()
            mock_response.content = f"{provider} {model} response"
            mock_response.usage = {"total_tokens": 50}
            mock_llm.chat.return_value = mock_response
            return mock_llm
        
        mock_get_llm.side_effect = mock_llm_factory
        
        with patch('time.time', side_effect=[0, 1.0, 2.0, 3.5]):  # Mock timing
            results = benchmark_models([
                'openai:gpt-5-mini',
                'gemini:gemini-2.5-flash'
            ])
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['provider'], 'openai')
        self.assertEqual(results[0]['model'], 'gpt-5-mini')
        self.assertAlmostEqual(results[0]['response_time'], 1.0)
        
        # Check benchmark summary
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("벤치마크 결과 요약", output)
    
    @patch('cli.yyt_ai.get_or_create_llm')
    @patch('builtins.print')
    def test_benchmark_models_with_error(self, mock_print, mock_get_llm):
        """Test model benchmarking with errors"""
        # First model succeeds, second fails
        def mock_llm_side_effect(provider, model, *args):
            if provider == 'openai':
                mock_llm = MagicMock()
                mock_response = MagicMock()
                mock_response.content = "Success response"
                mock_llm.chat.return_value = mock_response
                return mock_llm
            else:
                raise Exception("API 오류")
        
        mock_get_llm.side_effect = mock_llm_side_effect
        
        with patch('time.time', side_effect=[0, 1.0]):
            results = benchmark_models([
                'openai:gpt-5-mini',
                'gemini:gemini-2.5-flash'
            ])
        
        # Should only have 1 successful result
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['provider'], 'openai')
        
        # Check that error was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("오류", output)


if __name__ == '__main__':
    unittest.main()