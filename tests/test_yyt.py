#!/usr/bin/env python3
"""Tests for main yyt.py CLI interface"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import subprocess

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.yyt import (
    run_subcommand,
    pipeline_channel_summary,
    pipeline_full_analysis,
    main
)


class TestYyt(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_args = MagicMock()
        self.sample_args.channel_url = "https://www.youtube.com/@testchannel"
        self.sample_args.days = 7
        self.sample_args.date_range = None
        self.sample_args.max_videos = None
        
        self.sample_full_args = MagicMock()
        self.sample_full_args.video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.sample_full_args.output_dir = "./test_results"
    
    @patch('subprocess.run')
    def test_run_subcommand_success(self, mock_subprocess):
        """Test successful subcommand execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        returncode = run_subcommand('yyt_transcript', ['video_id', '--format', 'srt'])
        
        self.assertEqual(returncode, 0)
        mock_subprocess.assert_called_once_with(
            [sys.executable, '-m', 'cli.yyt_transcript', 'video_id', '--format', 'srt'],
            capture_output=False
        )
    
    @patch('subprocess.run')
    @patch('builtins.print')
    def test_run_subcommand_exception(self, mock_print, mock_subprocess):
        """Test subcommand execution with exception"""
        mock_subprocess.side_effect = Exception("명령 실행 오류")
        
        returncode = run_subcommand('yyt_transcript', ['video_id'])
        
        self.assertEqual(returncode, 1)
        mock_print.assert_called_with("명령 실행 실패: 명령 실행 오류", file=sys.stderr)
    
    @patch('cli.yyt.run_subcommand')
    @patch('builtins.print')
    def test_pipeline_channel_summary_success(self, mock_print, mock_run):
        """Test successful channel summary pipeline"""
        mock_run.return_value = 0
        
        result = pipeline_channel_summary(self.sample_args)
        
        self.assertEqual(result, 0)
        
        # Check that channel extraction was called with correct arguments
        expected_args = [
            self.sample_args.channel_url,
            '--days', '7',
            '--format', 'json',
            '--output', 'temp_videos.json'
        ]
        mock_run.assert_called_once_with('yyt_channel', expected_args)
    
    @patch('cli.yyt.run_subcommand')
    def test_pipeline_channel_summary_with_date_range(self, mock_run):
        """Test channel summary pipeline with date range"""
        mock_run.return_value = 0
        self.sample_args.days = None
        self.sample_args.date_range = "20240801-20240807"
        
        result = pipeline_channel_summary(self.sample_args)
        
        # Check that date-range was used instead of days
        call_args = mock_run.call_args[0][1]
        self.assertIn('--date-range', call_args)
        self.assertIn('20240801-20240807', call_args)
        self.assertNotIn('--days', call_args)
    
    @patch('cli.yyt.run_subcommand')
    def test_pipeline_channel_summary_with_max_videos(self, mock_run):
        """Test channel summary pipeline with max videos limit"""
        mock_run.return_value = 0
        self.sample_args.max_videos = 10
        
        result = pipeline_channel_summary(self.sample_args)
        
        call_args = mock_run.call_args[0][1]
        self.assertIn('--max-videos', call_args)
        self.assertIn('10', call_args)
    
    @patch('cli.yyt.run_subcommand')
    def test_pipeline_channel_summary_failure(self, mock_run):
        """Test channel summary pipeline with failure"""
        mock_run.return_value = 1
        
        result = pipeline_channel_summary(self.sample_args)
        
        self.assertEqual(result, 1)
    
    @patch('pathlib.Path.mkdir')
    @patch('cli.yyt.run_subcommand')
    @patch('builtins.print')
    def test_pipeline_full_analysis_success(self, mock_print, mock_run, mock_mkdir):
        """Test successful full analysis pipeline"""
        # Mock successful execution of all steps
        mock_run.side_effect = [0, 0, 0]  # meta, transcript, summarize
        
        result = pipeline_full_analysis(self.sample_full_args)
        
        self.assertEqual(result, 0)
        self.assertEqual(mock_run.call_count, 3)
        
        # Check that output directory was created
        mock_mkdir.assert_called_once_with(exist_ok=True)
        
        # Check completion message
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("완전한 분석 완료", output)
    
    @patch('pathlib.Path.mkdir')
    @patch('cli.yyt.run_subcommand')
    @patch('builtins.print')
    def test_pipeline_full_analysis_meta_failure(self, mock_print, mock_run, mock_mkdir):
        """Test full analysis pipeline with metadata extraction failure"""
        mock_run.side_effect = [1, 0, 0]  # meta fails, others would succeed
        
        result = pipeline_full_analysis(self.sample_full_args)
        
        self.assertEqual(result, 1)
        self.assertEqual(mock_run.call_count, 1)  # Should stop after first failure
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("메타데이터 추출 실패", output)
    
    @patch('pathlib.Path.mkdir')
    @patch('cli.yyt.run_subcommand')
    @patch('builtins.print')
    def test_pipeline_full_analysis_transcript_failure(self, mock_print, mock_run, mock_mkdir):
        """Test full analysis pipeline with transcript extraction failure"""
        mock_run.side_effect = [0, 1, 0]  # transcript fails
        
        result = pipeline_full_analysis(self.sample_full_args)
        
        self.assertEqual(result, 1)
        self.assertEqual(mock_run.call_count, 2)  # Should stop after transcript failure
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("자막 추출 실패", output)
    
    @patch('pathlib.Path.mkdir')
    @patch('cli.yyt.run_subcommand')
    @patch('builtins.print')
    def test_pipeline_full_analysis_default_output_dir(self, mock_print, mock_run, mock_mkdir):
        """Test full analysis pipeline with default output directory"""
        mock_run.side_effect = [0, 0, 0]
        self.sample_full_args.output_dir = None
        
        result = pipeline_full_analysis(self.sample_full_args)
        
        self.assertEqual(result, 0)
        
        # Check that default directory was used
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ''.join(print_calls)
        self.assertIn("./yyt_results", output)
    
    @patch('sys.argv', ['yyt.py'])
    @patch('builtins.print')
    def test_main_no_args(self, mock_print):
        """Test main function with no arguments"""
        with patch('argparse.ArgumentParser.print_help') as mock_help:
            main()
            mock_help.assert_called_once()
    
    @patch('sys.argv', ['yyt.py', 'transcript'])
    @patch('cli.yyt.run_subcommand')
    def test_main_help_for_subcommand(self, mock_run):
        """Test main function requesting help for subcommand"""
        mock_run.return_value = 0
        
        main()
        
        mock_run.assert_called_once_with('yyt_transcript', ['--help'])
    
    @patch('sys.argv', ['yyt.py', 'transcript', 'video_id', '--format', 'srt'])
    @patch('cli.yyt.run_subcommand')
    def test_main_subcommand_execution(self, mock_run):
        """Test main function executing subcommand"""
        mock_run.return_value = 0
        
        with patch('argparse.ArgumentParser.parse_known_args') as mock_parse:
            mock_args = MagicMock()
            mock_args.command = 'transcript'
            mock_parse.return_value = (mock_args, ['video_id', '--format', 'srt'])
            
            main()
            
            mock_run.assert_called_once_with('yyt_transcript', ['video_id', '--format', 'srt'])
    
    @patch('sys.argv', ['yyt.py', 'pipeline', 'channel-summary', '@testchannel', '--days', '7'])
    @patch('cli.yyt.pipeline_channel_summary')
    def test_main_pipeline_channel_summary(self, mock_pipeline):
        """Test main function executing channel summary pipeline"""
        mock_pipeline.return_value = 0
        
        with patch('argparse.ArgumentParser.parse_known_args') as mock_parse:
            mock_args = MagicMock()
            mock_args.command = 'pipeline'
            mock_args.pipeline_type = 'channel-summary'
            mock_parse.return_value = (mock_args, [])
            
            main()
            
            mock_pipeline.assert_called_once_with(mock_args)
    
    @patch('sys.argv', ['yyt.py', 'pipeline', 'full-analysis', 'video_url'])
    @patch('cli.yyt.pipeline_full_analysis')
    def test_main_pipeline_full_analysis(self, mock_pipeline):
        """Test main function executing full analysis pipeline"""
        mock_pipeline.return_value = 0
        
        with patch('argparse.ArgumentParser.parse_known_args') as mock_parse:
            mock_args = MagicMock()
            mock_args.command = 'pipeline'
            mock_args.pipeline_type = 'full-analysis'
            mock_parse.return_value = (mock_args, [])
            
            main()
            
            mock_pipeline.assert_called_once_with(mock_args)
    
    @patch('sys.argv', ['yyt.py', 'invalid_command'])
    def test_main_invalid_command(self, ):
        """Test main function with invalid command"""
        with patch('argparse.ArgumentParser.parse_known_args') as mock_parse, \
             patch('argparse.ArgumentParser.print_help') as mock_help:
            
            mock_args = MagicMock()
            mock_args.command = 'invalid_command'
            mock_parse.return_value = (mock_args, [])
            
            result = main()
            
            mock_help.assert_called_once()
            self.assertEqual(result, 1)
    
    @patch('sys.argv', ['yyt.py', 'transcript', 'video_id'])
    @patch('cli.yyt.run_subcommand')
    @patch('builtins.print')
    def test_main_keyboard_interrupt(self, mock_print, mock_run):
        """Test main function handling keyboard interrupt"""
        mock_run.side_effect = KeyboardInterrupt()
        
        with patch('argparse.ArgumentParser.parse_known_args') as mock_parse:
            mock_args = MagicMock()
            mock_args.command = 'transcript'
            mock_parse.return_value = (mock_args, ['video_id'])
            
            result = main()
            
            self.assertEqual(result, 130)
            mock_print.assert_called_with("\n작업이 중단되었습니다.", file=sys.stderr)
    
    @patch('sys.argv', ['yyt.py', 'transcript', 'video_id'])
    @patch('cli.yyt.run_subcommand')
    @patch('builtins.print')
    def test_main_general_exception(self, mock_print, mock_run):
        """Test main function handling general exception"""
        mock_run.side_effect = Exception("일반 오류")
        
        with patch('argparse.ArgumentParser.parse_known_args') as mock_parse:
            mock_args = MagicMock()
            mock_args.command = 'transcript'
            mock_parse.return_value = (mock_args, ['video_id'])
            
            result = main()
            
            self.assertEqual(result, 1)
            mock_print.assert_called_with("오류: 일반 오류", file=sys.stderr)


if __name__ == '__main__':
    unittest.main()