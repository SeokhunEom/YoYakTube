#!/usr/bin/env python3
"""Tests for yyt_config.py"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from pathlib import Path
import json
import tempfile
import os

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.yyt_config import (
    get_config_file_path,
    load_config_file,
    save_config_file,
    get_default_config,
    show_config,
    init_config,
    set_config_value,
    get_config_value,
    validate_config
)


class TestYytConfig(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_config = {
            "providers": ["openai", "gemini"],
            "models": {
                "openai": "gpt-5-mini",
                "gemini": "gemini-2.5-flash"
            },
            "api_settings": {
                "timeout": 60,
                "retry_attempts": 3,
                "temperature": 0.2
            }
        }
    
    @patch.dict('os.environ', {'YYT_CONFIG': '/custom/path/config.json'})
    def test_get_config_file_path_env_var(self):
        """Test getting config file path from environment variable"""
        path = get_config_file_path()
        self.assertEqual(path, Path('/custom/path/config.json'))
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('pathlib.Path.cwd')
    def test_get_config_file_path_default(self, mock_cwd):
        """Test getting default config file path"""
        mock_cwd.return_value = Path('/current/dir')
        
        path = get_config_file_path()
        
        self.assertEqual(path, Path('/current/dir/yoyaktube.config.json'))
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"providers": ["openai"]}')
    @patch('cli.yyt_config.get_config_file_path')
    def test_load_config_file_success(self, mock_get_path, mock_file):
        """Test successful config file loading"""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path
        
        config = load_config_file()
        
        self.assertEqual(config, {"providers": ["openai"]})
    
    @patch('cli.yyt_config.get_config_file_path')
    def test_load_config_file_not_exists(self, mock_get_path):
        """Test loading config file that doesn't exist"""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_path.return_value = mock_path
        
        config = load_config_file()
        
        self.assertEqual(config, {})
    
    @patch('builtins.open', side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
    @patch('cli.yyt_config.get_config_file_path')
    def test_load_config_file_invalid_json(self, mock_get_path, mock_file):
        """Test loading invalid JSON config file"""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path
        
        with self.assertRaises(ValueError) as context:
            load_config_file()
        
        self.assertIn("설정 파일을 읽을 수 없습니다", str(context.exception))
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('cli.yyt_config.get_config_file_path')
    @patch('builtins.print')
    def test_save_config_file_success(self, mock_print, mock_get_path, mock_file):
        """Test successful config file saving"""
        mock_path = Path('/test/config.json')
        mock_get_path.return_value = mock_path
        
        save_config_file(self.sample_config)
        
        mock_file.assert_called_once_with(mock_path, 'w', encoding='utf-8')
        # Check that JSON was written
        handle = mock_file()
        written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn('"providers"', written_data)
    
    def test_get_default_config(self):
        """Test getting default configuration"""
        config = get_default_config()
        
        self.assertIn('providers', config)
        self.assertIn('models', config)
        self.assertIn('api_settings', config)
        self.assertIn('transcript_settings', config)
        self.assertIn('output_settings', config)
        
        # Check specific defaults
        self.assertEqual(config['providers'], ["openai", "gemini", "ollama"])
        self.assertEqual(config['models']['openai'], "gpt-5-mini")
        self.assertEqual(config['api_settings']['timeout'], 60)
    
    @patch('builtins.print')
    @patch('cli.yyt_config.get_available_providers')
    @patch('cli.yyt_config.get_config')
    @patch('cli.yyt_config.get_config_file_path')
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_key',
        'GEMINI_API_KEY': '',
        'YYT_CONFIG': '/test/config.json'
    })
    def test_show_config(self, mock_get_path, mock_get_config, mock_get_providers, mock_print):
        """Test showing current configuration"""
        from unittest.mock import MagicMock
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.__str__ = lambda: '/test/config.json'
        mock_get_path.return_value = mock_path
        
        mock_get_config.return_value = self.sample_config
        mock_get_providers.return_value = ['openai', 'gemini']
        
        show_config()
        
        # Check that configuration info was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        
        self.assertIn("YoYakTube 현재 설정", output)
        self.assertIn("/test/config.json", output)
        self.assertIn("파일 존재: 예", output)
        self.assertIn("OPENAI_API_KEY: *******", output)  # Masked API key
        self.assertIn("GEMINI_API_KEY: (없음)", output)   # Empty API key
    
    @patch('builtins.input', return_value='y')
    @patch('cli.yyt_config.save_config_file')
    @patch('cli.yyt_config.get_config_file_path')
    @patch('builtins.print')
    def test_init_config_overwrite_existing(self, mock_print, mock_get_path, mock_save, mock_input):
        """Test initializing config with existing file (overwrite)"""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path
        
        init_config()
        
        # Should ask for confirmation and save
        mock_input.assert_called_once()
        mock_save.assert_called_once()
    
    @patch('builtins.input', return_value='n')
    @patch('cli.yyt_config.save_config_file')
    @patch('cli.yyt_config.get_config_file_path')
    @patch('builtins.print')
    def test_init_config_cancel_overwrite(self, mock_print, mock_get_path, mock_save, mock_input):
        """Test initializing config with existing file (cancel)"""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path
        
        init_config()
        
        # Should not save when user cancels
        mock_input.assert_called_once()
        mock_save.assert_not_called()
    
    @patch('cli.yyt_config.save_config_file')
    @patch('cli.yyt_config.load_config_file')
    @patch('builtins.print')
    def test_set_config_value_simple(self, mock_print, mock_load, mock_save):
        """Test setting simple config value"""
        mock_load.return_value = {"providers": ["openai"]}
        
        set_config_value("providers", "openai,gemini,ollama")
        
        # Should have called save with updated config
        mock_save.assert_called_once()
        saved_config = mock_save.call_args[0][0]
        self.assertEqual(saved_config["providers"], ["openai", "gemini", "ollama"])
    
    @patch('cli.yyt_config.save_config_file')
    @patch('cli.yyt_config.load_config_file')
    @patch('builtins.print')
    def test_set_config_value_nested(self, mock_print, mock_load, mock_save):
        """Test setting nested config value"""
        mock_load.return_value = {"api_settings": {"timeout": 30}}
        
        set_config_value("api_settings.timeout", "60")
        
        mock_save.assert_called_once()
        saved_config = mock_save.call_args[0][0]
        self.assertEqual(saved_config["api_settings"]["timeout"], 60)  # Should be converted to int
    
    @patch('cli.yyt_config.save_config_file')
    @patch('cli.yyt_config.load_config_file')
    @patch('builtins.print')
    def test_set_config_value_create_nested(self, mock_print, mock_load, mock_save):
        """Test setting nested config value that doesn't exist"""
        mock_load.return_value = {}
        
        set_config_value("new_section.new_key", "test_value")
        
        mock_save.assert_called_once()
        saved_config = mock_save.call_args[0][0]
        self.assertEqual(saved_config["new_section"]["new_key"], "test_value")
    
    @patch('builtins.print')
    @patch('cli.yyt_config.get_config')
    def test_get_config_value_success(self, mock_get_config, mock_print):
        """Test getting config value successfully"""
        mock_get_config.return_value = self.sample_config
        
        get_config_value("providers")
        
        mock_print.assert_called_with("openai,gemini")
    
    @patch('builtins.print')
    @patch('cli.yyt_config.get_config')
    def test_get_config_value_nested(self, mock_get_config, mock_print):
        """Test getting nested config value"""
        mock_get_config.return_value = self.sample_config
        
        get_config_value("api_settings.timeout")
        
        mock_print.assert_called_with(60)
    
    @patch('builtins.print')
    @patch('cli.yyt_config.get_config')
    def test_get_config_value_not_found(self, mock_get_config, mock_print):
        """Test getting non-existent config value"""
        mock_get_config.return_value = self.sample_config
        
        get_config_value("nonexistent.key")
        
        mock_print.assert_called_with("설정 키 'nonexistent.key'를 찾을 수 없습니다.")
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_key',
        'GEMINI_API_KEY': 'test_key'
    })
    @patch('builtins.print')
    @patch('cli.yyt_config.get_config')
    def test_validate_config_success(self, mock_get_config, mock_print):
        """Test successful config validation"""
        mock_get_config.return_value = {
            "providers": ["openai", "gemini"],
            "models": {
                "openai": "gpt-5-mini",
                "gemini": "gemini-2.5-flash"
            }
        }
        
        result = validate_config()
        
        self.assertTrue(result)
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("설정이 올바릅니다", output)
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('builtins.print')
    @patch('cli.yyt_config.get_config')
    def test_validate_config_missing_api_keys(self, mock_get_config, mock_print):
        """Test config validation with missing API keys"""
        mock_get_config.return_value = {
            "providers": ["openai", "gemini"],
            "models": {
                "openai": "gpt-5-mini",
                "gemini": "gemini-2.5-flash"
            }
        }
        
        result = validate_config()
        
        self.assertFalse(result)
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("OPENAI_API_KEY 환경변수가 설정되지 않았습니다", output)
        self.assertIn("GEMINI_API_KEY 환경변수가 설정되지 않았습니다", output)
    
    @patch('builtins.print')
    @patch('cli.yyt_config.get_config')
    def test_validate_config_invalid_provider(self, mock_get_config, mock_print):
        """Test config validation with invalid provider"""
        mock_get_config.return_value = {
            "providers": ["invalid_provider"],
            "models": {}
        }
        
        result = validate_config()
        
        self.assertFalse(result)
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("알 수 없는 제공자: invalid_provider", output)
    
    @patch('builtins.print')
    @patch('cli.yyt_config.get_config')
    def test_validate_config_missing_models(self, mock_get_config, mock_print):
        """Test config validation with missing model configuration"""
        mock_get_config.return_value = {
            "providers": ["openai", "gemini"],
            "models": {
                "openai": "gpt-5-mini"
                # Missing gemini model
            }
        }
        
        result = validate_config()
        
        self.assertFalse(result)
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("gemini 제공자의 모델이 설정되지 않았습니다", output)


if __name__ == '__main__':
    unittest.main()