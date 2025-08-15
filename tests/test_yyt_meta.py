#!/usr/bin/env python3
"""Tests for yyt_meta.py"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.yyt_meta import (
    format_metadata_table,
    format_metadata_json,
    get_video_metadata,
    list_available_fields
)


class TestYytMeta(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_metadata = {
            "id": "dQw4w9WgXcQ",
            "title": "테스트 영상",
            "uploader": "테스트 채널",
            "uploader_id": "@testchannel",
            "duration": 212,
            "view_count": 1000000,
            "like_count": 50000,
            "upload_date": "20240815",
            "description": "이것은 테스트 영상입니다. " * 20,  # Long description
            "tags": ["test", "video", "sample"] + [f"tag{i}" for i in range(20)],  # Many tags
            "category": "Entertainment",
            "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }
    
    @patch('builtins.print')
    def test_format_metadata_table(self, mock_print):
        """Test metadata table formatting"""
        format_metadata_table(self.sample_metadata)
        
        # Check that print was called multiple times
        self.assertTrue(mock_print.called)
        
        # Check some specific formatting
        print_calls = [str(call) for call in mock_print.call_args_list]
        table_content = ''.join(print_calls)
        
        self.assertIn("테스트 영상", table_content)
        self.assertIn("테스트 채널", table_content)
        self.assertIn("1,000,000", table_content)  # Formatted view count
    
    @patch('builtins.print')
    def test_format_metadata_table_empty(self, mock_print):
        """Test metadata table formatting with empty data"""
        format_metadata_table({})
        
        mock_print.assert_called_with("메타데이터가 없습니다.")
    
    def test_format_metadata_json_all_fields(self):
        """Test JSON formatting with all fields"""
        result = format_metadata_json(self.sample_metadata)
        
        parsed = json.loads(result)
        self.assertEqual(parsed["title"], "테스트 영상")
        self.assertEqual(parsed["id"], "dQw4w9WgXcQ")
    
    def test_format_metadata_json_selected_fields(self):
        """Test JSON formatting with selected fields"""
        fields = ["title", "uploader", "duration"]
        result = format_metadata_json(self.sample_metadata, fields)
        
        parsed = json.loads(result)
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed["title"], "테스트 영상")
        self.assertEqual(parsed["uploader"], "테스트 채널")
        self.assertEqual(parsed["duration"], 212)
        self.assertNotIn("id", parsed)
    
    def test_format_metadata_json_nonexistent_fields(self):
        """Test JSON formatting with non-existent fields"""
        fields = ["nonexistent", "title"]
        result = format_metadata_json(self.sample_metadata, fields)
        
        parsed = json.loads(result)
        self.assertEqual(len(parsed), 1)  # Only title should be included
        self.assertEqual(parsed["title"], "테스트 영상")
    
    @patch('cli.yyt_meta.fetch_video_metadata')
    @patch('cli.yyt_meta.extract_video_id')
    def test_get_video_metadata_success(self, mock_extract_id, mock_fetch):
        """Test successful metadata retrieval"""
        mock_extract_id.return_value = "dQw4w9WgXcQ"
        mock_fetch.return_value = self.sample_metadata
        
        result = get_video_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        self.assertEqual(result, self.sample_metadata)
        mock_extract_id.assert_called_once()
        mock_fetch.assert_called_once_with("dQw4w9WgXcQ")
    
    @patch('cli.yyt_meta.fetch_video_metadata')
    def test_get_video_metadata_direct_id(self, mock_fetch):
        """Test metadata retrieval with direct video ID"""
        mock_fetch.return_value = self.sample_metadata
        
        result = get_video_metadata("dQw4w9WgXcQ")
        
        self.assertEqual(result, self.sample_metadata)
        mock_fetch.assert_called_once_with("dQw4w9WgXcQ")
    
    @patch('cli.yyt_meta.extract_video_id')
    def test_get_video_metadata_invalid_url(self, mock_extract_id):
        """Test metadata retrieval with invalid URL"""
        mock_extract_id.return_value = None
        
        with self.assertRaises(ValueError) as context:
            get_video_metadata("invalid_url")
        
        self.assertIn("올바른 YouTube URL", str(context.exception))
    
    @patch('cli.yyt_meta.fetch_video_metadata')
    @patch('cli.yyt_meta.extract_video_id')
    def test_get_video_metadata_fetch_error(self, mock_extract_id, mock_fetch):
        """Test metadata retrieval with fetch error"""
        mock_extract_id.return_value = "dQw4w9WgXcQ"
        mock_fetch.side_effect = Exception("API 오류")
        
        with self.assertRaises(ValueError) as context:
            get_video_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        self.assertIn("메타데이터를 가져올 수 없습니다", str(context.exception))
    
    @patch('builtins.print')
    def test_list_available_fields(self, mock_print):
        """Test listing available fields"""
        list_available_fields()
        
        self.assertTrue(mock_print.called)
        
        # Check that common fields are mentioned
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        
        self.assertIn("id", output)
        self.assertIn("title", output)
        self.assertIn("uploader", output)
        self.assertIn("duration", output)


if __name__ == '__main__':
    unittest.main()