import pytest
from unittest.mock import patch, Mock
from typing import Optional


class TestExtractVideoId:
    """Tests for extract_video_id function"""
    
    def test_extract_from_watch_url(self, sample_video_urls):
        """Test extracting video ID from youtube.com/watch URL"""
        from yoyaktube.utils import extract_video_id
        
        result = extract_video_id(sample_video_urls["watch"])
        assert result == "sJPgXV350ug"
    
    def test_extract_from_youtu_be_url(self, sample_video_urls):
        """Test extracting video ID from youtu.be URL"""
        from yoyaktube.utils import extract_video_id
        
        result = extract_video_id(sample_video_urls["youtu_be"])
        assert result == "sJPgXV350ug"
    
    def test_extract_from_shorts_url(self, sample_video_urls):
        """Test extracting video ID from YouTube Shorts URL"""
        from yoyaktube.utils import extract_video_id
        
        result = extract_video_id(sample_video_urls["shorts"])
        assert result == "sJPgXV350ug"
    
    def test_extract_with_url_parameters(self, sample_video_urls):
        """Test extracting video ID from URL with additional parameters"""
        from yoyaktube.utils import extract_video_id
        
        result = extract_video_id(sample_video_urls["with_params"])
        assert result == "sJPgXV350ug"
    
    def test_extract_from_mobile_url(self, sample_video_urls):
        """Test extracting video ID from mobile YouTube URL"""
        from yoyaktube.utils import extract_video_id
        
        result = extract_video_id(sample_video_urls["mobile"])
        assert result == "sJPgXV350ug"
    
    def test_extract_from_video_id_only(self, sample_video_id):
        """Test that function returns video ID if input is already a video ID"""
        from yoyaktube.utils import extract_video_id
        
        result = extract_video_id(sample_video_id)
        assert result == sample_video_id
    
    def test_extract_from_invalid_urls(self, invalid_video_urls):
        """Test that function returns None for invalid URLs"""
        from yoyaktube.utils import extract_video_id
        
        for invalid_url in invalid_video_urls:
            result = extract_video_id(invalid_url)
            assert result is None
    
    def test_extract_from_empty_string(self):
        """Test that function returns None for empty string"""
        from yoyaktube.utils import extract_video_id
        
        result = extract_video_id("")
        assert result is None
    
    def test_extract_from_none(self):
        """Test that function returns None for None input"""
        from yoyaktube.utils import extract_video_id
        
        result = extract_video_id(None)
        assert result is None
    
    def test_extract_invalid_video_id_length(self):
        """Test that function returns None for invalid video ID length"""
        from yoyaktube.utils import extract_video_id
        
        # Too short
        result = extract_video_id("short")
        assert result is None
        
        # Too long
        result = extract_video_id("toolongvideoid123")
        assert result is None


class TestFormatHms:
    """Tests for format_hms function"""
    
    def test_format_zero_seconds(self):
        """Test formatting 0 seconds"""
        from yoyaktube.utils import format_hms
        
        result = format_hms(0)
        assert result == "0:00:00"
    
    def test_format_seconds_only(self):
        """Test formatting seconds only (less than 1 minute)"""
        from yoyaktube.utils import format_hms
        
        result = format_hms(45)
        assert result == "0:00:45"
    
    def test_format_minutes_and_seconds(self):
        """Test formatting minutes and seconds (less than 1 hour)"""
        from yoyaktube.utils import format_hms
        
        result = format_hms(90)  # 1 minute 30 seconds
        assert result == "0:01:30"
        
        result = format_hms(300)  # 5 minutes
        assert result == "0:05:00"
    
    def test_format_hours_minutes_seconds(self):
        """Test formatting hours, minutes, and seconds"""
        from yoyaktube.utils import format_hms
        
        result = format_hms(3661)  # 1 hour 1 minute 1 second
        assert result == "1:01:01"
        
        result = format_hms(7200)  # 2 hours
        assert result == "2:00:00"
    
    def test_format_float_seconds(self):
        """Test formatting float seconds (should round down)"""
        from yoyaktube.utils import format_hms
        
        result = format_hms(90.7)
        assert result == "0:01:30"
        
        result = format_hms(3661.9)
        assert result == "1:01:01"
    
    def test_format_none_input(self):
        """Test formatting None input"""
        from yoyaktube.utils import format_hms
        
        result = format_hms(None)
        assert result == "0:00:00"
    
    def test_format_negative_seconds(self):
        """Test formatting negative seconds (should return 0:00:00)"""
        from yoyaktube.utils import format_hms
        
        result = format_hms(-10)
        assert result == "0:00:00"
    
    def test_format_large_duration(self):
        """Test formatting very large duration"""
        from yoyaktube.utils import format_hms
        
        result = format_hms(90061)  # 25 hours 1 minute 1 second
        assert result == "25:01:01"


class TestBuildLlmSummaryContext:
    """Tests for build_llm_summary_context function"""
    
    def test_build_context_with_all_parameters(self, sample_transcript_entries, sample_transcript_text):
        """Test building context with all parameters provided"""
        from yoyaktube.utils import build_llm_summary_context
        
        result = build_llm_summary_context(
            source_url="https://www.youtube.com/watch?v=sJPgXV350ug",
            duration_sec=300.0,
            upload_date="2023-12-01",
            transcript_entries=sample_transcript_entries,
            plain_transcript=sample_transcript_text
        )
        
        assert "https://www.youtube.com/watch?v=sJPgXV350ug" in result
        assert "5:00" in result  # 300 seconds = 5:00
        assert "2023-12-01" in result
        assert "안녕하세요, 오늘은 테스트에 대해 이야기해보겠습니다." in result
    
    def test_build_context_with_transcript_entries_only(self, sample_transcript_entries):
        """Test building context with only transcript entries"""
        from yoyaktube.utils import build_llm_summary_context
        
        result = build_llm_summary_context(transcript_entries=sample_transcript_entries)
        
        assert "안녕하세요, 오늘은 테스트에 대해 이야기해보겠습니다." in result
        assert "[00:00]" in result  # Timestamp formatting
    
    def test_build_context_with_plain_transcript_only(self, sample_transcript_text):
        """Test building context with only plain transcript"""
        from yoyaktube.utils import build_llm_summary_context
        
        result = build_llm_summary_context(plain_transcript=sample_transcript_text)
        
        assert sample_transcript_text in result
    
    def test_build_context_with_minimal_parameters(self):
        """Test building context with minimal parameters"""
        from yoyaktube.utils import build_llm_summary_context
        
        result = build_llm_summary_context()
        
        # Should return a basic context structure even with no parameters
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_build_context_with_source_url_only(self):
        """Test building context with only source URL"""
        from yoyaktube.utils import build_llm_summary_context
        
        result = build_llm_summary_context(
            source_url="https://www.youtube.com/watch?v=sJPgXV350ug"
        )
        
        assert "https://www.youtube.com/watch?v=sJPgXV350ug" in result
    
    def test_build_context_with_duration_formatting(self):
        """Test that duration is properly formatted in context"""
        from yoyaktube.utils import build_llm_summary_context
        
        result = build_llm_summary_context(duration_sec=3661.0)  # 1 hour 1 minute 1 second
        
        assert "1:01:01" in result
    
    def test_build_context_with_none_values(self):
        """Test building context with None values (should handle gracefully)"""
        from yoyaktube.utils import build_llm_summary_context
        
        result = build_llm_summary_context(
            source_url=None,
            duration_sec=None,
            upload_date=None,
            transcript_entries=None,
            plain_transcript=None
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_timestamp_formatting_in_entries(self, sample_transcript_entries):
        """Test that timestamps are properly formatted in transcript entries"""
        from yoyaktube.utils import build_llm_summary_context
        
        result = build_llm_summary_context(transcript_entries=sample_transcript_entries)
        
        # Check that timestamps are formatted as [MM:SS]
        assert "[00:00]" in result  # 0.0 seconds
        assert "[00:04]" in result  # 4.5 seconds
        assert "[00:09]" in result  # 9.7 seconds
        assert "[00:15]" in result  # 15.8 seconds