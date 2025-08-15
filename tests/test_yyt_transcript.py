#!/usr/bin/env python3
"""Tests for yyt_transcript.py"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.yyt_transcript import (
    format_timestamp,
    format_as_srt,
    format_as_vtt,
    format_as_text,
    extract_transcript
)


class TestYytTranscript(unittest.TestCase):
    
    def test_format_timestamp(self):
        """Test timestamp formatting for SRT format"""
        # Test normal timestamp
        self.assertEqual(format_timestamp(65.5), "00:01:05,500")
        
        # Test zero timestamp
        self.assertEqual(format_timestamp(0), "00:00:00,000")
        
        # Test timestamp with hours
        self.assertEqual(format_timestamp(3661.123), "01:01:01,123")
    
    def test_format_as_srt(self):
        """Test SRT format conversion"""
        entries = [
            {"start": 0, "duration": 2.5, "text": "첫 번째 자막"},
            {"start": 3, "duration": 3, "text": "두 번째 자막"}
        ]
        
        result = format_as_srt(entries)
        
        self.assertIn("1", result)
        self.assertIn("00:00:00,000 --> 00:00:02,500", result)
        self.assertIn("첫 번째 자막", result)
        self.assertIn("2", result)
        self.assertIn("00:00:03,000 --> 00:00:06,000", result)
        self.assertIn("두 번째 자막", result)
    
    def test_format_as_vtt(self):
        """Test VTT format conversion"""
        entries = [
            {"start": 0, "duration": 2.5, "text": "첫 번째 자막"}
        ]
        
        result = format_as_vtt(entries)
        
        self.assertIn("WEBVTT", result)
        self.assertIn("00:00:00.000 --> 00:00:02.500", result)
        self.assertIn("첫 번째 자막", result)
    
    def test_format_as_text_without_timestamps(self):
        """Test text format without timestamps"""
        entries = [
            {"start": 0, "text": "첫 번째 자막"},
            {"start": 3, "text": "두 번째 자막"}
        ]
        
        result = format_as_text(entries, include_timestamps=False)
        
        self.assertEqual(result, "첫 번째 자막\n두 번째 자막")
    
    def test_format_as_text_with_timestamps(self):
        """Test text format with timestamps"""
        entries = [
            {"start": 65, "text": "첫 번째 자막"},
            {"start": 125, "text": "두 번째 자막"}
        ]
        
        result = format_as_text(entries, include_timestamps=True)
        
        self.assertIn("[01:05] 첫 번째 자막", result)
        self.assertIn("[02:05] 두 번째 자막", result)
    
    @patch('cli.yyt_transcript.collect_transcript_entries')
    def test_extract_transcript_srt_format(self, mock_collect_entries):
        """Test transcript extraction in SRT format"""
        mock_entries = [
            {"start": 0, "duration": 2, "text": "테스트 자막"}
        ]
        mock_collect_entries.return_value = (mock_entries, "ko")
        
        content, lang, error = extract_transcript("test_id", format_type="srt")
        
        self.assertIsNone(error)
        self.assertEqual(lang, "ko")
        self.assertIn("1", content)
        self.assertIn("테스트 자막", content)
    
    @patch('cli.yyt_transcript.collect_transcript')
    def test_extract_transcript_text_format(self, mock_collect):
        """Test transcript extraction in text format"""
        mock_collect.return_value = ("테스트 자막 내용", "ko")
        
        content, lang, error = extract_transcript("test_id", format_type="text")
        
        self.assertIsNone(error)
        self.assertEqual(lang, "ko")
        self.assertEqual(content, "테스트 자막 내용")
    
    @patch('cli.yyt_transcript.collect_transcript')
    def test_extract_transcript_no_result(self, mock_collect):
        """Test transcript extraction when no transcript found"""
        mock_collect.return_value = None
        
        content, lang, error = extract_transcript("test_id")
        
        self.assertEqual(content, "")
        self.assertEqual(lang, "")
        self.assertEqual(error, "자막을 찾을 수 없습니다.")
    
    @patch('cli.yyt_transcript.collect_transcript')
    def test_extract_transcript_exception(self, mock_collect):
        """Test transcript extraction with exception"""
        mock_collect.side_effect = Exception("테스트 오류")
        
        content, lang, error = extract_transcript("test_id")
        
        self.assertEqual(content, "")
        self.assertEqual(lang, "")
        self.assertEqual(error, "테스트 오류")


if __name__ == '__main__':
    unittest.main()