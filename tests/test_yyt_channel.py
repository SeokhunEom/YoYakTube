#!/usr/bin/env python3
"""Tests for yyt_channel.py"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.yyt_channel import (
    parse_date_range,
    get_channel_videos,
    print_videos_table
)


class TestYytChannel(unittest.TestCase):
    
    def test_parse_date_range_today(self):
        """Test parsing 'today' date range"""
        start, end = parse_date_range('today')
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.assertEqual(start, today)
        self.assertEqual(end, today + timedelta(days=1))
    
    def test_parse_date_range_yesterday(self):
        """Test parsing 'yesterday' date range"""
        start, end = parse_date_range('yesterday')
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        self.assertEqual(start, yesterday)
        self.assertEqual(end, today)
    
    def test_parse_date_range_days_ago(self):
        """Test parsing days ago as number"""
        start, end = parse_date_range('7')
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        expected_start = today - timedelta(days=7)
        expected_end = today + timedelta(days=1)
        
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)
    
    def test_parse_date_range_specific_range(self):
        """Test parsing specific date range"""
        start, end = parse_date_range('20240101-20240107')
        
        expected_start = datetime(2024, 1, 1)
        expected_end = datetime(2024, 1, 8)  # +1 day
        
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)
    
    def test_parse_date_range_single_date(self):
        """Test parsing single date"""
        start, end = parse_date_range('20240815')
        
        expected_start = datetime(2024, 8, 15)
        expected_end = datetime(2024, 8, 16)  # +1 day
        
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)
    
    @patch('cli.yyt_channel.yt_dlp.YoutubeDL')
    def test_get_channel_videos_success(self, mock_ydl_class):
        """Test successful channel video retrieval"""
        # Mock YoutubeDL instance
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        
        # Mock channel info
        mock_channel_info = {
            'title': '테스트 채널',
            'id': 'UC123456789',
            'entries': [
                {
                    'id': 'dQw4w9WgXcQ',
                    'title': '테스트 영상 1',
                    'upload_date': '20240815',
                    'duration': 212,
                    'view_count': 1000000,
                    'description': '테스트 설명'
                },
                {
                    'id': 'abc1234567',
                    'title': '테스트 영상 2',
                    'upload_date': '20240814',
                    'duration': 305,
                    'view_count': 500000,
                    'description': '테스트 설명 2'
                }
            ]
        }
        
        mock_ydl.extract_info.return_value = mock_channel_info
        
        videos = get_channel_videos('https://www.youtube.com/@testchannel')
        
        self.assertEqual(len(videos), 2)
        self.assertEqual(videos[0]['id'], 'dQw4w9WgXcQ')
        self.assertEqual(videos[0]['title'], '테스트 영상 1')
        self.assertEqual(videos[1]['id'], 'abc1234567')
    
    @patch('cli.yyt_channel.yt_dlp.YoutubeDL')
    def test_get_channel_videos_with_date_filter(self, mock_ydl_class):
        """Test channel video retrieval with date filtering"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        
        # Mock detailed video info for date filtering
        def mock_extract_info(url, download=False):
            if 'dQw4w9WgXcQ' in url:
                return {
                    'id': 'dQw4w9WgXcQ',
                    'title': '테스트 영상 1',
                    'upload_date': '20240815',
                    'duration': 212,
                    'view_count': 1000000,
                    'description': '테스트 설명'
                }
            elif 'channel' in url:
                return {
                    'title': '테스트 채널',
                    'id': 'UC123456789',
                    'entries': [{'id': 'dQw4w9WgXcQ', 'title': '테스트 영상 1'}]
                }
            return {}
        
        mock_ydl.extract_info.side_effect = mock_extract_info
        
        start_date = datetime(2024, 8, 15)
        end_date = datetime(2024, 8, 16)
        
        videos = get_channel_videos(
            'https://www.youtube.com/@testchannel',
            start_date=start_date,
            end_date=end_date
        )
        
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]['upload_date'], '2024-08-15T00:00:00')
    
    @patch('cli.yyt_channel.yt_dlp.YoutubeDL')
    def test_get_channel_videos_no_entries(self, mock_ydl_class):
        """Test channel video retrieval with no entries"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        
        mock_ydl.extract_info.return_value = {
            'title': '테스트 채널',
            'id': 'UC123456789'
            # No 'entries' key
        }
        
        with self.assertRaises(ValueError) as context:
            get_channel_videos('https://www.youtube.com/@testchannel')
        
        self.assertIn("채널 영상 목록을 가져올 수 없습니다", str(context.exception))
    
    @patch('cli.yyt_channel.yt_dlp.YoutubeDL')
    def test_get_channel_videos_exception(self, mock_ydl_class):
        """Test channel video retrieval with exception"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        
        mock_ydl.extract_info.side_effect = Exception("네트워크 오류")
        
        with self.assertRaises(ValueError) as context:
            get_channel_videos('https://www.youtube.com/@testchannel')
        
        self.assertIn("채널 정보를 가져올 수 없습니다", str(context.exception))
    
    @patch('builtins.print')
    def test_print_videos_table_empty(self, mock_print):
        """Test printing empty video table"""
        print_videos_table([])
        
        mock_print.assert_called_with("영상이 없습니다.")
    
    @patch('builtins.print')
    def test_print_videos_table_with_videos(self, mock_print):
        """Test printing video table with videos"""
        videos = [
            {
                'title': '테스트 영상 1',
                'upload_date': '2024-08-15T00:00:00',
                'view_count': 1000000,
                'duration': 212
            },
            {
                'title': '테스트 영상 2' * 30,  # Long title
                'upload_date': '2024-08-14T00:00:00',
                'view_count': 500000,
                'duration': 305
            }
        ]
        
        print_videos_table(videos)
        
        # Check that print was called multiple times
        self.assertTrue(mock_print.called)
        
        # Check content
        print_calls = [str(call) for call in mock_print.call_args_list]
        table_content = ''.join(print_calls)
        
        self.assertIn("총 2개 영상", table_content)
        self.assertIn("1,000,000", table_content)  # Formatted view count
        self.assertIn("3:25", table_content)  # Duration format
    
    @patch('cli.yyt_channel.yt_dlp.YoutubeDL')
    def test_get_channel_videos_max_videos_limit(self, mock_ydl_class):
        """Test channel video retrieval with max videos limit"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        
        mock_channel_info = {
            'title': '테스트 채널',
            'id': 'UC123456789',
            'entries': [
                {'id': f'video{i}', 'title': f'영상 {i}'} 
                for i in range(20)  # 20 videos
            ]
        }
        
        mock_ydl.extract_info.return_value = mock_channel_info
        
        videos = get_channel_videos(
            'https://www.youtube.com/@testchannel',
            max_videos=5
        )
        
        # Should be limited by max_videos parameter
        self.assertLessEqual(len(videos), 5)


if __name__ == '__main__':
    unittest.main()