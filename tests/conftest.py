#!/usr/bin/env python3
"""Test configuration and fixtures for YoYakTube CLI tests"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and utilities"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear environment variables that might affect tests
        self.env_patches = []
        
        # Common test data
        self.sample_video_id = "dQw4w9WgXcQ"
        self.sample_video_url = f"https://www.youtube.com/watch?v={self.sample_video_id}"
        self.sample_channel_url = "https://www.youtube.com/@testchannel"
        
        # Sample transcript data
        self.sample_transcript_text = """
        안녕하세요, 이것은 테스트 자막입니다.
        YoYakTube CLI 도구를 테스트하고 있습니다.
        모든 기능이 정상적으로 작동하는지 확인하겠습니다.
        """
        
        self.sample_transcript_entries = [
            {"start": 0.0, "duration": 3.0, "text": "안녕하세요, 이것은 테스트 자막입니다."},
            {"start": 3.0, "duration": 4.0, "text": "YoYakTube CLI 도구를 테스트하고 있습니다."},
            {"start": 7.0, "duration": 5.0, "text": "모든 기능이 정상적으로 작동하는지 확인하겠습니다."}
        ]
        
        # Sample metadata
        self.sample_metadata = {
            "id": self.sample_video_id,
            "title": "테스트 영상 제목",
            "uploader": "테스트 채널",
            "uploader_id": "@testchannel",
            "duration": 300,
            "view_count": 1000000,
            "like_count": 50000,
            "upload_date": "20240815",
            "description": "이것은 테스트용 영상 설명입니다.",
            "webpage_url": self.sample_video_url,
            "language": "ko",
            "category": "Education"
        }
        
        # Sample config
        self.sample_config = {
            "providers": ["openai", "gemini", "ollama"],
            "models": {
                "openai": "gpt-5-mini",
                "gemini": "gemini-2.5-flash",
                "ollama": "llama2"
            },
            "api_settings": {
                "timeout": 60,
                "retry_attempts": 3,
                "temperature": 0.2
            }
        }
    
    def tearDown(self):
        """Clean up test environment"""
        # Stop all environment patches
        for patcher in self.env_patches:
            patcher.stop()
        self.env_patches.clear()
    
    def mock_env_var(self, var_name, value):
        """Mock an environment variable for the test"""
        patcher = patch.dict('os.environ', {var_name: value})
        patcher.start()
        self.env_patches.append(patcher)
        return patcher
    
    def mock_llm_response(self, content="테스트 응답", usage=None):
        """Create a mock LLM response"""
        from unittest.mock import MagicMock
        
        response = MagicMock()
        response.content = content
        if usage:
            response.usage = usage
        return response
    
    def mock_llm_client(self, response_content="테스트 응답"):
        """Create a mock LLM client"""
        from unittest.mock import MagicMock
        
        client = MagicMock()
        response = self.mock_llm_response(response_content)
        client.chat.return_value = response
        return client
    
    def assertInOutput(self, text, mock_print_calls):
        """Assert that text appears in print mock calls"""
        output = ''.join(str(call) for call in mock_print_calls)
        self.assertIn(text, output)
    
    def assertNotInOutput(self, text, mock_print_calls):
        """Assert that text does not appear in print mock calls"""
        output = ''.join(str(call) for call in mock_print_calls)
        self.assertNotIn(text, output)


# Test utilities
def create_temp_config_file(config_data):
    """Create a temporary config file for testing"""
    import tempfile
    import json
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(config_data, temp_file, ensure_ascii=False, indent=2)
    temp_file.close()
    return temp_file.name


def cleanup_temp_file(file_path):
    """Clean up temporary file"""
    try:
        os.unlink(file_path)
    except (OSError, FileNotFoundError):
        pass


# Mock data constants
MOCK_OPENAI_MODELS = [
    'gpt-5-mini', 'gpt-5', 'gpt-5-nano',
    'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'
]

MOCK_GEMINI_MODELS = [
    'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite',
    'gemini-1.5-pro', 'gemini-1.5-flash'
]

MOCK_OLLAMA_MODELS = [
    'llama2:latest', 'codellama:7b', 'mistral:latest'
]